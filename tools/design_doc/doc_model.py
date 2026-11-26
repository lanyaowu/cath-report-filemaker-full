"""データモデルの詳細説明（構造・各セクション・値の約束・連携・保存形式・読込と保存・移行・検証）
usage: python3 tools/design_doc/doc_model.py
"""
import re
import subprocess
from extra_common import G, e, table, build_doc, RELATED

IMG = G.ROOT / 'docs/design/img'
FONT = 'Noto Sans CJK JP'


def dot(name, src):
    subprocess.run(['dot', '-Tsvg', '-o', str(IMG / f'{name}.svg')], input=src.encode('utf-8'), check=True)


def fig(name, cap, h='90mm'):
    return (f'<div class="fig"><img src="{(IMG / (name + ".svg")).as_uri()}" style="width:100%;max-height:{h};object-fit:contain"></div>'
            f'<p class="cap">{e(cap)}</p>')


def code(s):
    return f'<div class="tree">{e(s.strip(chr(10)))}</div>'


def field_counts():
    """docs/fields.md（自動生成の全項目一覧）から画面ごとの項目数を読む"""
    s = (G.ROOT / 'docs/fields.md').read_text(encoding='utf-8')
    total = re.search(r'全入力項目一覧（自動生成・(\d+) 項目）', s)
    secs = re.findall(r'^## (.+?)（(\d+) 項目）', s, re.M)
    return (int(total.group(1)) if total else sum(int(n) for _, n in secs)), secs


def make_figs():
    dot('dm_overview', f'''digraph G {{
  graph [rankdir=TB, fontname="{FONT}", nodesep=0.18, ranksep=0.45, bgcolor="transparent"];
  node [shape=box, style="rounded,filled", fontname="{FONT}", fontsize=15, fillcolor="#eef5f2", color="#5d8a7c", margin="0.12,0.07"];
  edge [fontname="{FONT}", fontsize=13, color="#5b6f75", fontcolor="#44585e"];
  pt [label="患者 Patient（patients）\\n属性・アレルギー・感染症・admissions[] 病歴総括", fillcolor="#e6f0fa", color="#5b84b1"];
  ms [label="マスタ Masters（masters）\\n術者・紹介病院・デバイス", fillcolor="#fdf6e3", color="#c9a54b"];
  us [label="利用者 users.json\\n（ファイル。DB ではない）", shape=note, fillcolor="#f1f1f1", color="#999999"];
  {{ rank=same; pt; ms; us; }}
  subgraph cluster_r {{ label="カテレポート CathReport（cath_reports）＝ 1 回の検査 ＝ 1 件"; fontname="{FONT}"; fontsize=15; style="rounded"; color="#5d8a7c";
    hd [label="id・patientRef・status（入力中/確定）・verified（照合済）\\nheader（施行日・Cine No・PCI No…）・history[] 登録履歴・version", fillcolor="#ffffff"];
    cr [label="cathRecord\\nカテ記録"]; cg [label="cagLvg\\nCAG/LVG"]; pc [label="pci\\nPCI"]; pi [label="pressureIvus\\nPressure/IVUS"]; ps [label="pcps\\nPCPS"];
    cf [label="conference\\nカンファレンス"]; mc [label="mace[5]\\nMACE"]; im [label="images[]\\n画像"]; rs [label="restudy\\nRestudy"];
    {{ rank=same; cr; cg; pc; pi; ps; }}
    {{ rank=same; cf; mc; im; rs; }}
    hd -> {{ cr cg pc pi ps }} [arrowhead=none, color="#9fb8b0"];
    cr -> cf [style=invis]; cg -> mc [style=invis]; pc -> im [style=invis]; pi -> rs [style=invis]; }}
  au [label="監査ログ audit_log", shape=cylinder, fillcolor="#f3e8f7", color="#9b6bb3"];
  pt -> hd [label="1 : N（patientRef）", penwidth=1.6];
  ms -> hd [style=dashed, label="選択の候補"];
  us -> au [style=dotted, label="誰が"]; rs -> au [style=invis]; hd -> au [style=dotted, constraint=false, label="操作を記録"];
}}''')
    dot('dm_storage', f'''digraph G {{
  graph [rankdir=LR, fontname="{FONT}", nodesep=0.3, ranksep=0.6, bgcolor="transparent"];
  node [shape=box, style="rounded,filled", fontname="{FONT}", fontsize=13, fillcolor="#e6f0fa", color="#5b84b1", margin="0.14,0.08"];
  edge [fontname="{FONT}", fontsize=11, color="#5b6f75", fontcolor="#44585e"];
  js [label="API の JSON\\n{{ patient }} / {{ report }}\\n（全版で同じ形）", shape=note, fillcolor="#fdf6e3", color="#c9a54b"];
  ls [label="ブラウザ localStorage\\ncath.patients・cath.reports・cath.masters\\n（配列を丸ごと JSON で保存）", fillcolor="#f1f1f1", color="#999999"];
  mg [label="MongoDB（Node.js・Spring）\\npatients・cath_reports・masters・audit_log\\n1 レポート ＝ 1 ドキュメント（画像も埋め込み）"];
  pg [label="PostgreSQL（Spring・Thymeleaf）\\ncath_reports：ヘッダは列・画面は JSONB 列\\n子テーブル：report_history・report_mace\\nreport_images・report_image_data（bytea）", fillcolor="#eef5f2", color="#5d8a7c"];
  js -> ls [label="React Local"]; js -> mg [label="React Remote"]; js -> pg [label="React Remote\\nThymeleaf"];
}}''')
    dot('dm_lifecycle', f'''digraph G {{
  graph [rankdir=TB, fontname="{FONT}", nodesep=0.35, ranksep=0.4, bgcolor="transparent"];
  node [shape=box, style="rounded,filled", fontname="{FONT}", fontsize=15, fillcolor="#e6f0fa", color="#5b84b1", margin="0.14,0.09"];
  edge [fontname="{FONT}", fontsize=13, color="#5b6f75", fontcolor="#44585e"];
  a [label="保存データ\\n（古い形・欠けあり）", shape=note, fillcolor="#fdf6e3", color="#c9a54b"];
  b [label="① mergeDefaults\\n全項目の既定値で補う"];
  c [label="② fitLists・fitPair\\n繰り返しの数を整える"];
  d [label="③ migrateReport\\n旧形式から移す"];
  f [label="④ 画面で編集\\n（Draft＝患者＋レポート）", fillcolor="#eef5f2", color="#5d8a7c"];
  g [label="⑤ 保存\\n検証・version・登録履歴", fillcolor="#f3e8f7", color="#9b6bb3"];
  a -> b -> c;
  d -> f -> g;
  c -> d;
  {{ rank=same; a; b; c; }} {{ rank=same; d; f; g; }}
  g -> a [constraint=false, style=dashed, label="次に開く時"];
}}''')


def counts_table():
    total, secs = field_counts()
    half = (len(secs) + 1) // 2
    rows = []
    for i in range(half):
        a = secs[i]
        b = secs[i + half] if i + half < len(secs) else ('', '')
        rows.append(((a[0], 'k'), (a[1], 'num'), (b[0], 'k'), (b[1], 'num')))
    return (f'<p>保存する項目は全部で <b>{total:,}</b> 項目です（docs/fields.md から自動集計。繰り返しの配列は 1 要素分で数えています）。</p>' +
            table(['区分', '項目数', '区分', '項目数'], rows, widths=['45mm', '22mm', '45mm', '22mm']))


def p_overview():
    return ('<h1>1. 概要</h1>'
            '<p class="lead">データは「患者」「カテレポート」「マスタ」の 3 つにまとめています。カテレポートは 1 回のカテ検査を 1 件とし、'
            '画面（カテ記録・CAG/LVG・PCI など）ごとのデータをその中に持ちます。画面を開くと 1 件のレポートを丸ごと読み、保存すると丸ごと書きます。</p>' +
            fig('dm_overview', 'データの全体像（実線は保存上の関係、破線は候補として使う関係）', '70mm') +
            '<h2>1.1 設計の方針</h2>' +
            table(['方針', '内容', '理由'], [
                (('1 検査 ＝ 1 件', 'k'), '1 回の検査の全画面のデータを 1 件のレポートにまとめる（MongoDB は 1 ドキュメント、PostgreSQL は 1 行＋子テーブル）', '画面単位で開いて保存する使い方に合い、検査の単位で確定・照合できる'),
                (('画面ごとのセクション', 'k'), 'レポートの中を cathRecord・cagLvg・pci… と画面単位に分ける', '項目の増減が多い（約 1,000 項目）。画面と対応させて見通しを良くする'),
                (('値は文字列', 'k'), '入力値は原則 string（空文字＝未入力）。チェックは boolean。数値は表示・計算の時に変換', '「未入力」と「0」を区別でき、手入力の書き方（<1・>90 など）も残せる'),
                (('算出値は保存しない', 'k'), 'BSA・BMI・EF・手技時間・J-CTO スコアなどは表示の時に計算', '元の値を直せば必ず合う。保存値と計算値の食い違いが起きない'),
                (('全項目を持つ形', 'k'), '読込時に既定値で全項目を補う（欠けている項目は空で作る）', '画面・帳票・集計のコードで「項目が無い」場合を考えなくてよい'),
                (('共通のキーは少なく', 'k'), 'コレクション間のキーは patientRef だけ。病変などは番号・名前の一致・複写でつなぐ', '構造を単純に保つ（代わりの注意点は 7 章・12 章）'),
            ], widths=['32mm', None, '60mm']))


def p_patient_report():
    return ('<h1>2. 患者（Patient）</h1>'
            '<p>患者は検査をまたいで共有するデータで、レポートとは別に保存します。1 人の患者に複数のレポートがあります（1 : N）。</p>' +
            table(['グループ', '項目', '補足'], [
                (('識別', 'k'), ('id・patientId・name・kana・sex・birthDate', 'code small'), 'id は内部 ID（pt-xxx）。patientId は病院の患者 ID（重複不可）'),
                (('基本・連絡先', 'k'), ('bloodType・rh・zip・address・phone・mobile・emergency{name,relation,phone}・insurance{type,number}', 'code small'), ''),
                (('アレルギー', 'k'), ('allergy{contrast,contrastDetail,drug,drugDetail,latex,iodine,food}', 'code small'), '造影剤・薬剤は有無＋詳細'),
                (('感染症', 'k'), ('infection{hbs,hcv,hiv,syphilis,mrsa}', 'code small'), "値は '' / '-' / '+' / 'unknown'"),
                (('担当・紹介', 'k'), ('primaryDoctor・ward・referral{hospital,doctor}・dnar', 'code small'), ''),
                (('病歴', 'k'), ('pastHistory・familyHistory・medicationNote・notes', 'code small'), '既往歴はカンファレンスでも参照表示'),
                (('病歴総括', 'k'), ('admissions[]{admitDate,dischargeDate,doctor,diagnosis,summary}', 'code small'), '入退院ごとに 1 行（数の上限なし）'),
                (('記録', 'k'), ('createdAt・updatedAt・version', 'code small'), 'version は同時保存の検出用（楽観ロック）'),
            ], widths=['26mm', '82mm', None]) +
            '<h1>3. カテレポート（CathReport）の共通部分</h1>' +
            table(['項目', '型', '内容'], [
                (('id', 'code'), 'string', '内部 ID（rp-xxx）'),
                (('patientRef', 'code'), 'string', '患者の id（コレクション間で唯一のキー）'),
                (('status', 'code'), "'入力中' | '確定'", '確定すると全項目が編集不可。「確定」をもう一度押すと入力中に戻る'),
                (('verified', 'code'), 'boolean', '照合済（確定とは別に記録）'),
                (('header', 'code'), 'object', 'studyDate（施行日・必須）・cineNo・pciNo・accessionNo・secretaryChecked・summary・submitted・qca・registrant。全画面の上部に表示'),
                (('history[]', 'code'), '{at, by, action}', '登録履歴。保存・確定・照合のたびにサーバーが追加。by はログイン中の利用者の表示名'),
                (('createdAt・updatedAt', 'code'), 'ISO 日時', 'サーバーが設定'),
                (('version', 'code'), 'number', '楽観ロック。読んだ時の値と保存先の値が違えば 409（他の人が先に保存）'),
                (('cathRecord … restudy', 'code'), 'object / 配列', '画面ごとのセクション（4 章）'),
            ], widths=['40mm', '34mm', None]) +
            '<h2>3.1 状態の変わり方</h2>' +
            table(['操作', '前', '後', '権限・条件'], [
                ('新規作成・保存', '—', '入力中', 'edit'),
                ('確定', '入力中', '確定', 'confirm。確定前の確認（未入力・自動判定との違い）を表示。警告だけで止めない'),
                ('確定の解除', '確定', '入力中', 'confirm'),
                ('照合', '（どちらでも）', 'verified = true / false', 'verify'),
                ('確定中の保存', '確定', '—', '拒否（409）。画面は全項目が入力不可'),
            ], widths=['32mm', '24mm', '36mm', None]))


SECTIONS = [
    ('cathRecord', 'カテ記録', [
        ('exam', '検査情報：緊急度・目的（CAG/PCI/SG/EVT…）・疾病・診断・アプローチ・シース・造影剤・透視時間・線量・開始/終了時刻'),
        ('doctors', '主治医・外来主治医・術者[3]・助手[3]・紹介元'),
        ('hemo', '血行動態：pressures{RA,RV,PA,PCW,LV,Ao…}×{s,d,m}・values{HR,CO,CI…}'),
        ('body・labs', '身長・体重・体温／入院時・血算・内分泌・退院時・血ガス・HBs/HCV'),
        ('risk', '危険因子（DM・HT・HL・喫煙…）と既往歴・併存症（priorMI・pciHx・renal…）'),
        ('complications・prognosis', '合併症（全検査で記録）／予後（死亡日・確認日・転院日…）'),
        ('pciSummary・futurePlan・comment・other', '自由記述'),
    ]),
    ('cagLvg', 'CAG/LVG', [
        ('approach・catheters{10}', 'アプローチ（動脈・静脈・シース）／カテーテル 10 枠（LCA・RCA・LV・LIMA…・任意 2）'),
        ('cag.segments{17}', 'AHA セグメント（RCA1〜LCX15・HL・4AV・4PD）ごとの径・石灰化・狭窄度・びまん性など'),
        ('cag.collaterals[1..5]・grafts[1..4]', '側副血行（from・to・grade・state）／バイパスグラフト（graft・anastomosis・patency）'),
        ('cag.lesions', '病変枝数と枝（「所見から算出」で設定）'),
        ('cag.syntax・euro・japan', 'スコア（PCI 基本タブで参照表示）'),
        ('lvg', '左室造影：values（EDV・ESV・EF…）・wallMotion（AHA 1〜7）・MR・AoG'),
    ]),
    ('pci', 'PCI', [
        ('basic', '標的病変数・サポート・結果・合併症・guiding[1..5]・micro[1..4]・gw[1..5]'),
        ('lesions[1..5]', '病変ごと：target・targetSub・Type・形態 morph・QCA pre/post・device{items[10]}・bif・cto・comp・summary・ict'),
        ('ctoScore', '手技全体の CTO スコア（病変の J-CTO の最大値を「反映」）'),
        ('patientComp・patientTreat', '患者単位の合併症・治療'),
        ('jpci{bg,pre,post,info,discharge}', 'J-PCI 登録項目（患者背景・術前検査・投薬・基本情報・補助循環…）'),
        ('risk・ami', '出血・血栓リスク（J-HBR・CREDO-Kyoto）／AMI の時刻（発症〜初回デバイス）'),
    ]),
    ('pressureIvus', 'Pressure/IVUS', [
        ('pressure[1..5]', 'Pressure Wire の病変ごと：lesion（病変名）・phase・薬剤・metrics{FFR,iFR,RFR…}・qca'),
        ('lesions[1..5]', 'IVUS の Lesion N：pre/post の指標×{lesion,proximal,distal}・性状・デバイス。数は pressure と同じ'),
    ]),
    ('pcps', 'PCPS', [('arrest〜start・detail', '心停止〜開始の時刻・初回心電図・術者・送脱血管・流量・離脱')]),
    ('conference', 'カンファレンス', [
        ('disease・nyha・ccs・onsetCourse', '病名・重症度・経過'),
        ('scinti・mdct・ucg・treadmill', '検査結果（シンチ・MDCT・心エコー・運動負荷）'),
        ('prevPci[5]・dischargeRx[]', '前回 PCI（手入力）／退院時処方 MedRow{drug,dose,usage,days}'),
    ]),
    ('mace[5]', 'MACE', [('mace[k]', '追跡調査 5 回分：MACE(-)確認・MACE(+)・死亡・ACS・脳卒中・心不全・出血・血行再建・その他（各 checked・date）')]),
    ('images[]', '画像', [('images[k]', 'カテゴリ・撮影日・方向・対象病変・題名・説明・ファイル名・MIME・dataUrl（Base64）・keyImage')]),
    ('restudy', 'Restudy', [('date・interval・lesions[5]・comment', '再検査：病変ごとの前回 %・今回 %・Late loss・再狭窄・TLR（前回 PCI から取込）')]),
]


def p_sections():
    rows = []
    for key, name, items in SECTIONS:
        for i, (p, d) in enumerate(items):
            rows.append(((name if i == 0 else '', 'k'), (p, 'code small'), d))
    return ('<h1>4. 画面ごとのセクション</h1>'
            '<p>レポートの中は画面と同じ単位に分かれています。<code>[1..5]</code> は数が可変（最大 5）の配列、<code>[5]</code> は数が固定の配列、'
            '<code>{17}</code> はキーが決まったオブジェクト（例：セグメント名がキー）です。</p>' +
            '<h2>4.1 項目の数</h2>' + counts_table() +
            '<h2>4.2 各セクションの中身</h2>' +
            table(['画面', 'パス（セクション内）', '内容'], rows, widths=['26mm', '56mm', None]))


def p_values():
    return ('<h1>5. 値の表し方（型の約束）</h1>' +
            table(['型', '値', '使い方'], [
                (('string', 'code'), "'' ＝ 未入力", '数値・日付・時刻もすべて文字列。日付は YYYY-MM-DD、時刻は HH:MM'),
                (('boolean', 'code'), 'true / false', 'チェックボックス（cancer・dnar・keyImage など）'),
                (('YN', 'code'), "'' / 'yes' / 'no'", '病変形態・J-CTO 項目など、「未回答」を区別したい Yes/No'),
                (('PM', 'code'), "'' / '-' / '+' / 'unknown'", '危険因子・感染症'),
                (('UMU', 'code'), "'' / 'yes' / 'no' / 'unknown'", '既往歴・J-PCI の項目'),
                (('Flags', 'code'), '{ キー: boolean }', '複数選択のチェック群（exam.flags・summary.tech など）'),
                (('StrMap・YNMap', 'code'), '{ キー: string }', '検査値（labs.*）・指標（metrics・qca）・形態（morph）'),
                (('Triple', 'code'), '{ s, d, m }', '圧（収縮期・拡張期・平均）'),
                (('DateTime', 'code'), '{ date, time }', 'AMI・PCPS の各時刻'),
                (('NameSize・ShapeSize', 'code'), '{ name, size } / { label, shape, size }', 'シース・ガイディング／カテーテル枠'),
            ], widths=['34mm', '52mm', None]) +
            '<p class="small">選択肢の値と表示名は <code>frontend/src/constants/options.ts</code>（Thymeleaf 版は同じ内容の Java 定数）にまとめています。保存するのは値で、表示名ではありません。</p>'
            '<h2>5.1 算出値（保存しない）</h2>' +
            table(['算出値', '元のデータ', '式・規則'], [
                ('BSA・BMI', 'cathRecord.body.height・weight', 'BSA＝0.007184×W^0.425×H^0.725（DuBois）、BMI＝W／(H/100)²'),
                ('手技時間', 'exam.startTime・endTime', '終了−開始（分）。終了が前なら日付をまたいだとみなす'),
                ('LVG の SV・EF・CO・各 Index', 'lvg.values.LVEDV・LVESV・HR、BSA', 'SV＝EDV−ESV、EF＝SV／EDV、CO＝SV×HR、Index＝÷BSA'),
                ('IVUS のプラーク面積・面積率・偏心率', 'IVUS の Vessel CSA・Lumen CSA・最大/最小厚', '(V−L)、(V−L)／V、(最大−最小)／最大'),
                ('J-CTO スコア', 'lesions[i].cto.jcto（5 項目）', 'yes の数（0〜5）。CTO で全項目回答の時だけ'),
                ('J-HBR 判定・CREDO-Kyoto', 'pci.risk.hbrMajor・hbrMinor・credo', '主要 1 以上 または 副次 2 以上で HBR／点数の合計で低・中・高'),
                ('Door to balloon など', 'pci.ami の各時刻', '時刻の差（分）'),
                ('JCS の狭窄度区分', 'セグメントの狭窄度・QCA %DS', 'QCA があれば QCA、なければ AHA 区分から変換'),
                ('ACC/AHA Type・成否の提案', '病変形態・術後 %・TIMI', '提案として表示（保存値は医師が選ぶ。違いは確定前の確認で表示）'),
            ], widths=['46mm', '52mm', None]) +
            '<p class="small">ボタンで値を作って保存するもの：<code>cag.lesions</code>（「所見から算出」）、<code>pci.ctoScore</code>（「病変の最大値を反映」）、'
            'QCA の「取得」、Restudy の「前回 PCI 病変を取込」。これらは押した時点の値を写すので、元を直しても自動では変わりません。</p>')


def p_lists():
    rows = [
        ('cagLvg.cag.collaterals', '側副血行', '可変 1〜5', '—'),
        ('cagLvg.cag.grafts', 'バイパスグラフト', '可変 1〜4', '—'),
        ('pci.basic.guiding', 'ガイディング', '可変 1〜5', '—'),
        ('pci.basic.micro', 'マイクロカテーテル', '可変 1〜4', '—'),
        ('pci.basic.gw', 'ガイドワイヤー', '可変 1〜5', '旧データは 10 件まで残す'),
        ('pci.lesions', 'PCI 病変', '可変 1〜5', 'PCI の全タブで同じ番号'),
        ('pressureIvus.pressure／lesions', 'Pressure Wire／IVUS', '可変 1〜5（2 つは同数）', '追加・削除も一緒'),
        ('pci.lesions[i].device.items', 'デバイス', '固定 10', '空の行も保存'),
        ('cagLvg.catheters', 'カテーテル枠', '固定 10（キー）', 'custom1・2 は名称も入力'),
        ('cagLvg.cag.segments', 'CAG セグメント', '固定 17（キー）', ''),
        ('mace', 'MACE', '固定 5', ''),
        ('restudy.lesions・conference.prevPci', 'Restudy・前回 PCI', '固定 5', ''),
        ('cathRecord.doctors.operators／assistants・pcps.operators', '術者・助手', '固定 3', ''),
        ('images・patient.admissions・conference.dischargeRx', '画像・病歴総括・処方', '上限なし', ''),
    ]
    return ('<h1>6. 繰り返し項目（配列）</h1>'
            '<p>可変の配列は <code>LIST_MAX</code>（frontend/src/model/defaults.ts）で最大数を決め、読込時に「末尾の空の要素を除く（最低 1 件）」形に整えます。'
            '途中の空の要素は詰めません（病変番号がずれないように）。詳しい仕組みは「繰り返し項目の仕組みと実装」（repeat_items.pdf）にあります。</p>' +
            table(['パス', '内容', '数', '補足'], [((a, 'code small'), b, c, (d, 'small')) for a, b, c, d in rows], widths=['62mm', '34mm', '36mm', None]) +
            code('''export const LIST_MAX = { collaterals: 5, grafts: 4, guiding: 5, micro: 4, gw: 5, lesions: 5, pressure: 5 } as const;'''))


def p_links():
    own = [
        ('患者属性（ID・氏名・フリガナ・性別・生年月日）', 'patient.*', '患者情報入力・カテ記録', '全画面のヘッダ'),
        ('施行日・Cine No・PCI No', 'report.header.*', 'カテ記録・患者情報入力（PCI No は PCI も）', '全画面のヘッダ'),
        ('透視時間・造影剤・Hb・Cr', 'cathRecord.exam.* / labs.*', 'カテ記録', 'PCI（J-PCI）'),
        ('危険因子・既往歴・併存症', 'cathRecord.risk', 'カテ記録', 'PCI（J-PCI）・カンファレンス'),
        ('身長・体重・血行動態・予後・HBs/HCV', 'cathRecord.body / hemo / prognosis / labs', 'カテ記録', 'カンファレンス'),
        ('Syntax・Euro・Japan Score', 'cagLvg.cag.syntax ほか', 'CAG/LVG', 'PCI（基本）'),
        ('LVG の値', 'cagLvg.lvg.values', 'CAG/LVG', 'カンファレンス'),
        ('感染症・既往歴（患者）', 'patient.infection / pastHistory', '患者情報入力', 'カンファレンス'),
    ]
    kinds = [
        (('同一', 'k'), '1 つのデータを複数のタブ・画面に表示', 'pci.lesions[i]（PCI の全タブ）、pressure[N].lesion（IVUS Lesion N の部位）'),
        (('同じ番号', 'k'), '2 つの配列の番号 N が同じ病変', 'pressure[N] ↔ lesions[N]（数をそろえ、追加・削除も一緒）'),
        (('名前の一致', 'k'), '文字列で探す・候補に出す（キーは持たない）', 'target の候補＝CAG セグメント、QCA 取得、画像の対象病変の候補'),
        (('複写・集計', 'k'), 'ボタンや表示の時に値を写す・数える', 'Restudy の取込、集計・帳票・確定前の確認（target のある病変だけ）'),
    ]
    return ('<h1>7. データの連携</h1>'
            '<h2>7.1 画面間で共有する項目（主画面）</h2>'
            '<p>同じパスの値を複数の画面に表示します。編集できるのは主画面だけで、他の画面では参照表示（淡い青・点線枠）になり、主画面へのリンクを出します。'
            '定義は <code>frontend/src/model/ownership.ts</code>（Thymeleaf 版は <code>form/Ownership.java</code>）で、サーバーも保存時に同じ規則で検査します。</p>' +
            table(['項目', 'パス', '編集できる画面', '参照のみの画面'], [(a, (b, 'code small'), c, d) for a, b, c, d in own], widths=['46mm', '46mm', '40mm', None]) +
            '<h2>7.2 病変（Target）を軸にした連携</h2>'
            '<p>病変を表すデータは画面ごとに別の配列にあり、共通の病変 ID はありません。つながり方は次の 4 種類です。</p>' +
            table(['種類', '意味', '例'], kinds, widths=['24mm', '56mm', None]) +
            fig('lesion_links', '病変（Target）を軸にしたデータ連携', '88mm'))


def p_storage():
    return ('<h1>8. 保存形式</h1>'
            '<p>画面とサーバーの間は全版で同じ JSON（<code>Patient</code>・<code>CathReport</code>・<code>Masters</code>）でやり取りし、保存先だけが違います。</p>' +
            fig('dm_storage', '同じ JSON を 3 種類の保存先に保存する', '56mm') +
            '<h2>8.1 MongoDB（Node.js・Spring MongoDB）</h2>' +
            table(['コレクション', '中身', 'インデックス'], [
                (('patients', 'code'), 'Patient（_id＝id）', 'patientId（一意）・kana'),
                (('cath_reports', 'code'), 'CathReport を丸ごと 1 ドキュメント（画像の dataUrl も含む）', 'patientRef・header.studyDate・header.cineNo・status＋verified'),
                (('masters', 'code'), 'Masters（_id＝default の 1 件）', '—'),
                (('audit_log', 'code'), '監査ログ', 'at・username＋at'),
            ], widths=['30mm', None, '64mm']) +
            '<p class="small">一覧の取得では <code>images.dataUrl</code> を読み込みません。同時保存は <code>version</code> を条件にした置き換えで検出します（違えば 409）。</p>'
            '<h2>8.2 PostgreSQL（Spring PostgreSQL・Thymeleaf 版）</h2>'
            '<p>「識別・検索・整合性に使う項目は列、画面の詳細は JSONB」の組み合わせです。項目を足しても表の変更（マイグレーション）は要りません。</p>' +
            table(['テーブル', '列・内容', '補足'], [
                (('patients', 'code'), '属性は列。emergency・insurance・allergy・infection・referral は JSONB', 'patient_id は一意。version で楽観ロック'),
                (('patient_admissions', 'code'), '病歴総括（patient_id, seq）', '患者の削除で一緒に削除'),
                (('cath_reports', 'code'), 'id・patient_ref・status・verified・ヘッダの各列＋cath_record・cag_lvg・pci・pressure_ivus・pcps・conference・restudy（JSONB）', "status は CHECK（'入力中','確定'）。pci・cath_record に GIN インデックス"),
                (('report_history', 'code'), '登録履歴（report_id, seq）', ''),
                (('report_mace', 'code'), 'data（JSONB）が正。has_death など集計用の列を保存時に展開', 'seq は 0〜9'),
                (('report_images', 'code'), '画像のメタ情報', '一覧ではこちらだけ読む'),
                (('report_image_data', 'code'), '画像本体（bytea）', 'dataUrl を Base64 デコードして保存'),
                (('master_items', 'code'), 'kind（doctor・hospital・device）・category・name・sort_order', ''),
                (('audit_log', 'code'), '監査ログ', 'トリガーで更新・削除・TRUNCATE を禁止'),
                (('v_report_summary・v_mace_events・v_monthly_stats', 'code small'), '集計用のビュー（JSONB から主要項目を列として取り出す）', '数値は cr_num() で文字列から変換'),
            ], widths=['40mm', None, '50mm']) +
            '<h2>8.3 ブラウザ（React 版の Local）</h2>' +
            table(['キー', '中身'], [
                (('cath.patients・cath.reports・cath.masters', 'code'), 'それぞれの配列・オブジェクトを JSON で保存（体験・デモ用）'),
                (('cath.seeded', 'code'), 'サンプルデータを入れたかどうか（サンプルの版）'),
            ], widths=['70mm', None]) +
            '<h2>8.4 Thymeleaf 版の画面とデータ</h2>'
            '<p>画面の入力欄は <code>data-path</code>（例：<code>report.cathRecord.exam.urgency</code>）で項目を指します。表示の時はサーバーが JSON を「パス → 値」の表に平らにして（PathValues.flatten）テンプレートへ渡し、'
            '保存の時は画面が変わった項目だけを「パス → 値」で送り、サーバーが元の JSON に当てはめます（PathValues.apply）。保存する形は React 版と同じです。</p>')


def p_lifecycle():
    return ('<h1>9. 読込と保存の流れ</h1>' +
            fig('dm_lifecycle', '読込のたびに正規化し、保存の時に検証する', '50mm') +
            table(['段階', '処理', '実装（React 版）'], [
                (('① 既定値で補う', 'k'), '空のレポート（createEmptyReport）に保存データを重ねる。保存データに無い項目は既定値（空）になる。知らない項目はそのまま残る', ('normalizeReport → mergeDefaults', 'code small')),
                (('② 数を整える', 'k'), '可変の配列の末尾の空を除く（最低 1 件）。Pressure Wire と IVUS は同じ数にそろえる', ('fitLists・fitList・fitPair', 'code small')),
                (('③ 旧形式から移す', 'k'), '10 章の移行を毎回行う（移した後は何もしない）', ('migrateReport', 'code small')),
                (('④ 編集', 'k'), '患者＋レポートを 1 つのフォーム（Draft）として扱う。値の読み書きはパス（getAt・setAt）', ('Draft・utils/path.ts', 'code small')),
                (('⑤ 保存', 'k'), '権限 → version → 確定ロック → 主画面 → 必須項目 → 登録履歴の追加 → 保存（患者 → レポート）', ('rules.ts・ReportRules・FormService', 'code small')),
            ], widths=['28mm', None, '50mm']) +
            '<p class="small">Thymeleaf 版は同じ処理をサーバー側（Clinical・FormService）と画面の JavaScript（screens.js の繰り返し項目）で行います。</p>'
            '<h1>10. 旧データからの移行</h1>'
            '<p>形を変えた時は、読込のたびに画面側で移し（React：migrateReport、Thymeleaf：Clinical）、PostgreSQL では必要に応じて SQL でも移します。古いデータもそのまま開けます。</p>' +
            table(['変更', '移し方', '場所'], [
                ('既往歴・併存症を J-PCI からカテ記録へ', 'jpci.bg の priorMI・priorHF・pciHx・cabgHx・renal・copd・pad を、カテ記録が空なら cathRecord.risk へ移し、J-PCI 側は消す', ('migrateReport・V4__history_to_cath_record.sql', 'code small')),
                ('CTO の閉塞期間を追加', '空なら旧「Age of Occlusion」から <3m／>=3m／unknown を補う', ('durationFromAge', 'code small')),
                ('IVUS の部位を Pressure Wire の病変名へ一本化', 'pressure[N].lesion が空で lesions[N].site がある時は移す。両方あって違う時は Pressure Wire を優先（IVUS 側の値は残す）', ('fitLists・Clinical.migratePressureIvus', 'code small')),
                ('繰り返し項目を可変長に', '末尾の空を除く。最大数を超えて入力済みの旧データ（GW 10 件など）は消さずに残す（追加だけできない）', ('fitList', 'code small')),
            ], widths=['46mm', None, '52mm']))


def p_integrity():
    return ('<h1>11. 整合性と検証</h1>' +
            table(['検査', '内容', '場所'], [
                (('必須項目', 'k'), '患者 ID・氏名・施行日', '画面・サーバー'),
                (('一意', 'k'), '患者 ID（patientId）の重複は 409', 'サーバー（一意インデックス・制約）'),
                (('参照', 'k'), 'レポートのある患者は削除できない（409。PostgreSQL は外部キーの ON DELETE RESTRICT でも防ぐ）', 'サーバー・DB'),
                (('同時保存', 'k'), '読んだ時の version と違えば 409（上書きしない）', 'サーバー・DB'),
                (('確定ロック', 'k'), '確定中は保存・画像の変更・レポートの削除を拒否（409）', '画面・サーバー'),
                (('主画面', 'k'), '主画面以外からの共有項目の変更を拒否', 'サーバー（Thymeleaf 版）・画面'),
                (('状態の値', 'k'), "status は '入力中' か '確定'", 'DB（CHECK）'),
                (('確定前の確認', 'k'), '未入力（PCI 病変の Type・狭窄度・TIMI・成否・J-CTO など）と、自動判定・提案との違いを一覧で表示。確定は止めない', '画面（confirmWarnings・confirmMismatches）'),
            ], widths=['28mm', None, '52mm']) +
            '<h1>12. 注意点と改善案</h1>' +
            table(['対象', '内容', '改善案'], [
                (('病変の共通キーがない', 'k'), '病変は番号・名前の一致・複写でつながる。名前を変えると QCA 取得などが探せなくなる', '病変 ID を持たせる、または病変名を CAG セグメントからの選択に統一'),
                (('QCA 取得の照合', 'k'), 'target の数字を含むかで探すため、#1 が LCX#13 にも一致することがある', 'セグメントのキーに正規化して完全一致'),
                (('同じ意味の欄が複数', 'k'), '術前・術後の狭窄度（QCA と基本タブ）、標的病変数（PCI 基本・J-PCI・病変の数）、左主幹部（J-PCI と CAG）', 'どれかを主にして他は参照表示・提案にする'),
                (('数値が文字列', 'k'), '集計の時に変換が要る（PostgreSQL は cr_num()）。範囲や単位はデータでは保証しない', '数値項目に入力の検査（範囲・形式）を足す'),
                (('画像の保存', 'k'), 'MongoDB は画像を 1 ドキュメントに埋め込むため、1 件 16MB の上限に近づく', 'GridFS や外部ストレージに分ける（PostgreSQL 版は分離済み）'),
                (('JSONB の検索', 'k'), '列にしていない項目の検索・集計は JSON のパスで書く必要がある', 'よく使う項目はビュー・生成列にする'),
                (('項目の増減', 'k'), '既定値の構造（defaults.ts）と Java・テンプレート・帳票を同時に直す必要がある', '項目定義を 1 か所にまとめて各版を生成'),
            ], widths=['34mm', None, '58mm']))


PARTS = [
    ('ov', 1, '1. 概要', p_overview),
    ('pr', 1, '2. 患者／3. カテレポートの共通部分', p_patient_report),
    ('se', 1, '4. 画面ごとのセクション', p_sections),
    ('va', 1, '5. 値の表し方', p_values),
    ('li', 1, '6. 繰り返し項目', p_lists),
    ('lk', 1, '7. データの連携', p_links),
    ('st', 1, '8. 保存形式', p_storage),
    ('lc', 1, '9. 読込と保存の流れ／10. 旧データからの移行', p_lifecycle),
    ('in', 1, '11. 整合性と検証／12. 注意点と改善案', p_integrity),
]

if __name__ == '__main__':
    make_figs()
    build_doc('データモデルの詳細説明', '患者・カテレポート・画面ごとのセクション・値の約束・データの連携・保存形式・読込と保存・移行・検証',
              '心カテーテルレポート（React 版・Thymeleaf 版）', RELATED, PARTS, G.ROOT / 'docs/design/data_model.pdf')

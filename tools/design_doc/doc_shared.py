"""画面間の共通データの整理（React 版・Thymeleaf 版で共通の仕様）"""
import subprocess
from extra_common import G, e, table, build_doc, RELATED
import content as C

IMG = G.ROOT / 'docs/design/img'

SCREENS = [('patient', '患者'), ('cathRecord', 'カテ'), ('cagLvg', 'CAG/LVG'), ('restudy', 'Restudy'), ('pci', 'PCI'), ('pressureIvus', 'P/IVUS'),
           ('images', '画像'), ('pcps', 'PCPS'), ('conference', 'カンファ'), ('mace', 'MACE'), ('list', '一覧'), ('stats', '集計')]
REC = ['patient', 'cathRecord', 'cagLvg', 'restudy', 'pci', 'pressureIvus', 'images', 'pcps', 'conference', 'mace']
NAME = {'patient': '患者情報入力', 'cathRecord': 'カテ記録', 'cagLvg': 'CAG/LVG', 'restudy': 'Restudy', 'pci': 'PCI', 'pressureIvus': 'Pressure/IVUS',
        'images': '画像', 'pcps': 'PCPS', 'conference': 'カンファレンス', 'mace': 'MACE', 'list': '一覧', 'stats': '集計'}

# ---------------------------------------------------------------- 1. 全画面に共通のデータ
COMMON = [
    ('患者ID・氏名・フリガナ・性別・生年月日', 'patient.patientId・name・kana・sex・birthDate', '患者情報入力・カテ記録', '全入力画面のヘッダ（参照）、一覧'),
    ('施行日・Cine No', 'report.header.studyDate・cineNo', 'カテ記録・患者情報入力', '全入力画面のヘッダ（参照）、一覧'),
    ('PCI No', 'report.header.pciNo', 'カテ記録・患者情報入力・PCI', '全入力画面のヘッダ（参照）、一覧'),
    ('年齢（計算）', '生年月日と施行日から算出', '-（保存しない）', '全入力画面のヘッダ、一覧'),
    ('カテ履歴', '同じ患者のレポート一覧（施行日・検査項目・緊急）', '-（表示のみ）', '全入力画面のヘッダ。クリックで移動'),
    ('照合・ステータス', 'report.verified・status', '全入力画面のサイドメニュー（医師・管理者）', '一覧（照合・状態）。確定で全項目ロック'),
    ('登録者', 'report.header.registrant', '全入力画面のトップバー', '登録履歴（React・サーバーの記録はログイン利用者）'),
    ('登録履歴', 'report.history', '-（保存時に自動追加）', 'サイドメニュー下部'),
]

# ---------------------------------------------------------------- 2. 共有項目（主画面で編集、他画面は参照表示）
SHARED = [
    # (項目, パス, 主画面, 参照画面と表示箇所)
    ('患者属性（ID・氏名・フリガナ・性別・生年月日）', 'patient.patientId・name・kana・sex・birthDate', ['patient', 'cathRecord'], '全入力画面のヘッダ'),
    ('感染症（HBs・HCV・HIV・梅毒・MRSA）', 'patient.infection', ['patient'], 'カンファレンス（臨床診断/感染症）'),
    ('既往歴', 'patient.pastHistory', ['patient'], 'カンファレンス（既往歴/経過）'),
    ('施行日・Cine No', 'report.header.studyDate・cineNo', ['cathRecord', 'patient'], '全入力画面のヘッダ'),
    ('PCI No', 'report.header.pciNo', ['cathRecord', 'patient', 'pci'], '全入力画面のヘッダ'),
    ('透視時間・造影剤（種類・量）', 'report.cathRecord.exam.fluoroTime・contrast', ['cathRecord'], 'PCI（J-PCI：手技情報）'),
    ('危険因子', 'report.cathRecord.risk', ['cathRecord'], 'PCI（J-PCI：DM・HT・HD・HL）、カンファレンス（基本：DM・CAPD・HD・HT・HL・家族歴・喫煙・DM 治療）'),
    ('Hb・Cr', 'report.cathRecord.labs.cbc.Hb・labs.admission.Cr', ['cathRecord'], 'PCI（J-PCI：術前）'),
    ('HBs 抗原・HCV 抗体（定性・定量）', 'report.cathRecord.labs.hbs・hcv', ['cathRecord'], 'カンファレンス（臨床診断/感染症）'),
    ('身長・体重（BSA・BMI）', 'report.cathRecord.body', ['cathRecord'], 'カンファレンス（基本）。BSA は CAG/LVG の計算にも使用'),
    ('血行動態（圧・CO・CI）', 'report.cathRecord.hemo', ['cathRecord'], 'カンファレンス（基本）。HR は LVG の計算にも使用'),
    ('予後（死亡日・確認日・確認者・コメント）', 'report.cathRecord.prognosis', ['cathRecord'], 'カンファレンス（基本）'),
    ('Syntax・Euro・Japan スコア', 'report.cagLvg.cag.syntax・euro・japan', ['cagLvg'], 'PCI（基本）'),
    ('LVG 値（EDV・ESV・EF ほか）', 'report.cagLvg.lvg.values', ['cagLvg'], 'カンファレンス（基本：LVG・LVEF）'),
]

# ---------------------------------------------------------------- 3. コピー・取込（複写。以後は別のデータ）
COPY_SAME = [
    # (操作, 画面, コピー元, コピー先)
    ('新規作成（自動）', '新規作成ダイアログ', '患者：主治医・紹介病院・紹介医（primaryDoctor・referral）', 'カテ記録：doctors.attending・referralHospital・referralDoctor'),
    ('画像の追加（自動）', '画像', '施行日（header.studyDate）', '画像の撮影日（images.takenAt）の初期値'),
    ('カテ記録のアプローチを反映', 'CAG/LVG', 'カテ記録：exam.approach・sheath', 'CAG/LVG：approach.artery・arterySheath'),
    ('QCA 取得（Pre/Post）', 'PCI（病変形態）', 'Pressure/IVUS：pressure[].qca（target の番号を含む病変名の列。post PCI は phase で区別）', 'PCI：lesions[i].pre / post（Ref・%DS・MLD）'),
    ('CAG コメントをコピー', 'カンファレンス', 'CAG/LVG：cag.comment', 'カンファレンス：comment（追記）'),
    ('病歴総括からコピー', 'カンファレンス', '患者：admissions（最新の1件）', 'カンファレンス：onsetCourse（追記）'),
]
COPY_PAST = [
    ('前回からコピー', 'カテ記録（検査値）', '同じ患者の前回レポート：cathRecord.labs・risk・body', 'カテ記録：labs・risk・body（置換）'),
    ('過去の CAG Comment コピー', 'カテ記録・CAG/LVG', '同じ患者の過去レポート：cagLvg.cag.comment（選択）', 'カテ記録：comment／CAG/LVG：cag.comment'),
    ('過去の CAG 所見コピー', 'CAG/LVG', '同じ患者の過去レポート：cag.segments・collaterals・collateralsNone・grafts', 'CAG/LVG：同じ項目（置換）'),
    ('前回 PCI 病変を取込', 'Restudy', '施行日より前の PCI レポート：pci.lesions（Target・Post %DS）', 'Restudy：lesions（5行）・interval（月数）'),
]

# ---------------------------------------------------------------- 4. 計算での参照
CALC = [
    ('年齢', '全画面ヘッダ・一覧', 'patient.birthDate、report.header.studyDate', '保存しない（表示のみ）'),
    ('BSA・BMI', 'カテ記録・カンファレンス', 'cathRecord.body.height・weight', '保存しない（表示のみ）'),
    ('LVG 指標（SV・EF・CO・各 Index・CI）', 'CAG/LVG（算出ボタン）', 'lvg.values.LVEDV・LVESV・HR、cathRecord.body（BSA）、cathRecord.hemo.values.HR（LVG の HR が空のとき）', 'lvg.values に保存'),
    ('PCI 後経過日数', 'MACE', 'mace[i].pciDate、各イベント日', '保存しない'),
    ('J-HBR・CREDO-Kyoto', 'PCI（出血・血栓リスク）', 'pci.bleeding の各項目（同じ画面内）', '判定を表示'),
    ('件数・平均', '集計', '一覧の絞込条件に合うレポート全体（cathRecord.exam・pci.lesions ほか）', '保存しない'),
]

# ---------------------------------------------------------------- 5. 他のレコードの参照（表示）
OTHER = [
    ('カテ履歴', '全画面ヘッダ', '同じ患者の全レポート（施行日の新しい順）'),
    ('この患者のレポート', '患者情報入力', '同じ患者の全レポート。新規作成もここから'),
    ('Previous PCI', 'カンファレンス', '同じ患者の他レポートのうち PCI 病変があるもの'),
    ('レコード送り', 'サイドメニュー', '一覧の絞込条件に合うレポート（先頭・前・次・最後）'),
]

# ---------------------------------------------------------------- 6. 整理して分かったこと
FINDINGS = [
    ('名前の一致の照合', 'QCA 取得（PCI ← Pressure/IVUS）', 'target の数字を含むかで列を探すため、#1 が LCX#13・LAD10 にも一致し、先にある列の QCA を取ることがある。',
     '病変名を CAG セグメントのキーに正規化して完全一致で照合する。病変名の入力も CAG セグメントからの選択に統一する。', '高'),
    ('同じ情報を2か所に保存', '術前・術後の狭窄度（PCI）', 'QCA の pre.pct／post.pct（病変形態）と summary.pre／post（基本タブ）が別の欄。帳票・成否判定・Restudy は QCA を優先、カンファレンスの当院 PCI 歴は summary だけを使う。',
     'どちらかを主にして、もう一方は参照表示にする。', '中'),
    ('同じ情報を複数か所に保存', '標的病変数・左主幹部病変', 'PCI 基本・J-PCI の標的病変数と病変の数、J-PCI の左主幹部病変と CAG の病変枝（LMT）が連動しない。',
     '病変の数・CAG の結果から提案する、または 1 つの欄を共有する。', '低'),
    ('同じ情報を2か所に保存', 'アプローチ・シース', 'カテ記録（exam.approach・sheath）と CAG/LVG（approach.artery・arterySheath）に別々に保存。「反映」ボタンで複写するため、後でカテ記録を直すと食い違う。',
     'CAG/LVG の動脈側アプローチを共有項目（主画面＝カテ記録）にし、CAG/LVG は参照表示にする。静脈側は CAG/LVG のまま。', '中'),
    ('同じ情報を2か所に保存', '感染症（HBs・HCV）', '患者（infection.hbs・hcv：±）とカテ記録（labs.hbs・hcv：定性・定量）の両方にある。カンファレンスでは両方を並べて表示。',
     '患者＝患者として確定した状態、カテ記録＝今回の検査値、と意味を分けて画面に明記する。または検査値を入力したら患者側の±を提案する。', '低'),
    ('入力する画面がない', 'QCA チェック（header.qca）', '一覧に「QCA」列として表示しているが、どの入力画面にも欄がない（サンプルデータの値のまま）。',
     'Pressure/IVUS か PCI に「QCA 済」のチェックを追加する（一覧の秘書入力確認と同様）。または QCA の入力があれば自動でチェックする。', '中'),
    ('ある時点の値の複写', '主治医・紹介元', '新規作成時に患者情報から複写。患者情報の主治医を後で変えても、既存のレポートは変わらない。',
     '「検査時点の担当」を残す意図どおり。画面のラベルで「検査時」であることを示す。', '低'),
    ('複写した元が分からない', 'コピー・取込の全般', 'コピー後は普通の入力と同じになり、いつ・どのレコードから複写したかが残らない。',
     '登録履歴または監査ログの detail に「前回（2026/10/01）からコピー」などを残す。', '低'),
    ('定義が2か所', '共有項目の表', 'React 版（model/ownership.ts）と Thymeleaf 版（form/Ownership.java）に同じ表を別々に記述（現在は 24 項目で一致）。',
     '1つの定義ファイル（JSON 等）から両方を生成する（課題 Q-03 の一部）。', '中'),
    ('画面だけの規則', '主画面（React 版）', 'React 版の API はレポート全体を置き換えるため、主画面の規則はサーバーで検査していない（Thymeleaf 版は検査）。',
     '保存時に「どの画面で保存したか」を送り、主画面以外の変更を検出する。または差分保存 API を追加する（課題 D-03）。', '低'),
]


def p_overview():
    kinds = [
        ('A', '全画面に共通', 'ヘッダの患者属性・施行日、照合・ステータス・登録者', len(COMMON)),
        ('B', '共有項目', '同じデータを複数の画面に表示。主画面でだけ編集し、他の画面は参照表示（淡い青・点線、主画面へのリンク付き）', len(SHARED)),
        ('C', 'コピー・取込', 'ボタンで別の項目・別のレコードから複写。複写した後は別のデータ', len(COPY_SAME) + len(COPY_PAST)),
        ('D', '計算での参照', '他の画面の値を使って計算（年齢・BSA・LVG 指標など）', len(CALC)),
        ('E', '他のレコードの参照', '同じ患者の他のレポートを表示（カテ履歴・Previous PCI など）', len(OTHER)),
    ]
    return ('<h1>1. 概要</h1>'
            '<p class="lead">心カテーテルレポートは、患者（Patient）1件とレポート（CathReport）1件を1つのフォームとして編集します。'
            '13の画面はこのデータの一部ずつを表示・編集しており、いくつかのデータは複数の画面で使われます。本資料は、その「画面間の共通データ」を種類ごとに整理し、整理して分かった課題をまとめます。</p>'
            '<h2>共通データの種類</h2>' +
            table(['', '種類', '内容', '件数'], [((a, 'k c'), (b, 'k'), c, (d, 'r')) for a, b, c, d in kinds], widths=['8mm', '30mm', None, '12mm']) +
            '<h2>基本の考え方</h2>' +
            table(['考え方', '内容'], [
                ('データは1か所', '共有項目は保存場所（パス）が1つ。どの画面で見ても同じ値（例：危険因子はカテ記録の report.cathRecord.risk を PCI・カンファレンスでも表示）。'),
                ('編集は主画面だけ', '主画面以外では参照表示（編集不可）。「○○で編集」のリンクで主画面へ移動できる。Thymeleaf 版はサーバーでも検査。'),
                ('保存はまとめて', 'どの画面で保存しても、患者（変更時）とレポート全体を保存する。画面ごとの保存はない。'),
                ('複写は複写', 'コピー・取込は、その時点の値を複写する。元を後で直しても、複写先は変わらない。'),
                ('確定で全体をロック', '確定済みのレポートは全画面で入力不可（照合・ステータス・登録者を除く）。'),
            ], widths=['30mm', None]) +
            '<h2>表の記号（7章のマトリクス）</h2>' +
            table(['記号', '意味'], [(('◎', 'c'), '編集できる（主画面）'), (('○', 'c'), '表示（参照のみ）'), (('→', 'c'), 'コピー・取込の複写先'),
                                  (('計', 'c'), '計算に使う'), (('－', 'c'), '使わない')], widths=['14mm', None]))


FLOW = [
    # (元, 先, 種類 shared/copy/calc, 内容)
    ('patient', 'hdr', 'shared', '患者属性（ID・氏名・フリガナ・性別・生年月日）'),
    ('cath', 'hdr', 'shared', '施行日・Cine No・PCI No'),
    ('cath', 'pci', 'shared', '透視時間・造影剤・DM/HT/HD/HL・Hb・Cr（J-PCI）'),
    ('cath', 'conf', 'shared', '危険因子・身長体重・血行動態・予後・HBs/HCV'),
    ('patient', 'conf', 'shared', '感染症・既往歴'),
    ('cag', 'pci', 'shared', 'Syntax・Euro・Japan スコア'),
    ('cag', 'conf', 'shared', 'LVG 値'),
    ('cath', 'cag', 'calc', 'BSA・HR（LVG の計算）'),
    ('cath', 'cag', 'copy', 'アプローチ・シース（反映ボタン）'),
    ('pi', 'pci', 'copy', 'QCA（Ref・%DS・MLD）'),
    ('cag', 'conf', 'copy', 'CAG コメント'),
    ('patient', 'conf', 'copy', '病歴総括 → 発症・経過'),
    ('patient', 'cath', 'copy', '主治医・紹介元（新規作成時）'),
    ('cath', 'images', 'copy', '施行日 → 撮影日の初期値'),
    ('past', 'cath', 'copy', '前回の検査値・危険因子・身長体重／過去の CAG Comment'),
    ('past', 'cag', 'copy', '過去の CAG 所見・CAG Comment'),
    ('past', 'restudy', 'copy', '前回 PCI 病変'),
    ('pci', 'images', 'calc', 'Target（対象病変の候補）'),
    ('cag', 'pci', 'calc', 'CAG セグメント（Target の候補）'),
    ('past', 'conf', 'calc', 'Previous PCI（表示）'),
]
NAME_F = {'patient': '患者情報入力', 'past': '過去のレポート', 'cath': 'カテ記録', 'pi': 'Pressure/IVUS', 'cag': 'CAG/LVG', 'hdr': '全画面ヘッダ',
          'pci': 'PCI', 'conf': 'カンファレンス', 'restudy': 'Restudy', 'images': '画像'}
NUM = '①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳'


def make_flow():
    style = {'shared': 'color="#33515f", fontcolor="#33515f", penwidth=1.4', 'copy': 'style=dashed, color="#c08a2e", fontcolor="#8a5f1a"',
             'calc': 'style=dotted, color="#4d6f86", fontcolor="#33515f"'}
    edges = '\n'.join(f'  {a} -> {b} [label="{NUM[i]}", {style[k]}];' for i, (a, b, k, _) in enumerate(FLOW))
    dot = f'''digraph G {{
  graph [rankdir=LR, fontname="Noto Sans CJK JP", nodesep=0.35, ranksep=1.1, bgcolor="transparent"];
  node [shape=box, style="rounded,filled", fontname="Noto Sans CJK JP", fontsize=12, fillcolor="#eef5f2", color="#5d8a7c", margin="0.15,0.08"];
  edge [fontname="Noto Sans CJK JP", fontsize=12, arrowsize=0.8];
  patient [label="患者情報入力", fillcolor="#fdf3e3", color="#b07a2f"];
  past [label="同じ患者の\n過去のレポート", shape=folder, fillcolor="#f6f6f6", color="#999999"];
  cath [label="カテ記録", fillcolor="#fdf3e3", color="#b07a2f"];
  pi [label="Pressure/IVUS"];
  cag [label="CAG/LVG"];
  hdr [label="全画面のヘッダ", fillcolor="#f1f1f1", color="#888888"];
  pci [label="PCI"];
  conf [label="カンファレンス"];
  restudy [label="Restudy"];
  images [label="画像"];
  {{ rank=same; patient; past; }}
  {{ rank=same; cath; pi; }}
  {{ rank=same; hdr; pci; conf; restudy; images; }}
{edges}
}}'''
    IMG.mkdir(parents=True, exist_ok=True)
    subprocess.run(['dot', '-Tsvg', '-o', str(IMG / 'shared_flow.svg')], input=dot.encode('utf-8'), check=True)


def p_flow():
    return ('<h1>2. 画面間のデータの流れ</h1>'
            '<div class="fig"><img src="' + (IMG / 'shared_flow.svg').as_uri() + '" style="width:100%;max-height:120mm;object-fit:contain"></div>'
            '<p class="cap">実線：共有項目（同じデータを表示）　破線（橙）：コピー・取込（複写）　点線：計算・表示での参照</p>' +
            table(['', '種類', '元 → 先', '内容'], [((NUM[i], 'c k'), {'shared': '共有', 'copy': 'コピー', 'calc': '参照'}[k], f'{NAME_F[a]} → {NAME_F[b]}', d)
                                                 for i, (a, b, k, d) in enumerate(FLOW)], widths=['8mm', '14mm', '48mm', None]) +
            '<div class="note">データの「元」になる画面は主に <b>患者情報入力</b> と <b>カテ記録</b> です。CAG/LVG はスコアと LVG 値の元、Pressure/IVUS は QCA の元になります。'
            'カンファレンスは、他の画面のデータを最も多く参照する画面です。</div>')


def p_common():
    return ('<h1>3. 全画面に共通のデータ</h1><p class="lead">全ての入力画面の上部（患者属性ヘッダ）・サイドメニュー・トップバーに出るデータです。</p>' +
            table(['データ', '保存場所（パス）', '編集する場所', '表示する場所'], [((a, 'k'), (b, 'code small'), c, d) for a, b, c, d in COMMON], widths=['30mm', '38mm', '36mm', '78mm']) +
            '<div class="note">ヘッダの患者属性・施行日・Cine No・PCI No は、患者情報入力とカテ記録（PCI No は PCI も）で編集でき、その他の画面では参照表示です。'
            '照合・ステータスはどの入力画面からも切り替えられますが、医師・管理者の権限が必要です。</div>')


def p_shared():
    rows = [((a, 'k'), (b, 'code small'), '・'.join(NAME[o] for o in owners), d) for a, b, owners, d in SHARED]
    return ('<h1>4. 共有項目（主画面と参照画面）</h1>'
            '<p class="lead">保存場所は1つで、複数の画面に表示する項目です。主画面でだけ編集でき、他の画面では参照表示になります。'
            '定義は React 版 model/ownership.ts と Thymeleaf 版 form/Ownership.java（24 項目。両版で一致）。</p>' +
            table(['項目', '保存場所（パス）', '主画面（編集）', '参照する画面と表示箇所'], rows, widths=['36mm', '44mm', '30mm', None]) +
            '<h2>参照表示の見え方</h2>' +
            table(['表示', '内容'], [
                ('入力欄', '淡い青・点線の枠で編集不可（.ref）。マウスを乗せると「参照のみ：○○画面で編集します」'),
                ('リンク', '「○○で編集」「○○はカテ記録で編集」をクリックすると主画面へ移動（未保存の変更があれば確認）'),
                ('変更の表示', '主画面で変更した値は、保存前でも他の画面の参照表示にすぐ反映（同じデータのため）'),
            ], widths=['26mm', None]))


def p_copy():
    return ('<h1>5. コピー・取込</h1>'
            '<p class="lead">ボタン（一部は自動）で、別の項目や別のレコードの値を複写します。複写した後は普通の入力と同じで、元を直しても変わりません。保存するまで確定しません。</p>'
            '<h2>5.1 同じレコードの中での複写</h2>' +
            table(['操作', '画面', 'コピー元', 'コピー先'], [((a, 'k'), b, (c, 'small'), (d, 'small')) for a, b, c, d in COPY_SAME], widths=['34mm', '26mm', None, None]) +
            '<h2>5.2 過去のレコードからの複写</h2>' +
            table(['操作', '画面', 'コピー元', 'コピー先'], [((a, 'k'), b, (c, 'small'), (d, 'small')) for a, b, c, d in COPY_PAST], widths=['34mm', '26mm', None, None]) +
            '<p class="small">過去のレコード：同じ患者の、現在のレコード以外のレポート（前回からコピーは施行日が同じか前のもの、Restudy は前のもの）。置換は既存の値を上書き、追記は改行して後ろに追加。</p>')


def p_calc():
    return ('<h1>6. 計算と他のレコードの参照</h1><h2>6.1 計算での参照</h2>' +
            table(['計算', '画面', '使うデータ', '結果'], [((a, 'k'), b, (c, 'code small'), d) for a, b, c, d in CALC], widths=['32mm', '32mm', None, '30mm']) +
            '<h2>6.2 他のレコードの参照（表示）</h2>' +
            table(['表示', '画面', '内容'], [((a, 'k'), b, c) for a, b, c in OTHER], widths=['32mm', '32mm', None]))


def p_matrix():
    rows_def = [
        ('全画面に共通', None),
        ('患者属性（ID・氏名・フリガナ・性別・生年月日）', {'patient': '◎', 'cathRecord': '◎', **{k: '○' for k in REC if k not in ('patient', 'cathRecord')}, 'list': '○'}),
        ('施行日・Cine No', {'patient': '◎', 'cathRecord': '◎', **{k: '○' for k in REC if k not in ('patient', 'cathRecord')}, 'list': '○', 'stats': '計'}),
        ('PCI No', {'patient': '◎', 'cathRecord': '◎', 'pci': '◎', **{k: '○' for k in REC if k not in ('patient', 'cathRecord', 'pci')}, 'list': '○'}),
        ('年齢（生年月日・施行日から）', {**{k: '計' for k in REC}, 'list': '計'}),
        ('照合・ステータス', {**{k: '◎' for k in REC}, 'list': '○', 'stats': '計'}),
        ('登録者', {k: '◎' for k in REC}),
        ('患者情報', None),
        ('感染症', {'patient': '◎', 'conference': '○'}),
        ('既往歴', {'patient': '◎', 'conference': '○'}),
        ('病歴総括', {'patient': '◎', 'conference': '○→'}),
        ('主治医・紹介元', {'patient': '◎', 'cathRecord': '→'}),
        ('カテ記録', None),
        ('透視時間・造影剤', {'cathRecord': '◎', 'pci': '○'}),
        ('危険因子', {'cathRecord': '◎', 'pci': '○', 'conference': '○'}),
        ('Hb・Cr', {'cathRecord': '◎', 'pci': '○'}),
        ('HBs 抗原・HCV 抗体', {'cathRecord': '◎', 'conference': '○'}),
        ('身長・体重（BSA）', {'cathRecord': '◎', 'cagLvg': '計', 'conference': '○'}),
        ('血行動態（HR）', {'cathRecord': '◎', 'cagLvg': '計', 'conference': '○'}),
        ('予後', {'cathRecord': '◎', 'conference': '○'}),
        ('アプローチ・シース', {'cathRecord': '◎', 'cagLvg': '→'}),
        ('検査値・危険因子・身長体重（前回）', {'cathRecord': '→'}),
        ('秘書入力確認・AccessionNo', {'cathRecord': '◎', 'list': '○'}),
        ('Follow-up', {'cathRecord': '◎', 'list': '○'}),
        ('CAG/LVG・その他', None),
        ('Syntax・Euro・Japan スコア', {'cagLvg': '◎', 'pci': '○'}),
        ('LVG 値', {'cagLvg': '◎', 'conference': '○'}),
        ('CAG コメント', {'cagLvg': '◎', 'conference': '→'}),
        ('QCA（Pressure Wire）', {'pressureIvus': '◎', 'pci': '→'}),
        ('病変名（Pressure Wire ↔ IVUS Lesion）', {'pressureIvus': '◎'}),
        ('PCI 病変（Target）', {'pci': '◎', 'images': '○', 'stats': '計', 'conference': '○'}),
        ('PCI 病変（前回）', {'pci': '◎', 'restudy': '→', 'conference': '○'}),
        ('サマリー・提出', {'conference': '◎', 'list': '○'}),
        ('QCA チェック（header.qca）', {'list': '○'}),
    ]
    head = '<tr><th style="width:52mm">データ</th>' + ''.join(f'<th class="c" style="font-size:7.6pt;padding:1mm 0.5mm">{e(l)}</th>' for _, l in SCREENS) + '</tr>'
    body = []
    for name, m in rows_def:
        if m is None:
            body.append(f'<tr class="grp"><td colspan="{len(SCREENS) + 1}" style="padding:0.6mm 1.2mm">{e(name)}</td></tr>')
            continue
        tds = ''.join(f'<td class="c" style="padding:0.5mm 0.3mm;{"background:#fdf3e3;font-weight:700" if "◎" in m.get(k, "") else ""}">{m.get(k, "<span style=\'color:#bbb\'>－</span>")}</td>' for k, _ in SCREENS)
        body.append(f'<tr><td style="padding:0.5mm 1.2mm">{e(name)}</td>{tds}</tr>')
    return ('<h1>7. 画面×データ マトリクス</h1>'
            '<p class="lead">◎ 編集（主画面）　○ 表示（参照のみ）　→ コピー・取込の複写先　計 計算に使う。P/IVUS＝Pressure/IVUS、カンファ＝カンファレンス。</p>'
            f'<table style="font-size:8.2pt;line-height:1.35"><thead>{head}</thead><tbody>{"".join(body)}</tbody></table>')


def p_findings():
    pri = {k: f'<span class="pri {k}">{k}</span>' for k in ('高', '中', '低')}
    rows = [(f'<b>{e(b)}</b><br><span class="small">{e(a)}</span>', e(c), e(d), (pri[p], 'c')) for a, b, c, d, p in FINDINGS]
    return ('<h1>8. 整理して分かったこと・改善案</h1>'
            '<p class="lead">共通データを洗い出した結果、次の点が分かりました。いずれも現在の動作に誤りはありませんが、データの食い違いや入力漏れの原因になり得ます。</p>' +
            table(['対象（分類）', '現状', '改善案', '優先'], rows, widths=['30mm', '72mm', '70mm', '10mm'], raw=True) +
            '<h2>まとめ</h2>'
            '<div class="note">共有項目（24 項目）は「保存場所1つ・主画面で編集・他は参照表示」で整理されており、両版で定義が一致しています。'
            '改善が必要なのは、<b>同じ情報を複写で持っている箇所</b>（アプローチ・PCI の狭窄度）、<b>入力欄のない項目</b>（QCA チェック）、そして<b>病変を名前の一致でつないでいる箇所</b>（QCA 取得）です。病変については、病変名を CAG セグメントのキーにそろえることが、照合の誤りを防ぐ一番の対策です（9 章）。</div>')


LESION_DATA = [
    ('PCI 病変', 'pci.lesions[i]', '1〜5（可変）', 'PCI：基本・病変形態・Device・Bif/CTO・Complication・J-PCI・検索用', 'target（#番号）＋ targetSub'),
    ('Pressure Wire の病変', 'pressureIvus.pressure[N]', '1〜5（可変）', 'Pressure/IVUS：Pressure Wire', 'lesion'),
    ('IVUS の病変', 'pressureIvus.lesions[N]', 'pressure と同数', 'Pressure/IVUS：Lesion N', 'pressure[N].lesion を共有'),
    ('CAG セグメント', 'cagLvg.cag.segments{key}', '17（固定）', 'CAG/LVG：CAG', 'key（RCA1〜LCX15・HL・4AV・4PD）'),
    ('病変枝', 'cagLvg.cag.lesions', '1', 'CAG/LVG：CAG', 'LMT・LAD・LCX・RCA'),
    ('Restudy の病変', 'restudy.lesions[k]', '5', 'Restudy', 'segment（取込・自由入力）'),
    ('画像の対象病変', 'images[].lesion', '画像ごと', '画像', '自由入力（候補＝target）'),
    ('前回 PCI（手入力）', 'conference.prevPci[k]', '5', 'カンファレンス', 'site'),
]


def make_lesion_flow():
    dot = '''digraph G {
  graph [rankdir=LR, fontname="Noto Sans CJK JP", nodesep=0.4, ranksep=0.9, bgcolor="transparent"];
  node [shape=box, style="rounded,filled", fontname="Noto Sans CJK JP", fontsize=11, fillcolor="#eef5f2", color="#5d8a7c", margin="0.15,0.07"];
  edge [fontname="Noto Sans CJK JP", fontsize=10, arrowsize=0.8];
  subgraph cluster_cag { label="CAG/LVG"; style="rounded"; color="#9fb7c9"; fontname="Noto Sans CJK JP"; fontsize=11;
    seg [label="CAG セグメント\nsegments{key}"]; br [label="病変枝\ncag.lesions"]; }
  subgraph cluster_pci { label="PCI（全タブ共通）"; style="rounded"; color="#d8a25e"; fontname="Noto Sans CJK JP"; fontsize=11;
    les [label="PCI 病変 lesions[i]\ntarget・targetSub", fillcolor="#fdf1e2", color="#d8a25e", penwidth=1.6];
    tabs [label="基本・病変形態・Device\nBif/CTO・Complication\nJ-PCI・検索用", shape=note, fillcolor="#fffaf2"];
    cto [label="手技全体の\nCTO スコア"]; }
  subgraph cluster_pi { label="Pressure/IVUS"; style="rounded"; color="#9b6bb3"; fontname="Noto Sans CJK JP"; fontsize=11;
    pw [label="Pressure Wire\npressure[N]（lesion）", fillcolor="#f3e8f7", color="#9b6bb3"]; iv [label="IVUS Lesion N\nlesions[N]", fillcolor="#f3e8f7", color="#9b6bb3"]; }
  img [label="画像\nimages[].lesion"]; rs [label="次回レポートの\nRestudy lesions[k]", shape=folder, fillcolor="#f6f6f6", color="#999999"];
  out [label="集計・検査報告書\n確定前の確認・当院 PCI 歴", fillcolor="#f1f1f1", color="#888888"];
  les -> tabs [label="同一（1 つのデータ）", color="#33515f", penwidth=1.6, dir=both];
  pw -> iv [label="同じ番号 N・病変名を共有\n追加・削除も一緒", color="#33515f", penwidth=1.6, dir=both];
  seg -> les [label="target の候補", style=dotted, color="#2b6cb0", fontcolor="#2b6cb0"];
  seg -> br [label="所見から算出", style=dotted, color="#4d6f86"];
  pw -> les [label="QCA 取得（名前の一致・複写）", style=dashed, color="#c08a2e", fontcolor="#8a5f1a"];
  les -> img [label="lesion の候補", style=dotted, color="#2b6cb0", fontcolor="#2b6cb0"];
  les -> rs [label="前回 PCI 病変を取込（複写）", style=dashed, color="#c08a2e", fontcolor="#8a5f1a"];
  les -> out [label="target ありだけ", style=dotted, color="#4d6f86"];
  les -> cto [label="J-CTO の最大値", style=dotted, color="#4d6f86"];
}'''
    subprocess.run(['dot', '-Tsvg', '-o', str(IMG / 'lesion_links.svg')], input=dot.encode('utf-8'), check=True)


def p_lesion():
    kinds = [('同一', '1 つのデータを複数のタブ・画面に表示', 'どこで変えても全部に反映'),
             ('同じ番号', '2 つの配列の番号 N が同じ病変', '数をそろえ、追加・削除も一緒（後ろを詰める）'),
             ('名前の一致', '病変名の文字列で探す・候補に出す', '名前を変えると探せなくなる（自動では追従しない）'),
             ('複写・集計', 'ボタンや表示時に値を写す・数える', '複写した後は別のデータ')]
    return ('<h1>9. 病変（Target）を軸にしたデータ連携</h1>'
            '<p class="lead">病変を表すデータは画面ごとに別の配列にあり、病変 ID（共通のキー）はありません。'
            '次の 4 種類のつながり方で、タブ・画面の間を結んでいます。データモデル（docs/ER.md・ER 図・types/model.ts）にも同じ内容を記載しています。</p>' +
            table(['種類', '意味', '追加・削除・変更した時'], [((a, 'k'), b, c) for a, b, c in kinds], widths=['24mm', None, None]) +
            '<div class="fig"><img src="' + (IMG / 'lesion_links.svg').as_uri() + '" style="width:100%;max-height:95mm;object-fit:contain"></div>'
            '<p class="cap">実線：同一・同じ番号　破線（橙）：複写　点線：候補・計算・集計</p>'
            '<h2>9.1 病変を表すデータ</h2>' +
            table(['データ', '保存場所', '数', '画面（タブ）', '病変の名前'], [((a, 'k'), (b, 'code small'), c, (d, 'small'), (f, 'small')) for a, b, c, d, f in LESION_DATA],
                  widths=['26mm', '40mm', '20mm', None, '38mm']) +
            '<h2>9.2 連携の一覧</h2>' +
            table(['種類', '元', '先', '内容'], [((a, 'k'), (b, 'code small'), (c, 'code small'), (d, 'small')) for a, b, c, d in C.LESION_LINKS], widths=['20mm', '36mm', '40mm', None]) +
            '<h2>9.3 注意点と改善案</h2>' +
            table(['対象', '内容', '改善案'], [((a, 'k'), (b, 'small'), (c, 'small')) for a, b, c in C.LESION_ISSUES], widths=['28mm', None, '62mm']) +
            '<p class="small">8 章の「整理して分かったこと」にも、優先度を付けて含めています。</p>')


PARTS = [
    ('ov', 1, '1. 概要（種類・考え方）', p_overview),
    ('flow', 1, '2. 画面間のデータの流れ', p_flow),
    ('common', 1, '3. 全画面に共通のデータ', p_common),
    ('shared', 1, '4. 共有項目（主画面と参照画面）', p_shared),
    ('copy', 1, '5. コピー・取込', p_copy),
    ('calc', 1, '6. 計算と他のレコードの参照', p_calc),
    ('matrix', 1, '7. 画面×データ マトリクス', p_matrix),
    ('find', 1, '8. 整理して分かったこと・改善案', p_findings),
    ('lesion', 1, '9. 病変（Target）を軸にしたデータ連携', p_lesion),
]

if __name__ == '__main__':
    make_flow()
    make_lesion_flow()
    build_doc('画面間の共通データ', '全画面に共通のデータ・共有項目・コピー/取込・計算での参照・マトリクス・改善案',
              'React 版・Thymeleaf 版（画面と共有の規則は両版で共通）', RELATED, PARTS, G.ROOT / 'docs/design/shared_data_between_screens.pdf')

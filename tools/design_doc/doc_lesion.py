"""CAG 所見・PCI 病変形態・所見（Findings）の整理（標準定義との対応と改善案）"""
from extra_common import G, e, table, build_doc, RELATED

SRC = [
    ('AHA 冠動脈セグメント分類', 'AHA 報告システム（Austen ら, Circulation 1975）', 'セグメント #1〜#15、狭窄度 25/50/75/90/99/100%（視覚的評価）。国内の CAG 報告の基本'),
    ('J-PCI', 'CVIT J-PCI CRF 記入の手引き 第12.00版（2024年1月1日）、J-PCI 定義', '病変番号（#1〜#15・HL・4AV・4PD・グラフト）、病変性状（新規/再狭窄/不詳）、成否、使用機器、病変枝数、病変成功・合併症の定義'),
    ('JCS 標準（SEAMAT）', 'JCS データ出力標準フォーマット ガイドライン V1.2（2025年7月）、JAHIS 心臓カテーテル検査レポート構造化記述規約 Ver.1.0', '心カテレポートの構成（検査情報・CAG・PCI）。PCI は処置部位ごとに 部位・術前/術後狭窄度・術前/術後 TIMI・病変分類・成否・使用機器'),
    ('ACC/AHA 病変分類', 'ACC/AHA Task Force（Type A/B1/B2/C）', '病変長・偏心性・屈曲・蛇行・石灰化・閉塞期間・入口部・分岐部・血栓などの特徴で分類'),
    ('SYNTAX スコア', 'SYNTAX Score 定義（syntaxscore.org）', '重度石灰化・血栓・入口部（3mm 以内）・高度蛇行・病変長 >20mm・分岐部（Medina）などの定義'),
    ('J-CTO スコア', 'J-CTO Registry', 'CTO の難易度：Blunt 入口・石灰化・屈曲 >45°・閉塞長 ≥20mm・再挑戦（各1点、0〜5点）'),
    ('TIMI 分類', 'TIMI Study Group', '冠血流（TIMI flow grade 0〜3）、血栓量（TIMI thrombus grade 0〜5）'),
    ('ISR 分類', 'Mehran 分類（1999）', 'ステント内再狭窄のパターン I〜IV'),
    ('分岐部', 'Medina 分類（European Bifurcation Club）', '近位本幹・遠位本幹・側枝の有意狭窄を 1/0 の3桁で表す'),
]

SEG = [
    ('RCA', '#1', 'RCA1', '右冠動脈 近位部（入口〜右室枝）'), ('', '#2', 'RCA2', '右冠動脈 中間部（〜鋭縁枝）'),
    ('', '#3', 'RCA3', '右冠動脈 遠位部（〜後下行枝分岐）'), ('', '#4AV', 'RCA4AV', '房室結節枝'), ('', '#4PD', 'RCA4PD', '後下行枝'),
    ('LMT', '#5', 'LMT5', '左主幹部'),
    ('LAD', '#6', 'LAD6', '前下行枝 近位部（〜第1中隔枝）'), ('', '#7', 'LAD7', '前下行枝 中間部（〜第2対角枝）'), ('', '#8', 'LAD8', '前下行枝 遠位部'),
    ('', '#9', 'LAD9', '第1対角枝'), ('', '#10', 'LAD10', '第2対角枝'),
    ('LCX', '#11', 'LCX11', '回旋枝 近位部（〜鈍縁枝）'), ('', 'HL', 'HL', '高位側壁枝（中間枝）'), ('', '#12', 'LCX12', '鈍縁枝'),
    ('', '#13', 'LCX13', '回旋枝 遠位部（鈍縁枝以降）'), ('', '#14', 'LCX14', '後側壁枝'), ('', '#15', 'LCX15', '後下行枝（左優位の場合）'),
]

STEN = [
    ('Normal', '0%', '狭窄なし', '－'),
    ('Irregular', '<25%', '壁不整のみ（有意でない）', '－'),
    ('25', '1〜25%', '軽度', '－'),
    ('50', '26〜50%', '中等度', '－'),
    ('75', '51〜75%', '有意狭窄の下限（J-PCI：AHA 75%＝実測 50% 以上を有意）', '有意（ピンク）'),
    ('90', '76〜90%', '高度', '有意'),
    ('99', '91〜99%', '亜完全閉塞。造影遅延の有無で 99%・99%（delay）に分ける方法もある', '有意'),
    ('100', '100%', '完全閉塞（TIMI 0）', '有意'),
]

# 病変形態：(項目, 現在の画面・データ, 標準の定義, 標準の区分, ACC/AHA での扱い, 提案)
MORPH = [
    ('病変長（Length）', 'Length：mm（lengthA）＋区分 <10mm／10-20mm／>20mm（lengthB、手入力）',
     '最も長く見える投影で、近位肩から遠位肩までの長さ（SYNTAX は ≥50% 狭窄部分の長さ）',
     'Discrete <10mm／Tubular 10〜20mm／Diffuse >20mm', 'A：<10mm、B：10〜20mm、C：>20mm', '区分は mm から自動で表示（手入力をやめる）'),
    ('偏心性（Eccentricity）', 'Yes／No', '内腔が血管の中心からずれている（片側性のプラーク）', '有／無', 'B の特徴', '現状どおり'),
    ('屈曲（Angulation）', '<45°／45-90°／>90°', '病変部の血管の曲がり', '<45°／45〜90°／>90°', 'A：<45°、B：45〜90°、C：>90°', '現状どおり（ACC/AHA と一致）'),
    ('近位部の蛇行（Proximal tortuosity）', 'None／Moderate／Severe',
     '病変より近位の蛇行。SYNTAX の高度蛇行：≥90° の屈曲1つ以上、または 45〜90° の屈曲3つ以上', 'なし／中等度／高度（excessive）', 'B：中等度、C：高度', '「Severe」の判定基準（SYNTAX）を画面に表示'),
    ('不整（Irregular）', 'Yes／No', '病変の輪郭が平滑でない（潰瘍・内膜片・鋸歯状を含む）', '有／無', 'B の特徴', '現状どおり'),
    ('石灰化（Calcification）', 'Yes／No（CAG はセグメントごとに□）',
     '透視で見える血管壁の不透過像。SYNTAX の重度：複数の投影で病変部の全周を囲む', 'なし／軽度／中等度／高度（重度）', 'B：中等度〜高度', '「なし・軽度・中等度・高度」の4段階に（J-CTO は有無、SYNTAX は高度を使う）'),
    ('血栓（Thrombus）', 'Yes／No',
     '3方向を造影剤に囲まれた内腔の陰影欠損（複数の投影）、または末梢への塞栓', 'TIMI thrombus grade 0〜5', 'B の特徴', 'TIMI thrombus grade（0〜5）で記録。有無は grade ≥2 から自動'),
    ('完全閉塞（CTO・Age of occlusion）', 'CTO：Yes／No、Age of Occlusion（自由入力）',
     'CTO：TIMI 0 で閉塞期間が3か月以上または不明（JCS 安定冠動脈疾患の血行再建ガイドライン）', '閉塞期間 <3か月／≥3か月／不明', 'B：<3か月、C：>3か月（または bridging collateral）', '閉塞期間を3区分の選択に。CTO なら J-CTO の5項目を病変ごとに入力（スコア自動計算）'),
    ('入口部（Ostial）', 'Yes／No', '冠動脈の起始部から 3mm 以内の病変（Aorto-ostial、SYNTAX）。分枝入口部と区別', '大動脈入口部／分枝入口部／なし', 'B の特徴', '「大動脈入口部」と「分枝入口部」を分ける'),
    ('分岐部（Bifurcation）', 'Yes／No、Branch Protection（自由入力）、Bif/CTO タブ：Main/Side branch（Medina 1,1,1 などを候補から入力）・Main/Side branch の血管',
     '親血管が 1.5mm 以上の2本に分かれる部位の病変。Medina：近位本幹・遠位本幹・側枝の ≥50% 狭窄を 1/0 で表す', 'Medina 1,1,1 など（7通り）', 'B：2本のワイヤーが必要、C：側枝を保護できない', 'Medina を候補入力から選択式にし、病変形態の Bifurcation（有無）と連動。側枝の径も記録'),
    ('解離（Dissection）', 'Yes／No', '造影上の内膜亀裂・偽腔（術前は自然解離、術後は NHLBI 分類 A〜F が一般的）', '術前：有無、術後：Type A〜F', '－', '術前と術後を分け、術後は Type A〜F'),
    ('Haziness', 'Yes／No', '病変部の造影剤の淡い濃度（血栓・石灰化・解離などが疑われる）', '有／無', '－', '現状どおり'),
    ('病変性状（de novo・再狭窄）', '大分類：de novo／restenosis／ISR／graft、小分類：focal／diffuse／proliferative／occlusive／edge',
     'J-PCI：新規／再狭窄／不詳。ISR は Mehran 分類（I 限局 ≤10mm、II びまん性・ステント内、III びまん性・ステント外に及ぶ、IV 閉塞）', 'J-PCI 3区分＋ISR パターン I〜IV',
     '－', '小分類を Mehran I〜IV と対応づけ（focal＝I、diffuse＝II、proliferative＝III、occlusive＝IV、edge は I の端部）。J-PCI へは自動変換'),
]

ACC = [
    ('病変長', '<10mm（Discrete）', '10〜20mm（Tubular）', '>20mm（Diffuse）'),
    ('偏心性', '同心性', '偏心性', '－'),
    ('到達性・近位部の蛇行', '到達容易', '中等度の蛇行', '高度の蛇行'),
    ('屈曲', '<45°', '45〜90°', '>90°'),
    ('輪郭', '平滑', '不整', '－'),
    ('石灰化', 'なし〜軽度', '中等度〜高度', '－'),
    ('閉塞', '完全閉塞でない', '完全閉塞 <3か月', '完全閉塞 >3か月'),
    ('入口部', '入口部でない', '入口部', '－'),
    ('分岐部', '主要分枝の関与なし', '2本のガイドワイヤーが必要', '主要側枝を保護できない'),
    ('血栓', 'なし', 'あり', '－'),
    ('グラフト', '－', '－', '脆弱な病変を伴う変性静脈グラフト'),
]

RESULT = [
    ('Pre／Post Ref・%DS・MLD', '数値（mm・%・mm）。Pressure/IVUS の QCA から取得可', 'JCS：Stenosis_Pre／Stenosis_Post（処置部位ごと）', 'QCA：参照血管径・狭窄率（径）・最小内腔径', '現状どおり。目視の狭窄度（AHA）も別に持つ'),
    ('TIMI（Pre／Post）', '0〜3（基本タブの病変表）', 'JCS：TimiGrade_Pre／TimiGrade_Post', '0：順行性血流なし、1：通過するが末梢まで造影されない、2：末梢まで造影されるが遅い、3：正常', '現状どおり（定義を画面に表示）'),
    ('成否（Success）', 'Success／Partial success／Failure', 'J-PCI：成功／不成功／不明。JCS：実施成否', '病変成功：術後の目視狭窄 ≤25% かつ TIMI 3（J-PCI）', 'Post 狭窄度と TIMI から「病変成功」を自動判定して提案'),
    ('使用機器', 'Device タブ（Balloon・NC・Scoring・Cutting・DES・BMS・DCB・Rota・OAS・IVL・DCA・Aspiration・Filter）', 'J-PCI：バルーンのみ・薬剤溶出バルーン・金属ステント・DES・ロータブレーター・アテレクトミー（DiamondBack）・ELCA・DCA・IVL・BRS・血栓吸引・遠位部保護・ワイヤー/デバイス不通過', '－', 'カテゴリを J-PCI の区分に対応づけ（ELCA・BRS・不通過を追加）'),
    ('最終造影所見（Final angiographic result）', 'Complication タブ：Slow/No flow・末梢塞栓・Abrupt closure・術前より悪化・ステント血栓症', '－', 'Slow flow／No reflow は TIMI ≤2、Abrupt closure は術中の急性閉塞', 'TIMI Post と矛盾しないよう連動チェック'),
    ('手技に伴う合併症', 'Complication タブ：残存解離・穿孔・ステント脱落・側枝閉塞 ほか', 'J-PCI：院内死亡・PCI 手技による心筋梗塞・心タンポナーデ・補助循環/強心薬を要する心不全/ショック・ステント血栓症（院内、ARC definite）・緊急手術・輸血を要する出血', '穿孔は Ellis 分類（I〜III）が一般的', '穿孔に Ellis 分類を追加。J-PCI の合併症へ対応づけ'),
    ('側副血行', 'Collaterals：From → To、J（Grade）、State', '－', 'Rentrop 0：なし、1：側枝のみ、2：本幹の一部、3：本幹全体が造影', 'Grade を Rentrop 0〜3 の選択に'),
]

GAPS = [
    ('高', 'CTO の詳細', 'CTO は有無と Age of Occlusion（自由入力）のみ。J-CTO スコアは PCI 全体で1欄', '病変ごとに閉塞期間（<3か月／≥3か月／不明）と J-CTO 5項目（Blunt・石灰化・屈曲>45°・閉塞長≥20mm・再挑戦）を入力し、スコアを自動計算'),
    ('高', 'ACC/AHA Type の自動判定', 'Type（A/B1/B2/C）を手入力。各特徴の入力と食い違うことがある', '病変長・屈曲・蛇行・石灰化・閉塞・入口部・分岐部・血栓・偏心・不整から Type を自動提案（手修正は可）'),
    ('高', '病変成功の自動判定', '成否を手入力', '術後の目視狭窄 ≤25% かつ TIMI 3 で「成功」を提案（J-PCI の定義）。食い違いは警告'),
    ('中', '石灰化・血栓の段階', 'Yes／No のみ', '石灰化：なし／軽度／中等度／高度、血栓：TIMI thrombus grade 0〜5'),
    ('低', '病変長の区分', 'mm と区分（<10／10-20／>20mm）を別々に手入力（食い違いうる）', '区分は mm から自動表示'),
    ('中', '分岐部（Medina）', 'Medina は Bif/CTO タブの候補入力（自由入力も可）。病変形態の Bifurcation（有無）とは連動しない', 'Medina を選択式にし、Bifurcation「Yes」と連動。側枝の径・角度も'),
    ('中', 'J-PCI 病変番号との対応', 'Target は自由入力（例 #6）。グラフト病変の番号がない', 'Target を CAG のセグメント（#1〜#15・HL・4AV・4PD）＋グラフト（SVG/AG ×LAD/LCX/RCA）＋その他から選択'),
    ('中', 'J-PCI への変換', '病変性状（大分類・小分類）・使用機器の区分が J-PCI と違う', '新規／再狭窄／不詳、使用機器の区分へ自動変換する表を持つ（ISR は Mehran I〜IV も記録）'),
    ('低', '99% の造影遅延', '99 のみ', '99%（delay）を選べるようにする（AHA 7段階での運用）'),
    ('低', '入口部の種類', 'Ostial は有無のみ', '大動脈入口部（3mm 以内）と分枝入口部を分ける'),
    ('低', '術後の解離・穿孔の分類', '有無のみ', '解離：NHLBI Type A〜F、穿孔：Ellis I〜III'),
    ('低', '側副血行の Grade', 'J（Grade）は自由入力', 'Rentrop 0〜3 を選択'),
]


def p_overview():
    return ('<h1>1. 概要</h1>'
            '<p class="lead">CAG の所見（セグメントごとの狭窄度など）、PCI の病変形態（術前の病変の特徴）、PCI の結果（術後の所見・成否・合併症）について、'
            '現在の画面（参考画面イメージ・アプリ）の項目を、国内外の標準の定義と突き合わせて整理しました。</p>'
            '<h2>参照した基準</h2>' + table(['基準', '出典', '本資料で使う内容'], [((a, 'k'), (b, 'small'), c) for a, b, c in SRC], widths=['30mm', '56mm', None]) +
            '<h2>データの単位</h2>' +
            table(['単位', '内容', '画面'], [
                ('セグメント（CAG）', 'AHA の #1〜#15 ごとの狭窄度と付帯所見。患者の冠動脈全体の状態', 'CAG/LVG（CAG タブ）'),
                ('病変（PCI）', '治療した病変ごと（最大5）の位置・形態・術前後の所見・使用機器・成否', 'PCI（基本・病変形態・Device・Bif/CTO・Complication）'),
                ('手技・患者（PCI）', '手技全体の成否・合併症、患者の合併症、J-PCI の登録項目', 'PCI（基本・J-PCI・Complication）'),
            ], widths=['32mm', None, '56mm']) +
            '<div class="note">JCS の標準（SEAMAT・JAHIS 規約）は、心カテレポートを「検査情報」「CAG」「PCI」の3つに分け、PCI は処置部位ごとに '
            '部位・術前/術後の狭窄度・術前/術後の TIMI・病変分類・成否・使用機器を持つ構成です。本アプリの「CAG のセグメント表」と「PCI の病変（最大5）」はこの構成に対応しています。'
            '病変形態の詳しい区分（石灰化の程度など）は JCS・J-PCI では定めていないため、ACC/AHA・SYNTAX・J-CTO・TIMI の定義を使います。</div>')


def p_cag():
    return ('<h1>2. CAG の所見</h1><h2>2.1 セグメント（AHA 分類）</h2>' +
            table(['枝', 'AHA', 'アプリのキー', '部位'], [((a, 'k'), (b, 'c'), (c, 'code'), d) for a, b, c, d in SEG], widths=['14mm', '16mm', '26mm', None]) +
            '<p class="small">J-PCI の病変番号は上記に加え、グラフト（SVG・AG それぞれ LAD／LCX／RCA への吻合）と「その他」がある。SYNTAX では 12a/12b・14a/14b・16 などの細分も使う。</p>'
            '<h2>2.2 狭窄度（視覚的評価）</h2>' +
            table(['画面の値', '狭窄の範囲', '意味', '有意'], [((a, 'k c'), (b, 'c'), c, (d, 'c')) for a, b, c, d in STEN], widths=['20mm', '22mm', None, '22mm']) +
            '<p class="small">AHA 分類の 75% は 51〜75% を指す。J-PCI は「AHA 分類 75%（実測 50%）以上」を有意狭窄とし、病変枝数を数える。</p>'
            '<h2>2.3 セグメントの付帯所見と CAG 全体の項目</h2>' +
            table(['項目', '現在の画面', '定義・選択肢（提案を含む）'], [
                ('血管のサイズ', 'Large／Small／Absent', '治療対象となる太さか（SYNTAX は 1.5mm 以上を対象）。Absent は分枝が存在しない'),
                ('Calcification', '□（有無）', 'セグメントの石灰化。病変形態と同じ4段階にそろえる案'),
                ('Diffuse／Segmental', '□', 'びまん性（セグメントの大部分）／限局性。SYNTAX の「びまん性病変・細小血管」は区間の 75% 以上で径が小さいもの'),
                ('Undefined', '□', '造影で評価できない（重なり・描出不良）'),
                ('Jeopardy', '□', '灌流域の広い危険な病変（側副血行の供給源など）'),
                ('Graftable', '□', 'バイパス吻合が可能な血管'),
                ('Dominance', 'Right／Left／Balanced（CAG タブ。Pressure/IVUS にも Dominancy 欄）', '後下行枝が RCA（#4）由来なら右優位、LCX（#15）由来なら左優位。SYNTAX は Balanced を使わない'),
                ('病変枝数・LMT', '数＋LMT/LAD/LCX/RCA（「病変枝」ボタンで算出）', 'J-PCI：AHA 75% 以上の有意狭窄がある主要冠動脈の数＋主幹部。LMT 病変は LAD・LCX の2枝に数える'),
                ('Collaterals', 'From → To、J（Grade）、State', 'Rentrop 0〜3 を Grade に'),
                ('Bypass Grafts', 'グラフト → 吻合先、開存', 'Patent／Stenosis／Occluded／String sign'),
                ('Squeezing・Spasm', '－／＋、Provocation of Spasm', '心筋ブリッジによる収縮期の圧排／攣縮（誘発薬：アセチルコリン・エルゴノビン）'),
                ('スコア', 'Syntax・Euro・Japan Score', 'SYNTAX は病変の特徴の合計、Euro（EuroSCORE II）・Japan（JapanSCORE）は手術リスク'),
            ], widths=['30mm', '46mm', None]))


def p_morph():
    blocks = ''.join(
        f'<div style="page-break-inside:avoid"><h3>3.{i} {e(a)}</h3>' +
        table(['', ''], [('現在の画面', b), ('標準の定義', c), ('標準の区分', d), ('ACC/AHA', f), ('提案', f'<b>{e(g)}</b>')], cls='kvb', widths=['28mm', None], raw=False)
        .replace('&lt;b&gt;', '<b>').replace('&lt;/b&gt;', '</b>') + '</div>'
        for i, (a, b, c, d, f, g) in enumerate(MORPH, 1))
    return ('<h1>3. PCI の病変形態（術前）</h1>'
            '<p class="lead">病変形態タブの項目（病変ごと、最大5）について、現在の画面・標準の定義と区分・ACC/AHA での扱い・提案をまとめます。</p>' + blocks)


def p_acc():
    return ('<h1>4. ACC/AHA 病変分類（Type A／B1／B2／C）</h1>'
            '<p class="lead">Type は病変形態の各特徴から決まります。B の特徴が1つなら B1、2つ以上なら B2、C の特徴が1つでもあれば C です。</p>' +
            table(['特徴', 'Type A', 'Type B', 'Type C'], [((a, 'k'), b, c, d) for a, b, c, d in ACC], widths=['32mm', None, None, None]) +
            '<h2>自動判定の案</h2>' +
            table(['手順', '内容'], [
                ('1', 'C の特徴（病変長 >20mm・高度蛇行・屈曲 >90°・閉塞 >3か月・側枝保護不能・変性グラフト）が1つでもあれば C'),
                ('2', 'B の特徴（10〜20mm・偏心・中等度蛇行・屈曲 45〜90°・不整・中等度以上の石灰化・閉塞 <3か月・入口部・分岐部で2本のワイヤー・血栓）を数え、2つ以上なら B2、1つなら B1'),
                ('3', 'どれにも当たらなければ A'),
                ('4', '判定結果を Type 欄に提案し、医師が確定（手で変更した場合は印を付ける）'),
            ], widths=['14mm', None]))


def p_result():
    blocks = ''.join(
        f'<div style="page-break-inside:avoid"><h3>5.{i} {e(a)}</h3>' +
        table(['', ''], [('現在の画面', b), ('J-PCI・JCS', c), ('定義', d), ('提案', f'<b>{e(f)}</b>')], cls='kvb', widths=['28mm', None])
        .replace('&lt;b&gt;', '<b>').replace('&lt;/b&gt;', '</b>') + '</div>'
        for i, (a, b, c, d, f) in enumerate(RESULT, 1))
    return ('<h1>5. PCI の結果・所見（Findings）</h1>' + blocks +
            '<h2>5.8 TIMI 分類</h2>' +

            table(['Grade', 'TIMI flow（冠血流）', 'TIMI thrombus（血栓量）'], [
                ('0', '閉塞部より先に順行性の血流がない', '血栓の所見なし'),
                ('1', '造影剤は閉塞部を通過するが、末梢まで造影されない', '血栓の可能性（濃度低下・不整・閉塞部の凸面など）'),
                ('2', '末梢まで造影されるが、流入・排出が正常部より遅い', '明らかな血栓、最大径が血管径の 1/2 以下'),
                ('3', '正常な速さで末梢まで造影される', '明らかな血栓、血管径の 1/2〜2 倍'),
                ('4', '－', '明らかな大きな血栓、血管径の 2 倍以上'),
                ('5', '－', '血栓による完全閉塞'),
            ], widths=['16mm', None, None]))


def p_gap():
    pri = {'高': '<span class="pri 高">高</span>', '中': '<span class="pri 中">中</span>', '低': '<span class="pri 低">低</span>'}
    return ('<h1>6. 現状とのギャップ・改善案</h1>'
            '<p class="lead">参考画面の項目はおおむね標準の項目を網羅しています。差は主に「区分の細かさ」「自動判定」「J-PCI への変換」です。</p>' +
            table(['優先', '対象', '現状', '改善案'], [((pri[p], 'c'), (a, 'k'), b, c) for p, a, b, c in GAPS], widths=['11mm', '32mm', '56mm', None], raw=True) +
            '<h2>データモデルの変更案（PciLesion への追加）</h2>' +
            table(['項目（案）', '型・値', '用途'], [
                (('calcGrade', 'code'), 'none／mild／moderate／severe', '石灰化の程度'),
                (('thrombusGrade', 'code'), '0〜5', 'TIMI thrombus grade'),
                (('ostialType', 'code'), 'none／aorto／branch', '入口部の種類'),
                (('bif.mainSide', 'code'), '既存。"Medina 1,1,1" など7通りに限定', '分岐部の Medina 分類（選択式に変更）'),
                (('cto', 'code'), '{ duration: <3m／≥3m／unknown, blunt, calc, bend45, len20, retry }', '閉塞期間と J-CTO 5項目（スコアは計算）'),
                (('isrPattern', 'code'), 'I／II／III／IV', 'Mehran 分類'),
                (('accAha', 'code'), '{ suggested, confirmed, overridden }', 'Type の自動提案と確定値'),
                (('jpci', 'code'), '{ lesionNo, character: 新規／再狭窄／不詳, success, devices[] }', 'J-PCI へ出力する値（変換表で自動作成）'),
            ], widths=['32mm', '66mm', None]) +
            '<div class="note">既存の項目（Yes/No など）は残し、新しい項目は旧データでは空（未入力）として扱います（normalizeReport の補完と同じ方針）。'
            'J-PCI・JCS（SEAMAT）への出力は、画面の入力から変換表で作る方式にすると、画面の使い勝手と登録の正確さを両立できます。</div>')


PARTS = [
    ('ov', 1, '1. 概要（参照した基準・データの単位）', p_overview),
    ('cag', 1, '2. CAG の所見（セグメント・狭窄度・付帯所見）', p_cag),
    ('morph', 1, '3. PCI の病変形態（術前）', p_morph),
    ('acc', 1, '4. ACC/AHA 病変分類と自動判定の案', p_acc),
    ('res', 1, '5. PCI の結果・所見（TIMI・成否・合併症）', p_result),
    ('gap', 1, '6. 現状とのギャップ・改善案', p_gap),
]

if __name__ == '__main__':
    build_doc('CAG・PCI 病変形態・所見の整理', 'AHA 分類・J-PCI・JCS（SEAMAT/JAHIS）・ACC/AHA・SYNTAX・J-CTO・TIMI との対応と改善案',
              '参考画面イメージ（CAG・PCI 病変形態ほか）とアプリの CAG/LVG・PCI 画面', RELATED, PARTS, G.ROOT / 'docs/design/cag_pci_lesion_findings.pdf')

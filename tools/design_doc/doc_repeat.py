"""繰り返し項目の仕組みと実装詳細（React 版・Thymeleaf 版）
usage: python3 tools/design_doc/doc_repeat.py
"""
import subprocess
from extra_common import G, e, table, build_doc, RELATED

IMG = G.ROOT / 'docs/design/img'
SHOT = G.ROOT / 'demo/screenshots'
FONT = 'Noto Sans CJK JP'


def dot(name, src):
    subprocess.run(['dot', '-Tsvg', '-o', str(IMG / f'{name}.svg')], input=src.encode('utf-8'), check=True)


def fig(name, cap, h='90mm'):
    return (f'<div class="fig"><img src="{(IMG / (name + ".svg")).as_uri()}" style="width:100%;max-height:{h};object-fit:contain"></div>'
            f'<p class="cap">{e(cap)}</p>')


CROP = G.ROOT / 'docs/design/img/crops'


def shot(fn, cap, w='100%'):
    return (f'<div class="fig"><img src="{(CROP / fn).as_uri()}" style="width:{w};border:1px solid #c9d3d6"></div>'
            f'<p class="cap">{e(cap)}</p>')


def code(s):
    return f'<div class="tree">{e(s.strip(chr(10)))}</div>'


ITEMS = [
    ('CAG/LVG', 'Collaterals（側副血行）', 'cagLvg.cag.collaterals', '行', '5', '「なし」の時は追加・削除不可'),
    ('CAG/LVG', 'Bypass Grafts', 'cagLvg.cag.grafts', '行', '4', ''),
    ('PCI 基本', 'ガイディングカテーテル', 'pci.basic.guiding', '行', '5', '名称＋サイズ'),
    ('PCI 基本', 'マイクロカテーテル', 'pci.basic.micro', '行', '4', '文字列の配列'),
    ('PCI 基本', 'ガイドワイヤー', 'pci.basic.gw', '行', '5', '文字列の配列。旧データは 10 まで'),
    ('PCI（全タブ）', 'Target（病変）', 'pci.lesions', '列', '5', '全タブ・J-PCI・検索用・基本の病変単位治療が同じ数'),
    ('Pressure/IVUS', 'Pressure Wire の病変', 'pressureIvus.pressure', '列', '5', 'IVUS の Lesion タブと連動（lesions と同じ数）'),
]

RULES = [
    ('表示する数', '入力済みの最後の行（列）まで。最低 1。新規レポートは 1 から始まる'),
    ('追加', '「＋ 追加」で末尾に空の行（列）を 1 つ足す。ボタンに「件数/最大」を表示し、最大数で押せなくなる'),
    ('削除', '「✖」でその行（列）を取り除き、後ろを前に詰める。入力がある時は確認ダイアログ。最後の 1 行は取り除かずに入力をクリア'),
    ('連動', 'Pressure Wire の病変 N と IVUS の Lesion N は一緒に追加・削除（どちらの画面からでも）'),
    ('入力不可の時', '確定済み・閲覧のみの権限・Collaterals「なし」の時は、追加・削除のボタンも押せない'),
    ('旧データ', '末尾の空の要素は表示しない。途中の空は残す（病変番号を変えない）。最大数を超えて入力済みのデータは消さずに表示し、追加だけできなくする'),
    ('保存', '変更として保存する（未保存の赤ボタン・画面移動時の確認の対象）'),
]


def make_figs():
    dot('rep_react', f'''digraph G {{
  graph [rankdir=TB, fontname="{FONT}", nodesep=0.35, ranksep=0.35, bgcolor="transparent"];
  node [shape=box, style="rounded,filled", fontname="{FONT}", fontsize=15, fillcolor="#e6f0fa", color="#5b84b1", margin="0.14,0.08"];
  edge [fontname="{FONT}", fontsize=11, color="#5b6f75", fontcolor="#44585e"];
  load [label="読込\\nnormalizeReport", fillcolor="#f1f1f1", color="#999999"];
  fit [label="fitLists / fitPair\\n末尾の空を除く・最低1\\n各要素を既定値で補う"];
  arr [label="配列（可変長）\\nreport.pci.lesions など", shape=note, fillcolor="#fffaf2", color="#d8a25e"];
  ui [label="画面\\nuseCount → range(n)\\n行・列を n 個描く"];
  btn [label="AddRowBtn / DelRowBtn\\n（linked で連動配列も）"];
  set [label="form.set / setMany\\n配列ごと置き換え"];
  save [label="保存\\n配列のまま JSON で送る", fillcolor="#f1f1f1", color="#999999"];
  {{ rank=same; load; fit; arr; save; }}
  {{ rank=same; ui; btn; set; }}
  load -> fit -> arr;
  arr -> save [style=dashed];
  arr -> ui -> btn -> set;
  set -> arr [label="配列を置き換え"];
}}''')
    dot('rep_tl', f'''digraph G {{
  graph [rankdir=TB, fontname="{FONT}", nodesep=0.35, ranksep=0.35, bgcolor="transparent"];
  node [shape=box, style="rounded,filled", fontname="{FONT}", fontsize=15, fillcolor="#fdf1e2", color="#d8a25e", margin="0.14,0.08"];
  edge [fontname="{FONT}", fontsize=11, color="#5b6f75", fontcolor="#44585e"];
  tpl [label="テンプレート\\n最大数ぶんの入力欄\\n（data-path=…N…）", fillcolor="#f1f1f1", color="#999999"];
  setup [label="setupRepeat\\ndata-path から行・列・タブを見つけ\\nボタンを差し込む"];
  cnt [label="表示数 n\\n入力済みの最後まで\\n（画面の値＋CTX）"];
  paint [label="paintRepeat\\nn 以降を隠す\\nボタンの有効・件数"];
  act [label="rep-add / rep-del\\n削除は値を前へ移す\\n（まとめて書き込み）"];
  save [label="保存\\n変更したパスだけ送る", fillcolor="#f1f1f1", color="#999999"];
  {{ rank=same; tpl; setup; cnt; }}
  {{ rank=same; paint; act; save; }}
  tpl -> setup -> cnt;
  cnt -> paint;
  paint -> act [label="ボタン"];
  act -> paint [label="再表示"];
  act -> save [style=dashed];
}}''')
    dot('rep_link', f'''digraph G {{
  graph [rankdir=LR, fontname="{FONT}", nodesep=0.4, ranksep=1.6, bgcolor="transparent"];
  node [shape=record, style="filled", fontname="{FONT}", fontsize=15, fillcolor="#f3e8f7", color="#9b6bb3"];
  edge [fontname="{FONT}", fontsize=11, color="#2b6cb0", fontcolor="#2b6cb0", dir=both];
  pw [label="pressure[ ]\\nPressure Wire|0: LCX#13|1: LAD#6|2: …"];
  iv [label="lesions[ ]\\nIVUS Lesion タブ|0: pre / post|1: pre / post|2: …"];
  pw -> iv [label="同じ番号 N・同じ数\\n追加・削除も一緒\\n病変名は pressure[N].lesion を共有"];
}}''')


def p_overview():
    return ('<h1>1. 概要</h1>'
            '<p class="lead">繰り返し項目は、行（または列）の数を入力に合わせて増減でき、最大数までしか追加できない項目です。'
            'React 版と Thymeleaf 版で同じ動きにしていますが、作り方は違います（React はデータの配列の数だけ描く、Thymeleaf は最大数ぶんの欄を持ち、使う数だけ見せる）。</p>' +
            table(['画面', '項目', 'データ', '並び', '最大', '補足'], [((a, 'k'), b, (c, 'code small'), d, (f, 'c'), (g, 'small')) for a, b, c, d, f, g in ITEMS],
                  widths=['24mm', '36mm', '44mm', '10mm', '10mm', None]) +
            '<h2>1.1 動きの決まり（両版共通）</h2>' +
            table(['決まり', '内容'], [((a, 'k'), b) for a, b in RULES], widths=['26mm', None]) +
            shot('rep_cag.png', 'CAG：Collaterals・Bypass Grafts（各行の ✖ と「＋ 追加 件数/最大」）', '85%'))


def p_model():
    return ('<h1>2. データの持ち方</h1>'
            '<p>繰り返し項目はレポートの中の<b>配列</b>です。配列の長さ＝使っている行（列）の数で、最大数は定数で決めています。</p>' +
            code('''
// frontend/src/model/defaults.ts
export const LIST_MAX = { collaterals: 5, grafts: 4, guiding: 5, micro: 4, gw: 5, lesions: 5, pressure: 5 } as const;

// 新規レポートは各 1 件から
cag: { ..., collaterals: [createCollateral()], grafts: [createGraft()] }
pci: { basic: { guiding: [createGuiding()], micro: [''], gw: [''] }, lesions: [createPciLesion()] }
pressureIvus: { pressure: [createPressureCol()], lesions: [createIvusLesion()] }
''') +
            '<h2>2.1 読込時の整形（旧データ・サーバーのデータ）</h2>'
            '<p>以前は固定長（側副血行 5・グラフト 4・GW 10・病変 5・Pressure 3・IVUS 4）で保存していたため、読み込む時に可変長へ整えます。</p>' +
            code('''
export function fitList<T>(src: unknown, create: () => T): T[] {
  const arr = Array.isArray(src) ? src.map((x) => mergeDefaults(create(), x)) : [];  // 各要素を既定値で補う
  let n = arr.length;
  while (n > 0 && !hasAnyValue(arr[n - 1])) n--;                                     // 末尾の空を除く
  return n === 0 ? [create()] : arr.slice(0, n);                                      // 最低 1 件
}
// Pressure Wire と IVUS は fitPair で同じ数にそろえる（末尾の「両方とも空」を除く）
''') +
            table(['ポイント', '内容'], [
                (('途中の空は残す', 'k'), '病変 2 が空で病変 3 に入力がある時、病変 3 を 2 に詰めると番号が変わってしまうため'),
                (('最大数を超えたデータ', 'k'), '消さない（ガイドワイヤーの 6 本目以降など）。表示はするが追加できない'),
                (('既定値で補う', 'k'), '旧データの要素に無い項目（新しく増えた項目）も、空の値で必ず持つ'),
                (('病変名の一本化', 'k'), 'Pressure Wire の lesion が空で IVUS の site だけある旧データは、site を lesion へ移す（食い違う時は Pressure Wire 優先）'),
            ], widths=['32mm', None]))


def p_react():
    return ('<h1>3. React 版の実装</h1>' + fig('rep_react', 'React 版：配列の数だけ描き、ボタンで配列を置き換える', '62mm') +
            shot('rep_lesion.png', 'PCI 病変形態：病変（Target）の列。見出しの ✖ と「＋ 病変 件数/最大」', '75%') +
            '<h2>3.1 部品（frontend/src/form/repeat.tsx）</h2>' +
            table(['部品', '役割'], [
                (('AddRowBtn', 'code'), '末尾に create() の要素を足す。件数/最大を表示。最大数・入力不可（readOnly）・disabled で押せない'),
                (('DelRowBtn', 'code'), 'index の要素を取り除く（最後の 1 件は create() で置き換え＝クリア）。入力がある時は app.confirm で確認。text を渡すと文字のボタン'),
                (('linked', 'code'), '連動する配列（{ path, create }[]）。追加・削除の時に同じ番号の要素を一緒に足す・消す。form.setMany で 1 回の変更にまとめる'),
                (('useCount / range', 'code'), '表示する数（配列の長さ、最低 1）と、0..n-1 の番号の配列'),
            ], widths=['32mm', None]) +
            '<h2>3.2 画面での使い方</h2>' +
            code('''
// CAG：側副血行（行）
const n = useCount('collaterals');
{range(n).map((i) => (
  <div className="route-row" key={i}>
    <TextF path={`collaterals.${i}.from`} … />  →  <TextF path={`collaterals.${i}.to`} … /> …
    <DelRowBtn path="collaterals" index={i} create={createCollateral} what="側副血行" disabled={none} />
  </div>
))}
<AddRowBtn path="collaterals" max={LIST_MAX.collaterals} create={createCollateral} label="側副血行を追加" disabled={none} />

// Pressure Wire（列）：IVUS の lesions を連動
<AddRowBtn path="pressure" max={LIST_MAX.pressure} create={createPressureCol}
           linked={[{ path: 'lesions', create: createIvusLesion }]} />
''') +
            table(['画面', '実装の要点'], [
                (('PCI の病変（列）', 'k'), 'LesionGrid が useLesions()（＝range(useCount("lesions"))）で列を描く。見出しの各列に ✖、左上に「＋ 病変」。'
                 '空いた列は lg-empty（透明）で埋めて、列の幅を保つ。J-PCI・検索用・基本の病変単位治療も同じ配列の長さで描く'),
                (('Pressure Wire（列）', 'k'), '列の数だけ描く（表は列数に合わせて伸びる）。先頭の行に「病変 N ✖」と「＋ 病変を追加」'),
                (('IVUS Lesion タブ', 'k'), 'タブは pressure の数だけ（タブ名に病変名）。タブ横に「＋ Lesion」、タブ内に「この病変を削除」。対象部位の入力は /report.pressureIvus.pressure.N.lesion を直接編集'),
                (('見出しの位置', 'k'), 'Collaterals・Bypass Grafts の見出しは、入力行と同じ幅・間隔（4px）で並べ、最後に ✖ ぶんの余白（rh-sp 16px）を置く'),
            ], widths=['32mm', None]))


def p_tl():
    return ('<h1>4. Thymeleaf 版の実装</h1>' + fig('rep_tl', 'Thymeleaf 版：最大数ぶんの欄を持ち、使う数だけ見せる', '62mm') +
            '<p>テンプレートはサーバーで最大数ぶんの入力欄を出力し、<b>static/js/screens.js の「繰り返し項目」</b>（約 200 行）が画面で数を管理します。'
            '行・列は入力欄の data-path（例 report.cagLvg.cag.collaterals.2.from）から見つけるので、テンプレートにはほとんど手を入れていません。</p>' +
            code('''
const REPEATS = [
  { base: 'report.cagLvg.cag.collaterals', max: 5, label: '側副血行を追加', what: '側副血行',
    offBy: 'report.cagLvg.cag.collateralsNone' },            // 「なし」の時は追加・削除不可
  { base: 'report.cagLvg.cag.grafts', max: 4, … },
  { base: 'report.pci.basic.guiding', max: 5, … },
  { base: 'report.pci.basic.micro', max: 4, … },
  { base: 'report.pci.basic.gw', max: 5, … },
  { base: 'report.pci.lesions', max: 5, label: '病変', what: '病変', cols: true },
  { base: 'report.pressureIvus.pressure', linked: ['report.pressureIvus.lesions'], max: 5, cols: true,
    tabs: { add: 'Lesion', del: 'この病変を削除',
            name: (k) => val(`report.pressureIvus.pressure.${k}.lesion`) } },
];
''') +
            '<h2>4.1 処理の流れ</h2>' +
            table(['処理', '内容'], [
                (('setupRepeat（行）', 'code'), '0 行目と 1 行目の入力欄を両方含む最も近い要素をコンテナとし、その直下の要素を 1 行とみなす。各行の末尾に ✖、コンテナの最後に「＋ 追加」を差し込む'),
                (('setupRepeat（列）', 'code'), '入力欄を含む表ごとに、1 行に複数の番号があれば「列の表」として、列の位置 → 番号の対応を作る（病変の表・Pressure Wire）。'
                 '1 行に 1 つの番号なら「行の表」（病変単位治療・J-PCI の病変情報・検索用）。病変の表は見出しに ✖ と「＋ 病変」、Pressure Wire は先頭に操作用の行を足す'),
                (('setupRepeat（タブ）', 'code'), '1 つの番号だけを含むタブのパネル（検索用の病変タブ・IVUS Lesion タブ）のタブボタンも、番号の単位として扱う。tabs 指定がある時は、タブ名・追加・削除ボタンを差し込む'),
                (('表示数 n', 'k'), '入力済みの最後の番号 + 1（最低 1）。画面の値に加え、画面に無い項目も CTX（サーバーから渡したレポート）で確かめる'),
                (('paintRepeat', 'code'), 'n 以降の行・タブは非表示（rep-off）、病変の表の列は visibility:hidden（rep-off-col：幅を保つ）。ボタンの有効・件数・タブ名を更新。'
                 '画面の初期化時と、「なし」・病変名の変更時に呼ぶ（A.hooks）'),
                (('rep-add', 'code'), 'n を 1 増やして表示（欄は最初から空）。新しい行の最初の入力欄へフォーカス'),
                (('rep-del', 'code'), '入力があれば確認（A.confirmDlg）。番号 k+1 以降の値を 1 つ前へ移し、最後を空にして n を 1 減らす。'
                 '値は A.els / A.writeEl でまとめて書き、最後に A.afterChange(null) を 1 回だけ呼ぶ（項目ごとに setVal すると病変では重い）'),
            ], widths=['34mm', None]) +
            '<h2>4.2 テンプレート・サーバー側の変更</h2>' +
            table(['対象', '変更'], [
                (('pressureIvus.html', 'code'), 'Pressure Wire の列を 3 → 5 に増やした。Lesion 5 のタブとパネルを追加。各 Lesion の対象部位の入力を pressure.N.lesion に変更'),
                (('cagLvg.html', 'code'), 'Collaterals・Bypass Grafts の見出しを入力行と同じ幅で並べる形に変更'),
                (('ガイドワイヤー', 'k'), '旧データ用に 10 枠を残し、追加は 5 本まで（入力済みの 6 本目以降は表示される）'),
                (('Clinical.migratePressureIvus', 'code'), '読込時に IVUS の site を Pressure Wire の病変名へ移す（レビュー用 HTML は engine.js の同じ処理）'),
            ], widths=['44mm', None]))


def p_link():
    return ('<h1>5. Pressure Wire と IVUS Lesion の連動</h1>' + fig('rep_link', 'pressure[N] と lesions[N] は同じ病変', '60mm') +
            table(['操作', 'React 版', 'Thymeleaf 版'], [
                (('追加', 'k'), 'AddRowBtn の linked で、pressure と lesions に 1 つずつ足す（setMany）', 'REPEATS の linked で lesions のパスも同じ番号の単位に含める。n を増やすと列とタブが両方出る'),
                (('削除', 'k'), 'DelRowBtn の linked で、両方の配列から同じ番号を取り除く。Lesion タブ側の削除は linked に pressure を指定', '番号 k の単位（列・タブ・パネル）に属する両方のパスの値を前へ移す。確認メッセージに「両方」と表示'),
                (('病変名', 'k'), 'IVUS の対象部位は /report.pressureIvus.pressure.N.lesion を直接表示・編集。タブ名も同じ値', '対象部位の入力欄の data-path を pressure.N.lesion にした（同じパスの欄は app.js が同期）。タブ名は paintRepeat で更新'),
                (('数がずれた旧データ', 'k'), 'fitPair で長い方に合わせ、短い方を空の要素で補う', '表示数は両方のパスで判定するので、どちらかに入力があればその番号まで表示'),
            ], widths=['20mm', None, None]) +
            shot('rep_pw.png', 'Pressure Wire の病変（列）と Lesion タブ（タブ横の「＋ Lesion」）', '85%'))


def p_ops():
    return ('<h1>6. 新しい繰り返し項目を追加する手順</h1>' +
            '<h2>6.1 React 版</h2><ol>'
            '<li>types/model.ts に要素の型を定義し、配列にする。</li>'
            '<li>model/defaults.ts：create 関数を書き、既定値を [create()] にする。LIST_MAX に最大数を足す。fitLists に fitList(…) を 1 行足す。</li>'
            '<li>画面：useCount(path) で数を取り、range(n) で行（列）を描く。各行に DelRowBtn、最後に AddRowBtn を置く。</li>'
            '<li>ほかの画面がその配列を固定の数で回していないか確かめる（帳票・集計・確定前の確認など）。</li>'
            '<li>test/lists.test.ts に、新規は 1 件・末尾の空を除く などのテストを足す。</li></ol>'
            '<h2>6.2 Thymeleaf 版</h2><ol>'
            '<li>テンプレートに最大数ぶんの入力欄を置く（data-path は base.N.…、th:value も同じキー）。</li>'
            '<li>screens.js の REPEATS に { base, max, label, what } を 1 行足す（列なら cols: true、連動なら linked、「なし」で止めるなら offBy）。</li>'
            '<li>行の見つけ方は「0 行目と 1 行目を両方含む最も近い要素の直下」なので、1 行を 1 つの要素（div・tr など）にまとめておく。</li>'
            '<li>レビュー用 HTML を作り直して（tools/review/build_review.py）、追加・削除・保存・再表示を確かめる。</li></ol>' +
            '<h2>6.3 テスト</h2>' +
            table(['テスト', '内容', '件数'], [
                (('単体（React）', 'k'), 'frontend/test/lists.test.ts：新規は各 1 件、最大数、fitList（末尾の空・途中の空・最大超え）、旧データの整形、Pressure ↔ IVUS の整形', '6'),
                (('ブラウザ操作（React）', 'k'), '最大数まで追加・件数表示・確認付きの削除と詰め・空の行の削除・「なし」・全タブで同じ列数・保存後の再表示', '34'),
                (('ブラウザ操作（Thymeleaf）', 'k'), '同上（レビュー用 HTML）', '32'),
                (('連動（両版）', 'k'), 'Pressure Wire ↔ Lesion タブの追加・削除・病変名・IVUS 入力の移動・最大 5・旧データ', '13 / 14'),
            ], widths=['34mm', None, '16mm']))


def p_limits():
    return ('<h1>7. 注意点・制限</h1>' +
            table(['対象', '内容', '対応案'], [
                (('Thymeleaf：画面に無い項目', 'k'), '削除で値を前へ移すのは画面にある入力欄だけ。テンプレートに無い項目がデータにあると、その項目は移らない', '移す処理をサーバー側（保存時）でも行う'),
                (('Thymeleaf：末尾の空', 'k'), '削除した末尾は空の要素としてデータに残る（次の表示では出さない）。React 版は配列から取り除く', '保存時にサーバーで末尾の空を除く'),
                (('数の上限の検査', 'k'), '最大数は画面だけで守っている（API で直接送れば超えられる）', 'サーバーの入力検査に最大数を加える'),
                (('見出しの幅', 'k'), 'Collaterals・Bypass Grafts の見出しは入力欄の幅を固定値で合わせている', '入力欄の幅を変える時は見出しの幅も直す'),
                (('病変の照合', 'k'), 'PCI の QCA 取得は病変名の一致（番号を含むか）で探すため、#1 が LCX#13 にも一致する', '病変名を CAG セグメントのキーに正規化して完全一致'),
            ], widths=['38mm', None, '52mm']))


PARTS = [
    ('ov', 1, '1. 概要', p_overview),
    ('md', 1, '2. データの持ち方', p_model),
    ('re', 1, '3. React 版の実装', p_react),
    ('tl', 1, '4. Thymeleaf 版の実装', p_tl),
    ('lk', 1, '5. Pressure Wire と IVUS Lesion の連動', p_link),
    ('op', 1, '6. 追加の手順・テスト', p_ops),
    ('li', 1, '7. 注意点・制限', p_limits),
]

if __name__ == '__main__':
    make_figs()
    build_doc('繰り返し項目の仕組みと実装', '数が可変（最大数あり）の行・列の作り方（React 版・Thymeleaf 版）',
              '心カテーテルレポート（React 版・Thymeleaf 版）', RELATED, PARTS, G.ROOT / 'docs/design/repeat_items.pdf')

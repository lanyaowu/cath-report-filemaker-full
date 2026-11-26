"""CAG/LVG 画面項目一覧"""
from extra_common import G, e, table, build_doc, RELATED
from items_common import OPTS, V, L, SHARE, CALC, REP, REF, Counter, items, shot, legend, kind_legend, wrap

C = Counter('CG')
R = 'report.cagLvg'
SEG_NAME = {
    'RCA1': '右冠動脈 近位部', 'RCA2': '右冠動脈 中間部', 'RCA3': '右冠動脈 遠位部', 'RCA4AV': '房室結節枝', 'RCA4PD': '後下行枝',
    'LMT5': '左主幹部', 'LAD6': '前下行枝 近位部', 'LAD7': '前下行枝 中間部', 'LAD8': '前下行枝 遠位部', 'LAD9': '第1対角枝', 'LAD10': '第2対角枝',
    'LCX11': '回旋枝 近位部', 'HL': '高位側壁枝（中間枝）', 'LCX12': '鈍縁枝', 'LCX13': '回旋枝 遠位部', 'LCX14': '後側壁枝', 'LCX15': '後下行枝（左優位）',
}


def p_overview():
    return ('<h1>1. 画面の概要</h1>'
            '<p class="lead">CAG/LVG 画面は、冠動脈造影（CAG）と左室造影（LVG）・大動脈造影（AOG）の所見を記録します。上部に「カテーテル」パネル、その下に CAG・LVG のタブがあります。'
            '保存先は <span class="code">report.cagLvg</span> です。</p>' +
            shot('12_cag.png', 'CAG タブ（セグメント所見・側副血行・バイパスグラフト・病変枝数）') +
            '<h2>画面の構成</h2>' +
            table(['領域', 'パネル', 'データ', '内容'], [
                ('上部', 'カテーテル', R + '.approach／catheters', 'Approach（動脈・静脈・シース・サポート）、Catheter 10枠（形状・サイズ）'),
                ('CAG 左', 'セグメント所見表', R + '.cag.segments', 'AHA 17セグメント × サイズ・石灰化・狭窄度・付帯所見'),
                ('CAG 右', 'Collaterals・Bypass Grafts', R + '.cag.collaterals／grafts', '側副血行 最大5行、グラフト 最大4行（行の追加・削除）'),
                ('CAG 右', 'その他・病変枝数・スコア', R + '.cag', '合併症・Squeezing・Spasm・誘発・Dominance、病変枝数、Syntax/Euro/Japan Score、Comment'),
                ('LVG', '左室造影・壁運動・所見', R + '.lvg', '撮影条件、容量・EF・圧、AHA 7分画の壁運動、MR・血栓・瘤、AOG'),
            ], widths=['16mm', '40mm', '46mm', None]) +
            '<h2>入力形式と記号</h2>' + kind_legend() + legend())


def p_catheter():
    slots = [(f'{lab}：形状・サイズ', f'{k}.shape／{k}.size', 'TL', '形状：下記の候補、サイズ：' + V('SHEATH_SIZES') + ' Fr', REP if k == 'LCA' else '')
             for k, lab in OPTS['CATHETER_SLOTS'] if not k.startswith('custom')]
    slots.append(('任意1・任意2：名称・形状・サイズ', 'custom1／custom2.{label,shape,size}', 'TL', '名称は自由入力', REP + '2枠'))
    return ('<h1>2. カテーテル</h1>' + items(C, [
        ('Approach', R + '.approach', [
            ('Artery', 'artery', 'TL', V('APPROACHES'), SHARE + 'カテ記録のアプローチから反映可'),
            ('Artery シース（名称・サイズ）', 'arterySheath.name／size', 'TL', V('SHEATH_NAMES') + '／' + V('SHEATH_SIZES') + ' Fr', SHARE + '同上'),
            ('Vein', 'vein', 'TL', 'Rt Femoral V／Lt Femoral V／Rt Internal Jugular V／Rt Brachial V'),
            ('Vein シース（名称・サイズ）', 'veinSheath.name／size', 'TL', V('SHEATH_NAMES') + '／' + V('SHEATH_SIZES') + ' Fr'),
            ('サポート', 'support', 'TL', V('SUPPORTS')),
            ('カテ記録のアプローチを反映', '－', 'B', '', 'カテ記録の exam.approach・sheath を Artery 欄へコピー'),
        ]),
        ('Catheter（形状／サイズ Fr）', R + '.catheters', slots),
    ]) + f'<p class="small">形状の候補（全枠共通）：{e(V("CATHETER_SHAPES"))}</p>')


def p_segments():
    seg_rows = [(f'{s["key"]}', SEG_NAME.get(s['key'], '')) for s in OPTS['CAG_SEGMENTS']]
    return ('<h1>3. CAG：セグメント所見</h1>'
            '<p class="lead">セグメント（行）ごとに、サイズ・石灰化・狭窄度・付帯所見（列）を入力する表です。データは <span class="code">report.cagLvg.cag.segments.&lt;キー&gt;</span> に保存します。</p>'
            '<h2>3.1 セグメント（行）</h2>' +
            table(['キー', '部位（AHA 分類）', 'キー', '部位（AHA 分類）'],
                  [((seg_rows[i][0], 'code'), seg_rows[i][1], (seg_rows[i + 9][0], 'code') if i + 9 < len(seg_rows) else '', seg_rows[i + 9][1] if i + 9 < len(seg_rows) else '')
                   for i in range(9)], widths=['22mm', None, '22mm', None]) +
            '<h2>3.2 セグメントごとの項目（列）</h2>' +
            items(C, [('各セグメント', R + '.cag.segments.<キー>', [
                ('サイズ', 'size', 'R', V('SEG_SIZES'), '再クリックで解除'),
                ('Calcification', 'calc', 'C'),
                ('狭窄度', 'stenosis', 'R', V('STENOSIS') + '（%）', '75 以上は有意（列・行をピンク表示）。再クリックで解除'),
                ('Diffuse', 'diffuse', 'C', '', 'びまん性'),
                ('Segmental', 'segmental', 'C', '', '限局性'),
                ('Undefined', 'undefined', 'C', '', '評価不能'),
                ('Jeopardy', 'jeopardy', 'C'),
                ('Graftable', 'graftable', 'C', '', 'バイパス吻合が可能'),
                ('JCS区分', '（計算）', 'K', '0%／1-24%／25-49%／50-69%／70-89%／90-99%／100%', CALC + '狭窄度（AHA）を区間の上限で対応付け（75→50-69%）'),
            ])]) +
            '<p class="small">17 セグメント × 8 項目＝136 の入力欄になります（一覧の項目数は列の 8＋自動表示の JCS 区分で数えています）。</p>'
            '<h2>3.3 操作</h2>' +
            table(['操作', '動作'], [
                ('Normal（表の左上）', '狭窄度が未入力のセグメントをすべて Normal にする'),
                ('過去の CAG をコピー', '同じ患者の過去レポートを選び、セグメント所見をコピーする（保存で確定）'),
            ], widths=['50mm', None]))


def p_cag_other():
    return ('<h1>4. CAG：側副血行・グラフト・その他</h1>' + items(C, [
        ('Collaterals（最大5行）', R + '.cag', [
            ('なし', 'collateralsNone', 'C', '', 'チェックすると 5 行とも入力不可'),
            ('送達元', 'collaterals[0..4].from', 'TL', 'LAD／LAD septal／LCX／RCA／Conus／Kugel／Bridge／Epicardial', REP + '1〜5行（＋で追加・✖で削除）'),
            ('送達先', 'collaterals[0..4].to', 'TL', 'セグメントのキー（RCA1〜LCX15）', REP),
            ('J（Rentrop）', 'collaterals[0..4].grade', 'TL', V('RENTROP'), REP + 'Rentrop 分類'),
            ('State', 'collaterals[0..4].state', 'TL', V('COLLATERAL_STATE'), REP),
        ]),
        ('Bypass Grafts（最大4行）', R + '.cag', [
            ('グラフト', 'grafts[0..3].graft', 'TL', V('GRAFT_NAMES'), REP + '1〜4行（＋で追加・✖で削除）'),
            ('吻合部', 'grafts[0..3].anastomosis', 'TL', 'セグメントのキー', REP),
            ('通行状態', 'grafts[0..3].patency', 'TL', V('GRAFT_PATENCY'), REP),
        ]),
        ('その他の所見', R + '.cag', [
            ('合併症', 'complication', 'T'),
            ('Squeezing', 'squeezing', 'R', V('PM2_OPTS'), '心筋ブリッジによる収縮期の圧排'),
            ('Spasm', 'spasm', 'R', V('PM2_OPTS')),
            ('Provocation of Spasm', 'provocation', 'TL', 'Ach／Er／陰性'),
            ('Dominance', 'dominance', 'TL', V('DOMINANCY')),
        ]),
        ('病変枝数', R + '.cag.lesions', [
            ('病変枝数', 'count', 'N', '0〜3', CALC + '「所見から算出」で自動入力'),
            ('LMT・LAD・LCX・RCA', 'LMT／LAD／LCX／RCA', 'C', '', CALC + '同上。術前の本幹病変・治療適用病変のみ。グラフトで保護されている枝は外す'),
            ('所見から算出', '－', 'B', '', '75% 以上（LMT は 50% 以上）の狭窄から算出。LMT 病変は LAD・LCX に数える'),
        ]),
        ('スコア', R + '.cag', [
            ('Syntax Score', 'syntax', 'N', '', SHARE + 'PCI 基本タブにも表示'),
            ('Euro Score', 'euro', 'N', '', SHARE),
            ('Japan Score', 'japan', 'N', '', SHARE),
        ]),
        ('Comment', R + '.cag', [('Comment', 'comment', 'A', '', '過去レポートの Comment をコピー可')]),
    ]))


def p_lvg():
    return ('<h1>5. LVG（左室造影）・AOG</h1>' + shot('13_lvg.png', 'LVG タブ') + items(C, [
        ('左室造影（LVG）', R + '.lvg', [
            ('施行', 'performed', 'C'),
            ('撮影方向', 'view', 'TL', 'RAO30/LAO60／RAO30／LAO60／Biplane'),
            ('造影剤', 'agent', 'TL', V('CONTRAST_AGENTS')),
            ('注入量', 'volume', 'N', 'ml'), ('注入速度', 'rate', 'N', 'ml/s'),
        ]),
        ('容量・機能', R + '.lvg.values', [
            ('LVEDV', 'LVEDV', 'N', 'ml', '算出の入力'), ('LVESV', 'LVESV', 'N', 'ml', '算出の入力'),
            ('LVSV', 'LVSV', 'N', 'ml', CALC + 'EDV−ESV'), ('LVEF', 'EF', 'N', '%', CALC + 'SV÷EDV×100'),
            ('LVEDVI', 'LVEDVI', 'N', 'ml/m²', CALC + 'EDV÷BSA'), ('LVESVI', 'LVESVI', 'N', 'ml/m²', CALC + 'ESV÷BSA'), ('LVSVI', 'LVSVI', 'N', 'ml/m²', CALC + 'SV÷BSA'),
            ('LVEDP', 'LVEDP', 'N', 'mmHg'),
            ('HR', 'HR', 'N', '/min', '空欄ならカテ記録の HR を使用'),
            ('CO', 'CO', 'N', 'L/min', CALC + 'SV×HR÷1000'), ('CI', 'CI', 'N', 'L/min/m²', CALC + 'CO÷BSA'),
            ('SV・EF・Index 算出', '－', 'B', '', 'BSA はカテ記録の身長・体重から（DuBois）'),
        ]),
        ('壁運動（AHA 7分画）', R + '.lvg.wallMotion', [
            (lab, k, 'S', V('WALL_MOTION'), REP + '図の分画クリックでも順に切替' if k == '1' else REP) for k, lab in OPTS['LV_SEGMENTS']
        ]),
        ('所見', R + '.lvg', [
            ('MR（Sellers）', 'mr', 'S', V('SELLERS')),
            ('LV内血栓', 'thrombus', 'C'), ('心室瘤', 'aneurysm', 'C'), ('心尖部バルーニング', 'apicalBallooning', 'C'), ('VSR', 'vsr', 'C', '', '心室中隔穿孔'),
        ]),
        ('大動脈造影（AOG）', R + '.lvg.aog', [
            ('施行', 'performed', 'C'), ('AR（Sellers）', 'ar', 'S', V('SELLERS')), ('所見', 'findings', 'T'),
        ]),
        ('LVG Comment', R + '.lvg', [('LVG Comment', 'comment', 'A')]),
    ]))


def p_links():
    return ('<h1>6. 他画面との連携・自動計算・項目数</h1>' +
            table(['項目', 'CAG/LVG のデータ', '関係する画面・内容'], [
                ('Artery・シース', 'approach.artery／arterySheath', 'カテ記録の exam.approach／sheath から反映（ボタン）'),
                ('Syntax・Euro・Japan Score', 'cag.syntax／euro／japan', 'PCI 基本タブで同じ値を表示（編集は CAG）'),
                ('セグメントのキー', 'cag.segments', 'PCI の Target 候補（#1〜#15・HL など）、側副血行の送達先、グラフトの吻合部'),
                ('BSA・HR', 'カテ記録 body／hemo.values.HR', 'LVG の Index・CO・CI 算出'),
                ('Dominance', 'cag.dominance', 'Pressure/IVUS 画面にも Dominancy 欄（別データ）'),
            ], widths=['42mm', '52mm', None]) +
            '<h2>入力の制御</h2>' +
            table(['条件', '動作'], [
                ('狭窄度 75・90・99・100', '列見出しと行をピンク表示（有意狭窄）'),
                ('Collaterals「なし」', '側副血行の行が入力不可（追加・削除も不可）'),
                ('タブにデータあり', 'CAG・LVG タブ名に印を表示'),
            ], widths=['60mm', None]) +
            '<p class="small">CAG の所見（狭窄度・付帯所見）の定義と標準との対応は「CAG・PCI 病変形態・所見の整理」（cag_pci_lesion_findings.pdf）を参照。</p>'
            '<h2>項目数</h2>' + table(['区分', '項目数'], [(k, (str(v), 'r')) for k, v in C.per.items()] + [(('合計', 'k'), (str(C.n), 'r k'))], widths=[None, '24mm']))


PARTS = [
    ('ov', 1, '1. 画面の概要', p_overview),
    ('ct', 1, '2. カテーテル', p_catheter),
    ('sg', 1, '3. CAG：セグメント所見', p_segments),
    ('co', 1, '4. CAG：側副血行・グラフト・その他', p_cag_other),
    ('lv', 1, '5. LVG（左室造影）・AOG', p_lvg),
    ('ln', 1, '6. 他画面との連携・自動計算・項目数', p_links),
]

if __name__ == '__main__':
    build_doc('CAG 項目一覧', 'CAG/LVG 画面の項目・データパス・入力形式・選択肢・連携', 'React 版「CAG/LVG」画面（report.cagLvg）',
              RELATED, wrap(PARTS), G.ROOT / 'docs/design/items_cag.pdf')

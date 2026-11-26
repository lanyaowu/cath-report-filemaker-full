#!/usr/bin/env python3
"""docs/ER.md の Mermaid 定義から Graphviz で ER 図（SVG / PNG）を生成
usage: python3 tools/gen_er_diagram.py   → docs/er(.svg/.png/.dot)（縦長）, docs/er_landscape(.svg/.png/.dot)（横長）
"""
import html, pathlib, re, subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]
md = (ROOT / 'docs/ER.md').read_text(encoding='utf-8')
src = md.split('```mermaid')[1].split('```')[0]

# ---- Mermaid erDiagram の解析 ----
entities, rels, cur = {}, [], None
for line in src.splitlines():
    s = line.strip()
    if not s or s == 'erDiagram':
        continue
    m = re.match(r'^(\w+)\s+([|}o][|o])--([|o][|{o])\s+(\w+)\s*:\s*"?([^"]*)"?$', s)
    if m:
        rels.append(m.groups())
        continue
    m = re.match(r'^(\w+)\s*\{$', s)
    if m:
        cur = m.group(1)
        entities[cur] = []
        continue
    if s == '}':
        cur = None
        continue
    if cur:
        m = re.match(r'^(\w+)\s+(\w+)(?:\s+(PK|FK|UK))?(?:\s+"([^"]*)")?', s)
        if m:
            entities[cur].append(m.groups())

# ---- グループ（コレクション / 画面） ----
GROUPS = [
    ('patients', 'collection: patients', '#efe9d6', ['PATIENT', 'ADMISSION']),
    ('masters', 'collection: masters', '#e8eef3', ['MASTERS', 'DEVICE_MASTER']),
    ('reports', 'collection: cath_reports（1検査 = 1ドキュメント）', '#f4f7f5', None),
]
SCREENS = [
    ('共通', '#ffffff', ['CATH_REPORT', 'REPORT_HEADER', 'REPORT_HISTORY']),
    ('カテ記録', '#e3f2e5', ['CATH_RECORD', 'EXAM_INFO', 'DOCTORS', 'HEMODYNAMICS', 'LABS', 'RISK_FACTORS', 'PROGNOSIS']),
    ('CAG / LVG', '#e6f0fa', ['CAG_LVG', 'CATHETER', 'CAG_SEGMENT', 'COLLATERAL', 'BYPASS_GRAFT', 'LVG']),
    ('PCI', '#fdf1e2', ['PCI', 'PCI_BASIC', 'PCI_LESION', 'DEVICE_ITEM', 'JPCI', 'BLEEDING_THROMBUS_RISK', 'AMI_TIMES']),
    ('Pressure / IVUS', '#f3e8f7', ['PRESSURE_IVUS', 'PRESSURE_COLUMN', 'IVUS_LESION']),
    ('PCPS・カンファレンス・MACE・画像・Restudy', '#eef0f2', ['PCPS', 'CONFERENCE', 'MED_ROW', 'MACE_ENTRY', 'IMAGE_ITEM', 'RESTUDY']),
]
HEAD = {'PATIENT': '#b9a76f', 'CATH_REPORT': '#3f5560', 'MASTERS': '#6d8fa6'}

FONT = 'Noto Sans CJK JP'
e = lambda t: html.escape(t or '', quote=True)


def font(t, color, size=None):
    if not t:
        return ' '
    sz = f' POINT-SIZE="{size}"' if size else ''
    return f'<FONT COLOR="{color}"{sz}>{e(t)}</FONT>'


def node(name):
    rows = ''.join(
        f'<TR><TD ALIGN="LEFT" PORT="{a}"><FONT COLOR="#6b7a7e">{e(t)}</FONT></TD>'
        f'<TD ALIGN="LEFT">{"<B>" if k == "PK" else ""}{e(a)}{"</B>" if k == "PK" else ""}</TD>'
        f'<TD ALIGN="LEFT">{font(k, "#b03a2e")}</TD>'
        f'<TD ALIGN="LEFT">{font(c, "#445", 9)}</TD></TR>'
        for t, a, k, c in entities.get(name, []))
    color = HEAD.get(name, '#7f939c')
    return (f'  {name} [label=<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="3" BGCOLOR="white" COLOR="#9aa8a4">'
            f'<TR><TD COLSPAN="4" BGCOLOR="{color}"><FONT COLOR="white"><B>{e(name)}</B></FONT></TD></TR>{rows}</TABLE>>];')


CARD = {'||': ('tee', 'tee'), '|o': ('teeodot', 'odottee'), 'o|': ('teeodot', 'odottee'), '|{': ('crowtee', 'crowtee'), 'o{': ('crowodot', 'crowodot'), '}|': ('crowtee', 'crowtee'), '}o': ('crowodot', 'crowodot')}

out = [
    'digraph ER {',
    f'  graph [rankdir=LR, fontname="{FONT}", fontsize=12, nodesep=0.25, ranksep=0.9, splines=spline, pad=0.3, bgcolor="white",',
    '         label=<<B>心カテーテルレポート ER図（MongoDB）</B><BR/><FONT POINT-SIZE="10">'
    '実線：埋め込み（サブドキュメント / 配列）　太い破線：コレクション間参照（patientRef → patients._id）</FONT>>, labelloc=t, fontsize=18];',
    f'  node [shape=plain, fontname="{FONT}", fontsize=10];',
    f'  edge [fontname="{FONT}", fontsize=9, color="#5d7b86", fontcolor="#33515c", dir=both, arrowsize=0.7];',
]
for gid, title, bg, members in GROUPS:
    out.append(f'  subgraph cluster_{gid} {{ label=<<B>{e(title)}</B>>; style="rounded,filled"; fillcolor="{bg}"; color="#8a9894"; fontsize=13;')
    if members:
        out += ['  ' + node(n) for n in members]
    else:
        for i, (st, sbg, ms) in enumerate(SCREENS):
            out.append(f'    subgraph cluster_s{i} {{ label=<{e(st)}>; style="rounded,filled"; fillcolor="{sbg}"; color="#b8c4c0";')
            out += ['    ' + node(n) for n in ms]
            out.append('    }')
    out.append('  }')

for a, ca, cb, b, label in rels:
    tail = CARD.get(ca, ('none', 'none'))[0]
    head = CARD.get(cb, ('none', 'none'))[1]
    style = ', style=dashed, penwidth=2.2, color="#b03a2e", fontcolor="#b03a2e"' if label == 'patientRef' else ''
    out.append(f'  {a} -> {b} [arrowtail={tail}, arrowhead={head}, label=<{e(label)}>{style}];')
out.append('}')

dot = '\n'.join(out)
docs = ROOT / 'docs'
# 縦長（画面グループ縦並び・スクロール閲覧向け）と横長（A3横印刷・プロジェクタ向け）の2種類
for name, rankdir in [('er', 'LR'), ('er_landscape', 'TB')]:
    d = dot.replace('rankdir=LR', f'rankdir={rankdir}')
    (docs / f'{name}.dot').write_text(d, encoding='utf-8')
    subprocess.run(['dot', '-Tsvg', '-o', str(docs / f'{name}.svg'), str(docs / f'{name}.dot')], check=True)
    svg = docs / f'{name}.svg'
    # Windows 等で Noto が無い場合のフォールバック
    svg.write_text(svg.read_text(encoding='utf-8').replace('font-family="Noto Sans CJK JP"', 'font-family="Noto Sans CJK JP, Meiryo, Yu Gothic, sans-serif"'), encoding='utf-8')
    subprocess.run(['dot', '-Tpng', '-Gdpi=144', '-o', str(docs / f'{name}.png'), str(docs / f'{name}.dot')], check=True)
    print(name, '->', docs / f'{name}.svg', docs / f'{name}.png')
print('entities', len(entities), 'relations', len(rels))

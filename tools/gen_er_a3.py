#!/usr/bin/env python3
"""ER図を A3 印刷用に分割（全体概要＋グループ別詳細）
出力: docs/er_a3/er_a3_XX_*.png（A3・200dpi）, *.svg, er_a3_all.pdf（全ページ）
usage: python3 tools/gen_er_a3.py
"""
import html, pathlib, re, subprocess, tempfile
from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/er_a3'
OUT.mkdir(parents=True, exist_ok=True)
for f in OUT.glob('er_a3_*'):
    f.unlink()

src = (ROOT / 'docs/ER.md').read_text(encoding='utf-8').split('```mermaid')[1].split('```')[0]
entities, rels, links, cur = {}, [], [], None
for line in src.splitlines():
    s = line.strip()
    m = re.match(r'^(\w+)\s+([|}o][|o])(--|\.\.)([|o][|{o])\s+(\w+)\s*:\s*"?([^"]*)"?$', s)
    if m:
        a, ca, kind, cb, b, label = m.groups()
        # '--' は埋め込み、'..' はデータの連携（同じ番号・名前の一致・複写。外部キーではない）
        (rels if kind == '--' else links).append((a, ca, cb, b, label)); continue
    m = re.match(r'^(\w+)\s*\{$', s)
    if m:
        cur = m.group(1); entities[cur] = []; continue
    if s == '}':
        cur = None; continue
    if cur:
        m = re.match(r'^(\w+)\s+(\w+)(?:\s+(PK|FK|UK))?(?:\s+"([^"]*)")?', s)
        if m:
            entities[cur].append(m.groups())

FONT = 'Noto Sans CJK JP'
FONT_FILE = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
e = lambda t: html.escape(t or '', quote=True)
CARD = {'||': ('tee', 'tee'), '|o': ('teeodot', 'odottee'), '|{': ('crowtee', 'crowtee'), 'o{': ('crowodot', 'crowodot')}
HEAD = {'PATIENT': '#b9a76f', 'CATH_REPORT': '#3f5560', 'MASTERS': '#6d8fa6'}

GROUPS = [  # (ファイル名, ページタイトル, 背景色, エンティティ, 他ページ参照の親)
    ('patients_masters', '患者（patients）・マスタ（masters）', '#efe9d6', ['PATIENT', 'ADMISSION', 'MASTERS', 'DEVICE_MASTER'], ['CATH_REPORT']),
    ('report_common', 'カテレポート（cath_reports）共通部分', '#f4f7f5', ['CATH_REPORT', 'REPORT_HEADER', 'REPORT_HISTORY'],
     ['PATIENT', 'CATH_RECORD', 'CAG_LVG', 'PCI', 'PRESSURE_IVUS', 'PCPS', 'CONFERENCE', 'MACE_ENTRY', 'IMAGE_ITEM', 'RESTUDY']),
    ('cath_record', 'カテ記録（cathRecord）', '#e3f2e5', ['CATH_RECORD', 'EXAM_INFO', 'DOCTORS', 'HEMODYNAMICS', 'LABS', 'RISK_FACTORS', 'PROGNOSIS'], ['CATH_REPORT']),
    ('cag_lvg', 'CAG / LVG（cagLvg）', '#e6f0fa', ['CAG_LVG', 'CATHETER', 'CAG_SEGMENT', 'COLLATERAL', 'BYPASS_GRAFT', 'LVG'], ['CATH_REPORT']),
    ('pci', 'PCI（pci）', '#fdf1e2', ['PCI', 'PCI_BASIC', 'PCI_LESION', 'DEVICE_ITEM', 'JPCI', 'BLEEDING_THROMBUS_RISK', 'AMI_TIMES'], ['CATH_REPORT']),
    ('pressure_pcps_others', 'Pressure/IVUS・PCPS・カンファレンス・MACE・画像・Restudy', '#eef0f2',
     ['PRESSURE_IVUS', 'PRESSURE_COLUMN', 'IVUS_LESION', 'PCPS', 'CONFERENCE', 'MED_ROW', 'MACE_ENTRY', 'IMAGE_ITEM', 'RESTUDY'], ['CATH_REPORT']),
]
PAGE_OF = {n: i + 2 for i, g in enumerate(GROUPS) for n in g[3]}  # p.1 は概要


def font(t, color, size=None):
    if not t:
        return ' '
    sz = f' POINT-SIZE="{size}"' if size else ''
    return f'<FONT COLOR="{color}"{sz}>{e(t)}</FONT>'


def node(name, detail=True, stub=False):
    color = HEAD.get(name, '#7f939c')
    if stub:
        return (f'  {name} [label=<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4" BGCOLOR="#f7f7f7" COLOR="#9aa8a4" STYLE="dashed">'
                f'<TR><TD BGCOLOR="#c9d1d6"><B>{e(name)}</B></TD></TR><TR><TD><FONT POINT-SIZE="9" COLOR="#555">詳細は p.{PAGE_OF.get(name, 1)}</FONT></TD></TR></TABLE>>];')
    rows = ''
    if detail:
        rows = ''.join(
            f'<TR><TD ALIGN="LEFT">{font(t, "#6b7a7e")}</TD><TD ALIGN="LEFT">{"<B>" if k == "PK" else ""}{e(a)}{"</B>" if k == "PK" else ""}</TD>'
            f'<TD ALIGN="LEFT">{font(k, "#b03a2e")}</TD><TD ALIGN="LEFT">{font(c, "#445", 9)}</TD></TR>' for t, a, k, c in entities.get(name, []))
    span = 4 if detail else 1
    return (f'  {name} [label=<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="3" BGCOLOR="white" COLOR="#9aa8a4">'
            f'<TR><TD COLSPAN="{span}" BGCOLOR="{color}"><FONT COLOR="white"><B>{e(name)}</B></FONT></TD></TR>{rows}</TABLE>>];')


def edge(a, ca, cb, b, label, link=False):
    tail, head = CARD.get(ca, ('none', 'none'))[0], CARD.get(cb, ('none', 'none'))[1]
    st = ', style=dashed, penwidth=2.2, color="#b03a2e", fontcolor="#b03a2e"' if label == 'patientRef' else ''
    if link:
        st = ', style=dashed, penwidth=1.8, color="#2b6cb0", fontcolor="#2b6cb0", constraint=false'
    return f'  {a} -> {b} [arrowtail={tail}, arrowhead={head}, label=<{e(label)}>{st}];'


def dot_doc(body, rankdir='LR'):
    return '\n'.join([
        'digraph ER {',
        f'  graph [rankdir={rankdir}, fontname="{FONT}", nodesep=0.3, ranksep=1.0, splines=spline, pad=0.2, bgcolor="white"];',
        f'  node [shape=plain, fontname="{FONT}", fontsize=10];',
        f'  edge [fontname="{FONT}", fontsize=9, color="#5d7b86", fontcolor="#33515c", dir=both, arrowsize=0.7];',
        body, '}'])


def render(dot, stem):
    with tempfile.NamedTemporaryFile('w', suffix='.dot', delete=False, encoding='utf-8') as f:
        f.write(dot)
    png = pathlib.Path(tempfile.mktemp(suffix='.png'))
    subprocess.run(['dot', '-Tpng', '-Gdpi=200', '-o', str(png), f.name], check=True, stderr=subprocess.DEVNULL)
    svg = OUT / f'{stem}.svg'
    subprocess.run(['dot', '-Tsvg', '-o', str(svg), f.name], check=True, stderr=subprocess.DEVNULL)
    svg.write_text(svg.read_text(encoding='utf-8').replace(f'font-family="{FONT}"', f'font-family="{FONT}, Meiryo, Yu Gothic, sans-serif"'), encoding='utf-8')
    return Image.open(png).convert('RGB')


DPI = 200
A3 = (int(420 / 25.4 * DPI), int(297 / 25.4 * DPI))  # 横 3307x2338
MARGIN, HEAD_H, FOOT_H = int(10 / 25.4 * DPI), 110, 60
pages = []


def place(img, title, page_no, total, stem):
    """図を A3（向きは自動）に収めて、見出し・凡例・ページ番号を付ける"""
    best = None
    for size in (A3, A3[::-1]):
        aw, ah = size[0] - 2 * MARGIN, size[1] - 2 * MARGIN - HEAD_H - FOOT_H
        sc = min(aw / img.width, ah / img.height, 1.0)
        if not best or sc > best[0]:
            best = (sc, size)
    sc, size = best
    canvas = Image.new('RGB', size, 'white')
    im = img.resize((int(img.width * sc), int(img.height * sc)), Image.LANCZOS) if sc < 1 else img
    x = (size[0] - im.width) // 2
    y = MARGIN + HEAD_H + (size[1] - 2 * MARGIN - HEAD_H - FOOT_H - im.height) // 2
    canvas.paste(im, (x, y))
    d = ImageDraw.Draw(canvas)
    fb = ImageFont.truetype(FONT_FILE.replace('Regular', 'Bold'), 46)
    fr = ImageFont.truetype(FONT_FILE, 26)
    d.text((MARGIN, MARGIN), f'心カテーテルレポート ER図　{title}', font=fb, fill='#2c3e45')
    d.text((MARGIN, MARGIN + 62), '実線：埋め込み（サブドキュメント／配列）　赤破線：コレクション間参照（patientRef → patients._id）　青破線：データの連携（同じ番号・名前の一致・複写）　灰色点線の枠：他ページで詳細表示',
           font=fr, fill='#6b7a7e')
    d.line((MARGIN, MARGIN + HEAD_H - 8, size[0] - MARGIN, MARGIN + HEAD_H - 8), fill='#b8c4c0', width=3)
    foot = f'{page_no} / {total}　（A3 {"横" if size[0] > size[1] else "縦"}・縮尺 {sc * 100:.0f}%）'
    w = d.textlength(foot, font=fr)
    d.text((size[0] - MARGIN - w, size[1] - MARGIN - 34), foot, font=fr, fill='#6b7a7e')
    path = OUT / f'{stem}.png'
    canvas.save(path, dpi=(DPI, DPI))
    pages.append(canvas)
    print(f'{path.name}: {size[0]}x{size[1]} scale={sc:.2f}')


total = 1 + len(GROUPS)

# ---- p.1 概要（エンティティ名のみ）
body = []
for gid, title, bg, members, _ in [('patients', 'collection: patients', '#efe9d6', ['PATIENT', 'ADMISSION'], None),
                                     ('masters', 'collection: masters', '#e8eef3', ['MASTERS', 'DEVICE_MASTER'], None)]:
    body.append(f'  subgraph cluster_{gid} {{ label=<<B>{e(title)}</B>>; style="rounded,filled"; fillcolor="{bg}"; color="#8a9894"; fontsize=14;')
    body += [node(n, detail=False) for n in members]
    body.append('  }')
body.append('  subgraph cluster_reports { label=<<B>collection: cath_reports（1検査 = 1ドキュメント）</B>>; style="rounded,filled"; fillcolor="#f4f7f5"; color="#8a9894"; fontsize=14;')
for i, (stem, title, bg, members, _) in enumerate(GROUPS[1:], 3):
    body.append(f'    subgraph cluster_{stem} {{ label=<{e(title)}　<FONT COLOR="#b03a2e">→ p.{i}</FONT>>; style="rounded,filled"; fillcolor="{bg}"; color="#b8c4c0"; fontsize=12;')
    body += ['  ' + node(n, detail=False) for n in members]
    body.append('    }')
body.append('  }')
body += [edge(*r) for r in rels]
body += [edge(*r, link=True) for r in links]
place(render(dot_doc('\n'.join(body), 'LR'), 'er_a3_01_overview'), '全体概要（項目は各ページ参照）', 1, total, 'er_a3_01_overview')

# ---- p.2〜 グループ別詳細
for i, (stem, title, bg, members, parents) in enumerate(GROUPS, 2):
    body = [f'  subgraph cluster_main {{ label=<<B>{e(title)}</B>>; style="rounded,filled"; fillcolor="{bg}"; color="#8a9894"; fontsize=14;']
    body += [node(n) for n in members]
    body.append('  }')
    used = set(members)
    for a, ca, cb, b, label in rels:
        if a in used and b in used:
            body.append(edge(a, ca, cb, b, label))
        elif (a in used) != (b in used):
            other = b if a in used else a
            if other in parents:
                if other not in body[-0:] and f'  {other} [' not in '\n'.join(body):
                    body.append(node(other, stub=True))
                body.append(edge(a, ca, cb, b, label))
    for a, ca, cb, b, label in links:
        if a in used or b in used:
            for other in (a, b):
                if other not in used and f'  {other} [' not in '\n'.join(body):
                    body.append(node(other, stub=True))
            body.append(edge(a, ca, cb, b, label, link=True))
    rank = 'LR'
    stem2 = f'er_a3_{i:02d}_{stem}'
    place(render(dot_doc('\n'.join(body), rank), stem2), title, i, total, stem2)

pdf = OUT / 'er_a3_all.pdf'
pages[0].save(pdf, save_all=True, append_images=pages[1:], resolution=DPI)
print('pdf ->', pdf)

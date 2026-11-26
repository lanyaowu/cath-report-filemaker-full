#!/usr/bin/env python3
"""demo/screenshots/*.png を1つの PDF（A3・表紙/目次付き）にまとめる
usage: python3 tools/demo/screenshots_pdf.py  → demo/cath-report-screenshots.pdf
"""
import csv, datetime, pathlib
from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parents[2]
SHOTS = ROOT / 'demo/screenshots'
OUT = ROOT / 'demo/cath-report-screenshots.pdf'
FONT = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
FONT_B = '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
DPI = 150
A3L = (int(420 / 25.4 * DPI), int(297 / 25.4 * DPI))  # 横
MARGIN = int(12 / 25.4 * DPI)
f = lambda size, bold=False: ImageFont.truetype(FONT_B if bold else FONT, size)

with open(SHOTS / 'index.csv', encoding='utf-8-sig') as fp:
    items = [(r['ファイル名'], r['画面']) for r in csv.DictReader(fp)]

pages = []


def new_page(size=A3L):
    return Image.new('RGB', size, 'white')


# ---- 表紙・目次
cover = new_page()
d = ImageDraw.Draw(cover)
d.rectangle((0, 0, A3L[0], 260), fill='#3f5560')
d.text((MARGIN, 70), '心カテーテルレポート　画面イメージ集', font=f(78, True), fill='white')
d.text((MARGIN, 180), f'全 {len(items)} 画面　｜　作成日 {datetime.date.today():%Y/%m/%d}　｜　統合版（選択値マスタ＋監査機能）レビュー用デモ版（サンプルデータ）', font=f(32), fill='#d7e3e8')
d.text((MARGIN, 300), '目次', font=f(44, True), fill='#2c3e45')
cols, per = 3, (len(items) + 2) // 3
cw = (A3L[0] - 2 * MARGIN) // cols
for i, (_, name) in enumerate(items):
    c, r = divmod(i, per)
    x, y = MARGIN + c * cw, 380 + r * 54
    d.text((x, y), f'{i + 1:02d}', font=f(28, True), fill='#2e7d6b')
    d.text((x + 60, y), name, font=f(28), fill='#2c3e45')
    d.text((x + cw - 90, y), f'p.{i + 2}', font=f(24), fill='#8a9894')
pages.append(cover)

# ---- 各画面
for i, (fn, name) in enumerate(items, 1):
    img = Image.open(SHOTS / fn).convert('RGB')
    head, foot = 110, 50
    best = None
    for size in (A3L, A3L[::-1]):
        aw, ah = size[0] - 2 * MARGIN, size[1] - 2 * MARGIN - head - foot
        sc = min(aw / img.width, ah / img.height)
        if not best or sc > best[0]:
            best = (sc, size)
    sc, size = best
    pg = new_page(size)
    im = img.resize((int(img.width * sc), int(img.height * sc)), Image.LANCZOS)
    x = (size[0] - im.width) // 2
    y = MARGIN + head
    pg.paste(im, (x, y))
    dd = ImageDraw.Draw(pg)
    dd.rectangle((x - 1, y - 1, x + im.width, y + im.height), outline='#b8c4c0', width=2)
    dd.text((MARGIN, MARGIN), f'{i:02d}　{name}', font=f(46, True), fill='#2c3e45')
    dd.text((MARGIN, MARGIN + 62), fn, font=f(22), fill='#8a9894')
    dd.line((MARGIN, MARGIN + head - 14, size[0] - MARGIN, MARGIN + head - 14), fill='#b8c4c0', width=3)
    t = f'{i + 1} / {len(items) + 1}'
    dd.text((size[0] - MARGIN - dd.textlength(t, font=f(22)), size[1] - MARGIN - 28), t, font=f(22), fill='#8a9894')
    pages.append(pg)

pages[0].save(OUT, save_all=True, append_images=pages[1:], resolution=DPI)
print(OUT, len(pages), 'pages', round(OUT.stat().st_size / 1e6, 1), 'MB')

#!/usr/bin/env python3
"""心カテーテルレポート（React 版）画面イメージ集 PDF（A3 横）を生成する。
前提: python3 tools/demo/screenshots.py demo/cath-report-demo.html docs/design/screens
      （日付表示を日本語にするため LANG=ja_JP.UTF-8 LANGUAGE=ja で実行）
出力: docs/design/react_screen_images_A3.pdf（表紙・目次・しおり・目次リンク付き）
"""
import asyncio, csv, pathlib, sys, re
from pypdf import PdfReader, PdfWriter

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import gen_doc as G
import screens_content as SC

ROOT = G.ROOT
SHOTS = ROOT / 'docs/design/screens'
OUT = ROOT / 'docs/design/react_screen_images_A3.pdf'
e = G.e
TITLE = '心カテーテルレポート（React 版）画面イメージ集'

EXTRA_CSS = '''
.shot { display: flex; gap: 6mm; align-items: flex-start; }
.shot .img { flex: 1; min-width: 0; text-align: center; }
.shot .img img { max-width: 100%; max-height: 236mm; border: 0.8pt solid #9fb0b6; box-shadow: 0 0 0 1mm #f1f4f3; }
.shot .side { width: 74mm; flex: none; font-size: 9.6pt; }
.shot .side h3 { margin: 0 0 1.4mm; font-size: 10pt; color: #2e6b5e; border-bottom: 0.6pt solid #cfd9d5; padding-bottom: 0.8mm; }
.shot .side p { margin: 0 0 4mm; }
.shot .side ul { margin: 0 0 4mm; padding-left: 4.5mm; } .shot .side li { margin-bottom: 1mm; }
.shot .side .code { font-size: 8.6pt; word-break: break-all; margin-bottom: 4mm; }
.no { display: inline-block; background: #2e6b5e; color: #fff; border-radius: 1.5mm; padding: 0 2.4mm; margin-right: 2.5mm; font-size: 13pt; }
.tocwrap { display: flex; gap: 10mm; } .tocwrap > table { flex: 1; }
.tocwrap .toc td { padding: 0.75mm 1mm; font-size: 9.4pt; } .tocwrap .toc tr.l1 td { padding-top: 1.8mm; }
'''


def items():
    with open(SHOTS / 'index.csv', encoding='utf-8-sig') as f:
        return {r['画面']: r['ファイル名'] for r in csv.DictReader(f)}


def shot_page(no, key, fn):
    title, desc, ops, funcs, src = SC.S[key]
    ops_html = ''.join(f'<li>{e(o)}</li>' for o in ops) or '<li>-</li>'
    return (f'<h1><span class="no">{no:02d}</span>{e(title)}</h1>'
            f'<div class="shot"><div class="img"><img src="{(SHOTS / fn).as_uri()}"></div>'
            f'<div class="side"><h3>概要</h3><p>{e(desc)}</p><h3>主な操作・表示</h3><ul>{ops_html}</ul>'
            f'<h3>関連する共通機能</h3><p>{e(funcs)}</p><h3>主なソース（frontend/src）</h3><div class="code">{e(src)}</div>'
            f'<h3>画像ファイル</h3><div class="code">screens/{e(fn)}</div></div></div>')


def cover():
    n = sum(len(v) for _, v in SC.CHAPTERS)
    return f'''
<div class="cover" style="height:245mm">
  <div class="band"></div>
  <div class="t1">心カテーテルレポート（React 版）<br><span style="font-size:22pt;color:#2e6b5e">画面イメージ集</span></div>
  <div class="t2">全 {n} 画面（タブ・ダイアログ・編集時の表示を含む）</div>
  <table>
    <tr><th style="width:32mm">対象</th><td>frontend（React 18 + TypeScript）。サンプルデータを読み込んだデモ版（Local Storage）で撮影</td></tr>
    <tr><th>版</th><td>{G.VERSION}</td></tr>
    <tr><th>作成日</th><td>{G.DATE}</td></tr>
    <tr><th>画面サイズ</th><td>横 1600px（縦は内容に合わせた全体）</td></tr>
    <tr><th>関連資料</th><td>設計資料 本文編（react_design_A4_text.pdf）・図面編（react_design_A3_diagrams.pdf）</td></tr>
  </table>
</div>'''


def toc(entries):
    """2段組みの目次。entries: [(level, title, page)]"""
    half = (len(entries) + 1) // 2
    # 章の途中で段が分かれないよう、次の章の見出しで区切る
    cut = next((i for i in range(half, len(entries)) if entries[i][0] == 1), half)
    cols = []
    for lo, hi in ((0, cut), (cut, len(entries))):
        rows = ''.join(f'<tr class="l{lvl}" data-i="{i}"><td>{e(t)}</td><td class="p">{pg}</td></tr>' for i, (lvl, t, pg) in enumerate(entries) if lo <= i < hi)
        cols.append(f'<table class="toc">{rows}</table>')
    return '<h1>目次</h1><div class="tocwrap">' + ''.join(cols) + '</div>'


def page(body):
    return G.page(body, 'A3').replace('</style>', EXTRA_CSS + '</style>')


async def render(parts):
    async with G.async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox', '--allow-file-access-from-files'])
        pg = await b.new_page()
        files = {}
        for pid, htm in parts:
            f = G.WORK / f'scr_{pid}.html'
            f.write_text(htm, encoding='utf-8')
            await pg.goto(f.as_uri())
            await pg.wait_for_load_state('networkidle')
            out = G.WORK / f'scr_{pid}.pdf'
            await pg.pdf(path=str(out), prefer_css_page_size=True, print_background=True)
            files[pid] = out
        await b.close()
    return files


def main():
    G.WORK.mkdir(parents=True, exist_ok=True)
    fmap = items()
    missing = [k for _, ks in SC.CHAPTERS for k in ks if k not in fmap or k not in SC.S]
    assert not missing, f'画像または説明がありません: {missing}'
    # ページ割り：表紙1・目次1・各画面1ページ（はみ出しは後で検査）
    seq, entries, no, pg = [], [], 0, 3
    for ch, keys in SC.CHAPTERS:
        entries.append((1, ch, pg))
        for k in keys:
            no += 1
            seq.append((f'{no:02d}', k, fmap[k], ch))
            entries.append((2, f'{no:02d}  {SC.S[k][0]}', pg))
            pg += 1
    total = pg - 1
    parts = [('cover', page(cover())), ('toc', page(toc(entries)))] + [(n, page(shot_page(int(n), k, f))) for n, k, f, ch in seq]
    files = asyncio.run(render(parts))
    for pid, f in files.items():
        assert len(PdfReader(str(f)).pages) == 1, f'{pid} が1ページに収まりません'
    secs = [('toc', '目次')] + [(n, ch) for n, k, f, ch in seq]
    ovs = asyncio.run(G.render_raw([(f'scr_ov_{pid}', G.overlay_html('A3', [(i + 2, sec)], total, TITLE)) for i, (pid, sec) in enumerate(secs)]))
    writer = PdfWriter()
    writer.add_page(PdfReader(str(files['cover'])).pages[0])
    for pid, sec in secs:
        p = PdfReader(str(files[pid])).pages[0]
        p.merge_page(PdfReader(str(ovs[f'scr_ov_{pid}'])).pages[0])
        writer.add_page(p)
    G.add_nav(writer, 'A3', page(toc(entries)), 1, entries)
    writer.add_metadata({'/Title': TITLE, '/Author': 'cath-report', '/Subject': '全画面のスクリーンショットと説明'})
    with open(OUT, 'wb') as f:
        writer.write(f)
    print(OUT, len(writer.pages), 'pages')


if __name__ == '__main__':
    main()

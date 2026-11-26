"""追加資料（比較表・非機能設計・課題と改善案・REST API 仕様）の共通部品"""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import gen_doc as G

e = G.e
table = G.table

STYLE = '''<style>
pre.json { font-family: "Noto Sans Mono CJK JP", "DejaVu Sans Mono", monospace; font-size: 7.9pt; line-height: 1.4; background: #f7f9f8;
  border: 0.6pt solid #cfd9d5; padding: 2mm 3mm; margin: 0 0 3mm; white-space: pre-wrap; word-break: break-all; page-break-inside: avoid; }
.ep { border: 0.8pt solid #8fb5a8; border-radius: 1.5mm; margin: 5mm 0 2mm; padding: 1.6mm 3mm; background: #eef5f2; break-inside: avoid; break-after: avoid; page-break-after: avoid; }
.ep .m { display: inline-block; min-width: 15mm; text-align: center; color: #fff; border-radius: 1mm; padding: 0 1.5mm; margin-right: 2mm; font-weight: 700; font-size: 9pt; }
.ep .p { font-family: "Noto Sans Mono CJK JP", monospace; font-weight: 700; font-size: 10.5pt; }
.ep .d { display: block; font-size: 9pt; color: #3c4c53; margin-top: 0.6mm; }
.m.GET { background: #3f7fbf; } .m.PUT { background: #c08a2e; } .m.POST { background: #4f8a5d; } .m.DELETE { background: #b5524a; }
.pri { display: inline-block; min-width: 7mm; text-align: center; border-radius: 1mm; font-weight: 700; color: #fff; }
.pri.高 { background: #b5524a; } .pri.中 { background: #c08a2e; } .pri.低 { background: #6d8a80; }
.cmp td:nth-child(2), .cmp td:nth-child(3) { width: 40%; }
.good { color: #2e6b5e; font-weight: 700; } .bad { color: #a14b42; font-weight: 700; }
.kv td:first-child { white-space: nowrap; font-weight: 700; color: #1f4f45; width: 34mm; }
.h2page { page-break-before: always; }
.kvb { table-layout: fixed; } .kvb thead { display: none; } .kvb td:first-child { width: 26mm; } .kvb td:first-child { white-space: nowrap; font-weight: 700; color: #1f4f45; background: #f3f6f4; }
h1, h2, h3 { break-after: avoid; page-break-after: avoid; }
</style>'''


def doc_cover(title, sub, desc, related):
    def cover(ed, size, other):
        return f'''
<div class="cover" style="height:255mm">
  <div class="band"></div>
  <div class="t1" style="font-size:22pt">心カテーテルレポート<br><span style="font-size:20pt;color:#2e6b5e">{e(title)}</span></div>
  <div class="t2">{e(sub)}</div>
  <table>
    <tr><th style="width:32mm">対象</th><td>{desc}</td></tr>
    <tr><th>版</th><td>{G.VERSION}</td></tr>
    <tr><th>作成日</th><td>{G.DATE}</td></tr>
    <tr><th>関連資料</th><td>{related}</td></tr>
  </table>
</div>'''
    return cover


def build_doc(title, sub, desc, related, parts, out):
    """gen_doc.build を使って A4 縦の資料を作る（表紙・目次・しおり・目次リンク・ヘッダ/ページ番号）"""
    G.TITLE = '心カテーテルレポート'
    G.part_cover = doc_cover(title, sub, desc, related)
    wrapped = [(pid, lvl, t, (lambda fn=fn: STYLE + fn()) if fn else None) for pid, lvl, t, fn in parts]
    G.build('A4', title, wrapped, out, '', '')


RELATED = '設計資料 本文編（react_design_A4_text.pdf）・図面編（react_design_A3_diagrams.pdf）・画面イメージ集（react_screen_images_A3.pdf）'

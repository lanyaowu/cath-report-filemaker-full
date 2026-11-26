"""画面項目一覧（カテ記録・CAG・PCI）の共通部品"""
import json
from extra_common import G, e, table

OPTS = json.load(open('/tmp/opts.json', encoding='utf-8'))
SHOTS = G.ROOT / 'docs/design/screens'

KIND = {
    'T': 'テキスト', 'TL': 'テキスト（候補）', 'N': '数値', 'R': 'ラジオ', 'C': 'チェック', 'S': '選択',
    'D': '日付', 'DT': '日付＋時刻', 'A': '複数行テキスト', 'K': '計算（表示のみ）', 'B': 'ボタン', 'P': '収縮期/拡張期/平均',
}

ITEM_CSS = '''<style>
.items td { font-size: 8.2pt; vertical-align: top; }
.items td.no { color: #6b7a80; white-space: nowrap; }
.items td.path { font-family: "DejaVu Sans Mono", monospace; font-size: 7.2pt; color: #24505f; word-break: break-all; }
.items td.kind { white-space: nowrap; }
.items tr.grp td { background: #e4eeea; color: #1f4f45; font-weight: 700; }
.items tr.grp td .bp { font-family: "DejaVu Sans Mono", monospace; font-weight: 400; font-size: 7.2pt; color: #4b6a73; margin-left: 6px; }
.shotbox { text-align: center; margin: 4mm 0; break-inside: avoid; }
.shotbox img { max-width: 100%; max-height: 120mm; border: 0.8pt solid #9fb0b6; }
.shotbox .cap { font-size: 8pt; color: #555; margin-top: 1mm; }
.fx { table-layout: fixed; width: 100%; } .fx td, .fx td.k { white-space: normal !important; overflow-wrap: anywhere; }
.badge { display: inline-block; font-size: 7pt; padding: 0 3px; border-radius: 2px; margin-right: 2px; color: #fff; }
.b-share { background: #2f7d6b; } .b-calc { background: #b0632a; } .b-rep { background: #546e7a; } .b-ref { background: #7b5ea7; }
</style>'''


def V(key):
    """options.ts の候補を「／」区切りの文字列に"""
    v = OPTS[key]
    out = []
    for x in v:
        if isinstance(x, dict):
            out.append(x.get('label') or x.get('key') or x.get('value'))
        elif isinstance(x, list):
            out.append(str(x[1]))
        else:
            out.append(str(x))
    return '／'.join(out)


def L(*xs):
    return '／'.join(xs)


SHARE = '<span class="badge b-share">共通</span>'
CALC = '<span class="badge b-calc">計算</span>'
REP = '<span class="badge b-rep">繰返し</span>'
REF = '<span class="badge b-ref">参照</span>'


class Counter:
    def __init__(self, prefix):
        self.prefix = prefix
        self.n = 0
        self.per = {}

    def next(self):
        self.n += 1
        return f'{self.prefix}-{self.n:03d}'


def items(cnt, groups):
    """groups: [(タイトル, ベースパス, [(項目, パス, 種別, 値・単位, 備考HTML), ...])]"""
    out = ['<table class="items"><thead><tr>'
           '<th style="width:14mm">No</th><th style="width:31mm">項目（画面）</th><th style="width:36mm">データパス</th>'
           '<th style="width:18mm">入力形式</th><th>選択肢・単位・基準</th><th style="width:34mm">備考</th></tr></thead><tbody>']
    for title, base, rows in groups:
        out.append(f'<tr class="grp"><td colspan="6">{e(title)}{f"<span class=bp>{e(base)}</span>" if base else ""}</td></tr>')
        cnt.per[title] = cnt.per.get(title, 0) + len(rows)
        for r in rows:
            lab, path, kind, vals, note = (list(r) + [''] * 5)[:5]
            out.append(f'<tr><td class="no">{cnt.next()}</td><td>{e(lab)}</td><td class="path">{e(path)}</td>'
                       f'<td class="kind">{e(KIND.get(kind, kind))}</td><td>{e(vals)}</td><td>{note}</td></tr>')
    out.append('</tbody></table>')
    return ''.join(out)


def labs(base, key, title, cnt):
    """検査値の定義（[キー, 名称, 単位, 下限, 上限]）から表を作る"""
    rows = []
    for d in OPTS[key]:
        k, lab, unit = d[0], d[1], d[2]
        lo = d[3] if len(d) > 3 else None
        hi = d[4] if len(d) > 4 else None
        rng = '' if lo is None and hi is None else f'{"" if lo is None else lo}〜{"" if hi is None else hi}'
        rows.append((lab, f'{k}', 'N', f'{unit}' + (f'　基準 {rng}' if rng else ''), '基準外はピンク表示' if rng else ''))
    return items(cnt, [(title, base, rows)])


def shot(fn, cap):
    p = SHOTS / fn
    if not p.exists():
        return ''
    return f'<div class="shotbox"><img src="{p.as_uri()}"><div class="cap">{e(cap)}</div></div>'


def legend():
    return ('<div class="note small">入力形式：テキスト（候補）＝候補リストから選ぶか自由入力、ラジオ＝同じ値の再クリックで解除できるものあり、計算＝入力不可の自動表示。'
            f'　{SHARE} 他画面と同じデータ　{CALC} 自動計算・算出ボタン　{REP} 同じ項目の繰返し（病変1〜5など）　{REF} 他画面の値を参照・編集</div>')


def kind_legend():
    return table(['入力形式', '説明'], [(v, {
        'テキスト': '自由入力', 'テキスト（候補）': '候補リストから選択、または自由入力（候補にない値も保存可）', '数値': '数値（右寄せ・半角で入力）。単位は表示のみ',
        'ラジオ': '一つを選択', 'チェック': 'あり／なし（true/false）', '選択': 'プルダウンから選択（自由入力不可）', '日付': 'YYYY-MM-DD',
        '日付＋時刻': '日付と時刻（HH:MM）の2欄', '複数行テキスト': '改行可の文章', '計算（表示のみ）': '他の項目から計算して表示。保存しない',
        'ボタン': '取得・算出・コピーなどの操作', '収縮期/拡張期/平均': '圧の3値（s/d/m）を1行で入力',
    }[v]) for v in KIND.values()], widths=['34mm', None])


def wrap(parts):
    """各パート（別々に描画される）に項目表の CSS を付ける"""
    return [(pid, lvl, t, (lambda fn=fn: ITEM_CSS + fn()) if fn else None) for pid, lvl, t, fn in parts]

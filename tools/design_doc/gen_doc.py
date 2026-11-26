#!/usr/bin/env python3
"""心カテーテルレポート（React 版）設計資料 PDF を生成する。

構成：表紙・目次／1 アプリの構成／2 機能一覧／3 データモデルの構造／4 ソース一覧／5 ロジックビュー
本文は A4 縦、大きな図は A3 横。各パートを Chrome で PDF にし、結合してヘッダ・ページ番号を付ける。
usage: python3 tools/design_doc/diagrams.py && python3 tools/design_doc/gen_doc.py
出力: docs/design/react_design_document.pdf
"""
import asyncio, html, io, pathlib, re, sys, datetime
from pypdf import PdfReader, PdfWriter
from playwright.async_api import async_playwright

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import content as C

ROOT = pathlib.Path(__file__).resolve().parents[2]
FE = ROOT / 'frontend'
IMG = ROOT / 'docs/design/img'
ERA3 = ROOT / 'docs/er_a3'
OUT = ROOT / 'docs/design/react_design_document.pdf'
WORK = ROOT / 'docs/design/_work'
TITLE = '心カテーテルレポート（React 版）設計資料'
VERSION = '1.0'
DATE = datetime.date.today().strftime('%Y年%m月%d日')
e = html.escape

CSS = '''
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; }
body { font-family: "Noto Sans CJK JP", "Noto Sans JP", sans-serif; color: #24323a; font-size: 9.6pt; line-height: 1.55; }
h1 { font-size: 17pt; color: #1f4f45; margin: 0 0 3mm; padding-bottom: 1.6mm; border-bottom: 2.2px solid #2e6b5e; }
h2 { font-size: 12.5pt; color: #2e6b5e; margin: 5mm 0 2mm; }
h3 { font-size: 10.5pt; color: #2e6b5e; margin: 3.5mm 0 1.4mm; }
p { margin: 0 0 2mm; }
.lead { color: #3c4c53; margin-bottom: 3mm; }
table { border-collapse: collapse; width: 100%; margin: 0 0 3mm; page-break-inside: auto; }
tr { page-break-inside: avoid; }
thead { display: table-header-group; }
th, td { border: 0.6pt solid #b6c4c0; padding: 1.1mm 1.6mm; vertical-align: top; text-align: left; }
th { background: #e4ebe7; color: #24423a; font-weight: 700; white-space: nowrap; }
td.c, th.c { text-align: center; }
td.r { text-align: right; white-space: nowrap; }
td.k { white-space: nowrap; font-weight: 700; color: #1f4f45; }
td.code, .code { font-family: "Noto Sans Mono CJK JP", "DejaVu Sans Mono", monospace; font-size: 8.4pt; }
td.small, .small { font-size: 8.4pt; color: #55656b; }
tr.grp td { background: #f3f6f4; font-weight: 700; color: #2e6b5e; }
.note { background: #f6f8f7; border-left: 3px solid #8fb5a8; padding: 2mm 3mm; margin: 2mm 0 3mm; font-size: 9pt; }
.fig { text-align: center; }
.fig img { max-width: 100%; }
.cap { text-align: center; font-size: 8.6pt; color: #5c6c72; margin-top: 1mm; }
.tree { font-family: "Noto Sans Mono CJK JP", monospace; font-size: 8.4pt; line-height: 1.45; white-space: pre; background: #f8faf9; border: 0.6pt solid #cfd9d5; padding: 2.5mm 3.5mm; }
.two { display: flex; gap: 6mm; } .two > div { flex: 1; min-width: 0; }
.legend span { display: inline-block; padding: 0.3mm 2mm; margin-right: 2mm; border: 0.6pt solid #aab; border-radius: 2px; font-size: 8.4pt; }
/* 表紙・目次 */
.cover { height: 260mm; display: flex; flex-direction: column; justify-content: center; }
.cover .band { height: 6mm; background: #2e6b5e; margin-bottom: 18mm; width: 60mm; }
.cover .t1 { font-size: 26pt; font-weight: 800; color: #1f4f45; line-height: 1.3; }
.cover .t2 { font-size: 14pt; color: #3c5a52; margin: 6mm 0 18mm; }
.cover table { width: 120mm; } .cover td { font-size: 10pt; }
.toc td { border: 0; border-bottom: 0.5pt dotted #b9c6c2; padding: 1.4mm 1mm; font-size: 10.5pt; }
.toc td.p { text-align: right; width: 18mm; }
.toc tr.l1 td { font-weight: 700; color: #1f4f45; padding-top: 3mm; }
.toc tr.l2 td:first-child { padding-left: 7mm; }
.toc .sz { font-size: 8pt; color: #7a8a86; margin-left: 2mm; }
/* 論理ビュー（レイヤー） */
.layers { display: flex; flex-direction: column; gap: 0; }
.layer { border: 1.4px solid; border-radius: 3mm; padding: 2.2mm 3mm 3mm; }
.layer .lt { font-weight: 800; font-size: 11pt; margin-bottom: 1.6mm; }
.layer .lt span { font-weight: 400; font-size: 8.8pt; color: #5c6c72; margin-left: 2mm; }
.layer .boxes { display: flex; gap: 3mm; }
.layer .box { flex: 1; background: #fff; border: 0.8pt solid #9fb0b6; border-radius: 2mm; padding: 1.6mm 2.4mm; font-size: 8.6pt; line-height: 1.45; }
.layer .box b { display: block; font-size: 9.4pt; color: #24323a; margin-bottom: 0.6mm; }
.arrowrow { text-align: center; color: #5d7b86; font-size: 8.6pt; line-height: 1; padding: 1.2mm 0; }
.layer { padding: 3mm 4mm 3.5mm; } .layer .lt { font-size: 13pt; margin-bottom: 2mm; } .layer .box { font-size: 10pt; padding: 2.2mm 3mm; line-height: 1.5; } .layer .box b { font-size: 11pt; } .arrowrow { font-size: 9.5pt; padding: 1.2mm 0; }
.arrowrow b { font-size: 13pt; display: block; line-height: 1; }
'''

A4CSS = '@page { size: A4 portrait; margin: 17mm 14mm 15mm 14mm; }'
A3CSS = '@page { size: A3 landscape; margin: 15mm 16mm 14mm 16mm; }'


def page(body, size):
    return f'<!DOCTYPE html><html lang="ja"><head><meta charset="utf-8"><style>{A4CSS if size == "A4" else A3CSS}{CSS}</style></head><body>{body}</body></html>'


def table(headers, rows, cls='', widths=None, raw=False):
    th = ''.join(f'<th{f" style=\"width:{w}\"" if widths and w else ""}>{e(h)}</th>' for h, w in zip(headers, widths or [None] * len(headers)))
    out = [f'<table class="{cls}"><thead><tr>{th}</tr></thead><tbody>']
    for r in rows:
        if isinstance(r, tuple) and len(r) == 2 and r[0] == '__grp__':
            out.append(f'<tr class="grp"><td colspan="{len(headers)}">{e(r[1])}</td></tr>')
            continue
        tds = []
        for v in r:
            if isinstance(v, tuple):
                v, c = v
                tds.append(f'<td class="{c}">{v if raw else e(str(v))}</td>')
            else:
                tds.append(f'<td>{v if raw else e(str(v))}</td>')
        out.append('<tr>' + ''.join(tds) + '</tr>')
    out.append('</tbody></table>')
    return ''.join(out)


def svg(name, max_h_mm, base=IMG):
    return f'<div class="fig"><img src="{(base / name).as_uri()}" style="max-height:{max_h_mm}mm"></div>'


def lines(p):
    try:
        return sum(1 for _ in open(p, encoding='utf-8'))
    except Exception:
        return ''


# ============================================================ 型定義の読み取り（types/model.ts）
def parse_model():
    src = (FE / 'src/types/model.ts').read_text(encoding='utf-8')
    out = {}
    for m in re.finditer(r'export interface (\w+)\s*\{', src):
        name = m.group(1)
        i, depth, j = m.end(), 1, m.end()
        while depth:
            if src[j] == '{':
                depth += 1
            elif src[j] == '}':
                depth -= 1
            j += 1
        body = src[i:j - 1]
        members, depth, cur = [], 0, ''
        k = 0
        while k < len(body):
            ch = body[k]
            if body.startswith('//', k):
                nl = body.find('\n', k)
                nl = len(body) if nl < 0 else nl
                comment = body[k + 2:nl].strip()
                if members and depth == 0 and not cur.strip():
                    members[-1] = (members[-1][0], members[-1][1], comment)
                k = nl
                continue
            if ch in '{(':
                depth += 1
            elif ch in '})':
                depth -= 1
            if (ch in ';\n') and depth == 0:
                if cur.strip():
                    members.append((cur.strip(), '', ''))
                cur = ''
            else:
                cur += ch
            k += 1
        if cur.strip():
            members.append((cur.strip(), '', ''))
        rows = []
        for raw, _, comment in members:
            mm = re.match(r'(\w+)\??\s*:\s*([\s\S]+)$', raw)
            if not mm:
                continue
            key, typ = mm.group(1), re.sub(r'\s+', ' ', mm.group(2)).strip()
            if typ.startswith('{'):
                keys = re.findall(r'(\w+)\??\s*:', typ[1:])
                depth_keys, d, top = [], 0, []
                # 1階層目のキーのみ
                t = typ[1:-1]
                buf, d = '', 0
                for ch in t:
                    if ch in '{(':
                        d += 1
                    if ch in '})':
                        d -= 1
                    if ch == ';' and d == 0:
                        top.append(buf)
                        buf = ''
                    else:
                        buf += ch
                top.append(buf)
                ks = [re.match(r'\s*(\w+)', x).group(1) for x in top if re.match(r'\s*(\w+)\??\s*:', x)]
                typ = '{ ' + '・'.join(ks) + ' }'
            rows.append((key, typ, comment))
        out[name] = rows
    return out


# ============================================================ 各パート
def part_cover(ed, size, other):
    h = 255 if size == 'A4' else 245
    return f'''
<div class="cover" style="height:{h}mm">
  <div class="band"></div>
  <div class="t1" style="font-size:{22 if size == 'A4' else 26}pt">心カテーテルレポート（React 版）設計資料<br><span style="font-size:20pt;color:#2e6b5e">{ed}</span></div>
  <div class="t2">アプリの構成／機能一覧／データモデルの構造／ソース一覧／ロジックビュー</div>
  <table>
    <tr><th style="width:32mm">対象</th><td>frontend（React 18 + TypeScript）と、保存先の REST API（Node.js 版・Spring Boot 版・Spring Boot + PostgreSQL 版）</td></tr>
    <tr><th>版</th><td>{VERSION}</td></tr>
    <tr><th>作成日</th><td>{DATE}</td></tr>
    <tr><th>用紙</th><td>{'A4 縦' if size == 'A4' else 'A3 横'}</td></tr>
    <tr><th>対になる資料</th><td>{other}</td></tr>
  </table>
</div>'''


def part_toc(entries, note=''):
    rows = []
    for i, (level, title, pg) in enumerate(entries):
        rows.append(f'<tr class="l{level}" data-i="{i}"><td>{e(title)}</td><td class="p">{pg}</td></tr>')
    return f'<h1>目次</h1><table class="toc">{"".join(rows)}</table>' + (f'<div class="note" data-note="1">{note}</div>' if note else '')


def part_intro():
    tech = [
        ('フロントエンド', 'React 18.3・TypeScript 5.6・Vite 5.4', 'SPA。外部 UI ライブラリなし（CSS は自作）'),
        ('状態管理', 'React Context（AppContext・FormContext）', 'Redux 等は使わず、Context と useState/useMemo で構成'),
        ('保存（既定）', 'ブラウザの localStorage', 'インストール不要。初回にサンプルデータを投入'),
        ('保存（Remote）', 'REST API（JSON）', '3種のバックエンドで同じ API'),
        ('バックエンド①', 'Node.js・Express 4・mongodb 6', 'backend-node'),
        ('バックエンド②', 'Java 17・Spring Boot 3.3・Spring Data MongoDB', 'backend-spring'),
        ('バックエンド③', 'Java 17・Spring Boot 3.3・Spring Data JPA・Flyway・PostgreSQL 16', 'backend-spring-pg'),
        ('対応ブラウザ', 'Chrome・Edge（最新版）', '画面は横 1600px 程度を想定'),
    ]
    terms = [
        ('レポート（CathReport）', '1回のカテーテル検査の記録。患者に対して N 件。'),
        ('セクション', 'レポート内の画面単位のデータ（cathRecord・cagLvg・pci など）。'),
        ('パス', 'データ内の位置をドット区切りで表したもの。例：report.cathRecord.exam.urgency。入力欄はパスで値を読み書きする。'),
        ('draft / original', '編集中のデータ／読込（保存）時のデータ。両者の差が「変更あり」。'),
        ('主画面', '複数画面に出る項目を編集できる画面。他の画面では参照表示（編集不可）。'),
        ('確定', 'レポートのステータス。確定済みは全項目ロック（ステータス・照合・登録者を除く）。'),
    ]
    return ('<h1>はじめに</h1>'
            '<p class="lead">本資料は、心カテーテル検査のレポートを入力・保存する Web アプリ（React 版）の設計をまとめたものです。'
            '開発・保守・レビューの参考資料として、アプリの構成、機能、データモデル、ソースの役割、内部ロジックを説明します。</p>'
            '<h2>対象範囲</h2><p>フロントエンド（frontend/）を中心に、Remote DB 選択時の保存先となる3種のバックエンド（backend-node・backend-spring・backend-spring-pg）を含みます。'
            '画面の詳細な項目は別資料「全入力項目一覧（field_list.xlsx）」、全画面のイメージは「画面イメージ集」を参照してください。</p>'
            '<h2>技術要素</h2>' + table(['区分', '技術', '備考'], tech, widths=['28mm', '78mm', None]) +
            '<h2>用語</h2>' + table(['用語', '説明'], terms, widths=['42mm', None]))


def part_system():
    return ('<h1>1. アプリの構成　1.1 システム構成図</h1>' + svg('system.svg', 205) +
            '<div class="note">ブラウザ内の React SPA が画面と状態を持ち、保存先は設定で切り替えます。既定は <b>localStorage</b>（サーバー不要）。'
            '<b>Remote DB</b> を選ぶと RemoteStorageAdapter が REST API（/api）を呼び、Node.js 版・Spring Boot（MongoDB）版・Spring Boot（PostgreSQL）版のいずれかが保存します。'
            '3つのバックエンドは同じ API・同じ JSON 形式です。</div>')


def part_components():
    return ('<h1>1. アプリの構成　1.2 コンポーネント構成図</h1>' + svg('components.svg', 215) +
            '<div class="note">App → AppProvider（状態）→ Main の下に TopBar・SideNav と、表示中の画面が入ります。入力画面は FormProvider の中に置かれ、'
            '入力部品（fields.tsx）が FormContext を通して編集中データを読み書きします。ScreenFrame（ロック表示＋患者属性ヘッダ）は全入力画面で使用します。</div>')


def part_dirs():
    groups = [
        ('frontend/', [('index.html・package.json・vite.config.ts・tsconfig.json', '設定・ビルド')]),
        ('frontend/src/', [('main.tsx', 'エントリポイント'), ('App.tsx', 'アプリ本体（画面の切替・ダイアログ）'), ('config.ts', '実行時の設定（public/config.js）'), ('styles.css', 'スタイル')]),
        ('  auth/', [('permissions.ts・session.ts', '役割と権限・ログイン情報')]),
        ('  state/', [('AppContext.tsx', 'アプリ状態・操作'), ('screens.ts', '画面定義')]),
        ('  form/', [('FormContext.tsx', 'フォームバインディング'), ('fields.tsx', '入力部品')]),
        ('  types/', [('model.ts', 'データモデル（型）')]),
        ('  model/', [('defaults.ts', '既定値・補完'), ('ownership.ts', '共有項目の主画面')]),
        ('  constants/', [('options.ts', '選択肢・項目定義')]),
        ('  utils/', [('calc.ts・date.ts', '計算・日付'), ('path.ts・id.ts', 'パス操作・ID')]),
        ('  storage/', [('StorageAdapter.ts・index.ts', 'インターフェース・切替'), ('LocalStorageAdapter.ts・RemoteStorageAdapter.ts', '保存先の実装')]),
        ('  components/', [('layout/', 'TopBar・SideNav・ScreenFrame・PatientHeader'), ('dialogs/', '新規作成・マスタ・設定・ログイン'), ('common/ui.tsx', '共通部品')]),
        ('  screens/', [('ReportList・PatientInfo・ImagesScreen・MaceScreen・PcpsScreen・RestudyScreen・StatsScreen', '単一ファイルの画面'),
                        ('CathRecord/・CagLvg/・Pci/・PressureIvus/・Conference/', '複数ファイルの画面')]),
        ('  data/', [('patients・reports・masters.json', 'サンプルデータ')]),
        ('frontend/test/', [('*.test.ts', '単体テスト（node:test）')]),
        ('backend-node/', [('src/', 'Express + MongoDB（security・auth・rules を含む）'), ('test/', '単体テスト')]),
        ('backend-spring/', [('src/main/java/…', 'Spring Boot + MongoDB')]),
        ('backend-spring-pg/', [('src/main/java/…・db/migration/', 'Spring Boot + PostgreSQL')]),
        ('sample-data/・docs/・tools/', [('', 'サンプルデータ・資料・資料生成ツール')]),
    ]
    rows = []
    for d, items in groups:
        for i, (f, desc) in enumerate(items):
            rows.append(((d if i == 0 else '', 'code'), (f, 'code'), desc))
    screens = [(s[0], s[1], s[2], s[3]) for s in [
        ('list', '一覧', '-', '不要'), ('patient', '患者情報入力', 'patient', '必要'), ('cathRecord', 'カテ記録', 'cathRecord', '必要'),
        ('cagLvg', 'CAG/LVG', 'cagLvg', '必要'), ('restudy', 'Restudy', 'restudy', '必要'), ('pci', 'PCI', 'pci', '必要'),
        ('pressureIvus', 'Pressure/IVUS', 'pressureIvus', '必要'), ('images', '画像', 'images', '必要'), ('pcps', 'PCPS', 'pcps', '必要'),
        ('conference', 'カンファレンス', 'conference', '必要'), ('mace', 'MACE', 'mace', '必要'), ('stats', '集計', '-', '不要')]]
    api = [('GET', '/api/health', 'ヘルスチェック（ログイン不要）'), ('POST / GET / POST', '/api/auth/login・/me・/logout', 'ログイン（トークン）・利用者・ログアウト'),
           ('GET', '/api/audit', '監査ログ（管理者）'), ('GET / PUT / POST / DELETE', '/api/patients[/{id}]', '患者の一覧・取得・登録/更新・削除（レポートがあれば 409）'),
           ('GET / PUT / POST / DELETE', '/api/reports[/{id}]', 'レポートの一覧（画像本体を除く）・取得・登録/更新・削除'),
           ('GET / PUT', '/api/masters', 'マスタの取得・更新（更新は管理者）'), ('POST', '/api/admin/seed', 'サンプルデータ投入（全置換。管理者かつ ALLOW_SEED_API=true のとき）'),
           ('GET', '/api/stats/monthly・/api/stats/mace', '集計ビュー（PostgreSQL 版のみ）')]
    return ('<h1>1. アプリの構成　1.3 ディレクトリ構成</h1>' + table(['フォルダ', 'ファイル', '内容'], rows, widths=['38mm', '78mm', None]) +
            '<h2>1.4 画面とセクションの対応（state/screens.ts）</h2>' +
            table(['キー', '画面名', 'レポートのセクション', 'レコード'], [((a, 'code'), b, (c, 'code'), (d, 'c')) for a, b, c, d in screens], widths=['32mm', '40mm', '45mm', None]) +
            '<p class="small">画面クリア（ごみ箱）は、対応するセクションを既定値に戻します。患者情報入力は Patient、一覧・集計はレコード不要です。</p>'
            '<h2>1.5 REST API（Remote DB 選択時・3バックエンド共通）</h2>' +
            table(['メソッド', 'パス', '内容'], [(a, (b, 'code'), c) for a, b, c in api], widths=['40mm', '62mm', None]) +
            '<p class="small">エラーは {"error": "メッセージ"} 形式。health・login 以外は Authorization: Bearer が必要（401）。権限がなければ 403。更新時は version が必須で、DB と異なれば 409。詳細は「REST API 詳細仕様」。</p>')


def part_funcs():
    common = [((a, 'c'), (b, 'k'), c, (d, 'small')) for a, b, c, d in C.COMMON_FUNCS]
    scr = [((a, 'k'), b, (c, 'r'), (d, 'r'), (f, 'small code')) for a, b, c, d, f in C.SCREEN_FUNCS]
    calc = [((a, 'k'), b, c, (d, 'small code')) for a, b, c, d in C.CALCS]
    return ('<h1>2. 機能一覧</h1><p class="lead">共通機能（全画面に関わる機能）と、画面ごとの機能をまとめます。</p>'
            '<h2>2.1 共通機能</h2>' + table(['No', '機能', '内容', '主な実装'], common, widths=['11mm', '30mm', None, '44mm']) +
            '<h2>2.2 画面別の機能</h2>' + table(['画面', '主な機能・項目', '項目数', '入力欄数', '主なソース'], scr, widths=['24mm', None, '13mm', '15mm', '28mm']) +
            '<p class="small">項目数：項目パス単位の件数（繰返しは1件）。入力欄数：病変×5・Device×10 などを展開した数（全入力項目一覧 field_list.xlsx の集計）。全体で 1,040 項目・2,225 入力欄。</p>'
            '<h2>2.3 自動計算・判定</h2>' + table(['計算', '入力', '内容', '実装'], calc, widths=['30mm', '38mm', None, '38mm']))


def part_model_fig():
    return ('<h1>3. データモデルの構造　3.1 全体構造</h1>' + svg('model.svg', 212) +
            '<div class="note">患者（Patient）1件に対しレポート（CathReport）が N 件。レポートは各画面のデータ（セクション）をまとめて持ち、'
            '保存・読込はレポート単位です。◆ はレポートに含まれる（同時に保存される）ことを表します。PCI 病変・Pressure Wire の病変・IVUS 病変は 1〜5 の可変長（Pressure と IVUS は同じ数）、MACE は 5 の固定長です。'
            '青破線はデータの連携（外部キーではなく、同じ番号・名前の一致・複写でつながる関係）で、詳細は本文編 3.7 と ER 図（docs/ER.md）にあります。</div>')


ER_PAGES = [('er_a3_02_patients_masters.svg', '患者・マスタ'), ('er_a3_03_report_common.svg', 'レポート共通（ヘッダ・画像・Restudy・履歴）'),
            ('er_a3_04_cath_record.svg', 'カテ記録'), ('er_a3_05_cag_lvg.svg', 'CAG / LVG'), ('er_a3_06_pci.svg', 'PCI'),
            ('er_a3_07_pressure_pcps_others.svg', 'Pressure/IVUS・PCPS・カンファレンス・MACE')]


def part_er(i, f, t):
    return f'<h1>3. データモデルの構造　3.6 詳細図（{i}/{len(ER_PAGES)}）{e(t)}</h1>' + svg(f, 238, ERA3)


def part_model_tables():
    m = parse_model()
    ents = [((a, 'k code'), b, c, (d, 'code small'), (n, 'c')) for a, b, c, d, n in C.ENTITIES]
    out = ['<h1>3. データモデルの構造　3.2 エンティティ一覧</h1>',
           table(['型', '名称', '内容', '保存場所', '件数'], ents, widths=['28mm', '26mm', None, '46mm', '17mm']),
           '<h2>3.3 値の表し方</h2>', table(['区分', 'ルール'], [((a, 'k'), b) for a, b in C.VALUE_RULES], widths=['26mm', None]),
           '<h2>3.4 永続化の対応</h2>', table(['保存先', 'キー / コレクション / テーブル', '内容'], [((a, 'k'), (b, 'code'), c) for a, b, c in C.PERSIST], widths=['44mm', '58mm', None])]
    order = ['Patient', 'Admission', 'CathReport', 'CathRecord', 'CagLvg', 'SegmentFinding', 'Collateral', 'BypassGraft', 'Pci', 'PciLesion', 'DeviceItem',
             'PressureIvus', 'PressureCol', 'IvusLesion', 'Pcps', 'Conference', 'MedRow', 'MaceEntry', 'MaceEvent', 'ImageItem', 'Restudy', 'ReportHistory',
             'Masters', 'Draft', 'Triple', 'NameSize', 'ShapeSize', 'DateTime']
    out.append('<h1 style="page-break-before:always">3. データモデルの構造　3.5 型定義（types/model.ts）</h1>'
               '<p class="lead">型ごとのメンバーです。入れ子のオブジェクトは { } 内に1階層目のキーを示します（全項目は field_list.xlsx）。</p>')
    for name in order:
        if name not in m:
            continue
        rows = [((k, 'code'), (t, 'code small'), C.DESC.get(f'{name}.{k}', c)) for k, t, c in m[name]]
        out.append(f'<h3>{name}</h3>' + table(['メンバー', '型', '説明'], rows, widths=['34mm', '82mm', None]))
    out.append('<h1 style="page-break-before:always">3. データモデルの構造　3.7 病変（Target）のデータ連携</h1>'
               '<p class="lead">病変を表すデータは画面ごとに別の配列にあり、病変 ID（共通のキー）はありません。'
               '「同一」「同じ番号」「名前の一致」「複写・集計」の 4 種類でつながります（図は図面編 3.1・3.6 の青破線）。</p>' +
               table(['種類', '元', '先', '内容'], [((a, 'k'), (b, 'code small'), (c, 'code small'), d) for a, b, c, d in C.LESION_LINKS], widths=['20mm', '38mm', '40mm', None]) +
               '<h2>注意点と改善案</h2>' +
               table(['対象', '内容', '改善案'], [((a, 'k'), b, c) for a, b, c in C.LESION_ISSUES], widths=['28mm', None, '62mm']))
    return ''.join(out)


def part_sources():
    rows = []
    cats = {}
    for p, (cat, fn, desc) in C.FRONTEND.items():
        cats.setdefault(cat, []).append((p, fn, desc))
    order = ['起動', '画面', '状態', 'フォーム', 'モデル', 'ロジック', '保存', 'データ', '設定']
    total = 0
    for cat in order:
        rows.append(('__grp__', f'frontend：{cat}'))
        for p, fn, desc in cats.get(cat, []):
            n = lines(FE / p)
            total += n if isinstance(n, int) and not p.endswith('.json') else 0
            rows.append(((p.replace('src/', ''), 'code'), (fn, 'k'), desc, (n if not p.startswith('src/data') else '-', 'r')))
    out = ['<h1>4. ソース一覧</h1><p class="lead">機能（役割）と説明、行数です。frontend は src/ からの相対パスで示します。</p>',
           '<h2>4.1 フロントエンド（frontend/）</h2>', table(['ファイル', '機能', '説明', '行数'], rows, widths=['56mm', '34mm', None, '11mm'], raw=False),
           f'<p class="small">TypeScript / TSX / CSS 合計 約 {total:,} 行（サンプル JSON を除く）。</p>']
    for title, items in C.BACKENDS:
        out.append(f'<h2>4.{len(out) - 2} {e(title)}</h2>')
        out.append(table(['ファイル', '機能', '説明'], [((a, 'code'), (b, 'k'), c) for a, b, c in items], widths=['70mm', '26mm', None]))
    return ''.join(out)


def part_layers():
    def layer(title, sub, color, fill, boxes):
        bx = ''.join(f'<div class="box"><b>{t}</b>{d}</div>' for t, d in boxes)
        return f'<div class="layer" style="border-color:{color};background:{fill}"><div class="lt" style="color:{color}">{title}<span>{sub}</span></div><div class="boxes">{bx}</div></div>'

    def arrow(t):
        return f'<div class="arrowrow"><b>▼</b>{t}</div>'
    body = ('<h1>5. ロジックビュー　5.1 論理アーキテクチャ（レイヤー構成）</h1>'
            '<p class="lead">上の層は下の層だけを使います（下の層は上の層を知りません）。画面は状態と入力部品を通してデータを扱い、保存先の違いはインフラ層で吸収します。</p>'
            '<div class="layers">' +
            layer('① プレゼンテーション層', 'App.tsx・components/・screens/', '#4f8a5d', '#eef6ee', [
                ('レイアウト', 'TopBar・SideNav・ScreenFrame・PatientHeader'),
                ('画面（13）', 'ReportList・PatientInfo・CathRecord・CagLvg・Pci（10タブ）・PressureIvus・Pcps・Conference・Mace・Images・Restudy・Stats'),
                ('ダイアログ・共通部品', 'NewReport・Master・Settings／Panel・Tabs・Modal・Btn・Toast'),
                ('画面固有のロジック', '条件付き入力・コピー/取込ボタン・計算欄の表示・時間経過シート')]) +
            arrow('入力欄を配置し、パスを渡す／遷移・保存を依頼') +
            layer('② フォームバインディング層', 'form/', '#4d73a5', '#f1f5fb', [
                ('FormProvider / Scope', '編集対象（FormApi）と相対パスの起点を配下に提供。"/" 始まりは絶対パス'),
                ('useField(path)', '値・set・変更あり（黄色）・参照のみ（主画面以外）・ロック（確定）を返す'),
                ('入力部品（fields.tsx）', 'TextF・NumF・DateF・TimeF・SelectF・TextAreaF・CheckF・RadioF・TripleF・DateTimeF・Calc・RefLink')]) +
            arrow('FormApi.set(path, 値)／主画面の判定') +
            layer('③ アプリケーション層', 'state/AppContext.tsx・state/screens.ts', '#3f6f9e', '#e6f0fa', [
                ('状態', 'screen・draft・original・isNew・highlight・filter・patients・reports・masters・settings'),
                ('派生値', 'isDirty（draft≠original または新規）・filteredReports・form（FormApi、確定ロックを含む）'),
                ('操作', 'guard・goto・openReport・newReport・save・deleteReport・clearSection・changeSettings・resetSample・saveMasters・refresh')]) +
            arrow('既定値・判定・計算を使う／永続化を依頼') +
            layer('④ ドメイン層', 'types/・model/・utils/calc・utils/date・constants/', '#b07a2f', '#fdf6ea', [
                ('データモデル', 'types/model.ts（Patient・CathReport・各セクション・Draft）'),
                ('既定値・補完', 'model/defaults.ts（createEmpty*・SECTION_FACTORIES・normalizeReport）'),
                ('主画面', 'model/ownership.ts（OWNERSHIP・ownerOf）'),
                ('計算・判定', 'utils/calc.ts（BSA・BMI・LVG・HBR・CREDO・IVUS・基準値）・utils/date.ts'),
                ('定義', 'constants/options.ts（選択肢・項目キー・基準範囲）')]) +
            arrow('読み書き') +
            layer('⑤ インフラ層', 'storage/・utils/path・utils/id', '#6d7a80', '#f4f4f4', [
                ('StorageAdapter', '患者・レポート・マスタの list / get / save / delete、resetWithSample'),
                ('LocalStorageAdapter', 'localStorage（既定）・サンプル投入'),
                ('RemoteStorageAdapter', 'fetch → REST /api（Node / Spring-Mongo / Spring-PostgreSQL）'),
                ('パス操作', 'getAt・setAt（イミュータブル）・deepEqual・mergeDefaults・hasAnyValue')]) +
            '</div>')
    return body


def part_state():
    return ('<h1>5. ロジックビュー　5.2 編集状態の遷移</h1>' + svg('state.svg', 150) +
            '<div class="note">「変更あり」は draft と original の比較で決まり、保存に成功すると original が保存結果に置き換わって「変更なし」に戻ります。'
            '新規は保存するまで常に「変更あり」です。確認ダイアログで「キャンセル」を選ぶと、遷移せずに変更項目を黄色で示します。</div>'
            '<h2>5.3 入力1件の処理の流れ</h2>' + svg('input_flow.svg', 62))


def part_seq():
    return ('<h1>5. ロジックビュー　5.4 処理シーケンス（レコードを開く／保存）</h1>'
            '<div class="two"><div><h3>レコードを開く（openReport）</h3>' + svg('seq_open.svg', 220) + '</div>'
            '<div><h3>保存（save）</h3>' + svg('seq_save.svg', 225) + '</div></div>')


def part_logic_tables():
    rules = [((a, 'k'), (b, 'code small'), c) for a, b, c in C.LOGIC_RULES]
    api = [((a, 'code'), b) for a, b in C.APP_API]
    field = [('full', '絶対パス（Scope を解決したもの）'), ('value', 'draft のその位置の値'), ('set(v)', 'FormApi.set(full, v) を呼ぶ'),
             ('changed', 'highlight 中で value ≠ original のとき true（黄色表示）'), ('readOnly', '確定済み、または主画面以外のとき true'),
             ('ref / refTitle', '主画面以外のとき：主画面の情報と「参照のみ：○○画面で編集します」')]
    return ('<h1>5. ロジックビュー　5.5 主要ロジック</h1>' + table(['ロジック', '実装', '内容'], rules, widths=['24mm', '42mm', None]) +
            '<h2>5.6 AppContext の公開 API（useApp）</h2>' + table(['名前', '内容'], api, widths=['78mm', None]) +
            '<h2>5.7 useField(path) の戻り値</h2>' + table(['名前', '内容'], [((a, 'code'), b) for a, b in field], widths=['34mm', None]) +
            '<h2>5.8 入力部品の表示ルール</h2>' +
            table(['表示', '条件', 'スタイル'], [
                ('黄色', '確認ダイアログで「キャンセル」後、original から変わった欄', '.changed'),
                ('ピンク', '基準値外の検査値、FFR≦0.80 等、必須欄の未入力', '.abn・.req'),
                ('参照表示（淡い青・点線）', '主画面以外の画面での共有項目。主画面へのリンク（RefLink）付き', '.ref'),
                ('入力不可（灰色）', '確定済み、または条件付き入力の条件を満たさない欄', 'readOnly・.disabled'),
                ('計算欄', '自動計算の結果（編集不可）', '.calc')], widths=['40mm', None, '30mm']))


# ============================================================ PDF 生成
# (id, 目次レベル, 目次の題名, 関数)  関数 None は見出しのみ（次のパートのページを指す）
PARTS_A4 = [
    ('intro', 1, 'はじめに（対象範囲・技術要素・用語）', part_intro),
    ('h1', 1, '1. アプリの構成（図は図面編）', None),
    ('dirs', 2, '1.3 ディレクトリ構成／1.4 画面とセクション／1.5 REST API', part_dirs),
    ('funcs', 1, '2. 機能一覧（共通機能・画面別・自動計算）', part_funcs),
    ('h3', 1, '3. データモデルの構造（図は図面編）', None),
    ('modeltbl', 2, '3.2 エンティティ一覧／3.3 値の表し方／3.4 永続化の対応／3.5 型定義／3.7 病変のデータ連携', part_model_tables),
    ('src', 1, '4. ソース一覧（フロントエンド・バックエンド・その他）', part_sources),
    ('h5', 1, '5. ロジックビュー（図は図面編）', None),
    ('logic', 2, '5.5 主要ロジック／5.6 AppContext API／5.7 useField／5.8 表示ルール', part_logic_tables),
]
PARTS_A3 = [
    ('h1', 1, '1. アプリの構成', None),
    ('system', 2, '1.1 システム構成図', part_system),
    ('components', 2, '1.2 コンポーネント構成図', part_components),
    ('h3', 1, '3. データモデルの構造', None),
    ('model', 2, '3.1 全体構造', part_model_fig),
] + [(f'er{i}', 2, f'3.6 詳細図 {i}：{t}', (lambda i=i, f=f, t=t: part_er(i, f, t))) for i, (f, t) in enumerate(ER_PAGES, 1)] + [
    ('h5', 1, '5. ロジックビュー', None),
    ('layers', 2, '5.1 論理アーキテクチャ（レイヤー構成）', part_layers),
    ('state', 2, '5.2 編集状態の遷移／5.3 入力1件の処理の流れ', part_state),
    ('seq', 2, '5.4 処理シーケンス（レコードを開く／保存）', part_seq),
]
DOCS = [
    ('A4', '本文編', PARTS_A4, ROOT / 'docs/design/react_design_A4_text.pdf', '図面編（react_design_A3_diagrams.pdf）：システム構成図・コンポーネント構成図・データモデル図・ロジックビューの図',
     '1.1・1.2（構成図）、3.1・3.6（データモデル図）、5.1〜5.4（ロジックビューの図）は A3 の図面編にあります。'),
    ('A3', '図面編', PARTS_A3, ROOT / 'docs/design/react_design_A3_diagrams.pdf', '本文編（react_design_A4_text.pdf）：機能一覧・データモデルの表・ソース一覧・主要ロジック',
     '2. 機能一覧、4. ソース一覧、および 1.3〜1.5・3.2〜3.5・3.7・5.5〜5.8 の表は A4 の本文編にあります。'),
]


async def render_all(parts_html):
    WORK.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox', '--allow-file-access-from-files'])
        pg = await b.new_page()
        files = {}
        for pid, size, body in parts_html:
            pid = f'{size}_{pid}'
            f = WORK / f'{pid}.html'
            f.write_text(page(body, size), encoding='utf-8')
            await pg.goto(f.as_uri())
            await pg.wait_for_load_state('networkidle')
            pdf = WORK / f'{pid}.pdf'
            await pg.pdf(path=str(pdf), prefer_css_page_size=True, print_background=True)
            files[pid.split('_', 1)[1]] = pdf
        await b.close()
    return files


async def render_raw(items):
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox'])
        pg = await b.new_page()
        files = {}
        for oid, htm in items:
            f = WORK / f'{oid}.html'
            f.write_text(htm, encoding='utf-8')
            await pg.goto(f.as_uri())
            out = WORK / f'{oid}.pdf'
            await pg.pdf(path=str(out), prefer_css_page_size=True, print_background=False)
            files[oid] = out
        await b.close()
    return files


def overlay_html(size, pages, total, title):
    """ヘッダ（資料名・章）とページ番号だけのページ。本文の PDF に重ねる（フォントは Chrome が埋め込む）"""
    w, h = (210, 297) if size == 'A4' else (420, 297)
    css = (f'@page {{ size: {w}mm {h}mm; margin: 0; }} html,body{{margin:0;padding:0}}'
           f'.pg{{width:{w}mm;height:{h}mm;position:relative;page-break-after:always;overflow:hidden;font-family:"Noto Sans CJK JP",sans-serif;color:#6b7f80}}'
           '.hd{position:absolute;left:14mm;right:14mm;top:6.2mm;font-size:7.5pt;display:flex;justify-content:space-between;border-bottom:0.5pt solid #bfcbc9;padding-bottom:1mm}'
           '.ft{position:absolute;left:0;right:0;bottom:5mm;text-align:center;font-size:8pt}')
    body = ''.join(f'<div class="pg"><div class="hd"><span>{e(title)}</span><span>{e(sec)}</span></div><div class="ft">{n} / {total}</div></div>' for n, sec in pages)
    return f'<!DOCTYPE html><html lang="ja"><head><meta charset="utf-8"><style>{css}</style></head><body>{body}</body></html>'



MARGIN_MM = {'A4': (17, 14), 'A3': (15, 16)}   # (上, 左)
PAGE_MM = {'A4': (210, 297), 'A3': (420, 297)}
PX = 72 / 96  # Chrome の PDF：1px = 0.75pt
MM = 72 / 25.4


async def _measure(htm, size):
    """目次 HTML を印刷時と同じ幅で描画し、行（data-i）と注記（data-note）の位置を px で返す"""
    w_mm = PAGE_MM[size][0] - 2 * MARGIN_MM[size][1]
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox'])
        pg = await b.new_page(viewport={'width': round(w_mm * 96 / 25.4), 'height': 1200})
        await pg.emulate_media(media='print')
        f = WORK / f'measure_{size}.html'
        f.write_text(htm, encoding='utf-8')
        await pg.goto(f.as_uri())
        r = await pg.evaluate("""() => {
            const g = (el) => { const r = el.getBoundingClientRect(); return [r.left, r.top, r.width, r.height]; };
            return { rows: [...document.querySelectorAll('[data-i]')].map(el => [+el.dataset.i, ...g(el)]),
                     notes: [...document.querySelectorAll('[data-note]')].map(g) };
        }""")
        await b.close()
    return r


def _rect(size, box):
    """px（本文左上基準）→ PDF 座標 [x1, y1, x2, y2]"""
    top, left = MARGIN_MM[size]
    H = PAGE_MM[size][1] * MM
    x, y, w, h = box
    x1, y1 = left * MM + x * PX, H - (top * MM + (y + h) * PX)
    return [x1, y1, x1 + w * PX, y1 + h * PX]


def add_nav(writer, size, toc_html, toc_index, entries, external=None, note_target=None):
    """しおり（entries の階層）と目次のリンクを付ける。
    entries: [(level, title, page_no)]（1始まり）。external: {行番号: (ファイル名, ページ番号)} は別 PDF へのリンク。"""
    from pypdf.generic import DictionaryObject, NameObject, ArrayObject, FloatObject, NumberObject, TextStringObject, BooleanObject
    from pypdf.annotations import Link
    writer.add_outline_item('表紙', 0)
    writer.add_outline_item('目次', toc_index)
    parent = None
    for level, title, pg in entries:
        if level <= 1:
            parent = writer.add_outline_item(title, pg - 1)
        else:
            writer.add_outline_item(title, pg - 1, parent=parent)
    writer.page_mode = '/UseOutlines'
    m = asyncio.run(_measure(toc_html, size))

    def remote(rect, fname, pg):
        writer.add_annotation(toc_index, DictionaryObject({
            NameObject('/Type'): NameObject('/Annot'), NameObject('/Subtype'): NameObject('/Link'),
            NameObject('/Rect'): ArrayObject([FloatObject(v) for v in rect]),
            NameObject('/Border'): ArrayObject([NumberObject(0)] * 3),
            NameObject('/A'): DictionaryObject({
                NameObject('/S'): NameObject('/GoToR'), NameObject('/F'): TextStringObject(fname),
                NameObject('/D'): ArrayObject([NumberObject(pg - 1), NameObject('/Fit')]),
                NameObject('/NewWindow'): BooleanObject(True)})}))

    for i, *box in m['rows']:
        rect = _rect(size, box)
        if external and i in external:
            remote(rect, *external[i])
        else:
            writer.add_annotation(toc_index, Link(rect=rect, target_page_index=entries[i][2] - 1))
    if note_target and m['notes']:
        remote(_rect(size, m['notes'][0]), *note_target)


def build(size, ed, parts, out, other, note, external=None, note_target=None):
    real = [(pid, lvl, t, fn) for pid, lvl, t, fn in parts if fn is not None]
    printable = [('cover', size, part_cover(ed, size, other))] + [(pid, size, fn()) for pid, lvl, t, fn in real]
    toc_dummy = part_toc([(lvl, t, 0) for pid, lvl, t, fn in parts], note)
    files = asyncio.run(render_all(printable + [('toc', size, toc_dummy)]))
    counts = {pid: len(PdfReader(str(f)).pages) for pid, f in files.items()}
    order = ['cover', 'toc'] + [pid for pid, *_ in real]
    start, pgno = {}, 1
    for pid in order:
        start[pid] = pgno
        pgno += counts[pid]
    entries = []
    for i, (pid, lvl, t, fn) in enumerate(parts):
        target = pid if fn else next(p_ for p_, l_, t_, f_ in parts[i:] if f_)
        entries.append((lvl, t, start[target]))
    files.update(asyncio.run(render_all([('toc', size, part_toc(entries, note))])))
    assert len(PdfReader(str(files['toc'])).pages) == counts['toc'], '目次のページ数が変わりました'
    total = pgno - 1
    title = f'{TITLE}（{ed}）'
    cur_sec, overlays = '目次', []
    lvl_of = {pid: lvl for pid, lvl, t, fn in parts}
    for i, (pid, lvl, t, fn) in enumerate(parts):
        pass
    sec_of = {}
    cur = '目次'
    for pid, lvl, t, fn in parts:
        if lvl == 1:
            cur = re.sub(r'（.*?）', '', t)
        if fn:
            sec_of[pid] = cur
    sec_of['toc'] = '目次'
    for pid in order[1:]:
        overlays.append((f'ov_{size}_{pid}', pid, [(start[pid] + k, sec_of[pid]) for k in range(counts[pid])]))
    ov_files = asyncio.run(render_raw([(oid, overlay_html(size, pgs, total, title)) for oid, pid, pgs in overlays]))
    ovmap = {pid: ov_files[oid] for oid, pid, pgs in overlays}
    writer = PdfWriter()
    for pid in order:
        ov = PdfReader(str(ovmap[pid])).pages if pid != 'cover' else None
        for k, pg in enumerate(PdfReader(str(files[pid])).pages):
            if ov is not None:
                pg.merge_page(ov[k])
            writer.add_page(pg)
    add_nav(writer, size, page(part_toc(entries, note), size), start['toc'] - 1, entries,
            external=external and external(entries), note_target=note_target)
    writer.add_metadata({'/Title': title, '/Author': 'cath-report', '/Subject': 'アプリの構成・機能一覧・データモデル・ソース一覧・ロジックビュー'})
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, 'wb') as f:
        writer.write(f)
    print(out, len(writer.pages), 'pages')
    return entries
    for pid in order:
        print(f'  {pid:10s} p.{start[pid]:>3}  {counts[pid]} 頁')


def main():
    WORK.mkdir(parents=True, exist_ok=True)
    a4, a3 = DOCS
    a3_entries = build(*a3, note_target=(a4[3].name, 2))
    a3_page = {t: pg for lvl, t, pg in a3_entries}

    def ext(entries):  # 本文編の「（図は図面編）」行 → 図面編の同じ章
        out = {}
        for i, (lvl, t, pg) in enumerate(entries):
            if '図は図面編' in t:
                out[i] = (a3[3].name, a3_page[t.replace('（図は図面編）', '')])
        return out
    build(*a4, external=ext, note_target=(a3[3].name, 2))


if __name__ == '__main__':
    main()

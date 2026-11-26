#!/usr/bin/env python3
"""データモデル・データフロー資料（統合版）を作る：図 → HTML → PDF（A3 横）

usage: python3 tools/docs/datamodel/build.py
  出力 docs/datamodel/datamodel_dataflow.pdf（と .html・img/）
  必要：Graphviz の dot、mermaid-cli の mmdc、Chrome（環境変数 CHROME、既定 /usr/bin/google-chrome）、Pillow
  選択値の表は sample-data/option-masters.json から作る（npx tsx tools/gen_option_masters.ts で更新）
"""
import json, collections, os, pathlib, runpy, subprocess
TOOL = pathlib.Path(__file__).resolve().parent
ROOT = TOOL.parents[2]
D = ROOT / 'docs' / 'datamodel'
runpy.run_path(str(TOOL / 'diagrams.py'))
OPT = json.load(open(ROOT / 'sample-data' / 'option-masters.json', encoding='utf-8'))

CSS = '''
@page { size: 420mm 297mm; margin: 0; }
* { box-sizing: border-box; }
body { margin: 0; font-family: "Noto Sans CJK JP", sans-serif; color: #1e3540; }
.pg { width: 420mm; height: 297mm; padding: 14mm 16mm 12mm; page-break-after: always; position: relative; overflow: hidden; background: #fff; display: flex; flex-direction: column; }
.pg.cover { background: #1e3540; color: #f4f6f1; padding: 36mm 30mm; }
.cover .bar { position:absolute; left:0; top:0; bottom:0; width: 6mm; background:#2e7d5b; }
.cover .k { color:#7fc4a0; font-weight:700; letter-spacing:2px; font-size: 15pt; }
.cover h1 { font-size: 44pt; margin: 8mm 0 6mm; line-height:1.2; }
.cover .sub { font-size: 17pt; color:#d4e2db; }
.cover .toc { margin-top: 16mm; display:grid; grid-template-columns: 1fr 1fr; gap: 3mm 14mm; font-size: 13.5pt; color:#cfe6da; max-width: 300mm; }
.cover .toc b { color:#7fc4a0; display:inline-block; width: 12mm; }
.cover .foot { position:absolute; left:30mm; bottom: 20mm; font-size: 11pt; color:#9fb4ad; line-height:1.7; }
.eb { color:#2e7d5b; font-weight:700; font-size: 11pt; letter-spacing: 1px; }
h2 { font-size: 22pt; margin: 1mm 0 2mm; }
.lead { font-size: 11pt; color:#3d4f57; line-height: 1.65; margin: 0 0 3mm; }
.body { flex: 1; display: flex; gap: 8mm; min-height: 0; }
.fig { flex: 1; min-width: 0; min-height: 0; overflow: hidden; display:flex; align-items:center; justify-content:center; border: 1px solid #dde5e0; border-radius: 3mm; padding: 3mm; background: #fcfdfb; }
.fig img { width: 100%; height: 100%; object-fit: contain; }
.side { width: 92mm; flex: none; font-size: 10pt; line-height: 1.6; color:#2f434b; overflow: hidden; }
.side h3 { font-size: 11.5pt; margin: 0 0 1.5mm; color:#1e3540; border-left: 1.2mm solid #2e7d5b; padding-left: 2mm; }
.side .box { background:#f4f7f3; border:1px solid #dde5e0; border-radius: 2mm; padding: 2.5mm 3.5mm; margin-bottom: 3mm; }
.side ul { margin: 0; padding-left: 4.5mm; } .side li { margin-bottom: 1mm; }
code { font-family: "DejaVu Sans Mono", monospace; font-size: .86em; background:#e8efea; padding: 0 1mm; border-radius: 1mm; }
table.t { width:100%; border-collapse: collapse; font-size: 9.6pt; }
table.t th { background:#1e3540; color:#fff; text-align:left; padding: 1.6mm 2.4mm; font-weight:700; }
table.t td { border-bottom: 1px solid #dde5e0; padding: 1.4mm 2.4mm; vertical-align: top; line-height:1.5; }
table.t tr:nth-child(even) td { background:#f6f8f5; }
table.t td.c { text-align:center; font-weight:700; }
.lg { display:flex; gap: 6mm; font-size: 9.5pt; color:#5c6b70; margin-top: 2mm; flex-wrap: wrap; }
.lg span i { display:inline-block; width: 4mm; height: 3mm; margin-right: 1.5mm; vertical-align: -0.3mm; border-radius: .6mm; }
.pno { position:absolute; right: 16mm; bottom: 6mm; font-size: 9pt; color:#8a9a95; }
.ttl { position:absolute; left: 16mm; bottom: 6mm; font-size: 9pt; color:#8a9a95; }
.under { flex: none; display:grid; grid-template-columns: repeat(auto-fit, minmax(0, 1fr)); gap: 6mm; font-size: 10pt; line-height:1.6; color:#2f434b; }
.under .box { margin:0; background:#f4f7f3; border:1px solid #dde5e0; border-radius:2mm; padding:2.5mm 3.5mm; }
.under h3 { font-size: 11.5pt; margin: 0 0 1.5mm; border-left: 1.2mm solid #2e7d5b; padding-left: 2mm; }
.under ul { margin:0; padding-left: 4.5mm; }
.cols2 { display:grid; grid-template-columns: 1fr 1fr; gap: 8mm; flex:1; min-height:0; }
.tag { display:inline-block; font-size: 8.5pt; padding: 0 2mm; border-radius: 1mm; color:#fff; background:#2e7d5b; margin-left: 1mm; }
.tag.x { background:#8a9a95; }
'''
LEG = '''<div class="lg"><span><i style="background:#1e3540"></i>業務データ</span><span><i style="background:#6b5a1e"></i>マスタ</span><span><i style="background:#2e7d5b"></i>選択値マスタ</span><span><i style="background:#8a2f2f"></i>監査</span><span><i style="background:#4a6478"></i>外部・ビュー</span><span>🔑 主キー　🔗 外部キー　──┼ ○＜ 1 対 0..n　──┼ ＜ 1 対 1..n　- - → 論理参照（FK なし）</span></div>'''

pages = []
def P(eb, title, lead, body):
    pages.append(f'<div class="eb">{eb}</div><h2>{title}</h2>' + (f'<p class="lead">{lead}</p>' if lead else '') + body)
def fig(name, side=None, legend=False, below=False):
    if below:
        ext = 'png' if name.startswith('s') else 'svg'
        s = f'<div class="body" style="flex-direction:column;gap:4mm"><div class="fig"><img src="img/{name}.{ext}"></div>'
        if side: s += f'<div class="under">{side}</div>'
        return s + '</div>' + (LEG if legend else '')
    ext = 'png' if name.startswith('s') else 'svg'
    s = f'<div class="body"><div class="fig"><img src="img/{name}.{ext}"></div>'
    if side: s += f'<div class="side">{side}</div>'
    return s + '</div>' + (LEG if legend else '')
def box(h, items):
    li = ''.join(f'<li>{x}</li>' for x in items)
    return f'<div class="box"><h3>{h}</h3><ul>{li}</ul></div>'

TOC = [('1', 'データモデルの考え方'), ('2', '概念データモデル（ER）'), ('3', 'PostgreSQL の物理モデル'), ('4', 'MongoDB・Local Storage のモデル'),
       ('5', 'レポートの構造と値の参照'), ('6', '選択値マスタのデータ'), ('7', '監査のデータ'), ('8', 'データフロー：全体（コンテキスト・DFD）'),
       ('9', 'データフロー：レポートの保存'), ('10', 'データフロー：選択値マスタの変更と反映'), ('11', 'データフロー：ログインと監査の参照'), ('12', 'CRUD 表（処理 × データ）')]

# ---- 1 考え方
P('1　データモデルの考え方', '1 検査＝1 レポート。検索に使う値は列、画面の項目はまとめて持つ', '統合版（選択値マスタ＋監査機能）のデータは、業務データ・マスタ・選択値マスタ・監査の 4 つのまとまりに分かれます。React 版は MongoDB／PostgreSQL／Local Storage から保存先を選べ、Thymeleaf 版は PostgreSQL 16 を使います。',
  '''<div class="cols2"><div>
<table class="t"><tr><th style="width:20%">まとまり</th><th style="width:40%">データ</th><th>持ち方の要点</th></tr>
<tr><td><b>業務データ</b></td><td>患者・入院歴、レポート（画面ごとのデータ）、登録履歴、MACE、画像</td><td>患者 1 : レポート n。レポートは画面ごとのかたまり（cathRecord・cagLvg・pci …）を持つ。同時更新は <code>version</code></td></tr>
<tr><td><b>マスタ</b></td><td>術者・医師、紹介病院、デバイス</td><td>レポートには名称を値として保存（参照キーではない）</td></tr>
<tr><td><b>選択値マスタ</b></td><td>カテゴリ 40・選択値 243、変更履歴</td><td>レポートには<b>コード</b>を保存。表示名は変えられ、コードは不変。削除せず「使用停止」</td></tr>
<tr><td><b>監査</b></td><td>監査ログ、変更項目</td><td>追加のみ（更新・削除はトリガーで禁止）。変更項目は「パス・変更前・変更後」</td></tr>
<tr><td><b>利用者</b></td><td>利用者・役割・パスワードのハッシュ</td><td>DB ではなく定義ファイル（<code>AUTH_USERS_FILE</code>）。監査ログには username を記録</td></tr>
</table></div><div>
<table class="t"><tr><th style="width:24%">保存先</th><th>レポートの持ち方</th><th style="width:30%">対応範囲</th></tr>
<tr><td><b>PostgreSQL 16</b><br>Thymeleaf 版／React＋Spring-pg</td><td>検索・整合性に使う値（患者 ID・施行日・状態など）は<b>列と制約</b>、画面の約 1,000 項目は <b>JSONB</b>、画像本体は <b>bytea</b>。Flyway で版管理</td><td>Thymeleaf 版：V1〜V6（選択値あり）<br>Spring-pg（API）：V1〜V5（選択値なし）</td></tr>
<tr><td><b>MongoDB</b><br>React＋Node.js／Spring</td><td>1 検査を 1 ドキュメントに。画面のデータ・MACE・画像・登録履歴を埋め込み</td><td>Node.js：選択値あり<br>Spring（Mongo）：選択値なし</td></tr>
<tr><td><b>Local Storage</b><br>React（体験用）</td><td>配列のまま JSON で保存</td><td>選択値・監査（最新 2,000 件）あり。ブラウザ内だけ</td></tr>
</table>
<div class="side" style="width:auto;margin-top:5mm">''' + box('全構成で共通の約束', [
      '項目は <b>パス</b>で識別（例 <code>report.cathRecord.exam.contrast.volume</code>）。画面の欄・保存・監査・選択値をこのパスでつなぐ',
      '<b>version</b> による同時更新の検知（患者・レポート・選択値カテゴリ）。違えば 409',
      '<b>主画面</b>：同じデータは 1 つの画面だけで編集（例：既往歴はカテ記録、J-PCI タブは参照）',
      '<b>確定ロック</b>：確定したレポートは一部の項目を除き変更不可（サーバーでも検査）']) + '</div></div></div>')

# ---- 2 概念
P('2　概念データモデル（ER）', '概念データモデル：エンティティと関係', '保存先によらない論理的な関係です。選択値・マスタとレポートの間は外部キーではなく「値として保存」する論理参照のため、選択値の表示名を変えても過去のレポートは書き換わりません。',
  fig('01_conceptual', box('関係の読み方', [
      '<b>患者 1 : レポート 0..n</b>。患者を削除できるのはレポートが無い時だけ（PostgreSQL は RESTRICT）',
      '<b>レポート 1 : 登録履歴 1..n</b>。新規作成で 1 件目、以後は追加のみ',
      '<b>レポート 1 : MACE 0..5</b>、<b>画像 0..n</b>',
      '<b>選択値カテゴリ 1 : 選択値 1..n</b>。使用中の選択値が 1 つ以上必要',
      '<b>監査ログ 1 : 変更項目 0..1000</b>（1 回の保存で 1,000 項目まで）']) +
    box('論理参照（破線・点線）', [
      '<span style="color:#2e7d5b">緑の破線</span>：レポートの項目値＝選択値の<b>コード</b>。カテゴリと項目の対応はプログラムの定義（<code>constants/options.ts</code>・テンプレート）',
      '<span style="color:#8a2f2f">赤の点線</span>：監査ログの対象 ID＝<code>rp-…</code>（レポート）、<code>pt-…</code>（患者）、カテゴリコード（選択値）、<code>default</code>（マスタ）', '<span style="color:#6b5a1e">茶の破線</span>：マスタの名称を値として保存']), legend=True, below=True))

# ---- 3 PG
P('3　PostgreSQL の物理モデル', 'PostgreSQL（Thymeleaf 版）：13 テーブル＋集計ビュー 3', 'Flyway の版：V1 基本テーブル → V2 集計ビュー → V3 監査ログ → V4 既往歴の移行（データのみ） → V5 変更項目 → V6 選択値マスタ。React 版の backend-spring-pg は V1〜V5 です。',
  fig('02_pg_physical', box('制約とトリガー', [
      '<code>cath_reports.patient_ref</code> → patients：<b>ON DELETE RESTRICT</b>。子テーブルは CASCADE',
      '<code>audit_log</code>・<code>audit_change</code>：UPDATE・DELETE・TRUNCATE を<b>トリガーで禁止</b>',
      '<code>option_item</code>：削除・TRUNCATE・<b>code の変更を禁止</b>。AFTER INSERT/UPDATE で <code>option_item_history</code> に 1 行（変更者は <code>set_config(\'app.user\')</code>）',
      '<code>version</code>：patients・cath_reports（bigint）、option_category（int）']) +
    box('JSONB と列の分け方', [
      '列：検索・並べ替え・制約に使う値（施行日・状態・照合済・Cine No など）',
      'JSONB：画面ごとのかたまり。項目を足しても DDL は不要',
      'report_mace は集計用に有無の列（has_death など）と全項目の JSONB を両方持つ',
      '画像は情報（report_images）と本体（report_image_data・bytea）を分け、一覧で本体を読まない']), legend=True))

# ---- 4 Mongo
P('4　MongoDB・Local Storage のモデル', 'MongoDB（React＋Node.js）と Local Storage', 'MongoDB は 1 検査を 1 ドキュメントにまとめ、画面のデータ・MACE・画像・登録履歴を埋め込みます。選択値はカテゴリ 1 件に items を埋め込み、変更前の内容を別コレクションに残します。',
  fig('03_mongo', box('コレクションと索引', [
      '<code>patients</code>：patientId（一意・sparse）、kana',
      '<code>cath_reports</code>：patientRef、header.studyDate（降順）、header.cineNo、status＋verified',
      '<code>audit_log</code>：at、username＋at、targetType＋targetId＋at',
      '<code>option_categories</code>：_id＝カテゴリコード。初回起動で初期データを投入（<code>seedOptionMasters</code>）',
      '<code>option_category_history</code>：code＋at']) +
    box('同時更新と追加のみ', [
      '更新は <code>{_id, version}</code> を条件に置き換え（<code>replaceOne</code>／<code>updateOne</code>）。0 件なら 409',
      '監査ログ・選択値の履歴は <code>insertOne</code> のみ（アプリから更新・削除しない）',
      'Spring Boot＋MongoDB（API 版）は patients・cath_reports・masters・audit_log。選択値はプログラムの初期値で表示']), legend=True, below=True))

# ---- 5 レポート構造
P('5　レポートの構造と値の参照', 'レポートの構造：画面ごとのかたまりと、マスタ・選択値の参照', '画面は「患者＋レポート」を 1 つの編集単位（Draft）として扱います。各入力欄はパスでこの構造の 1 か所を指し、選択肢はマスタ・選択値マスタから表示します。',
  fig('04_report_structure', box('値の参照の仕方', [
      '<b>選択値</b>：レポートには <b>コード</b> を保存し、画面は表示名で表示。使用停止の値が入っていれば「（使用停止）」付きで残す',
      '<b>🔒 標準の分類</b>（TIMI・ACC/AHA Type・NYHA・J-PCI の診断など 14 種類）は、自動判定やレジストリでコードを使うため編集不可',
      '<b>マスタ</b>：名称をそのまま保存（術者・デバイス・紹介病院）',
      '<b>複写</b>：前回の検査値・前回 PCI 病変などはボタンで写す（元を直しても写した先は変わらない）']) +
    box('項目数', ['保存する項目のパス：<b>1,058</b>（病変×5・MACE×5 などを展開すると画面の欄は 3,000 超）', '全項目の一覧：<code>docs/fields.md</code>・<code>docs/field_list.xlsx</code>（自動生成）'])))

# ---- 6 選択値
g = collections.OrderedDict()
for c in OPT:
    g.setdefault(c['screen'], []).append(c)
rows = ''
for scr, cs in g.items():
    names = '、'.join(c['name'] + ('<span class="tag x">🔒</span>' if not c['editable'] else '') + f'<span style="color:#8a9a95">（{len(c["items"])}）</span>' for c in cs)
    rows += f'<tr><td><b>{scr}</b></td><td class="c">{len(cs)}</td><td class="c">{sum(len(c["items"]) for c in cs)}</td><td>{names}</td></tr>'
ncat, nitem, nfix = len(OPT), sum(len(c['items']) for c in OPT), sum(1 for c in OPT if not c['editable'])
P('6　選択値マスタのデータ', f'選択値マスタ：{ncat} カテゴリ・{nitem} 選択値（編集可 {ncat - nfix}・標準の分類 {nfix}）', '初期値は <code>constants/options.ts</code> の <code>cat(...)</code> に 1 か所で定義し、<code>tools/gen_option_masters.ts</code> で初期データ（sample-data/option-masters.json）と Flyway V6 の投入 SQL を作ります。（ ）内は選択値の数、🔒 は編集不可。',
  f'''<div class="body"><div style="flex:1;min-width:0"><table class="t"><tr><th style="width:15%">画面</th><th style="width:6%">種類</th><th style="width:6%">値</th><th>カテゴリ</th></tr>{rows}</table></div><div class="side">''' +
  box('1 件の選択値', ['<code>code</code>：レポートに保存される値。作成後は変えない', '<code>label</code>：表示名（変更可）', '<code>sortOrder</code>：並び順（10 刻み）', '<code>active</code>：false で使用停止（新しい入力の候補に出さない）']) +
  box('保存の規則（サーバーで検査）', ['管理者のみ。<code>editable=false</code> のカテゴリは拒否', '空欄・コードの重複・既存コードの変更や削除は拒否', '使用中の選択値が 1 つ以上', 'カテゴリの version を照合し +1']) +
  box('変更の記録', ['PostgreSQL：<code>option_item_history</code>（トリガーで選択値ごとに 1 行）', 'MongoDB：<code>option_category_history</code>（変更前の items を 1 件）', '監査ログ：<code>UPDATE_OPTIONS</code>・対象 <code>option</code>・カテゴリコード']) + '</div></div>')

# ---- 7 監査
P('7　監査のデータ', '監査：監査ログ 1 行と、変わった項目', '業務の保存が成功した後に、保存前後の JSON をパスに平らにして比べ（AuditDiff。全構成で同じ規則）、監査ログ 1 行と変更項目を記録します。記録に失敗しても業務の保存は止めません（サーバーのログに残します）。',
  '''<div class="cols2"><div>
<table class="t"><tr><th style="width:30%">操作（action）</th><th style="width:16%">対象</th><th>いつ・内容</th></tr>
<tr><td>LOGIN／LOGIN_FAILURE／LOGIN_LOCKED／LOGOUT</td><td>user</td><td>ログインの成否・5 回失敗でロック・ログアウト</td></tr>
<tr><td>VIEW_PATIENT／VIEW_REPORT</td><td>patient／report</td><td>1 件を開いた時（閲覧の記録）</td></tr>
<tr><td>CREATE_PATIENT／UPDATE_PATIENT</td><td>patient</td><td>患者の登録・更新。変更項目あり</td></tr>
<tr><td>CREATE_REPORT／UPDATE_REPORT</td><td>report</td><td>レポートの登録・更新（確定・照合・確定解除を含む。要約に記載）。変更項目あり</td></tr>
<tr><td>DELETE_PATIENT／DELETE_REPORT</td><td>patient／report</td><td>削除（患者は管理者のみ）</td></tr>
<tr><td>UPDATE_MASTERS</td><td>masters</td><td>術者・紹介病院・デバイスの保存</td></tr>
<tr><td><b>UPDATE_OPTIONS</b></td><td>option</td><td>選択値マスタの保存。要約（例：使用停止:IABP 追加:ECMO）と選択値ごとの変更項目</td></tr>
<tr><td>SEED</td><td>all</td><td>サンプルデータの投入（既定は無効）</td></tr>
</table>
<p class="lead" style="margin-top:3mm;font-size:9.5pt">React 版（Node.js）の名称。Thymeleaf 版も同じ分類で記録します。</p>
</div><div>
<table class="t"><tr><th style="width:42%">変更項目の例（path）</th><th style="width:20%">変更前</th><th>変更後</th></tr>
<tr><td><code>cathRecord.exam.contrast.volume</code></td><td>66</td><td>120</td></tr>
<tr><td><code>pci.lesions.0.summary.timiPost</code></td><td>2</td><td>3</td></tr>
<tr><td><code>status</code></td><td>確定</td><td>入力中（確定解除）</td></tr>
<tr><td><code>IABP.使用</code></td><td>使用</td><td>使用停止</td></tr>
<tr><td><code>ECMO.表示名</code></td><td>（空）</td><td>ECMO</td></tr>
<tr><td><code>Impella.並び順</code></td><td>30</td><td>20</td></tr>
</table>
<div class="side" style="width:auto;margin-top:4mm">''' +
  box('差分の規則（AuditDiff）', ['配列は要素番号付きのパスに展開（<code>lesions.0</code>）', '除外：version・更新日時・登録履歴・画像本体', '値は 200 文字まで、1 回の保存で 1,000 項目まで', '選択値のパスは「コード.表示名／使用／並び順」。コード内の「.」は「．」に置き換え']) +
  box('参照と保管', ['監査ログ：管理者のみ（期間・利用者・操作・対象で検索、CSV 出力）', '項目ごとの変更履歴：レポートの閲覧権限で表示（確定解除は赤、その後の変更は橙）', '保管期間・アーカイブは運用で決める（未実装）']) + '</div></div></div>')

# ---- 8 DFD
P('8　データフロー：全体', 'データフロー：利用者・処理・データストア', '上段はコンテキスト図（システムと外部のやり取り）、下段は処理（P1〜P7）とデータストア（D0〜D7）の流れです。すべての保存処理（P3・P4・P5）は P6 監査記録を通ります。',
  '''<div style="display:flex;flex-direction:column;gap:3mm;flex:1;min-height:0">
<div class="fig" style="flex:0 0 48mm"><img src="img/00_context.svg"></div>
<div class="body"><div class="fig"><img src="img/05_dfd.svg"></div><div class="side">''' +
  box('処理', ['<b>P1 認証</b>：D0 で照合、結果を監査へ', '<b>P2 画面入力</b>：D1・D2 を読み、D4・D5 から選択肢', '<b>P3 保存</b>：権限・業務ルール・version 照合 → D1〜D3', '<b>P4 選択値マスタ管理</b>：→ D5、変更前 → D6', '<b>P5 マスタ管理</b>：→ D4', '<b>P6 監査記録</b>：→ D7（追加のみ）', '<b>P7 参照・出力</b>：一覧・集計・報告書・監査・CSV']) +
  box('外部', ['医師・秘書：入力・保存（確定・照合は医師）', '管理者：マスタ・選択値・監査', '閲覧者：参照のみ', '利用者定義ファイル：運用担当が配置']) + '</div></div></div>')

# ---- 9-11 sequences
P('9　データフロー：レポートの保存', 'レポートの保存：画面とサーバーの二重チェックと監査', 'React 版はレポート全体、Thymeleaf 版は変わった項目だけ（path→値）を送ります。サーバーは認証・権限・業務ルール・version を検査し、保存できたら差分を監査に記録します。',
  fig('s1_save', box('画面側', ['表示時の値と比べて変更を検知（保存ボタンが赤）', '未保存で画面を移る時は確認。キャンセルすると変更項目が黄色', 'BSA・EF・D2B・J-CTO などはその場で計算']) +
      box('サーバー側の拒否', ['401：未ログイン・期限切れ', '403：役割で許されない操作', '400：確定ロック・主画面の規則・登録履歴の改変', '409：version の不一致（他の端末が先に保存）']) +
      box('Thymeleaf 版の保存', ['患者 → レポートを 1 トランザクションで更新', 'パスを列・JSONB の位置に振り分けて反映']), below=True))
P('10　データフロー：選択値マスタの変更と反映', '選択値マスタ：変更 → 記録 → 全画面に反映', '管理者がカテゴリ単位で保存すると、選択値の変更履歴と監査ログ（UPDATE_OPTIONS）が残り、次の表示からすべての入力画面の選択肢が変わります。',
  fig('s2_options', box('反映の仕組み', ['React：<code>OptionsProvider</code> が状態を持ち、<code>SelectF</code>・<code>RadioF</code>・<code>TextF</code> が自動で参照', 'Thymeleaf：<code>OptionMasterService</code> のキャッシュを、<code>OptionsAdvice</code> が全画面のモデル（opts・optCodes・optLists）に渡す', 'レビュー用 HTML・デモ HTML でも同じ動き']) +
      box('過去データへの影響', ['レポートの値（コード）は変わらない', '表示名を変えると過去のレポートも新しい表示名で表示', '使用停止の値は候補から消え、入っているレポートでは「（使用停止）」付き']), below=True))
P('11　データフロー：ログインと監査の参照', 'ログインと、監査ログ・変更履歴の参照', 'ログインの成否も監査ログに残ります。監査ログの検索は管理者のみ、レポートごとの変更履歴は閲覧権限があれば見られます。',
  fig('s3_login_audit', box('認証', ['パスワード：PBKDF2-SHA256（12 万回）', '5 回続けて失敗で 15 分ロック（429）', 'React：Bearer トークン（8 時間）／Thymeleaf：セッション（8 時間）＋CSRF']) +
      box('参照の API', ['<code>GET /api/audit</code>：from・to・username・action・targetType・targetId・withChanges', '<code>GET /api/reports/{id}/history</code>：変更項目を新しい順', 'Thymeleaf：<code>/audit</code>・<code>/reports/{id}/history</code>']), below=True))

# ---- 12 CRUD
st = ['D0 利用者定義', 'D1 患者', 'D2 レポート', 'D3 画像', 'D4 マスタ', 'D5 選択値マスタ', 'D6 選択値の変更履歴', 'D7 監査ログ']
M = [('P1 認証', ['R', '', '', '', '', '', '', 'C']),
     ('P2 画面入力', ['', 'R', 'R', 'R', 'R', 'R', '', '']),
     ('P3 保存（患者・レポート・画像）', ['', 'CUD', 'CUD', 'CUD', '', '', '', '']),
     ('P4 選択値マスタ管理', ['', '', '', '', '', 'CRU', 'C', '']),
     ('P5 マスタ管理', ['', '', '', '', 'RU', '', '', '']),
     ('P6 監査記録', ['', '', '', '', '', '', '', 'C']),
     ('P7 参照・出力', ['', 'R', 'R', 'R', '', 'R', '', 'R'])]
th = ''.join(f'<th style="text-align:center">{x}</th>' for x in st)
tr = ''.join(f'<tr><td><b>{p}</b></td>' + ''.join(f'<td class="c" style="color:{"#8a2f2f" if "D" in v else "#2e7d5b" if "C" in v or "U" in v else "#1e3540"}">{v}</td>' for v in vs) + '</tr>' for p, vs in M)
P('12　CRUD 表', 'CRUD 表：処理 × データストア', 'C＝作成、R＝読取、U＝更新、D＝削除。監査ログと選択値の変更履歴は作成と読取のみで、更新・削除はどの処理にもありません（PostgreSQL はトリガーでも禁止）。',
  f'<table class="t" style="font-size:13pt"><tr><th style="width:22%">処理</th>{th}</tr>{tr}</table>' +
  '<div class="body" style="margin-top:6mm"><div class="side" style="width:auto;flex:1">' +
  box('削除の扱い', ['患者の削除：管理者のみ、レポートが残っていれば不可', 'レポートの削除：医師・管理者。子（登録履歴・MACE・画像）も削除', '選択値：削除なし（使用停止）', '監査ログ・変更履歴：削除なし']) + '</div><div class="side" style="width:auto;flex:1">' +
  box('役割と処理', ['管理者：P1〜P7 すべて', '医師：P2・P3（確定・照合を含む）・P7（監査ログ以外）', '秘書：P2・P3（確定・照合・削除を除く）・P7（監査ログ以外）', '閲覧者：P7（参照のみ）']) + '</div><div class="side" style="width:auto;flex:1">' +
  box('作り直し', ['<code>python3 tools/docs/datamodel/build.py</code>（React 版。Graphviz・mermaid-cli・Chrome）', 'DB の版を足したら 3 ページを、API を足したら 9〜11 ページを見直す']) + '</div></div>')

TITLE = '心カテーテルレポートシステム データモデル・データフロー（統合版）'
cover = '''<div class="pg cover"><div class="bar"></div><div class="k">設計資料　｜　統合版（選択値マスタ＋監査機能）</div>
<h1>心カテーテルレポートシステム<br>データモデル・データフロー</h1><div class="sub">React 版・Thymeleaf 版　｜　PostgreSQL・MongoDB・Local Storage</div>
<div class="toc">''' + ''.join(f'<div><b>{n}</b>{t}</div>' for n, t in TOC) + '''</div>
<div class="foot">2026年11月25日<br>統合版ソース（cath-report_after-high9_audit_options／cath-report-thymeleaf_after-high9_audit_options）の Flyway・API・画面の実装にもとづく</div></div>'''
html = [f'<!DOCTYPE html><html lang="ja"><head><meta charset="utf-8"><title>{TITLE}</title><style>{CSS}</style></head><body>', cover]
for i, p in enumerate(pages, 2):
    html.append(f'<div class="pg">{p}<div class="ttl">{TITLE}</div><div class="pno">{i} / {len(pages) + 1}</div></div>')
html.append('</body></html>')
out = D / 'datamodel_dataflow.html'
out.write_text('\n'.join(html), encoding='utf-8')
chrome = os.environ.get('CHROME', '/usr/bin/google-chrome')
subprocess.run([chrome, '--headless', '--no-sandbox', '--disable-gpu', '--no-pdf-header-footer', '--virtual-time-budget=5000',
                f'--print-to-pdf={D / "datamodel_dataflow.pdf"}', out.as_uri()], check=True, capture_output=True)
print(len(pages) + 1, 'pages →', D / 'datamodel_dataflow.pdf')

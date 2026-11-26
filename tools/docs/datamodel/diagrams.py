#!/usr/bin/env python3
"""統合版のデータモデル・データフロー図を作る（Graphviz の dot → SVG、mermaid-cli の mmdc → PNG）。

出力：docs/datamodel/img/  usage: python3 tools/docs/datamodel/build.py（この中から呼ばれる）
環境変数 CHROME：mmdc が使う Chrome（既定 /usr/bin/google-chrome）
"""
import json, os, pathlib, subprocess, html, tempfile
TOOL = pathlib.Path(__file__).resolve().parent
ROOT = TOOL.parents[2]
O = ROOT / 'docs' / 'datamodel' / 'img'
O.mkdir(parents=True, exist_ok=True)
F = 'Noto Sans CJK JP'
HEAD = f'''graph [fontname="{F}", fontsize=13, bgcolor="transparent", pad=0.2, nodesep=0.35, ranksep=0.55];
node [fontname="{F}", fontsize=12, shape=plaintext];
edge [fontname="{F}", fontsize=11, color="#4a6478", fontcolor="#33515c", penwidth=1.4, arrowsize=0.8];
'''
C = {'biz': ('#1e3540', '#fbfcf9'), 'mst': ('#6b5a1e', '#fffaf0'), 'aud': ('#8a2f2f', '#fff6f5'), 'opt': ('#2e7d5b', '#f1f8f3'), 'ext': ('#4a6478', '#f4f6f8')}

def tbl(name, title, cols, kind='biz', note=None, w=None):
    hd, bg = C[kind]
    rows = ''
    for c in cols:
        if isinstance(c, str):
            c = (c, '', '')
        n, t, k = (list(c) + ['', ''])[:3]
        key = {'PK': '🔑', 'FK': '🔗', 'PF': '🔑🔗'}.get(k, '')
        nm = f'<B>{html.escape(n)}</B>' if k in ('PK', 'PF') else html.escape(n)
        rows += f'<TR><TD ALIGN="LEFT" BALIGN="LEFT">{key} {nm}</TD><TD ALIGN="LEFT">{('<FONT COLOR="#5c6b70" POINT-SIZE="10">' + html.escape(t) + '</FONT>') if t else ' '}</TD></TR>'
    nt = f'<TR><TD COLSPAN="2" ALIGN="LEFT" BGCOLOR="#f0f0ea"><FONT POINT-SIZE="10" COLOR="#5c4a00">{note}</FONT></TD></TR>' if note else ''
    return f'''{name} [label=<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="4" COLOR="{hd}" BGCOLOR="{bg}">
<TR><TD COLSPAN="2" BGCOLOR="{hd}"><FONT COLOR="white"><B>{title}</B></FONT></TD></TR>{rows}{nt}</TABLE>>];\n'''

def dot(name, src, engine='dot'):
    p = O / f'{name}.dot'; p.write_text(src, encoding='utf-8')
    subprocess.run([engine, '-Tsvg', str(p), '-o', str(O / f'{name}.svg')], check=True)

# ---------------------------------------------------------------- 1 概念データモデル
def ent(name, title, attrs, kind='biz'):
    return tbl(name, title, attrs, kind)
src = 'digraph G {\n' + HEAD + 'rankdir=TB; ranksep=0.8; nodesep=0.6;\n'
src += ent('user', '利用者（定義ファイル）', [('username', '', 'PK'), ('表示名', ''), ('役割', 'admin/doctor/secretary/viewer'), ('パスワード', 'PBKDF2')], 'ext')
src += ent('patient', '患者', [('内部 ID', 'pt-…', 'PK'), ('患者 ID（病院）', '一意'), ('氏名・カナ・性別・生年月日', ''), ('アレルギー・感染症・紹介元', ''), ('version', '同時更新')])
src += ent('adm', '入院歴', [('患者', '', 'PF'), ('連番', '', 'PK'), ('入院日・退院日・診断', '')])
src += ent('report', 'カテレポート（1 検査）', [('内部 ID', 'rp-…', 'PK'), ('患者', '', 'FK'), ('状態（入力中／確定）・照合済', ''), ('施行日・Cine No・PCI No', ''), ('画面ごとのデータ', 'カテ記録・CAG/LVG・PCI …'), ('version', '同時更新')])
src += ent('hist', '登録履歴', [('レポート', '', 'PF'), ('連番', '', 'PK'), ('日時・実施者・操作', '追加のみ')])
src += ent('mace', 'MACE', [('レポート', '', 'PF'), ('連番（1〜5）', '', 'PK'), ('イベント有無・日付', '')])
src += ent('img', '画像', [('レポート', '', 'PF'), ('画像 ID', '', 'PK'), ('種別・撮影方向・病変', ''), ('キー画像・本体', '')])
src += ent('mst', 'マスタ', [('種類', '術者/紹介病院/デバイス', 'PK'), ('名称・カテゴリ・並び順', '')], 'mst')
src += ent('ocat', '選択値カテゴリ', [('コード', 'EXAM_ITEM …', 'PK'), ('名称・画面', ''), ('編集可否', '標準の分類は不可'), ('version', '同時更新')], 'opt')
src += ent('oitem', '選択値', [('カテゴリ', '', 'PF'), ('コード', '保存される値・不変', 'PK'), ('表示名・並び順', ''), ('使用／使用停止', '削除しない')], 'opt')
src += ent('ohist', '選択値の変更履歴', [('日時・変更者', ''), ('変更前・変更後', '表示名・使用・並び順')], 'opt')
src += ent('alog', '監査ログ', [('ID', '', 'PK'), ('日時・利用者・IP', ''), ('操作', 'LOGIN/UPDATE/UPDATE_OPTIONS…'), ('対象の種類・対象 ID', ''), ('要約', '')], 'aud')
src += ent('achg', '変更項目', [('監査ログ', '', 'PF'), ('連番', '', 'PK'), ('項目のパス', ''), ('変更前・変更後', '')], 'aud')
src += '''
patient -> adm [arrowhead=crowodot, arrowtail=teetee, dir=both, label="1 : 0..n"];
patient -> report [arrowhead=crowodot, arrowtail=teetee, dir=both, label="1 : 0..n"];
report -> hist [arrowhead=crow, arrowtail=teetee, dir=both, label="1 : 1..n"];
report -> mace [arrowhead=crowodot, arrowtail=teetee, dir=both, label="1 : 0..5"];
report -> img [arrowhead=crowodot, arrowtail=teetee, dir=both, label="1 : 0..n"];
ocat -> oitem [arrowhead=crow, arrowtail=teetee, dir=both, label="1 : 1..n"];
oitem -> ohist [arrowhead=crowodot, arrowtail=teetee, dir=both, label="1 : 0..n"];
alog -> achg [arrowhead=crowodot, arrowtail=teetee, dir=both, label="1 : 0..1000"];
oitem -> report [style=dashed, color="#2e7d5b", fontcolor="#2e7d5b", dir=forward, arrowhead=open];
mst -> report [style=dashed, color="#6b5a1e", fontcolor="#6b5a1e", label="名称を値として保存", arrowhead=open];
user -> alog [style=dashed, color="#8a2f2f", fontcolor="#8a2f2f", label="username を記録", arrowhead=open];
alog -> report [style=dotted, color="#8a2f2f", fontcolor="#8a2f2f", arrowhead=open, constraint=false];
{rank=same; user; patient; ocat}
{rank=same; alog; adm; report; oitem; mst}
{rank=same; achg; hist; mace; img; ohist}
}'''
dot('01_conceptual', src)

# ---------------------------------------------------------------- 2 PostgreSQL 物理
src = 'digraph G {\n' + HEAD + 'rankdir=LR; ranksep=0.7; nodesep=0.3;\n'
def cl(name, label, color, body):
    return f'subgraph cluster_{name} {{ label=<<B>{label}</B>>; fontsize=15; style="rounded,dashed"; color="{color}"; fontcolor="{color}";\n{body}}}\n'
b = tbl('patients', 'patients（患者）', [('id', 'varchar(64)', 'PK'), ('patient_id', 'varchar(32) 一意'), ('name / kana / sex / birth_date', ''), ('blood_type / rh / zip / address / phone', ''), ('emergency / insurance', 'JSONB'), ('allergy / infection / referral', 'JSONB'), ('primary_doctor / ward / dnar', ''), ('past_history … notes', 'text'), ('created_at / updated_at', ''), ('version', 'bigint 楽観ロック')])
b += tbl('patient_admissions', 'patient_admissions（入院歴）', [('patient_id', '→ patients', 'PF'), ('seq', 'int', 'PK'), ('admit_date / discharge_date', ''), ('doctor / diagnosis / summary', '')])
b += tbl('cath_reports', 'cath_reports（レポート）', [('id', 'varchar(64)', 'PK'), ('patient_ref', '→ patients（RESTRICT）', 'FK'), ('status', '入力中／確定'), ('verified', '照合済'), ('study_date', '施行日 NOT NULL'), ('cine_no / pci_no / accession_no', ''), ('secretary_checked / summary / submitted / qca', 'bool'), ('registrant', ''), ('cath_record / cag_lvg / pci', 'JSONB'), ('pressure_ivus / pcps', 'JSONB'), ('conference / restudy', 'JSONB'), ('created_at / updated_at', ''), ('version', 'bigint 楽観ロック')])
b += tbl('report_history', 'report_history（登録履歴）', [('report_id', '→ cath_reports', 'PF'), ('seq', 'int', 'PK'), ('at / by_name / action', '追加のみ')])
b += tbl('report_mace', 'report_mace（MACE）', [('report_id', '→ cath_reports', 'PF'), ('seq', '1〜5', 'PK'), ('mace / pci_date / last_visit', ''), ('has_death … has_other', 'bool（集計用）'), ('first_event_date', ''), ('data', 'JSONB 画面の全項目')])
b += tbl('report_images', 'report_images（画像の情報）', [('report_id', '→ cath_reports', 'PF'), ('seq', 'int', 'PK'), ('image_id', '一意（レポート内）'), ('category / taken_at / view_name / lesion', ''), ('title / description / file_name', ''), ('mime_type / key_image', '')])
b += tbl('report_image_data', 'report_image_data（画像本体）', [('report_id', '→ cath_reports', 'PF'), ('image_id', '', 'PK'), ('mime_type', ''), ('data', 'bytea'), ('size_bytes', '生成列'), ('updated_at', '')])
src += cl('biz', '業務データ（V1）', '#1e3540', b)
src += cl('mst', 'マスタ（V1）', '#6b5a1e', tbl('master_items', 'master_items', [('id', 'bigserial', 'PK'), ('kind', 'doctor / hospital / device'), ('category', 'デバイスの区分'), ('name', ''), ('sort_order', '')], 'mst'))
src += cl('opt', '選択値マスタ（V6）', '#2e7d5b',
          tbl('option_category', 'option_category', [('code', 'varchar(50)', 'PK'), ('name / screen', ''), ('editable', 'false＝標準の分類'), ('sort_order', ''), ('version', 'int 楽観ロック'), ('updated_at / updated_by', '')], 'opt') +
          tbl('option_item', 'option_item', [('category_code', '→ option_category', 'PF'), ('code', '保存される値', 'PK'), ('label', '表示名'), ('sort_order', ''), ('active', 'false＝使用停止')], 'opt',
              note='トリガー：削除・TRUNCATE・code の変更を禁止<BR ALIGN="LEFT"/>AFTER INSERT/UPDATE で履歴を 1 行追加<BR ALIGN="LEFT"/>') +
          tbl('option_item_history', 'option_item_history', [('id', 'bigserial', 'PK'), ('at / changed_by', 'app.user から'), ('operation', 'INSERT / UPDATE'), ('category_code / code', ''), ('old_label / new_label', ''), ('old_active / new_active', ''), ('old_sort / new_sort', '')], 'opt'))
src += cl('aud', '監査（V3・V5）', '#8a2f2f',
          tbl('audit_log', 'audit_log', [('id', 'bigserial', 'PK'), ('at', 'timestamptz'), ('username / display_name', ''), ('action', 'varchar(32)'), ('target_type / target_id', ''), ('detail', '要約'), ('ip', '')], 'aud', note='トリガー：UPDATE・DELETE・TRUNCATE を禁止<BR ALIGN="LEFT"/>') +
          tbl('audit_change', 'audit_change', [('audit_id', '→ audit_log', 'PF'), ('seq', 'int', 'PK'), ('path', 'varchar(300)'), ('before_value / after_value', 'text（200 文字まで）')], 'aud', note='トリガー：UPDATE・DELETE・TRUNCATE を禁止<BR ALIGN="LEFT"/>'))
src += cl('view', '集計ビュー（V2）', '#4a6478', '''views [label=<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="5" COLOR="#4a6478" BGCOLOR="#f4f6f8">
<TR><TD BGCOLOR="#4a6478"><FONT COLOR="white"><B>ビュー</B></FONT></TD></TR>
<TR><TD ALIGN="LEFT">v_report_summary（一覧・集計用の 1 行要約）</TD></TR>
<TR><TD ALIGN="LEFT">v_mace_events（MACE イベント）</TD></TR>
<TR><TD ALIGN="LEFT">v_monthly_stats（月別件数・成功率・D2B）</TD></TR></TABLE>>];''')
E = 'arrowhead=crowodot, arrowtail=teetee, dir=both'
src += f'''
patients:e -> patient_admissions [{E}]; patients -> cath_reports [{E}];
cath_reports -> report_history [{E}]; cath_reports -> report_mace [{E}]; cath_reports -> report_images [{E}]; cath_reports -> report_image_data [{E}];
report_images -> report_image_data [style=dashed, arrowhead=none, label="image_id"];
option_category -> option_item [arrowhead=crow, arrowtail=teetee, dir=both];
option_item -> option_item_history [style=dashed, color="#2e7d5b", label="トリガー", arrowhead=open];
audit_log -> audit_change [{E}];
cath_reports -> views [style=dotted, arrowhead=open]; report_mace -> views [style=dotted, arrowhead=open];
}}'''
dot('02_pg_physical', src)

# ---------------------------------------------------------------- 3 MongoDB / Local Storage
def doc(name, title, lines, kind='biz'):
    hd, bg = C[kind]
    rows = ''.join(f'<TR><TD ALIGN="LEFT" BALIGN="LEFT"><FONT FACE="DejaVu Sans Mono" POINT-SIZE="11">{l}</FONT></TD></TR>' for l in lines)
    return f'{name} [label=<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="3" COLOR="{hd}" BGCOLOR="{bg}"><TR><TD BGCOLOR="{hd}"><FONT COLOR="white"><B>{title}</B></FONT></TD></TR>{rows}</TABLE>>];\n'
sp = '&#160;&#160;'
src = 'digraph G {\n' + HEAD + 'rankdir=TB; nodesep=0.5; ranksep=0.6;\n'
src += doc('m_pat', 'patients', ['_id: "pt-001"', 'patientId: "0001234567"  <FONT COLOR="#8a8a8a">（一意）</FONT>', 'name, kana, sex, birthDate …', 'allergy: {…}, infection: {…}', 'admissions: [ {…} ]', 'version: 3'])
src += doc('m_rep', 'cath_reports（1 検査 = 1 ドキュメント）', ['_id: "rp-001"', 'patientRef: "pt-001"', 'status: "入力中", verified: false', 'header: { studyDate, cineNo, pciNo, … }', 'cathRecord: { exam, body, hemo, labs, risk, … }', 'cagLvg: { segments, collaterals, grafts, lvg }', 'pci: { basic, lesions:[…×5], device, jpci, … }', 'pressureIvus, pcps, conference, restudy', 'mace: [ {…} ×5 ]', 'images: [ { id, category, view, dataUrl, … } ]', 'history: [ { at, by, action } ]', 'version: 7, createdAt, updatedAt'])
src += doc('m_mst', 'masters', ['_id: "default"', 'doctors: [ "…" ]', 'hospitals: [ "…" ]', 'devices: [ { category, name } ]'], 'mst')
src += doc('m_opt', 'option_categories', ['_id: "SUPPORT"  <FONT COLOR="#8a8a8a">（カテゴリコード）</FONT>', 'name: "補助循環・サポート"', 'screen: "CAG・PCI", editable: true', 'items: [', f'{sp}{{ code: "IABP", label: "IABP",', f'{sp}{sp}sortOrder: 10, active: false }}, … ]', 'version: 2, updatedAt, updatedBy'], 'opt')
src += doc('m_oh', 'option_category_history', ['code: "SUPPORT", at, by', 'version: 1  <FONT COLOR="#8a8a8a">（変更前の版）</FONT>', 'items: [ …変更前の内容… ]'], 'opt')
src += doc('m_aud', 'audit_log', ['at, username, displayName, ip', 'action: "UPDATE_OPTIONS"', 'targetType: "option", targetId: "SUPPORT"', 'detail: "使用停止:IABP 追加:ECMO"', 'changeCount: 3', 'changes: [ { path: "IABP.使用",', f'{sp}before: "使用", after: "使用停止" }}, … ]'], 'aud')
src += '''
subgraph cluster_ls { label=<<B>Local Storage（React 版の体験用・ブラウザ内）</B>>; style="rounded,dashed"; color="#4a6478"; fontcolor="#4a6478";
ls [label=<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4" COLOR="#c9d5cf" BGCOLOR="#fbfcf9">
<TR><TD BGCOLOR="#e8efea"><B>キー</B></TD><TD BGCOLOR="#e8efea"><B>内容</B></TD></TR>
<TR><TD ALIGN="LEFT">cath.patients</TD><TD ALIGN="LEFT">患者の配列</TD></TR>
<TR><TD ALIGN="LEFT">cath.reports</TD><TD ALIGN="LEFT">レポートの配列（画像は data URL）</TD></TR>
<TR><TD ALIGN="LEFT">cath.masters</TD><TD ALIGN="LEFT">術者・紹介病院・デバイス</TD></TR>
<TR><TD ALIGN="LEFT">cath.optionMasters</TD><TD ALIGN="LEFT">選択値マスタ（変更したカテゴリ）</TD></TR>
<TR><TD ALIGN="LEFT">cath.audit</TD><TD ALIGN="LEFT">監査ログ（最新 2,000 件）</TD></TR>
<TR><TD ALIGN="LEFT">cath.storageSettings / cath.seeded</TD><TD ALIGN="LEFT">保存先の設定・初期投入済みの印</TD></TR></TABLE>>];
}
m_pat -> m_rep [label="_id = patientRef", arrowhead=crowodot, arrowtail=teetee, dir=both];
m_opt -> m_oh [label="保存のたびに 1 件", arrowhead=open, style=dashed, color="#2e7d5b"];
m_opt -> m_rep [label="code を値として保存", style=dashed, color="#2e7d5b", arrowhead=open];
m_aud -> m_rep [label="targetId", style=dotted, color="#8a2f2f", arrowhead=open];
{rank=same; m_pat; m_opt; m_mst}
{rank=same; m_rep; m_oh; m_aud}
}'''
dot('03_mongo', src)

# ---------------------------------------------------------------- 4 レポートの構造
src = 'digraph G {\n' + HEAD + 'rankdir=LR; nodesep=0.12; ranksep=0.5; node [shape=box, style="rounded,filled", fillcolor="#fbfcf9", color="#9db5a8", fontsize=12, margin="0.12,0.05"];\n'
src += 'draft [label="編集の単位（Draft）\\npatient ＋ report", fillcolor="#1e3540", fontcolor="white", color="#1e3540"];\n'
src += 'patient [label="patient（患者情報入力）\\n基本情報・アレルギー・感染症・入院歴・病歴総括"]; report [label="report（1 検査）\\nid・patientRef・status・verified・version", fillcolor="#e6eee7"];\n'
secs = [
 ('header', 'header', '施行日・Cine No・PCI No・Accession No・登録者'),
 ('cathRecord', 'cathRecord（カテ記録）', 'exam 検査情報・術者・手技時間 ／ body 身長体重 ／ hemo 血行動態\\nlabs 検査値 ／ risk 危険因子・既往歴 ／ complication 合併症 ／ prognosis'),
 ('cagLvg', 'cagLvg（CAG/LVG）', 'catheters ／ segments（AHA 1〜15）狭窄度 ／ collaterals ／ grafts ／ lvg EF'),
 ('pci', 'pci（PCI）', 'basic ／ lesions[1..5] 形態・QCA・Device・結果 ／ bifCto ／ complication\\njpci 診断・症状・リスク ／ bleedingThrombusRisk ／ ami 時刻'),
 ('pressureIvus', 'pressureIvus', 'pressure[1..5] FFR・iFR ／ ivus Lesion タブ（派生値）'),
 ('pcps', 'pcps（PCPS）', '心停止 → PCPS 開始の時刻・時間差'),
 ('conference', 'conference（カンファレンス）', '経過・シンチ・CT・UCG・トレッドミル・処方'),
 ('restudy', 'restudy', '前回 PCI 病変の再狭窄評価'),
 ('mace', 'mace[1..5]', 'イベント有無・日付・経過日数'),
 ('images', 'images[]', '種別・撮影方向・病変・キー画像・本体'),
 ('history', 'history[]', '登録履歴（追加のみ）'),
]
for k, t, d in secs:
    src += f'{k} [label=<<B>{t}</B><BR/><FONT POINT-SIZE="10" COLOR="#3d4f57">{d.replace(chr(92)+"n", "<BR/>")}</FONT>>];\nreport -> {k};\n'
src += 'draft -> patient; draft -> report;\n'
src += '''opt [label=<<B>選択値マスタ（例）</B><BR/><FONT POINT-SIZE="10">EXAM_ITEM 検査項目 → cathRecord.exam<BR/>APPROACH・CONTRAST → cathRecord / cagLvg<BR/>SUPPORT 補助循環 → pci.basic.support<BR/>LESION_TYPE 🔒・TIMI 🔒 → pci.lesions[n]<BR/>IMAGE_CATEGORY・VIEW → images[]<BR/>NYHA 🔒・CCS 🔒・用法 → conference</FONT>>, fillcolor="#f1f8f3", color="#2e7d5b"];
mst [label=<<B>マスタ</B><BR/><FONT POINT-SIZE="10">術者・医師 → cathRecord.exam の術者<BR/>デバイス → pci.lesions[n].device<BR/>紹介病院 → patient.referral</FONT>>, fillcolor="#fffaf0", color="#6b5a1e"];
opt -> cathRecord [style=dashed, color="#2e7d5b", constraint=false]; opt -> pci [style=dashed, color="#2e7d5b", constraint=false]; opt -> conference [style=dashed, color="#2e7d5b", constraint=false];
mst -> pci [style=dashed, color="#6b5a1e", constraint=false];
{rank=same; patient; report}
}'''
dot('04_report_structure', src)

# ---------------------------------------------------------------- 5 DFD
src = 'digraph G {\n' + HEAD + '''rankdir=TB; nodesep=0.5; ranksep=0.65; splines=true;
node [fontsize=13];
'''
def ext(n, l): return f'{n} [shape=box, style="filled", fillcolor="#fff7d6", color="#c9a227", penwidth=1.6, label="{l}", margin="0.2,0.1"];\n'
def proc(n, no, l): return f'{n} [shape=box, style="rounded,filled", fillcolor="#e6eef7", color="#4a6fa5", penwidth=1.6, label=<<B>{no}</B><BR/>{l}>, margin="0.15,0.08"];\n'
def store(n, no, l, k='biz'):
    col = {'biz': '#1e3540', 'opt': '#2e7d5b', 'aud': '#8a2f2f', 'mst': '#6b5a1e', 'ext': '#4a6478'}[k]
    return f'{n} [shape=plaintext, label=<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="6" COLOR="{col}"><TR><TD BGCOLOR="{col}"><FONT COLOR="white"><B>{no}</B></FONT></TD><TD BGCOLOR="#fbfcf9"><FONT COLOR="{col}">{l}</FONT></TD></TR></TABLE>>];\n'
src += ext('u_doc', '医師・秘書') + ext('u_adm', '管理者') + ext('u_view', '閲覧者')
src += proc('p1', 'P1 認証', 'ログイン・セッション/トークン<BR/>失敗回数とロック') + proc('p2', 'P2 画面入力', '変更検知・自動計算<BR/>選択肢の表示（マスタ参照）')
src += proc('p3', 'P3 保存', '権限・業務ルール<BR/>確定ロック・version 照合') + proc('p4', 'P4 選択値マスタ管理', '入力チェック・version 照合<BR/>変更の要約と差分')
src += proc('p5', 'P5 マスタ管理', '術者・紹介病院・デバイス') + proc('p6', 'P6 監査記録', '差分（AuditDiff）<BR/>追加のみで記録') + proc('p7', 'P7 参照・出力', '一覧・集計・検査報告書<BR/>監査ログ・変更履歴・CSV')
src += store('d0', 'D0', '利用者定義（users.json）', 'ext') + store('d1', 'D1', '患者') + store('d2', 'D2', 'レポート（登録履歴・MACE）') + store('d3', 'D3', '画像')
src += store('d4', 'D4', 'マスタ', 'mst') + store('d5', 'D5', '選択値マスタ', 'opt') + store('d6', 'D6', '選択値の変更履歴', 'opt') + store('d7', 'D7', '監査ログ・変更項目', 'aud')
src += '''
u_doc -> p1 [label="ID・パスワード"]; u_adm -> p1; u_view -> p1;
d0 -> p1 [label="利用者・役割"];
p1 -> p6 [label="ログイン成功/失敗/ロック"];
p1 -> p2 [label="利用者・役割"];
u_doc -> p2 [label="入力値"];
d5 -> p2 [label="使用中の選択値"]; d4 -> p2 [label="候補"];
d1 -> p2 [label="患者"]; d2 -> p2 [label="レポート（version）"];
p2 -> p3 [label="React：全体＋version\\nThymeleaf：変更項目＋version"];
p3 -> d1 [label="患者"]; p3 -> d2 [label="レポート・履歴"]; p3 -> d3 [label="画像"];
p3 -> p6 [label="保存前後"];
p3 -> p2 [label="409 / 403 / 400", style=dashed];
u_adm -> p4 [label="表示名・並び順\\n追加・使用停止"];
p4 -> d5; p4 -> d6 [label="変更前"]; p4 -> p6 [label="要約・差分"];
u_adm -> p5 [label="マスタ"]; p5 -> d4; p5 -> p6;
p6 -> d7;
d7 -> p7; d2 -> p7; d1 -> p7;
p7 -> u_adm [label="監査ログ・CSV"]; p7 -> u_view [label="一覧・報告書・変更履歴"]; p7 -> u_doc;
{rank=same; u_doc; u_adm; u_view; d0}
{rank=same; p1; p4; p5}
{rank=same; d4; d5; d6}
{rank=same; d1; d2; d3; p6}
{rank=same; d7; p7}
}'''
dot('05_dfd', src)

# context diagram
src = 'digraph G {\n' + HEAD + 'rankdir=LR; nodesep=0.4; ranksep=1.0; node [fontsize=13];\n'
src += ext('a', '医師・秘書') + ext('b', '管理者') + ext('c', '閲覧者') + ext('f', '利用者定義ファイル\\n（運用担当が配置）')
src += 'sys [shape=circle, style="filled", fillcolor="#e6eef7", color="#4a6fa5", penwidth=2, label=<<B>心カテーテル<BR/>レポート<BR/>システム</B>>, width=2.2, fixedsize=true];\n'
src += '''a -> sys [label="検査の入力・保存・確定"]; sys -> a [label="入力画面・報告書・\\n確定前の確認"];
b -> sys [label="マスタ・選択値の変更\\n監査の検索"]; sys -> b [label="監査ログ・CSV・\\n変更履歴"];
c -> sys [label="検索"]; sys -> c [label="一覧・レポート（参照のみ）"];
f -> sys [label="利用者・役割・\\nパスワードのハッシュ"];
}'''
dot('00_context', src)

# ---------------------------------------------------------------- 6 シーケンス（mermaid → PNG、余白を切る）
def sequences():
    from PIL import Image, ImageChops
    with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False) as pp:
        json.dump({'executablePath': os.environ.get('CHROME', '/usr/bin/google-chrome'), 'args': ['--no-sandbox']}, pp)
    for m in sorted((TOOL / 'sequences').glob('*.mmd')):
        png = O / f'{m.stem}.png'
        subprocess.run(['mmdc', '-q', '-i', str(m), '-o', str(png), '-c', str(TOOL / 'sequences' / 'mm.json'), '-p', pp.name, '-b', 'white', '-w', '2400', '-s', '1.5'], check=True)
        im = Image.open(png).convert('RGB')
        # 下の黒い帯（描画域の外）を除き、白い余白を切る
        g = im.convert('L'); w, h = im.size
        cut = next((y for y in range(h) if sum(1 for x in range(0, w, 8) if g.getpixel((x, y)) < 40) > 0.9 * (w // 8 + 1)), h)
        im = im.crop((0, 0, w, cut))
        bb = ImageChops.difference(im, Image.new('RGB', im.size, 'white')).getbbox()
        im.crop((max(bb[0] - 20, 0), max(bb[1] - 20, 0), min(bb[2] + 20, im.width), min(bb[3] + 20, im.height))).save(png)
sequences()
print('diagrams ok')

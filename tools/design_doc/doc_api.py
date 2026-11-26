"""REST API 詳細仕様"""
import json
from extra_common import G, e, table, build_doc, RELATED

ROOT = G.ROOT
SAMPLE_P = json.load(open(ROOT / 'sample-data/patients.json', encoding='utf-8'))[0]
SAMPLE_R = json.load(open(ROOT / 'sample-data/reports.json', encoding='utf-8'))[0]
MASTERS = json.load(open(ROOT / 'sample-data/masters.json', encoding='utf-8'))
BK = ['Node.js', 'Spring（Mongo）', 'Spring（PostgreSQL）']


def js(o):
    return f'<pre class="json">{e(json.dumps(o, ensure_ascii=False, indent=2))}</pre>'


def txt(s):
    return f'<pre class="json">{e(s)}</pre>'


def ep(method, path, desc):
    return f'<div class="ep"><span class="m {method}">{method}</span><span class="p">{e(path)}</span><span class="d">{e(desc)}</span></div>'


def params(rows):
    return table(['名前', '場所', '型', '必須', '説明'], [((a, 'code'), b, (c, 'code'), (d, 'c'), f) for a, b, c, d, f in rows], widths=['26mm', '16mm', '18mm', '11mm', None])


def status(rows):
    return table(['コード', '条件', 'エラーの例（error）'], [((a, 'k'), b, (c, 'small')) for a, b, c in rows], widths=['16mm', None, '62mm'])


def trim_report():
    r = {k: SAMPLE_R[k] for k in ['id', 'patientRef', 'status', 'verified', 'header']}
    r['cathRecord'] = {'exam': {k: SAMPLE_R['cathRecord']['exam'][k] for k in list(SAMPLE_R['cathRecord']['exam'])[:4]}, '…': '（各セクションの項目）'}
    r['cagLvg'] = r['pci'] = r['pressureIvus'] = r['conference'] = '{ … }'
    r['mace'] = '[ … ]'
    im = dict(SAMPLE_R['images'][0])
    im['dataUrl'] = im['dataUrl'][:40] + '…'
    r['images'] = [im]
    r['history'] = SAMPLE_R['history'][:1]
    r['createdAt'], r['updatedAt'] = SAMPLE_R['createdAt'], SAMPLE_R['updatedAt']
    return r


def trim_patient():
    keys = ['id', 'patientId', 'name', 'kana', 'sex', 'birthDate', 'primaryDoctor', 'referral']
    p = {k: SAMPLE_P[k] for k in keys}
    p['…'] = '（住所・連絡先・保険・アレルギー・感染症・既往歴 など）'
    p['admissions'] = SAMPLE_P.get('admissions', [])[:1]
    p['createdAt'], p['updatedAt'] = SAMPLE_P['createdAt'], SAMPLE_P['updatedAt']
    return p


# ============================================================ 1. 共通事項
def p_common():
    return ('<h1>1. 共通事項</h1>'
            '<p class="lead">React 版の保存先（Remote DB）となる REST API の仕様です。Node.js＋MongoDB 版・Spring Boot＋MongoDB 版・Spring Boot＋PostgreSQL 版の3種は同じ API を提供します。'
            'Thymeleaf 版も同じ形式の API（/api/patients 等）を他システム連携用に持ちます（8章）。</p>' +
            table(['項目', '内容'], [
                ('ベース URL', 'http://{ホスト}:8080/api（ポートは環境変数 PORT）'),
                ('形式', 'JSON（Content-Type: application/json; charset=UTF-8）。日本語はそのまま（エスケープ不要）'),
                ('認証', 'GET /api/health・POST /api/auth/login 以外は必須。ヘッダー Authorization: Bearer <トークン>（2章）。未ログイン・期限切れは 401'),
                ('権限', '役割（admin・doctor・secretary・viewer）ごとに操作を制御。権限がなければ 403（2章）'),
                ('CORS', '許可するオリジンを環境変数 CORS_ORIGIN で指定（既定 http://localhost:5173）。メソッドは GET・POST・PUT・DELETE・OPTIONS'),
                ('ID', '患者・レポート・画像の id はクライアントが採番する文字列（例 pt-001、rp-001）。患者の病院 ID は patientId（id とは別）'),
                ('日付', '日付は YYYY-MM-DD、日時は ISO 8601（例 2026-11-02T10:00:00.000Z）。時刻欄は HH:MM'),
                ('値', '入力欄の値は原則として文字列（未入力は ""）。チェックボックスは true/false'),
                ('更新の方式', 'レポート単位・患者単位の全体置換（PUT）。部分更新（PATCH）はない'),
                ('null の扱い', 'Spring 版は null の項目を応答から省く（non_null）。未知の項目は無視'),
            ], widths=['26mm', None], cls='kv') +
            '<h2>1.1 エラー応答</h2><p>エラー時は全バックエンド共通で次の形式を返します。</p>' + js({'error': '患者ID 0001234567 は既に登録されています'}) +
            table(['コード', '意味', '主な発生条件'], [
                (('200', 'k'), '成功', '取得・登録・更新'),
                (('204', 'k'), '成功（本文なし）', '削除'),
                (('401', 'k'), 'ログインが必要', 'トークンなし・不正・期限切れ。ログインの失敗（ユーザー名またはパスワードが違う）'),
                (('403', 'k'), '権限がない', '役割に許可されていない操作。サンプル投入が無効（ALLOW_SEED_API=false）'),
                (('429', 'k'), 'ロック中', 'ログインに 5 回続けて失敗（15 分間）'),
                (('400', 'k'), '要求が不正', '必須項目なし、id なし、患者が存在しない、日付・status が不正（PostgreSQL）、JSON の形式が不正（PostgreSQL）'),
                (('404', 'k'), '見つからない', '指定した id の患者・レポートがない、マスタが未登録（MongoDB 版）'),
                (('409', 'k'), '競合', '患者 ID の重複、レポートがある患者の削除、version の不一致・未指定（更新時）、確定済みの内容変更・削除、登録履歴の変更、制約違反（PostgreSQL）'),
                (('500', 'k'), 'サーバーエラー', '想定外の例外（DB 停止など）。error は一般的なメッセージ（詳細はサーバーのログ）'),
            ], widths=['16mm', '30mm', None]) +
            '<div class="note">404 の error は Node.js 版が "not found"、Spring 版が "404 NOT_FOUND" です。React 版の画面は 404 を「データなし（null）」として扱います。</div>'
            '<h2>1.2 バックエンドによる違い</h2>' +
            table(['項目'] + BK, [
                ('health の backend', 'node', 'spring-boot', 'spring-boot-postgresql（db 版数も返す）'),
                ('必須の検査（患者）', 'patientId・name', 'patientId・name', 'patientId・name'),
                ('必須の検査（レポート）', 'patientRef・header', 'patientRef・header・header.studyDate', '同左＋ status の値・日付の形式'),
                ('同時更新の検知', 'version（更新時は必須）', 'version（更新時は必須）', 'version（更新時は必須）'),
                ('認証・権限・業務ルール・監査ログ', '共通', '共通', '共通（監査ログは改ざん防止のトリガー付き）'),
                ('一覧の件数', 'limit（既定 5,000）', 'limit（既定 5,000）', 'limit を 1〜5,000 に制限'),
                ('患者の検索', '正規表現（大小無視）', '部分一致（大小無視）', 'LIKE（大小無視）'),
                ('集計ビュー', 'なし', 'なし', '/stats/monthly・/stats/mace'),
                ('本文の上限', '20MB（BODY_LIMIT）', 'サーバー既定', 'サーバー既定'),
            ], widths=['36mm', None, None, None]))


def p_auth():
    roles = [('閲覧（GET）', '○', '○', '○', '○'), ('患者・レポートの登録・更新', '○', '○', '○', '－'), ('確定・確定解除（status の変更）', '○', '○', '－', '－'),
             ('照合（verified の変更）', '○', '○', '－', '－'), ('レポート削除', '○', '○', '－', '－'), ('患者削除・マスタ更新・監査ログ・サンプル投入', '○', '－', '－', '－')]
    return ('<h1>2. 認証・権限・業務ルール</h1>' +
            ep('POST', '/api/auth/login', 'ログイン。トークン（既定 8 時間有効）を返す') +
            js({'username': 'yamada', 'password': '••••••'}) +
            '<p><b>応答 200</b></p>' + js({'token': 'eyJzdWIiOiJ5YW1hZGEi…', 'expiresAt': '2026-11-20T09:00:00Z', 'user': {'username': 'yamada', 'displayName': '山田 太郎', 'roles': ['doctor']}}) +
            status([('401', 'ユーザー名またはパスワードが違う', 'ユーザー名またはパスワードが違います'), ('429', '5 回続けて失敗（15 分ロック）', 'ログインに続けて失敗したため、15:47 までログインできません')]) +
            ep('GET', '/api/auth/me', 'ログイン中の利用者（username・displayName・roles）') +
            ep('POST', '/api/auth/logout', 'ログアウト（監査ログに記録。トークンは期限まで有効なので、画面側で破棄する）') + '<p><b>応答 204</b></p>' +
            ep('GET', '/api/audit', '監査ログの検索（管理者のみ）。新しい順') +
            params([('from', 'query', 'YYYY-MM-DD', '', '開始日'), ('to', 'query', 'YYYY-MM-DD', '', '終了日'), ('username', 'query', 'string', '', '利用者'),
                    ('action', 'query', 'string', '', 'LOGIN・LOGIN_FAILURE・VIEW_REPORT・CREATE_REPORT・UPDATE_REPORT・DELETE_REPORT・UPDATE_MASTERS・SEED など'), ('limit', 'query', 'number', '', '最大件数（既定 500、上限 5,000）')]) +
            js([{'at': '2026-11-20T06:44:57.602Z', 'username': 'hisho', 'displayName': '秘書 花子', 'action': 'UPDATE_REPORT', 'targetType': 'report', 'targetId': 'rp-001', 'detail': '', 'ip': '10.0.0.21'}]) +
            '<h2>2.1 役割と権限</h2>' + table(['操作', 'admin', 'doctor', 'secretary', 'viewer'], [(a, (b, 'c'), (c, 'c'), (d, 'c'), (f, 'c')) for a, b, c, d, f in roles], widths=[None, '18mm', '18mm', '20mm', '18mm']) +
            '<h2>2.2 レポート保存時の検査（サーバー）</h2>' +
            table(['順', '検査', '違反時'], [('1', '編集の権限', '403'), ('2', 'version（更新時は必須。取得時の値と同じか）', '409 version が必要です／他の端末で更新されています'),
                                         ('3', 'status を変えるなら確定の権限、verified を変えるなら照合の権限', '403'),
                                         ('4', '確定ロック：確定済みのまま保存する場合、status・verified・header.registrant・history 以外は変更不可', '409 確定済みのため編集できません'),
                                         ('5', '登録履歴：既存の履歴は変更・削除不可（追加のみ）', '409 登録履歴は変更・削除できません')], widths=['10mm', None, '62mm']) +
            '<p class="small">保存に成功すると、今回追加された登録履歴の記録者（by）をサーバーがログイン中の利用者に置き換えます（追加がなければ1件追加）。version は +1 されて返ります。</p>'
            '<div class="note">開発用に AUTH_ENABLED=false で認証を無効にできます（全操作を管理者として扱う）。本番では使わないでください。</div>')


def p_list():
    rows = [
        ('GET', '/health', 'ヘルスチェック', '共通'), ('GET', '/patients', '患者の一覧・検索', '共通'), ('GET', '/patients/{id}', '患者の取得', '共通'),
        ('POST', '/patients', '患者の登録', '共通'), ('PUT', '/patients/{id}', '患者の登録・更新', '共通'), ('DELETE', '/patients/{id}', '患者の削除', '共通'),
        ('GET', '/reports', 'レポートの一覧（画像本体なし）', '共通'), ('GET', '/reports/{id}', 'レポートの取得（画像本体あり）', '共通'),
        ('POST', '/reports', 'レポートの登録', '共通'), ('PUT', '/reports/{id}', 'レポートの登録・更新', '共通'), ('DELETE', '/reports/{id}', 'レポートの削除', '共通'),
        ('GET', '/masters', 'マスタの取得', '共通'), ('PUT', '/masters', 'マスタの更新', '共通'), ('POST', '/admin/seed', 'サンプルデータの投入（全置換）', '共通'),
        ('GET', '/stats/monthly', '月別の件数・平均', 'PostgreSQL 版'), ('GET', '/stats/mace', 'MACE の追跡一覧', 'PostgreSQL 版'),
        ('POST', '/form/save', '画面の保存（変更項目のみ）', 'Thymeleaf 版'),
        ('POST', '/auth/login', 'ログイン（トークンを取得）', 'React 版の API'), ('GET', '/auth/me', 'ログイン中の利用者', 'React 版の API'),
        ('POST', '/auth/logout', 'ログアウト', 'React 版の API'), ('GET', '/audit', '監査ログの検索（管理者）', '共通'),
    ]
    use = {'/auth/login': 'POST', '/auth/me': 'GET', '/auth/logout': 'POST', '/patients': '-', '/patients/{id}': 'GET・PUT・DELETE', '/reports': 'GET', '/reports/{id}': 'GET・PUT・DELETE', '/masters': 'GET・PUT', '/admin/seed': 'POST', '/health': 'GET'}
    return ('<h1>3. エンドポイント一覧</h1>' +
            table(['メソッド', 'パス（/api 以下）', '内容', '提供', 'React 版の使用'],
                  [(f'<span class="m {m}" style="display:inline-block;color:#fff;border-radius:1mm;padding:0 1.5mm;font-weight:700">{m}</span>', (p, 'code'), d, b,
                    ('○' if (p in use and (m in use[p] or use[p] == m)) else '', 'c')) for m, p, d, b in rows],
                  widths=['18mm', '40mm', None, '26mm', '22mm'], raw=True) +
            '<p class="small">React 版の使用：画面（RemoteStorageAdapter）が呼び出すもの。POST /patients・/reports は他システム連携用（画面は PUT で登録・更新）。</p>'
            '<h2>3.1 React 版の画面と API の対応</h2>' +
            table(['画面の操作', '呼び出す API'], [
                ('ログイン（Remote DB 選択時）', 'POST /auth/login → GET /auth/me（タブを開き直したとき）'),
                ('起動・一覧の再読込', 'GET /patients、GET /reports、GET /masters'),
                ('レコードを開く', 'GET /reports/{id}（画像を含む全体）'),
                ('保存', 'PUT /patients/{id}（患者を変更したときのみ）→ PUT /reports/{id}'),
                ('レコードの削除', 'DELETE /reports/{id}'),
                ('マスタの保存', 'PUT /masters'),
                ('保存先設定：接続テスト', 'GET /health'),
                ('保存先設定：サンプルデータ投入', 'POST /admin/seed'),
            ], widths=['56mm', None]))


def p_patients():
    p = trim_patient()
    return ('<h1>4. 患者（patients）</h1>' +
            ep('GET', '/api/patients', '患者の一覧。q を指定すると患者 ID・氏名・フリガナの部分一致で絞り込み、フリガナ順で返す') +
            params([('q', 'query', 'string', '', '検索文字列（大文字・小文字を区別しない）')]) +
            '<p><b>応答 200</b>：患者の配列（Patient[]）。</p>' + txt('GET /api/patients?q=シンゾウ') +
            ep('GET', '/api/patients/{id}', '患者を1件取得') + params([('id', 'path', 'string', '○', '患者の id（例 pt-001）')]) +
            '<p><b>応答 200</b>：Patient</p>' + js(p) + status([('404', '患者がない', 'not found（Node.js）／404 NOT_FOUND（Spring）')]) +
            ep('PUT', '/api/patients/{id}', '患者の登録・更新（upsert）。本文は Patient 全体') +
            params([('id', 'path', 'string', '○', '患者の id。本文の id より優先'), ('本文', 'body', 'Patient', '○', 'patientId・name は必須。更新時は取得した version が必須')]) +
            '<p><b>権限</b>：admin・doctor・secretary</p>' +
            '<p><b>応答 200</b>：保存後の Patient（createdAt・updatedAt と新しい version）。</p>' +
            status([('403', '権限がない（viewer）', 'この操作の権限がありません（編集）'),
                    ('400', 'patientId・name がない', '必須項目がありません: patientId（Node.js）／入力エラー: name: …（Spring）'),
                    ('409', '別の患者が同じ patientId を使用', '患者ID 0001234567 は既に登録されています'),
                    ('409', '更新時に version がない', 'version が必要です（この患者を再読み込みしてから保存してください）'),
                    ('409', 'version の不一致', 'この患者は他の端末で更新されています。再読み込みしてください')]) +
            ep('POST', '/api/patients', '患者の登録。PUT と同じ処理で、id は本文から取る') +
            status([('400', '本文に id がない（全バックエンド）', 'id が必要です')]) +
            ep('DELETE', '/api/patients/{id}', '患者の削除（admin のみ）。レポートがある患者は削除できない') +
            '<p><b>応答 204</b>（本文なし）。存在しない id でも 204。</p>' +
            status([('409', 'その患者のレポートがある', 'この患者には 2 件のレポートがあるため削除できません')]))


def p_reports():
    r = trim_report()
    return ('<h1>5. レポート（reports）</h1>' +
            ep('GET', '/api/reports', 'レポートの一覧。施行日の新しい順。画像本体（images[].dataUrl）は含まない') +
            params([('from', 'query', 'YYYY-MM-DD', '', '施行日の開始（以上）'), ('to', 'query', 'YYYY-MM-DD', '', '施行日の終了（以下）'),
                    ('patientRef', 'query', 'string', '', '患者の id'), ('status', 'query', 'string', '', '入力中／確定'),
                    ('limit', 'query', 'number', '', '最大件数（既定 5,000。PostgreSQL 版は 1〜5,000 に制限）')]) +
            '<p><b>応答 200</b>：CathReport[]（images は画像の情報のみ）。PostgreSQL 版は日付が不正なら 400（例：from の日付形式が不正です: 2026-13-01）。</p>' +
            txt('GET /api/reports?from=2026-11-01&to=2026-11-30&status=入力中') +
            ep('GET', '/api/reports/{id}', 'レポートを1件取得（画像本体を含む）') +
            '<p><b>応答 200</b>：CathReport（下は一部を省略した例）</p>' + js(r) +
            status([('404', 'レポートがない', 'not found／404 NOT_FOUND')]) +
            ep('PUT', '/api/reports/{id}', 'レポートの登録・更新（upsert）。本文はレポート全体（全セクション・全画像）') +
            params([('id', 'path', 'string', '○', 'レポートの id'), ('本文', 'body', 'CathReport', '○', 'patientRef・header は必須。Spring は header.studyDate も必須。更新時は version が必須')]) +
            '<p><b>権限</b>：admin・doctor・secretary（status・verified の変更は admin・doctor）。検査の順序は 2.2 を参照。</p>'
            '<p><b>応答 200</b>：保存後の CathReport（createdAt・updatedAt・新しい version。追加した登録履歴の by はログイン中の利用者。Spring は status 未指定なら「入力中」、verified 未指定なら false）。</p>' +
            status([('403', '権限がない（編集・確定・照合）', 'この操作の権限がありません（確定・確定解除）'),
                    ('409', '確定済みの内容を変更', '確定済みのため編集できません（ステータスを「入力中」に戻してください）'),
                    ('409', '既存の登録履歴を変更・削除', '登録履歴は変更・削除できません（追加のみ）'),
                    ('409', '更新時に version がない', 'version が必要です（このレポートを再読み込みしてから保存してください）'),('400', 'patientRef・header（・studyDate）がない', '必須項目がありません: header／入力エラー: header.studyDate: …'),
                    ('400', 'patientRef の患者がない', '患者が存在しません（patientRef）'),
                    ('400', 'status が 入力中／確定 以外（PostgreSQL）', 'status は 入力中 / 確定 のいずれかです'),
                    ('400', '日付の形式が不正（PostgreSQL）', 'header.studyDate の日付形式が不正です: 2026/11/02'),
                    ('409', 'version の不一致', 'このレポートは他の端末で更新されています。再読み込みしてください'),
                    ('409', '制約違反（PostgreSQL）', 'データ整合性エラー: …')]) +
            ep('POST', '/api/reports', 'レポートの登録。PUT と同じ処理で、id は本文から取る') +
            status([('400', '本文に id がない（全バックエンド）', 'id が必要です')]) +
            ep('DELETE', '/api/reports/{id}', 'レポートの削除（admin・doctor。PostgreSQL 版は画像・履歴・MACE も削除）') +
            '<p><b>応答 204</b>（本文なし）。存在しない id でも 204。</p>' +
            status([('403', '権限がない', 'この操作の権限がありません（レポート削除）'), ('409', '確定済み', '確定済みのレポートは削除できません（ステータスを「入力中」に戻してください）')]))


def p_misc():
    m = {'doctors': MASTERS['doctors'][:3], 'hospitals': MASTERS['hospitals'][:2], 'devices': MASTERS['devices'][:2]}
    return ('<h1>6. マスタ・管理・集計</h1>' +
            ep('GET', '/api/masters', 'マスタ（術者・医師、紹介病院、デバイス）を取得') +
            '<p><b>応答 200</b>：Masters（例は一部）。MongoDB 版は未登録なら 404。PostgreSQL 版は未登録でも空の配列を返す。</p>' + js(m) +
            ep('PUT', '/api/masters', 'マスタを全体置換で更新（admin のみ）') +
            '<p><b>本文</b>：Masters（doctors・hospitals・devices。省略した配列は空として扱う）。<b>応答 200</b>：保存後の Masters。</p>' +
            ep('POST', '/api/admin/seed', 'サンプルデータの投入。全データを削除してサンプルに置き換える（admin のみ、かつサーバーの ALLOW_SEED_API=true のときだけ。既定は 403）') +
            '<p><b>応答 200</b>：投入件数。</p>' + js({'patients': 8, 'reports': 9, 'images': 38}) +
            '<p class="small">images は PostgreSQL 版のみ。監査ログは削除しません。</p>' +
            ep('GET', '/api/health', 'ヘルスチェック') + js({'status': 'ok', 'backend': 'spring-boot-postgresql', 'db': '16.4', 'time': '2026-11-20T05:00:00Z'}) +
            '<p class="small">db は PostgreSQL 版のみ。値は例。</p>' +
            ep('GET', '/api/stats/monthly', '月別の件数・平均（PostgreSQL 版のみ。ビュー v_monthly_stats）') +
            table(['項目', '内容'], [(('month', 'code'), '月（月初日）'), (('reports', 'code'), '件数'), (('pci', 'code'), 'PCI を目的に含む件数'),
                                   (('emergency', 'code'), '緊急の件数'), (('avg_contrast_ml', 'code'), '平均造影剤量（mL）'), (('avg_fluoro_min', 'code'), '平均透視時間（分）')], widths=['36mm', None]) +
            ep('GET', '/api/stats/mace', 'MACE の追跡一覧（PostgreSQL 版のみ。ビュー v_mace_events）') +
            '<p>report_id・mace_no・patient_id・patient_name・study_date・pci_date・last_visit・first_event_date・follow_up_days・has_death・has_acs・has_stroke・has_hf・has_bleeding・has_revasc・has_other・has_major_event</p>')


def p_types():
    m = G.parse_model()

    def tbl(name, only=None, note=''):
        rows = [((k, 'code'), (t, 'code small'), G.C.DESC.get(f'{name}.{k}', c)) for k, t, c in m[name] if not only or k in only]
        return f'<h2>{name}</h2>{note}' + table(['項目', '型', '説明'], rows, widths=['32mm', '78mm', None])
    return ('<h1>7. データ形式</h1><p class="lead">React 版の型定義（frontend/src/types/model.ts）と同じ形式です。入れ子のオブジェクトは { } 内に1階層目の項目を示します（全項目は field_list.xlsx）。'
            'API が付ける項目：createdAt・updatedAt・version（全バックエンド）。</p>' +
            tbl('Patient') + tbl('Admission') +
            tbl('CathReport', note='<p class="small">cathRecord 以降の各セクションの項目は設計資料 本文編「3.5 型定義」を参照。</p>') +
            tbl('ImageItem', note='<p class="small">dataUrl は data:{mimeType};base64,… 形式。一覧（GET /reports）では含まない。</p>') +
            tbl('ReportHistory') + tbl('Masters'))


def p_tl():
    req = {'reportId': 'rp-001', 'patientRef': 'pt-001', 'isNew': False, 'screen': 'cathRecord', 'version': 3,
           'changes': {'report.cathRecord.exam.diagnosis': 'AP（労作性）', 'report.cathRecord.exam.contrast.volume': '80'}}
    return ('<h1>8. Thymeleaf 版の画面保存 API</h1>'
            '<p class="lead">Thymeleaf 版は 1〜6章と同じ REST API に加え、画面の保存専用の API を持ちます。変更された項目だけを送り、サーバーで業務ルールを検査してから患者・レポートを1トランザクションで保存します。</p>'
            '<div class="note">Thymeleaf 版の認証はログイン画面（POST /login）とセッションです（トークンではありません）。GET 以外の要求には、画面の meta name="csrf" の値をヘッダー X-CSRF-Token（フォームは _csrf）で送ります。一致しなければ 403、未ログインは 401（画面は /login へ転送）。</div>' +
            ep('POST', '/api/form/save', '画面の保存（変更項目のみ）') +
            table(['項目', '型', '必須', '説明'], [
                (('reportId', 'code'), 'string', ('既存', 'c'), '保存するレポートの id'),
                (('patientRef', 'code'), 'string', ('新規', 'c'), '新規作成時の患者 id（新規患者なら空）'),
                (('isNew', 'code'), 'boolean', '', 'true で新規作成'),
                (('screen', 'code'), 'string', '○', '保存した画面（patient・cathRecord・cagLvg・restudy・pci・pressureIvus・images・pcps・conference・mace）'),
                (('version', 'code'), 'number', '', '表示時のレポートの version。DB と異なれば 409'),
                (('changes', 'code'), 'object', '○', '変更された項目（パス → 値）。パスは patient. または report. で始まる'),
                (('images', 'code'), 'array', '', '画像画面：画像の一覧（追加分のみ dataUrl を含む）'),
                (('admissions', 'code'), 'array', '', '患者情報入力：病歴総括の全行'),
            ], widths=['26mm', '18mm', '13mm', None]) +
            '<p><b>例</b></p>' + js(req) +
            '<p><b>応答 200</b>：保存後に表示する画面の URL。</p>' + js({'reportId': 'rp-001', 'patientRef': 'pt-001', 'url': '/reports/rp-001/cathRecord'}) +
            status([('403', '編集・確定・照合の権限がない／CSRF トークン不一致', 'この操作の権限がありません（照合）'),
                    ('400', '画面が不正', '画面が不正です: xxx'),
                    ('400', 'パスが patient.／report. 以外', '項目が不正です: xxx'),
                    ('400', 'id・patientRef・version を変更しようとした', '変更できない項目です: report.id'),
                    ('400', '主画面以外で共有項目を変更', '「report.cathRecord.risk.DM」は「カテ記録」画面で編集します'),
                    ('400', '必須項目が未入力', '必須項目が未入力です: 患者ID、施行日'),
                    ('404', 'レポートがない', 'レポートがありません'),
                    ('409', 'version の不一致', 'このレポートは他の端末で更新されています。再読み込みしてください'),
                    ('409', '確定済み（ステータスを入力中に戻す変更を含まない）', '確定済みのため編集できません（ステータスを「入力中」に戻してください）')]))


def p_flow():
    return ('<h1>9. 利用の流れ（例）</h1><h2>9.1 レポートの取得と保存（PostgreSQL 版・楽観ロック）</h2>' +
            txt('''0. POST /api/auth/login             → 200  { "token": "…" }   以後 Authorization: Bearer <token>
1. GET  /api/reports/rp-001          → 200  { …, "version": 3 }
2. （画面で編集）
3. PUT  /api/patients/pt-001        → 200  （患者を変更したときのみ。version を含めて送る）
4. PUT  /api/reports/rp-001         本文 { …, "version": 3 }
     → 200  { …, "version": 4 }      保存成功。以後は version 4 を使う
     → 409  {"error": "このレポートは他の端末で更新されています。再読み込みしてください"}
             他の端末が先に保存した。GET し直して入力をやり直す''') +
            '<h2>9.2 curl の例</h2>' +
            txt('''# ヘルスチェック（ログイン不要）
curl http://localhost:8080/api/health

# ログインしてトークンを変数に入れる
TOKEN=$(curl -s -X POST -H "Content-Type: application/json" -d '{"username":"yamada","password":"…"}' \\
  http://localhost:8080/api/auth/login | jq -r .token)
AUTH="Authorization: Bearer $TOKEN"

# 患者の検索
curl -H "$AUTH" "http://localhost:8080/api/patients?q=0001234567"

# 11月のレポート一覧（入力中のみ）
curl -H "$AUTH" "http://localhost:8080/api/reports?from=2026-11-01&to=2026-11-30&status=%E5%85%A5%E5%8A%9B%E4%B8%AD"

# レポートの保存（ファイルの JSON を送る）
curl -X PUT -H "$AUTH" -H "Content-Type: application/json" --data @rp-001.json http://localhost:8080/api/reports/rp-001

# レポートの削除
curl -X DELETE -H "$AUTH" http://localhost:8080/api/reports/rp-001''') +
            '<h2>9.3 連携時の注意</h2>' +
            table(['注意点', '内容'], [
                ('全体置換', 'PUT はレポート全体を置き換える。一部だけ送ると、送らなかったセクションは空になる。必ず GET した全体を変更して送る'),
                ('画像', 'GET /reports（一覧）の images には dataUrl がない。一覧の結果をそのまま PUT すると画像本体が失われるため、PUT の前に GET /reports/{id} で全体を取得する'),
                ('業務ルール', '確定ロック・権限・登録履歴はサーバーが検査する（2.2）。連携用の利用者には必要最小限の役割を与える'),
                ('id の採番', '新規作成時は重複しない id をクライアントが決める（例：接頭辞＋日時＋乱数）'),
                ('文字コード', 'UTF-8。クエリ文字列の日本語は URL エンコードする'),
            ], widths=['26mm', None]))


PARTS = [
    ('common', 1, '1. 共通事項（形式・エラー・バックエンドの違い）', p_common),
    ('auth', 1, '2. 認証・権限・業務ルール', p_auth),
    ('list', 1, '3. エンドポイント一覧', p_list),
    ('pat', 1, '4. 患者（patients）', p_patients),
    ('rep', 1, '5. レポート（reports）', p_reports),
    ('misc', 1, '6. マスタ・管理・集計', p_misc),
    ('types', 1, '7. データ形式', p_types),
    ('tl', 1, '8. Thymeleaf 版の画面保存 API', p_tl),
    ('flow', 1, '9. 利用の流れ（例）', p_flow),
]

if __name__ == '__main__':
    build_doc('REST API 詳細仕様', 'Node.js 版・Spring Boot（MongoDB）版・Spring Boot（PostgreSQL）版 共通／Thymeleaf 版の画面保存 API',
              'React 版の保存先となる REST API（3種のバックエンド）と、Thymeleaf 版の /api/form/save', RELATED, PARTS, G.ROOT / 'docs/design/rest_api_spec.pdf')

"""ログイン・利用者・権限の仕組みと実装詳細（React 版・Thymeleaf 版・各サーバー）
usage: python3 tools/design_doc/doc_auth.py
"""
import subprocess
from extra_common import G, e, table, build_doc, RELATED

IMG = G.ROOT / 'docs/design/img'
SHOT = G.ROOT / 'demo/screenshots'
FONT = 'Noto Sans CJK JP'


def dot(name, src):
    subprocess.run(['dot', '-Tsvg', '-o', str(IMG / f'{name}.svg')], input=src.encode('utf-8'), check=True)


def fig(name, cap, h='90mm'):
    return (f'<div class="fig"><img src="{(IMG / (name + ".svg")).as_uri()}" style="width:100%;max-height:{h};object-fit:contain"></div>'
            f'<p class="cap">{e(cap)}</p>')


def shot(fn, cap, w='70%'):
    return (f'<div class="fig"><img src="{(SHOT / fn).as_uri()}" style="width:{w};border:1px solid #c9d3d6"></div>'
            f'<p class="cap">{e(cap)}</p>')


def code(s):
    return f'<div class="tree">{e(s.strip(chr(10)))}</div>'


def make_figs():
    dot('auth_overview', f'''digraph G {{
  graph [rankdir=TB, fontname="{FONT}", nodesep=0.45, ranksep=0.5, bgcolor="transparent"];
  node [shape=box, style="rounded,filled", fontname="{FONT}", fontsize=14, fillcolor="#eef5f2", color="#5d8a7c", margin="0.16,0.08"];
  edge [fontname="{FONT}", fontsize=12, color="#5b6f75", fontcolor="#44585e"];
  users [label="利用者定義 users.json\\n（ユーザー名・表示名・役割・PBKDF2）\\nAUTH_USERS_FILE で差し替え", shape=note, fillcolor="#fdf6e3", color="#c9a54b"];
  subgraph cluster_r {{ label="React 版"; fontname="{FONT}"; fontsize=14; style="rounded"; color="#5b84b1";
    login [label="ログイン画面\\nLoginScreen", fillcolor="#e6f0fa", color="#5b84b1"];
    ctx [label="AppContext\\nuser・authRequired・can(p)", fillcolor="#e6f0fa", color="#5b84b1"];
    local [label="Local（デモ）\\nlocalAuth：ブラウザ内で照合", fillcolor="#f1f1f1", color="#999999"];
    api [label="REST API（Node.js / Spring）\\nログイン → トークン（8 時間）\\n毎回 Bearer で検査・権限 403", fillcolor="#e6f0fa", color="#5b84b1"];
    login -> ctx; ctx -> local [label="Local の時", style=dashed]; ctx -> api [label="Remote の時"]; }}
  subgraph cluster_t {{ label="Thymeleaf 版"; fontname="{FONT}"; fontsize=14; style="rounded"; color="#d8a25e";
    tlogin [label="ログイン画面 login.html\\nLoginController", fillcolor="#fdf1e2", color="#d8a25e"];
    sess [label="セッション（8 時間）＋ CSRF\\nSessionAuthInterceptor", fillcolor="#fdf1e2", color="#d8a25e"];
    view [label="ViewAdvice\\ncurrentUser・perm → 画面のボタン", fillcolor="#fdf1e2", color="#d8a25e"];
    tlogin -> sess -> view; }}
  rules [label="業務ルール ReportRules / rules.ts\\n権限 → version → 確定・照合 → 確定ロック → 登録履歴", fillcolor="#f3e8f7", color="#9b6bb3"];
  audit [label="監査ログ audit_log\\n（PostgreSQL はトリガーで改ざん防止）", shape=cylinder, fillcolor="#f3e8f7", color="#9b6bb3"];
  users -> local [style=dotted]; users -> api [style=dotted]; users -> tlogin [style=dotted];
  api -> rules; sess -> rules; rules -> audit; api -> audit [style=dashed, label="ログイン等"]; tlogin -> audit [style=dashed];
}}''')
    dot('auth_react_seq', f'''digraph G {{
  graph [rankdir=LR, fontname="{FONT}", nodesep=0.3, ranksep=0.35, bgcolor="transparent"];
  node [shape=box, style="rounded,filled", fontname="{FONT}", fontsize=15, fillcolor="#e6f0fa", color="#5b84b1", margin="0.12,0.1"];
  edge [fontname="{FONT}", fontsize=12, color="#5b6f75", fontcolor="#44585e"];
  a [label="① ログイン画面\\nユーザー名・パスワード"];
  b [label="② POST /api/auth/login\\n照合（PBKDF2）\\n失敗 5 回で 15 分ロック", fillcolor="#f3e8f7", color="#9b6bb3"];
  c [label="③ トークン＋利用者\\nsessionStorage に保存"];
  d [label="④ 各 API に\\nAuthorization: Bearer", fillcolor="#f3e8f7", color="#9b6bb3"];
  f [label="⑤ 401（期限切れ）\\n→ ログイン画面\\n入力中の内容は残す", fillcolor="#fff6d6", color="#c9a54b"];
  a -> b -> c -> d;
  d -> f [label="401"];
  f -> a [constraint=false, style=dashed, label="再ログイン"];
}}''')


def p_overview():
    rows = [
        ('React 版・Local（デモ）', 'ログイン画面 → ブラウザ内で照合（localAuth）', 'sessionStorage（cath.auth:local）', '画面のボタン・入力不可', '体験用。データを守る仕組みではない'),
        ('React 版・Remote', 'POST /api/auth/login → トークン（8 時間）', 'sessionStorage（cath.auth:{API URL}）', '画面 ＋ サーバー（401・403・409）', 'Node.js・Spring MongoDB・Spring PostgreSQL の 3 種で共通'),
        ('Thymeleaf 版', 'ログイン画面（POST /login）→ セッション', 'サーバーのセッション（8 時間）', '画面（th:disabled）＋ サーバー', 'GET 以外は CSRF トークンを検査'),
        ('レビュー用 HTML', 'ログイン画面 → ブラウザ内で照合（engine.js）', 'sessionStorage（cathreport-review:user）', '画面のボタン', 'サーバーの動きを模したもの'),
    ]
    return ('<h1>1. 概要</h1>'
            '<p class="lead">すべての版で、ログインしてから使います。利用者は 1 つの定義ファイル（users.json）にまとめ、役割（管理者・医師・秘書・閲覧）ごとに使える操作を決めています。'
            '画面は権限の無いボタンを押せなくするだけで、最終的な判断（拒否）はサーバーが行います。</p>' +
            fig('auth_overview', 'ログイン・利用者・権限の全体像', '120mm') +
            table(['版・保存先', 'ログイン', 'ログイン情報の保存', '権限の検査', '補足'], [((a, 'k'), b, (c, 'code small'), d, (f, 'small')) for a, b, c, d, f in rows],
                  widths=['30mm', '42mm', '34mm', '28mm', None]))


def p_users():
    perm = [
        ('read', '閲覧', '○', '○', '○', '○'),
        ('edit', '入力・保存（患者・レポート）', '○', '○', '○', '－'),
        ('confirm', '確定・確定解除', '○', '○', '－', '－'),
        ('verify', '照合', '○', '○', '－', '－'),
        ('deleteReport', 'レポート削除（入力中のみ）', '○', '○', '－', '－'),
        ('deletePatient', '患者削除', '○', '－', '－', '－'),
        ('masters', 'マスタ編集', '○', '－', '－', '－'),
        ('seed', 'サンプルデータ投入', '○', '－', '－', '－'),
        ('audit', '監査ログの閲覧', '○', '－', '－', '－'),
    ]
    return ('<h1>2. 利用者・役割・権限</h1>'
            '<h2>2.1 利用者の定義（users.json）</h2>' +
            code('''
[
  { "username": "yamada", "displayName": "山田 太郎", "roles": ["doctor"],
    "password": "pbkdf2_sha256$120000$<salt base64>$<hash base64>",
    "disabled": false }            // true にするとログインできない
]
// パスワードのハッシュの作成：node tools/auth/hash_password.mjs <パスワード>
''') +
            table(['項目', '内容'], [
                (('置き場所', 'k'), '既定はデモ用の sample-data/users.json（5 名、パスワードは demo-ユーザー名）。本番は AUTH_USERS_FILE で別のファイルを指定する'),
                (('読み込み', 'k'), 'サーバーの起動時に読む（変更したら再起動）。トークンの検査では、役割を定義ファイルの最新の値に置き換える（トークンの中の役割は使わない）'),
                (('React 版のデモ', 'k'), '同じファイルを frontend/src/data/users.json に複写して、Local（デモ）のログインに使う'),
            ], widths=['26mm', None]) +
            '<h2>2.2 権限の表（全版で同じ）</h2>'
            '<p>権限の表は TypeScript（auth/permissions.ts・backend-node/src/security.ts）と Java（Permission.java）、レビュー用の engine.js に同じ内容で持っています。</p>' +
            table(['権限', '操作', '管理者', '医師', '秘書', '閲覧'], [((a, 'code'), b, (c, 'c'), (d, 'c'), (f, 'c'), (g, 'c')) for a, b, c, d, f, g in perm],
                  widths=['28mm', None, '16mm', '16mm', '16mm', '16mm']))


def p_authn():
    return ('<h1>3. 認証の仕組み</h1>'
            '<h2>3.1 パスワード</h2>'
            '<p>PBKDF2-SHA256（12 万回・16 バイトの salt・32 バイト）。照合は一定時間の比較（Node.js は timingSafeEqual、Java は MessageDigest.isEqual）で行います。</p>' +
            code('''
pbkdf2_sha256 $ 120000 $ <salt：base64> $ <hash：base64>
''') +
            '<h2>3.2 トークン（React 版の API）</h2>'
            '<p>サーバーの鍵（AUTH_SECRET）で署名した、8 時間有効のトークンです。サーバーには保存しません（署名と期限だけで検査）。</p>' +
            code('''
token = base64url(JSON{ sub: ユーザー名, name: 表示名, roles, exp: 期限（秒） })
        + "." + base64url(HMAC-SHA256(鍵, 前半))
検査：形式 → 署名（一定時間の比較）→ 期限 → 利用者が定義ファイルに居るか
      → 役割は最新の定義で置き換え
''') +
            table(['項目', '内容'], [
                (('鍵', 'k'), 'AUTH_SECRET（32 文字以上の乱数）。未設定なら起動ごとに生成（再起動で全員ログアウト）'),
                (('有効期間', 'k'), 'AUTH_TOKEN_TTL_MIN（既定 480 分）'),
                (('送り方', 'k'), 'Authorization: Bearer <トークン>（RemoteStorageAdapter が付ける）'),
            ], widths=['26mm', None]) +
            '<h2>3.3 セッション＋CSRF（Thymeleaf 版）</h2>' +
            table(['項目', '内容'], [
                (('ログイン', 'k'), 'POST /login（LoginController）。成功するとセッション ID を作り直し（セッション固定攻撃の対策）、利用者をセッションに保存して元の画面へ'),
                (('未ログイン', 'k'), 'SessionAuthInterceptor：画面は /login?next=… へ転送、/api は 401'),
                (('CSRF', 'k'), 'GET 以外は、セッションの CSRF トークンと、ヘッダー X-CSRF-Token（app.js が付ける）またはフォームの _csrf が一致しなければ 403'),
                (('有効期間', 'k'), 'server.servlet.session.timeout: 8h。HTTPS では SESSION_COOKIE_SECURE=true'),
            ], widths=['26mm', None]) +
            '<h2>3.4 ログイン失敗の制限・開発用の設定</h2>' +
            table(['項目', '内容'], [
                (('失敗の制限', 'k'), 'LoginThrottle：同じユーザー名で 5 回続けて失敗すると 15 分ロック（React 版の API は 429、Thymeleaf 版は画面に解除時刻）。成功で回数を戻す'),
                (('開発用', 'k'), 'AUTH_ENABLED=false で認証なし（全操作を「開発ユーザー」＝管理者として扱う）。本番では使わない'),
            ], widths=['26mm', None]))


def p_react():
    return ('<h1>4. React 版の画面側</h1>' + fig('auth_react_seq', 'ログインから API 呼び出し・期限切れまで（Remote の時）', '45mm') +
            table(['部品', '役割'], [
                (('components/auth/LoginScreen.tsx', 'code'), '全画面のログイン画面。未ログイン・期限切れの時に App が通常の画面の代わりに表示。Local の時はデモ用の利用者の一覧（クリックで入力）、保存先設定へも移れる'),
                (('auth/localAuth.ts', 'code'), 'Local（デモ）用。data/users.json の PBKDF2 を Web Crypto（crypto.subtle）で照合'),
                (('auth/session.ts', 'code'), 'ログイン情報（トークン・期限・利用者）を sessionStorage に保存・読込・削除。キーは保存先ごと（cath.auth:{API URL}、Local は cath.auth:local）'),
                (('auth/permissions.ts', 'code'), '役割・権限の表と hasPermission(user, p)'),
                (('state/AppContext.tsx', 'code'), 'user・authRequired（＝確認済みで未ログイン）・can(p)・login・logout。保存先を切り替えると、その保存先のログイン情報を確かめ直す'),
                (('storage/RemoteStorageAdapter.ts', 'code'), 'トークンを Authorization ヘッダーで送る。401 を受けたら onUnauthorized でログイン情報を消す → ログイン画面（入力中の内容は残る）'),
            ], widths=['56mm', None]) +
            '<h2>4.1 画面での権限の使い方</h2>' +
            table(['権限', '画面での扱い'], [
                (('edit', 'code'), '無い時は全入力欄が入力不可（フォームの readOnly）、保存・新規作成ボタンが押せない、「閲覧のみの権限のため編集できません」と表示'),
                (('confirm / verify', 'code'), 'サイドメニューの「入力中/確定」「照合」のボタン'),
                (('deleteReport', 'code'), '一覧の ✖（削除）'),
                (('masters / seed', 'code'), 'マスタボタン、保存先設定の「サンプルデータを投入」'),
                (('（記録者）', 'k'), '保存時の登録履歴の記録者はログイン中の利用者（Remote はサーバーでも上書き）'),
            ], widths=['32mm', None]) +
            shot('00_login.png', 'ログイン画面（Local・デモ）', '48%'))


def p_server():
    return ('<h1>5. サーバー側（React 版の API）</h1>'
            '<p>Node.js 版（backend-node/src/security.ts・auth.ts・rules.ts）と Spring 版（security パッケージ：PasswordHasher・TokenService・ApiAuthInterceptor・AuthController・ReportRules・LoginThrottle・UserStore）は同じ仕様です。</p>' +
            table(['処理', '内容'], [
                (('認証（全 /api）', 'k'), 'authenticate（Spring は ApiAuthInterceptor）。公開は POST /api/auth/login と GET /api/health だけ。トークンが無い・正しくない・期限切れは 401'),
                (('権限', 'k'), "allow('edit') など（Spring は ReportRules.require）。権限が無ければ 403「この操作の権限がありません（○○）」"),
                (('保存時の検査', 'k'), '1. 編集権限 → 2. version（違えば 409「他の端末で更新されています」）→ 3. 確定・照合の権限 → 4. 確定ロック（確定済みは状態・照合・登録者・履歴以外の変更を 409）→ 5. 登録履歴（追加のみ。記録者はログイン中の利用者に置換）'),
                (('API', 'k'), 'POST /api/auth/login（トークン＋利用者）、GET /api/auth/me、POST /api/auth/logout（監査ログに記録）、GET /api/audit（管理者のみ）'),
            ], widths=['30mm', None]) +
            code('''
// backend-node/src/server.ts・routes/api.ts（抜粋）
app.use('/api', authenticate, authApi, api);              // 全 /api：未ログインは 401
api.put('/reports/:id', wrap(upsertReport));              // 保存：rules.ts で 編集権限 → version → … を検査（403・409）
api.delete('/reports/:id', allow('deleteReport'), …);     // 権限が無ければ 403
api.put('/masters', allow('masters'), …);
''') +
            '<h1 style="page-break-before:always">6. Thymeleaf 版</h1>' +
            table(['クラス・ファイル', '役割'], [
                (('SessionAuthInterceptor', 'code'), '未ログインは /login へ（/api は 401）。GET 以外の CSRF 検査。AUTH_ENABLED=false なら開発ユーザー'),
                (('LoginController', 'code'), 'GET /login（ログイン画面）、POST /login（照合・ロック・監査・セッション ID の作り直し）、POST /logout'),
                (('UserStore', 'code'), '利用者定義の読込と照合。demoUsers()：デモ用の定義を使っている時だけ、ログイン画面に出す利用者の一覧を返す（本番の定義では null）'),
                (('ViewAdvice', 'code'), '全画面のモデルに currentUser（右上の表示）・perm（権限ごとの true/false）・csrf を入れる'),
                (('templates', 'code'), "th:disabled=\"${perm != null and not perm['edit']}\" のように、権限の無いボタンを無効にする（保存・新規作成・マスタ・削除・確定・照合）"),
                (('ReportRules・FormService', 'code'), '保存（/api/form/save）で React 版の API と同じ順に検査'),
                (('tools/review/engine.js', 'code'), 'レビュー用 HTML の模擬：未ログインは login テンプレート、ログインは users.json の PBKDF2 をブラウザ内で照合、currentUser・perm を同じ表で作る'),
            ], widths=['44mm', None]) +
            '<h1>7. 監査ログ</h1>' +
            table(['項目', '内容'], [
                (('記録する操作', 'k'), 'LOGIN・LOGIN_FAILURE・LOGIN_LOCKED・LOGOUT、患者/レポートの閲覧・登録・更新（確定/照合の変更を含む）・削除、マスタ更新、サンプル投入'),
                (('記録する内容', 'k'), '日時・ユーザー名・表示名・操作・対象（種類・ID）・詳細・IP'),
                (('保存先', 'k'), 'PostgreSQL 版・Thymeleaf 版：テーブル audit_log（トリガーで更新・削除・TRUNCATE を禁止）。MongoDB 版：コレクション audit_log'),
                (('検索', 'k'), 'GET /api/audit?from=&to=&username=&action=&limit=（管理者のみ）'),
            ], widths=['26mm', None]))


def p_settings():
    envs = [
        ('AUTH_ENABLED', 'true', '全版', 'false で認証なし（開発専用）'),
        ('AUTH_USERS_FILE', '（デモの定義）', '全サーバー', '本番の利用者定義ファイル'),
        ('AUTH_SECRET', '（起動ごとに生成）', 'React 版の API', 'トークンの署名鍵（32 文字以上）'),
        ('AUTH_TOKEN_TTL_MIN', '480', 'React 版の API', 'トークンの有効期間（分）'),
        ('SESSION_COOKIE_SECURE', 'false', 'Thymeleaf 版', 'HTTPS で true'),
        ('ALLOW_SEED_API', 'false', '全サーバー', 'サンプル投入 API を有効にする（管理者のみ）'),
        ('storageLock（config.js）', '（なし）', 'React 版の画面', "'remote' で保存先を Remote DB に固定（Local のデモログインを使えなくする）"),
    ]
    tests = [
        ('frontend（node:test）', '権限表・主画面（ownership）など'),
        ('backend-node（node:test）', 'パスワード・トークン（改ざん・期限）・権限・ログイン制限・業務ルール・version'),
        ('Spring（SecurityRulesTest）', 'パスワード・トークン・権限・確定ロック・履歴・version'),
        ('ブラウザ操作（React）', 'ログイン画面・誤ったパスワード・デモ利用者の入力・閲覧者は入力不可・再読込で継続・ログアウト・医師は入力可（12 件）'),
        ('ブラウザ操作（Thymeleaf レビュー）', 'ログイン画面・エラー・閲覧者は保存/新規作成不可・開こうとした画面へ戻る・ログアウト・管理者はマスタ可（12 件）'),
    ]
    return ('<h1>8. 設定項目</h1>' +
            table(['設定', '既定', '対象', '内容'], [((a, 'code'), (b, 'small'), (c, 'small'), d) for a, b, c, d in envs], widths=['46mm', '28mm', '28mm', None]) +
            '<h1>9. テスト</h1>' +
            table(['テスト', '内容'], [((a, 'k'), b) for a, b in tests], widths=['50mm', None]) +
            '<h1>10. 注意点・制限</h1>' +
            table(['対象', '内容', '対応案'], [
                (('Local（デモ）のログイン', 'k'), '利用者定義（ハッシュ）を画面に同梱し、ブラウザ内で照合する。データの保護にはならない', '本番は storageLock: remote。デモ以外では使わない'),
                (('トークンの取り消し', 'k'), 'トークンはサーバーに保存しないため、ログアウトしても期限（8 時間）までは有効。利用者を定義ファイルから消すと次の API から 401', '短い有効期間＋更新、または取り消しリスト'),
                (('ログイン失敗の回数', 'k'), 'サーバーのメモリで数える（再起動で戻る。複数台構成では台ごと）', '共有ストア（DB・Redis）で数える'),
                (('利用者定義の変更', 'k'), '起動時に読み込むため、変更は再起動で反映', '定期的な再読込、院内 AD・SSO との連携'),
                (('Thymeleaf：閲覧者の入力欄', 'k'), '閲覧者でも入力欄は入力できる（保存ボタン・API で止まる）。React 版は入力欄も入力不可', 'perm.edit が無い時は画面を読み取り専用にする'),
                (('パスワードの変更', 'k'), '画面からは変更できない（定義ファイルを管理者が更新）', 'パスワード変更画面・有効期限'),
            ], widths=['36mm', None, '52mm']))


PARTS = [
    ('ov', 1, '1. 概要', p_overview),
    ('us', 1, '2. 利用者・役割・権限', p_users),
    ('an', 1, '3. 認証の仕組み', p_authn),
    ('re', 1, '4. React 版の画面側', p_react),
    ('sv', 1, '5. サーバー側（React 版の API）／6. Thymeleaf 版／7. 監査ログ', p_server),
    ('st', 1, '8. 設定項目／9. テスト／10. 注意点・制限', p_settings),
]

if __name__ == '__main__':
    make_figs()
    build_doc('ログイン・利用者・権限の仕組みと実装', '認証（パスワード・トークン・セッション）・役割と権限・画面とサーバーの検査・監査ログ',
              '心カテーテルレポート（React 版・Thymeleaf 版）', RELATED, PARTS, G.ROOT / 'docs/design/auth_permissions.pdf')

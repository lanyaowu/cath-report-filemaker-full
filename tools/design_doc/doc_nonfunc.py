"""非機能の設計（React 版を中心に、Thymeleaf 版との違いを併記）"""
from extra_common import G, e, table, build_doc, RELATED

ST = {'済': '<span class="good">実装済</span>', '一部': '<span style="color:#c08a2e;font-weight:700">一部</span>', '未': '<span class="bad">未実装</span>'}


def p_scope():
    return ('<h1>1. 前提と対象範囲</h1>'
            '<p class="lead">心カテーテルレポート（React 版）の非機能（性能・容量・可用性・セキュリティ・信頼性・運用・移植性・使いやすさ）について、'
            '現在の実装と、本番運用に向けた設計方針・目標値（案）をまとめます。Thymeleaf 版で扱いが異なる点は併記します。</p>'
            '<h2>想定する利用環境（前提・案）</h2>' +
            table(['項目', '前提'], [
                ('利用者', '循環器内科の医師・技師・医療秘書。同時利用は 10 名程度'),
                ('利用場所', '院内ネットワーク（カテ室・医局・病棟）。インターネットには公開しない'),
                ('端末', 'Windows PC＋ Chrome / Edge（最新版）。画面幅 1600px 以上'),
                ('件数', '年間 1,500 件のカテーテル検査（10年保存で 15,000 件）'),
                ('画像', '1件あたり 5 枚・1枚 300KB 程度（心電図・造影の静止画など）'),
                ('稼働時間', '平日日中が中心。夜間・休日の緊急カテでも利用'),
            ], widths=['30mm', None], cls='kv') +
            '<div class="note">件数・画像・同時利用数は設計のための仮定です。実際の値が分かり次第、5章・3章の見積りを見直してください。</div>'
            '<h2>構成ごとの位置付け</h2>' +
            table(['構成', '用途', '本資料での扱い'], [
                ('React＋ localStorage', 'デモ・試用・個人利用', '容量の制約と、個人情報が端末に残る点を記載'),
                ('React＋ Node.js／Spring Boot（MongoDB）', '開発・検証', '同時更新の検知がない点を記載'),
                ('React＋ Spring Boot＋ PostgreSQL', '本番候補', '主な設計対象'),
                ('Thymeleaf 版（Spring Boot＋ PostgreSQL）', '本番候補', '違いを併記'),
            ], widths=['62mm', '40mm', None]))


def p_perf():
    return ('<h1>2. 性能</h1><h2>2.1 目標値（案）</h2>' +
            table(['処理', '目標（95% の操作）', '現状の実装・根拠'], [
                ('一覧の表示（5,000件まで）', '2 秒以内', '画像本体を除いて取得。施行日の索引（PostgreSQL：ix_cath_reports_study_date）'),
                ('レコードを開く', '1 秒以内', '1件の GET（画像を含む）。画像が多い場合は画像の読込が支配的'),
                ('画面（タブ）の切替', '0.3 秒以内', 'React 版は通信なし。Thymeleaf 版は 1 往復'),
                ('保存', '2 秒以内', 'React 版はレポート全体を PUT。Thymeleaf 版は変更項目のみ'),
                ('入力1文字あたりの反映', '体感できる遅れがないこと', 'イミュータブル更新（setAt）＋変更判定（deepEqual）'),
                ('集計', '3 秒以内', '画面内で集計。PostgreSQL はビュー（v_monthly_stats 等）'),
            ], widths=['42mm', '30mm', None]) +
            '<h2>2.2 データ量（実測）</h2>' +
            table(['対象', '大きさ', '備考'], [
                ('レポート1件（画像なし・全項目を補完した形）', '約 33,000 文字', 'デモで保存したレポートの JSON。未入力の項目も既定値で持つため'),
                ('レポート1件（サンプルデータ、画像なし）', '約 1,800〜6,100 文字', '入力のある項目だけを持つ形'),
                ('画像（Base64）', '元のサイズの約 1.33 倍', 'JSON 内に dataUrl として保持（React 版）'),
                ('サンプル 9 件（画像 38 枚込み）', '約 216,000 文字', 'localStorage の cath.reports'),
            ], widths=['70mm', '36mm', None]) +
            '<h2>2.3 性能のための設計</h2>' +
            table(['対策', '内容', '状態'], [
                ('一覧では画像本体を返さない', 'MongoDB は images.dataUrl を除外、PostgreSQL は画像本体を別表（report_image_data）に分離', ST['済']),
                ('索引', '施行日・患者・状態・Cine No・PCI No、JSONB の GIN 索引（pci・cath_record）', ST['済']),
                ('一覧の件数上限', 'limit（既定 5,000）。PostgreSQL 版は 1〜5,000 に制限', ST['済']),
                ('N+1 の回避', 'Hibernate default_batch_fetch_size: 100', ST['済']),
                ('HTTP 圧縮', 'Thymeleaf 版は gzip 有効（server.compression）。React 用バックエンドは未設定', ST['一部']),
                ('差分保存', 'Thymeleaf 版は変更項目のみ送信。React 版はレポート全体＋全画像', ST['一部']),
                ('一覧のページング', 'サーバー側のページ分割はなし（全件を取得して画面で絞込）', ST['未']),
                ('画像の縮小・サムネイル', '登録時の縮小なし（1.5MB 上限のみ）', ST['未']),
            ], widths=['40mm', None, '18mm'], raw=True))


def p_capacity():
    return ('<h1>3. 容量</h1><h2>3.1 localStorage（React 版・Local 選択時）</h2>'
            '<p>ブラウザの保存上限はおよそ 5MB（約 500万文字）です。2.2 の実測から、目安は次のとおりです。</p>' +
            table(['条件', '保存できる件数の目安'], [
                ('画像なし（全項目を補完した形）', '約 140 件'),
                ('サンプル程度の画像あり（1件あたり約 55,000 文字）', '約 90 件'),
                ('1件に 300KB の画像 5 枚', '約 2〜3 件'),
            ], widths=['100mm', None]) +
            '<div class="note">上限を超えると保存に失敗します（現在は専用のメッセージなし）。Local は<b>デモ・試用専用</b>とし、本番は Remote DB を使う方針とします。</div>'
            '<h2>3.2 データベース（PostgreSQL・見積り）</h2>' +
            table(['対象', '1件あたり', '年間（1,500件）', '10年'], [
                ('レポート（JSONB・列）', '約 35KB', '約 50MB', '約 0.5GB'),
                ('画像（bytea）', '約 1.5MB（5枚）', '約 2.3GB', '約 23GB'),
                ('索引・その他', '-', '約 20MB', '約 0.2GB'),
                (('合計', 'k'), '', ('約 2.4GB', 'k'), ('約 24GB', 'k')),
            ], widths=['50mm', '34mm', '34mm', None]) +
            '<p class="small">JSONB は PostgreSQL が自動で圧縮（TOAST）するため、実際はこれより小さくなる見込みです。容量の大半は画像のため、将来は画像をファイルストレージ（または PACS）に置く案も検討します。</p>'
            '<h2>3.3 リクエストの大きさ</h2>' +
            table(['構成', '上限', '備考'], [
                ('Node.js 版', '20MB（BODY_LIMIT）', 'express.json の limit'),
                ('Spring Boot 版（2種）', '明示設定なし（アプリサーバーの既定）', 'multipart の 20MB 設定はあるが、JSON の本文には効かない'),
                ('画面（画像1枚）', '1.5MB', 'React 版・Thymeleaf 版とも、超えると登録しない'),
            ], widths=['42mm', '60mm', None]))


def p_avail():
    return ('<h1>4. 可用性・バックアップ</h1><h2>4.1 目標（案）</h2>' +
            table(['項目', '目標（案）', '現状'], [
                ('稼働率', '99%（計画停止を除く）', '単一サーバー構成。冗長化なし'),
                ('目標復旧時点（RPO）', '24 時間以内（日次バックアップ）', 'バックアップ・復元スクリプトあり（cron 登録は運用）'),
                ('目標復旧時間（RTO）', '4 時間以内', '復元スクリプト・手順（docs/security.md）'),
                ('障害時の業務継続', '紙の記録で継続し、復旧後に入力', '-'),
            ], widths=['42mm', '56mm', None]) +
            '<h2>4.2 バックアップ設計（案）</h2>' +
            table(['対象', '方法', '頻度・保存期間'], [
                ('PostgreSQL', 'tools/backup/pg_backup.sh（pg_dump・読込確認・SHA-256）。任意の時点に戻す場合は WAL アーカイブも', '日次・30世代、月次・12世代'),
                ('PostgreSQL の復元', 'tools/backup/pg_restore.sh（チェックサム確認・件数表示）。月1回、確認用 DB で復元を確かめる', '-'),
                ('MongoDB（開発用）', 'tools/backup/mongo_backup.sh（mongodump）', '必要時'),
                ('アプリ・設定', 'Docker イメージ・docker-compose.yml・環境変数をリポジトリで管理', '変更時'),
                ('localStorage', '対象外（デモ用。端末故障で失われる）', '-'),
            ], widths=['34mm', None, '44mm']) +
            '<h2>4.3 起動・停止・ヘルスチェック</h2>' +
            table(['項目', '内容'], [
                ('ヘルスチェック', 'GET /api/health（PostgreSQL 版は DB のバージョンも返す）。docker compose の DB は pg_isready で監視'),
                ('自動再起動', 'Thymeleaf 版の app は restart: unless-stopped'),
                ('起動時の処理', 'Flyway でスキーマを作成・更新。DB が空ならサンプルを投入（SEED_ON_STARTUP）'),
                ('停止', 'SIGTERM で接続を閉じて終了（Node.js 版）。Spring Boot は標準の終了処理'),
            ], widths=['34mm', None]) +
            '<div class="note"><b>注意：</b>本番では <code>SEED_ON_STARTUP=false</code> にします。<code>POST /api/admin/seed</code>（全データを削除してサンプルに置換）は既定で無効です（<code>ALLOW_SEED_API=true</code> かつ管理者のときだけ）。</div>')


def p_sec():
    return ('<h1>5. セキュリティ</h1>'
            '<p class="lead">患者の氏名・生年月日・病歴を扱うため、厚生労働省「医療情報システムの安全管理に関するガイドライン」に沿った対策が必要です。認証・権限・監査ログなどは実装済みです（設定と本番前のチェックリストは docs/security.md）。</p>' +
            table(['対策', '方針（案）', '現状'], [
                ('認証', 'ログイン必須（React 版：トークン 8 時間、Thymeleaf 版：セッション＋CSRF）。PBKDF2 のパスワード、5 回失敗で 15 分ロック。院内 AD／SSO 連携は今後', ST['済']),
                ('権限', '役割（admin・doctor・secretary・viewer）ごとに、編集・確定・照合・削除・マスタ編集・監査ログ・サンプル投入をサーバーで制御', ST['済']),
                ('通信の暗号化', 'HTTPS（院内 CA の証明書）。アプリ単体の HTTPS 設定あり（TLS_CERT_FILE・SSL_ENABLED）、リバースプロキシ推奨', ST['一部'] + '<br><span class="small">証明書の用意は運用</span>'),
                ('CORS', '許可するオリジンを環境変数で指定（既定 http://localhost:5173）', ST['済']),
                ('入力の無害化（XSS）', 'React・Thymeleaf とも出力時に自動でエスケープ。HTML を直接差し込む処理なし', ST['済']),
                ('SQL インジェクション', 'JPA・パラメータ付き SQL。LIKE 検索はワイルドカードをエスケープ', ST['済']),
                ('NoSQL インジェクション', 'Node.js 版の検索文字列は正規表現をエスケープ', ST['済']),
                ('監査ログ', 'ログイン・閲覧・登録・更新・削除・確定・照合を記録（audit_log。PostgreSQL はトリガーで更新・削除を禁止）。登録履歴の記録者はログイン利用者', ST['済']),
                ('エラー情報', '利用者には一般的なメッセージ、詳細はサーバーのログへ', ST['済']),
                ('端末内のデータ', 'Local Storage は本番で使わない（config.js の storageLock で固定）', ST['済']),
                ('危険な管理機能', '/api/admin/seed は既定で無効（ALLOW_SEED_API・管理者のみ）', ST['済']),
                ('DB の資格情報', '既定のパスワード（cathreport）を変更し、環境変数／シークレットで渡す', ST['一部']),
                ('依存ライブラリ', '定期的に脆弱性を確認（npm audit・OWASP Dependency-Check）', ST['未']),
            ], widths=['36mm', None, '22mm'], raw=True))


def p_rel():
    return ('<h1>6. 信頼性・データ整合性</h1>' +
            table(['仕組み', '内容', 'React 版', 'Thymeleaf 版'], [
                ('必須チェック', '患者ID・氏名・施行日', '画面＋ API（施行日は Spring のみ）', '画面＋サーバー'),
                ('主画面（共有項目）', '主画面以外での変更を禁止', '画面のみ（API は全体置換のため対象外）', '画面＋サーバー'),
                ('確定ロック', '確定済みは全項目ロック（ステータス・照合・登録者を除く）', '画面＋サーバー', '画面＋サーバー'),
                ('同時更新の検知', 'version（楽観ロック）が DB と異なれば 409。更新時は必須', 'あり（全バックエンド）', 'あり'),
                ('権限', '編集・確定・照合・削除', '画面＋サーバー', '画面＋サーバー'),
                ('参照整合性', 'レポートの患者が存在すること。レポートがある患者は削除不可', 'API で検査（PostgreSQL は外部キーも）', 'DB の外部キー'),
                ('値の制約', 'status は 入力中／確定、日付の形式', 'PostgreSQL 版のみ（CHECK 制約・変換時に検査）', 'あり'),
                ('トランザクション', '患者とレポートの保存', '別々の API 呼出し', '1トランザクション'),
                ('未保存の警告', '画面遷移時の確認・ブラウザを閉じる時の警告', 'あり', 'あり'),
                ('旧データの補完', '項目追加前のデータを読込時に既定値で補う', 'normalizeReport', 'テンプレートの既定値'),
                ('保存履歴', '保存ごとに日時・記録者（ログイン利用者）・画面を追加。既存の履歴は変更不可', 'あり', 'あり'),
            ], widths=['30mm', None, '34mm', '28mm']) +
            '<div class="note">確定ロック・権限・登録履歴・version は、React 版の3種のバックエンドと Thymeleaf 版で同じ規則をサーバーで検査します（docs/security.md）。</div>')


def p_ops():
    return ('<h1>7. 運用・保守</h1><h2>7.1 設定（環境変数）</h2>' +
            table(['変数', '既定値', '対象', '内容'], [
                (('PORT', 'code'), '8080', '全バックエンド', '待受ポート'),
                (('CORS_ORIGIN', 'code'), 'http://localhost:5173', 'React 用バックエンド', '許可するオリジン（カンマ区切り）'),
                (('SEED_ON_STARTUP', 'code'), 'true', '全バックエンド', 'DB が空ならサンプル投入'),
                (('MONGODB_URI・MONGODB_DB', 'code'), 'mongodb://localhost:27017・cathreport', 'Node.js 版', 'MongoDB の接続先（Spring 版は MONGODB_URI のみ）'),
                (('BODY_LIMIT', 'code'), '20mb', 'Node.js 版', 'JSON 本文の上限'),
                (('DB_URL・DB_USER・DB_PASSWORD', 'code'), 'localhost:5432／cathreport', 'PostgreSQL 版・Thymeleaf 版', 'PostgreSQL の接続先'),
                (('DB_POOL_SIZE', 'code'), '10', '同上', '接続プールの最大数'),
                (('THYMELEAF_CACHE', 'code'), 'true', 'Thymeleaf 版', 'false でテンプレートの変更を即時反映（開発用）'),
                (('AUTH_USERS_FILE', 'code'), 'デモ用の利用者', '全バックエンド', '利用者の定義（JSON）。本番では必ず指定'),
                (('AUTH_SECRET・AUTH_TOKEN_TTL_MIN', 'code'), '起動ごとに乱数・480', 'React 用バックエンド', 'トークンの鍵・有効時間（分）'),
                (('AUTH_ENABLED', 'code'), 'true', '全バックエンド', 'false で認証なし（開発専用）'),
                (('ALLOW_SEED_API', 'code'), 'false', '全バックエンド', 'POST /api/admin/seed を許可'),
                (('TLS_CERT_FILE・TLS_KEY_FILE', 'code'), '-', 'Node.js 版', 'HTTPS（PEM）'),
                (('SSL_ENABLED・SSL_KEY_STORE 他', 'code'), 'false', 'Spring 版・Thymeleaf 版', 'HTTPS（PKCS12）。Thymeleaf 版は SESSION_COOKIE_SECURE も'),
            ], widths=['46mm', '42mm', '34mm', None]) +
            '<h2>7.2 運用作業</h2>' +
            table(['作業', '方法', '状態'], [
                ('スキーマの変更', 'Flyway のマイグレーション（V3__…sql を追加）', ST['済']),
                ('マスタの更新', '画面（マスタ編集）または PUT /api/masters', ST['済']),
                ('ログ', '標準出力（Docker のログ）。Spring は SQL 表示用のプロファイル（sql）あり', ST['一部']),
                ('監視', 'ヘルスチェック URL を院内の監視ツールに登録', ST['未']),
                ('バックアップ', 'tools/backup のスクリプトを cron に登録。別媒体へ複製', ST['一部']),
                ('自動テスト', 'npm test（frontend・Node.js 版）、mvn test（Spring 版）', ST['済']),
                ('リリース', 'Docker イメージのタグで版を管理。DB は Flyway が自動で更新', ST['一部']),
                ('項目の追加', 'React 版：types → defaults → 画面 → ownership。Thymeleaf 版：テンプレート → Ownership', ST['済']),
            ], widths=['32mm', None, '18mm'], raw=True))


def p_port():
    return ('<h1>8. 移植性・使いやすさ</h1><h2>8.1 動作環境</h2>' +
            table(['項目', '内容'], [
                ('ブラウザ', 'Chrome・Edge の最新版（ES2020・CSS Grid を使用）。Safari・Firefox は未確認'),
                ('画面サイズ', '横 1600px 以上を想定。タブレット・スマートフォンは対象外'),
                ('サーバー', 'Java 17 以上（Spring Boot 3.3）／Node.js 18 以上を想定（Node.js 版）／PostgreSQL 16／MongoDB 7'),
                ('OS', 'Docker が動く環境（Linux 推奨）。Windows でも Docker Desktop で可'),
                ('日時', '日付は YYYY-MM-DD、日時は ISO 8601（UTC）で保存し、画面は日本時間で表示'),
                ('文字コード', 'UTF-8（API・DB・画面）'),
            ], widths=['26mm', None], cls='kv') +
            '<h2>8.2 使いやすさ</h2>' +
            table(['観点', '内容'], [
                ('紙の様式に近い配置', '既存の入力様式に合わせた項目配置。タイトルは右寄せ'),
                ('入力の負担軽減', 'マスタの候補・自動計算・前回値のコピー・条件付き入力'),
                ('誤りの防止', '基準値外のピンク表示・必須の未入力表示・変更項目の黄色表示・保存ボタンの赤表示'),
                ('キーボード', 'Ctrl+S で保存。Tab で項目移動'),
                ('アクセシビリティ', '色だけに頼る表示がある（黄色・ピンク）。読み上げ対応は未確認'),
            ], widths=['32mm', None]))


def p_summary():
    rows = [
        ('性能', '一覧 2 秒・保存 2 秒・画面切替 0.3 秒', '索引・画像の分離・一覧の上限', '一部', '一覧のページング、画像の縮小、差分保存（React 版）'),
        ('容量', '10 年で約 24GB', 'PostgreSQL（画像は bytea）', '済', '画像のファイルストレージ化を検討'),
        ('可用性', '稼働率 99%・RPO 24 時間・RTO 4 時間', 'ヘルスチェック・自動再起動・バックアップ／復元スクリプト', '一部', 'cron 登録・別媒体への複製・復元訓練'),
        ('セキュリティ', 'ガイドライン準拠（認証・権限・暗号化・監査）', '認証・権限・監査ログ・CSRF・seed 無効化・HTTPS 設定', '一部', '証明書の用意（HTTPS）、院内 AD／SSO 連携'),
        ('信頼性', '業務ルールをサーバーで強制・同時更新の検知', '全バックエンドで実装済', '済', '-'),
        ('運用・保守', '設定の外出し・スキーマ管理・監視', '環境変数・Flyway', '一部', '監視・ログの集約・CI'),
        ('移植性', 'Chrome/Edge・Docker', 'Docker 構成あり', '済', '他ブラウザの確認'),
        ('使いやすさ', '入力の負担軽減・誤りの防止', '自動計算・強調表示・コピー', '済', 'アクセシビリティの確認'),
    ]
    return ('<h1>9. 非機能要件の一覧（まとめ）</h1>' +
            table(['区分', '目標（案）', '現在の実装', '状態', '今後の対応'],
                  [((a, 'k'), b, c, ST[d], f) for a, b, c, d, f in rows], widths=['20mm', '44mm', '42mm', '16mm', None], raw=True) +
            '<p class="small">状態：実装済＝目標を満たす仕組みがある／一部＝一部の構成のみ、または不足あり／未実装＝仕組みがない。詳細は「課題と改善案の一覧」。</p>')


PARTS = [
    ('scope', 1, '1. 前提と対象範囲', p_scope),
    ('perf', 1, '2. 性能', p_perf),
    ('cap', 1, '3. 容量', p_capacity),
    ('avail', 1, '4. 可用性・バックアップ', p_avail),
    ('sec', 1, '5. セキュリティ', p_sec),
    ('rel', 1, '6. 信頼性・データ整合性', p_rel),
    ('ops', 1, '7. 運用・保守', p_ops),
    ('port', 1, '8. 移植性・使いやすさ', p_port),
    ('sum', 1, '9. 非機能要件の一覧（まとめ）', p_summary),
]

if __name__ == '__main__':
    build_doc('非機能の設計', '性能・容量・可用性・セキュリティ・信頼性・運用・移植性・使いやすさ',
              'React 版（frontend＋REST API 3種）。Thymeleaf 版との違いを併記', RELATED,
              PARTS, G.ROOT / 'docs/design/nonfunctional_design.pdf')

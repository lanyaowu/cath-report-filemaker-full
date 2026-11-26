"""React 版と Thymeleaf 版の比較表"""
from extra_common import G, e, table, build_doc, RELATED

R, T = 'React 版', 'Thymeleaf 版'


def cmp(rows, head=('観点', R, T)):
    out = [f'<table class="cmp"><thead><tr><th style="width:30mm">{head[0]}</th><th>{head[1]}</th><th>{head[2]}</th></tr></thead><tbody>']
    for r in rows:
        if r[0] == '__grp__':
            out.append(f'<tr class="grp"><td colspan="3">{e(r[1])}</td></tr>')
        else:
            out.append(f'<tr><td class="k">{e(r[0])}</td><td>{r[1]}</td><td>{r[2]}</td></tr>')
    return ''.join(out) + '</tbody></table>'


def p_overview():
    return ('<h1>1. 概要</h1>'
            '<p class="lead">心カテーテルレポートは、同じ画面・同じデータモデル（13画面・約1,040項目）で2つの実装を作りました。本資料は両者を構成・機能・非機能の面から比較し、採用判断の材料とします。</p>' +
            table(['', R, T], [
                (('方式', 'k'), 'SPA（シングルページアプリケーション）。画面はブラウザの React が描画', 'サーバーサイドレンダリング。画面は Spring Boot + Thymeleaf がサーバーで HTML を生成'),
                (('構成', 'k'), 'frontend（React 18 + TypeScript）＋ 保存先を選択：localStorage（既定）または REST API（Node.js＋MongoDB／Spring Boot＋MongoDB／Spring Boot＋PostgreSQL）',
                 'Spring Boot 3.3 ＋ Thymeleaf ＋ PostgreSQL 16 の1アプリ。HTML＋素の JavaScript（ライブラリなし）'),
                (('起動', 'k'), 'ブラウザだけで動作（サーバー不要）。Remote DB 時は DB とバックエンドを別に起動', 'docker compose up で app・db を一括起動'),
                (('レビュー用', 'k'), 'デモ HTML（1ファイル・サンプルデータ入り）', 'レビュー用 HTML（1ファイル・テンプレートをブラウザ内で再現）'),
            ], widths=['22mm', None, None]) +
            '<h2>結論（要約）</h2>'
            '<div class="note">両版とも、認証・権限・確定ロック・同時更新の検知・監査ログをサーバーで検査します。<b>院内で複数人が使う本番運用</b>には、保存を1トランザクションで行い、主画面の規則もサーバーで守る <b>Thymeleaf 版</b>、または <b>React 版＋ Spring Boot＋PostgreSQL バックエンド</b>が向いています。'
            '<b>試作・デモ・操作性の検討</b>や、将来の高度な UI（入力補助・オフライン・他システムの画面組込み）を重視するなら <b>React 版</b>が有利です。'
            '詳しくは「6. 選定の目安」を参照してください。</div>')


def p_arch():
    return ('<h1>2. 構成の比較</h1>' + cmp([
        ('__grp__', 'アーキテクチャ'),
        ('画面の生成', 'ブラウザ（React の仮想 DOM）。画面切替はページ遷移なし', 'サーバー（Thymeleaf）。画面ごとに HTML を取得（1画面＝1リクエスト）'),
        ('状態の持ち方', 'AppContext に draft（編集中）と original（保存時）を保持。変更判定は2つの比較', 'HTML の各入力欄に表示時の値を記録し、JavaScript が入力ごとに比較'),
        ('入力と値の結び付け', 'useField(path)／Scope による相対パス', 'data-path 属性＋ th:value="${f[\'path\']}"'),
        ('画面数・項目', '13画面・約1,040項目（同一）', '13画面・約1,040項目（同一）'),
        ('__grp__', '保存'),
        ('保存の単位', '<b>レポート全体</b>を送信（PUT /api/reports/{id}）。患者は変更時のみ PUT', '<b>変更された項目だけ</b>を送信（POST /api/form/save、パス→値）。サーバーで JSON に反映'),
        ('トランザクション', '患者→レポートの2回の API 呼出し（別トランザクション）', '患者→レポートを1トランザクションで保存'),
        ('保存先', 'localStorage／MongoDB（2種）／PostgreSQL から選択', 'PostgreSQL のみ'),
        ('画像', 'JSON 内の dataUrl（Base64）。保存のたびに全画像を送信', 'DB は bytea。表示は画像 URL（/reports/{id}/images/{imageId}）。送信は追加分のみ'),
        ('__grp__', 'サーバー側の検証'),
        ('必須項目', 'バックエンドにより異なる（Node：患者ID・氏名・patientRef・header／Spring：加えて施行日）', '患者ID・氏名・施行日を保存時に検査'),
        ('主画面（共有項目）', '画面のみ（API はレポート全体の置換のため対象外）', '<span class="good">画面＋サーバー</span>（form/Ownership）'),
        ('確定ロック', '<span class="good">画面＋サーバー</span>（確定済みは 409）', '<span class="good">画面＋サーバー</span>（確定済みは 409）'),
        ('同時更新の検知', '<span class="good">version で 409</span>（全バックエンド）', '<span class="good">version で 409</span>'),
        ('認証・権限・監査', 'トークン（Bearer）・役割・監査ログ', 'セッション＋CSRF・役割・監査ログ'),
        ('__grp__', '技術・規模'),
        ('言語', 'TypeScript（画面）／TypeScript・Java（API）', 'Java（サーバー）／JavaScript（画面）'),
        ('依存ライブラリ', 'React・React DOM（実行時）、Vite・TypeScript（開発時）', 'Spring Boot スターター・Flyway・PostgreSQL JDBC（画面側は依存なし）'),
        ('コード量（概数）', 'frontend 約7,000行＋バックエンド3種 約2,800行', 'Java 約2,600行・テンプレート 約3,800行・JS 約1,100行・CSS 約440行'),
        ('自動テスト', 'node:test（計算・パス操作・権限・業務ルール）＋ JUnit（Spring 版）', 'JUnit：画面描画・保存ロジック・パス操作・変換・権限・DB 結合（Testcontainers）'),
        ('環境構築', 'Node.js（開発）。DB は docker compose（mongo・postgres）', 'Docker（app・db・pgAdmin）。Java 17 / Maven でも可'),
    ]))


def p_func():
    return ('<h1>3. 機能の比較</h1><p class="lead">業務機能はほぼ同じです。違いが出るのは、画面の切替・保存・印刷・データの扱いです。</p>' + cmp([
        ('一覧・検索', '同じ（施行日・キーワード・状態）。条件は画面の状態として保持', '同じ。条件はセッションに保存し、レコード送り・集計にも反映'),
        ('新規作成', 'ダイアログで患者を選び、メモリ上に作成（保存まで「変更あり」）', '同じ流れ。/reports/new で未保存の画面を表示'),
        ('画面の切替', '<span class="good">即時</span>（再描画のみ）', 'ページ遷移（サーバー往復）'),
        ('変更の見える化・確認', '保存ボタン赤・遷移時の確認・変更項目の黄色表示', '同じ'),
        ('自動計算・強調表示', 'BSA・LVG・D2B・HBR・CREDO-Kyoto・IVUS など（TypeScript）', '同じ（JavaScript）。結果の表示も同じ'),
        ('コピー・取込', '前回の検査値・過去 CAG 所見など', '同じ'),
        ('画像', '追加・削除・コメント。1.5MB を超える画像は登録不可', '同じ操作。画像本体は別 URL で取得するため一覧・画面表示が軽い'),
        ('マスタ', 'ダイアログで編集', '専用画面で編集'),
        ('保存先の切替', '<span class="good">あり</span>（Local／Remote）', 'なし（PostgreSQL 固定）'),
        ('集計', '画面内で集計', '画面内で集計＋ DB ビュー（月別・MACE）'),
        ('印刷', '検査報告書・一覧・時間経過シート（ブラウザ印刷）', '同じ'),
        ('キーボード', 'Ctrl+S で保存', 'Ctrl+S で保存'),
        ('オフライン', 'Local Storage なら<span class="good">ネットワーク不要</span>', '<span class="bad">サーバー必須</span>'),
        ('他システム連携', 'REST API（全体置換）', 'REST API（同じ形式）＋画面保存 API'),
    ]))


def p_nonfunc():
    return ('<h1>4. 非機能の比較</h1>' + cmp([
        ('__grp__', '性能'),
        ('初回表示', 'JavaScript 一式を読み込んでから描画', 'HTML を受け取ってすぐ表示（gzip 圧縮あり）'),
        ('画面切替', '<span class="good">速い</span>（通信なし）', '1画面ごとにサーバー往復'),
        ('保存の通信量', 'レポート全体＋全画像（数十KB〜数MB）', '<span class="good">変更項目だけ</span>（数百バイト〜）'),
        ('一覧', '画像本体を除いて取得（Remote）', '画像本体を除いて取得'),
        ('__grp__', '信頼性・データ整合性'),
        ('業務ルールの強制', '<span class="good">サーバーで強制</span>（権限・確定ロック・履歴）', '<span class="good">サーバーで強制</span>（主画面・確定ロック・必須・権限）'),
        ('同時編集', '<span class="good">検知</span>', '<span class="good">検知</span>'),
        ('保存の一貫性', '患者とレポートは別々に保存（途中失敗の可能性）', '<span class="good">1トランザクション</span>'),
        ('Local 時の容量', 'ブラウザの保存上限（約5MB）。画像なしで約140件が目安', '該当なし'),
        ('__grp__', 'セキュリティ（両版とも認証・権限・監査ログあり）'),
        ('データの所在', 'Local 時は各端末のブラウザに保存（本番は config.js で Remote に固定）', 'サーバーの DB に集約'),
        ('攻撃面', 'API を公開（CORS で許可元を制限）', '画面と API を同一オリジンで提供'),
        ('__grp__', '保守・運用'),
        ('変更のしやすさ', '画面と状態が型付きで結び付き、大規模な UI 変更に強い', '画面（テンプレート）とサーバーの両方に手を入れることが多い'),
        ('学習コスト', 'React・TypeScript・状態管理の知識が必要', 'Java/Spring と HTML の知識で保守可能'),
        ('配置', '静的ファイル配信＋（任意）API サーバー', 'Docker イメージ1つ＋ DB'),
        ('スキーマ管理', 'PostgreSQL 版は Flyway。MongoDB 版はスキーマなし', 'Flyway'),
    ]))


def p_pros():
    return ('<h1>5. 長所と短所</h1><div class="two"><div><h2>React 版</h2>' +
            table(['', '内容'], [
                (('長所', 'k good'), '画面の切替が速く、入力の操作感が良い'),
                (('長所', 'k good'), 'サーバーなしで動き、デモ・試用・オフライン利用が簡単'),
                (('長所', 'k good'), '保存先を差し替えられる（3種のバックエンド）'),
                (('長所', 'k good'), 'TypeScript の型で画面とデータの不整合を早期に発見'),
                (('短所', 'k bad'), '主画面（共有項目）の規則は画面だけで守っている（API は全体置換）'),
                (('短所', 'k bad'), '保存がレポート全体の置換で、通信量が多い（画像込み）'),
                (('短所', 'k bad'), 'Local 時は個人情報が端末に残り、共有もできない（本番は Remote に固定）'),
                (('短所', 'k bad'), '患者とレポートを別々の API で保存する（途中失敗の可能性）'),
            ], widths=['14mm', None]) +
            '</div><div><h2>Thymeleaf 版</h2>' +
            table(['', '内容'], [
                (('長所', 'k good'), '検証・排他・保存をサーバーで一元管理でき、データが壊れにくい'),
                (('長所', 'k good'), '保存は変更項目だけで軽い。画像は URL で配信'),
                (('長所', 'k good'), 'Docker で一括起動。DB ビューで二次利用しやすい'),
                (('長所', 'k good'), 'Java の知識で保守でき、テストが揃っている'),
                (('短所', 'k bad'), '画面切替のたびにサーバー往復があり、React 版より遅い'),
                (('短所', 'k bad'), 'サーバーがないと使えない'),
                (('短所', 'k bad'), '画面の動き（JavaScript）とテンプレートが分かれ、複雑な UI の追加は手間'),
                (('短所', 'k bad'), 'テンプレートが大きく（約3,800行）、項目追加時の修正箇所が多い'),
            ], widths=['14mm', None]) + '</div></div>')


def p_choose():
    return ('<h1>6. 選定の目安</h1>' +
            table(['状況・重視する点', '向いている版', '理由'], [
                ('院内で複数の医師・秘書が同時に使う', (T, 'k'), 'サーバーでのルール強制・同時更新の検知・1トランザクション保存'),
                ('データの正確さ・監査対応を重視', (T, 'k'), '保存経路が1つで、検証を集中して強化できる'),
                ('IT 部門が Java 中心で保守する', (T, 'k'), '技術要素が少なく、学習コストが低い'),
                ('操作感・入力速度を重視', (R, 'k'), '画面切替が即時'),
                ('デモ・試用・要件確認の段階', (R, 'k'), 'サーバー不要で配布でき、変更の反映も速い'),
                ('ネットワークが不安定な場所でも使いたい', (R, 'k'), 'Local Storage で動作（要：同期の仕組み）'),
                ('将来、電子カルテ等の画面に組み込む・高度な UI を作る', (R, 'k'), 'コンポーネント単位で再利用しやすい'),
            ], widths=['62mm', '24mm', None]) +
            '<h2>推奨する進め方</h2>'
            '<div class="note">1. 要件確認・画面レビューは React 版のデモで行う（変更が速い）。<br>'
            '2. 本番は <b>Thymeleaf 版</b>、または <b>React 版＋ Spring Boot＋PostgreSQL バックエンド</b>（MongoDB 版は開発用）。どちらも認証・権限・確定ロック・同時更新の検知・監査ログをサーバーで検査する。<br>'
            '3. 本番前に、HTTPS の証明書・本番の利用者定義・バックアップの cron 登録などを docs/security.md のチェックリストで確認する。</div>')


PARTS = [
    ('ov', 1, '1. 概要', p_overview),
    ('arch', 1, '2. 構成の比較', p_arch),
    ('func', 1, '3. 機能の比較', p_func),
    ('nf', 1, '4. 非機能の比較', p_nonfunc),
    ('pros', 1, '5. 長所と短所', p_pros),
    ('choose', 1, '6. 選定の目安', p_choose),
]

if __name__ == '__main__':
    build_doc('React 版と Thymeleaf 版の比較表', '構成・機能・非機能・長所と短所・選定の目安',
              'React 版（frontend＋REST API 3種）と Thymeleaf 版（Spring Boot＋Thymeleaf＋PostgreSQL）', RELATED,
              PARTS, G.ROOT / 'docs/design/compare_react_thymeleaf.pdf')

# 心カテーテルレポート（React + TypeScript / Node.js・Spring Boot / MongoDB・PostgreSQL）

参考画面イメージ（一覧・カテ記録・CAG/LVG・PCI 各タブ・Pressure/IVUS・PCPS・カンファレンス・MACE）を元にした心カテーテルレポートシステムです。
参考画面の無い「患者情報入力」「LVG」「画像」「Restudy」「集計」は、日本循環器学会の報告書項目・J-PCI レジストリ項目を参考に推測して作成しています。

```
cathreport/
├─ frontend/          React 18 + TypeScript + Vite（UI・永続化切替）
├─ backend-node/      Node.js + Express + MongoDB（TypeScript）
├─ backend-spring/    Java 17 + Spring Boot 3 + Spring Data MongoDB
├─ backend-spring-pg/ Java 17 + Spring Boot 3 + Spring Data JPA + PostgreSQL（Flyway）
├─ sample-data/       サンプルデータ（患者8名・レポート9件・マスタ）※全バージョン共通
├─ docs/
│   ├─ ER.md          ER図（Mermaid）＋画面間共有項目の一覧
│   ├─ er.svg / er.png                 ER図（縦長）
│   ├─ er_landscape.svg / er_landscape.png  ER図（横長・印刷向け）
│   ├─ er.html        ER図ビューア（Mermaid）
│   ├─ er_postgres.svg / er_postgres.png  PostgreSQL 版のテーブル構成
│   ├─ fields.md      全入力項目一覧（1,058 項目・自動生成）
│   └─ api.md         REST API 仕様（両バックエンド共通）
├─ tools/gen_sample_data.py   サンプルデータ生成スクリプト
├─ tools/gen_er_diagram.py    ER図(SVG/PNG)生成（ER.md → Graphviz）
├─ tools/gen_pg_er.py         PostgreSQL 版 ER図生成（V1__init.sql → Graphviz）
└─ docker-compose.yml         MongoDB / PostgreSQL
```

## 認証・権限（本番運用の前に docs/security.md を必ず読む）

- **ログインが必要**です（Remote DB はサーバーで認証、Local Storage はデモ用の利用者でブラウザ内で照合）。デモ用の利用者：`admin / demo-admin`（管理者）、`yamada / demo-yamada`（医師）、`hisho / demo-hisho`（秘書）、`etsuran / demo-etsuran`（閲覧）。
- 役割ごとに、入力・確定・照合・削除・マスタ編集を制御します。確定ロック・同時更新の検知（version）・登録履歴の保護は**サーバーでも検査**します。
- 操作は監査ログ（`GET /api/audit`、管理者のみ）に記録します。PostgreSQL 版はトリガーで改ざんを防止。
- 患者・レポートの保存では、**変わった項目ごとの変更前・変更後**も記録します。トップバーの「監査ログ」（管理者のみ）と、サイドメニューの「項目ごとの変更履歴」で確かめられます（詳細は docs/security.md の 4 章）。
- `POST /api/admin/seed`（全データ置換）は既定で無効（`ALLOW_SEED_API=true` で有効）。
- 本番では `frontend/dist/config.js` を `config.production.example.js` の内容にして、保存先を Remote DB に固定します。
- バックアップ：`tools/backup/pg_backup.sh`・`pg_restore.sh`・`mongo_backup.sh`。テスト：`backend-node` と `frontend` で `npm test`、Spring 版は `mvn test`。

## 優先度「高」の不足項目への対応（2026/11）

`docs/design/missing_items.pdf` の優先度「高」9 件を、React 版・Node.js／Spring Boot（MongoDB・PostgreSQL）・Thymeleaf 版のすべてに実装しました。

| No | 内容 | 主な場所 |
|---|---|---|
| G-01 | 既往歴・併存症（心筋梗塞・心不全・PCI・CABG・腎不全・COPD・AAA/PAD）をカテ記録で記録。J-PCI タブは参照 | カテ記録（危険因子）・`cathRecord.risk` |
| G-08 | 手技の開始・終了時刻と手技時間（自動計算） | カテ記録（検査情報）・`cathRecord.exam.startTime/endTime` |
| G-15 | 狭窄度の JCS 標準区分（AHA を区間の上限で対応付け、QCA 実測値を優先） | CAG のセグメント表・検査報告書 |
| G-25 | 病変ごとの閉塞期間・J-CTO 5 項目とスコア | PCI（Bif/CTO）・`pci.lesions[].cto.duration/jcto` |
| G-26 | ACC/AHA Type の自動提案（「適用」で反映） | PCI（病変形態） |
| G-27 | 病変成功の自動判定（術後 ≤25% かつ TIMI 3） | PCI（J-PCI） |
| G-35 | 合併症（全検査共通） | カテ記録・`cathRecord.complications` |
| G-40 | 確定前の確認（未入力の必須項目・自動判定との食い違い。警告のみ） | サイドメニューの「確定」 |
| G-41 | 検査報告書（A4） | 上部の「🖨 検査報告書」 |

- 判定の規則は `frontend/src/utils/clinical.ts`（テスト：`frontend/test/clinical.test.ts`）。Thymeleaf 版は `service/Clinical.java` と `static/js/screens.js` に同じ規則があります。
- **既存データの移行**：画面は読込時に旧形式（J-PCI の既往歴、Age of Occlusion）を自動で移すため、そのままでも動きます。DB のデータも揃える場合：
  - PostgreSQL 版：Flyway の `V4__history_to_cath_record.sql` が起動時に自動で実行されます。
  - MongoDB 版：`mongosh "mongodb://localhost:27017/cathreport" tools/migrate/mongo_v4_history.js`

## 繰り返し項目の可変化（2026/11/23）

次の項目は、行（列）の数を入力に合わせて増減できるようにしました。最大数を超えては追加できません。

| 画面 | 項目 | 最大 |
|---|---|---|
| CAG/LVG | Collaterals | 5 行 |
| CAG/LVG | Bypass Grafts | 4 行 |
| PCI（基本） | ガイディングカテーテル | 5 行 |
| PCI（基本） | マイクロカテーテル | 4 行 |
| PCI（基本） | ガイドワイヤー | 5 行（以前は 10 枠） |
| PCI（全タブ） | Target（病変） | 5 列 |
| Pressure/IVUS | Pressure Wire の病変 | 5 列（以前は 3 列） |

- 「＋ 追加」で 1 行（列）ずつ増やす。ボタンに件数（例：3/5）を表示し、最大数で押せなくなる。
- 「✖」でその行（列）を削除し、後ろを前に詰める。入力がある時は確認してから削除する。最後の 1 行は削除せず入力をクリアする。
- PCI の病変は、どのタブ（病変形態・Device・Bif/CTO・Complication など）からでも追加・削除でき、全タブ・J-PCI の病変情報・検索用・基本タブの病変単位治療が同じ数になる。
- 新規レポートは各 1 行（列）から始まる。保存済みのデータは、読み込み時に末尾の空の行を除いて表示する（途中の空の行は病変番号を変えないよう残す）。最大数を超えて入力済みの旧データ（ガイドワイヤーの 6 本目以降など）は消さずに表示し、追加だけできなくなる。
- 実装：`frontend/src/form/repeat.tsx`（追加・削除ボタン。連動する配列は `linked`）、`model/defaults.ts` の `LIST_MAX`・`fitList`・`fitPair`（最大数・読込時の整形）、テスト `frontend/test/lists.test.ts`。

### Pressure Wire の病変と IVUS の Lesion タブの連携（2026/11/23）

- Pressure Wire の病変 N と IVUS の Lesion N は同じ病変として扱う。Lesion タブは Pressure Wire の病変の数だけ（最大 5 つ。以前は Lesion 1〜4 の固定）表示する。
- 追加・削除は連動する：Pressure Wire の「＋ 病変を追加」・タブ横の「＋ Lesion」のどちらでも両方が増え、Pressure Wire の列の「✖」・Lesion タブの「この病変を削除」のどちらでも両方が消えて後ろが詰まる（IVUS の入力も一緒に移る）。
- 病変名は 1 つのデータ（`pressureIvus.pressure[N].lesion`）を共有する。Lesion タブの「対象部位」はこの値を表示・編集し、タブ名にも病変名を出す（例：Lesion 1 LCX#13）。
- 旧データ：Pressure Wire の病変名が空で IVUS の部位（`lesions[N].site`）だけある時は、読み込み時に部位を病変名へ移す。両方あって違う時は Pressure Wire を優先し、IVUS 側の値は消さずに残す（画面には出さない）。

### 病変（Target）のデータ連携の整理（2026/11/23）

- 画面・タブ間で病変がどうつながっているか（同一・同じ番号・名前の一致・複写/集計の 4 種類）を整理し、データモデルに記載した。
  - `docs/ER.md`：点線（`..`）の関係として連携を追加し、「病変（Target）のデータ連携」の節（病変を表すデータ・連携の一覧・注意点）を追加。ER 図（`docs/er_a3`）は青破線で表示。
  - `frontend/src/types/model.ts`：連携の概要と、target・lesion・site などの項目にコメント。
  - 設計資料：`react_design_A3_diagrams.pdf`（3.1 全体構造に青破線）、`react_design_A4_text.pdf`（3.7 病変のデータ連携）、`shared_data_between_screens.pdf`（9 章）。
- 分かった注意点（未修正）：QCA 取得の照合が「番号を含むか」のため #1 が LCX#13 にも一致する、病変名の書き方が画面ごとに違う、狭窄度・標的病変数が複数の欄にある、など。

### ログイン画面（2026/11/23）

- **保存先にかかわらず、全画面のログイン画面からログイン**します（以前は Remote DB の時だけ小さなダイアログ）。デモ HTML（Local Storage）でも同じです。
- Local Storage（デモ）では、サーバーと同じ利用者定義（`frontend/src/data/users.json`＝`sample-data/users.json`、PBKDF2）でブラウザ内で照合します。ログイン画面にデモ用の利用者（admin・yamada・sato・hisho・etsuran、パスワードは `demo-ユーザー名`）を出し、クリックで入力できます。役割ごとの権限（閲覧者は入力・保存不可など）もそのまま体験できます。
  - これは画面を体験するためのもので、端末内のデータを守る仕組みではありません。本番は `config.js` で保存先を Remote DB に固定し、サーバーで認証します。
- 保存の登録履歴の記録者は、ログイン中の利用者になります（Remote はサーバーでも上書き）。
- 画面右上に利用者名とログアウト。ログアウトでログイン画面に戻ります。
- 画面イメージ集の先頭（00_login.png）にログイン画面を追加しました。
- 実装：`frontend/src/components/auth/LoginScreen.tsx`、`frontend/src/auth/localAuth.ts`、`state/AppContext.tsx`（login・logout・authRequired）。

## 選択値マスタ（2026/11/24）

> **選択値マスタ＋監査機能の統合版（2026/11/24）**：監査機能の版（after-high9_audit）に選択値マスタを統合しました。選択値マスタの保存は監査ログに「選択値マスタの更新」として残り、行の ▶ で選択値ごとの「表示名・使用・並び順」の変更前→変更後を確認できます。

画面の選択肢（アプローチ部位・シース・造影剤・カテーテル形状・デバイス種別・薬剤の用法 など）を DB で管理し、管理者が画面から編集できるようにしました。

- **画面**：上部の「選択値」（管理者のみ）。左でカテゴリを選び、右で表示名の変更・並べ替え（▲▼）・追加・使用停止を行い、カテゴリ単位で保存します。
- **対象**：40 カテゴリ・243 選択値。施設で編集できるもの 26、標準の分類 14（TIMI・ACC/AHA Type・屈曲・蛇行・PCI 結果・NYHA・CCS・CAD-RADS・J-PCI の診断/症状 など。自動判定・レジストリで値を使うため編集不可 🔒）。
  ＋/−/不明 のような汎用の選択肢と、表の列・チェック項目（データ構造そのもの）はプログラムのままです。
- **既存データ**：レポートに保存するのは「コード」で、既存の値をそのままコードにしたため**移行は不要**です。保存済みのコードは削除・変更できず、使わなくなった値は「使用停止」にします。使用停止の値は新しい入力の候補から外れ、その値が入ったレポートでは「（使用停止）」付きで表示されます。
- **保存先**：Local Storage（`cath.optionMasters`）／ Node.js＋MongoDB（コレクション `option_categories`、選択値は配列で埋め込み。変更前の内容は `option_category_history`、要約は監査ログ `UPDATE_OPTIONS`）。
  初期データは起動時に、無いカテゴリだけ追加します（施設で編集した内容は上書きしません）。
- **未対応のバックエンド**（Spring Boot＋MongoDB / Spring Boot＋PostgreSQL の API 版）：`GET /api/options` が 404 のため、画面はプログラムの初期値で表示し、選択値画面は表示のみになります。
- **同時更新**：version で検知（他の人が先に保存していれば 409）。
- 実装：
  - 定義（初期値）：`frontend/src/constants/options.ts` の `cat(...)`。選択肢を追加する時はここに書き、`npx tsx tools/gen_option_masters.ts` で初期データ（`sample-data/option-masters.json`）を作り直す。
  - 画面：`model/optionMaster.ts`（合成・表示する選択肢の決定・入力チェック）、`form/OptionsContext.tsx`（`SelectF`・`RadioF`・`TextF` の list が自動でマスタを使う）、`components/dialogs/OptionMasterDialog.tsx`。
  - サーバー：`backend-node/src/options.ts`（入力チェック・変更の要約）、`routes/api.ts`（`/api/options`）、`db.ts`（`seedOptionMasters`）。
  - テスト：`frontend/test/optionMaster.test.ts`、`backend-node/test/options.test.ts`。
  - デモ HTML（`demo/cath-report-demo.html`）も作り直し、選択値画面を Local Storage で操作できます。

## 多言語対応：日本語・中文（簡体字）（2026/11/26）

ヘッダー右上（ログイン画面は右上）の言語の切替で、画面の全文言（メニュー・ボタン・項目名・タブ・メッセージ・確定前の確認・検査報告書）を日本語 ⇔ 簡体字中国語に切り替えます。TIMI・FFR などの英語の医学用語、人名・医療機関名はそのままです。

- **仕組み**：画面の文言は日本語のまま書き、表示の直前に DOM の文字（テキスト・title・placeholder・aria-label）を辞書で置き換えます（`frontend/src/i18n/translator.ts`）。React の再描画は MutationObserver で追いかけます。`confirm` / `alert` の文言も訳します。日本語に戻すと元の文字に戻します。
- **保存する値は変わりません**：入力欄の値・選択肢の value（コード）・ステータス（入力中／確定）などは日本語のまま保存されます。翻訳しない部分は `data-no-i18n` を付けます。
- **辞書**：`frontend/src/i18n/zh-CN.json`（完全一致 約1,290 件＋パターン 約135 件。`{}` は数値・名前などの可変部分）。React 版・Node.js 版・Thymeleaf 版のソースから日本語の文字列を抜き出して作成しました。足りない文言はここに追加します（パターンは `{}` の数を訳と同じにする。`test/i18n.test.ts` で検査）。
- **言語の保存**：Local Storage の `cath.lang`（`ja` / `zh-CN`）。
- **選択値マスタの中国語の表示名**：選択値ごとに `labels: { "zh-CN": "…" }` を持てます。管理者は「選択値」ダイアログの「表示名（中国語）」で編集できます（空なら日本語の表示名を辞書で訳して表示）。初期値は辞書から作成（`tools/gen_option_masters.ts` → `sample-data/option-masters.json`）。変更は監査ログに `コード.表示名(zh-CN)` として残ります。Node.js 版の API も `items[].labels` を受け付けて検査します（対応言語は zh-CN のみ・200 文字以内）。
- **Thymeleaf 版への反映**：`node tools/i18n/build-tl.mjs ../cath-report-tl` で翻訳の部品（`static/js/i18n.js`）と辞書（`static/js/i18n-zh-CN.js`）を書き出します。
- **制限**：自由入力欄に保存済みの日本語の値（例：造影剤名の入力値）、CSV 出力の見出し・内容、サンプルデータの名称は日本語のままです。

## 起動方法

### 1. フロントエンドのみ（Local Storage・既定）
```bash
cd frontend
npm install
npm run dev        # http://localhost:5173
```
初回起動時にサンプルデータが Local Storage に投入されます。バックエンド不要で全機能を試せます。

### 2. MongoDB + バックエンド（Remote DB）
```bash
docker compose up -d mongo            # MongoDB を起動

# Node 版
cd backend-node && npm install && npm run dev        # http://localhost:8080/api

# または Spring Boot 版（同じポート・同じAPI）
cd backend-spring && mvn spring-boot:run             # http://localhost:8080/api
```
### 3. PostgreSQL + Spring Boot（Remote DB）
```bash
docker compose up -d postgres
cd backend-spring-pg && mvn spring-boot:run           # http://localhost:8080/api（同じAPI）
```
テーブル設計・集計ビュー・同時更新検知は `backend-spring-pg/README.md` を参照。

いずれも DB が空なら起動時にサンプルデータを投入します（`SEED_ON_STARTUP=false` で無効化）。
画面右上の「💾 Local」ボタン →「Remote DB」を選択すると切り替わります（API URL 既定 `/api`。開発サーバーが 8080 へプロキシ）。

環境変数: `PORT` / `MONGODB_URI` / `MONGODB_DB`(Node) / `CORS_ORIGIN` / `SEED_ON_STARTUP` / `SAMPLE_DIR`(Node)

## 主な仕様

| 要件 | 実装 |
|---|---|
| 入力 UI のタイトルは右寄せ | `form/fields.tsx` の `Fld`（ラベル幅指定＋右寄せ） |
| 変更時「保存」ボタンが赤 | `isDirty`（保存値と編集値の比較）で `btn-dirty`（赤・点滅） |
| 画面遷移時に変更確認 | `guard()` が全遷移（メニュー・レコード送り・カテ履歴・一覧・保存先切替）を仲介 |
| 「放棄」 | 編集内容を破棄して遷移 |
| 「キャンセル」 | 遷移せず、保存値から変更された項目を黄色表示 |
| 永続化切替 | `storage/` の `StorageAdapter`（LocalStorage / Remote REST）。既定 Local |
| 画面間のデータ関連 | 共有項目は同一パスを参照（docs/ER.md 参照）。例：J-PCI の透視時間＝カテ記録の透視時間 |
| コンポーネント化 | 入力部品（`TextF/NumF/RadioF/CheckF/TripleF…`）はパス指定だけで値・変更判定・黄色表示が働く |

### 画面と入力ロジック
- **カテ記録**：目的（CAG/PCI/S-G/EVT/Follow-up/その他1/その他2）、Follow-up→理由、担癌患者→癌の名称、大動脈疾患→分類が入力可能に。シース（名称・サイズ）、造影剤（種類・使用量）、術者/助手 各3名、Hemodynamics の RA〜Ao pre は収縮期/拡張期/平均、HBs抗原・HCV抗体（検査日・定性・C値）、検査値は基準範囲外をピンク表示、前回からコピー。
- **CAG/LVG**：Approach（Artery・シース名称/サイズ・Vein・シース名称/サイズ・サポート）、Catheter 10 項目（形状・サイズ、任意1/2は名称入力）、セグメント所見表（Normal 一括・75%以上ピンク）、Collaterals / Bypass Grafts を「送達元 → 送達先」の2入力＋矢印で表現、病変枝数を所見から算出、過去所見/コメントのコピー。LVG は推測項目（容積・EF 算出、AHA 7分画の壁運動図をクリックで入力、MR、AOG）。
- **PCI**：基本・病変形態・Device・Bif/CTO・Complication・J-PCI・出血/血栓リスク（HBR 判定・CREDO-Kyoto スコア自動計算）・AMI（Onset/Door to balloon 自動計算、時間経過シート）・検索用・参考資料（分岐部タイプ/ストラテジー/Medina の模式図）。病変形態の「取得」は Pressure Wire の QCA を取り込み。
- **Pressure/IVUS**：Pressure Wire の病変 1〜5 列（可変。FFR≦0.80 等をピンク表示）、Lesion 1〜5 タブ（Pressure Wire の病変と同じ数・同じ病変名で連動。Pre/Post × 病変部位/Proximal/Distal、プラーク CSA・面積率・偏心率を算出）。
- **PCPS / MACE**：時間差・PCI 後経過日数を自動計算。MACE 1〜5 タブ。
- **カンファレンス**：血行動態・危険因子・LVG 値・予後はカテ記録/LVG と共通データ。病歴総括からコピー、検査未実施、Previous PCI は当院 PCI 歴を自動表示。
- **画像**：画像アップロード（1.5MB まで）、種別・撮影方向・対象病変・所見・キー画像、拡大表示。サンプルにシネ/心電図/IVUS/X-P の模式画像を同梱。

## 補足
- 画面の外部連携ボタン（数値取得・採血取得 等）はダミーです（通知を表示）。ヘッダーの G-NAVI・WEB・予定表・病歴総括 ボタンは 2026/11/26 に削除しました。
- Local Storage は約 5MB が上限のため、画像を多く扱う場合は Remote DB を使用してください。
- サンプルデータの患者・医師名はすべて架空です。

## レビュー用デモ（HTML 単一ファイル）・画面イメージ
- `demo/cath-report-demo.html` … ダブルクリックでブラウザ表示（サーバー・インストール不要、Local Storage 保存、サンプルデータ入り）。
  React 互換の簡易ランタイム（`tools/demo/mini-react.js`）で同じソースを動かしています。再生成: `node tools/demo/build-demo.mjs`
- `demo/screenshots/*.png` … 全画面の画像（ログイン画面を含む 49 枚）。再生成: `python3 tools/demo/screenshots.py`（Playwright + Chrome）
- `demo/cath-report-screenshots.pdf` … 全画面イメージ集（A3・表紙/目次付き）。再生成: `python3 tools/demo/screenshots_pdf.py`
- `docs/field_list.xlsx` … 全入力項目一覧（Excel：画面別集計／項目一覧 1,040 行／選択肢一覧）。再生成: `python3 tools/gen_field_list.py`（事前に defaults を JS へ変換した /tmp/dump.json が必要。手順はスクリプト冒頭参照）
- `docs/er_a3/` … A3 印刷用に分割した ER 図（全体概要＋グループ別 6 ページ、PNG 200dpi / SVG / 全ページ PDF）。再生成: `python3 tools/gen_er_a3.py`
- `sample-data/images/` … サンプル画像（38枚・SVG、架空の模式図）と一覧 index.csv。サンプルデータ（reports.json）に埋め込み済み。生成: `tools/sample_images.py`
  ※既にブラウザで一度デモを開いている場合は、画面右上「💾 Local」→「現在の保存先にサンプルデータを投入」で新しいサンプルに入れ替わります。
- `docs/architecture/` … システム構成図・データフロー図（DFD）・画面間データ連携図・処理シーケンス図（SVG / PNG / A3 PNG / `architecture_a3.pdf`）。再生成: `python3 tools/gen_arch_diagrams.py`
- `docs/datamodel/datamodel_dataflow.pdf` … **統合版（選択値マスタ＋監査機能）のデータモデル・データフロー**（A3 横 13 ページ：概念 ER、PostgreSQL・MongoDB・Local Storage のモデル、レポートの構造、選択値・監査のデータ、DFD、保存・選択値変更・ログインのシーケンス、CRUD 表）。再生成: `python3 tools/docs/datamodel/build.py`（Graphviz・mermaid-cli・Chrome）
- `docs/operations/operations_manual.pdf` … **運用手順書（統合版）**（A4 19 ページ：導入、日常の確認、利用者・マスタ・選択値の管理、監査ログの点検、バックアップと復元、更新、障害対応、セキュリティの点検）。本文は Thymeleaf 版（Docker＋PostgreSQL）、React 版（Node.js＋MongoDB）の違いは付録 A

# 心カテーテルレポート REST API（Spring Boot 3 / PostgreSQL）

MongoDB 版（`backend-spring/`・`backend-node/`）と **同じ REST API・同じ JSON 形式** のバックエンドです。
フロントエンドは変更なしで、画面右上の保存先を「Remote DB」にすると利用できます。

| 項目 | 内容 |
|---|---|
| 言語・FW | Java 17 / Spring Boot 3.3（Web・Data JPA・Validation） |
| DB | PostgreSQL 14 以上（16 で確認） |
| スキーマ管理 | Flyway（`src/main/resources/db/migration`）。Hibernate の自動生成は不使用 |
| 接続 | HikariCP / PostgreSQL JDBC |

## 起動

```bash
# 1. PostgreSQL（リポジトリ直下で）
docker compose up -d postgres          # DB: cathreport / ユーザー: cathreport / パスワード: cathreport

# 2. API
cd backend-spring-pg
mvn spring-boot:run                    # http://localhost:8080/api
```

初回起動時に Flyway がテーブル・ビューを作成し、DB が空ならサンプルデータ（患者8名・レポート9件・画像38枚・マスタ）を投入します。

| 環境変数 | 既定値 |
|---|---|
| `DB_URL` | `jdbc:postgresql://localhost:5432/cathreport` |
| `DB_USER` / `DB_PASSWORD` | `cathreport` / `cathreport` |
| `DB_POOL_SIZE` | `10` |
| `PORT` | `8080` |
| `CORS_ORIGIN` | `http://localhost:5173` |
| `SEED_ON_STARTUP` | `true`（`false` で投入しない） |
| `SPRING_PROFILES_ACTIVE=sql` | 実行 SQL をログ出力 |

テスト: `mvn test`（`EntityMapperTest` は DB 不要。`PostgresIntegrationTest` は Docker があれば Testcontainers で実 PostgreSQL を起動して実行、無ければスキップ）

## テーブル設計（ハイブリッド：列 ＋ JSONB）

ER 図: `docs/er_postgres.svg` / `.png`（再生成 `python3 tools/gen_pg_er.py`）

| テーブル | 内容 | 主な列 |
|---|---|---|
| `patients` | 患者 | 患者ID（一意）・氏名・フリガナ・生年月日（DATE）… 連絡先/保険/アレルギー/感染症/紹介元は JSONB |
| `patient_admissions` | 病歴総括 | 入院日・退院日・担当医・診断・要約 |
| `cath_reports` | カテレポート（1検査=1行） | 施行日（DATE）・Cine No・PCI No・ステータス（入力中/確定）・照合済・各チェック ／ 画面ごとの詳細は JSONB（`cath_record` `cag_lvg` `pci` `pressure_ivus` `pcps` `conference` `restudy`） |
| `report_history` | 登録履歴 | 日時・登録者・操作 |
| `report_mace` | MACE 1〜5 | 画面の全項目（`data` JSONB）＋集計用に展開した列（死亡/ACS/脳卒中/心不全/出血/再血行再建の有無、最初のイベント日） |
| `report_images` | 画像メタ情報 | 種別・撮影日・撮影方向・対象病変・所見・キー画像 |
| `report_image_data` | 画像本体 | `bytea`（data URL を base64 デコードして保存。約25%小さくなる） |
| `master_items` | マスタ | 種別（doctor / hospital / device）・カテゴリ・名称・並び順 |

**この形にした理由**
- 検索・整合性に関わる項目（患者ID の一意性、施行日、ステータス、患者⇔レポートの外部キー）は列にして制約をかける。
- 各画面の詳細項目（約1,000項目）は画面単位で一括保存・一括取得する UI と同じ単位の JSONB にする。項目の追加・変更でマイグレーションが不要で、MongoDB 版とデータ形式も一致する。
- 画像本体は別テーブルにし、一覧取得（`GET /reports`）では読み込まない。
- JSONB には GIN インデックスを張っており、`cath_record @> '{"exam":{"urgency":"緊急"}}'` のような検索ができる。

**制約**: 患者ID 一意 / レポートのある患者は削除不可（RESTRICT）/ レポート削除で履歴・MACE・画像も削除（CASCADE）/ ステータスは「入力中」「確定」のみ（CHECK）/ 日付は DATE 型（不正な日付は 400）。

## MongoDB 版との違い

| | MongoDB 版 | PostgreSQL 版 |
|---|---|---|
| API・JSON 形式 | 同一 | 同一（`version` 項目が追加で返る） |
| 同時更新の検知 | なし | `version`（楽観ロック）。送信された `version` が DB と異なれば **409**。送らなければ従来どおり上書き |
| 集計 | アプリ側 | ビュー `v_report_summary` / `v_mace_events` / `v_monthly_stats`、API `GET /api/stats/monthly` `GET /api/stats/mace` |
| 画像 | 文書内に data URL | `bytea` で別テーブル。同じ内容なら再書き込みしない |

フロントエンドは保存後にサーバーの返却値（新しい `version`）で状態を更新するため、通常操作で 409 になることはありません。別の端末で同じレポートを先に保存した場合のみ「他の端末で更新されています。再読み込みしてください」と表示されます。

## 集計ビューの例

```sql
SELECT study_date, patient_name, age_at_study, urgency, approach, contrast_ml, fluoro_time_min, image_count
FROM v_report_summary ORDER BY study_date DESC;

SELECT * FROM v_monthly_stats;          -- 月別件数・PCI件数・緊急件数・平均造影剤量・平均透視時間
SELECT * FROM v_mace_events WHERE has_major_event;
```

## ソース構成

```
src/main/java/jp/example/cathreport/
├─ api/          API の JSON 形式（Patient / CathReport / ReportHeader / Masters）
├─ entity/       JPA エンティティ（PatientEntity / CathReportEntity / MasterItemEntity）
├─ repository/   Spring Data JPA ＋ ImageDataDao（画像本体、JdbcTemplate）
├─ service/      EntityMapper（JSON⇔エンティティ）・各サービス・SampleDataService
├─ web/          REST コントローラ・例外ハンドラ（{"error": "..."} 形式）
└─ config/       CORS
src/main/resources/db/migration/
├─ V1__init.sql  テーブル・制約・インデックス
└─ V2__views.sql 集計ビュー・cr_num()（数値変換）
```

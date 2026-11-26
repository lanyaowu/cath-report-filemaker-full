-- =====================================================================
-- 心カテーテルレポート PostgreSQL スキーマ（V1）
--
-- 方針（ハイブリッド設計）
--   ・識別・検索・整合性に関わる項目は「列」で持つ（患者、レポートヘッダ、
--     ステータス、画像メタ情報、登録履歴、MACE の主要イベント、マスタ）。
--   ・各画面の詳細項目（約1,000項目、今後も増減する）は画面単位の JSONB 列に持つ。
--     画面単位で一括保存・一括取得する UI と一致し、項目追加でマイグレーション不要。
--   ・画像本体は別テーブル（bytea）に分離し、一覧取得で読み込まない。
--   ・日付は DATE、日時は TIMESTAMPTZ（API 上は ISO 文字列）。
-- =====================================================================

-- ---------- 患者 ----------
CREATE TABLE patients (
  id              VARCHAR(64)  PRIMARY KEY,           -- アプリ内部ID（例: pt-001）
  patient_id      VARCHAR(32)  NOT NULL,              -- 病院の患者ID
  name            VARCHAR(100) NOT NULL,
  kana            VARCHAR(100),
  sex             VARCHAR(8),
  birth_date      DATE,
  blood_type      VARCHAR(4),
  rh              VARCHAR(4),
  zip             VARCHAR(16),
  address         VARCHAR(300),
  phone           VARCHAR(32),
  mobile          VARCHAR(32),
  emergency       JSONB,                              -- 緊急連絡先 {name, relation, phone}
  insurance       JSONB,                              -- 保険 {type, number}
  allergy         JSONB,                              -- アレルギー {contrast, drug, latex, iodine, food, ...}
  infection       JSONB,                              -- 感染症 {hbs, hcv, hiv, syphilis, mrsa}
  primary_doctor  VARCHAR(100),
  ward            VARCHAR(50),
  referral        JSONB,                              -- 紹介元 {hospital, doctor}
  dnar            BOOLEAN      NOT NULL DEFAULT FALSE,
  past_history    TEXT,
  family_history  TEXT,
  medication_note TEXT,
  notes           TEXT,
  created_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
  updated_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
  version         BIGINT       NOT NULL DEFAULT 0,    -- 楽観ロック
  CONSTRAINT uq_patients_patient_id UNIQUE (patient_id)
);
CREATE INDEX ix_patients_kana ON patients (kana);
COMMENT ON TABLE patients IS '患者';

-- 病歴総括（患者 1 : N）
CREATE TABLE patient_admissions (
  patient_id     VARCHAR(64) NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
  seq            INTEGER     NOT NULL,
  admit_date     DATE,
  discharge_date DATE,
  doctor         VARCHAR(100),
  diagnosis      VARCHAR(300),
  summary        TEXT,
  PRIMARY KEY (patient_id, seq)
);
COMMENT ON TABLE patient_admissions IS '病歴総括（入退院歴）';

-- ---------- カテレポート（1回のカテ検査 = 1行） ----------
CREATE TABLE cath_reports (
  id                VARCHAR(64) PRIMARY KEY,
  patient_ref       VARCHAR(64) NOT NULL REFERENCES patients(id) ON DELETE RESTRICT,
  status            VARCHAR(8)  NOT NULL DEFAULT '入力中',
  verified          BOOLEAN     NOT NULL DEFAULT FALSE,           -- 照合済
  -- ヘッダ（全画面共通）
  study_date        DATE        NOT NULL,                         -- 施行日
  cine_no           VARCHAR(32),
  pci_no            VARCHAR(32),
  accession_no      VARCHAR(32),
  secretary_checked BOOLEAN     NOT NULL DEFAULT FALSE,
  summary           BOOLEAN     NOT NULL DEFAULT FALSE,
  submitted         BOOLEAN     NOT NULL DEFAULT FALSE,
  qca               BOOLEAN     NOT NULL DEFAULT FALSE,
  registrant        VARCHAR(100),
  -- 画面ごとの詳細（JSONB）
  cath_record       JSONB,      -- カテ記録（検査情報・医師・血行動態・検査値・危険因子・予後）
  cag_lvg           JSONB,      -- CAG/LVG
  pci               JSONB,      -- PCI（基本・病変×5・Device・合併症・J-PCI・出血/血栓リスク・AMI）
  pressure_ivus     JSONB,      -- Pressure Wire / IVUS
  pcps              JSONB,      -- PCPS
  conference        JSONB,      -- カンファレンス
  restudy           JSONB,      -- Restudy
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  version           BIGINT      NOT NULL DEFAULT 0,               -- 楽観ロック
  CONSTRAINT ck_cath_reports_status CHECK (status IN ('入力中', '確定'))
);
CREATE INDEX ix_cath_reports_study_date ON cath_reports (study_date DESC);
CREATE INDEX ix_cath_reports_patient    ON cath_reports (patient_ref, study_date DESC);
CREATE INDEX ix_cath_reports_status     ON cath_reports (status, verified);
CREATE INDEX ix_cath_reports_cine_no    ON cath_reports (cine_no);
CREATE INDEX ix_cath_reports_pci_no     ON cath_reports (pci_no);
-- JSONB 内の検索（例: pci @> '{"jpci": {"...": "..."}}'）用
CREATE INDEX ix_cath_reports_pci_gin    ON cath_reports USING gin (pci jsonb_path_ops);
CREATE INDEX ix_cath_reports_cr_gin     ON cath_reports USING gin (cath_record jsonb_path_ops);
COMMENT ON TABLE cath_reports IS 'カテレポート（1検査=1行。画面詳細は JSONB）';

-- 登録履歴（レポート 1 : N）
CREATE TABLE report_history (
  report_id VARCHAR(64)  NOT NULL REFERENCES cath_reports(id) ON DELETE CASCADE,
  seq       INTEGER      NOT NULL,
  at        TIMESTAMPTZ  NOT NULL,
  by_name   VARCHAR(100),
  action    VARCHAR(200),
  PRIMARY KEY (report_id, seq)
);
COMMENT ON TABLE report_history IS 'レポート登録履歴';

-- MACE（レポート 1 : N、最大5）。data が正、イベント列は集計用に保存時に展開
CREATE TABLE report_mace (
  report_id     VARCHAR(64) NOT NULL REFERENCES cath_reports(id) ON DELETE CASCADE,
  seq           INTEGER     NOT NULL,
  mace          VARCHAR(8),             -- MACE 有無区分
  pci_date      DATE,
  last_visit    DATE,
  has_death     BOOLEAN NOT NULL DEFAULT FALSE,
  has_acs       BOOLEAN NOT NULL DEFAULT FALSE,
  has_stroke    BOOLEAN NOT NULL DEFAULT FALSE,
  has_hf        BOOLEAN NOT NULL DEFAULT FALSE,
  has_bleeding  BOOLEAN NOT NULL DEFAULT FALSE,
  has_revasc    BOOLEAN NOT NULL DEFAULT FALSE,
  has_other     BOOLEAN NOT NULL DEFAULT FALSE,
  first_event_date DATE,                -- 最初のイベント日
  data          JSONB   NOT NULL,       -- 画面の全項目
  PRIMARY KEY (report_id, seq),
  CONSTRAINT ck_report_mace_seq CHECK (seq BETWEEN 0 AND 9)
);
COMMENT ON TABLE report_mace IS 'MACE（追跡調査）';

-- 画像メタ情報（レポート 1 : N）
CREATE TABLE report_images (
  report_id   VARCHAR(64)  NOT NULL REFERENCES cath_reports(id) ON DELETE CASCADE,
  seq         INTEGER      NOT NULL,
  image_id    VARCHAR(64)  NOT NULL,
  category    VARCHAR(32),
  taken_at    DATE,
  view_name   VARCHAR(64),     -- 撮影方向（API: view）
  lesion      VARCHAR(64),
  title       VARCHAR(200),
  description TEXT,
  file_name   VARCHAR(255),
  mime_type   VARCHAR(100),
  key_image   BOOLEAN NOT NULL DEFAULT FALSE,
  PRIMARY KEY (report_id, seq),
  CONSTRAINT uq_report_images_image UNIQUE (report_id, image_id)
);
COMMENT ON TABLE report_images IS '画像メタ情報';

-- 画像本体（一覧取得では読まない）
CREATE TABLE report_image_data (
  report_id  VARCHAR(64)  NOT NULL REFERENCES cath_reports(id) ON DELETE CASCADE,
  image_id   VARCHAR(64)  NOT NULL,
  mime_type  VARCHAR(100) NOT NULL,
  data       BYTEA        NOT NULL,
  size_bytes INTEGER      GENERATED ALWAYS AS (octet_length(data)) STORED,
  updated_at TIMESTAMPTZ  NOT NULL DEFAULT now(),
  PRIMARY KEY (report_id, image_id)
);
COMMENT ON TABLE report_image_data IS '画像本体（data URL を base64 デコードして保存）';

-- ---------- マスタ ----------
CREATE TABLE master_items (
  id         BIGSERIAL    PRIMARY KEY,
  kind       VARCHAR(16)  NOT NULL,     -- doctor / hospital / device
  category   VARCHAR(32),               -- device のカテゴリ（DES, BMS, DCB ...）
  name       VARCHAR(200) NOT NULL,
  sort_order INTEGER      NOT NULL DEFAULT 0,
  CONSTRAINT ck_master_items_kind CHECK (kind IN ('doctor', 'hospital', 'device'))
);
CREATE INDEX ix_master_items_kind ON master_items (kind, sort_order);
COMMENT ON TABLE master_items IS 'マスタ（術者・紹介病院・デバイス）';

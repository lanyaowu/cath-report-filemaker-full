-- =====================================================================
-- 監査ログ（V5）：項目ごとの変更履歴（保存のたびに、変わった項目の変更前・変更後を記録）
-- audit_log と同じく追加のみ。更新・削除・TRUNCATE はトリガーで禁止する。
-- path は JSON のパス（例：pci.lesions.0.target）。患者は患者の JSON、レポートはレポートの JSON の中のパス。
-- =====================================================================
CREATE TABLE audit_change (
  audit_id     BIGINT        NOT NULL REFERENCES audit_log (id),
  seq          INT           NOT NULL,
  path         VARCHAR(300)  NOT NULL,
  before_value TEXT          NOT NULL DEFAULT '',
  after_value  TEXT          NOT NULL DEFAULT '',
  PRIMARY KEY (audit_id, seq)
);
COMMENT ON TABLE audit_change IS '監査ログ：変わった項目（追加のみ）';

-- 変わった項目の数（一覧で使う。変更の記録を始める前の記録は 0）
ALTER TABLE audit_log ADD COLUMN change_count INT NOT NULL DEFAULT 0;

CREATE TRIGGER trg_audit_change_no_update BEFORE UPDATE OR DELETE ON audit_change
  FOR EACH ROW EXECUTE FUNCTION audit_log_readonly();
CREATE TRIGGER trg_audit_change_no_truncate BEFORE TRUNCATE ON audit_change
  FOR EACH STATEMENT EXECUTE FUNCTION audit_log_readonly();

-- =====================================================================
-- 監査ログ（V3）：誰が・いつ・何を（ログイン・閲覧・登録・更新・削除・確定・照合・マスタ・サンプル投入）
-- 追加のみ。更新・削除・TRUNCATE はトリガーで禁止する（保存期間を過ぎた分の削除は DBA が手順に従って行う）。
-- =====================================================================
CREATE TABLE audit_log (
  id           BIGSERIAL    PRIMARY KEY,
  at           TIMESTAMPTZ  NOT NULL DEFAULT now(),
  username     VARCHAR(64)  NOT NULL DEFAULT '',
  display_name VARCHAR(128) NOT NULL DEFAULT '',
  action       VARCHAR(32)  NOT NULL,
  target_type  VARCHAR(16)  NOT NULL DEFAULT '',
  target_id    VARCHAR(64)  NOT NULL DEFAULT '',
  detail       TEXT         NOT NULL DEFAULT '',
  ip           VARCHAR(64)  NOT NULL DEFAULT ''
);
CREATE INDEX ix_audit_log_at     ON audit_log (at DESC);
CREATE INDEX ix_audit_log_user   ON audit_log (username, at DESC);
CREATE INDEX ix_audit_log_target ON audit_log (target_type, target_id, at DESC);
COMMENT ON TABLE audit_log IS '監査ログ（追加のみ）';

CREATE FUNCTION audit_log_readonly() RETURNS trigger
  LANGUAGE plpgsql AS
$$ BEGIN RAISE EXCEPTION '監査ログは変更・削除できません'; END $$;

CREATE TRIGGER trg_audit_log_no_update BEFORE UPDATE OR DELETE ON audit_log
  FOR EACH ROW EXECUTE FUNCTION audit_log_readonly();
CREATE TRIGGER trg_audit_log_no_truncate BEFORE TRUNCATE ON audit_log
  FOR EACH STATEMENT EXECUTE FUNCTION audit_log_readonly();

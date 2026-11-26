-- =====================================================================
-- 集計・二次利用向けのビュー（V2）
-- JSONB の詳細項目から、よく使う項目を列として取り出す。
-- 画面からの入力値は文字列のため、数値は cr_num() で安全に変換する。
-- =====================================================================

-- 数値に変換できる文字列だけを numeric にする（それ以外は NULL）
CREATE FUNCTION cr_num(v TEXT) RETURNS NUMERIC
  LANGUAGE sql IMMUTABLE PARALLEL SAFE AS
$$ SELECT CASE WHEN v ~ '^\s*-?[0-9]+(\.[0-9]+)?\s*$' THEN trim(v)::numeric END $$;

-- レポート一覧（患者情報付き）
CREATE VIEW v_report_summary AS
SELECT
  r.id                                  AS report_id,
  r.study_date,
  r.status,
  r.verified,
  r.cine_no,
  r.pci_no,
  p.patient_id,
  p.name                                AS patient_name,
  p.sex,
  date_part('year', age(r.study_date, p.birth_date))::int AS age_at_study,
  r.cath_record #>> '{exam,urgency}'    AS urgency,
  r.cath_record #>> '{exam,disease}'    AS disease,
  r.cath_record #>> '{exam,approach}'   AS approach,
  r.cath_record #>> '{exam,examItems}'  AS exam_items,
  COALESCE((r.cath_record #>> '{exam,purposes,PCI}')::boolean, FALSE) AS purpose_pci,
  cr_num(r.cath_record #>> '{exam,fluoroTime}')       AS fluoro_time_min,
  cr_num(r.cath_record #>> '{exam,totalDose}')        AS total_dose_mgy,
  r.cath_record #>> '{exam,contrast,agent}'           AS contrast_agent,
  cr_num(r.cath_record #>> '{exam,contrast,volume}')  AS contrast_ml,
  r.cath_record #>> '{doctors,attending}'             AS attending,
  r.cath_record #>> '{risk,DM}'         AS risk_dm,
  r.cath_record #>> '{risk,HT}'         AS risk_ht,
  r.cath_record #>> '{risk,HL}'         AS risk_hl,
  r.cath_record #>> '{risk,smoking}'    AS risk_smoking,
  (SELECT count(*) FROM report_images i WHERE i.report_id = r.id)::int AS image_count,
  r.updated_at
FROM cath_reports r
JOIN patients p ON p.id = r.patient_ref;
COMMENT ON VIEW v_report_summary IS 'レポート一覧（患者・検査情報・危険因子の主要項目）';

-- MACE イベント（患者単位で追跡）
CREATE VIEW v_mace_events AS
SELECT
  m.report_id,
  m.seq + 1      AS mace_no,
  p.patient_id,
  p.name         AS patient_name,
  r.study_date,
  m.pci_date,
  m.last_visit,
  m.first_event_date,
  (m.last_visit - COALESCE(m.pci_date, r.study_date)) AS follow_up_days,
  m.has_death, m.has_acs, m.has_stroke, m.has_hf, m.has_bleeding, m.has_revasc, m.has_other,
  (m.has_death OR m.has_acs OR m.has_stroke OR m.has_revasc) AS has_major_event
FROM report_mace m
JOIN cath_reports r ON r.id = m.report_id
JOIN patients p     ON p.id = r.patient_ref;
COMMENT ON VIEW v_mace_events IS 'MACE 追跡（イベント有無・追跡日数）';

-- 月別件数（集計画面・統計用）
CREATE VIEW v_monthly_stats AS
SELECT
  date_trunc('month', r.study_date)::date AS month,
  count(*)                                AS reports,
  count(*) FILTER (WHERE COALESCE((r.cath_record #>> '{exam,purposes,PCI}')::boolean, FALSE)) AS pci,
  count(*) FILTER (WHERE r.cath_record #>> '{exam,urgency}' = '緊急')                         AS emergency,
  round(avg(cr_num(r.cath_record #>> '{exam,contrast,volume}')), 1)                          AS avg_contrast_ml,
  round(avg(cr_num(r.cath_record #>> '{exam,fluoroTime}')), 1)                               AS avg_fluoro_min
FROM cath_reports r
GROUP BY 1;
COMMENT ON VIEW v_monthly_stats IS '月別件数・平均造影剤量・平均透視時間';

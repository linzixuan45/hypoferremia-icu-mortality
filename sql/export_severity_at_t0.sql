-- export_severity_at_t0.sql
-- Output: data/mimic_severity_scores.parquet
-- Join t0_charttime from mimic_t0_labs; score at or before t0

-- === MIMIC-IV SOFA (example; add APACHE II / SAPS II from derived tables) ===
WITH t0 AS (
    SELECT stay_id, t0_charttime, subject_id, hadm_id
    FROM mimic_t0_labs  -- materialized from export_t0_cohort.sql
),
sofa_at_t0 AS (
    SELECT DISTINCT ON (t.stay_id)
        t.stay_id,
        s.sofa AS sofa_at_t0
    FROM t0 t
    JOIN mimiciv_derived.sofa s
        ON s.stay_id = t.stay_id
    WHERE s.starttime <= t.t0_charttime
    ORDER BY t.stay_id, s.starttime DESC
),
apache_at_admission AS (
    SELECT
        t.stay_id,
        a.apacheii AS apache_ii
    FROM t0 t
    JOIN mimiciv_derived.apacheapsvar a
        ON a.stay_id = t.stay_id
),
saps_at_admission AS (
    SELECT
        t.stay_id,
        s.sapsii AS saps_ii
    FROM t0 t
    JOIN mimiciv_derived.sapsii s
        ON s.stay_id = t.stay_id
)
SELECT
    t.stay_id,
    t.subject_id,
    t.hadm_id,
    sofa.sofa_at_t0,
    ap.apache_ii,
    sap.saps_ii
FROM t0 t
LEFT JOIN sofa_at_t0 sofa ON sofa.stay_id = t.stay_id
LEFT JOIN apache_at_admission ap ON ap.stay_id = t.stay_id
LEFT JOIN saps_at_admission sap ON sap.stay_id = t.stay_id;

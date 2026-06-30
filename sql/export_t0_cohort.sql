-- export_t0_cohort.sql
-- MIMIC-III v1.4 / MIMIC-IV v2.2 template for co-author offline export
-- Output: data/mimic_t0_labs.parquet (one row per index ICU stay)
--
-- Columns: subject_id, hadm_id, stay_id, icu_intime, t0_charttime,
--          first_iron_lab_charttime, iron_at_t0, hypoferremia_stratum

-- === MIMIC-IV example (adapt schema for MIMIC-III icustays) ===
-- Verify iron itemids for your MIMIC build (template uses common chemistry itemids).
WITH first_icu AS (
    SELECT DISTINCT ON (hadm_id)
        subject_id,
        hadm_id,
        stay_id,
        intime AS icu_intime,
        outtime AS icu_outtime
    FROM mimiciv_icu.icustays
    ORDER BY hadm_id, intime
),
iron_labs AS (
    SELECT
        fi.subject_id,
        fi.hadm_id,
        fi.stay_id,
        fi.icu_intime,
        le.charttime,
        le.valuenum AS iron
    FROM first_icu fi
    JOIN mimiciv_hosp.labevents le
        ON le.subject_id = fi.subject_id
        AND le.hadm_id = fi.hadm_id
    WHERE le.itemid IN (50998, 50809)  -- iron itemids (verify for your build)
      AND le.valuenum IS NOT NULL
),
first_iron_lab AS (
    SELECT DISTINCT ON (stay_id)
        stay_id,
        charttime AS first_iron_lab_charttime,
        iron AS first_iron
    FROM iron_labs
    ORDER BY stay_id, charttime
),
t0 AS (
    SELECT DISTINCT ON (stay_id)
        il.subject_id,
        il.hadm_id,
        il.stay_id,
        il.icu_intime,
        il.charttime AS t0_charttime,
        il.iron AS iron_at_t0
    FROM iron_labs il
    WHERE il.iron < 60
    ORDER BY stay_id, charttime
)
SELECT
    t.subject_id,
    t.hadm_id,
    t.stay_id,
    t.icu_intime,
    t.t0_charttime,
    f.first_iron_lab_charttime,
    t.iron_at_t0,
    CASE
        WHEN t.t0_charttime <= f.first_iron_lab_charttime + INTERVAL '24 hours'
             AND f.first_iron < 60
        THEN 'admission'
        ELSE 'acquired'
    END AS hypoferremia_stratum,
    EXTRACT(EPOCH FROM (t.t0_charttime - t.icu_intime)) / 3600.0 AS hours_icu_to_t0
FROM t0 t
JOIN first_iron_lab f ON f.stay_id = t.stay_id
WHERE EXTRACT(EPOCH FROM (t.icu_outtime - t.icu_intime)) / 3600.0 >= 48;

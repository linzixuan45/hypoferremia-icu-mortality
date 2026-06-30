# MIMIC Excel Reproduction Guide

**Audience:** credentialed PhysioNet users who want to reproduce the full analysis pipeline.

This repository does **not** redistribute patient-level data or provide raw-table ETL. You must build `data/mimic_dataset.xlsx` locally from authorized MIMIC access.

**Related docs:** [preprocessing_excel.md](preprocessing_excel.md) · [required_excel_columns.csv](../config/required_excel_columns.csv) · [data/README.md](../data/README.md)

---

## Prerequisites

1. Completed PhysioNet training and signed data-use agreement for [MIMIC-III](https://physionet.org/content/mimiciii/) and/or [MIMIC-IV](https://physionet.org/content/mimiciv/).
2. Local SQL access (PostgreSQL for MIMIC-III, BigQuery or PostgreSQL for MIMIC-IV) or an equivalent authorized export workflow.
3. Python 3.10+ and `pip install -r requirements.txt`.

Use the community [MIMIC Code Repository](https://github.com/MIT-LCP/mimic-code) for SQL patterns (labs, vitals, ICU stays, demographics).

---

## Target artifact

```
data/mimic_dataset.xlsx
├── sheet: mimic3_low_fe   (MIMIC-III external validation, n ≈ 1,046)
└── sheet: mimic4_low_fe   (MIMIC-IV development, n ≈ 1,568 after filters)
```

Validate before running the pipeline:

```bash
python scripts/validate_excel_input.py
python scripts/validate_excel_input.py --report
```

Column checklist: [config/required_excel_columns.csv](../config/required_excel_columns.csv).

---

## Step 1 — Define the hypoferremia cohort

Apply these inclusion rules (FE1 specification; see [FE1_spec_en.md](FE1_spec_en.md)):

| Rule | Definition |
|------|------------|
| Age | 18–100 years (`admission_age`) |
| ICU stay | ≥ 48 hours (`los_icu >= 2` days) |
| Hypoferremia | At least one serum iron < 60 µg/dL during ICU stay |
| First ICU stay | One row per first ICU stay per admission where identifiable |

Export separate cohorts for MIMIC-III (2001–2012) and MIMIC-IV (2008–2020).

---

## Step 2 — Build t₀ proxy columns (Excel path)

Without charttime-level serum iron, the pipeline uses an Excel proxy:

| Column | Purpose |
|--------|---------|
| `iron_1st` | First measured serum iron (µg/dL) |
| `iron_min` | Minimum serum iron during stay (µg/dL) |

Strata (computed by `prepare_t0_labs_parquet.py`):

- **Admission:** `iron_1st < 60`
- **Acquired:** `iron_1st >= 60` (or missing) and `iron_min < 60`

---

## Step 3 — Aggregate features to t₀ (conservative mapping)

For the primary analysis, prefer `_1st` and `_min` suffixes over full-stay `_max` / `_mean` where both exist.

**Required 8-feature columns:**

`platelet_mean`, `wbc_min`, `bun_min`, `pco2_max`, `creatinine_min`, `is_noninvasive_ventilator`, `spo2_min`, `platelet_1st`

**20-feature LASSO panel:** see [config/low_fe_lasso_feature.csv](../config/low_fe_lasso_feature.csv). Replace `los_icu` with `los_icu_to_t0` in the pipeline (derived from proxy timing).

**Outcome columns:**

- `hospital_expire_flag`
- `hosp_survival_days` or `icu_survival_days` (for deriving `outcome_28d_t0`)

**Optional severity (Table 5):**

- `sofa_score` (Excel proxy). Full APACHE II / SAPS II require SQL export — see [sql/README.md](../sql/README.md).

---

## Step 4 — Run the pipeline

```bash
python scripts/validate_excel_input.py
python scripts/run_pipeline.py
```

Or step by step (see [preprocessing_excel.md](preprocessing_excel.md)).

After completion, compare your run to the locked reference:

```bash
python scripts/verify_reproduction.py
```

---

## Optional upgrade — charttime-level t₀ (SQL)

When MIMIC SQL access is available:

1. Run [sql/export_t0_cohort.sql](../sql/export_t0_cohort.sql) → `data/mimic_t0_labs.parquet`
2. Optionally run [sql/export_severity_at_t0.sql](../sql/export_severity_at_t0.sql) → `data/mimic_severity_scores.parquet`
3. Validate: `python scripts/validate_parquet_export.py`
4. Re-run from `python scripts/build_t0_cohort.py`

The manifest records `t0_source: parquet` when this path is used.

---

## Limitations (disclose in Methods)

- Excel exports cannot truly truncate min/max/mean aggregates to t₀ without charttime.
- This guide describes the **expected input shape**, not the proprietary export scripts used during original analysis.
- Chinese geographic validation (F3/NH) requires separate local files under `data/external/` — see [DATA_AVAILABILITY.md](../DATA_AVAILABILITY.md).

---

## Troubleshooting

| Symptom | Action |
|---------|--------|
| `file not found: mimic_dataset.xlsx` | Place workbook at `data/mimic_dataset.xlsx`; see [data/README.md](../data/README.md) |
| Missing core columns | Compare sheets to [required_excel_columns.csv](../config/required_excel_columns.csv) |
| `verify_reproduction.py` fails | Check cohort n and AUROC tolerance (±0.005); ensure same FE1 filters and random seed (42) |
| Missing model weights | Repository ships `model_weights/8_features_model.pkl`; re-export with `python scripts/export_github_weights.py` after pipeline |

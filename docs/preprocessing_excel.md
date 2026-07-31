# Excel-Based Preprocessing and Reproduction Path

> **Round 2 status:** this document also describes legacy proxy-t₀ scripts retained for audit
> history. The current manuscript uses retrospective whole-ICU-stay summaries, an outcome measured
> from hospital admission, and the corrected MIMIC-III cohort (n=799). See
> [`FE1_spec_en.md`](FE1_spec_en.md) and [`reference/r2/`](../reference/r2/).

**Scope:** credentialed users who hold a local `data/mimic_dataset.xlsx`. This repository does **not** redistribute patient-level data and does **not** include MIMIC raw-table ETL.

**Start here:** [mimic_excel_reproduction_guide.md](mimic_excel_reproduction_guide.md) · column checklist: [required_excel_columns.csv](../config/required_excel_columns.csv)

For public reproduction, use the Excel input plus the scripts below.

---

## Required input

Place your authorized export at:

```
data/mimic_dataset.xlsx
```

### Required sheets

| Sheet | Purpose |
|-------|---------|
| `mimic3_low_fe` | MIMIC-III external validation source |
| `mimic4_low_fe` | MIMIC-IV development / internal test source |
| `Feature_names` | Optional; used by exploratory `dataset.py` / LASSO flows |

### Minimum columns

**Identifiers**

| Column | MIMIC-III | MIMIC-IV |
|--------|-----------|----------|
| `subject_id` | required | required |
| `icustay_id` | required (preferred join key) | — |

**Outcome and follow-up**

| Column | Purpose |
|--------|---------|
| `hospital_expire_flag` | In-hospital death indicator |
| `hosp_survival_days` or `icu_survival_days` | Used to derive `outcome_28d_t0` from t₀ |

**Cohort filters**

| Column | Purpose |
|--------|---------|
| `admission_age` | Clipped to 18–100 years |
| `los_icu` | Primary analysis: ≥ 2 days (48 h ICU stay) |

**t₀ proxy (Excel path)**

| Column | Purpose |
|--------|---------|
| `iron_1st` | Admission-stratum proxy (< 60 µg/dL) |
| `iron_min` | Acquired-hypoferremia proxy |

**8-feature model panel** — see [data_dictionary.md](data_dictionary.md):

`platelet_mean`, `wbc_min`, `bun_min`, `pco2_max`, `creatinine_min`, `is_noninvasive_ventilator`, `spo2_min`, `platelet_1st`

**20-feature / severity benchmark**

| Column | Purpose |
|--------|---------|
| `sofa_score` | Table 5 SOFA comparator (Excel proxy) |
| APACHE II / SAPS II | **Not in Excel**; require SQL export via [sql/README.md](../sql/README.md) |

---

## Pipeline (Excel path)

```bash
python scripts/validate_excel_input.py
python scripts/prepare_t0_labs_parquet.py
python scripts/build_t0_cohort.py
python scripts/train_models.py
python scripts/supplementary_analysis.py
python scripts/benchmark_severity_scores.py
python scripts/build_table1_baseline.py
python scripts/export_github_weights.py
```

Or:

```bash
python scripts/run_pipeline.py
```

---

## Cohort split (FE1)

| Set | Role |
|-----|------|
| MIMIC-IV 80% | Development train |
| MIMIC-IV 20% | Internal test |
| MIMIC-III corrected | Same-institution temporal evaluation (799) |

---

## Script roles

| Script | Role |
|--------|------|
| `validate_excel_input.py` | Pre-flight column/sheet checks |
| `prepare_t0_labs_parquet.py` | Synthetic t₀ timing from `iron_*` + `los_icu` |
| `build_t0_cohort.py` | Filters, `outcome_28d_t0`, train/test/external ID lists |
| `train_models.py` | 20/8-feature soft-voting ensemble |

---

## Limitations (Methods disclosure)

- No charttime-level serum iron in the Excel export; t₀ uses **excel_derived_interim** proxy per [FE1_spec.md](FE1_spec.md).
- Full-stay min/max/mean aggregates cannot be truly truncated to t₀ without SQL; primary 20-feature set uses conservative `_1st`/`_min` mapping.

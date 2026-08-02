# Excel-Based Round 2 Preprocessing

This path is for credentialed investigators who hold an authorized `data/mimic_dataset.xlsx`. The workbook is not public.

## Required semantics

- Sheets: `mimic4_low_fe` and `mimic3_low_fe`.
- ICU eligibility: `los_icu >= 2` days.
- Documented hypoferremia: `iron_1st < 60` or `iron_min < 60` µg/dL after the LOS filter.
- Outcome: `hospital_expire_flag == 1` and survival time from hospital admission ≤28 days.
- Predictor suffixes: `_1st` is first ICU value; `_min`, `_max`, `_mean` summarize the full ICU stay.
- Historical `los_icu_to_t0`: synthetic R1 proxy; retained only in the locked benchmark and removed in a sensitivity analysis.

## Leakage controls

The MIMIC-IV split is patient-separated. KNN imputation (`n_neighbors=5`) is fitted only on the training set. StandardScaler is fitted only to the imputed training matrix. Both objects are applied unchanged to internal and non-training cohorts. Multiple-imputation sensitivity preprocessing is refitted inside each training fold.

## Commands

```bash
python scripts/validate_excel_input.py --report --strict
python scripts/run_r2_analysis.py
python scripts/verify_reproduction.py
```

Outputs under `result/` are local and gitignored. Do not commit cohort IDs, row-level predictions, or fitted objects.

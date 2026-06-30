# SQL extraction (optional)

When credentialed MIMIC SQL access is available, run these scripts offline and place outputs under `data/`.

| Script | Output |
|--------|--------|
| `export_t0_cohort.sql` | `data/mimic_t0_labs.parquet` |
| `export_severity_at_t0.sql` | `data/mimic_severity_scores.parquet` |

Expected t₀ columns: `stay_id`, `t0_charttime`, `hypoferremia_stratum`, `hours_icu_to_t0`.

After export, validate and re-run the pipeline from `build_t0_cohort.py`:

```bash
python scripts/validate_parquet_export.py
python scripts/build_t0_cohort.py
python scripts/train_models.py
```

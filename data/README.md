# Local data (not redistributed)

Place credentialed MIMIC feature tables here. **How to build the Excel workbook:** [docs/mimic_excel_reproduction_guide.md](../docs/mimic_excel_reproduction_guide.md)

| File | Description |
|------|-------------|
| `mimic_dataset.xlsx` | Sheets `mimic3_low_fe`, `mimic4_low_fe` — see [docs/preprocessing_excel.md](../docs/preprocessing_excel.md) and [config/required_excel_columns.csv](../config/required_excel_columns.csv) |

Optional (generated or from SQL):

| File | Description |
|------|-------------|
| `mimic_t0_labs.parquet` | t₀ timing (`prepare_t0_labs_parquet.py` or `sql/export_t0_cohort.sql`) |
| `mimic_severity_scores.parquet` | SOFA / APACHE / SAPS at t₀ |

Chinese external validation (optional):

| Priority | Path | Description |
|----------|------|-------------|
| Primary | `external/mimic_validation_cohorts.xlsx` | Sheets `low_fe_F3`, `low_fe_NH` |
| Alternate | `external/mimic论文数据测试集0901.xlsx` | Accepted by `external_cohort_data.py` |
| Optional | `external/f3_rdw_correction.xls` | F3 RDW correction |
| Optional | `external/nh_relabel_candidates.csv` | NH relabel candidates |

Validate before running:

```bash
python scripts/validate_excel_input.py
```

# Data Availability

## MIMIC-III and MIMIC-IV

MIMIC data are available from PhysioNet to credentialed users:

- [MIMIC-III](https://physionet.org/content/mimiciii/)
- [MIMIC-IV](https://physionet.org/content/mimiciv/)

Access requires completion of required training and a data-use agreement. This repository does **not** include MIMIC raw tables, patient identifiers, derived patient-level feature exports, row-level outcomes, or row-level predicted probabilities.

## Local feature tables (not redistributed)

Full reproduction requires locally prepared files placed by the user. Start with [docs/mimic_excel_reproduction_guide.md](docs/mimic_excel_reproduction_guide.md) and [config/required_excel_columns.csv](config/required_excel_columns.csv).

| File | Purpose |
|------|---------|
| `data/mimic_dataset.xlsx` | MIMIC-III / MIMIC-IV pre-aggregated feature tables (user-prepared; entry point for the public pipeline) |
| `data/mimic_t0_labs.parquet` | Optional charttime-level SQL export; the legacy Excel-derived file is synthetic and is retained only for locked-result reproduction |
| `data/mimic_severity_scores.parquet` | SOFA proxy from Excel or full SOFA/APACHE/SAPS from SQL (optional) |

Validate your Excel before running:

```bash
python scripts/validate_excel_input.py
python scripts/run_pipeline.py
python scripts/verify_reproduction.py
```

## Chinese external validation (not redistributed)

Geographic validation used institution-held cohorts. If reproducing F3/NH evaluation locally, place authorized files under `data/external/`:

| Priority | File | Purpose |
|----------|------|---------|
| Primary | `mimic_validation_cohorts.xlsx` | Sheets `low_fe_F3`, `low_fe_NH` |
| Alternate | `mimic论文数据测试集0901.xlsx` | Accepted by `external_cohort_data.py` if primary missing |
| Optional | `f3_rdw_correction.xls` | F3 RDW correction input |
| Optional | `nh_relabel_candidates.csv` | NH relabel candidates |

These files are not included in the public repository.

## What we do publish

- HTTPS research demonstration calculator: https://fe.mixaihub.top (not for clinical use)
- Code: https://github.com/linzixuan45/hypoferremia-icu-mortality
- SQL scripts, model card, methods documentation
- Released 8-feature model weights for research inference (`model_weights/8_features_model.pkl`)
- Locked reference metrics (`reference/manifest.json`, `reference/table2_3_performance.csv`)
- Corrected R2 aggregate analyses and Figure 2 source files (`reference/r2/`)
- Non-patient configuration such as the LASSO feature name list (`config/low_fe_lasso_feature.csv`)

## Manuscript text (optional Data Availability paragraph)

```text
MIMIC-III and MIMIC-IV data are available from PhysioNet to credentialed researchers under the applicable data-use agreement. The Chinese evaluation cohorts are institution-held and are not publicly redistributed. The public repository provides the complete analysis code, non-patient aggregate result tables, Figure 2 plotting source, model card, and released non-patient-specific model bundle. Patient-level feature tables, outcomes, and prediction probabilities are not redistributed. A versioned archive will be deposited at Zenodo.
```

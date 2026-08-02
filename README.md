# Hypoferremia ICU Mortality Risk Stratification

**Research use only. Not for clinical decision-making.**

Companion code for:

> *Mortality Risk Stratification Among Critically Ill Patients with Documented Hypoferremia: Multi-Cohort Development and Retrospective Evaluation*

This repository provides the active Round 2 analysis workflow from authorized, user-prepared modelling tables. It includes cohort construction, patient-separated splitting, training-set-only preprocessing, candidate-model fitting, locked soft-voting and post hoc reduced-model evaluation, calibration analyses, figure generation, and reviewer-requested supplementary audits.

It does **not** redistribute raw or derived patient-level data, cohort-ID lists, individual outcomes or probabilities, or fitted preprocessing/model objects. The previously tracked 8-feature pickle was removed because its fitted KNN imputer retained a training-feature matrix.

- Repository: https://github.com/linzixuan45/hypoferremia-icu-mortality
- Research demonstration: https://fe.mixaihub.top (not for clinical use)
- Planned reproducibility release: `v1.2.0`
- Zenodo DOI: pending release; do not cite a DOI until Zenodo assigns it

## Scientific scope

| Item | Round 2 definition |
|---|---|
| Population | ICU admissions with documented serum iron <60 µg/dL and ICU length of stay ≥48 h |
| Outcome | Death in hospital within 28 days of hospital admission |
| Predictor window | `_1st`: first recorded ICU-stay value; `_min`, `_max`, `_mean`: full ICU-stay summaries |
| Benchmark | Locked 18-predictor soft-voting model retained for R1 protocol continuity |
| Reduced model | Post hoc 8-feature derivative; not prespecified and not proven superior |
| MIMIC-III role | Same-institution cross-database temporal sensitivity cohort, not independent external validation |
| Chinese cohorts | Small exploratory geographic evaluations of the post hoc reduced model |

The retained `los_icu_to_t0` variable is a synthetic R1 proxy rather than an observed timestamp. The model is therefore described as retrospective whole-stay risk stratification, not real-time or admission-time prediction.

## What is and is not provided

| Provided | Not provided |
|---|---|
| Active Python analysis and audit scripts | MIMIC tables or prepared patient-level workbooks |
| Input schema and data dictionary | Chinese validation cohort files |
| Optional SQL examples | A complete raw-database-to-modelling-table ETL |
| Aggregate Round 2 reference outputs | Cohort-ID lists or row-level predictions |
| Research-interface source | Public fitted model, imputer, or scaler objects |
| Tests enforcing release and privacy boundaries | Clinical-use approval or calibrated bedside risk estimates |

## Data access and local inputs

MIMIC-III and MIMIC-IV are available to credentialed users through PhysioNet under their respective data-use requirements. Place an authorized prepared workbook at:

```text
data/mimic_dataset.xlsx
```

The required sheets and columns are described in [docs/R2_INPUT_SCHEMA.md](docs/R2_INPUT_SCHEMA.md), [docs/preprocessing_excel.md](docs/preprocessing_excel.md), and [config/required_excel_columns.csv](config/required_excel_columns.csv). Institution-held F3/NH data remain local and are described in [DATA_AVAILABILITY.md](DATA_AVAILABILITY.md).

## Reproduce the Round 2 workflow

Python 3.12 is recommended. Install the audited environment where practical:

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements-frozen.txt
```

Validate the authorized workbook and run the core plus reviewer-requested analyses:

```bash
python scripts/validate_excel_input.py --report --strict
python scripts/run_r2_analysis.py
python scripts/verify_reproduction.py
pytest -q
```

`scripts/run_r2_analysis.py` fails if a required core step fails. It first reconstructs local cohort IDs, fitted preprocessing objects, models, predictions, tables, and figures under the gitignored `result/` directory, then executes the supplementary Round 2 audit workflow. Missing optional Chinese cohorts are reported explicitly and limit the run to the MIMIC analyses.

## Repository map

| Path | Purpose |
|---|---|
| `scripts/run_r2_analysis.py` | End-to-end prepared-table Round 2 orchestrator |
| `scripts/run_pipeline.py` | Core cohort, model, evaluation, and figure workflow |
| `scripts/r2_supplementary_analyses.py` | Reviewer-requested R2 analyses |
| `scripts/validate_excel_input.py` | Input validation |
| `scripts/train_models.py` | Locked and post hoc model training/evaluation |
| `scripts/plot_figure4_benchmark.py` | Twelve-model comparison and temporal sensitivity |
| `reference/r2/` | Non-patient aggregate Round 2 reference outputs |
| `docs/R2_REPRODUCTION_SCOPE.md` | Reproduction claim and boundaries |
| `MODEL_CARD.md` | Intended use, model status, and limitations |
| `tests/` | Data-free integrity, parameter, and privacy tests |

Historical patch scripts are isolated under `scripts/legacy_R1/`. A small number
of active compatibility filenames still contain the historical token
`20_features`; in the Round 2 workflow these files refer to the locked
18-predictor benchmark and do not denote a current 20-predictor model.

## Locked aggregate results

| Model and cohort | n (events) | AUROC (95% CI) |
|---|---:|---:|
| Locked benchmark, MIMIC-IV internal test | 269 (40) | 0.840 (0.767–0.913) |
| Locked benchmark, corrected MIMIC-III temporal sensitivity | 799 (140) | 0.705 (0.657–0.751) |
| Post hoc reduced model, MIMIC-IV internal test | 269 (40) | 0.796 (0.716–0.871) |
| Post hoc reduced model, corrected MIMIC-III temporal sensitivity | 799 (140) | 0.715 (0.669–0.761) |
| Post hoc reduced model, Third Xiangya exploratory cohort | 101 (26) | 0.810 (0.703–0.901) |
| Post hoc reduced model, First Affiliated Hospital of University of South China (Nanhua cohort, NH), exploratory | 98 (37) | 0.898 (0.827–0.956) |

See [reference/r2/README.md](reference/r2/README.md) for calibration, missing-data, serum-iron, and sensitivity results.

## Research demonstration

The hosted interface illustrates input/output behaviour and XGBoost-component SHAP explanations. It is not a medical device and is not intended for diagnosis, triage, treatment selection, or other clinical decisions. Local interface and inference source are retained for audit, but a fitted bundle is deliberately not published. Authorized investigators may reconstruct it locally by running the workflow.

## Citation and archive

Use [CITATION.cff](CITATION.cff) or [CITATION.bib](CITATION.bib). After the reviewed branch is merged, create GitHub release `v1.2.0`, allow Zenodo to archive that exact release, and replace all DOI placeholders only with the assigned concept and version DOIs.

## License

Code is released under the [MIT License](LICENSE). Data retain their original access restrictions. No clinical use is authorized.

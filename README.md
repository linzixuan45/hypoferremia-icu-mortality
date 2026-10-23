# Hypoferremia ICU Mortality Risk Stratification

**Research use only. Not for clinical decision-making.**

Companion code for:

> *Retrospective mortality risk stratification in critically ill patients with documented hypoferremia*

**R3 reporting-correction review candidate; versioned release pending.** This tree is based on the published v1.2.2 computation archive. It corrects documentation, citation metadata and AUROC confidence-interval reporting using the unchanged canonical interval functions. Primary fitted models, predictions and cohort definitions are unchanged. An inherited manuscript discrepancy in the existing NIV-exclusion sensitivity was resolved by a bounded verification refit using the unchanged archived procedure and locked split. The review branch is `r3-reporting-corrections-20261023`; maintainer review, a new versioned release and a new immutable archive DOI remain pending.

This repository provides the active Round 2 analysis workflow from authorized, user-prepared modelling tables. It includes cohort construction, patient-separated splitting, training-set-only preprocessing, candidate-model fitting, locked soft-voting and post hoc reduced-model evaluation, calibration analyses, figure generation, and reviewer-requested supplementary audits.

It does **not** redistribute raw or derived patient-level data, cohort-ID lists, individual outcomes or probabilities, or fitted preprocessing/model objects. The previously tracked 8-feature pickle was removed because its fitted KNN imputer retained a training-feature matrix.

- Repository: https://github.com/linzixuan45/hypoferremia-icu-mortality
- Research demonstration: https://fe.mixaihub.top (not for clinical use)
- Published computation archive: `v1.2.2`, DOI [10.5281/zenodo.21772246](https://doi.org/10.5281/zenodo.21772246), archived source tree `b9beaac`
- Historical reviewed release: `v1.2.1`, DOI [10.5281/zenodo.21768779](https://doi.org/10.5281/zenodo.21768779)
- Zenodo all-versions concept DOI: [10.5281/zenodo.21761212](https://doi.org/10.5281/zenodo.21761212)
- Current reporting corrections: branch-review candidate, not a new versioned release. Preserve the existing v1.2.2 tag and DOI; cite a new immutable patch archive only after its actual release and deposition are verified.
- Source archive SHA-256: `ff159c6722becf34c33180adf830e74392c1383db02d7345ba366e5be47734b5` (local archived copy verified; no fresh Zenodo download claimed).

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

The required sheets and columns are described in [docs/R2_INPUT_SCHEMA.md](docs/R2_INPUT_SCHEMA.md), [docs/preprocessing_excel.md](docs/preprocessing_excel.md), and [config/required_excel_columns.csv](config/required_excel_columns.csv). Institution-held F3/USC-FAH data remain local and are described in [DATA_AVAILABILITY.md](DATA_AVAILABILITY.md).

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
| `docs/R3_REPORTING_CORRECTION.md` | Local correction scope, evidence and publication steps |
| `scripts/plot_figure7b_auroc.py` | Aggregate-only Figure 7B panel source with neutral CI axis label |
| `tests/` | Data-free integrity, parameter, and privacy tests |

Historical patch scripts are isolated under `scripts/legacy_R1/`. A small number
of active compatibility filenames still contain the historical token
`20_features`; in the Round 2 workflow these files refer to the locked
18-predictor benchmark and do not denote a current 20-predictor model.

## Locked aggregate results

| Model and cohort | n (events) | AUROC (95% CI) |
|---|---:|---:|
| Locked benchmark, MIMIC-IV internal test | 269 (40) | 0.840 (0.767–0.913) |
| Locked benchmark, corrected MIMIC-III temporal sensitivity | 799 (140) | 0.705 (0.659–0.752) |
| Post hoc reduced model, MIMIC-IV internal test | 269 (40) | 0.796 (0.718–0.874) |
| Post hoc reduced model, corrected MIMIC-III temporal sensitivity | 799 (140) | 0.715 (0.669–0.763) |
| Post hoc reduced model, Third Xiangya exploratory cohort | 101 (26) | 0.810 (0.699–0.900) |
| Post hoc reduced model, The First Affiliated Hospital of University of South China (USC-FAH), exploratory | 98 (37) | 0.898 (0.826–0.954) |

See [reference/r2/README.md](reference/r2/README.md) for calibration, missing-data, serum-iron, and sensitivity results.

The internal reduced-model interval above is the R3 DeLong reporting correction (unrounded limits 0.7183612417056014–0.8742151775083723), recomputed from the retained original internal-test probabilities. Temporal and exploratory intervals have been regenerated using the unchanged canonical `scripts/metric_intervals.py`: class-stratified percentile bootstrap, 2,000 resamples, random seed 42. MIMIC-III predictions were recovered by inference with the original fitted bundles in the audited scikit-learn 1.8.0 / XGBoost 3.2.0 environment, in the original prepared-workbook order. Chinese estimates use the retained original prediction order. Primary AUROC point estimates and Brier scores are unchanged. The reported intervals now follow one reproducible policy; the different older finite-bootstrap limits are retained only as historical provenance. See [the correction audit](docs/R3_CORRECTION_AUDIT.json).

The NIV-exclusion verification reproduced all four pre-existing canonical reference rows within 1e-10. Manuscript S11 reporting is synchronized to that existing output: internal 17-predictor benchmark AUROC 0.814 and internal 7-feature derivative 0.785, rather than 0.816 and 0.783; temporal AUROCs remain 0.727 and 0.751. The corresponding Brier and calibration entries follow the same canonical rows. This is a check of the existing sensitivity, not a new modelling strategy or a primary-model retraining. Aggregate provenance is in `docs/R3_NIV_SENSITIVITY_VERIFICATION.json`.

## Research demonstration

The hosted interface illustrates input/output behaviour and XGBoost-component SHAP explanations. It is not a medical device and is not intended for diagnosis, triage, treatment selection, or other clinical decisions. On 3 August 2026, the production deployment was opened and executed with the default record: it returned a 28-day mortality probability of 22.4%, displayed the three manuscript-aligned case-level SHAP headings, and showed the research-only warning. This records the historical verified deployment, not a new live check of this local R3 candidate. Local interface and inference source are retained for audit, but a fitted bundle is deliberately not published. Authorized investigators may reconstruct it locally by running the workflow.

## Citation and archive

Use [CITATION.cff](CITATION.cff) or [CITATION.bib](CITATION.bib). The version-specific DOI 10.5281/zenodo.21772246 identifies the prior v1.2.2 computation archive; it does not identify this corrected review tree. A new patch release and its assigned version DOI are required before claiming that the R3 reporting corrections are archived as that release. No replacement DOI or release version has been invented. Original embedded metadata are retained in `provenance/v1.2.2_embedded_metadata/` to distinguish the published record from its stale in-tree release wording.

This integration starts from current-main commit `12f0267414ae35ef775711db699da643307807ea`, preserving its v1.2.2 metadata cleanup and historical Figure 8 deployment verification. The accurate v1.2.2 release metadata from that base are preserved in `provenance/v1.2.2_release_metadata/`. See `docs/R3_CURRENT_MAIN_INTEGRATION.json` for the integration scope and [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md) for the author/maintainer review and archive steps. Pushing the review branch does not itself create a release or a new DOI. The manuscript files are outside this code update and remain unchanged at this step.

## License

Code is released under the [MIT License](LICENSE). Data retain their original access restrictions. No clinical use is authorized.

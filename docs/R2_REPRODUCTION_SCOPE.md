# Round 2 Reproducibility Scope

| Component | Public input | Public code | Output | Status |
|---|---|---|---|---|
| Release integrity and privacy checks | none | `tests/` | test report | fully executable without controlled data |
| Core R2 analysis | authorized prepared workbook | `scripts/run_pipeline.py` | local cohort IDs, fitted objects, predictions, tables, figures | executable by credentialed investigators |
| Reviewer-requested R2 analyses | core local outputs plus authorized workbook | `scripts/r2_supplementary_analyses.py` | local private intermediates and aggregate tables | executable after the core workflow |
| End-to-end prepared-table orchestration | authorized prepared workbook | `scripts/run_r2_analysis.py` | required core and R2 outputs | fails on required missing steps or outputs |
| Aggregate-value audit | none | tests and manifests | `reference/r2/` | auditable without patient data |
| Raw database to protected workbook | controlled source databases | optional SQL examples only | local prepared workbook | outside the claimed public workflow |
| Figure 8 research interface | locally reconstructed fitted bundle | interface source | local or hosted research demonstration | source is auditable; no public fitted bundle |

## Required local input

The active workflow expects `data/mimic_dataset.xlsx`, constructed and governed by a credentialed investigator. The public repository does not redistribute this workbook or claim complete reconstruction of it from raw databases.

## Privacy boundary

Do not commit patient identifiers, row-level predictors, outcomes, individual probabilities, cross-validation assignments, cohort-ID lists, fitted nearest-neighbour imputers, scalers, or trained model objects. The public reference directory contains aggregate values only.

## Scientific boundary

The endpoint is death in hospital within 28 days of hospital admission. Full-stay `_min`, `_max`, and `_mean` summaries are not admission-time predictors. `los_icu_to_t0` is a synthetic legacy variable retained only for R1 protocol continuity and is evaluated in an exclusion sensitivity analysis.

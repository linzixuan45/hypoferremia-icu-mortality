# Round 2 Methods and Analysis Specification

**Status:** current audited Round 2 specification. The former proxy-t₀ specification and MIMIC-III n=1,046 results are retained only as version history and do not support the current manuscript conclusions.

## Analysis task

The study performs retrospective, whole-ICU-stay mortality-risk stratification among patients with ICU length of stay ≥48 hours and at least one serum iron measurement <60 µg/dL. It is not an admission-time, real-time, or causal prediction study.

## Outcome and predictor windows

- Outcome: in-hospital death within 28 days of hospital admission.
- `_1st`: first recorded value during the ICU stay.
- `_min`, `_max`, `_mean`: minimum, maximum, and mean across the full ICU stay.
- `los_icu_to_t0`: synthetic legacy proxy retained for compatibility with the locked model; not an observed timestamp.
- Reliable serum-iron chart times were not retained, so no observed prediction time t₀ is claimed.

## Cohorts

| Cohort | Current role | n | Events |
|---|---|---:|---:|
| MIMIC-IV after ICU LOS ≥48 h | Screening set | 1,568 | — |
| MIMIC-IV meeting fixed iron definition | Statistical/sensitivity set | 1,487 | 215 |
| MIMIC-IV complete locked matrix | Model development/internal test | 1,344 | 200 |
| MIMIC-IV training | Development (80%) | 1,075 | 160 |
| MIMIC-IV internal test | Internal evaluation (20%) | 269 | 40 |
| MIMIC-III | Same-institution temporal evaluation | 799 | 140 |
| F3 | Exploratory geographic evaluation of 8-feature model | 101 | 26 |
| NH | Exploratory geographic evaluation of 8-feature model | 98 | 37 |

## Models and additional analyses

- The locked 18-predictor soft-voting model is retained as the protocol-continuity benchmark; the data do not establish superiority over logistic regression.
- The 8-feature model is a post hoc development-data derivative and does not replace the benchmark.
- Five-imputation, five-fold out-of-fold sensitivity analysis includes all 1,487 eligible MIMIC-IV admissions.
- The first-serum-iron explanatory model treats race as unordered categorical, uses numeric-median/categorical-mode imputation, and includes a complete-case sensitivity analysis.
- The restricted cubic spline uses four knots at percentiles 5, 35, 65, and 95 (9, 20, 33, and 55 µg/dL).
- Incremental serum-iron prediction fits all preprocessing and unweighted logistic regression within each training fold.

## Reproducibility boundary

The public repository provides analysis code beginning from authorized prepared modeling tables, locked model/preprocessing objects, and aggregate outputs. It does not redistribute patient-level records, labels, or probabilities, and it is not represented as a complete raw-MIMIC-to-modeling-table ETL pipeline.

Current aggregate evidence is under [`reference/r2/`](../reference/r2/). The older [`reference/manifest.json`](../reference/manifest.json) is an R1 historical manifest superseded for Round 2.

# v1.1.0 — Scientific Reports second-revision archive

This release is the DOI-ready code and aggregate-results archive for the second manuscript revision.

## Added

- `scripts/r2_supplementary_analyses.py`
  - corrected MIMIC-IV patient flow;
  - included-versus-excluded comparison;
  - five-imputation, five-fold out-of-fold sensitivity analysis;
  - standard calibration-in-the-large, calibration slope, and Brier score;
  - MIMIC-III re-evaluation after the stated ICU LOS ≥48 h criterion;
  - NIV-exclusion sensitivity;
  - adjusted within-cohort serum-iron analysis and incremental-value analysis;
  - Figure 2 plotting source.
- `reference/r2/`: non-patient aggregate R2 tables and Figure 2 source files.
- `.zenodo.json` and `CITATION.cff`.

## Corrected reporting

- The MIMIC-IV LOS-filtered screening set contains 1,568 records, of which 1,487 satisfy the fixed serum iron <60 µg/dL definition.
- The locked complete-case model matrix contains 1,344 patients; 143 eligible patients were excluded for predictor missingness.
- The original MIMIC-III n=1,046 analysis did not enforce ICU LOS ≥48 h. The corrected eligibility set contains 799 patients and 140 timed outcome events.
- The workbook's `_min`, `_max`, and `_mean` variables summarize the full ICU stay.
- The legacy Excel-derived t₀ is synthetic and is retained only for locked-result audit; it is not an observed timestamp.

## Data protection

This release does not contain MIMIC or Chinese patient-level feature tables, identifiers, cohort ID lists, row-level outcomes, or row-level prediction probabilities. Reproduction requires separately authorized access to the underlying databases.

## Intended use

Research audit only. The model is not for clinical decision-making.

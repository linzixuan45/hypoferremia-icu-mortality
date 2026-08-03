# Aggregate Reference Outputs

This directory contains non-patient aggregate values used to audit the Round 2 manuscript and local reproductions.

- `manifest.json`: current cohort and headline metric manifest.
- `table2_3_performance.csv`: locked benchmark and post hoc reduced-model performance.
- `r2/`: flow, calibration, missing-data, serum-iron, NIV-exclusion, observation-window, patient-unit, and synthetic-duration-proxy aggregate outputs.
- `r2/figure8_reviewed_interface.png`: reviewed Figure 8 interface rendering for the synthetic/default demonstration record; SHA-256 and expected 22.4% output are locked in `manifest.json`.

No row-level predictors, outcomes, probabilities, cohort identifiers, or fitted objects are included.

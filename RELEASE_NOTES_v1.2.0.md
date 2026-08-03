# Release v1.2.0 — Round 2 Reproducibility Alignment

- Aligns the active endpoint to 28-day in-hospital death from hospital admission.
- Reapplies ICU length of stay ≥48 h to the MIMIC-III temporal sensitivity cohort (n=799; 140 events).
- Adds a strict prepared-table Round 2 orchestrator and reviewer-requested analysis workflow.
- Publishes aggregate R2 flow, calibration, missing-data, serum-iron, NIV-exclusion, observation-window, patient-unit, and duration-proxy results.
- Records the ensemble-specific RF and XGBoost parameters separately from the stand-alone comparator settings.
- Removes the public fitted model pickle because the fitted KNN imputer retains a training-feature matrix.
- Adds data-free privacy, parameter, denominator, and release-integrity tests.

Research use only. No clinical use is authorized.

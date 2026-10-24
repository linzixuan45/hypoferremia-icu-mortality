# R2 supplementary analysis summary

This directory retains R2 computation outputs with local R3 confidence-interval synchronization documented in `docs/R3_CORRECTION_AUDIT.json`. The internal reduced-model DeLong CI is 0.7183612417056014–0.8742151775083723. Temporal and exploratory intervals use the unchanged canonical bootstrap module with 2,000 resamples and seed 42. MIMIC-III benchmark/reduced CIs are 0.659–0.752 and 0.669–0.763; Third Xiangya/USC-FAH CIs are 0.699–0.900 and 0.826–0.954. AUROCs, Brier scores, denominators and fitted predictions are unchanged. This corrected tree has not yet been published as a new patch archive.

## Cohort accounting

The LOS-filtered screening set contained 1,568 records, but only 1,487 satisfied the fixed iron <60 micrograms/dL definition. The locked complete-case matrix contained 1,344 patients; 143 eligible patients were excluded because at least one locked predictor was missing.
Among eligible patients, 28-day in-hospital mortality from hospital admission was 200/1344 in complete cases and 15/143 among missingness exclusions.

## Multiple-imputation sensitivity

Five-imputation, five-fold out-of-fold AUROC was 0.808; Brier score was 0.112, calibration-in-the-large -0.917, and calibration slope 1.454.

## Corrected MIMIC-III eligibility analysis

Applying the stated ICU-LOS >=48-hour criterion reduced the MIMIC-III evaluation cohort from 1,046 to 799. The locked 18-predictor model AUROC was 0.705, Brier score 0.141, calibration-in-the-large -0.597, and calibration slope 0.929.

## Serum iron association and incremental value

Within the eligible documented-hypoferremia cohort, the adjusted odds ratio per 10-micrograms/dL increase in first serum iron was 1.062 (95% CI 0.954-1.182; P=0.2733).
Adding first serum iron to the prespecified clinical covariate model changed out-of-fold AUROC by -0.001 (95% CI -0.007 to 0.005).

## Interpretation limits

- The available workbook does not contain a valid normal-iron comparator from the full MIMIC-IV screening population.
- The available workbook does not contain charttime-level predictor measurements.
- `_min`, `_max`, and `_mean` are full-ICU-stay summaries; the legacy `t0` timing is synthetic and must not be presented as an observed timestamp.
- The dose-response analysis is within a selected documented-hypoferremia cohort and is not an estimate of the causal effect of hypoferremia versus normal iron.
- Public release includes code and aggregate outputs but excludes fitted objects retaining row-level information, not the protected workbook or row-level outcomes/probabilities.

## Generated tables

- `result\r2_analysis\tables\r2_corrected_mimic3_evaluation.csv`
- `result\r2_analysis\tables\r2_corrected_mimic3_flow_and_niv_missingness.csv`
- `result\r2_analysis\tables\r2_included_vs_excluded.csv`
- `result\r2_analysis\tables\r2_iron_adjusted_effect.csv`
- `result\r2_analysis\tables\r2_iron_incremental_value.csv`
- `result\r2_analysis\tables\r2_locked_matrix_missingness_and_windows.csv`
- `result\r2_analysis\tables\r2_multiple_imputation_per_imputation.csv`
- `result\r2_analysis\tables\r2_multiple_imputation_sensitivity.csv`
- `result\r2_analysis\tables\r2_niv_exclusion_sensitivity.csv`
- `result\r2_analysis\tables\r2_patient_flow.csv`
- `result\r2_analysis\tables\r2_standard_calibration_metrics.csv`
- `result\r2_analysis\tables\r2_table1_mimic4_eligible.csv`

## Public-release privacy boundary

This public release excludes patient-level records, identifiers, outcomes, individual prediction probabilities, and fitted preprocessing or model objects that retain row-level training information. In particular, the previously staged serialized 8-feature bundle was removed because its fitted KNN imputer retained a training-feature matrix. Credentialed users may reconstruct preprocessing and model objects locally from authorized prepared data. Submission-building scripts that depend on private project paths are also excluded. The repository supports analysis from authorized prepared tables; it is not a complete raw-clinical-database-to-table extraction pipeline.

# Hypoferremia 8-Feature Research Model — Model Card

**Research use only. Not for clinical decision-making.**

Companion article: *Retrospective mortality risk stratification in critically ill patients with documented hypoferremia*.

This R3 reporting-correction candidate is prepared for branch review and is based on computation archive v1.2.2 (DOI 10.5281/zenodo.21772246). Maintainer review, a new versioned release and a new archive DOI remain pending. It does not represent a new released model. Primary fitted models and stored predictions are unchanged. The existing NIV-exclusion sensitivity alone was refitted for verification and reproduced its pre-existing canonical aggregate output; this resolves inherited S11 reporting differences without a new modelling strategy.

## Status and intended use

The 8-feature soft-voting model is a post hoc, implementation-oriented derivative developed after review of development-data feature importance and SHAP results. It was not prespecified, does not replace the locked 18-predictor benchmark, and has not demonstrated non-inferiority, superiority, clinical utility, or universal transportability.

Permitted purpose: retrospective research audit and independently specified future validation. Prohibited purpose: diagnosis, triage, treatment selection, surveillance escalation, patient-facing risk communication, or autonomous clinical decision support.

## Analysis frame

- Population: ICU admissions with serum iron <60 µg/dL and ICU length of stay ≥48 h.
- Outcome: death in hospital within 28 days of hospital admission.
- Predictor window: `_1st` is the first ICU-stay value; `_min`, `_max`, and `_mean` summarize the full ICU stay.
- Timing limitation: the model is retrospective whole-stay risk stratification, not admission-time or real-time prediction.
- Preprocessing: KNNImputer with `n_neighbors=5`, fitted only in MIMIC-IV training data, followed by a training-set-fitted StandardScaler. Both are applied unchanged to non-training cohorts.

## Ensemble configuration

- Logistic regression: `max_iter=2000`, `class_weight='balanced'`, `random_state=42`.
- Random forest: `n_estimators=200`, `max_depth=6`, `class_weight='balanced'`, `random_state=42`.
- XGBoost: `n_estimators=120`, `max_depth=4`, `learning_rate=0.08`, `eval_metric='logloss'`, `random_state=42`.
- Combination: unweighted soft voting.

## Input features

`platelet_mean`, `wbc_min`, `bun_min`, `pco2_max`, `creatinine_min`, `is_noninvasive_ventilator`, `spo2_min`, and `platelet_1st`.

Creatinine and BUN use mg/dL. The NIV feature represents documented use, not physiological ventilatory status; missingness and documentation practices may differ substantially across datasets.

## Performance

| Cohort | n (events) | AUROC (95% CI) |
|---|---:|---:|
| MIMIC-IV internal test | 269 (40) | 0.796 (0.718–0.874) |
| Corrected MIMIC-III temporal sensitivity | 799 (140) | 0.715 (0.669–0.763) |
| Third Xiangya exploratory | 101 (26) | 0.810 (0.699–0.900) |
| The First Affiliated Hospital of University of South China (USC-FAH), exploratory | 98 (37) | 0.898 (0.826–0.954) |

These discrimination estimates do not establish calibration or clinical value. Probability miscalibration, small event counts, cross-system missingness, and dataset-specific documentation require independent prospective validation and local recalibration.

The internal-test confidence interval is DeLong (unrounded 0.7183612417056014–0.8742151775083723); the other three intervals use class-stratified percentile bootstrap with 2,000 resamples and seed 42. All limits were regenerated using the unchanged canonical interval module, from original retained probabilities or original-bundle inference. The MIMIC-III locked-benchmark interval is also synchronized to 0.659–0.752. Primary point estimates and Brier scores are unchanged. See `docs/R3_CORRECTION_AUDIT.json` for the reporting correction and aggregate provenance.

## Interpretability boundary

SHAP analyses describe the XGBoost base learner's fitted mortality output. They do not exactly decompose the soft-voting probability, identify causal mechanisms, or show that intervening on a feature would change mortality.

## Distribution boundary

The public repository does not distribute the fitted model bundle because the fitted KNN imputer retains a patient-level training-feature matrix. Authorized investigators may reconstruct fitted objects locally from protected data. The hosted interface is a research demonstration and is not evidence of clinical deployment readiness.

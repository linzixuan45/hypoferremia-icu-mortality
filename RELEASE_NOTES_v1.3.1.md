# Release v1.3.1 — R3 reporting corrections

Version 1.3.1 publishes the reviewed R3 reporting corrections for the retrospective ICU hypoferremia risk-stratification study. It is based on the v1.2.2 computation archive and does not retrain either primary model.

- GitHub release: https://github.com/linzixuan45/hypoferremia-icu-mortality/releases/tag/v1.3.1
- Zenodo concept DOI: https://doi.org/10.5281/zenodo.21761212
- Zenodo version DOI: assigned at deposition and recorded after verification
- Prior computation archive: v1.2.2, DOI https://doi.org/10.5281/zenodo.21772246, source tree `b9beaac`
- Historical unarchived GitHub release: v1.3.0, retained unchanged

## Changes

- Corrects the post hoc 8-feature MIMIC-IV internal-test DeLong 95% CI to 0.718–0.874 (AUROC 0.796; n=269; 40 events), replacing a mislabelled interval.
- Regenerates temporal and exploratory AUROC intervals with the unchanged canonical module (`scripts/metric_intervals.py`): class-stratified percentile bootstrap, 2,000 resamples, seed 42. MIMIC-III benchmark and reduced CIs are 0.659–0.752 and 0.669–0.763; Third Xiangya and USC-FAH CIs are 0.699–0.900 and 0.826–0.954.
- Uses the neutral Figure 7B axis label `AUROC (95% CI)` because the four rows use cohort-specific interval methods, and adds an aggregate-only panel generator.
- Synchronizes the inherited S11 NIV-exclusion sensitivity reporting to the existing canonical output: internal AUROCs 0.814 (17-predictor benchmark) and 0.785 (7-feature derivative); temporal AUROCs remain 0.727 and 0.751.
- Updates citation metadata, provenance records, the model card, the journal-compliance snippets and the release checklist.

## Boundaries

Primary fitted models, predictions, AUROC point estimates and Brier scores are unchanged. Only the pre-existing NIV-exclusion sensitivity was refitted for verification, using its unchanged archived functions and locked split; all four rows reproduce the canonical CSV within 1e-10. Patient-level records, identifiers, row-level outcomes, individual probabilities, cohort-ID lists and fitted preprocessing/model objects are not redistributed. The data-free tests are not independent clinical validation.

The manuscript is outside this code release. Its version and DOI citations are updated only after the v1.3.1 version DOI has been assigned and verified.

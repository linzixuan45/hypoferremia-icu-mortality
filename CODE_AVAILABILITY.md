# Code Availability

## Repository and archive status

- GitHub: https://github.com/linzixuan45/hypoferremia-icu-mortality
- Current release: `v1.3.1` (R3 reporting corrections), archived under Zenodo concept DOI `10.5281/zenodo.21761212`
- Current version DOI: recorded in `CITATION.cff` after Zenodo deposition and verification
- Prior computation archive: `v1.2.2`, DOI `10.5281/zenodo.21772246`, archived source tree `b9beaac`
- Historical reviewed release: `v1.2.1`, DOI `10.5281/zenodo.21768779`
- Historical GitHub release without a version DOI: `v1.3.0`, retained unchanged

Release integration: the reviewed R3 branch was merged onto current-main commit `12f0267414ae35ef775711db699da643307807ea`. Its accurate v1.2.2 citation/release metadata are retained in `provenance/v1.2.2_release_metadata/`; the source ZIP's stale embedded metadata remain separately preserved as historical evidence.

The prior v1.2.2 record remains unchanged. Version 1.3.1 updates reporting documentation and synchronizes AUROC intervals to the unchanged canonical computation: DeLong internally and class-stratified bootstrap with 2,000 resamples and seed 42 for temporal/exploratory evaluations. Original primary-model predictions, point estimates and Brier scores are unchanged; primary models were not retrained. The existing NIV-exclusion sensitivity alone was refitted for verification, reproducing all four pre-existing canonical reference rows and resolving an inherited manuscript reporting mismatch. The original v1.2.2 tag and archive remain unchanged. The local v1.2.2 source ZIP matches its supplied SHA-256 sidecar; a new remote download has not been claimed.

## Reproduction scope

The repository provides the active Round 2 workflow from an authorized, user-prepared modelling workbook: input validation, cohort construction, patient-separated splitting, training-set-only KNN imputation and standardization, candidate-model fitting, locked soft-voting and post hoc reduced-model evaluation, calibration analyses, figure generation, and reviewer-requested supplementary audits. It also includes non-patient aggregate reference outputs, an input schema, frozen dependencies, a model card, citation metadata, and research-interface source.

The repository does not provide a complete raw-clinical-database-to-modelling-table extraction pipeline. Optional SQL examples are provided for credentialed investigators but do not replace the protected data-preparation process.

## Privacy boundary

The public release excludes:

- raw or derived patient-level records;
- identifiers and cohort-ID lists;
- row-level outcomes and individual prediction probabilities;
- institution-held Chinese validation data;
- fitted imputers, scalers, and model objects.

The fitted KNN imputer retains its training-feature matrix. For that reason, the previously tracked 8-feature pickle is removed and must not be included in GitHub or Zenodo. Credentialed investigators can reconstruct fitted objects locally from authorized data.

## Manuscript-ready wording

The following describes version 1.3.1. Replace the concept DOI with the verified version-specific DOI once it is assigned.

```text
Analysis code and non-patient aggregate outputs for the R3 reporting corrections are archived as version 1.3.1 under the Zenodo concept DOI https://doi.org/10.5281/zenodo.21761212; the version-specific DOI is recorded in the released citation metadata. The repository is https://github.com/linzixuan45/hypoferremia-icu-mortality. The release synchronizes AUROC confidence intervals using the unchanged canonical functions: DeLong internally and class-stratified percentile bootstrap with 2,000 resamples and seed 42 otherwise. Primary models were not retrained, and their predictions, AUROC point estimates and Brier scores were unchanged. A bounded verification refit of the pre-existing NIV-exclusion sensitivity reproduced its canonical aggregate output and supports synchronizing the inherited manuscript values to that output. The previous v1.2.2 computation archive remains available at https://doi.org/10.5281/zenodo.21772246. The workflow starts from authorized prepared modelling tables and provides input validation, cohort construction, patient-separated splitting, training-set-only preprocessing, model fitting, evaluation, figure generation, and supplementary audits. It excludes patient-level records, identifiers, outcomes, individual probabilities, cohort-ID lists, and fitted preprocessing or model objects that retain training-row information.
```

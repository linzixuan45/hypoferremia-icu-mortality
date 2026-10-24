# Code Availability

## Repository and archive status

- GitHub: https://github.com/linzixuan45/hypoferremia-icu-mortality
- Published computation archive: `v1.2.2`, archived source tree `b9beaac`
- Published version DOI: `10.5281/zenodo.21772246`
- Zenodo concept DOI: `10.5281/zenodo.21761212`
- Historical reviewed release: `v1.2.1`, DOI `10.5281/zenodo.21768779`
- Current tree: R3 branch-review candidate; no assigned patch version or new DOI
- Review branch: `r3-reporting-corrections-20261023`; author/maintainer review and versioned deposition are pending

Integration base: current-main commit `12f0267414ae35ef775711db699da643307807ea`. Its accurate v1.2.2 citation/release metadata are retained in `provenance/v1.2.2_release_metadata/`; the source ZIP's stale embedded metadata remain separately preserved as historical evidence.

The published v1.2.2 record remains the prior computation archive. This review candidate updates reporting documentation and synchronizes AUROC intervals to the unchanged canonical computation: DeLong internally and class-stratified bootstrap with 2,000 resamples and seed 42 for temporal/exploratory evaluations. Original primary-model predictions, point estimates and Brier scores are unchanged; primary models were not retrained. The existing NIV-exclusion sensitivity alone was refitted for verification, reproducing all four pre-existing canonical reference rows and resolving an inherited manuscript reporting mismatch. A new patch release and version-specific DOI are required before describing these corrections as a newly archived release. The original v1.2.2 tag and archive must remain unchanged. The local source ZIP matches its supplied SHA-256 sidecar; a new remote download has not been claimed.

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

The following accurately describes the current status. Update it only after an actual patch release has been published and verified.

```text
Analysis code and non-patient aggregate outputs for the previous computation workflow are archived as version 1.2.2 at https://doi.org/10.5281/zenodo.21772246. The repository is https://github.com/linzixuan45/hypoferremia-icu-mortality. The R3 reporting-correction review candidate updates documentation and synchronizes AUROC confidence intervals using the unchanged canonical functions: DeLong internally and class-stratified percentile bootstrap with 2,000 resamples and seed 42 otherwise. Primary models were not retrained, and their predictions, AUROC point estimates and Brier scores were unchanged. A bounded verification refit of the pre-existing NIV-exclusion sensitivity reproduced its canonical aggregate output and supports synchronizing the inherited manuscript values to that output. A new versioned release and archive DOI remain pending review; the prior DOI must not be presented as the identifier for these R3 corrections. The workflow starts from authorized prepared modelling tables and provides input validation, cohort construction, patient-separated splitting, training-set-only preprocessing, model fitting, evaluation, figure generation, and supplementary audits. It excludes patient-level records, identifiers, outcomes, individual probabilities, cohort-ID lists, and fitted preprocessing or model objects that retain training-row information.
```

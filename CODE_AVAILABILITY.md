# Code Availability

## Repository and archive status

- GitHub: https://github.com/linzixuan45/hypoferremia-icu-mortality
- Current reviewed public release: `v1.2.2`, GitHub tagged merge commit `b9beaac`
- Current reviewed version DOI: `10.5281/zenodo.21772246`
- Zenodo concept DOI: `10.5281/zenodo.21761212`
- Historical reviewed release: `v1.2.1`, DOI `10.5281/zenodo.21768779`

GitHub release v1.2.2 and Zenodo DOI 10.5281/zenodo.21772246 archive the reviewed Round 2 scientific workflow and aggregate outputs at tagged merge commit `b9beaac`. The documentation- and manifest-only cleanup in this branch removes stale pre-publication wording; it does not change the cohort definitions, fitted-model specifications, figures, or reported aggregate results.

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

```text
Analysis code operating on authorized prepared modelling tables and non-patient aggregate Round 2 outputs is available in GitHub release v1.2.2 (https://github.com/linzixuan45/hypoferremia-icu-mortality/releases/tag/v1.2.2). The corresponding DOI-bearing Zenodo archive is available at https://doi.org/10.5281/zenodo.21772246. The repository provides input validation, cohort construction, patient-separated splitting, training-set-only preprocessing, model fitting, evaluation, figure generation, and supplementary-audit workflows. It excludes patient-level records, identifiers, outcomes, individual probabilities, cohort-ID lists, and fitted preprocessing or model objects that retain training-row information.
```

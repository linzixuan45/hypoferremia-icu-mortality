# Code Availability

## Repository and archive status

- GitHub: https://github.com/linzixuan45/hypoferremia-icu-mortality
- Current reviewed public release: `v1.2.1`, GitHub merge commit `b9beaac`
- Current reviewed version DOI: `10.5281/zenodo.21768779`
- Zenodo concept DOI: `10.5281/zenodo.21761212`
- Metadata-cleanup release prepared in this tree: `v1.2.2`

GitHub release v1.2.1 and Zenodo DOI 10.5281/zenodo.21768779 archive the reviewed Round 2 scientific workflow and aggregate outputs at merge commit `b9beaac`. Version 1.2.2 is a documentation- and manifest-only cleanup that removes stale pre-publication wording from the archived source tree; it does not change the cohort definitions, fitted-model specifications, figures, or reported aggregate results. Its new immutable version DOI must be inserted before the v1.2.2 tag is created.

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

## Wording to finalize after the v1.2.2 DOI is assigned

```text
Analysis code operating on authorized prepared modelling tables and non-patient aggregate Round 2 outputs is available in GitHub release v1.2.2 (https://github.com/linzixuan45/hypoferremia-icu-mortality/releases/tag/v1.2.2). The corresponding DOI-bearing Zenodo archive is available at https://doi.org/[INSERT_V1.2.2_VERSION_DOI]. The repository provides input validation, cohort construction, patient-separated splitting, training-set-only preprocessing, model fitting, evaluation, figure generation, and supplementary-audit workflows. It excludes patient-level records, identifiers, outcomes, individual probabilities, cohort-ID lists, and fitted preprocessing or model objects that retain training-row information.
```

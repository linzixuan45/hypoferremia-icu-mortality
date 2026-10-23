# Code Availability

## Repository and archive status

- GitHub: https://github.com/linzixuan45/hypoferremia-icu-mortality
- Published prior snapshot: `v1.2.0`, GitHub commit `0e49490`
- Published version DOI: `10.5281/zenodo.21761430`
- Zenodo concept DOI: `10.5281/zenodo.21761212`
- Exact reviewed release target after merge: `v1.2.1`

The published v1.2.0 record predates the final R2-alignment commits and must not be described as the exact archive of the reviewed branch. The post-review merge commit will be archived as the next immutable Zenodo version.

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
Analysis code operating on authorized prepared modelling tables and non-patient aggregate Round 2 outputs is available at https://github.com/linzixuan45/hypoferremia-icu-mortality. Zenodo v1.2.0 is archived at https://doi.org/10.5281/zenodo.21761430. Because that immutable record corresponds to GitHub commit 0e49490 and predates the final Round 2 alignment commits, the reviewed merge commit will be deposited as the next Zenodo version and its version DOI will be inserted before final resubmission. The repository provides input validation, cohort construction, patient-separated splitting, training-set-only preprocessing, model fitting, evaluation, figure generation, and supplementary-audit workflows. It excludes patient-level records, identifiers, outcomes, individual probabilities, cohort-ID lists, and fitted preprocessing or model objects that retain training-row information.
```

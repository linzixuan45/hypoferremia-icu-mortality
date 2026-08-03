# Data Availability

## MIMIC-III and MIMIC-IV

MIMIC-III and MIMIC-IV are available to credentialed researchers through PhysioNet under their respective training and data-use requirements. This repository does not include MIMIC tables, patient identifiers, or derived patient-level feature exports.

## Institution-held cohorts

The Third Xiangya exploratory cohort and The First Affiliated Hospital of University of South China exploratory cohort (USC-FAH; ethics approval 2025LL0115001) contain institution-held clinical data and are not publicly redistributed. Official University of South China materials list The First Affiliated Hospital of University of South China and Affiliated Nanhua Hospital, University of South China as separate institutions; the public manuscript and repository therefore do not use “Nanhua Hospital” or “NH” as the legal name for the USC-FAH cohort. Access, if legally and ethically permissible, remains subject to the responsible institutions, approvals, and data-governance procedures; no unconditional “available upon request” promise is made here.

## Local files required for reproduction

Authorized users prepare `data/mimic_dataset.xlsx` according to [docs/R2_INPUT_SCHEMA.md](docs/R2_INPUT_SCHEMA.md). Optional institution-held cohort files remain under `data/external/`. All local workbooks, parquet files, cohort-ID lists, predictions, fitted objects, and result directories are gitignored.

## Public non-patient outputs

The repository publishes:

- analysis and validation code;
- input schema and non-patient configuration;
- aggregate cohort counts and performance/calibration results in `reference/r2/`;
- model and reporting documentation;
- research-interface source without a public fitted model bundle.

## Manuscript-ready wording

```text
MIMIC-III and MIMIC-IV data are available to credentialed researchers through PhysioNet under the applicable data-use requirements. The two Chinese exploratory cohorts are institution-held and are not publicly redistributed. The public repository contains analysis code, input-schema documentation, and non-patient aggregate reference outputs, but excludes patient-level data, identifiers, cohort-ID lists, individual outcomes or probabilities, and fitted preprocessing or model objects.
```

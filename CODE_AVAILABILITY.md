# Code Availability

Repository positioning: **auditable analysis source code** — pipeline logic, inference, model card, and locked reference metrics are public; patient-level data are not redistributed. See [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md) for publication-day steps. Review submission bundles may omit internal release docs; see the GitHub repository for the full file tree.

## Research demonstration calculator

- URL: https://fe.mixaihub.top
- Purpose: 8-feature research probability calculator with SHAP audit (not for clinical use)

## GitHub

- Repository: https://github.com/linzixuan45/hypoferremia-icu-mortality
- Release tag: `v1.1.0` (recommended for the second revision)

## Zenodo (DOI-assigning archive)

- Concept DOI: **Pending** (assign after GitHub release and Zenodo integration)
- Version DOI: **Pending**

## What is deposited

The archived repository includes:

- Analysis pipeline (`scripts/`)
- Second-revision statistical analyses (`scripts/r2_supplementary_analyses.py`)
- MIMIC SQL extraction scripts (`sql/`)
- Inference code (`inference.py`)
- Released 8-feature model bundle (`model_weights/8_features_model.pkl`)
- Model card and data dictionary (`MODEL_CARD.md`, `docs/data_dictionary.md`)
- Methods documentation (`docs/FE1_spec.md`, `docs/data_flow_cohorts.md`)
- Locked reference metrics (`reference/manifest.json`)
- Corrected non-patient R2 tables and Figure 2 source (`reference/r2/`)

Raw patient-level data, cohort ID lists, row-level outcomes, and row-level prediction probabilities are **not** redistributed because MIMIC and local validation data are access-restricted. Non-patient aggregate result tables are included.

## Manuscript text (paste into Methods or Code Availability)

```text
An HTTPS research demonstration calculator for the 8-feature model is available at https://fe.mixaihub.top (not for clinical use). The complete analysis code, R2 sensitivity analyses, non-patient aggregate results, Figure 2 plotting source, model card, and released research model bundle are available at https://github.com/linzixuan45/hypoferremia-icu-mortality and will be archived with a version DOI at Zenodo. Raw and derived patient-level data, including row-level outcomes and prediction probabilities, are not redistributed because access to MIMIC and local validation data is restricted.
```

## Zenodo release checklist

1. Push `Project_low_Fe` to a public GitHub repository.
2. In Zenodo, enable GitHub integration and select the repository.
3. Create a GitHub release (`v1.1.0`).
4. Confirm Zenodo generates a version DOI.
5. Replace Zenodo placeholders in this file, `README.md`, and the manuscript.
6. Add the Zenodo DOI to the point-by-point response letter.

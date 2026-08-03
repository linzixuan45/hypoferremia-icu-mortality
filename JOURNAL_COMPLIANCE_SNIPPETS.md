# Journal Compliance Snippets

GitHub release v1.2.1 and Zenodo DOI 10.5281/zenodo.21768779 archive the reviewed Round 2 workflow at merge commit `b9beaac`. Version 1.2.2 is a metadata-only cleanup of that reviewed source. Replace `[INSERT_V1.2.2_VERSION_DOI]` below with the immutable DOI assigned to the v1.2.2 release before resubmission.

## Code Availability

```text
Analysis code operating on authorized prepared modelling tables and non-patient aggregate Round 2 outputs is available in GitHub release v1.2.2 (https://github.com/linzixuan45/hypoferremia-icu-mortality/releases/tag/v1.2.2). The corresponding DOI-bearing Zenodo archive is available at https://doi.org/[INSERT_V1.2.2_VERSION_DOI]. The repository excludes patient-level records, identifiers, outcomes, individual probabilities, cohort-ID lists, and fitted preprocessing or model objects that retain training-row information.
```

## Editor response on code deposit

```text
We re-audited the repository and prepared release v1.2.2 as a metadata-only cleanup of the reviewed Round 2 source. The active workflow reconstructs the analyses from an authorized prepared modelling workbook and includes validation, cohort construction, patient-separated splitting, training-set-only preprocessing, candidate and ensemble model fitting, evaluation, figure generation, and supplementary audits. The release excludes patient-level data, cohort-ID lists, row-level outcomes or probabilities, and fitted objects that retain training-row information. The v1.2.2 GitHub release and its immutable Zenodo version DOI will be cited in the final resubmission.
```

## Placeholder tracking

| Item | Status | Value |
|---|---|---|
| GitHub | Complete | https://github.com/linzixuan45/hypoferremia-icu-mortality |
| Current reviewed release | Complete | `v1.2.1`, commit `b9beaac` |
| Metadata-cleanup release | Prepared | `v1.2.2` |
| Zenodo concept DOI | Complete | `10.5281/zenodo.21761212` |
| Zenodo version DOI | Required before tagging | `[INSERT_V1.2.2_VERSION_DOI]` |

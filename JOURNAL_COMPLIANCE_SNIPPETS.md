# Journal Compliance Snippets

Zenodo v1.2.0 (10.5281/zenodo.21761430) is a prior snapshot corresponding to commit `0e49490`. Insert the new version DOI only after Zenodo has archived the reviewed merge commit as `v1.2.1`.

## Code Availability

```text
Analysis code operating on authorized prepared modelling tables and non-patient aggregate Round 2 outputs is available at https://github.com/linzixuan45/hypoferremia-icu-mortality. Zenodo v1.2.0 is archived at https://doi.org/10.5281/zenodo.21761430, but that immutable record corresponds to commit 0e49490 and predates the final R2-alignment commits. The reviewed merge commit will therefore be archived as the next Zenodo version and its version DOI inserted before resubmission. The repository excludes patient-level records, identifiers, outcomes, individual probabilities, cohort-ID lists, and fitted preprocessing or model objects that retain training-row information.
```

## Editor response on code deposit

```text
We re-audited the repository and prepared the reviewed `v1.2.1` release candidate. The active workflow reconstructs the Round 2 analyses from an authorized prepared modelling workbook and includes validation, cohort construction, patient-separated splitting, training-set-only preprocessing, candidate and ensemble model fitting, evaluation, figure generation, and supplementary audits. The release excludes patient-level data, cohort-ID lists, row-level outcomes or probabilities, and fitted objects that retain training-row information. Zenodo v1.2.0 remains a prior snapshot; the exact reviewed merge commit will be archived as the next version before final resubmission.
```

## Placeholder tracking

| Item | Status | Value |
|---|---|---|
| GitHub | Complete | https://github.com/linzixuan45/hypoferremia-icu-mortality |
| Release target | Prepared | `v1.2.1` after review and merge |
| Zenodo concept DOI | Pending | |
| Zenodo version DOI | Pending | |

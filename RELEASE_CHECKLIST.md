# Release checklist for the R3 reporting-correction review branch

Published baseline: v1.2.2, DOI 10.5281/zenodo.21772246, archived source tree `b9beaac`. This candidate has no new tag or DOI. Historical v1.2.0 is DOI 10.5281/zenodo.21761430, commit `0e49490`; historical release notes remain under their original filenames.

Review branch: `r3-reporting-corrections-20261023`, based on main commit `12f0267414ae35ef775711db699da643307807ea`. The author has authorized pushing this separate branch for collaborator review. That push is separate from merging, creating a release or minting a DOI.

## Checks for this reporting-only branch

- [ ] `pytest -q` passes.
- [ ] No `.xlsx`, `.xls`, `.parquet`, `.pkl`, `.joblib`, `.npz`, cohort-ID list, row-level outcome, or individual probability is tracked.
- [ ] `model_weights/8_features_model.pkl` is absent from the release tree.
- [ ] Aggregate outputs match `reference/r2/` and the manuscript.
- [ ] Table S4 ensemble-specific parameters match `scripts/train_models.py`, `scripts/plot_figure4_benchmark.py`, and `reference/r2/model_bundle_metadata.json`.
- [ ] Python sources compile, `git diff --check` passes, and the safe-file SHA-256 manifest matches the exact proposed branch tree.
- [ ] Confirm the corrected internal reduced-model DeLong 95% CI 0.718–0.874 and neutral Figure 7B axis label `AUROC (95% CI)`.
- [ ] Confirm canonical 2,000-resample seed-42 bootstrap CIs: MIMIC-III benchmark 0.659–0.752, reduced 0.669–0.763; Third Xiangya 0.699–0.900; USC-FAH 0.826–0.954. Primary point estimates and Brier scores remain unchanged.
- [ ] Confirm the existing canonical NIV sensitivity CSV and aggregate verification record agree: internal AUROCs 0.814/0.785, temporal 0.727/0.751; corresponding Brier/CITL/slope entries are synchronized.

The data-free tests check software/reporting consistency and privacy boundaries. They are not independent clinical validation. The completed calculation audits and bounded verification refit of the pre-existing NIV sensitivity support this patch. Re-running primary model training or the full `run_r2_analysis.py` workflow is not required for this reporting-only branch.

## Author and maintainer publication actions

- [ ] Push the separate review branch without changing `main` or existing tags; ask the designated collaborator to review the actual branch diff and aggregate audit records.
- [ ] After author/maintainer approval, merge the reviewed changes into `main`.
- [ ] Assign an actual new patch version and create a release from the reviewed merge commit; preserve all existing tags including v1.2.2.
- [ ] Archive the new release as a new version under Zenodo concept DOI `10.5281/zenodo.21761212`.
- [ ] Record the actual new immutable version DOI; v1.2.2 DOI `10.5281/zenodo.21772246` remains the prior computation snapshot.
- [ ] Only after a real new version DOI is assigned and verified, record it in the repository citation/availability metadata. If archived files are subsequently changed, preserve the existing archive and use a new immutable version rather than replacing it silently.
- [ ] The author can then authorize synchronizing the verified version and DOI into the manuscript, checklist, cover letter and point-by-point response. Manuscript files are unchanged by this branch update; do not insert a placeholder or guessed DOI.
- [ ] Re-run all tests after DOI-only edits and confirm the archived tree remains data-free.
- [ ] Run `python scripts/verify_reporting_manifest.py` and verify the final downloadable archive.

No release version or DOI has yet been assigned to the R3 correction. The real v1.2.2 DOI remains a historical computation reference throughout branch review.

## Historical or separate tasks

- The original full modelling workflow and protected-workbook validator remain available for authorized reproduction; they are not outstanding requirements for this reporting patch.
- Figure 8's default-case deployment was verified on 3 August 2026. This code/reporting branch does not require or perform web redeployment; a new deployment audit would be a separately requested task.
- Manuscript/PDF submission checks and the Figure 1 BioRender licence are managed in the submission package. Do not add those graphics or licence documents to this code branch.

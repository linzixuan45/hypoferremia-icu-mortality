# Release checklist — v1.3.1 (R3 reporting corrections)

Published baseline: v1.2.2, DOI 10.5281/zenodo.21772246, archived source tree `b9beaac`. Historical v1.2.1 is DOI 10.5281/zenodo.21768779; historical v1.2.0 is DOI 10.5281/zenodo.21761430, commit `0e49490`. The unarchived GitHub release v1.3.0 is retained unchanged and is not used for citation.

Current release: v1.3.1, based on main commit `12f0267414ae35ef775711db699da643307807ea` plus the reviewed R3 merge. Zenodo version DOI: 10.5281/zenodo.23608695 (record 23608695), under concept DOI 10.5281/zenodo.21761212.

## Pre-release checks

- [x] `pytest -q` passes (26 data-free tests).
- [x] No `.xlsx`, `.xls`, `.parquet`, `.pkl`, `.joblib`, `.npz`, cohort-ID list, row-level outcome, or individual probability is tracked.
- [x] `model_weights/8_features_model.pkl` is absent from the release tree.
- [x] Aggregate outputs match `reference/r2/` and the corrected manuscript S11 values.
- [x] Table S4 ensemble-specific parameters match `scripts/train_models.py`, `scripts/plot_figure4_benchmark.py`, and `reference/r2/model_bundle_metadata.json`.
- [x] Python sources compile, `git diff --check` passes, and `SOURCE_SHA256_MANIFEST.tsv` matches the release tree.
- [x] `CITATION.cff` validates against CFF 1.2.0, including authors on `preferred-citation`.
- [x] Confirm the corrected internal reduced-model DeLong 95% CI 0.718–0.874 and neutral Figure 7B axis label `AUROC (95% CI)`.
- [x] Confirm canonical 2,000-resample seed-42 bootstrap CIs: MIMIC-III benchmark 0.659–0.752, reduced 0.669–0.763; Third Xiangya 0.699–0.900; USC-FAH 0.826–0.954. Primary point estimates and Brier scores remain unchanged.
- [x] Confirm the existing canonical NIV sensitivity CSV and aggregate verification record agree: internal AUROCs 0.814/0.785, temporal 0.727/0.751; corresponding Brier/CITL/slope entries are synchronized.
- [x] `.zenodo.json` carries `version: 1.3.1` and a release description, without a guessed DOI.

The data-free tests check software/reporting consistency and privacy boundaries. They are not independent clinical validation. Re-running primary model training or the full `run_r2_analysis.py` workflow is not required for this reporting-only release.

## Release and archive actions

- [x] Merge the reviewed PR #3 into `main` without rewriting or moving existing tags.
- [x] Assign version `v1.3.1`; preserve v1.2.2, v1.2.1, v1.2.0 and v1.3.0 exactly as they are.
- [x] Create GitHub release `v1.3.1` from the release commit; Zenodo archived it as record 23608695 under concept DOI `10.5281/zenodo.21761212`.
- [x] Verify the newly assigned version DOI `10.5281/zenodo.23608695`.
- [x] Record the verified DOI in `CITATION.cff`, `CITATION.bib`, `README.md`, `CODE_AVAILABILITY.md`, `JOURNAL_COMPLIANCE_SNIPPETS.md` and the R3 audit JSONs; keep the prior v1.2.2 DOI as the earlier computation archive.
- [ ] Re-run all tests after DOI-only edits, regenerate `SOURCE_SHA256_MANIFEST.tsv`, and confirm the archived tree remains data-free.
- [ ] After the DOI is verified, update the manuscript, cover letter and point-by-point response to cite v1.3.1; do not insert a placeholder or guessed DOI.

Version 1.3.1 is the first release containing the R3 corrections; it is archived at DOI 10.5281/zenodo.23608695. The v1.2.2 DOI remains a historical computation reference; v1.3.0 remains an unarchived GitHub release.

## Historical or separate tasks

- The original full modelling workflow and protected-workbook validator remain available for authorized reproduction; they are not outstanding requirements for this reporting release.
- Figure 8's default-case deployment was verified on 3 August 2026. This release does not require or perform web redeployment; a new deployment audit would be a separately requested task.
- Manuscript/PDF submission checks and the Figure 1 BioRender licence are managed in the submission package. Do not add those graphics or licence documents to this code release.

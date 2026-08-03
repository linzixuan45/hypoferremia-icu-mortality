# Release Checklist — v1.2.2

## Privacy and reproducibility gate

- [ ] `pytest -q` passes.
- [ ] No `.xlsx`, `.xls`, `.parquet`, `.pkl`, `.joblib`, `.npz`, cohort-ID list, row-level outcome, or individual probability is tracked.
- [ ] `model_weights/8_features_model.pkl` is absent from the release tree.
- [ ] `python scripts/validate_excel_input.py --report --strict` passes on the authorized local workbook.
- [ ] `python scripts/run_r2_analysis.py` completes, or any unavailable optional cohort is stated explicitly.
- [ ] Aggregate outputs match `reference/r2/` and the manuscript.
- [ ] Table S4 ensemble-specific parameters match `scripts/train_models.py`, `scripts/plot_figure4_benchmark.py`, and `reference/r2/model_bundle_metadata.json`.

## GitHub and Zenodo

- [ ] Merge the reviewed v1.2.2 cleanup pull request into `main`.
- [ ] Reserve or obtain the immutable Zenodo version DOI for `v1.2.2`.
- [ ] Insert that DOI in `README.md`, `CODE_AVAILABILITY.md`, `CITATION.cff`, `CITATION.bib`, `JOURNAL_COMPLIANCE_SNIPPETS.md`, and the submission documents before tagging.
- [ ] Create GitHub release `v1.2.2` from that exact DOI-bearing merge commit; do not move the published v1.2.1 tag.
- [ ] Archive release `v1.2.2` as the next version under Zenodo concept DOI `10.5281/zenodo.21761212`.
- [ ] Confirm that the Zenodo v1.2.2 archive contains no `[INSERT_V1.2.2_VERSION_DOI]` placeholder or stale pre-publication wording.
- [ ] Re-run all tests after DOI-only edits and confirm the archived tree remains data-free.

## Submission-only items

- [ ] Upload the final response letter as PDF after page-by-page visual inspection.
- [ ] Retain the Figure 1 BioRender publication licence or equivalent rights documentation.
- [ ] Confirm Figure 1 authorship/provenance with the journal as requested.
- [x] Verify https://fe.mixaihub.top against the reviewed web source and confirm that the probability direction, all three case-level Figure 8 headings, and the research-only warning match the manuscript (verified 3 August 2026).

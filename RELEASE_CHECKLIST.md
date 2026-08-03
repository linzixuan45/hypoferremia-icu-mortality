# Release Checklist — v1.2.1

## Privacy and reproducibility gate

- [ ] `pytest -q` passes.
- [ ] No `.xlsx`, `.xls`, `.parquet`, `.pkl`, `.joblib`, `.npz`, cohort-ID list, row-level outcome, or individual probability is tracked.
- [ ] `model_weights/8_features_model.pkl` is absent from the release tree.
- [ ] `python scripts/validate_excel_input.py --report --strict` passes on the authorized local workbook.
- [ ] `python scripts/run_r2_analysis.py` completes, or any unavailable optional cohort is stated explicitly.
- [ ] Aggregate outputs match `reference/r2/` and the manuscript.
- [ ] Table S4 ensemble-specific parameters match `scripts/train_models.py`, `scripts/plot_figure4_benchmark.py`, and `reference/r2/model_bundle_metadata.json`.

## GitHub and Zenodo

- [ ] Merge the reviewed pull request into `main`.
- [ ] Create GitHub release `v1.2.1` from that exact merge commit; do not move the published v1.2.0 tag.
- [ ] Archive release `v1.2.1` as the next version under Zenodo concept DOI `10.5281/zenodo.21761212`.
- [ ] Record the new immutable version DOI; v1.2.0 DOI `10.5281/zenodo.21761430` remains a prior snapshot.
- [ ] Insert the new version DOI in `README.md`, `CODE_AVAILABILITY.md`, `CITATION.cff`, `.zenodo.json`, the manuscript, and the point-by-point response.
- [ ] Re-run all tests after DOI-only edits and confirm the archived tree remains data-free.

## Submission-only items

- [ ] Upload the final response letter as PDF after page-by-page visual inspection.
- [ ] Retain the Figure 1 BioRender publication licence or equivalent rights documentation.
- [ ] Confirm Figure 1 authorship/provenance with the journal as requested.
- [ ] Refresh https://fe.mixaihub.top from the reviewed web source and verify that all visible Figure 8 headings and warning text match the manuscript.

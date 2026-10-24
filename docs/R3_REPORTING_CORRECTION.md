# R3 reporting corrections (version 1.3.1)

The companion manuscript title is **Retrospective mortality risk stratification in critically ill patients with documented hypoferremia**.

Version 1.3.1 integrates the reviewed R3 branch onto current-main commit `12f0267414ae35ef775711db699da643307807ea`. The v1.2.2 metadata cleanup, historical release notes, completed 3 August 2026 Figure 8 verification and its regression checks are preserved. Accurate prior-release citation metadata are in `provenance/v1.2.2_release_metadata/`, separately from the older source ZIP's embedded metadata. See `docs/R3_CURRENT_MAIN_INTEGRATION.json`.

This release is based on the locally retained public Zenodo v1.2.2 source archive, source tree `b9beaac`, DOI **10.5281/zenodo.21772246**. The archive SHA-256 matches its supplied sidecar (`ff159c6722becf34c33180adf830e74392c1383db02d7345ba366e5be47734b5`). The original archive is unchanged. This check is local archive verification, not a claim of a new remote Zenodo download.

## Correction scope

1. The post hoc 8-feature MIMIC-IV internal-test AUROC remains 0.7962882096069869, n=269 and events=40. The correctly reported DeLong 95% CI is **0.7183612417056014–0.8742151775083723** (0.718–0.874 at three decimals). The previous figure metrics row carried 0.7161722821965112–0.8711261727911128 while labelling the method DeLong. The corrected limits replace only this internal reduced-model interval.
2. MIMIC-III and Chinese exploratory intervals are regenerated with the unchanged canonical `scripts/metric_intervals.py`: class-stratified percentile bootstrap, 2,000 resamples, random seed 42. Original fitted-bundle inference in the scikit-learn 1.8.0 / XGBoost 3.2.0 environment exactly reproduces the MIMIC-III primary AUROCs and Brier scores; predictions follow the original prepared-workbook order. Chinese intervals use retained original prediction order. The resulting MIMIC-III benchmark/reduced intervals are 0.659–0.752 and 0.669–0.763; Third Xiangya/USC-FAH intervals are 0.699–0.900 and 0.826–0.954. Primary point estimates and Brier scores are unchanged.
3. Figure 7B uses the neutral axis label **AUROC (95% CI)** because its four rows use different cohort-specific methods. A narrowly scoped aggregate-only panel generator is provided in `scripts/plot_figure7b_auroc.py`. It reads the corrected reference CSV and does not load patient data, models or probabilities. It does not regenerate panels A, C or D.
4. Active documentation and citation files use the R3 manuscript title and remove obsolete instructions to publish v1.2.1. The original stale embedded metadata are preserved in `provenance/v1.2.2_embedded_metadata/`; their software-version wording is historical, not the release status of this release.
5. The software title of the prior v1.2.2 archive remains unchanged in its historical citation. This release is version **1.3.1**; `.zenodo.json` carries that version and its version-specific DOI is assigned at Zenodo deposition.

Neither primary model was retrained. The original training code, cohort construction, split logic, endpoint definition, preprocessing and metric algorithms are unchanged. Only the pre-existing NIV-exclusion sensitivity was refitted using its unchanged archived functions, original fixed split and pinned libraries to resolve an inherited manuscript-versus-reference discrepancy. All four recomputed rows match the pre-existing canonical CSV within 1e-10. Accordingly, S11 and the corresponding Results sentence are synchronized to the canonical internal AUROCs 0.814 (17-predictor benchmark) and 0.785 (7-feature derivative), rather than inherited manuscript values 0.816 and 0.783; temporal AUROCs remain 0.727 and 0.751. Brier, calibration-in-the-large and slope reporting follow those same canonical rows. The canonical CSV itself is unchanged. This bounded verification is not a new analysis strategy. Safe aggregate provenance is in `docs/R3_NIV_SENSITIVITY_VERIFICATION.json`. Protected records, individual predictions and fitted objects are not copied into this tree.

## Verification and provenance

`docs/R3_CORRECTION_AUDIT.json` records the change and source archive. `SOURCE_SHA256_MANIFEST.tsv` records release file hashes, excluding its own row and runtime caches. Run:

```bash
python -m compileall -q scripts src web tests inference.py webui.py
python -m pytest -q
python scripts/verify_reporting_manifest.py
```

The data-free tests do not independently retrain or validate clinical performance. The R3 manuscript team regenerated all headline AUROC intervals from authorized retained original probabilities or inference with the original fitted bundles; the redacted aggregate evidence is in `docs/R3_AGGREGATE_PREDICTION_AUDIT.json`. The internal DeLong and all temporal/exploratory canonical-bootstrap limits now have direct calculation evidence. The exact resampling process that produced the older published bootstrap limits is not reconstructed; those older limits are replaced by the documented 2,000-resample seed-42 canonical outputs rather than being described as reproduced.

To render only the aggregate corrected panel for subsequent visual inspection:

```bash
python scripts/plot_figure7b_auroc.py --output-prefix result/r3_reporting/figure7b_corrected
```

This generator was run for layout QA during release preparation; the submission figure assembly and its visual audit remain separate deliverables.

## Publication status

Version 1.3.1 was released from the reviewed merge commit. The version-specific DOI is assigned by Zenodo at deposition and must be verified before the manuscript cites it. The prior v1.2.2 computation archive remains available at DOI 10.5281/zenodo.21772246, and the unarchived v1.3.0 GitHub release is retained unchanged. The manuscript files are outside this code release and are updated only after the version DOI is verified. The exact release and archive steps are listed in `RELEASE_CHECKLIST.md`.

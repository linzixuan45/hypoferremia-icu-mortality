# Hypoferremia ICU Mortality Risk Model

**Research use only. Not for clinical use.**

Code repository for the manuscript on functional hypoferremia in ICU patients.

**Code:** https://github.com/linzixuan45/hypoferremia-icu-mortality · **Web demo:** https://k.mixaihub.top · See [CODE_AVAILABILITY.md](CODE_AVAILABILITY.md)

This repository provides the analysis pipeline, optional MIMIC SQL exports, inference code, model card, data dictionary, and a released 8-feature research model bundle. **Raw patient-level data are not redistributed.**

To learn more about the underlying critical care databases, see [MIMIC](https://mimic.mit.edu) and the community [MIMIC Code Repository](https://github.com/MIT-LCP/mimic-code).

---

## Choose your path

### A. Try the 8-feature model (~5 min)

The repository **includes** the released model weights (`model_weights/8_features_model.pkl`). No MIMIC data required.

```bash
pip install -r requirements.txt
python inference.py --demo
python inference.py --help
```

Re-run `python scripts/export_github_weights.py` only if you retrain the pipeline and want to overwrite the bundled weights.

### B. Reproduce the full analysis (requires MIMIC Excel)

1. Obtain credentialed MIMIC access on PhysioNet.
2. Build `data/mimic_dataset.xlsx` — see [docs/mimic_excel_reproduction_guide.md](docs/mimic_excel_reproduction_guide.md).
3. Run:

```bash
python scripts/validate_excel_input.py
python scripts/run_pipeline.py
python scripts/verify_reproduction.py
```

### C. Verify against the locked reference run (reviewers)

Locked aggregate metrics (no patient IDs): [reference/manifest.json](reference/manifest.json) · [reference/table2_3_performance.csv](reference/table2_3_performance.csv)

After a local reproduction (path B), run `python scripts/verify_reproduction.py` to compare AUROC and cohort counts (tolerance ±0.005 AUROC).

---

## Access to data

Full reproduction requires credentialed access to MIMIC on PhysioNet:

| Database | PhysioNet |
|----------|-----------|
| MIMIC-III | [mimiciii](https://physionet.org/content/mimiciii/) |
| MIMIC-IV | [mimiciv](https://physionet.org/content/mimiciv/) |

Place locally prepared feature tables at `data/mimic_dataset.xlsx` (format in [docs/preprocessing_excel.md](docs/preprocessing_excel.md)). Chinese geographic validation (F3/NH) requires additional local files under `data/external/` — see [DATA_AVAILABILITY.md](DATA_AVAILABILITY.md).

---

## Navigating this repository

| Path | Contents |
|------|----------|
| [`inference.py`](inference.py) | Single-patient / batch 28-day mortality probability (CLI) |
| [`model_weights/`](model_weights/) | Released 8-feature ensemble + imputer + scaler |
| [`reference/`](reference/) | Locked AUROC / cohort-count benchmark (no patient IDs) |
| [`scripts/`](scripts/) | End-to-end analysis pipeline (Python) |
| [`sql/`](sql/) | Optional SQL exports for charttime-level t₀ |
| [`docs/`](docs/) | Methods specs, data dictionary, Excel preprocessing guide |
| [`config/`](config/) | Non-patient metadata (e.g. LASSO feature list, column checklist) |
| [`data/README.md`](data/README.md) | Where to place local `mimic_dataset.xlsx` |

Pipeline outputs are written to `result/analysis/` (local only; gitignored).

### Documentation (language)

| Document | Language |
|----------|----------|
| README, MODEL_CARD, preprocessing_excel, mimic_excel_reproduction_guide | English |
| FE1_spec.md, data_flow_cohorts.md | Chinese (methods); see [FE1_spec_en.md](docs/FE1_spec_en.md) for English summary |

### Analysis pipeline (`scripts/`)

| Script | Role |
|--------|------|
| [`run_pipeline.py`](scripts/run_pipeline.py) | Run the full Excel-based pipeline |
| [`validate_excel_input.py`](scripts/validate_excel_input.py) | Validate `mimic_dataset.xlsx` before analysis |
| [`verify_reproduction.py`](scripts/verify_reproduction.py) | Compare local manifest to `reference/manifest.json` |
| [`prepare_t0_labs_parquet.py`](scripts/prepare_t0_labs_parquet.py) | Build interim t₀ timing from Excel |
| [`build_t0_cohort.py`](scripts/build_t0_cohort.py) | Cohort filters, outcomes, ID lists, `manifest.json` |
| [`train_models.py`](scripts/train_models.py) | Train 20/8-feature soft-voting models; Tables 2–6, S8–S9 |
| [`supplementary_analysis.py`](scripts/supplementary_analysis.py) | DCA, sensitivities, subgroups; Tables S6–S15 |
| [`verify_manifest.py`](scripts/verify_manifest.py) | Manifest ↔ table consistency checks |

Further detail: [docs/preprocessing_excel.md](docs/preprocessing_excel.md) · [docs/data_flow_cohorts.md](docs/data_flow_cohorts.md)

### SQL extraction (`sql/`)

Optional upgrade when charttime-level t₀ is available from PhysioNet SQL. See [sql/README.md](sql/README.md).

After SQL export, re-run from `build_t0_cohort.py`.

---

## Step-by-step reproduction

```bash
python scripts/validate_excel_input.py
python scripts/prepare_t0_labs_parquet.py
python scripts/build_t0_cohort.py
python scripts/train_models.py
python scripts/supplementary_analysis.py
python scripts/benchmark_severity_scores.py
python scripts/build_table1_baseline.py
python scripts/export_github_weights.py
python scripts/verify_reproduction.py
```

**Diagnostic tools:**

```bash
python scripts/audit_mimic_excel.py
python scripts/validate_excel_input.py --report
python scripts/validate_parquet_export.py
python scripts/verify_manifest.py
```

---

## Model overview

| Item | Definition |
|------|------------|
| **Cohort** | ICU patients with documented functional hypoferremia (serum iron < 60 µg/dL) |
| **Index time t₀** | Proxy first hypoferremia episode (Excel) or first iron < 60 from SQL |
| **Outcome** | Death within 28 calendar days from t₀ |
| **Model** | 8-feature soft-voting ensemble (XGBoost + Random Forest + Logistic Regression) |
| **Class balance** | `class_weight='balanced'` on MIMIC-IV development set |

**8 input features:** `platelet_mean`, `wbc_min`, `bun_min`, `pco2_max`, `creatinine_min`, `is_noninvasive_ventilator`, `spo2_min`, `platelet_1st` — see [docs/data_dictionary.md](docs/data_dictionary.md) and [MODEL_CARD.md](MODEL_CARD.md).

**Locked reference AUROC (8-feature):** MIMIC-IV internal test 0.796 · MIMIC-III external 0.712 — see [reference/manifest.json](reference/manifest.json).

---

## License / use

- **Code:** [MIT License](LICENSE)
- **Data:** MIMIC and local validation cohorts require separate authorized access; not redistributed here.
- **Use:** Research use only. **Do not use for clinical decision-making.**

Citation: see [CITATION.bib](CITATION.bib).

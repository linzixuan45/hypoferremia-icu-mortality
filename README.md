# Hypoferremia ICU Mortality Risk Model

**Research use only. Not for clinical use.**

Code repository for the manuscript:

> *Machine-Learning Prediction of In-Hospital Mortality in Critically Ill Patients with Hypoferremia: Multi-Cohort Development, External Evaluation, and Research Web Demonstration*

This repository is deposited as **auditable analysis source code**: the pipeline, inference code, model card, data dictionary, locked reference metrics, and a released 8-feature research model bundle. **Raw patient-level data are not redistributed.**

- **Repository:** https://github.com/linzixuan45/hypoferremia-icu-mortality  
- **Research calculator:** https://fe.mixaihub.top (not for clinical use)

To learn more about the underlying critical care databases, see [MIMIC](https://mimic.mit.edu) and the community [MIMIC Code Repository](https://github.com/MIT-LCP/mimic-code).

**User guide:** [docs/USER_GUIDE.md](docs/USER_GUIDE.md)

---

## What this repository provides

| Provided | Not provided |
|----------|--------------|
| Full analysis scripts (`scripts/`) and optional SQL (`sql/`) | MIMIC raw tables or patient identifiers |
| Released 8-feature model weights (`model_weights/`) | Pre-built `mimic_dataset.xlsx` |
| Local inference CLI (`inference.py`) | ETL from raw MIMIC to Excel |
| Model card, data dictionary, methods specs | Bit-exact guarantee of manuscript AUROC/tables |
| Locked aggregate reference metrics (`reference/`) | Chinese validation cohort files |
| Reviewer verification script (`verify_reproduction.py`) | |
| Online SHAP research calculator (Track B below) | |

Python ≥3.10 recommended.

---

## Access to data

Re-running the pipeline requires credentialed access to MIMIC on PhysioNet:

| Database | PhysioNet |
|----------|-----------|
| MIMIC-III | [mimiciii](https://physionet.org/content/mimiciii/) |
| MIMIC-IV | [mimiciv](https://physionet.org/content/mimiciv/) |

Access requires completion of required training and a data-use agreement. Place locally prepared feature tables at `data/mimic_dataset.xlsx` (format in [docs/preprocessing_excel.md](docs/preprocessing_excel.md) and [docs/mimic_excel_reproduction_guide.md](docs/mimic_excel_reproduction_guide.md)). Chinese geographic validation (F3/NH) requires additional local files under `data/external/` — see [DATA_AVAILABILITY.md](DATA_AVAILABILITY.md).

---

## Navigating this repository

| Path | Contents |
|------|----------|
| [`inference.py`](inference.py) | Single-patient / batch 28-day mortality probability (CLI) |
| [`model_weights/`](model_weights/) | Released 8-feature ensemble + imputer + scaler |
| [`reference/`](reference/) | Locked AUROC / cohort-count benchmark (no patient IDs) |
| [`scripts/`](scripts/) | End-to-end analysis pipeline (Python) |
| [`sql/`](sql/) | Optional SQL exports for charttime-level t₀ and severity scores |
| [`docs/`](docs/) | User guide, methods specs, data dictionary, Excel preprocessing |
| [`config/`](config/) | Non-patient metadata (e.g. LASSO feature list, column checklist) |
| [`data/README.md`](data/README.md) | Where to place local `mimic_dataset.xlsx` |

Pipeline outputs are written to `result/analysis/` (local only; gitignored).

### Documentation (language)

| Document | Language |
|----------|----------|
| README, MODEL_CARD, USER_GUIDE, preprocessing_excel, mimic_excel_reproduction_guide | English |
| FE1_spec.md, data_flow_cohorts.md | Chinese (methods); see [FE1_spec_en.md](docs/FE1_spec_en.md) for English summary |

### Analysis pipeline (`scripts/`)

| Script | Role |
|--------|------|
| [`run_pipeline.py`](scripts/run_pipeline.py) | Run the full Excel-based pipeline |
| [`validate_excel_input.py`](scripts/validate_excel_input.py) | Validate `mimic_dataset.xlsx` before analysis |
| [`verify_reproduction.py`](scripts/verify_reproduction.py) | Compare local manifest to `reference/manifest.json` |
| [`prepare_t0_labs_parquet.py`](scripts/prepare_t0_labs_parquet.py) | Build interim t₀ timing from Excel (`excel_derived_interim`) |
| [`build_t0_cohort.py`](scripts/build_t0_cohort.py) | Cohort filters, `outcome_28d`, train/test/val ID lists, `manifest.json` |
| [`train_models.py`](scripts/train_models.py) | Train 20/8-feature soft-voting models; Tables 2–6, S8–S9 |
| [`supplementary_analysis.py`](scripts/supplementary_analysis.py) | DCA, sensitivities, subgroups, SHAP Figure 7; Tables S6–S15 |
| [`benchmark_severity_scores.py`](scripts/benchmark_severity_scores.py) | Table 5 severity-score benchmark |
| [`build_table1_baseline.py`](scripts/build_table1_baseline.py) | Table 1 baseline characteristics |
| [`export_github_weights.py`](scripts/export_github_weights.py) | Export `model_weights/8_features_model.pkl` |
| [`verify_manifest.py`](scripts/verify_manifest.py) | Manifest ↔ table consistency checks |

`subgroup_analysis.py` is invoked by `supplementary_analysis.py`; no need to run it separately.

Further detail: [docs/preprocessing_excel.md](docs/preprocessing_excel.md) · [docs/data_flow_cohorts.md](docs/data_flow_cohorts.md)

### SQL extraction (`sql/`)

Optional upgrade when definitive charttime-level t₀ and APACHE/SAPS scores are available from PhysioNet SQL access. See [sql/README.md](sql/README.md).

| File | Purpose |
|------|---------|
| [`export_t0_cohort.sql`](sql/export_t0_cohort.sql) | Charttime-level t₀ → `data/mimic_t0_labs.parquet` |
| [`export_severity_at_t0.sql`](sql/export_severity_at_t0.sql) | SOFA / APACHE II / SAPS II at t₀ |

After SQL export, re-run from `build_t0_cohort.py`.

---

## Quick start

### Track A — Local probability (no MIMIC data required)

```bash
pip install -r requirements.txt
python inference.py
```

Outputs a 28-day mortality probability for the built-in demo case. Use `python inference.py --help` for JSON/CSV batch input.

### Track B — SHAP audit

- **Online (recommended):** https://fe.mixaihub.top — interactive probability + SHAP exploration.
- **Local Figure 7 (optional):** requires your own `data/mimic_dataset.xlsx`:

```bash
pip install -r requirements-optional.txt
python scripts/run_pipeline.py
```

### Track C — Reviewer verification (locked reference)

Locked aggregate metrics (no patient IDs): [reference/manifest.json](reference/manifest.json) · [reference/table2_3_performance.csv](reference/table2_3_performance.csv)

After a local reproduction (Track B), run:

```bash
python scripts/verify_reproduction.py
```

Compares AUROC and cohort counts against the locked reference (tolerance ±0.005 AUROC).

---

## Re-running the analysis pipeline

Requires a user-prepared `data/mimic_dataset.xlsx`. The default public path uses an Excel-derived t₀ proxy; metrics may differ slightly from the published manuscript. See [docs/preprocessing_excel.md](docs/preprocessing_excel.md) (Known limitations).

**One command:**

```bash
python scripts/validate_excel_input.py
python scripts/run_pipeline.py
python scripts/verify_reproduction.py
```

**Step by step:**

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

`run_pipeline.py` flags: `--skip-validate`, `--skip-extended`, `--skip-weights`, `--strict-validate`.

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

**Locked reference performance** (8-feature; see [reference/manifest.json](reference/manifest.json)):

| Cohort | AUROC |
|--------|-------|
| MIMIC-IV internal test | 0.796 |
| MIMIC-III external | 0.712 |

---

## Acknowledgement

If you use this repository, we ask that you:

1. Cite the accompanying manuscript (BibTeX below; also in [CITATION.bib](CITATION.bib)).
2. Cite the MIMIC database(s) you used, as described on PhysioNet: [MIMIC-III](https://physionet.org/content/mimiciii/) · [MIMIC-IV](https://physionet.org/content/mimiciv/).
3. Acknowledge use of the [MIMIC Code Repository](https://github.com/MIT-LCP/mimic-code) if you adopt its data-access or SQL workflow patterns.

```bibtex
@article{hypoferremia_icu_mortality,
  title   = {Machine-learning model for mortality risk stratification in ICU patients with functional hypoferremia},
  author  = {Li, Y. and others},
  journal = {[Journal name -- fill after acceptance]},
  volume  = {[Volume -- fill]},
  number  = {[Issue -- fill]},
  pages   = {[Pages -- fill]},
  year    = {[Year -- fill]},
  doi     = {[DOI -- fill]},
  note    = {Manuscript under revision at Scientific Reports. Accompanying code: https://github.com/linzixuan45/hypoferremia-icu-mortality}
}
```

Additional availability text: [CODE_AVAILABILITY.md](CODE_AVAILABILITY.md).

---

## Archive and citation

| Resource | Link |
|----------|------|
| GitHub | https://github.com/linzixuan45/hypoferremia-icu-mortality |
| Zenodo DOI | `[fill after release]` — see [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md) |
| Research demo | https://fe.mixaihub.top |

Recommended release tag: `v1.0.0`

---

## License / use

- **Code:** [MIT License](LICENSE)
- **Data:** MIMIC and local validation cohorts require separate authorized access; not redistributed here.
- **Use:** Research use only. **Do not use for clinical decision-making.**

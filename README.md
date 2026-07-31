# Hypoferremia ICU Mortality Risk Model

**Research use only. Not for clinical use.**

Code repository for the manuscript:

> *Mortality Risk Stratification Among Critically Ill Patients with Documented Hypoferremia: Multi-Cohort Development and Retrospective Evaluation*

This repository is deposited as **auditable analysis source code**: the pipeline, second-revision sensitivity analyses, inference code, model card, data dictionary, aggregate reference metrics, and a released 8-feature research model bundle. **Raw or derived patient-level data are not redistributed.**

- **Repository:** https://github.com/linzixuan45/hypoferremia-icu-mortality  
- **Research calculator:** https://fe.mixaihub.top (not for clinical use)

To learn more about the underlying critical care databases, see [MIMIC](https://mimic.mit.edu) and the community [MIMIC Code Repository](https://github.com/MIT-LCP/mimic-code).

**User guide:** [docs/USER_GUIDE.md](docs/USER_GUIDE.md)

---

## What this repository provides

| Provided | Not provided |
|----------|--------------|
| Analysis scripts from the prepared modeling table (`scripts/`) and optional timing templates (`sql/`) | MIMIC raw tables, patient identifiers, or raw-table-to-modeling-table ETL |
| Released 8-feature model weights (`model_weights/`) | Pre-built `mimic_dataset.xlsx` |
| Local inference CLI (`inference.py`) | Chinese validation cohort files |
| Local Gradio web demo (`webui.py`, `start.sh`) | Bit-exact guarantee of manuscript AUROC/tables |
| Model card, data dictionary, methods specs | Bit-exact guarantee of manuscript AUROC/tables |
| Locked and R2 aggregate reference metrics (`reference/`) | Chinese validation cohort files |
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
| [`webui.py`](webui.py) | Gradio research calculator with SHAP audit (local) |
| [`start.sh`](start.sh) | Launch local web demo (port 7788 by default) |
| [`src/inference.py`](src/inference.py) | Shared inference module for CLI and web |
| [`model_weights/`](model_weights/) | Released 8-feature ensemble + imputer + scaler |
| [`reference/`](reference/) | Locked benchmark plus R2 aggregate results (no patient IDs) |
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
| [`r2_supplementary_analyses.py`](scripts/r2_supplementary_analyses.py) | Corrected cohort flow, calibration, multiple-imputation, NIV, and iron-association analyses |
| [`validate_excel_input.py`](scripts/validate_excel_input.py) | Validate `mimic_dataset.xlsx` before analysis |
| [`verify_reproduction.py`](scripts/verify_reproduction.py) | Compare local manifest to `reference/manifest.json` |
| [`prepare_t0_labs_parquet.py`](scripts/prepare_t0_labs_parquet.py) | Legacy synthetic timing used for locked-result reproduction; not an observed t₀ |
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

- **Online:** https://fe.mixaihub.top — interactive probability + SHAP exploration.
- **Local web demo** (no MIMIC data required):

```bash
pip install -r requirements-web.txt
./start.sh
# or: python webui.py
```

Default: `http://0.0.0.0:7788`. Override with env vars `SERVER_PORT`, `SERVER_NAME`, `ROOT_PATH` (set empty to disable reverse-proxy prefix).

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

## Re-running the analyses

Requires a user-prepared, authorized `data/mimic_dataset.xlsx`. The workbook contains full-ICU-stay aggregates and does not contain charttime-level predictors. Therefore `_min`, `_max`, and `_mean` are interpreted as full-stay summaries, and the legacy synthetic t₀ must not be interpreted as an observed index time.

**Second-revision analyses:**

```bash
python scripts/validate_excel_input.py
python scripts/r2_supplementary_analyses.py
```

This writes patient-level intermediate predictions only under gitignored `result/r2_analysis/private/` and publishes non-patient aggregate tables and figures under [`reference/r2/`](reference/r2/).

**Locked R1 reproduction path:**

```bash
python scripts/validate_excel_input.py
python scripts/run_pipeline.py
python scripts/verify_reproduction.py
```

The locked path reproduces the previously reported model objects and metrics. It includes an explicitly labeled synthetic timing proxy solely for result comparability and is not the methodological basis for a real-time or admission-time prediction claim.

**Locked path, step by step:**

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
| **Cohort** | ICU patients with documented biochemical hypoferremia (serum iron <60 µg/dL) and ICU LOS ≥48 h |
| **Observation window** | Full ICU stay for `_min`, `_max`, and `_mean`; first recorded ICU value for `_1st` |
| **Available timed outcome** | In-hospital death within 28 days of hospital admission |
| **Model** | 8-feature soft-voting ensemble (XGBoost + Random Forest + Logistic Regression) |
| **Class balance** | `class_weight='balanced'` on MIMIC-IV development set |

**8 input features:** `platelet_mean`, `wbc_min`, `bun_min`, `pco2_max`, `creatinine_min`, `is_noninvasive_ventilator`, `spo2_min`, `platelet_1st` — all in model-native units (creatinine and BUN in **mg/dL**); see [docs/data_dictionary.md](docs/data_dictionary.md) and [MODEL_CARD.md](MODEL_CARD.md).

**Chinese cohort harmonization:** F3/NH creatinine (μmol/L→mg/dL, ÷88.4) and BUN (mmol/L urea→mg/dL, ×2.801) at load time (`scripts/external_cohort_data.py`).

**R2 eligibility-corrected performance:**

| Model and cohort | n | Events | AUROC |
|------------------|---:|-------:|------:|
| Locked 18-predictor model, MIMIC-IV internal test | 269 | 40 | 0.840 |
| Locked 18-predictor model, MIMIC-III after the stated ICU LOS ≥48 h filter | 799 | 140 | 0.705 |
| Reduced 8-feature model, MIMIC-IV internal test | 269 | 40 | 0.796 |
| Reduced 8-feature model, MIMIC-III after the stated ICU LOS ≥48 h filter | 799 | 140 | 0.715 |
| Reduced 8-feature model, F3 exploratory | 101 | 26 | 0.810 |
| Reduced 8-feature model, NH exploratory | 98 | 37 | 0.898 |

The previously locked MIMIC-III result used all 1,046 exported rows and did not actually enforce the manuscript's ICU LOS ≥48 h criterion. It is retained under `reference/` for audit history but is superseded by the corrected R2 evaluation in [`reference/r2/`](reference/r2/).

---

## Acknowledgement

If you use this repository, we ask that you:

1. Cite the accompanying manuscript (BibTeX below; also in [CITATION.bib](CITATION.bib)).
2. Cite the MIMIC database(s) you used, as described on PhysioNet: [MIMIC-III](https://physionet.org/content/mimiciii/) · [MIMIC-IV](https://physionet.org/content/mimiciv/).
3. Acknowledge use of the [MIMIC Code Repository](https://github.com/MIT-LCP/mimic-code) if you adopt its data-access or SQL workflow patterns.

```bibtex
@article{hypoferremia_icu_mortality,
  title   = {Mortality risk stratification among critically ill patients with documented hypoferremia: multi-cohort development and retrospective evaluation},
  author  = {Xie, Liangpeng and Zhang, Chang and Sheng, Jiaowen and Jiang, Linxuan and Xiao, Mingxuan and Xi, Yang},
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

Recommended second-revision release tag: `v1.1.0`

---

## License / use

- **Code:** [MIT License](LICENSE)
- **Data:** MIMIC and local validation cohorts require separate authorized access; not redistributed here.
- **Use:** Research use only. **Do not use for clinical decision-making.**

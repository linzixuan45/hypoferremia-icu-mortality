# Hypoferremia 8-Feature Research Model — Model Card

**NOT FOR CLINICAL USE.** Research demonstration and audit only.

## Intended use

- Retrospective, post hoc mortality-risk characterization among ICU patients with documented biochemical hypoferremia (serum iron <60 µg/dL)
- Model audit / SHAP exploration in research settings
- **Not** for real-time clinical decision support, treatment modification, surveillance escalation, or patient-facing use

## Model

- 8-feature soft-voting ensemble (XGBoost + Random Forest + Logistic Regression)
- Trained on the locked MIMIC-IV development cohort (`train_models.py`)
- Primary locked soft-voting ensemble uses balanced class weights where supported; random undersampling is sensitivity-only (Supp S9)
- KNN imputation (k=5) fit on MIMIC-IV training data only; applied without refitting to external cohorts

## Input features

| Feature | Description |
|---------|-------------|
| `platelet_mean` | Mean platelet count over the available ICU stay |
| `wbc_min` | Minimum WBC over the available ICU stay |
| `bun_min` | Minimum BUN over the available ICU stay (mg/dL) |
| `pco2_max` | Maximum PaCO₂ over the available ICU stay (mmHg) |
| `creatinine_min` | Minimum creatinine over the available ICU stay (mg/dL) |
| `is_noninvasive_ventilator` | Documented non-invasive ventilation during the available record (`1` = documented use; `0` = no documented use) |
| `spo2_min` | Minimum SpO₂ over the available ICU stay (%) |
| `platelet_1st` | First recorded platelet count during the ICU stay |

Chinese exploratory cohorts (F3/NH): laboratory values are harmonized to mg/dL at load time (creatinine ÷88.4; BUN ×2.801) before locked-model evaluation.

## Performance summary (8-feature reduced model)

| Cohort | n | Events | AUROC (95% CI) |
|--------|---|--------|----------------|
| MIMIC-IV internal test | 269 | 40 | 0.796 (0.718–0.874) |
| MIMIC-III corrected temporal evaluation (ICU LOS ≥48 h) | 799 | 140 | 0.715 |
| Third Xiangya (F3) exploratory | 101 | 26 | 0.810 (0.713–0.908) |
| Nanhua (NH) exploratory | 98 | 37 | 0.898 (0.835–0.961) |

## Development and evaluation cohorts

| Cohort | Role |
|--------|------|
| MIMIC-IV | Development (80% train / 20% internal test) |
| MIMIC-III | Non-training same-institution temporal evaluation after identical ICU LOS filtering (n=799) |
| Third Xiangya (F3) | Exploratory geographic evaluation |
| Nanhua (NH) | Exploratory geographic evaluation |

The LASSO panel retained 20 candidate predictors; the locked benchmark modeling matrix uses **18 variables** after prespecified consolidation (Methods).

## Known limitations

- The available Excel export has no charttime-level predictors; min/max/mean variables summarize the full ICU stay and preclude an admission-time or real-time interpretation
- The legacy t₀ variable is synthetic and is retained only for locked-result reproduction
- Serum iron alone does not identify absolute iron deficiency; ferritin/transferrin saturation not uniformly available
- Chinese cohorts (F3/NH) are exploratory geographic evaluations and do not have fully harmonized timing with MIMIC
- Cross-site KNN imputation may anchor external cohorts toward the MIMIC-IV training distribution
- Undocumented non-invasive ventilation was coded as zero in the locked model; 58.6% of the corrected MIMIC-III cohort lacked this field
- APACHE II / SAPS II benchmarks require full MIMIC SQL export
- Model probabilities require local prevalence context and recalibration outside derivation settings

## Research demonstration calculator

| Channel | Capability |
|---------|------------|
| **Local CLI** (`python inference.py`) | 28-day mortality **probability only** — `--demo`, `--json`, or `--csv` |
| **Local web** (`./start.sh` or `python webui.py`) | Probability + **SHAP audit** (research use only) |
| **Web calculator** (https://fe.mixaihub.top) | Same as local web demo (production deployment) |

SHAP explanations require `requirements-web.txt` (Gradio + SHAP). The base `requirements.txt` covers CLI inference only.

## Citation

Xie L, Zhang C, et al. *Scientific Reports* — Machine-learning model for mortality risk stratification in ICU patients with functional hypoferremia.

See [CITATION.bib](CITATION.bib) and [CODE_AVAILABILITY.md](CODE_AVAILABILITY.md).

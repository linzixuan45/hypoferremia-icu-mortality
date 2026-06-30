# Hypoferremia 8-Feature Research Model — Model Card

**NOT FOR CLINICAL USE.** Research demonstration and audit only.

## Intended use

- Retrospective risk stratification among ICU patients with documented biochemical hypoferremia compatible with functional iron restriction (serum iron < 60 µg/dL)
- Model audit / SHAP exploration in research settings
- **Not** for real-time clinical decision support, treatment modification, surveillance escalation, or patient-facing use

## Model

- 8-feature soft-voting ensemble (XGBoost + Random Forest + Logistic Regression)
- Trained on MIMIC-IV development cohort with t₀-proxy FE1 definition (`train_models.py`)
- Class imbalance handled via `class_weight='balanced'` (primary); random undersampling is sensitivity-only (Supp S9)
- KNN imputation (k=5) fit on MIMIC-IV training data only; applied without refitting to external cohorts

## Input features

| Feature | Description |
|---------|-------------|
| `platelet_mean` | Platelet mean to t₀ |
| `wbc_min` | WBC minimum to t₀ |
| `bun_min` | BUN minimum to t₀ (mg/dL) |
| `pco2_max` | PaCO₂ maximum to t₀ (mmHg) |
| `creatinine_min` | Creatinine minimum to t₀ (mg/dL) |
| `is_noninvasive_ventilator` | Non-invasive ventilation before t₀ (0/1) |
| `spo2_min` | SpO₂ minimum to t₀ (%) |
| `platelet_1st` | First platelet to t₀ |

See `docs/data_dictionary.md` for timing rules.

## Development and evaluation cohorts

| Cohort | Role |
|--------|------|
| MIMIC-IV | Development (80% train / 20% internal test) |
| MIMIC-III | Non-training same-institution external/temporal evaluation (n ≈ 1,046) |
| Third Xiangya (F3) | Exploratory geographic evaluation |
| Nanhua (NH) | Exploratory geographic evaluation |

The LASSO panel retained 20 candidate predictors; the locked benchmark modeling matrix uses **18 variables** after prespecified consolidation (Methods).

## Known limitations

- Excel t₀ proxy; residual temporal-leakage risk for aggregate min/max/mean without uniform charttime
- Serum iron alone does not identify absolute iron deficiency; ferritin/transferrin saturation not uniformly available
- Chinese cohorts (F3/NH) are exploratory geographic validation only (option β; not re-anchored to MIMIC t₀)
- Cross-site KNN imputation may anchor external cohorts toward the MIMIC-IV training distribution
- APACHE II / SAPS II benchmarks require full MIMIC SQL export
- Model probabilities require local prevalence context and recalibration outside derivation settings

## Research demonstration calculator

| Channel | Capability |
|---------|------------|
| **Local CLI** (`python inference.py`) | 28-day mortality **probability only** — `--demo`, `--json`, or `--csv` |
| **Web calculator** (https://k.mixaihub.top) | Probability + **SHAP audit** (research use only) |

SHAP explanations are available on the web demo only; the local CLI does not compute SHAP.

## Citation

Li Y, et al. *Scientific Reports* — Machine-learning model for mortality risk stratification in ICU patients with functional hypoferremia.

See [CITATION.bib](../CITATION.bib) and [CODE_AVAILABILITY.md](../CODE_AVAILABILITY.md).

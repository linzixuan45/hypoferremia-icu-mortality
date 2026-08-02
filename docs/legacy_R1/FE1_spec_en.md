# FE1 Methods Specification — Legacy R1 Proxy-t₀ Protocol

> Historical file: superseded by the Round 2 admission-anchored outcome and retrospective whole-ICU-stay analysis. Do not use this document to describe the current submission.

**Status:** finalized v1 (2026-06-18)  
**Full specification (Chinese):** [FE1_spec.md](FE1_spec.md)  
**Locked reference:** [reference/manifest.json](../reference/manifest.json)

---

## 1. Prediction task

Among ICU patients with **functional hypoferremia**, at **proxy t₀ (first hypoferremia episode)**, estimate the risk of **in-hospital death within 28 calendar days from t₀** using predictors observable at or before t₀.

---

## 2. Cohort inclusion (MIMIC-III / MIMIC-IV)

| Rule | Definition |
|------|------------|
| Age | 18–100 years |
| ICU stay | ≥ 48 h (`los_icu >= 2` days) |
| Hypoferremia | Serum iron < 60 µg/dL at least once |
| t₀ | Excel proxy (no iron charttime); pipeline writes `mimic_t0_labs.parquet` → manifest `t0_source=parquet` |
| MIMIC-IV | Development cohort; 80% train / 20% internal test |
| MIMIC-III | External validation only (n = 1,046); never merged into training |

---

## 3. t₀ proxy strata (Excel path)

| Stratum | Definition |
|---------|------------|
| Admission | `iron_1st < 60` µg/dL |
| Acquired | `iron_1st >= 60` (or missing) and `iron_min < 60` |
| Legacy sensitivity | Full-stay aggregates + admission-anchored 28-day outcome → Supp Table S10 |

---

## 4. Outcome

- **Label:** `hospital_expire_flag` within 28 days from t₀ (`outcome_28d_t0`)
- Primary analysis horizon differs from legacy sensitivity (admission-anchored 28 days)

---

## 5. Feature windows

| Model | Features |
|-------|----------|
| **8-feature (deployment)** | `platelet_mean`, `wbc_min`, `bun_min`, `pco2_max`, `creatinine_min`, `is_noninvasive_ventilator`, `spo2_min`, `platelet_1st` |
| **20-feature (primary)** | LASSO panel in [config/low_fe_lasso_feature.csv](../config/low_fe_lasso_feature.csv); `los_icu` → `los_icu_to_t0` in pipeline |

Conservative mapping: prefer `_1st` / `_min` over full-stay `_max` / `_mean` where applicable.

---

## 6. Training / validation split

| Set | Role | Locked n |
|-----|------|----------|
| MIMIC-IV train | Development (80%) | 1,075 |
| MIMIC-IV internal test | Internal validation (20%) | 269 |
| MIMIC-III external | Temporal external | 1,046 |
| F3 / NH | Geographic exploratory (option β) | optional |

---

## 7. Class imbalance

- **Primary:** `class_weight='balanced'`
- **Sensitivity:** random undersampling × 5 seeds (Supp Table S9)

---

## 8. Model

8-feature and 20-feature **soft-voting** ensembles (XGBoost + Random Forest + Logistic Regression). KNN imputation (k=5) fit on MIMIC-IV training data only.

---

## Reproduce

See [mimic_excel_reproduction_guide.md](mimic_excel_reproduction_guide.md) and run:

```bash
python scripts/run_pipeline.py
python scripts/verify_reproduction.py
```

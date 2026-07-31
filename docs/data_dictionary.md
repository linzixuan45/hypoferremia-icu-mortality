# Data dictionary — 8-feature hypoferremia model

| Feature | Description | Unit |
|---------|-------------|------|
| `platelet_mean` | Platelet count (mean to t₀) | 10⁹/L |
| `wbc_min` | White blood cell count (min to t₀) | 10⁹/L |
| `bun_min` | Blood urea nitrogen (min to t₀) | mg/dL |
| `pco2_max` | Partial pressure of CO₂ (max to t₀) | mmHg |
| `creatinine_min` | Serum creatinine (min to t₀) | mg/dL |
| `is_noninvasive_ventilator` | Non-invasive ventilation before t₀ (`1` = documented use; `0` = no documented use) | 0/1 |
| `spo2_min` | Peripheral oxygen saturation (min to t₀) | % |
| `platelet_1st` | First platelet measurement to t₀ | 10⁹/L |

**Chinese cohort harmonization (F3/NH):** before model input, `creatinine_min` is converted from μmol/L to mg/dL (÷88.4) and `bun_min` from mmol/L urea to mg/dL BUN (×2.801), matching the MIMIC-aligned model scale. See `scripts/external_cohort_data.py`.

**Web demo inputs** (`web/webui_low_fe.py`, https://fe.mixaihub.top): always enter creatinine and BUN in **mg/dL**.

Outcome (training): death within 28 calendar days from t₀ (`outcome_28d_t0`).

See `docs/FE1_spec.md` for full variable timing rules.

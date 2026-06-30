# Data dictionary — 8-feature hypoferremia model

| Feature | Description | Unit |
|---------|-------------|------|
| `platelet_mean` | Platelet count (mean to t₀) | 10⁹/L |
| `wbc_min` | White blood cell count (min to t₀) | 10⁹/L |
| `bun_min` | Blood urea nitrogen (min to t₀) | mg/dL |
| `pco2_max` | Partial pressure of CO₂ (max to t₀) | mmHg |
| `creatinine_min` | Serum creatinine (min to t₀) | mg/dL |
| `is_noninvasive_ventilator` | Non-invasive ventilation before t₀ | 0/1 |
| `spo2_min` | Peripheral oxygen saturation (min to t₀) | % |
| `platelet_1st` | First platelet measurement to t₀ | 10⁹/L |

Outcome (training): death within 28 calendar days from t₀ (`outcome_28d_t0`).

See `docs/FE1_spec.md` for full variable timing rules.

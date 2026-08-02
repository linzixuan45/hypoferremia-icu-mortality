# Data Dictionary — Post Hoc 8-Feature Derivative

| Feature | Round 2 interpretation | Unit |
|---|---|---|
| `platelet_mean` | Mean platelet count over the full ICU stay | 10⁹/L |
| `wbc_min` | Minimum white blood cell count over the full ICU stay | 10⁹/L |
| `bun_min` | Minimum blood urea nitrogen over the full ICU stay | mg/dL |
| `pco2_max` | Maximum PaCO₂ over the full ICU stay | mmHg |
| `creatinine_min` | Minimum creatinine over the full ICU stay | mg/dL |
| `is_noninvasive_ventilator` | Documented NIV use; not equivalent to confirmed physiological absence when 0 or missing | 0/1 |
| `spo2_min` | Minimum oxygen saturation over the full ICU stay | % |
| `platelet_1st` | First recorded platelet count during the ICU stay | 10⁹/L |

Chinese exploratory cohort values are harmonized to the MIMIC-aligned scale before evaluation: creatinine µmol/L to mg/dL by dividing by 88.4; urea mmol/L to BUN mg/dL by multiplying by 2.801.

Outcome: death in hospital within 28 days of hospital admission (`outcome_28d_admission`). Full-stay summaries may be outcome-proximal or extend beyond day 28, so the model is retrospective whole-stay risk stratification rather than admission-time prediction.

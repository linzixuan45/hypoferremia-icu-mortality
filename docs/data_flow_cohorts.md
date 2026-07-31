# Round 2 Cohort Data Flow

| Step / cohort | n | 28-day in-hospital events | Role |
|---|---:|---:|---|
| MIMIC-IV export before LOS filtering | 1,931 | — | Local audit input |
| MIMIC-IV ICU LOS ≥48 h | 1,568 | — | Screening set |
| MIMIC-IV meeting serum iron <60 µg/dL | 1,487 | 215 | Eligible analysis set |
| Complete locked 18-predictor matrix | 1,344 | 200 | Development/internal-test set |
| Excluded for locked-matrix missingness | 143 | 15 | Selection comparison |
| MIMIC-IV training | 1,075 | 160 | Model development |
| MIMIC-IV internal test | 269 | 40 | Internal evaluation |
| Corrected MIMIC-III ICU LOS ≥48 h | 799 | 140 | Same-institution temporal evaluation |
| F3 | 101 | 26 | Exploratory geographic evaluation |
| NH | 98 | 37 | Exploratory geographic evaluation |

The current outcome is in-hospital death within 28 days of hospital admission. Full-ICU `_min`, `_max`, and `_mean` summaries are retained, so the analysis is retrospective whole-stay risk stratification. The earlier n=1,046 MIMIC-III and proxy-t₀ workflow is historical and is not used for Round 2 conclusions.

Machine-readable aggregate flow is available in [`reference/r2/r2_patient_flow.csv`](../reference/r2/r2_patient_flow.csv).

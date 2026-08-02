# Round 2 Cohort Data Flow

| Cohort | Role | Current denominator |
|---|---|---:|
| MIMIC-IV eligible documented hypoferremia | Descriptive and sensitivity analyses | 1,487 (215 events) |
| MIMIC-IV complete locked matrix | Development/internal split | 1,344 (200 events) |
| MIMIC-IV training | Model fitting and preprocessing fit | 1,075 (160 events) |
| MIMIC-IV internal test | Locked internal evaluation | 269 (40 events) |
| Corrected MIMIC-III | Same-institution cross-database temporal sensitivity | 799 (140 events) |
| Third Xiangya | Exploratory geographic evaluation of post hoc reduced model | 101 (26 events) |
| Nanhua | Exploratory geographic evaluation of post hoc reduced model | 98 (37 events) |

The endpoint is death in hospital within 28 days of hospital admission. MIMIC-III is filtered with the same ICU length-of-stay ≥48 h criterion and is not described as independent external validation.

The historical R1 flow is retained at [legacy_R1/data_flow_cohorts.md](legacy_R1/data_flow_cohorts.md) for provenance only.

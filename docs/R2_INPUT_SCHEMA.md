# Prepared-Workbook Input Schema

The active workflow expects `data/mimic_dataset.xlsx` with sheets `mimic4_low_fe` and `mimic3_low_fe`. The workbook is controlled patient-level material and must not be committed.

Before analysis, run:

```bash
python scripts/validate_excel_input.py --report --strict
python scripts/run_r2_analysis.py
```

The validator checks required fields and feature names. Investigators must also verify units, coding, observation windows, and institutional governance.

Key semantics:

- `los_icu` is measured in days; eligibility requires at least 2 days.
- `iron_1st` and `iron_min` are measured in µg/dL; documented hypoferremia is <60 µg/dL.
- `hosp_survival_days` is measured from hospital admission and defines the available 28-day in-hospital endpoint together with `hospital_expire_flag`.
- `_1st` is the first recorded ICU-stay value.
- `_min`, `_max`, and `_mean` summarize the full ICU stay and may include outcome-proximal or post-day-28 measurements.
- `los_icu_to_t0` is a synthetic R1 proxy, not an observed laboratory timestamp.
- Blank treatment/documentation flags are interpreted only according to their stated source coding and must not be relabelled as confirmed physiological absence.

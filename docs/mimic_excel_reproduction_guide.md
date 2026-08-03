# MIMIC Prepared-Workbook Reproduction Guide — Round 2

## Scope

This repository reproduces the Round 2 analyses from an authorized prepared workbook. It does not claim a complete raw-database-to-workbook ETL. Credentialed users remain responsible for source access, extraction validity, units, coding, and governance.

## Setup

1. Place the authorized workbook at `data/mimic_dataset.xlsx`.
2. Confirm sheet and field semantics in [R2_INPUT_SCHEMA.md](R2_INPUT_SCHEMA.md).
3. Install `requirements-frozen.txt` where compatible.
4. Run the strict validator and orchestrator.

```bash
python scripts/validate_excel_input.py --report --strict
python scripts/run_r2_analysis.py
python scripts/verify_reproduction.py
pytest -q
```

## Expected cohort accounting

- MIMIC-IV: 1,568 after LOS ≥48 h; 1,487 with documented iron <60 µg/dL; 1,344 in the complete locked matrix; 1,075 training and 269 internal test.
- Corrected MIMIC-III temporal sensitivity: 799 admissions, 140 events.

If these denominators differ, do not silently continue. Check the source snapshot, units, duplicate handling, LOS filter, iron definition, and endpoint derivation before interpreting model metrics.

## Output boundary

Patient-level outputs, cohort IDs, predictions, and fitted objects remain under gitignored `result/` paths. Only aggregate, disclosure-reviewed outputs may be copied into `reference/r2/` for a public release.

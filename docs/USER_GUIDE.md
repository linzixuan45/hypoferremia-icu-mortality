# User Guide — Round 2 Research Workflow

## Data-free audit

```bash
pytest -q
```

This checks release identity, endpoint semantics, corrected denominators, ensemble parameters, aggregate outputs, and the absence of fitted or patient-level artifacts.

## Authorized full run

Place `data/mimic_dataset.xlsx` locally, then run:

```bash
python scripts/validate_excel_input.py --report --strict
python scripts/run_r2_analysis.py
python scripts/verify_reproduction.py
```

Core and supplementary patient-level intermediates remain under gitignored `result/` paths. Do not commit them.

## Research interface

Interface source is provided for audit. A fitted bundle is not public. Credentialed investigators may reconstruct it locally from authorized data. The interface is not for clinical use.

## Interpretation

- The endpoint is 28-day in-hospital death from hospital admission.
- Full-stay summaries make the model retrospective whole-stay risk stratification.
- MIMIC-III is a same-institution cross-database temporal sensitivity cohort.
- The 8-feature model is post hoc and does not replace the locked benchmark.
- SHAP describes the XGBoost component and is non-causal.

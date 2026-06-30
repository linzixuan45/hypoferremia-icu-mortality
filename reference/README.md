# Locked reference run

This directory holds **aggregate, non-patient-level** outputs from the FE1 locked analysis run (`fe1_v1_2026-06-18`).

Use it to verify that your local pipeline reproduction matches the published results.

## Files

| File | Purpose |
|------|---------|
| `manifest.json` | Locked cohort counts, AUROC metrics, FE1 version |
| `table2_3_performance.csv` | Table 2/3 summary (AUROC + 95% CI) |

## Compare your run

After `python scripts/run_pipeline.py`:

```bash
python scripts/verify_reproduction.py
```

## Tolerance

- AUROC metrics: ±0.005 vs `reference/manifest.json`
- Cohort counts: exact match for `mimic3_external` (1,046) and train/test split sizes

Patient-level cohort ID lists and prediction pickles remain under `result/analysis/` (local only, not redistributed).

# Research Interface Source

**Not for clinical use.**

The source illustrates mortality-probability and XGBoost-component SHAP rendering. A fitted model bundle is deliberately not distributed because the fitted KNN imputer retains training-row information.

Authorized investigators may reconstruct the protected local bundle by running:

```bash
python scripts/run_r2_analysis.py
```

The local interface must not be used for diagnosis, triage, treatment selection, or patient-facing decisions. The hosted demonstration at https://fe.mixaihub.top is also research-only and does not establish local calibration or clinical utility.

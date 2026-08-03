# Audited Software Environment

Round 2 release environment recorded on 2026-08-02:

- Python 3.12.13
- Windows 11, CPU-only
- exact Python package versions: `requirements-frozen.txt`
- random state 42 where applicable

The manuscript-locked discrimination estimates were reproduced with
`scikit-learn==1.8.0` and `xgboost==3.2.0`. XGBoost 3.3.0 produced small but
detectable AUROC drift despite identical rows, preprocessing, parameters, and
random state; it is therefore outside the audited numerical environment.

The frozen file records the audited environment. It does not guarantee wheel availability on every operating system or future Python version.

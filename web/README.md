# Web research demo (Figure 8)

**Not for clinical use.** Deploys the 8-feature ensemble from `model_weights/8_features_model.pkl`.

## Run locally

```bash
pip install -r ../requirements-optional.txt
python scripts/export_github_weights.py   # if bundle missing
cd web && python3 webui_low_fe.py
```

Default demo inputs match manuscript units (creatinine/BUN in **mg/dL**).

## Production

Server script: `start.sh` (port 7788, root path `https://fe.mixaihub.top`).

After code update, redeploy and re-screenshot **Figure 8** for the manuscript.

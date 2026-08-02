"""Web demo inference: 8-feature ensemble bundle + SHAP on XGB base learner."""
from __future__ import annotations

import pickle
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
WEIGHTS_PATH = ROOT / "model_weights" / "8_features_model.pkl"

FEATURES = [
    "platelet_mean",
    "wbc_min",
    "bun_min",
    "pco2_max",
    "creatinine_min",
    "is_noninvasive_ventilator",
    "spo2_min",
    "platelet_1st",
]


class WebInference:
    def __init__(self, weights_path: Path | None = None):
        path = weights_path or WEIGHTS_PATH
        if not path.exists():
            raise FileNotFoundError(
                f"Protected local model bundle not found: {path}\n"
                "The public release intentionally excludes fitted objects. Reconstruct "
                "the bundle locally from authorized data before starting the interface.\n"
                "Run: python scripts/export_github_weights.py"
            )
        with open(path, "rb") as f:
            bundle = pickle.load(f)
        self.model = bundle["model"]
        self.imputer = bundle["imputer"]
        self.scaler = bundle["scaler"]
        self.features = list(bundle.get("features", FEATURES))
        self.threshold = float(bundle.get("threshold", 0.5))
        self.xgb = self.model.named_estimators_["xgb"]

    def preprocess(self, row: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
        missing = [k for k in self.features if k not in row]
        if missing:
            raise KeyError(f"Missing features: {missing}")
        df = pd.DataFrame([{k: row[k] for k in self.features}])
        df["is_noninvasive_ventilator"] = int(float(row["is_noninvasive_ventilator"]) >= 0.5)
        x_raw = df[self.features]
        x_imp = pd.DataFrame(self.imputer.transform(x_raw), columns=self.features)
        x_scaled = pd.DataFrame(self.scaler.transform(x_imp), columns=self.features)
        return x_raw, x_scaled

    def predict_proba(self, row: dict) -> float:
        _, x_scaled = self.preprocess(row)
        return float(self.model.predict_proba(x_scaled)[0, 1])

    def predict_label(self, row: dict) -> tuple[float, int]:
        prob = self.predict_proba(row)
        return prob, int(prob >= self.threshold)

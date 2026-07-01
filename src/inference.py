"""Shared 8-feature hypoferremia inference for CLI and web demo."""
from __future__ import annotations

import pickle
from pathlib import Path

import pandas as pd

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

ROOT = Path(__file__).resolve().parent.parent
WEIGHTS_PATH = ROOT / "model_weights" / "8_features_model.pkl"

_BUNDLE = None


def load_bundle(weights_path: Path | None = None) -> dict:
    global _BUNDLE
    path = weights_path or WEIGHTS_PATH
    if _BUNDLE is not None and weights_path is None:
        return _BUNDLE
    if not path.exists():
        raise FileNotFoundError(
            f"Model weights not found: {path}\n"
            "This repository ships 8_features_model.pkl for Quick Start. "
            "If missing, re-export with: python scripts/export_github_weights.py "
            "(after running the analysis pipeline). See README.md."
        )
    with open(path, "rb") as f:
        bundle = pickle.load(f)
    if weights_path is None:
        _BUNDLE = bundle
    return bundle


class Inference:
    """Ensemble inference with imputer, scaler, and XGBoost for SHAP."""

    def __init__(self, weights_path: Path | None = None):
        bundle = load_bundle(weights_path)
        self.model = bundle["model"]
        self.imputer = bundle["imputer"]
        self.scaler = bundle["scaler"]
        self.features = list(bundle.get("features", FEATURES))
        self.threshold = float(bundle["threshold"])
        self.xgb = self.model.named_estimators_["xgb"]

    def _to_frame(self, row: dict) -> pd.DataFrame:
        missing = [k for k in self.features if k not in row]
        if missing:
            raise KeyError(f"Missing feature keys: {missing}")
        df = pd.DataFrame([{k: row[k] for k in self.features}])
        df["is_noninvasive_ventilator"] = int(
            float(row["is_noninvasive_ventilator"]) >= 0.5
        )
        return df

    def preprocess(self, row: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
        df = self._to_frame(row)
        x_raw = df[self.features].copy()
        x_imp = pd.DataFrame(
            self.imputer.transform(df[self.features]), columns=self.features
        )
        x_scaled = pd.DataFrame(
            self.scaler.transform(x_imp), columns=self.features
        )
        return x_raw, x_scaled

    def predict_proba(self, row: dict) -> float:
        _, x_scaled = self.preprocess(row)
        return float(self.model.predict_proba(x_scaled)[0, 1])


def predict_proba(row: dict, weights_path: Path | None = None) -> float:
    return Inference(weights_path).predict_proba(row)

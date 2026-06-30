#!/usr/bin/env python3
"""8-feature research model inference for hypoferremia (research demo)."""
from __future__ import annotations

import argparse
import json
import pickle
import sys
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

ROOT = Path(__file__).resolve().parent
WEIGHTS_PATH = ROOT / "model_weights" / "8_features_model.pkl"

_BUNDLE = None


def load_bundle():
    global _BUNDLE
    if _BUNDLE is not None:
        return _BUNDLE
    if not WEIGHTS_PATH.exists():
        raise FileNotFoundError(
            f"Model weights not found: {WEIGHTS_PATH}\n"
            "This repository ships 8_features_model.pkl for Quick Start. "
            "If missing, re-export with: python scripts/export_github_weights.py "
            "(after running the analysis pipeline). See README.md."
        )
    with open(WEIGHTS_PATH, "rb") as f:
        _BUNDLE = pickle.load(f)
    return _BUNDLE


def predict_proba(row: dict) -> float:
    bundle = load_bundle()
    model = bundle["model"]
    imp = bundle["imputer"]
    scaler = bundle["scaler"]
    missing = [k for k in FEATURES if k not in row]
    if missing:
        raise KeyError(f"Missing feature keys: {missing}")
    df = pd.DataFrame([{k: row[k] for k in FEATURES}])
    df["is_noninvasive_ventilator"] = int(float(row["is_noninvasive_ventilator"]) >= 0.5)
    X = pd.DataFrame(imp.transform(df[FEATURES]), columns=FEATURES)
    Xs = pd.DataFrame(scaler.transform(X), columns=FEATURES)
    return float(model.predict_proba(Xs)[0, 1])


def _demo_row() -> dict:
    return {
        "platelet_mean": 180.0,
        "wbc_min": 5.0,
        "bun_min": 15.0,
        "pco2_max": 42.0,
        "creatinine_min": 0.9,
        "is_noninvasive_ventilator": 0,
        "spo2_min": 95.0,
        "platelet_1st": 175.0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="8-feature hypoferremia 28-day mortality probability (research use only)"
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--demo", action="store_true", help="Run built-in demo case (default)")
    group.add_argument("--json", type=str, help="Single patient as JSON object")
    group.add_argument("--csv", type=Path, help="Batch CSV with 8 feature columns")
    args = parser.parse_args()

    try:
        if args.json:
            row = json.loads(args.json)
            p = predict_proba(row)
            print(f"28-day mortality probability: {p:.3f}")
        elif args.csv:
            df = pd.read_csv(args.csv)
            missing = [c for c in FEATURES if c not in df.columns]
            if missing:
                print(f"CSV missing columns: {missing}", file=sys.stderr)
                sys.exit(1)
            for i, r in df.iterrows():
                p = predict_proba(r.to_dict())
                print(f"row {i}: 28-day mortality probability: {p:.3f}")
        else:
            p = predict_proba(_demo_row())
            print(f"28-day mortality probability: {p:.3f}")
    except FileNotFoundError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

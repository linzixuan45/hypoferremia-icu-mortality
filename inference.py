#!/usr/bin/env python3
"""8-feature research model inference for hypoferremia (research demo)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

from src.inference import FEATURES, predict_proba

ROOT = Path(__file__).resolve().parent


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

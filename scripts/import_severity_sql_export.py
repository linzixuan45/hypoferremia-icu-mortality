#!/usr/bin/env python3
"""Import co-author SQL CSV export → data/mimic_severity_scores.parquet."""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "mimic_severity_scores.parquet"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True, type=Path)
    args = ap.parse_args()
    df = pd.read_csv(args.csv)
    df["source"] = "mimic_sql"
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT, index=False)
    print(f"Wrote {OUT} ({len(df)} rows)")


if __name__ == "__main__":
    main()

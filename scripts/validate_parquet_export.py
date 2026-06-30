#!/usr/bin/env python3
"""Validate J.1/J.2 parquet exports before pipeline v2."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
T0 = ROOT / "data" / "mimic_t0_labs.parquet"
SEV = ROOT / "data" / "mimic_severity_scores.parquet"


def main() -> int:
    ok = True
    if not T0.exists():
        print("FAIL: missing", T0)
        return 1
    t0 = pd.read_parquet(T0)
    req = {"stay_id", "t0_charttime", "hypoferremia_stratum"}
    missing = req - set(t0.columns)
    if missing:
        print("FAIL: mimic_t0_labs missing columns", missing)
        ok = False
    nn = t0["t0_charttime"].notna().mean()
    print(f"t0_labs: n={len(t0)} t0_charttime non-null={nn:.1%} source={t0.get('source', pd.Series(['?'])).iloc[0]}")
    if nn < 0.95:
        print("WARN: t0_charttime non-null rate < 95%")

    if SEV.exists():
        sev = pd.read_parquet(SEV)
        ap = sev["apache_ii"].notna().sum() if "apache_ii" in sev.columns else 0
        sa = sev["saps_ii"].notna().sum() if "saps_ii" in sev.columns else 0
        src = sev["source"].iloc[0] if "source" in sev.columns else "unknown"
        print(f"severity: n={len(sev)} apache_ii={ap} saps_ii={sa} source={src}")
        if ap == 0 or sa == 0:
            print("WARN: APACHE/SAPS not populated — Table 5 will be SOFA-only until SQL")
    else:
        print("WARN: missing", SEV)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

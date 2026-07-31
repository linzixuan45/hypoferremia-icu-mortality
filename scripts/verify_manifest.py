#!/usr/bin/env python3
"""Manifest and table consistency guards for the historical R1 FE1 locked run.

Current Round 2 checks are implemented in tests/test_r2_revision.py and use
reference/r2/r2_analysis_manifest.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "result" / "analysis"
TABLES = OUT / "tables"


def check_manifest() -> list[str]:
    errors: list[str] = []
    manifest_path = OUT / "manifest.json"
    if not manifest_path.exists():
        return ["manifest.json missing — run build_t0_cohort.py and train_models.py"]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    metrics = manifest.get("metrics", {})
    required = [
        "mimic4_test_8f_auroc",
        "mimic3_external_8f_auroc",
        "mimic4_test_20f_auroc",
        "mimic3_external_20f_auroc",
    ]
    for key in required:
        if key not in metrics:
            errors.append(f"manifest.metrics missing {key}")

    t23 = TABLES / "table2_3_performance.csv"
    if t23.exists() and metrics:
        df = pd.read_csv(t23)
        for feat_tag, m4_key, m3_key in [
            ("8-feature", "mimic4_test_8f_auroc", "mimic3_external_8f_auroc"),
            ("20-feature", "mimic4_test_20f_auroc", "mimic3_external_20f_auroc"),
        ]:
            m4_row = df[(df["Model"] == feat_tag) & (df["Cohort"].str.contains("MIMIC-IV"))]
            m3_row = df[(df["Model"] == feat_tag) & (df["Cohort"].str.contains("MIMIC-III"))]
            if len(m4_row) and abs(float(m4_row["AUROC"].iloc[0]) - float(metrics[m4_key])) > 0.005:
                errors.append(f"Table 2/3 {feat_tag} MIMIC-IV AUROC != manifest {m4_key}")
            if len(m3_row) and abs(float(m3_row["AUROC"].iloc[0]) - float(metrics[m3_key])) > 0.005:
                errors.append(f"Table 2/3 {feat_tag} MIMIC-III AUROC != manifest {m3_key}")

    counts = manifest.get("cohort_counts", {})
    if counts.get("mimic3_external") and counts["mimic3_external"] != 1046:
        errors.append(
            "Historical R1 mimic3_external count changed unexpectedly; "
            "current R2 n=799 is stored in reference/r2/r2_analysis_manifest.json"
        )

    for artifact in (
        "table_s6a_lasso20_missingness",
        "table_s7_missingness",
        "table_s9_imbalance",
        "table_s10_legacy",
    ):
        rel = manifest.get("artifacts", {}).get(artifact)
        if rel and not (ROOT / rel).exists():
            errors.append(f"manifest artifact missing on disk: {rel}")

    s6a = TABLES / "table_s6a_lasso20_missingness.csv"
    if s6a.exists():
        s6 = pd.read_csv(s6a)
        if len(s6) != 60:
            errors.append(f"S6A expected 60 rows, got {len(s6)}")
        if "po2_max" in set(s6["Variable"]):
            errors.append("po2_max must not appear in S6A")

    return errors


def main() -> int:
    errors = check_manifest()
    if errors:
        print("verify_manifest FAILED:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("verify_manifest OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())

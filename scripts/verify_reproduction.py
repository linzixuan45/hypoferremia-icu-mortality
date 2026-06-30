#!/usr/bin/env python3
"""Compare local pipeline output against the locked reference manifest."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOCAL = ROOT / "result" / "analysis" / "manifest.json"
REFERENCE = ROOT / "reference" / "manifest.json"

AUROC_KEYS = (
    "mimic4_test_8f_auroc",
    "mimic3_external_8f_auroc",
    "mimic4_test_20f_auroc",
    "mimic3_external_20f_auroc",
)
COUNT_KEYS = (
    "mimic4_train",
    "mimic4_internal_test",
    "mimic3_external",
)
AUROC_TOL = 0.005


def main() -> None:
    if not REFERENCE.exists():
        print(f"Reference manifest missing: {REFERENCE}", file=sys.stderr)
        sys.exit(1)
    if not LOCAL.exists():
        print(
            f"Local manifest missing: {LOCAL}\n"
            "Run the analysis pipeline first:\n"
            "  python scripts/validate_excel_input.py\n"
            "  python scripts/run_pipeline.py",
            file=sys.stderr,
        )
        sys.exit(1)

    ref = json.loads(REFERENCE.read_text(encoding="utf-8"))
    local = json.loads(LOCAL.read_text(encoding="utf-8"))
    errors: list[str] = []

    ref_metrics = ref.get("metrics", {})
    local_metrics = local.get("metrics", {})
    for key in AUROC_KEYS:
        if key not in local_metrics:
            errors.append(f"local metrics missing {key}")
            continue
        if key not in ref_metrics:
            continue
        diff = abs(float(local_metrics[key]) - float(ref_metrics[key]))
        if diff > AUROC_TOL:
            errors.append(
                f"{key}: local={local_metrics[key]:.6f} ref={ref_metrics[key]:.6f} (diff={diff:.6f})"
            )

    ref_counts = ref.get("cohort_counts", {})
    local_counts = local.get("cohort_counts", {})
    for key in COUNT_KEYS:
        if local_counts.get(key) != ref_counts.get(key):
            errors.append(
                f"cohort_counts.{key}: local={local_counts.get(key)} ref={ref_counts.get(key)}"
            )

    if errors:
        print("verify_reproduction FAIL:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        sys.exit(1)

    print("verify_reproduction OK")
    print(f"  FE1: {local.get('fe1_version')} | t0_source: {local.get('t0_source')}")
    for key in AUROC_KEYS:
        if key in local_metrics:
            print(f"  {key}: {local_metrics[key]:.4f}")


if __name__ == "__main__":
    main()

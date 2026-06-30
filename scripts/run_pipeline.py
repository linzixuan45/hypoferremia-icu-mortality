#!/usr/bin/env python3
"""Run the Excel-based analysis pipeline end-to-end."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = Path(__file__).resolve().parent


def run_step(name: str, script: str, extra_args: list[str] | None = None) -> None:
    cmd = [sys.executable, str(SCRIPTS / script)] + (extra_args or [])
    print(f"[step] {name} ...", flush=True)
    result = subprocess.run(cmd, cwd=ROOT)
    if result.returncode != 0:
        print(f"[step] {name} FAIL (exit {result.returncode})", flush=True)
        sys.exit(result.returncode)
    print(f"[step] {name} OK", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Excel-based analysis pipeline")
    parser.add_argument("--skip-validate", action="store_true")
    parser.add_argument("--skip-extended", action="store_true")
    parser.add_argument("--skip-weights", action="store_true")
    parser.add_argument("--strict-validate", action="store_true", help="Pass --strict to validate_excel_input.py")
    args = parser.parse_args()

    if not args.skip_validate:
        validate_args = ["--report"]
        if args.strict_validate:
            validate_args.append("--strict")
        run_step("validate_excel_input", "validate_excel_input.py", validate_args)

    run_step("prepare_t0_labs_parquet", "prepare_t0_labs_parquet.py")
    run_step("build_t0_cohort", "build_t0_cohort.py")
    run_step("train_models", "train_models.py")

    if not args.skip_extended:
        run_step("supplementary_analysis", "supplementary_analysis.py")
        run_step("benchmark_severity_scores", "benchmark_severity_scores.py")

    run_step("build_table1_baseline", "build_table1_baseline.py")

    if not args.skip_weights:
        run_step("export_github_weights", "export_github_weights.py")

    print("[pipeline] complete", flush=True)


if __name__ == "__main__":
    main()

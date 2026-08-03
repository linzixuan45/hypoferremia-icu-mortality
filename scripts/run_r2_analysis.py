#!/usr/bin/env python3
"""Run the active prepared-table Round 2 workflow without silent partial success."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = Path(__file__).resolve().parent


def run(script: str, *args: str) -> None:
    command = [sys.executable, str(SCRIPTS / script), *args]
    print(f"[R2] {' '.join(command)}", flush=True)
    completed = subprocess.run(command, cwd=ROOT)
    if completed.returncode:
        raise SystemExit(f"[R2] required step failed: {script} (exit {completed.returncode})")


def require_outputs() -> None:
    required = [
        ROOT / "result" / "analysis" / "manifest.json",
        ROOT / "result" / "analysis" / "tables" / "table2_3_performance.csv",
        ROOT / "result" / "r2_analysis" / "tables" / "r2_patient_flow.csv",
        ROOT / "result" / "r2_analysis" / "tables" / "r2_standard_calibration_metrics.csv",
        ROOT / "result" / "r2_analysis" / "tables" / "r2_niv_exclusion_sensitivity.csv",
        ROOT / "result" / "r2_analysis" / "tables" / "r2_iron_adjusted_effect.csv",
        ROOT / "result" / "r2_analysis" / "tables" / "r2_iron_incremental_value.csv",
    ]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.is_file()]
    if missing:
        raise SystemExit("[R2] required outputs are missing:\n- " + "\n- ".join(missing))


def main() -> None:
    run("validate_excel_input.py", "--report", "--strict")
    run("run_pipeline.py")
    run("r2_supplementary_analyses.py")
    require_outputs()
    print("[R2] complete: core and supplementary outputs are present", flush=True)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Validate mimic_dataset.xlsx before running the analysis pipeline."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA = ROOT / "data" / "mimic_dataset.xlsx"
DEFAULT_REPORT = ROOT / "result" / "analysis" / "reports" / "excel_validation.json"

REQUIRED_SHEETS = ("mimic3_low_fe", "mimic4_low_fe")

CORE_COLUMNS = (
    "subject_id",
    "hospital_expire_flag",
    "admission_age",
    "los_icu",
    "iron_1st",
    "iron_min",
)

FEAT8 = (
    "platelet_mean",
    "wbc_min",
    "bun_min",
    "pco2_max",
    "creatinine_min",
    "is_noninvasive_ventilator",
    "spo2_min",
    "platelet_1st",
)

OUTCOME_COLS = ("hosp_survival_days", "icu_survival_days")


def _id_columns(df: pd.DataFrame) -> list[str]:
    return [
        c
        for c in df.columns
        if any(x in c.lower() for x in ("subject", "hadm", "stay", "icustay"))
    ]


def _time_columns(df: pd.DataFrame) -> list[str]:
    return [
        c
        for c in df.columns
        if any(x in c.lower() for x in ("time", "date", "charttime"))
        and "chartevents" not in c.lower()
    ]


def _severity_columns(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if any(x in c.lower() for x in ("sofa", "apache", "saps"))]


def validate_sheet(name: str, df: pd.DataFrame, *, strict: bool) -> dict:
    cols = set(df.columns)
    missing_core = [c for c in CORE_COLUMNS if c not in cols]
    missing_feat8 = [c for c in FEAT8 if c not in cols]
    has_outcome_time = any(c in cols for c in OUTCOME_COLS)

    id_cols = _id_columns(df)
    dup_ids = []
    if "icustay_id" in cols:
        dup_ids = df["icustay_id"].duplicated().sum()
    elif "subject_id" in cols:
        dup_ids = df["subject_id"].duplicated().sum()

    errors: list[str] = []
    warnings: list[str] = []

    if len(df) == 0:
        errors.append(f"{name}: empty sheet")
    if missing_core:
        msg = f"{name}: missing core columns: {missing_core}"
        if strict:
            errors.append(msg)
        else:
            warnings.append(msg)
    if missing_feat8:
        warnings.append(f"{name}: missing 8-feature columns: {missing_feat8}")
    if not has_outcome_time:
        warnings.append(
            f"{name}: no hosp_survival_days or icu_survival_days "
            "(the 28-day in-hospital outcome from admission may be coarse)"
        )
    if dup_ids:
        warnings.append(f"{name}: {int(dup_ids)} duplicate ID rows detected")

    return {
        "sheet": name,
        "n_rows": len(df),
        "n_columns": len(cols),
        "id_columns": id_cols,
        "timestamp_columns": _time_columns(df),
        "severity_columns": _severity_columns(df),
        "missing_core": missing_core,
        "missing_feat8": missing_feat8,
        "has_outcome_time_column": has_outcome_time,
        "duplicate_id_rows": int(dup_ids),
        "errors": errors,
        "warnings": warnings,
    }


def run_validation(data_path: Path, *, strict: bool) -> dict:
    if not data_path.exists():
        guide = ROOT / "docs" / "mimic_excel_reproduction_guide.md"
        hint = (
            f"Place your MIMIC export at {data_path}. "
            f"See {guide.relative_to(ROOT)} and data/README.md for required sheets and columns."
        )
        print(hint, file=sys.stderr)
        return {
            "ok": False,
            "data_path": str(data_path),
            "errors": [f"file not found: {data_path}"],
            "warnings": [],
            "sheets": [],
            "hint": hint,
        }

    xl = pd.ExcelFile(data_path)
    missing_sheets = [s for s in REQUIRED_SHEETS if s not in xl.sheet_names]
    if missing_sheets:
        return {
            "ok": False,
            "data_path": str(data_path),
            "errors": [f"missing required sheets: {missing_sheets}"],
            "warnings": [],
            "sheets": [],
            "available_sheets": xl.sheet_names,
        }

    sheet_reports = []
    all_errors: list[str] = []
    all_warnings: list[str] = []

    for sheet in REQUIRED_SHEETS:
        df = pd.read_excel(data_path, sheet_name=sheet)
        rep = validate_sheet(sheet, df, strict=strict)
        sheet_reports.append(rep)
        all_errors.extend(rep["errors"])
        all_warnings.extend(rep["warnings"])

    if "icustay_id" not in pd.read_excel(data_path, sheet_name="mimic3_low_fe", nrows=1).columns:
        all_warnings.append("mimic3_low_fe: icustay_id absent; pipeline falls back to subject_id")

    m4_rep = next(r for r in sheet_reports if r["sheet"] == "mimic4_low_fe")
    has_charttime = bool(m4_rep["timestamp_columns"])
    if not has_charttime:
        all_warnings.append(
            "No charttime-level columns in Excel; use prepare_t0_labs_parquet.py (excel_derived_interim) or SQL export"
        )

    ok = len(all_errors) == 0
    return {
        "ok": ok,
        "data_path": str(data_path),
        "strict": strict,
        "errors": all_errors,
        "warnings": all_warnings,
        "sheets": sheet_reports,
        "available_sheets": xl.sheet_names,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate mimic_dataset.xlsx for analysis pipeline")
    parser.add_argument("--data-path", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--strict", action="store_true", help="Treat missing core columns as errors")
    parser.add_argument("--report", action="store_true", help="Write JSON report under result/analysis/reports/")
    args = parser.parse_args()

    report = run_validation(args.data_path, strict=args.strict)
    print(json.dumps(report, indent=2))

    if args.report:
        out = DEFAULT_REPORT
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"Wrote {out}", file=sys.stderr)

    sys.exit(0 if report["ok"] else 1)


if __name__ == "__main__":
    main()

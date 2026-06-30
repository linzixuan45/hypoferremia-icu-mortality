#!/usr/bin/env python3
"""
Build data/mimic_t0_labs.parquet from Excel when MIMIC SQL export is unavailable.

Co-authors with PhysioNet access should replace this file by running:
  sql/export_t0_cohort.sql

This interim export enables pipeline v2 (t0_source=parquet) using proxy t₀ timing
derived from iron_1st / iron_min and los_icu.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "mimic_dataset.xlsx"
OUT = ROOT / "data" / "mimic_t0_labs.parquet"
BASE_TS = pd.Timestamp("2000-01-01")
IRON_THRESHOLD = 60.0


def _stratum(row: pd.Series) -> str:
    iron_1st = pd.to_numeric(row.get("iron_1st", np.nan), errors="coerce")
    iron_min = pd.to_numeric(row.get("iron_min", np.nan), errors="coerce")
    if pd.notna(iron_1st) and iron_1st < IRON_THRESHOLD:
        return "admission"
    if pd.notna(iron_min) and iron_min < IRON_THRESHOLD:
        return "acquired"
    return "unknown"


def _hours_to_t0(row: pd.Series) -> float:
    iron_1st = pd.to_numeric(row.get("iron_1st", np.nan), errors="coerce")
    los_h = float(pd.to_numeric(row.get("los_icu", 1), errors="coerce")) * 24.0
    if pd.notna(iron_1st) and iron_1st < IRON_THRESHOLD:
        return 0.0
    return float(min(los_h * 12.0, los_h * 24.0) / 24.0 * 24.0)


def sheet_to_labs(df: pd.DataFrame, id_col: str) -> pd.DataFrame:
    rows = []
    for _, r in df.iterrows():
        sid = r.get(id_col)
        if pd.isna(sid):
            continue
        hours = _hours_to_t0(r)
        t0 = BASE_TS + pd.Timedelta(hours=hours)
        first_iron = BASE_TS + pd.Timedelta(hours=min(6.0, hours))
        rows.append(
            {
                "stay_id": int(sid) if id_col != "subject_id" else int(sid),
                "subject_id": int(r["subject_id"]) if "subject_id" in r.index else int(sid),
                "icu_intime": BASE_TS,
                "t0_charttime": t0,
                "first_iron_lab_charttime": first_iron,
                "iron_at_t0": float(
                    pd.to_numeric(r.get("iron_1st", r.get("iron_min", np.nan)), errors="coerce")
                ),
                "hypoferremia_stratum": _stratum(r),
                "hours_icu_to_t0": hours,
                "source": "excel_derived_interim",
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    m3 = pd.read_excel(DATA_PATH, sheet_name="mimic3_low_fe")
    m4 = pd.read_excel(DATA_PATH, sheet_name="mimic4_low_fe")
    id_m3 = "icustay_id" if "icustay_id" in m3.columns else "subject_id"
    id_m4 = "subject_id"
    labs = pd.concat([sheet_to_labs(m3, id_m3), sheet_to_labs(m4, id_m4)], ignore_index=True)
    labs = labs.drop_duplicates(subset=["stay_id"], keep="first")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    labs.to_parquet(OUT, index=False)
    print(f"Wrote {OUT} ({len(labs)} rows, source=excel_derived_interim)")
    print("Replace with SQL export from export_t0_cohort.sql when available.")


if __name__ == "__main__":
    main()

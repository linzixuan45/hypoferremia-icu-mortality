#!/usr/bin/env python3
"""Supplementary Table S2/S3 baseline stats for F3/NH (harmonized units)."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

SCRIPTS = Path(__file__).resolve().parent
ROOT = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))

from external_cohort_data import load_corrected_f3_feature_table, load_corrected_nh_feature_table

OUT = ROOT / "result" / "analysis" / "tables"
LABEL = "hospital_expire_flag"


def _fmt_median_iqr(s: pd.Series) -> str:
    s = pd.to_numeric(s, errors="coerce").dropna()
    if s.empty:
        return "—"
    q1, med, q3 = s.quantile([0.25, 0.5, 0.75])
    return f"{med:.2g} ({q1:.2g}–{q3:.2g}) (n={len(s)})"


def _fmt_n_pct(n: int, total: int) -> str:
    pct = 100.0 * n / total if total else 0.0
    return f"{n} ({pct:.1f})"


def _p_continuous(a: pd.Series, b: pd.Series) -> str:
    a = pd.to_numeric(a, errors="coerce").dropna()
    b = pd.to_numeric(b, errors="coerce").dropna()
    if len(a) < 3 or len(b) < 3:
        return ""
    try:
        _, p = stats.mannwhitneyu(a, b, alternative="two-sided")
        if p < 0.001:
            return f"{p:.2e}"
        return f"{p:.4g}"
    except Exception:
        return ""


def _p_categorical(dead: pd.Series, alive: pd.Series) -> str:
    try:
        table = pd.crosstab(
            pd.concat([dead, alive]),
            pd.concat([pd.Series(["dead"] * len(dead)), pd.Series(["alive"] * len(alive))]),
        )
        _, p, _, _ = stats.chi2_contingency(table)
        return f"{p:.4g}"
    except Exception:
        return ""


def build_baseline_table(df: pd.DataFrame, cohort: str) -> pd.DataFrame:
    y = pd.to_numeric(df[LABEL], errors="coerce").astype(int)
    dead = df[y == 1]
    alive = df[y == 0]
    n_dead, n_alive = len(dead), len(alive)

    rows: list[dict] = [
        {
            "Characteristic": "Participants, n (%)",
            "Non_survivors": _fmt_n_pct(n_dead, n_dead + n_alive),
            "Survivors": _fmt_n_pct(n_alive, n_dead + n_alive),
            "P_value": "",
        }
    ]

    if "is_noninvasive_ventilator" in df.columns:
        v_dead = (pd.to_numeric(dead["is_noninvasive_ventilator"], errors="coerce") >= 0.5).astype(int)
        v_alive = (pd.to_numeric(alive["is_noninvasive_ventilator"], errors="coerce") >= 0.5).astype(int)
        for val, label in [(0, "Non-invasive ventilation = 0"), (1, "Non-invasive ventilation = 1")]:
            rows.append(
                {
                    "Characteristic": label,
                    "Non_survivors": _fmt_n_pct(int((v_dead == val).sum()), n_dead),
                    "Survivors": _fmt_n_pct(int((v_alive == val).sum()), n_alive),
                    "P_value": _p_categorical(v_dead, v_alive) if val == 0 else "",
                }
            )

    lab_rows = [
        ("Minimum SpO₂ (%)", "spo2_min"),
        ("Maximum pCO₂ (mmHg)", "pco2_max"),
        ("First platelet count (×10⁹/L)", "platelet_1st"),
        ("Mean platelet count (×10⁹/L)", "platelet_mean"),
        ("Minimum WBC (×10⁹/L)", "wbc_min"),
        ("Minimum BUN (mg/dL)", "bun_min"),
        ("Minimum creatinine (mg/dL)", "creatinine_min"),
    ]
    for label, col in lab_rows:
        if col not in df.columns:
            continue
        a = dead[col]
        b = alive[col]
        rows.append(
            {
                "Characteristic": label,
                "Non_survivors": _fmt_median_iqr(a),
                "Survivors": _fmt_median_iqr(b),
                "P_value": _p_continuous(a, b),
            }
        )

    out = pd.DataFrame(rows)
    out.insert(0, "Cohort", cohort)
    return out


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    f3 = load_corrected_f3_feature_table()
    nh = load_corrected_nh_feature_table()
    t2 = build_baseline_table(f3, "F3")
    t3 = build_baseline_table(nh, "NH")
    t2.to_csv(OUT / "table_s2_f3_baseline.csv", index=False)
    t3.to_csv(OUT / "table_s3_nh_baseline.csv", index=False)
    print(f"Wrote {OUT / 'table_s2_f3_baseline.csv'} ({len(t2)} rows)")
    print(f"Wrote {OUT / 'table_s3_nh_baseline.csv'} ({len(t3)} rows)")


if __name__ == "__main__":
    main()

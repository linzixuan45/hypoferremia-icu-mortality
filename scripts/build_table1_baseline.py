#!/usr/bin/env python3
"""Legacy training-cohort baseline for MIMIC-IV (not the manuscript Table 1)."""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "mimic_dataset.xlsx"
TRAIN_IDS = ROOT / "result" / "analysis" / "cohorts" / "mimic4_train_ids.csv"
OUT = ROOT / "result" / "analysis" / "tables" / "legacy_training_cohort_baseline_not_for_manuscript.csv"

LAB_ROWS = [
    "Chloride",
    "Magnesium",
    "Potassium",
    "Sodium",
    "Sbp",
    "Sbp Ni",
    "Dbp",
    "Dbp Ni",
    "Mbp",
    "Mbp Ni",
    "Spo2",
    "Glucose",
    "Albumin",
    "Alp",
    "Alt",
    "Amylase",
    "Aniongap",
    "Ast",
    "Atypical Lymphocytes",
    "Bands",
    "Baseexcess",
    "Basophils",
    "Bicarbonate",
    "Bilirubin Direct",
    "Bilirubin Indirect",
    "Bilirubin Total",
    "Bun",
    "Carboxyhemoglobin",
    "Ck Mb",
    "Creatinine",
    "Crp",
    "D-Dimer",
    "Eosinophils",
    "Fibrinogen",
    "Ggt",
    "Globulin",
    "Hematocrit",
    "Hemoglobin",
    "Inr",
    "Lactate",
    "Ld",
    "Lymphocytes",
    "Mch",
    "Mchc",
    "Mcv",
    "Metamyelocytes",
    "Methemoglobin",
    "Monocytes",
    "Neutrophils",
    "Pco2",
    "Ph",
    "Platelet",
    "Po2",
    "Pt",
    "Ptt",
    "Rbc",
    "Rdw",
    "Thrombin",
    "Total Protein",
    "Totalco2",
    "Wbc",
]

LABEL_TO_COL = {
    "Age": "admission_age",
    "Height": "height_mean",
    "Weight": "weight_mean",
    "Heart Rate": "heart_rate_mean",
    "Resp Rate": "resp_rate_mean",
    "Temperature": "temperature_mean",
    "Hospitalization days": "los_hospital",
    "ICU hospitalization days": "los_icu",
    "SOFA Score": "sofa_score",
}


def _label_to_col(label: str) -> str | None:
    if label in LABEL_TO_COL:
        return LABEL_TO_COL[label]
    key = re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_")
    return f"{key}_mean"


def _fmt_median(s: pd.Series) -> str:
    s = pd.to_numeric(s, errors="coerce").dropna()
    if s.empty:
        return "—"
    q1, med, q3 = s.quantile([0.25, 0.5, 0.75])
    return f"{med:.2f} ({q1:.2f}, {q3:.2f})"


def _fmt_median_with_n(s: pd.Series) -> str:
    """Median (IQR) plus the variable-specific available observation count."""
    numeric = pd.to_numeric(s, errors="coerce").dropna()
    if numeric.empty:
        return "— [n=0]"
    q1, med, q3 = numeric.quantile([0.25, 0.5, 0.75])
    return f"{med:.2f} ({q1:.2f}, {q3:.2f}) [n={len(numeric)}]"


def _fmt_count(n: int, total: int) -> str:
    pct = 100.0 * n / total if total else 0.0
    return f"{n} ({pct:.2f})"


def _p_continuous(a: pd.Series, b: pd.Series) -> str:
    a = pd.to_numeric(a, errors="coerce").dropna()
    b = pd.to_numeric(b, errors="coerce").dropna()
    if len(a) < 5 or len(b) < 5:
        return ""
    try:
        _, p = stats.mannwhitneyu(a, b, alternative="two-sided")
    except ValueError:
        return ""
    if p < 0.001:
        return "<0.001"
    return f"{p:.3f}"


def _p_binary(mask_all: pd.Series, y: pd.Series) -> str:
    tab = pd.crosstab(mask_all.astype(int), y.astype(int))
    if tab.shape != (2, 2):
        return ""
    try:
        _, p, _, _ = stats.chi2_contingency(tab)
    except ValueError:
        return ""
    if p < 0.001:
        return "<0.001"
    return f"{p:.3f}"


def _race_bucket(race: str) -> str:
    r = str(race).upper()
    if "WHITE" in r:
        return "White"
    if "ASIAN" in r:
        return "Asian"
    if "BLACK" in r:
        return "Black"
    if "HISPANIC" in r or "LATINO" in r:
        return "Latino"
    return "Other"


def load_train_cohort() -> pd.DataFrame:
    """Legacy MIMIC-IV development subset (not the manuscript Table 1)."""
    train = pd.read_csv(TRAIN_IDS)
    m4 = pd.read_excel(DATA_PATH, sheet_name="mimic4_low_fe")
    id_col = "subject_id" if "subject_id" in train.columns else "icustay_id"
    df = m4.merge(train, on=id_col, how="inner")
    if "admission_age" in df.columns:
        age = pd.to_numeric(df["admission_age"], errors="coerce")
        df = df[(age >= 18) & (age <= 100)]
    if "los_icu" in df.columns:
        los = pd.to_numeric(df["los_icu"], errors="coerce")
        df = df[los >= 2.0]
    if "outcome_28d_admission" not in df.columns:
        raise ValueError("outcome_28d_admission missing after merge")
    return df.reset_index(drop=True)


def build_table1(df: pd.DataFrame) -> pd.DataFrame:
    y = df["outcome_28d_admission"].astype(int)
    dead = df[y == 1]
    alive = df[y == 0]
    n_all, n_d, n_a = len(df), len(dead), len(alive)

    rows: list[dict] = [
        {
            "Variables": "Variables",
            "Total": f"Total (n={n_all})",
            "Non_survivors": f"Non-survivors (n={n_d})",
            "Survivors": f"Survivors (n={n_a})",
            "P": "P",
        }
    ]

    def add_section(title: str) -> None:
        rows.append({"Variables": title, "Total": "", "Non_survivors": "", "Survivors": "", "P": ""})

    def add_binary(label: str, mask: pd.Series, p_row: str = "") -> None:
        rows.append(
            {
                "Variables": label,
                "Total": _fmt_count(int(mask.sum()), n_all),
                "Non_survivors": _fmt_count(int(mask[dead.index].sum()), n_d),
                "Survivors": _fmt_count(int(mask[alive.index].sum()), n_a),
                "P": p_row,
            }
        )

    def add_continuous(label: str, col: str) -> None:
        if not col or col not in df.columns:
            rows.append({"Variables": label, "Total": "—", "Non_survivors": "—", "Survivors": "—", "P": ""})
            return
        rows.append(
            {
                "Variables": label,
                "Total": _fmt_median_with_n(df[col]),
                "Non_survivors": _fmt_median_with_n(dead[col]),
                "Survivors": _fmt_median_with_n(alive[col]),
                "P": _p_continuous(dead[col], alive[col]),
            }
        )

    add_section("Gender, n (%)")
    male = df["gender"].astype(str).str.upper().str.startswith("M")
    add_binary("Male", male, _p_binary(male, y))
    add_binary("Female", ~male, "")

    add_continuous("Age, Median (Q1, Q3)", "admission_age")
    # Height is omitted because the eligible export contains too few observed
    # values for a defensible group comparison.
    add_continuous("Weight, Median (Q1, Q3)", "weight_mean")
    add_continuous("Heart Rate, Median (Q1, Q3)", "heart_rate_mean")
    add_continuous("Resp Rate, Median (Q1, Q3)", "resp_rate_mean")
    add_continuous("Temperature, Median (Q1, Q3)", "temperature_mean")

    add_section("Race, n (%)")
    if "race" in df.columns:
        buckets = df["race"].map(_race_bucket)
        for race_label in ["White", "Asian", "Black", "Latino", "Other"]:
            m = buckets == race_label
            add_binary(race_label, m, _p_binary(m, y) if race_label == "White" else "")

    add_continuous("Hospitalization days, Median (Q1, Q3)", "los_hospital")
    add_continuous("ICU hospitalization days, Median (Q1, Q3)", "los_icu")
    add_continuous("SOFA Score, Median (Q1, Q3)", "sofa_score")

    vent = pd.to_numeric(df.get("is_ventilator", 0), errors="coerce").fillna(0) > 0
    rows.append(
        {
            "Variables": "Any documented ventilatory-support flag, n (%)",
            "Total": _fmt_count(int(vent.sum()), n_all),
            "Non_survivors": _fmt_count(int(vent[dead.index].sum()), n_d),
            "Survivors": _fmt_count(int(vent[alive.index].sum()), n_a),
            "P": _p_binary(vent, y),
        }
    )

    vaso = pd.to_numeric(df.get("vasoactive", 0), errors="coerce").fillna(0) > 0
    rows.append(
        {
            "Variables": "Vasoactive, n (%)",
            "Total": _fmt_count(int(vaso.sum()), n_all),
            "Non_survivors": _fmt_count(int(vaso[dead.index].sum()), n_d),
            "Survivors": _fmt_count(int(vaso[alive.index].sum()), n_a),
            "P": _p_binary(vaso, y),
        }
    )

    add_section("Laboratory Data, Median (Q1, Q3)")
    for lab in LAB_ROWS:
        col = _label_to_col(lab)
        add_continuous(lab, col if col in df.columns else "")

    return pd.DataFrame(rows)


def main() -> None:
    df = load_train_cohort()
    table = build_table1(df)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(OUT, index=False)
    print(f"Wrote {OUT} ({len(table)} rows, n={len(df)}, events={int(df['outcome_28d_admission'].sum())})")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Build the R2 retrospective whole-stay cohorts and analysis manifest.

The 28-day in-hospital endpoint is anchored to hospital admission. The retained
``los_icu_to_t0`` field is a synthetic R1 protocol-continuity predictor, not an
observed prediction time. MIMIC-IV is split 80/20 by patient; MIMIC-III is
filtered with the same ICU length-of-stay criterion and used only as a
same-institution cross-database temporal sensitivity cohort.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "mimic_dataset.xlsx"
T0_LABS_PATH = ROOT / "data" / "mimic_t0_labs.parquet"
SEVERITY_PATH = ROOT / "data" / "mimic_severity_scores.parquet"
OUT = ROOT / "result" / "analysis"
COHORT_DIR = OUT / "cohorts"
FLOW_DIR = OUT / "tables"
RANDOM_STATE = 42
LOS_ICU_MIN_DAYS = 2.0  # >= 48 h per FE1 §2
OUTCOME_HORIZON_DAYS = 28
FE1_VERSION = "fe1_v1_2026-06-18"

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from dataset import MISSING_THRESHOLD, MIMIC3_THRESHOLD, encoder_gender, encoder_race

FEAT8 = [
    "platelet_mean",
    "wbc_min",
    "bun_min",
    "pco2_max",
    "creatinine_min",
    "is_noninvasive_ventilator",
    "spo2_min",
    "platelet_1st",
]


def _git_commit() -> str:
    try:
        return (
            subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, stderr=subprocess.DEVNULL
            )
            .decode()
            .strip()
        )
    except Exception:
        return "unknown"


def load_lasso_features(n: int = 20) -> list[str]:
    path = ROOT / "config" / "low_fe_lasso_feature.csv"
    return pd.read_csv(path, header=None)[0].tolist()[:n]


def load_raw() -> tuple[pd.DataFrame, pd.DataFrame]:
    m4 = pd.read_excel(DATA_PATH, sheet_name="mimic4_low_fe")
    m3 = pd.read_excel(DATA_PATH, sheet_name="mimic3_low_fe")
    return m4, m3


def clean_raw(m3: pd.DataFrame, m4: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    m3c = m3.dropna(thresh=m3.shape[0] * MIMIC3_THRESHOLD, axis=1)
    m4c = m4.dropna(thresh=m4.shape[0] * MISSING_THRESHOLD, axis=1)
    return m3c, m4c


def apply_base_filters(df: pd.DataFrame, los_icu_min_days: float = LOS_ICU_MIN_DAYS) -> pd.DataFrame:
    out = df.copy()
    if "admission_age" in out.columns:
        out["admission_age"] = pd.to_numeric(out["admission_age"], errors="coerce").clip(18, 100)
    if "race" in out.columns:
        out = encoder_race(out)
    if "gender" in out.columns:
        out = encoder_gender(out)
    if "los_icu" in out.columns:
        los = pd.to_numeric(out["los_icu"], errors="coerce")
        out = out[los >= los_icu_min_days]
    return out.reset_index(drop=True)


def hypoferremia_stratum_proxy(df: pd.DataFrame) -> pd.Series:
    iron_1st = pd.to_numeric(df.get("iron_1st", np.nan), errors="coerce")
    iron_min = pd.to_numeric(df.get("iron_min", np.nan), errors="coerce")
    admission = (iron_1st < 60) & iron_1st.notna()
    acquired = (~admission) & (iron_min < 60) & iron_min.notna()
    return pd.Series(
        np.where(admission, "admission", np.where(acquired, "acquired", "unknown")),
        index=df.index,
    )


def hours_icu_to_t0_proxy(df: pd.DataFrame, stratum: pd.Series) -> pd.Series:
    los = pd.to_numeric(df["los_icu"], errors="coerce").fillna(0)
    hours = np.where(stratum == "admission", 0.0, np.minimum(los * 12.0, los * 24.0))
    return pd.Series(hours, index=df.index)


def los_icu_to_t0(df: pd.DataFrame, hours: pd.Series) -> pd.Series:
    los = pd.to_numeric(df["los_icu"], errors="coerce").fillna(0)
    return pd.Series(np.minimum(los, hours / 24.0), index=df.index)


def days_from_admission(df: pd.DataFrame) -> pd.Series:
    if "hosp_survival_days" in df.columns:
        s = pd.to_numeric(df["hosp_survival_days"], errors="coerce")
        if s.notna().any():
            return s.fillna(999)
    if "icu_survival_days" in df.columns:
        raw = pd.to_numeric(df["icu_survival_days"], errors="coerce")
        if raw.notna().any():
            converted = np.where(raw > 30, raw / 24.0, raw)
            return pd.Series(converted, index=df.index).fillna(999)
    los = pd.to_numeric(df.get("los_hospital", np.nan), errors="coerce")
    expired = pd.to_numeric(df.get("hospital_expire_flag", 0), errors="coerce").fillna(0)
    proxy = np.where(expired == 1, los, 999.0)
    return pd.Series(proxy, index=df.index).fillna(999)


def outcome_28d_from_admission(df: pd.DataFrame) -> pd.Series:
    """Death in hospital within 28 days of hospital admission."""
    expired = pd.to_numeric(df["hospital_expire_flag"], errors="coerce").fillna(0).astype(int)
    days_from_adm = days_from_admission(df)
    return ((expired == 1) & (days_from_adm <= OUTCOME_HORIZON_DAYS)).astype(int)


def attach_outcomes(raw: pd.DataFrame, cleaned: pd.DataFrame, t0_source: str) -> pd.DataFrame:
    out = cleaned.copy()
    for col in ["hospital_expire_flag", "hosp_survival_days", "icu_survival_days", "los_icu"]:
        if col not in out.columns and col in raw.columns:
            out[col] = raw.loc[out.index, col]
    stratum = hypoferremia_stratum_proxy(out)
    out["hypoferremia_stratum"] = stratum
    out = out[stratum != "unknown"].copy()
    out["hours_icu_to_t0"] = hours_icu_to_t0_proxy(out, out["hypoferremia_stratum"])
    out["los_icu_to_t0"] = los_icu_to_t0(out, out["hours_icu_to_t0"])
    out["outcome_28d_admission"] = outcome_28d_from_admission(out)
    out["t0_source"] = t0_source
    return out


def merge_t0_labs(m3: pd.DataFrame, m4: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, str]:
    if not T0_LABS_PATH.exists():
        return m3, m4, "excel_proxy"

    labs = pd.read_parquet(T0_LABS_PATH)
    id_col_m3 = "icustay_id" if "icustay_id" in m3.columns else "subject_id"
    id_col_m4 = "stay_id" if "stay_id" in m4.columns else "subject_id"
    join_col = "stay_id" if "stay_id" in labs.columns else id_col_m4

    lab_cols = [
        c
        for c in [
            join_col,
            "t0_charttime",
            "hypoferremia_stratum",
            "hours_icu_to_t0",
            "iron_at_t0",
            "source",
        ]
        if c in labs.columns
    ]
    labs_sub = labs[lab_cols].drop_duplicates(subset=[join_col])

    m3 = m3.merge(labs_sub, left_on=id_col_m3, right_on=join_col, how="left", suffixes=("", "_t0"))
    m4 = m4.merge(labs_sub, left_on=id_col_m4, right_on=join_col, how="left", suffixes=("", "_t0"))
    return m3, m4, "parquet"


def primary_features(lasso20: list[str]) -> list[str]:
    """Map LASSO list to FE1 primary features (los_icu -> los_icu_to_t0; drop redundant max/mean)."""
    mapped: list[str] = []
    for feat in lasso20:
        if feat == "los_icu":
            mapped.append("los_icu_to_t0")
            continue
        if feat.endswith("_max") or feat.endswith("_mean"):
            base = re.sub(r"_(max|mean)$", "", feat)
            if f"{base}_1st" in lasso20 or f"{base}_min" in lasso20:
                continue
        mapped.append(feat)
    return list(dict.fromkeys(mapped))


def feature_complete(df: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    use = [c for c in features if c in df.columns]
    sub = df[use + ["outcome_28d_admission"]].dropna(subset=use)
    return df.loc[sub.index]


def assign_splits(
    m3: pd.DataFrame, m4: pd.DataFrame, features: list[str]
) -> tuple[dict, pd.DataFrame, pd.DataFrame]:
    m3_base = apply_base_filters(m3)
    m4_base = apply_base_filters(m4)

    m3_external = m3_base.dropna(subset=["hypoferremia_stratum"]).copy()
    m3_external = m3_external[m3_external["hypoferremia_stratum"] != "unknown"]

    m4f = feature_complete(m4_base, features)
    y = m4f["outcome_28d_admission"]
    train_idx, test_idx = train_test_split(
        m4f.index, test_size=0.2, random_state=RANDOM_STATE, stratify=y
    )

    id_col_m3 = "icustay_id" if "icustay_id" in m3_external.columns else "subject_id"
    id_col_m4 = "subject_id" if "subject_id" in m4f.columns else "icustay_id"

    splits = {
        "mimic4_train": m4f.loc[train_idx, [id_col_m4, "outcome_28d_admission", "hypoferremia_stratum"]],
        "mimic4_test": m4f.loc[test_idx, [id_col_m4, "outcome_28d_admission", "hypoferremia_stratum"]],
        "mimic3_external": m3_external[[id_col_m3, "outcome_28d_admission", "hypoferremia_stratum"]],
        "legacy_mimic4_test": m4f.loc[test_idx].copy(),
        "legacy_mimic3_external": m3_external.copy(),
        "mimic4_train_indices": pd.Series(train_idx, name="index"),
        "mimic4_test_indices": pd.Series(test_idx, name="index"),
    }
    m3f = feature_complete(m3_base, features)
    return splits, m3f, m4f


def export_severity_proxy(m3f: pd.DataFrame, m4f: pd.DataFrame) -> None:
    if SEVERITY_PATH.exists():
        sev = pd.read_parquet(SEVERITY_PATH)
        if sev.get("source", pd.Series(["excel_proxy"])).iloc[0] == "mimic_sql":
            return
        if sev.get("apache_ii", pd.Series(dtype=float)).notna().any():
            return
    rows = []
    id_col_m3 = "icustay_id" if "icustay_id" in m3f.columns else "subject_id"
    for tag, df, idc in [("mimic3", m3f, id_col_m3), ("mimic4", m4f, "subject_id")]:
        if "sofa_score" not in df.columns:
            continue
        for _, r in df.iterrows():
            rows.append(
                {
                    "cohort": tag,
                    "stay_id": r.get(idc),
                    "sofa_at_t0": r.get("sofa_score"),
                    "apache_ii": np.nan,
                    "saps_ii": np.nan,
                    "source": "excel_proxy",
                }
            )
    if rows:
        pd.DataFrame(rows).to_parquet(SEVERITY_PATH, index=False)


def _severity_source() -> str:
    if not SEVERITY_PATH.exists():
        return "excel_proxy_sofa_only"
    sev = pd.read_parquet(SEVERITY_PATH)
    src = sev["source"].iloc[0] if "source" in sev.columns else "unknown"
    if sev.get("apache_ii", pd.Series(dtype=float)).notna().any():
        return "mimic_sql"
    if src == "excel_proxy":
        return "excel_proxy_sofa_only"
    return str(src)


def write_flow_table(
    m3_raw: pd.DataFrame,
    m4_raw: pd.DataFrame,
    m3f: pd.DataFrame,
    m4f: pd.DataFrame,
    splits: dict,
) -> None:
    rows = [
        {"step": "mimic3_raw", "n": len(m3_raw)},
        {"step": "mimic4_raw", "n": len(m4_raw)},
        {"step": "mimic3_external_cohort_all", "n": len(splits["mimic3_external"])},
        {"step": "mimic3_feature_complete_modeling", "n": len(m3f)},
        {"step": "mimic4_after_fe1_base_filters", "n": len(apply_base_filters(m4_raw))},
        {"step": "mimic4_feature_complete_modeling", "n": len(m4f)},
        {"step": "mimic4_train", "n": len(splits["mimic4_train"])},
        {"step": "mimic4_internal_test", "n": len(splits["mimic4_test"])},
    ]
    for tag in ("admission", "acquired"):
        rows.append(
            {"step": f"mimic4_stratum_{tag}", "n": int((m4f["hypoferremia_stratum"] == tag).sum())}
        )
    FLOW_DIR.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(FLOW_DIR / "table_s8_patient_flow.csv", index=False)


def write_manifest(
    t0_source: str,
    features: list[str],
    n_train: int,
    n_test: int,
    n_external: int,
) -> None:
    manifest = {
        "pipeline": "hypoferremia_mortality",
        "fe1_version": FE1_VERSION,
        "fe1_spec_status": "finalized_2026-06-18",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": _git_commit(),
        "random_state": RANDOM_STATE,
        "los_icu_min_days": LOS_ICU_MIN_DAYS,
        "downsample_ratio": 0,
        "imbalance_primary": "class_weight_balanced",
        "imbalance_sensitivity": "random_undersample_x5_seeds",
        "t0_source": t0_source,
        "outcome": "death_in_hospital_within_28_days_from_hospital_admission",
        "analysis_frame": "retrospective_whole_ICU_stay_risk_stratification",
        "predictor_window": "full_ICU_stay_for_min_max_mean; first_ICU_value_for_1st",
        "legacy_t0_status": "synthetic_proxy_retained_only_for_R1_protocol_continuity",
        "primary_features": features,
        "feat8": FEAT8,
        "china_cohorts": "option_beta_no_reanchor",
        "cohort_counts": {
            "mimic4_train": n_train,
            "mimic4_internal_test": n_test,
            "mimic3_external": n_external,
        },
        "severity_source": _severity_source(),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def main() -> None:
    lasso20 = load_lasso_features(20)
    features = primary_features(lasso20)
    m4_raw, m3_raw = load_raw()
    m3_clean, m4_clean = clean_raw(m3_raw, m4_raw)
    m3, m4, t0_source = merge_t0_labs(m3_clean, m4_clean)
    m3 = attach_outcomes(m3_raw, m3, t0_source)
    m4 = attach_outcomes(m4_raw, m4, t0_source)
    splits, m3f, m4f = assign_splits(m3, m4, features)

    COHORT_DIR.mkdir(parents=True, exist_ok=True)
    for name, df in splits.items():
        if name.endswith("_indices"):
            df.to_csv(COHORT_DIR / f"{name}.csv", index=False)
        elif name.startswith("legacy"):
            df.to_pickle(COHORT_DIR / f"{name}.pkl")
        else:
            df.to_csv(COHORT_DIR / f"{name}_ids.csv", index=False)

    export_severity_proxy(m3f, m4f)
    write_flow_table(m3_raw, m4_raw, m3f, m4f, splits)
    write_manifest(
        t0_source,
        features,
        len(splits["mimic4_train"]),
        len(splits["mimic4_test"]),
        len(splits["mimic3_external"]),
    )
    print(f"t0_source={t0_source}")
    print(f"primary_features ({len(features)}): {features}")
    print(
        f"mimic4 train={len(splits['mimic4_train'])} "
        f"test={len(splits['mimic4_test'])} "
        f"mimic3 external={len(splits['mimic3_external'])}"
    )
    print(f"manifest -> {OUT / 'manifest.json'}")


if __name__ == "__main__":
    main()

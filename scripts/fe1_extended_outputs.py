#!/usr/bin/env python3
"""FE1 extended outputs: Supp S6A/S7 missingness, S9 imbalance, S10 legacy window."""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

from build_t0_cohort import (  # noqa: E402
    apply_base_filters,
    attach_outcomes,
    clean_raw,
    days_from_admission,
    load_lasso_features,
    load_raw,
    primary_features,
)
from train_models import (  # noqa: E402
    COHORT,
    LABEL,
    OUT,
    RANDOM_STATE,
    TABLES,
    build_soft_voting,
    delong_ci,
    impute_scale,
    load_cohort_frames,
    prep_subset,
)

UNDERSAMPLE_SEEDS = [42, 43, 44, 45, 46]
OUTCOME_HORIZON_DAYS = 28
S6A_EXTRA_VARS = ["platelet_mean", "bun_max"]
S6A_COHORT_LABELS = {
    "MIMIC-IV train": "MIMIC-IV train",
    "MIMIC-IV test": "MIMIC-IV test",
    "MIMIC-III temporal sensitivity": "MIMIC-III temporal sensitivity",
}

load_lasso20 = load_lasso_features


def outcome_28d_from_admission(df: pd.DataFrame) -> pd.Series:
    expired = pd.to_numeric(df["hospital_expire_flag"], errors="coerce").fillna(0).astype(int)
    days = days_from_admission(df)
    return ((expired == 1) & (days <= OUTCOME_HORIZON_DAYS)).astype(int)


def undersample_xy(X: pd.DataFrame, y: pd.Series, seed: int) -> tuple[pd.DataFrame, pd.Series]:
    pos_idx = np.where(y.values == 1)[0]
    neg_idx = np.where(y.values == 0)[0]
    if len(pos_idx) == 0 or len(neg_idx) == 0:
        return X, y
    rng = np.random.RandomState(seed)
    n_pos = len(pos_idx)
    neg_pick = rng.choice(neg_idx, size=n_pos, replace=False)
    idx = np.concatenate([pos_idx, neg_pick])
    idx.sort()
    return X.iloc[idx], y.iloc[idx]


def build_soft_voting_no_weight():
    from sklearn.ensemble import RandomForestClassifier, VotingClassifier
    from sklearn.linear_model import LogisticRegression
    from xgboost import XGBClassifier

    est = [
        ("lr", LogisticRegression(max_iter=2000, random_state=RANDOM_STATE)),
        (
            "rf",
            RandomForestClassifier(n_estimators=200, max_depth=6, random_state=RANDOM_STATE),
        ),
        (
            "xgb",
            XGBClassifier(
                n_estimators=120,
                max_depth=4,
                learning_rate=0.08,
                random_state=RANDOM_STATE,
                eval_metric="logloss",
            ),
        ),
    ]
    return VotingClassifier(estimators=est, voting="soft")


def eval_ensemble(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    ext_df: pd.DataFrame,
    features: list[str],
    label_col: str,
    *,
    undersample_seed: int | None = None,
) -> list[dict]:
    X_train, y_train = prep_subset(train_df, features, label_col=label_col)
    X_test, y_test = prep_subset(test_df, features, label_col=label_col)
    X_ext, y_ext = prep_subset(ext_df, features, label_col=label_col)

    train_n_before = len(y_train)
    if undersample_seed is not None:
        X_train, y_train = undersample_xy(X_train, y_train, undersample_seed)

    _, X_train_s, _, [X_test_s, X_ext_s], _, _ = impute_scale(X_train, [X_test, X_ext])
    model = build_soft_voting_no_weight() if undersample_seed is not None else build_soft_voting()
    model.fit(X_train_s, y_train)

    rows = []
    for cohort, y, X_s in [
        ("MIMIC-IV internal test", y_test, X_test_s),
        ("MIMIC-III temporal sensitivity", y_ext, X_ext_s),
    ]:
        prob = model.predict_proba(X_s)[:, 1]
        auc, lo, hi = delong_ci(y.values, prob)
        rows.append(
            {
                "Analysis": (
                    f"undersample_seed_{undersample_seed}"
                    if undersample_seed is not None
                    else "class_weight_primary"
                ),
                "Cohort": cohort,
                "train_n_before": train_n_before,
                "train_n_after": len(y_train),
                "train_events_after": int(y_train.sum()),
                "train_neg_after": int((y_train == 0).sum()),
                "n": len(y),
                "Events": int(y.sum()),
                "AUROC": round(auc, 3),
                "AUROC_95CI": f"{lo:.3f}-{hi:.3f}",
            }
        )
    return rows


def _cohort_frames_for_missingness() -> list[tuple[str, pd.DataFrame]]:
    m4_raw, m3_raw = load_raw()
    m3_clean, m4_clean = clean_raw(m3_raw, m4_raw)
    m3 = attach_outcomes(m3_raw, m3_clean, "excel_proxy")
    m4 = attach_outcomes(m4_raw, m4_clean, "excel_proxy")

    train_ids = pd.read_csv(COHORT / "mimic4_train_ids.csv")
    test_ids = pd.read_csv(COHORT / "mimic4_test_ids.csv")
    ext_ids = pd.read_csv(COHORT / "mimic3_external_ids.csv")
    id_m4 = "subject_id" if "subject_id" in m4.columns else "icustay_id"
    id_m3 = "icustay_id" if "icustay_id" in m3.columns else "subject_id"

    return [
        ("MIMIC-IV train", m4.merge(train_ids, on=id_m4, how="inner")),
        ("MIMIC-IV test", m4.merge(test_ids, on=id_m4, how="inner")),
        ("MIMIC-III temporal sensitivity", m3.merge(ext_ids, on=id_m3, how="inner")),
    ]


def _missingness_rows(cohort_key: str, df: pd.DataFrame, variables: list[str]) -> list[dict]:
    label = S6A_COHORT_LABELS.get(cohort_key, cohort_key)
    rows = []
    for feat in variables:
        if feat not in df.columns:
            rows.append(
                {
                    "Cohort": label,
                    "Variable": feat,
                    "n": len(df),
                    "Missing_n": len(df),
                    "Missing_pct": 100.0,
                    "lasso_excluded_from_modeling": feat in S6A_EXTRA_VARS,
                }
            )
            continue
        miss = int(df[feat].isna().sum())
        rows.append(
            {
                "Cohort": label,
                "Variable": feat,
                "n": len(df),
                "Missing_n": miss,
                "Missing_pct": round(100.0 * miss / len(df), 2) if len(df) else 0.0,
                "lasso_excluded_from_modeling": feat in S6A_EXTRA_VARS,
            }
        )
    return rows


def generate_s6a_missingness() -> Path:
    print("S6A: LASSO 20-scope missingness (18 modeling + 2 excluded)...")
    f18 = primary_features(load_lasso20())
    variables = f18 + S6A_EXTRA_VARS
    rows: list[dict] = []
    for cohort_key, df in _cohort_frames_for_missingness():
        rows.extend(_missingness_rows(cohort_key, df, variables))

    out = TABLES / "table_s6a_lasso20_missingness.csv"
    TABLES.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out, index=False)
    assert len(rows) == 60, f"expected 60 S6A rows, got {len(rows)}"
    assert "po2_max" not in {r["Variable"] for r in rows}
    print(f"  wrote {out} ({len(rows)} rows)")
    return out


def generate_s7_missingness() -> Path:
    print("S7: missingness by cohort (18-predictor locked matrix)...")
    f18 = primary_features(load_lasso20())
    rows: list[dict] = []
    for cohort_name, df in _cohort_frames_for_missingness():
        for feat in f18:
            if feat not in df.columns:
                rows.append(
                    {
                        "Cohort": cohort_name,
                        "Variable": feat,
                        "n": len(df),
                        "Missing_n": len(df),
                        "Missing_pct": 100.0,
                    }
                )
                continue
            miss = int(df[feat].isna().sum())
            rows.append(
                {
                    "Cohort": cohort_name,
                    "Variable": feat,
                    "n": len(df),
                    "Missing_n": miss,
                    "Missing_pct": round(100.0 * miss / len(df), 2) if len(df) else 0.0,
                }
            )

    out = TABLES / "table_s7_missingness.csv"
    TABLES.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out, index=False)
    print(f"  wrote {out}")
    return out


def generate_s9_imbalance_sensitivity() -> Path:
    print("S9: class-weight vs undersampling sensitivity...")
    train_df, test_df, ext_df = load_cohort_frames("excel_proxy")
    f20 = primary_features(load_lasso20())

    rows = eval_ensemble(train_df, test_df, ext_df, f20, LABEL)
    for seed in UNDERSAMPLE_SEEDS:
        rows.extend(eval_ensemble(train_df, test_df, ext_df, f20, LABEL, undersample_seed=seed))

    out = TABLES / "table_s9_imbalance_sensitivity.csv"
    TABLES.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out, index=False)
    print(f"  wrote {out}")
    return out


def attach_legacy_outcome(raw: pd.DataFrame, cleaned: pd.DataFrame) -> pd.DataFrame:
    out = cleaned.copy()
    for col in ["hospital_expire_flag", "hosp_survival_days", "icu_survival_days", "los_icu", "los_hospital"]:
        if col not in out.columns and col in raw.columns:
            out[col] = raw.loc[out.index, col]
    out["outcome_28d_admission"] = outcome_28d_from_admission(out)
    return out


def load_legacy_cohort_frames() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    m4_raw, m3_raw = load_raw()
    m3_clean, m4_clean = clean_raw(m3_raw, m4_raw)
    m3 = attach_legacy_outcome(m3_raw, apply_base_filters(m3_clean))
    m4 = attach_legacy_outcome(m4_raw, apply_base_filters(m4_clean))

    train_ids = pd.read_csv(COHORT / "mimic4_train_ids.csv")
    test_ids = pd.read_csv(COHORT / "mimic4_test_ids.csv")
    ext_ids = pd.read_csv(COHORT / "mimic3_external_ids.csv")

    id_m4 = "subject_id" if "subject_id" in m4.columns else "icustay_id"
    id_m3 = "icustay_id" if "icustay_id" in m3.columns else "subject_id"

    train_df = m4.merge(train_ids, on=id_m4, how="inner", suffixes=("", "_cohort"))
    test_df = m4.merge(test_ids, on=id_m4, how="inner", suffixes=("", "_cohort"))
    ext_df = m3.merge(ext_ids, on=id_m3, how="inner", suffixes=("", "_cohort"))
    return train_df, test_df, ext_df


def generate_s10_legacy_window() -> Path:
    print("S10: t0-proxy primary vs legacy full-stay window...")
    f20_primary = primary_features(load_lasso20())
    f20_legacy = load_lasso20()[:20]

    train_p, test_p, ext_p = load_cohort_frames("excel_proxy")
    train_l, test_l, ext_l = load_legacy_cohort_frames()

    primary_rows = eval_ensemble(train_p, test_p, ext_p, f20_primary, LABEL)
    for r in primary_rows:
        r["Feature_window"] = "t0_proxy_primary"
        r["Outcome"] = "death_in_hospital_within_28_days_from_hospital_admission"

    legacy_rows = eval_ensemble(train_l, test_l, ext_l, f20_legacy, "outcome_28d_admission")
    for r in legacy_rows:
        r["Feature_window"] = "legacy_full_stay"
        r["Outcome"] = "death_within_28d_from_admission"

    out = TABLES / "table_s10_legacy_window.csv"
    TABLES.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(primary_rows + legacy_rows).to_csv(out, index=False)
    print(f"  wrote {out}")
    return out


def update_manifest_artifacts() -> None:
    path = OUT / "manifest.json"
    if not path.exists():
        return
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest.setdefault("artifacts", {}).update(
        {
            "table_s6a_lasso20_missingness": "result/analysis/tables/table_s6a_lasso20_missingness.csv",
            "table_s7_missingness": "result/analysis/tables/table_s7_missingness.csv",
            "table_s9_imbalance": "result/analysis/tables/table_s9_imbalance_sensitivity.csv",
            "table_s10_legacy": "result/analysis/tables/table_s10_legacy_window.csv",
            "table_s10_8f_four_cohorts": "result/analysis/tables/table_s10_8f_four_cohorts.csv",
            "table_s2_f3_baseline": "result/analysis/tables/table_s2_f3_baseline.csv",
            "table_s3_nh_baseline": "result/analysis/tables/table_s3_nh_baseline.csv",
        }
    )
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def main() -> None:
    if not (COHORT / "mimic4_train_ids.csv").exists():
        raise SystemExit("Run build_t0_cohort.py first.")
    generate_s6a_missingness()
    generate_s7_missingness()
    generate_s9_imbalance_sensitivity()
    generate_s10_legacy_window()
    update_manifest_artifacts()
    print("FE1 extended outputs complete.")


if __name__ == "__main__":
    main()

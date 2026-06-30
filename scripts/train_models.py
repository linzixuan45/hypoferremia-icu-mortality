#!/usr/bin/env python3
"""Train 20/8-feature soft-voting ensembles (FE1); write preds + tables."""
from __future__ import annotations

import json
import pickle
import sys
import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.calibration import calibration_curve
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.impute import KNNImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, roc_curve
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

from build_t0_cohort import (
    FEAT8,
    attach_outcomes,
    clean_raw,
    load_lasso_features,
    load_raw,
    primary_features,
)

load_lasso20 = load_lasso_features
load_mimic_data = load_raw
from dataset import MISSING_THRESHOLD, MIMIC3_THRESHOLD, encoder_gender, encoder_race
from external_cohort_data import (
    external_cohorts_available,
    load_corrected_f3_feature_table,
    load_corrected_nh_feature_table,
)

OUT = ROOT / "result" / "analysis"
PREDS = OUT / "preds"
TABLES = OUT / "tables"
FIGURES = OUT / "figures"
COHORT = OUT / "cohorts"
DATA_PATH = ROOT / "data" / "mimic_dataset.xlsx"
RANDOM_STATE = 42
LABEL = "outcome_28d_t0"
LOS_ICU_MIN_DAYS = 2.0


def delong_ci(y_true, y_score, alpha=0.05):
    y_true = np.asarray(y_true, dtype=int)
    y_score = np.asarray(y_score, dtype=float)
    pos, neg = y_score[y_true == 1], y_score[y_true == 0]
    m, n = len(pos), len(neg)
    if m < 5 or n < 5:
        return np.nan, np.nan, np.nan
    all_s = np.concatenate([pos, neg])
    j = np.argsort(all_s)
    z = all_s[j]
    rank = np.zeros(m + n)
    i = 0
    while i < m + n:
        k = i
        while k < m + n - 1 and z[k + 1] == z[k]:
            k += 1
        for t in range(i, k + 1):
            rank[t] = 0.5 * (i + k) + 1
        i = k + 1
    rank_out = np.empty(m + n)
    rank_out[j] = rank
    auc = (np.sum(rank_out[:m]) - m * (m + 1) / 2) / (m * n)
    v10 = np.array([(np.sum(neg < pos[i]) + 0.5 * np.sum(neg == pos[i])) / n for i in range(m)])
    v01 = np.array([(np.sum(pos > neg[j]) + 0.5 * np.sum(pos == neg[j])) / m for j in range(n)])
    se = np.sqrt((np.var(v10, ddof=1) if m > 1 else 0) / m + (np.var(v01, ddof=1) if n > 1 else 0) / n)
    zv = stats.norm.ppf(1 - alpha / 2)
    return auc, max(0.0, auc - zv * se), min(1.0, auc + zv * se)


def _binarize_vent(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "is_noninvasive_ventilator" in out.columns:
        out["is_noninvasive_ventilator"] = (
            pd.to_numeric(out["is_noninvasive_ventilator"], errors="coerce").fillna(0) >= 0.5
        ).astype(int)
    return out


def prep_frame(
    df: pd.DataFrame,
    features: list[str],
    label_col: str = LABEL,
    los_icu_min: float = LOS_ICU_MIN_DAYS,
) -> pd.DataFrame:
    out = _binarize_vent(df.copy())
    if "admission_age" in out.columns:
        out["admission_age"] = pd.to_numeric(out["admission_age"], errors="coerce").clip(18, 100)
    if "race" in out.columns:
        out = encoder_race(out)
    if "gender" in out.columns:
        out = encoder_gender(out)
    if "los_icu" in out.columns:
        los = pd.to_numeric(out["los_icu"], errors="coerce")
        out = out[los >= los_icu_min]
    cols = [c for c in features if c in out.columns]
    if label_col in out.columns:
        cols = cols + [label_col]
    elif "hospital_expire_flag" in out.columns:
        cols = cols + ["hospital_expire_flag"]
        label_col = "hospital_expire_flag"
    sub = out[cols].dropna()
    if label_col == LABEL and label_col in sub.columns:
        sub["hospital_expire_flag"] = sub[label_col]
    return sub


def impute_scale(X_train: pd.DataFrame, X_other: list[pd.DataFrame]):
    imp = KNNImputer(n_neighbors=5)
    tr = pd.DataFrame(imp.fit_transform(X_train), columns=X_train.columns)
    others = [pd.DataFrame(imp.transform(x), columns=X_train.columns) for x in X_other]
    scaler = StandardScaler()
    tr_s = pd.DataFrame(scaler.fit_transform(tr), columns=tr.columns)
    oth_s = [pd.DataFrame(scaler.transform(o), columns=o.columns) for o in others]
    return tr, tr_s, others, oth_s, imp, scaler


def build_soft_voting():
    est = [
        ("lr", LogisticRegression(max_iter=2000, random_state=RANDOM_STATE, class_weight="balanced")),
        (
            "rf",
            RandomForestClassifier(
                n_estimators=200, max_depth=6, random_state=RANDOM_STATE, class_weight="balanced"
            ),
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


build_stacking = build_soft_voting


def youden_threshold(y_true, y_prob):
    fpr, tpr, thr = roc_curve(y_true, y_prob)
    j = tpr - fpr
    idx = np.argmax(j)
    return float(thr[idx])


def load_cohort_frames(t0_source: str = "excel_proxy") -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """MIMIC-IV train/test + MIMIC-III external, aligned with cohort ID lists."""
    m4_raw, m3_raw = load_raw()
    m3_clean, m4_clean = clean_raw(m3_raw, m4_raw)
    m3 = attach_outcomes(m3_raw, m3_clean, t0_source)
    m4 = attach_outcomes(m4_raw, m4_clean, t0_source)

    train_ids = pd.read_csv(COHORT / "mimic4_train_ids.csv")
    test_ids = pd.read_csv(COHORT / "mimic4_test_ids.csv")
    ext_ids = pd.read_csv(COHORT / "mimic3_external_ids.csv")

    id_m4 = "subject_id" if "subject_id" in m4.columns else "icustay_id"
    id_m3 = "icustay_id" if "icustay_id" in m3.columns else "subject_id"

    train_df = m4.merge(train_ids, on=id_m4, how="inner", suffixes=("", "_cohort"))
    test_df = m4.merge(test_ids, on=id_m4, how="inner", suffixes=("", "_cohort"))
    ext_df = m3.merge(ext_ids, on=id_m3, how="inner", suffixes=("", "_cohort"))
    return train_df, test_df, ext_df


def prep_subset(
    df: pd.DataFrame, features: list[str], label_col: str = LABEL
) -> tuple[pd.DataFrame, pd.Series]:
    sub = prep_frame(df, features, label_col=label_col)
    ycol = label_col if label_col in sub.columns else "hospital_expire_flag"
    return sub[features], sub[ycol].astype(int)


def train_and_predict(features: list[str], tag: str):
    train_df, test_df, ext_df = load_cohort_frames("excel_proxy")

    train_p = prep_frame(train_df, features)
    test_p = prep_frame(test_df, features)
    ext_p = prep_frame(ext_df, features)

    X_train = train_p[features]
    y_train = train_p["hospital_expire_flag"].astype(int)
    X_test = test_p[features]
    y_test = test_p["hospital_expire_flag"].astype(int)
    X_ext = ext_p[features]
    y_ext = ext_p["hospital_expire_flag"].astype(int)

    _, X_train_s, _, [X_test_s, X_ext_s], imp, scaler = impute_scale(X_train, [X_test, X_ext])

    model = build_soft_voting()
    oof = cross_val_predict(
        model,
        X_train_s,
        y_train,
        cv=StratifiedKFold(5, shuffle=True, random_state=RANDOM_STATE),
        method="predict_proba",
    )[:, 1]
    thresh = youden_threshold(y_train, oof)
    model.fit(X_train_s, y_train)

    def pack(y, prob, name):
        pred = (prob >= thresh).astype(int)
        auc, lo, hi = delong_ci(y, prob)
        return {
            "model_name": "Ensemble_Voting",
            "cohort": name,
            "n": len(y),
            "events": int(np.sum(y)),
            "auroc": auc,
            "auroc_ci_lo": lo,
            "auroc_ci_hi": hi,
            "youden_threshold": thresh,
            "pred_prob": prob.tolist(),
            "pred": pred.tolist(),
            "lable": y.tolist(),
        }

    test_prob = model.predict_proba(X_test_s)[:, 1]
    ext_prob = model.predict_proba(X_ext_s)[:, 1]

    weight_dir = OUT / "model_weight" / tag
    weight_dir.mkdir(parents=True, exist_ok=True)
    with open(weight_dir / "model_weight.pkl", "wb") as f:
        pickle.dump(
            {
                "Ensemble_Voting": model,
                "imputer": imp,
                "scaler": scaler,
                "features": features,
                "threshold": thresh,
            },
            f,
        )

    results = {
        "test": pack(y_test, test_prob, "mimic4_internal_test"),
        "external": pack(y_ext, ext_prob, "mimic3_external"),
    }
    for k, v in results.items():
        with open(PREDS / f"{tag}_{k}_preds.pkl", "wb") as f:
            pickle.dump([v], f)
    return results, model, imp, scaler, thresh


def infer_external(model, imp, scaler, features, df, label_col="hospital_expire_flag"):
    sub = prep_frame(df, features, label_col=label_col if label_col in df.columns else "hospital_expire_flag")
    X = sub[features]
    y = sub["hospital_expire_flag"].astype(int)
    X_i = pd.DataFrame(imp.transform(X), columns=features)
    X_s = pd.DataFrame(scaler.transform(X_i), columns=features)
    prob = model.predict_proba(X_s)[:, 1]
    return y, prob, len(sub), int(y.sum())


def write_table23(res20, res8):
    rows = []
    for feat_tag, res in [("20-feature", res20), ("8-feature", res8)]:
        for split, label in [
            ("test", "MIMIC-IV internal test"),
            ("external", "MIMIC-III external"),
        ]:
            d = res[split]
            rows.append(
                {
                    "Model": feat_tag,
                    "Cohort": label,
                    "n": d["n"],
                    "Events": d["events"],
                    "AUROC": round(d["auroc"], 3),
                    "AUROC_95CI": f"{d['auroc_ci_lo']:.3f}-{d['auroc_ci_hi']:.3f}",
                }
            )
    pd.DataFrame(rows).to_csv(TABLES / "table2_3_performance.csv", index=False)


def calibration_metrics(y, prob):
    brier = brier_score_loss(y, prob)
    prob_true, prob_pred = calibration_curve(y, prob, n_bins=8, strategy="quantile")
    if len(prob_true) >= 2:
        slope, intercept = np.polyfit(prob_pred, prob_true, 1)
    else:
        slope, intercept = np.nan, np.nan
    return brier, slope, intercept


def write_table6(all_cohorts):
    rows = []
    for name, y, prob in all_cohorts:
        brier, slope, intercept = calibration_metrics(y, prob)
        rows.append(
            {"Cohort": name, "Brier": brier, "Calibration_slope": slope, "Calibration_intercept": intercept}
        )
    pd.DataFrame(rows).to_csv(TABLES / "table6_calibration.csv", index=False)


def write_s8_s9(m4_raw, test_ids, model, imp, scaler, features20):
    m3_raw = pd.read_excel(DATA_PATH, sheet_name="mimic3_low_fe")
    _, m4_clean = clean_raw(m3_raw, m4_raw)
    m4_fe = attach_outcomes(m4_raw, m4_clean, "excel_proxy")
    id_m4 = "subject_id" if "subject_id" in m4_fe.columns else "icustay_id"
    test = m4_fe[m4_fe[id_m4].isin(test_ids[id_m4])].copy()
    rows8 = []
    for stratum in ["admission", "acquired"]:
        sub = test[test["hypoferremia_stratum"] == stratum]
        if len(sub) < 10:
            continue
        sub_p = prep_frame(sub, features20)
        y = sub_p["hospital_expire_flag"].astype(int)
        X = sub_p[features20]
        X_s = pd.DataFrame(
            scaler.transform(pd.DataFrame(imp.transform(X), columns=features20)),
            columns=features20,
        )
        prob = model.predict_proba(X_s)[:, 1]
        auc, lo, hi = delong_ci(y, prob)
        brier, slope, _ = calibration_metrics(y, prob)
        rows8.append(
            {
                "Stratum": stratum,
                "n": len(y),
                "Events": int(y.sum()),
                "AUROC": auc,
                "CI_lo": lo,
                "CI_hi": hi,
                "Brier": brier,
                "Slope": slope,
            }
        )
    pd.DataFrame(rows8).to_csv(TABLES / "table_s8_strata.csv", index=False)

    legacy_path = COHORT / "legacy_mimic4_test.pkl"
    if legacy_path.exists():
        legacy_test = pd.read_pickle(legacy_path)
        if "los_icu_to_t0" not in legacy_test.columns and "hours_icu_to_t0" in legacy_test.columns:
            legacy_test = legacy_test.copy()
            los = pd.to_numeric(legacy_test["los_icu"], errors="coerce").fillna(0)
            legacy_test["los_icu_to_t0"] = np.minimum(los, legacy_test["hours_icu_to_t0"] / 24.0)
        sub_p = prep_frame(legacy_test, features20, label_col="hospital_expire_flag")
        y = sub_p["hospital_expire_flag"].astype(int)
        X_s = pd.DataFrame(
            scaler.transform(pd.DataFrame(imp.transform(sub_p[features20]), columns=features20)),
            columns=features20,
        )
        prob = model.predict_proba(X_s)[:, 1]
        auc, lo, hi = delong_ci(y, prob)
        pd.DataFrame(
            [
                {
                    "Analysis": "legacy_admission_anchored",
                    "n": len(y),
                    "Events": int(y.sum()),
                    "AUROC": auc,
                    "CI_lo": lo,
                    "CI_hi": hi,
                }
            ]
        ).to_csv(TABLES / "table_s9_legacy.csv", index=False)


def plot_figure5(y_test, prob_test, y_ext, prob_ext, out_path):
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    for ax, y, p, title in [
        (axes[0], y_test, prob_test, "MIMIC-IV internal test"),
        (axes[1], y_ext, prob_ext, "MIMIC-III external"),
    ]:
        prob_true, prob_pred = calibration_curve(y, p, n_bins=8, strategy="quantile")
        ax.plot([0, 1], [0, 1], "k--", lw=1)
        ax.plot(prob_pred, prob_true, "o-", label="8-feature ensemble")
        ax.set_title(title)
        ax.set_xlabel("Predicted probability")
        ax.set_ylabel("Observed fraction")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def main():
    for d in (PREDS, TABLES, FIGURES, OUT / "model_weight"):
        d.mkdir(parents=True, exist_ok=True)

    f20 = primary_features(load_lasso_features(20))
    f8 = [f for f in FEAT8]

    res20, model20, imp20, sc20, _ = train_and_predict(f20, "20_features")
    res8, model8, imp8, sc8, _ = train_and_predict(f8, "8_features")

    write_table23(
        {"test": res20["test"], "external": res20["external"]},
        {"test": res8["test"], "external": res8["external"]},
    )

    ext_rows = []
    all_cal = []
    if external_cohorts_available():
        f3 = load_corrected_f3_feature_table()
        nh = load_corrected_nh_feature_table()
        f3["hospital_expire_flag"] = f3["hospital_expire_flag"].astype(int)
        nh["hospital_expire_flag"] = nh["hospital_expire_flag"].astype(int)

        for tag, df in [("F3", f3), ("NH", nh)]:
            y, prob, n, ev = infer_external(model8, imp8, sc8, f8, df)
            auc, lo, hi = delong_ci(y, prob)
            ext_rows.append({"Cohort": tag, "n": n, "Events": ev, "AUROC": auc, "CI_lo": lo, "CI_hi": hi})
            with open(PREDS / f"8_features_{tag}_preds.pkl", "wb") as f:
                pickle.dump(
                    [
                        {
                            "model_name": "Ensemble_Voting",
                            "lable": y.tolist(),
                            "pred_prob": prob.tolist(),
                            "n": n,
                            "events": ev,
                        }
                    ],
                    f,
                )
            all_cal.append((tag, y, prob))
    else:
        print("Skipping F3/NH: data/external/ cohort workbook not found (MIMIC-only path)")

    pd.DataFrame(ext_rows).to_csv(TABLES / "external_f3_nh.csv", index=False)

    all_cal.extend(
        [
            ("MIMIC-IV test 8f", np.array(res8["test"]["lable"]), np.array(res8["test"]["pred_prob"])),
            ("MIMIC-III external 8f", np.array(res8["external"]["lable"]), np.array(res8["external"]["pred_prob"])),
        ]
    )
    write_table6(all_cal)

    m4_raw = pd.read_excel(DATA_PATH, sheet_name="mimic4_low_fe")
    test_ids = pd.read_csv(COHORT / "mimic4_test_ids.csv")
    write_s8_s9(m4_raw, test_ids, model20, imp20, sc20, f20)

    plot_figure5(
        np.array(res8["test"]["lable"]),
        np.array(res8["test"]["pred_prob"]),
        np.array(res8["external"]["lable"]),
        np.array(res8["external"]["pred_prob"]),
        FIGURES / "figure5_calibration.png",
    )

    manifest_path = OUT / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["training"] = {
        "model": "Ensemble_Voting_soft",
        "imbalance": "class_weight_balanced_primary",
        "imputer": "KNN_k5_train_fit",
    }
    manifest["metrics"] = {
        "mimic4_test_8f_auroc": res8["test"]["auroc"],
        "mimic3_external_8f_auroc": res8["external"]["auroc"],
        "mimic4_test_events": res8["test"]["events"],
        "mimic3_external_events": res8["external"]["events"],
        "mimic4_test_20f_auroc": res20["test"]["auroc"],
        "mimic3_external_20f_auroc": res20["external"]["auroc"],
    }
    if len(ext_rows) >= 2:
        manifest["metrics"].update(
            {
                "F3_auroc": ext_rows[0]["AUROC"],
                "NH_auroc": ext_rows[1]["AUROC"],
                "F3_events": ext_rows[0]["Events"],
                "NH_events": ext_rows[1]["Events"],
            }
        )
    manifest["external_cohorts_evaluated"] = external_cohorts_available()
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest["metrics"], indent=2))
    _export_legacy_pred_layout(sc8, sc20)


def _export_legacy_pred_layout(sc8, sc20):
    import shutil

    subdirs = {
        "20_features": [
            ("test_preds.pkl", "20_features_test_preds.pkl"),
            ("external_preds.pkl", "20_features_external_preds.pkl"),
            ("val_preds.pkl", "20_features_external_preds.pkl"),
        ],
        "8_features": [
            ("test_preds.pkl", "8_features_test_preds.pkl"),
            ("external_preds.pkl", "8_features_external_preds.pkl"),
            ("val_preds.pkl", "8_features_external_preds.pkl"),
            ("F3_preds.pkl", "8_features_F3_preds.pkl"),
            ("NH_preds.pkl", "8_features_NH_preds.pkl"),
        ],
    }
    for sub, pairs in subdirs.items():
        d = PREDS / sub
        d.mkdir(parents=True, exist_ok=True)
        for dest, src in pairs:
            src_path = PREDS / src
            if src_path.exists():
                shutil.copy2(src_path, d / dest)
    for tag, scaler in [("8_features", sc8), ("20_features", sc20)]:
        wdir = OUT / "model_weight" / tag
        wdir.mkdir(parents=True, exist_ok=True)
        with open(wdir / "stand_encoder.pkl", "wb") as f:
            pickle.dump(scaler, f)


if __name__ == "__main__":
    main()

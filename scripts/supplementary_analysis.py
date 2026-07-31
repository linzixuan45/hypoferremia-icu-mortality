#!/usr/bin/env python3
"""Supplementary analysis — DCA, sensitivities, S6-S15, Figure 5/7, TRIPOD/PROBAST."""
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
from sklearn.experimental import enable_iterative_imputer  # noqa: F401
from sklearn.impute import IterativeImputer
from sklearn.metrics import (
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

from train_models import (
    FEAT8,
    build_stacking,
    delong_ci,
    impute_scale,
    load_lasso20,
    prep_frame,
    youden_threshold,
)
from build_t0_cohort import primary_features
from external_cohort_data import external_cohorts_available
from dataset import MIMIC3_THRESHOLD, MISSING_THRESHOLD

OUT = ROOT / "result" / "analysis"
TABLES = OUT / "tables"
FIGURES = OUT / "figures"
PREDS8 = OUT / "preds" / "8_features"
PREDS20 = OUT / "preds" / "20_features"
DATA_PATH = ROOT / "data" / "mimic_dataset.xlsx"
COHORT = OUT / "cohorts"
RANDOM_STATE = 42


def _eval_cohort_splits() -> list[tuple[str, str]]:
    cohorts = [("MIMIC-IV internal test", "test"), ("MIMIC-III external", "external")]
    if external_cohorts_available():
        cohorts.extend([("F3", "F3"), ("NH", "NH")])
    return cohorts


def _pred_path(split: str, tag: str = "8_features") -> Path:
    if split == "val":
        split = "external"
    for path in (
        OUT / "preds" / f"{tag}_{split}_preds.pkl",
        PREDS8 / f"{split}_preds.pkl",
    ):
        if path.exists():
            return path
    raise FileNotFoundError(f"No predictions for split={split} tag={tag}")


def load_pkl(path):
    with open(path, "rb") as f:
        return pickle.load(f)


def load_stacking(tag: str = "8_features"):
    bundle = load_pkl(OUT / "model_weight" / tag / "model_weight.pkl")
    model = bundle.get("Ensemble_Voting") or bundle.get("Ensemble_Stacking") or bundle.get("model")
    if model is None:
        raise KeyError(f"No ensemble model in {tag} bundle; keys={list(bundle.keys())}")
    return model, bundle["imputer"], bundle["scaler"], bundle["features"]


def _load_pred_any(split: str, tag: str = "8_features"):
    path = _pred_path(split, tag)
    d = load_pkl(path)[0]
    return np.array(d["lable"]), np.array(d["pred_prob"])


def dca_nb(y_true, y_prob, thresholds):
    y_true = np.asarray(y_true, dtype=int)
    y_prob = np.asarray(y_prob, dtype=float)
    nb = []
    for t in thresholds:
        pred = y_prob >= t
        tp = np.sum(pred & (y_true == 1))
        fp = np.sum(pred & (y_true == 0))
        n = len(y_true)
        nb.append(tp / n - fp / n * (t / (1 - t)) if t < 1 else 0)
    return np.array(nb)


def treat_all_nb(y_true, thresholds):
    prev = np.mean(y_true)
    return np.array([prev - (1 - prev) * (t / (1 - t)) if t < 1 else 0 for t in thresholds])


def sofa_probs(y, sofa_scores):
    s = np.asarray(sofa_scores, dtype=float)
    mask = np.isfinite(s)
    if mask.sum() < 10:
        return None
    from sklearn.linear_model import LogisticRegression

    lr = LogisticRegression(max_iter=500)
    lr.fit(s[mask].reshape(-1, 1), y[mask])
    prob = np.full(len(y), np.nan)
    prob[mask] = lr.predict_proba(s[mask].reshape(-1, 1))[:, 1]
    return prob


# ── P1: DCA + SOFA ──────────────────────────────────────────────────


def generate_dca_figures():
    print("DCA figures...")
    thresholds_full = np.linspace(0.01, 0.99, 99)
    thresholds_main = np.linspace(0.15, 0.40, 50)

    cohorts = [
        ("MIMIC-IV internal test", "test"),
        ("MIMIC-III external", "external"),
    ]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    for ax, (title, split) in zip(axes, cohorts):
        y, prob = _load_pred_any(split)
        nb_m = dca_nb(y, prob, thresholds_main)
        nb_a = treat_all_nb(y, thresholds_main)
        ax.plot(thresholds_main, nb_m, "r-", lw=2, label="8-feature ML")
        ax.plot(thresholds_main, nb_a, "k--", lw=1, label="Treat all")
        ax.axhline(0, color="gray", ls=":", lw=1, label="Treat none")
        ax.set_xlim(0.15, 0.40)
        ax.set_xlabel("Threshold probability")
        ax.set_ylabel("Net benefit")
        ax.set_title(f"{title} (n={len(y)})")
        ax.legend(fontsize=8)
        ax.grid(alpha=0.3)
    fig.suptitle("Figure 5B: Decision curve analysis (0.15–0.40)", fontsize=12)
    fig.tight_layout()
    fig.savefig(FIGURES / "figure5_dca_main.png", dpi=200, bbox_inches="tight")
    plt.close(fig)

    # Supp S5 — available cohorts only
    datasets = {
        "MIMIC-IV internal test": PREDS8 / "test_preds.pkl",
        "MIMIC-III external": PREDS8 / "external_preds.pkl",
    }
    if external_cohorts_available():
        datasets["F3"] = PREDS8 / "F3_preds.pkl"
        datasets["NH"] = PREDS8 / "NH_preds.pkl"
    datasets = {k: v for k, v in datasets.items() if v.exists()}
    n_panels = len(datasets)
    ncols = 2 if n_panels > 1 else 1
    nrows = (n_panels + ncols - 1) // ncols
    fig2, axes2 = plt.subplots(nrows, ncols, figsize=(6 * ncols, 5 * nrows))
    axes_flat = np.atleast_1d(axes2).flatten()
    for ax, (label, path) in zip(axes_flat, datasets.items()):
        d = load_pkl(path)[0]
        y, prob = np.array(d["lable"]), np.array(d["pred_prob"])
        nb_m = dca_nb(y, prob, thresholds_full)
        nb_a = treat_all_nb(y, thresholds_full)
        ax.plot(thresholds_full, nb_m, "r-", lw=2, label="ML")
        ax.plot(thresholds_full, nb_a, "k--", lw=1, label="Treat all")
        ax.axhline(0, color="gray", ls=":", lw=1)
        ax.set_title(f"{label} (n={len(y)})")
        ax.legend(fontsize=8)
        ax.grid(alpha=0.3)
    for ax in axes_flat[len(datasets) :]:
        ax.set_visible(False)
    fig2.suptitle("Supplementary Figure S5: DCA all cohorts", fontsize=12)
    fig2.tight_layout()
    fig2.savefig(FIGURES / "figure_s5_dca_all.png", dpi=200, bbox_inches="tight")
    plt.close(fig2)

    # Supp S7 with SOFA (MIMIC-III external)
    m3 = pd.read_excel(DATA_PATH, sheet_name="mimic3_low_fe")
    ext_ids = pd.read_csv(COHORT / "mimic3_external_ids.csv")
    id_m3 = "icustay_id" if "icustay_id" in m3.columns else "subject_id"
    m3m = m3.merge(ext_ids, on=id_m3, how="inner")
    y_ext, prob_ext = _load_pred_any("external")
    sofa_col = "sofa_score" if "sofa_score" in m3m.columns else "SOFA"
    sofa_p = sofa_probs(y_ext, m3m[sofa_col].values[: len(y_ext)])
    fig3, ax3 = plt.subplots(figsize=(7, 5))
    nb_ml = dca_nb(y_ext, prob_ext, thresholds_main)
    ax3.plot(thresholds_main, nb_ml, "r-", lw=2, label="8-feature ML")
    if sofa_p is not None:
        nb_s = dca_nb(y_ext, sofa_p, thresholds_main)
        ax3.plot(thresholds_main, nb_s, "b-", lw=2, label="SOFA alone")
    ax3.plot(thresholds_main, treat_all_nb(y_ext, thresholds_main), "k--", lw=1, label="Treat all")
    ax3.axhline(0, color="gray", ls=":", lw=1)
    ax3.set_xlim(0.15, 0.40)
    ax3.set_title("Supplementary Figure S7: DCA vs SOFA (MIMIC-III external)")
    ax3.legend()
    ax3.grid(alpha=0.3)
    fig3.tight_layout()
    fig3.savefig(FIGURES / "figure_s7_dca_sofa.png", dpi=200, bbox_inches="tight")
    plt.close(fig3)


# ── P1/P2: LOS sensitivity S14 ──────────────────────────────────────


def los_sensitivity_s14():
    print("LOS sensitivity S14...")
    from train_models import load_cohort_frames

    f18 = primary_features(load_lasso20())
    los_cols = [c for c in f18 if "los" in c.lower()]
    _, test, _ = load_cohort_frames("parquet")

    model, imp, scaler, model_feats = load_stacking("20_features")
    rows = []
    for label, drop_los in [("With LOS predictors", False), ("Without LOS predictors", True)]:
        feats = [c for c in f18 if c not in los_cols] if drop_los else f18
        sub = prep_frame(test, feats, label_col="outcome_28d_t0")
        X = sub[feats]
        y = sub["outcome_28d_t0"].astype(int)
        if drop_los:
            m, imp2, sc2 = _quick_train(feats)
            Xs = pd.DataFrame(sc2.transform(pd.DataFrame(imp2.transform(X), columns=feats)), columns=feats)
            prob = m.predict_proba(Xs)[:, 1]
        else:
            Xs = pd.DataFrame(
                scaler.transform(pd.DataFrame(imp.transform(X), columns=model_feats)),
                columns=model_feats,
            )
            prob = model.predict_proba(Xs)[:, 1]
        auc, lo, hi = delong_ci(y, prob)
        rows.append({"Analysis": label, "n": len(y), "Events": int(y.sum()), "AUROC": auc, "CI_lo": lo, "CI_hi": hi})
    pd.DataFrame(rows).to_csv(TABLES / "table_s14_los_sensitivity.csv", index=False)

    fig, ax = plt.subplots(figsize=(6, 4))
    for i, row in enumerate(rows):
        ax.bar(i, row["AUROC"], yerr=[[row["AUROC"] - row["CI_lo"]], [row["CI_hi"] - row["AUROC"]]], capsize=4)
        ax.set_xticks(range(len(rows)))
        ax.set_xticklabels([r["Analysis"] for r in rows], rotation=15, ha="right")
        ax.set_ylabel("AUROC")
        ax.set_ylim(0, 1)
    ax.set_title("Supplementary Figure S8: LOS predictor sensitivity")
    fig.tight_layout()
    fig.savefig(FIGURES / "figure_s8_los_sensitivity.png", dpi=150)
    plt.close(fig)


def _quick_train(features):
    from train_models import load_cohort_frames

    train, _, _ = load_cohort_frames("parquet")
    tr = prep_frame(train, features, label_col="outcome_28d_t0")
    X = tr[features]
    y = tr["outcome_28d_t0"].astype(int)
    imp = IterativeImputer(max_iter=5, random_state=RANDOM_STATE)
    X_i = pd.DataFrame(imp.fit_transform(X), columns=features)
    sc = StandardScaler()
    Xs = pd.DataFrame(sc.fit_transform(X_i), columns=features)
    m = build_stacking()
    m.fit(Xs, y)
    return m, imp, sc


# ── P2: ICU stay S10 ────────────────────────────────────────────────


def _s10_train_eval(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    val_df: pd.DataFrame,
    feats: list[str],
    los_min: float,
) -> list[dict] | None:
    """Retrain 8-feature stacking on train; evaluate test and val."""
    use_feats = [f for f in feats if f in train_df.columns and f in test_df.columns and f in val_df.columns]
    if len(use_feats) < len(feats):
        return None

    train_p = prep_frame(train_df, use_feats, label_col="outcome_28d_t0", los_icu_min=los_min)
    test_p = prep_frame(test_df, use_feats, label_col="outcome_28d_t0", los_icu_min=los_min)
    val_p = prep_frame(val_df, use_feats, label_col="outcome_28d_t0", los_icu_min=los_min)

    y_tr = train_p["outcome_28d_t0"].astype(int)
    if y_tr.nunique() < 2 or len(train_p) < 40:
        return None

    X_tr = train_p[use_feats]
    _, X_tr_s, _, [X_te_s, X_va_s], _, _ = impute_scale(X_tr, [test_p[use_feats], val_p[use_feats]])
    y_te = test_p["outcome_28d_t0"].astype(int)
    y_va = val_p["outcome_28d_t0"].astype(int)

    model = build_stacking()
    model.fit(X_tr_s, y_tr)

    out = []
    for tag, X_s, y in [("MIMIC-IV internal test", X_te_s, y_te), ("MIMIC-III external", X_va_s, y_va)]:
        if len(y) < 20 or y.nunique() < 2:
            continue
        prob = model.predict_proba(X_s)[:, 1]
        auc, lo, hi = delong_ci(y, prob)
        out.append(
            {
                "Cohort": tag,
                "n": len(y),
                "Events": int(y.sum()),
                "AUROC": auc,
                "CI": f"{lo:.3f}-{hi:.3f}",
            }
        )
    return out


def icu_stay_los_sensitivity():
    """Exploratory LOS inclusion sensitivity (not FE1 Supp S10 legacy window)."""
    print("ICU stay LOS sensitivity (exploratory)...")
    from build_t0_cohort import (
        apply_base_filters,
        attach_outcomes,
        clean_raw,
        feature_complete,
        load_raw,
        merge_t0_labs,
    )
    from sklearn.model_selection import train_test_split

    m4_raw, m3_raw = load_raw()
    m3_clean, m4_clean = clean_raw(m3_raw, m4_raw)
    m3_m, m4_m, t0_src = merge_t0_labs(m3_clean, m4_clean)
    m3 = attach_outcomes(m3_raw, m3_m, t0_src)
    m4 = attach_outcomes(m4_raw, m4_m, t0_src)

    feats = FEAT8
    train_ids = pd.read_csv(COHORT / "mimic4_train_ids.csv")
    test_ids = pd.read_csv(COHORT / "mimic4_test_ids.csv")
    val_ids = pd.read_csv(COHORT / "mimic3_external_ids.csv")
    id_m3 = "icustay_id" if "icustay_id" in m3.columns else "subject_id"
    id_m4 = "subject_id" if "subject_id" in m4.columns else "icustay_id"

    rows = []
    for hours, days in [(6, 6 / 24), (12, 12 / 24), (24, 1.0)]:
        m3_f = feature_complete(apply_base_filters(m3, los_icu_min_days=days), feats)
        m4_f = feature_complete(apply_base_filters(m4, los_icu_min_days=days), feats)

        if hours == 24:
            train_df = m4_f.merge(train_ids[[id_m4]], on=id_m4, how="inner")
            test_df = m4_f.merge(test_ids[[id_m4]], on=id_m4, how="inner")
            val_df = m3_f.merge(val_ids[[id_m3]], on=id_m3, how="inner")
        else:
            y_all = m4_f["outcome_28d_t0"]
            if y_all.nunique() < 2 or len(m4_f) < 40:
                print(f"  WARN LOS sensitivity: skip {hours}h — insufficient MIMIC-IV pool")
                continue
            train_idx, test_idx = train_test_split(
                m4_f.index, test_size=0.2, random_state=RANDOM_STATE, stratify=y_all
            )
            train_df = m4_f.loc[train_idx]
            test_df = m4_f.loc[test_idx]
            val_df = m3_f

        eval_rows = _s10_train_eval(train_df, test_df, val_df, feats, days)
        if eval_rows is None:
            print(f"  WARN LOS sensitivity: skip {hours}h — train fold failed")
            continue
        for er in eval_rows:
            rows.append(
                {
                    "ICU_min_hours": hours,
                    "Model": "8-feature",
                    **er,
                }
            )

    pd.DataFrame(rows).to_csv(TABLES / "table_s10_icu_los_sensitivity.csv", index=False)
    ns = pd.DataFrame(rows)["n"].unique().tolist() if rows else []
    print(f"  LOS sensitivity rows: {len(rows)} unique n: {ns}")
    if rows:
        r24 = [r for r in rows if r["ICU_min_hours"] == 24 and r["Cohort"] == "MIMIC-IV internal test"]
        if r24:
            print(f"  24h MIMIC-IV internal test: n={r24[0]['n']} AUROC={r24[0]['AUROC']:.3f}")


# ── P2: MIMIC-IV develop → MIMIC-III test S12 ───────────────────────


def reverse_temporal_s12():
    print("Reverse temporal S12 (MIMIC-III train → MIMIC-IV test)...")
    f8 = FEAT8
    m3 = pd.read_excel(DATA_PATH, sheet_name="mimic3_low_fe").dropna(thresh=MIMIC3_THRESHOLD, axis=1)
    m4 = pd.read_excel(DATA_PATH, sheet_name="mimic4_low_fe").dropna(thresh=MISSING_THRESHOLD, axis=1)
    test_ids = pd.read_csv(COHORT / "mimic4_test_ids.csv")
    ext_ids = pd.read_csv(COHORT / "mimic3_external_ids.csv")
    id_m3 = "icustay_id" if "icustay_id" in m3.columns else "subject_id"
    id_m4 = "subject_id" if "subject_id" in m4.columns else "icustay_id"
    train = m3.merge(ext_ids, on=id_m3, how="inner")
    test = m4.merge(test_ids, on=id_m4, how="inner")
    tr = prep_frame(train, f8)
    te = prep_frame(test, f8)
    _, Xtr_s, _, [Xte_s], imp, sc = impute_scale(tr[f8], [te[f8]])
    ytr = tr["hospital_expire_flag"].astype(int)
    yte = te["hospital_expire_flag"].astype(int)
    m = build_stacking()
    m.fit(Xtr_s, ytr)
    prob = m.predict_proba(Xte_s)[:, 1]
    auc, lo, hi = delong_ci(yte, prob)
    pd.DataFrame(
        [{"Analysis": "MIMIC-III train → MIMIC-IV test", "n": len(yte), "Events": int(yte.sum()), "AUROC": auc, "CI_lo": lo, "CI_hi": hi}]
    ).to_csv(TABLES / "table_s12_reverse_temporal.csv", index=False)


# ── P2: Alternative thresholds S13 ──────────────────────────────────


def alternative_thresholds_s13():
    print("Alternative thresholds S13...")
    rows = []
    for cohort_label, split in _eval_cohort_splits():
        y, prob = _load_pred_any(split)
        fpr, tpr, thr = roc_curve(y, prob)
        j = tpr - fpr
        youden_t = float(thr[np.argmax(j)])
        for name, t in [("Youden", youden_t), ("Sens_0.85", _threshold_at_sens(y, prob, 0.85)), ("Sens_0.90", _threshold_at_sens(y, prob, 0.90))]:
            pred = (prob >= t).astype(int)
            tn, fp, fn, tp = confusion_matrix(y, pred).ravel()
            sens = tp / (tp + fn) if tp + fn else 0
            spec = tn / (tn + fp) if tn + fp else 0
            ppv = tp / (tp + fp) if tp + fp else 0
            npv = tn / (tn + fn) if tn + fn else 0
            rows.append(
                {
                    "Cohort": cohort_label,
                    "Threshold_rule": name,
                    "Threshold": round(t, 4),
                    "Sensitivity": round(sens, 3),
                    "Specificity": round(spec, 3),
                    "PPV": round(ppv, 3),
                    "NPV": round(npv, 3),
                    "F1": round(f1_score(y, pred, zero_division=0), 3),
                }
            )
    pd.DataFrame(rows).to_csv(TABLES / "table_s13_thresholds.csv", index=False)


def _threshold_at_sens(y, prob, target):
    fpr, tpr, thr = roc_curve(y, prob)
    idx = np.where(tpr >= target)[0]
    return float(thr[idx[0]]) if len(idx) else 0.5


# ── P2: DeLong S15 ──────────────────────────────────────────────────


def delong_pairwise_s15():
    print("DeLong S15...")
    rows = []
    for cohort, split in _eval_cohort_splits():
        y, p8 = _load_pred_any(split)
        try:
            _, p20 = _load_pred_any(split, "20_features")
        except FileNotFoundError:
            rows.append({"Cohort": cohort, "AUROC_20": "NA", "CI_20": "NA", "AUROC_8": round(delong_ci(y, p8)[0], 3), "CI_8": "NA", "DeLong_p": "NA"})
            continue
        auc8, lo8, hi8 = delong_ci(y, p8)
        auc20, lo20, hi20 = delong_ci(y, p20)
        p_val = _delong_pvalue(y, p8, p20)
        rows.append(
            {
                "Cohort": cohort,
                "AUROC_20": round(auc20, 3),
                "CI_20": f"{lo20:.3f}-{hi20:.3f}",
                "AUROC_8": round(auc8, 3),
                "CI_8": f"{lo8:.3f}-{hi8:.3f}",
                "DeLong_p": round(p_val, 4) if np.isfinite(p_val) else "NA",
            }
        )
    pd.DataFrame(rows).to_csv(TABLES / "table_s15_delong_pairwise.csv", index=False)


def _delong_pvalue(y, s1, s2):
    try:
        from scipy.stats import norm

        auc1 = roc_auc_score(y, s1)
        auc2 = roc_auc_score(y, s2)
        n1 = np.sum(y == 1)
        n0 = np.sum(y == 0)
        if n1 < 5 or n0 < 5:
            return np.nan
        # Hanley-McNeil approximate SE for difference
        q1 = auc1 / (2 - auc1)
        q2 = 2 * auc1**2 / (1 + auc1)
        se1 = np.sqrt((auc1 * (1 - auc1) + (n1 - 1) * (q1 - auc1**2) + (n0 - 1) * (q2 - auc1**2)) / (n1 * n0))
        q1 = auc2 / (2 - auc2)
        q2 = 2 * auc2**2 / (1 + auc2)
        se2 = np.sqrt((auc2 * (1 - auc2) + (n1 - 1) * (q1 - auc2**2) + (n0 - 1) * (q2 - auc2**2)) / (n1 * n0))
        se_diff = np.sqrt(se1**2 + se2**2)
        z = (auc1 - auc2) / se_diff if se_diff > 0 else 0
        return 2 * (1 - norm.cdf(abs(z)))
    except Exception:
        return np.nan


# ── P1: TRIPOD S7 + PROBAST S11 ─────────────────────────────────────


def generate_tripod_s7():
    print("TRIPOD S7...")
    items = [
        ("5a", "Outcome", "28-day mortality from first iron <60 µg/dL (t0)", "Methods Index time; FE1_spec"),
        ("5b", "Predictors", "All predictors at or before t0", "Methods; FE1_spec §5"),
        ("7a", "Analysis", "No random undersampling; natural prevalence", "Methods"),
        ("10a", "Performance", "AUROC with DeLong CI from train_models", "Tables 2-3; manifest.json"),
        ("AI-7", "Reproducibility", "GitHub release + manifest", "Project_low_Fe repository"),
    ]
    base_path = ROOT / "config" / "table_s7_tripod_ai_checklist.csv"
    if not base_path.exists():
        base_path = ROOT / "result" / "revision_outputs" / "table_s7_tripod_ai_checklist.csv"
    base = pd.read_csv(base_path)
    extra = pd.DataFrame(items, columns=["Item", "Section", "Description", "Location in Manuscript"])
    out = pd.concat([base, extra]).drop_duplicates(subset=["Item"], keep="last")
    out.to_csv(TABLES / "table_s7_tripod_checklist.csv", index=False)


def generate_probast_s11():
    print("PROBAST S11...")
    rows = [
        {"Domain": "Participants", "Arm": "Development (MIMIC-IV)", "Rating": "Moderate", "Note": "t0-proxy; S10 legacy sensitivity"},
        {"Domain": "Participants", "Arm": "External (MIMIC-III)", "Rating": "Moderate", "Note": "Non-training same-institution temporal evaluation"},
        {"Domain": "Participants", "Arm": "External (F3/NH)", "Rating": "High", "Note": "Small n; exploratory geographic only"},
        {"Domain": "Predictors", "Arm": "All", "Rating": "Moderate", "Note": "Excel proxy t0 until SQL export"},
        {"Domain": "Outcome", "Arm": "All", "Rating": "Low", "Note": "Hospital mortality objectively ascertained"},
        {"Domain": "Analysis", "Arm": "Development", "Rating": "Moderate", "Note": "Natural prevalence; no random undersampling"},
        {"Domain": "Analysis", "Arm": "External", "Rating": "Moderate", "Note": "NH ensemble-driven label refinement"},
    ]
    pd.DataFrame(rows).to_csv(TABLES / "table_s11_probast_ai.csv", index=False)


# ── P1: Figure 7 SHAP (XGB base from stacking) ──────────────────────


def compose_figure7_composite(col_width: int = 600) -> Path | None:
    """2×2 layout: 7A | 7B / 7C | 7D (same pattern as paper/low_k/compose_figure_7.py)."""
    try:
        from PIL import Image
    except ImportError:
        print("  skip composite: Pillow not installed")
        return None

    paths = [
        FIGURES / "figure7a_shap_summary.png",
        FIGURES / "figure7b_roc_four_cohorts.png",
        FIGURES / "figure7c_shap_force.png",
        FIGURES / "figure7d_shap_force.png",
    ]
    for p in paths:
        if not p.exists():
            print(f"  skip composite: missing {p}")
            return None

    def fit_width(im, w):
        scale = w / im.width
        return im.resize((w, int(im.height * scale)), Image.Resampling.LANCZOS)

    a, b, c, d = (fit_width(Image.open(p).convert("RGB"), col_width) for p in paths)
    top_h = max(a.height, b.height)
    bottom_h = max(c.height, d.height)
    out = Image.new("RGB", (col_width * 2, top_h + bottom_h), (255, 255, 255))
    out.paste(a, (0, 0))
    out.paste(b, (col_width, 0))
    out.paste(c, (0, top_h))
    out.paste(d, (col_width, top_h))
    composite = FIGURES / "figure7_composite.png"
    out.save(composite)
    print(f"  Saved: {composite} (4-panel 7A|7B / 7C|7D)")
    return composite


def _pick_force_plot_cases(y, pred_prob, shap_values_survival, base_val_survival):
    """Panel C = high-risk (dead); panel D = low-risk (alive)."""
    survival_score = base_val_survival + np.asarray(shap_values_survival).sum(axis=1)
    alive = np.where(y == 0)[0]
    dead = np.where(y == 1)[0]
    if len(alive) == 0 or len(dead) == 0:
        return None, None
    alive_conf = alive[pred_prob[alive] < 0.02]
    dead_conf = dead[pred_prob[dead] > 0.98]
    if len(alive_conf) == 0:
        alive_conf = alive
    if len(dead_conf) == 0:
        dead_conf = dead
    high_idx = int(dead_conf[np.argmin(survival_score[dead_conf])])
    low_idx = int(alive_conf[np.argmax(survival_score[alive_conf])])
    return high_idx, low_idx


def generate_figure7_shap():
    print("Figure 7 SHAP...")
    try:
        import shap
    except ImportError:
        print("  skip: shap not installed")
        return

    model, imp, scaler, feats = load_stacking("8_features")
    xgb = model.named_estimators_["xgb"]
    m3 = pd.read_excel(DATA_PATH, sheet_name="mimic3_low_fe")
    ext_ids = pd.read_csv(COHORT / "mimic3_external_ids.csv")
    id_m3 = "icustay_id" if "icustay_id" in m3.columns else "subject_id"
    ext = m3.merge(ext_ids, on=id_m3, how="inner")
    sub = prep_frame(ext, feats).head(200)
    X = sub[feats]
    Xs = pd.DataFrame(scaler.transform(pd.DataFrame(imp.transform(X), columns=feats)), columns=feats)

    explainer = shap.TreeExplainer(xgb)
    sv = explainer.shap_values(Xs)
    if isinstance(sv, list):
        sv = sv[1]

    plt.figure(figsize=(8, 6))
    shap.summary_plot(sv, Xs, show=False, max_display=8)
    plt.tight_layout()
    plt.savefig(FIGURES / "figure7a_shap_summary.png", dpi=200, bbox_inches="tight")
    plt.close()

    # ROC four cohort
    fig, ax = plt.subplots(figsize=(6, 5))
    manifest = json.loads((OUT / "manifest.json").read_text())
    m = manifest["metrics"]
    labels = [
        ("MIMIC-IV internal test", "test", m["mimic4_test_8f_auroc"]),
        ("MIMIC-III external", "external", m["mimic3_external_8f_auroc"]),
    ]
    if external_cohorts_available() and "F3_auroc" in m:
        labels.extend([("F3", "F3", m["F3_auroc"]), ("NH", "NH", m["NH_auroc"])])
    for name, split, auc_target in labels:
        y, prob = _load_pred_any(split)
        fpr, tpr, _ = roc_curve(y, prob)
        ax.plot(fpr, tpr, lw=2, label=f"{name} (AUROC={auc_target:.3f})")
    ax.plot([0, 1], [0, 1], "k--")
    ax.set_xlabel("FPR")
    ax.set_ylabel("TPR")
    ax.legend(fontsize=8)
    ax.set_title("Figure 7B: ROC four cohorts")
    fig.tight_layout()
    fig.savefig(FIGURES / "figure7b_roc_four_cohorts.png", dpi=200)
    plt.close(fig)

    # 7C & 7D: SHAP force plots on full MIMIC-III external cohort
    sub_full = prep_frame(ext, feats)
    X_full = sub_full[feats]
    Xi_full = pd.DataFrame(imp.transform(X_full), columns=feats)
    Xs_full = pd.DataFrame(scaler.transform(Xi_full), columns=feats)
    y_full = sub_full["hospital_expire_flag"].astype(int).values
    pred_prob = xgb.predict_proba(Xs_full)[:, 1]

    sv_raw = explainer.shap_values(Xs_full)
    if isinstance(sv_raw, list):
        shap_values_survival = sv_raw[0]
        exp_val = np.atleast_1d(explainer.expected_value)
        base_val_survival = exp_val[0] if len(exp_val) > 1 else -float(exp_val[0])
    else:
        shap_values_survival = -np.asarray(sv_raw)
        base_val_survival = -float(np.atleast_1d(explainer.expected_value).flat[0])

    high_idx, low_idx = _pick_force_plot_cases(
        y_full, pred_prob, shap_values_survival, base_val_survival
    )
    if high_idx is None:
        print("  skip 7C/7D: no alive/dead samples in external cohort")
    else:
        X_disp = Xi_full.round(2)
        for idx, fname, label in [
            (high_idx, "figure7c_shap_force.png", "high-risk"),
            (low_idx, "figure7d_shap_force.png", "low-risk"),
        ]:
            shap.force_plot(
                base_val_survival,
                shap_values_survival[idx],
                X_disp.iloc[idx],
                matplotlib=True,
                show=False,
                figsize=(20, 5),
                feature_names=feats,
                contribution_threshold=0.1,
            )
            plt.tight_layout()
            out_path = FIGURES / fname
            plt.savefig(out_path, dpi=200, bbox_inches="tight")
            plt.close()
            print(
                f"  Saved: {out_path} ({label}; pred_death={pred_prob[idx]:.4f})"
            )

    compose_figure7_composite()


# ── Table 4 summary from subgroup ───────────────────────────────────


def table4_from_subgroup():
    print("Table 4 from subgroup (8-feature)...")
    from subgroup_analysis import run_subgroup_analysis
    from train_models import calibration_metrics

    results = run_subgroup_analysis(model_tag="8_features")
    out_path = TABLES / "table4_subgroup_summary.csv"
    main_subgroups = [
        "Overall",
        "Age <= 65",
        "Age > 65",
        "Male",
        "Female",
        "Admission hypoferremia",
        "Acquired hypoferremia",
    ]
    calib = {}
    for split, label in [("test", "MIMIC-IV internal test"), ("external", "MIMIC-III external")]:
        y, prob = _load_pred_any(split, tag="8_features")
        brier, slope, _ = calibration_metrics(y, prob)
        calib[label] = {"Brier": round(brier, 3), "Calibration_slope": round(slope, 3)}

    rows = []
    for sg in main_subgroups:
        for cohort in ["MIMIC-IV internal test", "MIMIC-III external"]:
            m = results[(results["Subgroup"] == sg) & (results["Cohort"] == cohort)]
            if len(m):
                row = m.iloc[0]
                entry = {
                    "Subgroup": sg,
                    "Cohort": cohort,
                    "n": row["n"],
                    "Events": row["Events"],
                    "AUROC": round(row["AUROC"], 3),
                    "AUROC_CI_lo": round(row["CI_lower"], 3),
                    "AUROC_CI_hi": round(row["CI_upper"], 3),
                    "AUROC_CI": row["AUROC (95% CI)"],
                }
                if sg == "Overall" and cohort in calib:
                    entry.update(calib[cohort])
                rows.append(entry)
    pd.DataFrame(rows).to_csv(out_path, index=False)
    results.to_csv(TABLES / "table_s6_subgroup_full.csv", index=False)


def main():
    TABLES.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)
    from fe1_extended_outputs import main as fe1_extended_main

    fe1_extended_main()
    generate_dca_figures()
    los_sensitivity_s14()
    icu_stay_los_sensitivity()
    reverse_temporal_s12()
    alternative_thresholds_s13()
    delong_pairwise_s15()
    generate_tripod_s7()
    generate_probast_s11()
    generate_figure7_shap()
    table4_from_subgroup()
    print("All extended outputs written to", OUT)


if __name__ == "__main__":
    main()

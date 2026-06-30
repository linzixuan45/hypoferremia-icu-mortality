#!/usr/bin/env python3
"""Table 5: SOFA / APACHE II / SAPS II vs ML on evaluation subsets."""
from __future__ import annotations

import json
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import brier_score_loss, roc_auc_score
from sklearn.linear_model import LogisticRegression

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

from train_models import delong_ci, calibration_metrics

OUT = ROOT / "result" / "analysis"
TABLES = OUT / "tables"
SEVERITY_PATH = ROOT / "data" / "mimic_severity_scores.parquet"
DATA_PATH = ROOT / "data" / "mimic_dataset.xlsx"
COHORT = OUT / "cohorts"


def delong_pvalue(y, s1, s2):
    """Approximate two-sided p-value for AUROC difference (Hanley-McNeil)."""
    from scipy.stats import norm

    y = np.asarray(y, dtype=int)
    s1 = np.asarray(s1, dtype=float)
    s2 = np.asarray(s2, dtype=float)
    auc1 = roc_auc_score(y, s1)
    auc2 = roc_auc_score(y, s2)
    n1 = np.sum(y == 1)
    n0 = np.sum(y == 0)
    if n1 < 5 or n0 < 5:
        return np.nan, np.nan, np.nan

    def _se_auc(auc, n_pos, n_neg):
        q1 = auc / (2 - auc)
        q2 = 2 * auc**2 / (1 + auc)
        return np.sqrt(
            (auc * (1 - auc) + (n_pos - 1) * (q1 - auc**2) + (n_neg - 1) * (q2 - auc**2))
            / (n_pos * n_neg)
        )

    se1 = _se_auc(auc1, n1, n0)
    se2 = _se_auc(auc2, n1, n0)
    se_diff = np.sqrt(se1**2 + se2**2)
    delta = auc1 - auc2
    z = delta / se_diff if se_diff > 0 else 0.0
    p = 2 * (1 - norm.cdf(abs(z)))
    zv = norm.ppf(0.975)
    delta_lo = delta - zv * se_diff
    delta_hi = delta + zv * se_diff
    return delta, delta_lo, delta_hi, p


def load_preds(tag: str, split: str):
    if split == "val":
        split = "external"
    with open(OUT / "preds" / f"{tag}_{split}_preds.pkl", "rb") as f:
        d = pickle.load(f)[0]
    return np.array(d["lable"]), np.array(d["pred_prob"]), d.get("auroc", np.nan)


def score_metrics(y, score):
    score = np.asarray(score, dtype=float)
    y = np.asarray(y, dtype=int)
    mask = np.isfinite(score)
    if mask.sum() < 10 or len(np.unique(y[mask])) < 2:
        return {"AUROC": np.nan, "Brier": np.nan, "Slope": np.nan}
    prob = score[mask]
    # normalize continuous scores to 0-1 for calibration via logistic link
    if prob.max() > 1.0 or prob.min() < 0:
        lr = LogisticRegression(max_iter=500)
        lr.fit(prob.reshape(-1, 1), y[mask])
        prob_cal = lr.predict_proba(prob.reshape(-1, 1))[:, 1]
    else:
        prob_cal = prob
    auc = roc_auc_score(y[mask], prob)
    brier, slope, _ = calibration_metrics(y[mask], prob_cal)
    return {"AUROC": auc, "Brier": brier, "Slope": slope}


def main():
    TABLES.mkdir(parents=True, exist_ok=True)
    rows = []

    # ML rows from saved predictions
    for model, tag in [("20-feature ML", "20_features"), ("8-feature ML", "8_features")]:
        for split, cohort in [("test", "MIMIC-IV internal test"), ("external", "MIMIC-III external")]:
            y, prob, _ = load_preds(tag, split)
            auc, lo, hi = delong_ci(y, prob)
            brier, slope, intercept = calibration_metrics(y, prob)
            rows.append(
                {
                    "Comparator": model,
                    "Cohort": cohort,
                    "n": len(y),
                    "Events": int(y.sum()),
                    "AUROC": round(auc, 3),
                    "AUROC_95CI": f"{lo:.3f}-{hi:.3f}",
                    "Brier": round(brier, 3),
                    "Calibration_slope": round(slope, 3),
                }
            )

    # Severity scores — sofa from excel proxy parquet
    if SEVERITY_PATH.exists():
        sev = pd.read_parquet(SEVERITY_PATH)
        m3 = pd.read_excel(DATA_PATH, sheet_name="mimic3_low_fe")
        m4 = pd.read_excel(DATA_PATH, sheet_name="mimic4_low_fe")
        test_ids = pd.read_csv(OUT / "cohorts" / "mimic4_test_ids.csv")
        ext_ids = pd.read_csv(OUT / "cohorts" / "mimic3_external_ids.csv")
        id_col_m3 = "icustay_id" if "icustay_id" in m3.columns else "subject_id"
        id_col_m4 = "subject_id" if "subject_id" in m4.columns else "icustay_id"

        for cohort_name, ids, raw, idc, outcome in [
            ("MIMIC-IV internal test", test_ids, m4, id_col_m4, "outcome_28d_t0"),
            ("MIMIC-III external", ext_ids, m3, id_col_m3, "outcome_28d_t0"),
        ]:
            merged = raw.merge(ids[[idc, outcome]], left_on=idc, right_on=idc, how="inner")
            if "sofa_at_t0" in sev.columns:
                scols = [c for c in ["sofa_at_t0", "apache_ii", "saps_ii"] if c in sev.columns]
                merged = merged.merge(
                    sev[["stay_id"] + scols].drop_duplicates("stay_id"),
                    left_on=idc,
                    right_on="stay_id",
                    how="left",
                )
            y = merged[outcome].astype(int).values
            for comp, col in [("SOFA", "sofa_at_t0"), ("SOFA", "sofa_score"), ("APACHE II", "apache_ii"), ("SAPS II", "saps_ii")]:
                if comp == "SOFA" and col == "sofa_score":
                    if "sofa_at_t0" in merged.columns and merged["sofa_at_t0"].notna().any():
                        continue
                if col not in merged.columns or not np.isfinite(pd.to_numeric(merged[col], errors="coerce")).any():
                    if comp in ("APACHE II", "SAPS II"):
                        rows.append(
                            {
                                "Comparator": comp,
                                "Cohort": cohort_name,
                                "n": len(y),
                                "Events": int(y.sum()),
                                "AUROC": "NA",
                                "AUROC_95CI": "requires SQL export",
                                "Brier": "NA",
                                "Calibration_slope": "NA",
                            }
                        )
                    continue
                sc = pd.to_numeric(merged[col], errors="coerce").values
                m = score_metrics(y, sc)
                auc = m["AUROC"]
                lo, hi = (np.nan, np.nan)
                if np.isfinite(auc):
                    lo, hi = delong_ci(y, sc if sc.max() <= 1 else sc / (sc.max() + 1e-6))[1:3]
                rows.append(
                    {
                        "Comparator": comp,
                        "Cohort": cohort_name,
                        "n": len(y),
                        "Events": int(y.sum()),
                        "AUROC": round(auc, 3) if np.isfinite(auc) else "NA",
                        "AUROC_95CI": f"{lo:.3f}-{hi:.3f}" if np.isfinite(lo) else "NA",
                        "Brier": round(m["Brier"], 3) if np.isfinite(m["Brier"]) else "NA",
                        "Calibration_slope": round(m["Slope"], 3) if np.isfinite(m["Slope"]) else "NA",
                    }
                )

    out_path = TABLES / "table5_severity_benchmark.csv"
    pd.DataFrame(rows).to_csv(out_path, index=False)
    print(f"Wrote {out_path} ({len(rows)} rows)")

    write_table5_incremental()


def _sofa_scores_for_cohort(cohort_name: str):
    """Return y, sofa scores aligned to evaluation cohort IDs."""
    test_ids = pd.read_csv(COHORT / "mimic4_test_ids.csv")
    ext_ids = pd.read_csv(COHORT / "mimic3_external_ids.csv")
    m3 = pd.read_excel(DATA_PATH, sheet_name="mimic3_low_fe")
    m4 = pd.read_excel(DATA_PATH, sheet_name="mimic4_low_fe")
    id_col_m3 = "icustay_id" if "icustay_id" in m3.columns else "subject_id"
    id_col_m4 = "subject_id" if "subject_id" in m4.columns else "icustay_id"

    if cohort_name == "MIMIC-IV internal test":
        ids, raw, idc, outcome = test_ids, m4, id_col_m4, "outcome_28d_t0"
    else:
        ids, raw, idc, outcome = ext_ids, m3, id_col_m3, "outcome_28d_t0"

    merged = raw.merge(ids[[idc, outcome]], on=idc, how="inner")
    y = merged[outcome].astype(int).values
    if SEVERITY_PATH.exists():
        sev = pd.read_parquet(SEVERITY_PATH)
        scols = [c for c in ["sofa_at_t0", "sofa_score"] if c in sev.columns]
        if scols:
            merged = merged.merge(
                sev[["stay_id"] + scols].drop_duplicates("stay_id"),
                left_on=idc,
                right_on="stay_id",
                how="left",
            )
    col = "sofa_at_t0" if "sofa_at_t0" in merged.columns and merged["sofa_at_t0"].notna().any() else "sofa_score"
    if col not in merged.columns:
        return y, None
    sc = pd.to_numeric(merged[col], errors="coerce").values
    return y, sc


def write_table5_incremental():
    """ΔAUROC (ML − SOFA) with 95% CI and DeLong p-value."""
    inc_rows = []
    for ml_label, tag in [("8-feature", "8_features"), ("20-feature", "20_features")]:
        for cohort_name, split in [
            ("MIMIC-IV internal test", "test"),
            ("MIMIC-III external", "external"),
        ]:
            y_ml, prob_ml, _ = load_preds(tag, split)
            y_sofa, sofa = _sofa_scores_for_cohort(cohort_name)
            if sofa is None or len(y_ml) != len(y_sofa):
                continue
            mask = np.isfinite(sofa)
            if mask.sum() < 10 or len(np.unique(y_ml[mask])) < 2:
                continue
            y = y_ml[mask]
            p_ml = prob_ml[mask]
            s_sofa = sofa[mask]
            if s_sofa.max() > 1.0 or s_sofa.min() < 0:
                lr = LogisticRegression(max_iter=500)
                lr.fit(s_sofa.reshape(-1, 1), y)
                p_sofa = lr.predict_proba(s_sofa.reshape(-1, 1))[:, 1]
            else:
                p_sofa = s_sofa
            auc_ml, lo_ml, hi_ml = delong_ci(y, p_ml)
            auc_sofa, lo_sofa, hi_sofa = delong_ci(y, p_sofa)
            delta, d_lo, d_hi, p_val = delong_pvalue(y, p_ml, p_sofa)
            inc_rows.append(
                {
                    "Cohort": cohort_name,
                    "ML_model": ml_label,
                    "Comparator": "SOFA",
                    "AUROC_ML": round(auc_ml, 3),
                    "AUROC_comp": round(auc_sofa, 3),
                    "Delta_AUROC": round(delta, 3),
                    "Delta_95CI": f"{d_lo:.3f}-{d_hi:.3f}",
                    "DeLong_p": round(p_val, 4) if np.isfinite(p_val) else "NA",
                }
            )

    inc_path = TABLES / "table5_incremental.csv"
    pd.DataFrame(inc_rows).to_csv(inc_path, index=False)
    print(f"Wrote {inc_path} ({len(inc_rows)} rows)")


if __name__ == "__main__":
    main()

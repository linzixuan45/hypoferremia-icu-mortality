#!/usr/bin/env python3
"""Generate Figure 6 SHAP panels for the 18-predictor locked benchmark Ensemble_Voting model."""
from __future__ import annotations

import argparse
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

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

from build_t0_cohort import load_lasso_features, primary_features
from train_models import FIGURES, LABEL, OUT, load_cohort_frames, prep_frame

MODEL_TAG = "20_features"
FORBIDDEN = frozenset({"platelet_mean", "los_icu", "bun_max"})
MANIFEST_PATH = FIGURES / "figure6_shap_manifest.json"


def load_stacking(tag: str = MODEL_TAG):
    bundle_path = OUT / "model_weight" / tag / "model_weight.pkl"
    if not bundle_path.exists():
        raise FileNotFoundError(f"Missing model bundle: {bundle_path}. Run train_models.py first.")
    with open(bundle_path, "rb") as f:
        bundle = pickle.load(f)
    model = bundle.get("Ensemble_Voting") or bundle.get("Ensemble_Stacking") or bundle.get("model")
    if model is None:
        raise KeyError(f"No ensemble model in {tag} bundle; keys={list(bundle.keys())}")
    return model, bundle["imputer"], bundle["scaler"], bundle["features"]


def _pick_force_plot_cases(y, pred_prob, shap_values_mortality, base_val_mortality):
    """Panel C = low-risk (alive); panel D = high-risk (dead)."""
    mortality_score = base_val_mortality + np.asarray(shap_values_mortality).sum(axis=1)
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
    high_idx = int(dead_conf[np.argmax(mortality_score[dead_conf])])
    low_idx = int(alive_conf[np.argmin(mortality_score[alive_conf])])
    return low_idx, high_idx


def verify_bundle(feats: list[str]) -> dict:
    expected = primary_features(load_lasso_features(20))
    overlap = set(feats) & FORBIDDEN
    report = {
        "n_features": len(feats),
        "features": feats,
        "expected_features": expected,
        "features_match_expected": feats == expected,
        "forbidden_absent": sorted(overlap),
        "forbidden_ok": len(overlap) == 0,
    }
    if len(feats) != 18:
        raise ValueError(f"Expected 18 locked features, got {len(feats)}")
    if overlap:
        raise ValueError(f"Forbidden legacy features in bundle: {sorted(overlap)}")
    if feats != expected:
        raise ValueError("Bundle features do not match primary_features() locked matrix")
    return report


def compose_figure6_composite(col_width: int = 600) -> Path:
    try:
        from PIL import Image
    except ImportError as exc:
        raise SystemExit("Pillow required for figure6 composite") from exc

    paths = [
        FIGURES / "figure6a_shap_summary.png",
        FIGURES / "figure6b_shap_importance.png",
        FIGURES / "figure6c_shap_force.png",
        FIGURES / "figure6d_shap_force.png",
    ]
    for path in paths:
        if not path.exists():
            raise FileNotFoundError(f"Missing panel: {path}")

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
    composite = FIGURES / "figure6_composite.png"
    out.save(composite)
    print(f"  Saved: {composite}")
    return composite


def generate_figure6_shap() -> dict:
    try:
        import shap
    except ImportError as exc:
        raise SystemExit("shap not installed; pip install -r requirements-optional.txt") from exc

    FIGURES.mkdir(parents=True, exist_ok=True)

    expected_feats = primary_features(load_lasso_features(20))
    model, imp, scaler, feats = load_stacking(MODEL_TAG)
    bundle_report = verify_bundle(feats)
    xgb = model.named_estimators_["xgb"]

    _, _, ext_df = load_cohort_frames("excel_proxy")
    sub = prep_frame(ext_df, feats)
    X = sub[feats]
    Xi = pd.DataFrame(imp.transform(X), columns=feats)
    Xs = pd.DataFrame(scaler.transform(Xi), columns=feats)
    y = sub[LABEL].astype(int).values

    explainer = shap.TreeExplainer(xgb)
    sv_raw = explainer.shap_values(Xs)
    if isinstance(sv_raw, list):
        sv = sv_raw[1]
    else:
        sv = sv_raw

    # 6A: global beeswarm (18 locked predictors)
    plt.figure(figsize=(9, 7))
    shap.summary_plot(sv, Xs, show=False, max_display=len(feats))
    plt.tight_layout()
    path_6a = FIGURES / "figure6a_shap_summary.png"
    plt.savefig(path_6a, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {path_6a}")

    # 6B: mean |SHAP| bar chart
    mean_abs = np.abs(sv).mean(axis=0)
    order = np.argsort(mean_abs)
    ranked = [feats[i] for i in order[::-1]]
    top3 = ranked[:3]

    fig, ax = plt.subplots(figsize=(7, 6))
    y_pos = np.arange(len(feats))
    ax.barh(y_pos, mean_abs[order], color="steelblue")
    ax.set_yticks(y_pos)
    ax.set_yticklabels([feats[i] for i in order])
    ax.set_xlabel("mean |SHAP value|")
    ax.set_title("Figure 6B: Ranked SHAP feature importance (18-predictor locked)")
    fig.tight_layout()
    path_6b = FIGURES / "figure6b_shap_importance.png"
    fig.savefig(path_6b, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {path_6b}")

    # 6C / 6D: mortality-oriented force plots (positive SHAP raises death risk).
    pred_prob = xgb.predict_proba(Xs)[:, 1]
    if isinstance(sv_raw, list):
        shap_values_mortality = sv_raw[1]
        exp_val = np.atleast_1d(explainer.expected_value)
        base_val_mortality = exp_val[1] if len(exp_val) > 1 else float(exp_val[0])
    else:
        shap_values_mortality = np.asarray(sv_raw)
        base_val_mortality = float(np.atleast_1d(explainer.expected_value).flat[0])

    low_idx, high_idx = _pick_force_plot_cases(
        y, pred_prob, shap_values_mortality, base_val_mortality
    )
    if low_idx is None:
        raise RuntimeError("Could not select low/high-risk force-plot cases")

    X_disp = Xi.round(2)
    case_meta = {}
    for idx, fname, label in [
        (low_idx, "figure6c_shap_force.png", "low-risk"),
        (high_idx, "figure6d_shap_force.png", "high-risk"),
    ]:
        shap.force_plot(
            base_val_mortality,
            shap_values_mortality[idx],
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
        print(f"  Saved: {out_path} ({label}; pred_death={pred_prob[idx]:.4f})")
        case_meta[label] = {
            "index": int(idx),
            "pred_death_prob": float(pred_prob[idx]),
            "outcome": int(y[idx]),
            "feature_values": {k: float(X_disp.iloc[idx][k]) for k in feats},
        }

    compose_figure6_composite()

    manifest = {
        **bundle_report,
        "model_tag": MODEL_TAG,
        "cohort": "MIMIC-III temporal sensitivity",
        "n_samples_shap": int(len(y)),
        "top_feature": ranked[0],
        "top3_features": top3,
        "platelet_1st_in_top3": "platelet_1st" in top3,
        "cases": case_meta,
        "outputs": {
            "composite": str(FIGURES / "figure6_composite.png"),
            "panels": [
                str(FIGURES / "figure6a_shap_summary.png"),
                str(FIGURES / "figure6b_shap_importance.png"),
                str(FIGURES / "figure6c_shap_force.png"),
                str(FIGURES / "figure6d_shap_force.png"),
            ],
        },
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"  Saved: {MANIFEST_PATH}")
    print(f"  top_feature={ranked[0]}; top3={top3}")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Plot Figure 6 SHAP for 18-predictor locked benchmark")
    parser.add_argument("--verify-only", action="store_true", help="Check bundle features only")
    args = parser.parse_args()

    expected = primary_features(load_lasso_features(20))
    if args.verify_only:
        _, _, _, feats = load_stacking(MODEL_TAG)
        report = verify_bundle(feats)
        print(json.dumps(report, indent=2))
        return

    manifest = generate_figure6_shap()
    if not manifest["forbidden_ok"]:
        raise SystemExit("VERIFY FAIL: forbidden legacy features present")
    if manifest["n_features"] != 18:
        raise SystemExit("VERIFY FAIL: n_features != 18")
    print("Figure 6 SHAP generation OK")


if __name__ == "__main__":
    main()

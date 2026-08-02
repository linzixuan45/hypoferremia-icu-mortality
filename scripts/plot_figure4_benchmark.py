#!/usr/bin/env python3
"""Train the locked R2 benchmark models and export Figure 4 ROC panels."""
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
from sklearn.ensemble import AdaBoostClassifier, RandomForestClassifier, StackingClassifier, VotingClassifier
from sklearn.linear_model import LogisticRegression, LogisticRegressionCV
from sklearn.metrics import roc_curve
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.svm import SVC
from xgboost import XGBClassifier

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

from build_t0_cohort import load_lasso_features, primary_features
from train_models import (
    COHORT,
    FIGURES,
    LABEL,
    OUT,
    PREDS,
    RANDOM_STATE,
    TABLES,
    delong_ci,
    impute_scale,
    load_cohort_frames,
    prep_subset,
)

try:
    from lightgbm import LGBMClassifier
except ImportError:  # pragma: no cover
    LGBMClassifier = None

MODEL_ORDER = [
    "Logistic Regression",
    "KNN",
    "SVM",
    "Decision Tree",
    "Random Forest",
    "ANN",
    "XGBoost",
    "LightGBM",
    "AdaBoost",
    "GaussianNB",
    "Ensemble_Voting",
    "Ensemble_Stacking",
]

# Locked manuscript AUROC values (3 d.p.) used only as guardrails.  The full
# twelve-model temporal profile must be recomputed after applying the corrected
# MIMIC-III eligibility rule; the earlier values came from the broader cohort.
REFERENCE_AUROC = {
    "MIMIC-IV internal test": {
        "Logistic Regression": 0.846,
        "KNN": 0.712,
        "SVM": 0.848,
        "Decision Tree": 0.653,
        "Random Forest": 0.822,
        "ANN": 0.717,
        "XGBoost": 0.804,
        "LightGBM": 0.819,
        "AdaBoost": 0.798,
        "GaussianNB": 0.803,
        "Ensemble_Voting": 0.840,
        "Ensemble_Stacking": 0.840,
    },
    "MIMIC-III temporal sensitivity": {
        "Ensemble_Voting": 0.705,
    },
}


def _base_lr() -> LogisticRegression:
    return LogisticRegression(max_iter=2000, random_state=RANDOM_STATE, class_weight="balanced")


def _base_rf() -> RandomForestClassifier:
    return RandomForestClassifier(
        n_estimators=200,
        max_depth=6,
        random_state=RANDOM_STATE,
        class_weight="balanced",
    )


def _base_xgb() -> XGBClassifier:
    return XGBClassifier(
        n_estimators=120,
        max_depth=4,
        learning_rate=0.08,
        random_state=RANDOM_STATE,
        eval_metric="logloss",
    )


def build_prespecified_ensembles() -> dict[str, object]:
    bases = [
        ("lr", _base_lr()),
        ("rf", _base_rf()),
        ("xgb", _base_xgb()),
    ]
    return {
        "Ensemble_Voting": VotingClassifier(estimators=bases, voting="soft"),
        "Ensemble_Stacking": StackingClassifier(
            estimators=bases,
            final_estimator=LogisticRegression(max_iter=2000, random_state=RANDOM_STATE),
            cv=5,
            passthrough=False,
        ),
    }


def build_standalone_models() -> dict[str, object]:
    """Hyperparameters per Supplementary Table S4 + balanced class weights where supported."""
    if LGBMClassifier is None:
        raise SystemExit("lightgbm is required: pip install lightgbm")

    from sklearn.tree import DecisionTreeClassifier

    return {
        "Logistic Regression": LogisticRegressionCV(
            cv=5,
            max_iter=1000,
            class_weight="balanced",
            random_state=RANDOM_STATE,
        ),
        "KNN": KNeighborsClassifier(n_neighbors=5),
        "SVM": SVC(
            kernel="rbf",
            C=1.0,
            gamma="scale",
            probability=True,
            class_weight="balanced",
            random_state=RANDOM_STATE,
        ),
        "Decision Tree": DecisionTreeClassifier(
            max_depth=5,
            class_weight="balanced",
            random_state=RANDOM_STATE,
        ),
        "Random Forest": RandomForestClassifier(
            n_estimators=100,
            max_depth=5,
            class_weight="balanced",
            random_state=RANDOM_STATE,
        ),
        "ANN": MLPClassifier(
            hidden_layer_sizes=(100, 50),
            max_iter=1000,
            random_state=RANDOM_STATE,
        ),
        "XGBoost": XGBClassifier(random_state=RANDOM_STATE, eval_metric="logloss"),
        "LightGBM": LGBMClassifier(
            n_estimators=20,
            learning_rate=0.1,
            max_depth=5,
            num_leaves=31,
            min_child_samples=10,
            min_child_weight=0.001,
            subsample=0.8,
            colsample_bytree=0.8,
            reg_alpha=0.01,
            reg_lambda=0.01,
            random_state=2018,
            verbose=-1,
        ),
        "AdaBoost": AdaBoostClassifier(
            n_estimators=100,
            learning_rate=0.5,
            random_state=RANDOM_STATE,
        ),
        "GaussianNB": GaussianNB(),
    }


def build_all_models() -> dict[str, object]:
    models = build_standalone_models()
    models.update(build_prespecified_ensembles())
    return models


def evaluate_all_cohorts(
    models: dict[str, object],
    X_train_s: pd.DataFrame,
    y_train: pd.Series,
    X_test_s: pd.DataFrame,
    y_test: pd.Series,
    X_ext_s: pd.DataFrame,
    y_ext: pd.Series,
) -> tuple[list[dict], list[dict]]:
    test_rows: list[dict] = []
    ext_rows: list[dict] = []
    cohorts = [
        (test_rows, y_test.values.astype(int), X_test_s),
        (ext_rows, y_ext.values.astype(int), X_ext_s),
    ]
    for name in MODEL_ORDER:
        model = models[name]
        model.fit(X_train_s, y_train)
        for rows, y, X_eval_s in cohorts:
            prob = model.predict_proba(X_eval_s)[:, 1]
            auroc, lo, hi = delong_ci(y, prob)
            fpr, tpr, _ = roc_curve(y, prob)
            rows.append(
                {
                    "model": name,
                    "n": len(y),
                    "events": int(y.sum()),
                    "auroc": auroc,
                    "auroc_ci_lo": lo,
                    "auroc_ci_hi": hi,
                    "AUROC_95CI": f"{lo:.3f}-{hi:.3f}",
                    "y": y,
                    "prob": prob,
                    "fpr": fpr,
                    "tpr": tpr,
                }
            )
    return test_rows, ext_rows


def rows_to_table(rows: list[dict], cohort_label: str) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Model": r["model"],
                "Cohort": cohort_label,
                "n": r["n"],
                "Events": r["events"],
                "AUROC": round(r["auroc"], 3),
                "AUROC_95CI": r["AUROC_95CI"],
            }
            for r in rows
        ]
    )


def pack_preds(rows: list[dict], cohort: str) -> list[dict]:
    packed = []
    for r in rows:
        packed.append(
            {
                "model_name": r["model"],
                "cohort": cohort,
                "n": r["n"],
                "events": r["events"],
                "auroc": r["auroc"],
                "auroc_ci_lo": r["auroc_ci_lo"],
                "auroc_ci_hi": r["auroc_ci_hi"],
                "lable": r["y"].tolist(),
                "pred_prob": r["prob"].tolist(),
                "roc_curve": {"fpr": r["fpr"].tolist(), "tpr": r["tpr"].tolist()},
            }
        )
    return packed


def plot_roc_panel(ax, rows: list[dict], title: str) -> None:
    for r in rows:
        ax.plot(
            r["fpr"],
            r["tpr"],
            lw=2,
            label=f"{r['model']} (AUC = {r['auroc']:.3f})",
        )
    ax.plot([0, 1], [0, 1], "k--", lw=1)
    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(0.0, 1.05)
    ax.set_xlabel("False Positive Rate", fontsize=11)
    ax.set_ylabel("True Positive Rate", fontsize=11)
    ax.set_title(title, fontsize=11)
    ax.legend(loc="lower right", fontsize=7)
    ax.grid(False)


def plot_figure4(test_rows: list[dict], ext_rows: list[dict], out_path: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
    fig.patch.set_facecolor("white")
    plot_roc_panel(
        axes[0],
        test_rows,
        "MIMIC-IV internal test (n=269)",
    )
    plot_roc_panel(
        axes[1],
        ext_rows,
        f"MIMIC-III temporal sensitivity (n={ext_rows[0]['n']:,})",
    )
    axes[0].text(-0.12, 1.05, "A", transform=axes[0].transAxes, fontsize=12, fontweight="bold")
    axes[1].text(-0.12, 1.05, "B", transform=axes[1].transAxes, fontsize=12, fontweight="bold")
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def verify_reference(rows: list[dict], cohort_label: str, tol: float = 0.005) -> list[str]:
    ref = REFERENCE_AUROC.get(cohort_label, {})
    errors: list[str] = []
    for r in rows:
        target = ref.get(r["model"])
        if target is None:
            continue
        if abs(r["auroc"] - target) > tol:
            errors.append(
                f"{cohort_label} {r['model']}: got {r['auroc']:.3f}, expected {target:.3f}"
            )
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description="FE1 12-model benchmark ROC (Figure 4)")
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Fail if AUROC differs from manuscript Table 2/3 by >0.005",
    )
    parser.add_argument(
        "--tol",
        type=float,
        default=0.005,
        help="AUROC verification tolerance (default 0.005)",
    )
    args = parser.parse_args()

    if not (COHORT / "mimic4_train_ids.csv").exists():
        raise SystemExit("Run build_t0_cohort.py first.")

    features = primary_features(load_lasso_features(20))
    train_df, test_df, ext_df = load_cohort_frames("excel_proxy")

    X_train, y_train = prep_subset(train_df, features)
    X_test, y_test = prep_subset(test_df, features)
    X_ext, y_ext = prep_subset(ext_df, features)

    _, X_train_s, _, [X_test_s, X_ext_s], _, _ = impute_scale(X_train, [X_test, X_ext])
    models = build_all_models()

    test_rows, ext_rows = evaluate_all_cohorts(
        models, X_train_s, y_train, X_test_s, y_test, X_ext_s, y_ext
    )

    for d in (TABLES, FIGURES, PREDS):
        d.mkdir(parents=True, exist_ok=True)

    table2 = rows_to_table(test_rows, "MIMIC-IV internal test")
    table3 = rows_to_table(ext_rows, "MIMIC-III temporal sensitivity")
    table2.to_csv(TABLES / "table2_benchmark_12models.csv", index=False)
    table3.to_csv(TABLES / "table3_benchmark_12models.csv", index=False)
    pd.concat([table2, table3], ignore_index=True).to_csv(
        TABLES / "table2_3_benchmark_12models.csv",
        index=False,
    )

    with open(PREDS / "18_features_benchmark_test_preds.pkl", "wb") as f:
        pickle.dump(pack_preds(test_rows, "mimic4_internal_test"), f)
    with open(PREDS / "18_features_benchmark_external_preds.pkl", "wb") as f:
        pickle.dump(pack_preds(ext_rows, "mimic3_external"), f)

    plot_figure4(test_rows, ext_rows, FIGURES / "figure4_roc_12models.png")

    print("Table 2 (internal test):")
    print(table2.to_string(index=False))
    print("\nTable 3 (external):")
    print(table3.to_string(index=False))
    print(f"\nSaved figure: {FIGURES / 'figure4_roc_12models.png'}")

    errors = verify_reference(test_rows, "MIMIC-IV internal test", args.tol)
    errors.extend(verify_reference(ext_rows, "MIMIC-III temporal sensitivity", args.tol))
    if errors:
        print("\nAUROC verification mismatches:")
        for e in errors:
            print(f"  - {e}")
        if args.verify:
            raise SystemExit(1)

    manifest_path = OUT / "manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    else:
        manifest = {}
    manifest.setdefault("artifacts", {}).update(
        {
            "table2_benchmark_12models": "result/analysis/tables/table2_benchmark_12models.csv",
            "table3_benchmark_12models": "result/analysis/tables/table3_benchmark_12models.csv",
            "figure4_roc_12models": "result/analysis/figures/figure4_roc_12models.png",
            "benchmark_18f_test_preds": "result/analysis/preds/18_features_benchmark_test_preds.pkl",
            "benchmark_18f_external_preds": "result/analysis/preds/18_features_benchmark_external_preds.pkl",
        }
    )
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Export Figure 5 composite (calibration + DCA + CIC) from FE1 12-model benchmark preds."""
from __future__ import annotations

import argparse
import json
import pickle
import sys
import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import numpy as np
from sklearn.calibration import calibration_curve

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

from plot_figure4_benchmark import FIGURES, MODEL_ORDER, OUT, PREDS

BENCHMARK_PKL = PREDS / "18_features_benchmark_test_preds.pkl"
OUTPUT_PNG = FIGURES / "figure5_calibration_dca_cic.png"
EXPECTED_N = 269
EXPECTED_EVENTS = 40
LEGACY_IMAGE5_MD5 = "a2ba665ab9dca4b40fdcabd39c6f24ef"


def load_test_benchmark_preds(path: Path = BENCHMARK_PKL) -> list[dict]:
    if not path.exists():
        raise SystemExit(
            f"Missing {path}. Run scripts/plot_figure4_benchmark.py first."
        )
    with open(path, "rb") as f:
        preds = pickle.load(f)
    if not isinstance(preds, list) or not preds:
        raise SystemExit(f"Invalid benchmark preds format in {path}")
    return preds


def _preds_by_model(preds: list[dict]) -> dict[str, dict]:
    return {p["model_name"]: p for p in preds}


def dca_net_benefit(
    y_true: np.ndarray, y_prob: np.ndarray, thresholds: np.ndarray
) -> np.ndarray:
    y_true = np.asarray(y_true, dtype=int)
    y_prob = np.asarray(y_prob, dtype=float)
    n = len(y_true)
    nb = np.empty(len(thresholds), dtype=float)
    for i, t in enumerate(thresholds):
        if t >= 1.0:
            nb[i] = 0.0
            continue
        pred = y_prob >= t
        tp = np.sum(pred & (y_true == 1))
        fp = np.sum(pred & (y_true == 0))
        nb[i] = tp / n - fp / n * (t / (1.0 - t))
    return nb


def treat_all_nb(y_true: np.ndarray, thresholds: np.ndarray) -> np.ndarray:
    prev = float(np.mean(np.asarray(y_true, dtype=int)))
    return np.array(
        [prev - (1.0 - prev) * (t / (1.0 - t)) if t < 1.0 else 0.0 for t in thresholds]
    )


def plot_calibration_panel(ax, preds: list[dict], n: int) -> None:
    lookup = _preds_by_model(preds)
    for name in MODEL_ORDER:
        entry = lookup[name]
        y = np.asarray(entry["lable"], dtype=int)
        prob = np.asarray(entry["pred_prob"], dtype=float)
        prob_true, prob_pred = calibration_curve(y, prob, n_bins=8)
        ax.plot(prob_pred, prob_true, lw=1.5, label=name)
    ax.plot([0, 1], [0, 1], "k--", lw=1)
    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(0.0, 1.0)
    ax.set_xlabel("Mean predicted probability", fontsize=10)
    ax.set_ylabel("Fraction of positives", fontsize=10)
    ax.legend(loc="lower right", fontsize=6)
    ax.grid(False)
    ax.text(0.02, 0.98, "A", transform=ax.transAxes, fontsize=12, fontweight="bold", va="top")


def plot_dca_panel(ax, preds: list[dict], n: int) -> None:
    thresholds = np.linspace(0, 1, 100)
    lookup = _preds_by_model(preds)
    y_ref = np.asarray(lookup["Ensemble_Voting"]["lable"], dtype=int)

    for name in MODEL_ORDER:
        entry = lookup[name]
        y = np.asarray(entry["lable"], dtype=int)
        prob = np.asarray(entry["pred_prob"], dtype=float)
        nb = dca_net_benefit(y, prob, thresholds)
        lw = 2.5 if name == "Ensemble_Voting" else 1.0
        alpha = 1.0 if name == "Ensemble_Voting" else 0.85
        ax.plot(thresholds, nb, lw=lw, alpha=alpha, label=name)

    ax.plot(thresholds, treat_all_nb(y_ref, thresholds), "k--", lw=1.5, label="Treat all")
    ax.axhline(0, color="gray", linestyle=":", lw=1, label="Treat none")
    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(-0.15, 0.6)
    ax.set_xlabel("Threshold Probability", fontsize=10)
    ax.set_ylabel("Net Benefit", fontsize=10)
    ax.legend(loc="upper right", fontsize=5.5)
    ax.grid(False)
    ax.text(0.02, 0.98, "B", transform=ax.transAxes, fontsize=12, fontweight="bold", va="top")


def plot_cic_panel(ax, y: np.ndarray, prob: np.ndarray, n: int) -> None:
    thresholds = np.linspace(0, 1, 101)
    y_true = np.asarray(y, dtype=int)
    y_pred = np.asarray(prob, dtype=float)
    high_risk = [int(np.sum(y_pred >= t)) for t in thresholds]
    true_pos = [int(np.sum((y_pred >= t) & (y_true == 1))) for t in thresholds]
    y_max = int(np.ceil(n / 25.0) * 25)

    ax.set_xlabel("Threshold Probability", fontsize=10)
    ax.set_ylabel("High-Risk Population", color="tab:red", fontsize=10)
    ax.plot(thresholds, high_risk, color="tab:red", linestyle="-", lw=2, label="High Risk")
    ax.tick_params(axis="y", labelcolor="tab:red")
    ax.set_ylim(0, y_max)
    ax.set_xlim(0.0, 1.0)

    ax2 = ax.twinx()
    ax2.set_ylabel("True Positives", color="tab:blue", fontsize=10)
    ax2.plot(
        thresholds,
        true_pos,
        color="tab:blue",
        linestyle="--",
        lw=2,
        label="True Positive",
    )
    ax2.tick_params(axis="y", labelcolor="tab:blue")
    tp_max = max(true_pos) if true_pos else n
    ax2.set_ylim(0, int(np.ceil(tp_max / 25.0) * 25) or 25)

    lines, labels = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines + lines2, labels + labels2, loc="upper right", fontsize=9)
    ax.grid(False)
    ax.text(0.02, 0.98, "C", transform=ax.transAxes, fontsize=12, fontweight="bold", va="top")


def plot_figure5_composite(preds: list[dict], out_path: Path) -> None:
    lookup = _preds_by_model(preds)
    ev = lookup["Ensemble_Voting"]
    n = len(ev["lable"])

    fig = plt.figure(figsize=(13, 9))
    fig.patch.set_facecolor("white")
    gs = gridspec.GridSpec(2, 2, figure=fig, height_ratios=[1, 1], hspace=0.35, wspace=0.28)

    ax_a = fig.add_subplot(gs[0, 0])
    ax_b = fig.add_subplot(gs[0, 1])
    ax_c = fig.add_subplot(gs[1, :])

    plot_calibration_panel(ax_a, preds, n)
    plot_dca_panel(ax_b, preds, n)
    plot_cic_panel(
        ax_c,
        np.asarray(ev["lable"], dtype=int),
        np.asarray(ev["pred_prob"], dtype=float),
        n,
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def verify_figure5(preds: list[dict]) -> list[str]:
    errors: list[str] = []
    lookup = _preds_by_model(preds)

    missing = [name for name in MODEL_ORDER if name not in lookup]
    if missing:
        errors.append(f"Missing models in pickle: {missing}")

    for name in MODEL_ORDER:
        if name not in lookup:
            continue
        n = len(lookup[name]["lable"])
        if n != EXPECTED_N:
            errors.append(f"{name}: n={n}, expected {EXPECTED_N}")

    ev = lookup.get("Ensemble_Voting")
    if ev is None:
        errors.append("Ensemble_Voting not found")
    else:
        events = int(np.sum(np.asarray(ev["lable"], dtype=int)))
        if events != EXPECTED_EVENTS:
            errors.append(f"Ensemble_Voting events={events}, expected {EXPECTED_EVENTS}")
        prob = np.asarray(ev["pred_prob"], dtype=float)
        max_hr = int(np.sum(prob >= 0.0))
        if max_hr != EXPECTED_N:
            errors.append(f"CIC max high-risk={max_hr}, expected {EXPECTED_N}")
        if max_hr == 175:
            errors.append("CIC max high-risk=175 suggests legacy n=175 cohort")

    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description="FE1 Figure 5 calibration/DCA/CIC composite")
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Exit 1 if cohort size / CIC checks fail",
    )
    args = parser.parse_args()

    preds = load_test_benchmark_preds()
    errors = verify_figure5(preds)

    ev = _preds_by_model(preds)["Ensemble_Voting"]
    n = len(ev["lable"])
    prob = np.asarray(ev["pred_prob"], dtype=float)
    max_hr = int(np.sum(prob >= 0.0))
    events = int(np.sum(np.asarray(ev["lable"], dtype=int)))
    print(f"MIMIC-IV internal test: n={n}, events={events}, CIC max high-risk={max_hr}")

    if errors:
        print("\nVerification issues:")
        for err in errors:
            print(f"  - {err}")
        if args.verify:
            raise SystemExit(1)

    plot_figure5_composite(preds, OUTPUT_PNG)
    print(f"Saved figure: {OUTPUT_PNG}")

    manifest_path = OUT / "manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    else:
        manifest = {}
    manifest.setdefault("artifacts", {}).update(
        {
            "figure5_calibration_dca_cic": "result/analysis/figures/figure5_calibration_dca_cic.png",
        }
    )
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()

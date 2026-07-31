#!/usr/bin/env python3
"""Create corrected aggregate performance panels for manuscript Figures 4 and 7."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image


ROOT = Path(__file__).resolve().parent.parent
REF = ROOT / "reference" / "r2"
LEGACY_FIGURES = ROOT / "result" / "analysis" / "figures"


def _bar_panel(ax, rows, title, color):
    labels = [x["label"] for x in rows]
    values = [x["auroc"] for x in rows]
    y = np.arange(len(rows))
    ax.barh(y, values, color=color, height=0.58)
    ax.set_yticks(y, labels)
    ax.invert_yaxis()
    ax.set_xlim(0.5, 1.0)
    ax.set_xlabel("AUROC")
    ax.set_title(title, loc="left", fontweight="bold")
    ax.axvline(0.5, color="#6B7280", lw=1, ls="--")
    ax.grid(axis="x", alpha=0.18)
    for i, row in enumerate(rows):
        ax.text(
            row["auroc"] + 0.008,
            i,
            f'{row["auroc"]:.3f}\nn={row["n"]}; events={row["events"]}',
            va="center",
            fontsize=8.5,
        )


def performance_rows():
    cal = pd.read_csv(REF / "r2_standard_calibration_metrics.csv")
    corr = pd.read_csv(REF / "r2_corrected_mimic3_evaluation.csv")

    def select(analysis: str, cohort: str):
        row = cal[
            cal["Analysis"].str.contains(analysis, regex=False)
            & cal["Cohort"].str.contains(cohort, regex=False)
        ]
        if len(row) != 1:
            raise ValueError(
                f"Expected one row for analysis={analysis!r}, cohort={cohort!r}; "
                f"found {len(row)}"
            )
        return row.iloc[0]

    internal18 = select("Locked 18-predictor", "MIMIC-IV internal")
    internal8 = select("Reduced 8-feature", "MIMIC-IV internal")
    f3 = select("Reduced 8-feature", "F3 exploratory")
    nh = select("Reduced 8-feature", "NH exploratory")
    corrected18 = corr.iloc[0]
    corrected8 = corr.iloc[1]
    rows18 = [
        {
            "label": "MIMIC-IV\ninternal test",
            "auroc": float(internal18.AUROC),
            "n": int(internal18.n),
            "events": int(internal18.Events),
        },
        {
            "label": "MIMIC-III\ncorrected temporal",
            "auroc": float(corrected18.AUROC),
            "n": int(corrected18.n),
            "events": int(corrected18.Events),
        },
    ]
    rows8 = [
        {
            "label": "MIMIC-IV\ninternal test",
            "auroc": float(internal8.AUROC),
            "n": int(internal8.n),
            "events": int(internal8.Events),
        },
        {
            "label": "MIMIC-III\ncorrected temporal",
            "auroc": float(corrected8.AUROC),
            "n": int(corrected8.n),
            "events": int(corrected8.Events),
        },
        {
            "label": "F3\nexploratory geographic",
            "auroc": float(f3.AUROC),
            "n": int(f3.n),
            "events": int(f3.Events),
        },
        {
            "label": "NH\nexploratory geographic",
            "auroc": float(nh.AUROC),
            "n": int(nh.n),
            "events": int(nh.Events),
        },
    ]
    return rows18, rows8


def figure4(rows18, rows8):
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.8), constrained_layout=True)
    _bar_panel(
        axes[0],
        rows18,
        "A  Locked 18-predictor benchmark",
        "#1F6F8B",
    )
    _bar_panel(
        axes[1],
        rows8,
        "B  Post hoc 8-feature derivative",
        "#D97706",
    )
    fig.text(
        0.5,
        -0.01,
        "Cohort-level discrimination; F3 and NH estimates are exploratory and do not imply calibrated transportability.",
        ha="center",
        fontsize=9,
        color="#374151",
    )
    out = REF / "figure4_corrected_cohort_performance.png"
    fig.savefig(out, dpi=300, bbox_inches="tight", facecolor="white")
    fig.savefig(out.with_suffix(".svg"), bbox_inches="tight", facecolor="white")
    plt.close(fig)


def figure7(rows8):
    fig = plt.figure(figsize=(14, 9), constrained_layout=True)
    gs = fig.add_gridspec(2, 2, height_ratios=[1.2, 1.0])
    panels = [
        (LEGACY_FIGURES / "figure7a_shap_summary.png", "A"),
        (None, "B"),
        (LEGACY_FIGURES / "figure7c_shap_force.png", "C"),
        (LEGACY_FIGURES / "figure7d_shap_force.png", "D"),
    ]
    for idx, (path, label) in enumerate(panels):
        ax = fig.add_subplot(gs[idx // 2, idx % 2])
        if path is None:
            _bar_panel(ax, rows8, "B  Cohort-level AUROC", "#D97706")
        else:
            with Image.open(path) as im:
                ax.imshow(im.convert("RGB"))
            ax.axis("off")
            ax.text(
                0.01,
                0.99,
                label,
                transform=ax.transAxes,
                va="top",
                ha="left",
                fontsize=14,
                fontweight="bold",
                bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.85},
            )
    out = REF / "figure7_reduced_model_corrected.png"
    fig.savefig(out, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def main():
    rows18, rows8 = performance_rows()
    figure4(rows18, rows8)
    figure7(rows8)
    print("Created corrected Figures 4 and 7 in reference/r2")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Aggregate-only source for the R3 Figure 7B reporting correction.

Figure contract: display cohort-specific discrimination uncertainty, without
claiming model superiority. This single-panel quantitative forest plot reads
all four aggregate rows; it does not train, infer, or load patient records.
Python is the exclusive plotting backend. No panel A/C/D assets are modified.
The neutral axis is necessary because internal CI is DeLong and the other
three CIs are stratified bootstrap. Publication assembly requires visual QA.
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_METRICS = ROOT / "reference/r2/figure7_corrected_metrics.csv"
AXIS_LABEL = "AUROC (95% CI)"


def load_aggregate_rows(path: Path = DEFAULT_METRICS) -> list[dict]:
    """Validate four aggregate rows while preserving their supplied order."""
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 4:
        raise ValueError("Figure 7B requires all four aggregate cohort rows")
    converted = []
    for row in rows:
        item = dict(row)
        for key in ("n", "Events"):
            item[key] = int(item[key])
        for key in ("AUROC", "CI_lo", "CI_hi"):
            item[key] = float(item[key])
        if not 0 <= item["CI_lo"] <= item["AUROC"] <= item["CI_hi"] <= 1:
            raise ValueError(f"Invalid aggregate interval for {item['Cohort']}")
        if not 0 < item["Events"] < item["n"]:
            raise ValueError(f"Invalid aggregate denominator for {item['Cohort']}")
        expected = "DeLong" if "MIMIC-IV internal" in item["Cohort"] else "Stratified bootstrap"
        if item["CI_method"].casefold() != expected.casefold():
            raise ValueError(f"Unexpected CI method for {item['Cohort']}")
        converted.append(item)
    return converted


def render_panel(rows: list[dict], output_prefix: Path) -> None:
    """Export an editable vector panel plus 600-dpi raster for assembly."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
        "font.size": 7,
        "axes.labelsize": 7,
        "xtick.labelsize": 6.5,
        "ytick.labelsize": 6.5,
        "axes.linewidth": 0.65,
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    })
    labels = [
        "MIMIC-IV internal test",
        "MIMIC-III temporal sensitivity",
        "Third Xiangya exploratory",
        "USC-FAH exploratory",
    ]
    fig, ax = plt.subplots(figsize=(3.5, 3.1))
    fig.subplots_adjust(left=0.46, right=0.98, bottom=0.18, top=0.89)
    for index, row in enumerate(rows):
        y = len(rows) - 1 - index
        color = "#245B80" if index < 2 else "#BC6B25"
        ax.errorbar(
            row["AUROC"], y,
            xerr=[[row["AUROC"] - row["CI_lo"]], [row["CI_hi"] - row["AUROC"]]],
            fmt="o", markersize=3, color=color, ecolor=color,
            elinewidth=0.85, capsize=2, capthick=0.7,
        )
        ax.text(
            row["AUROC"], y + 0.21,
            f"{row['AUROC']:.3f} ({row['CI_lo']:.3f}–{row['CI_hi']:.3f})",
            ha="center", va="bottom", fontsize=6,
        )
    ax.set_yticks(list(range(len(rows) - 1, -1, -1)), labels)
    ax.tick_params(axis="y", length=0, pad=4)
    ax.set_xlim(0.5, 1.0)
    ax.set_xticks([0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
    ax.set_ylim(-0.55, 3.65)
    ax.set_xlabel(AXIS_LABEL)
    ax.axvline(0.5, color="#888888", lw=0.6, ls="--")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.text(0.015, 0.97, "B", fontweight="bold", fontsize=9, va="top")
    output_prefix.parent.mkdir(parents=True, exist_ok=True)
    for extension in ("pdf", "svg", "png", "tiff"):
        output = output_prefix.with_suffix(f".{extension}")
        if output.exists():
            raise FileExistsError(f"Refusing to overwrite existing output: {output}")
    fig.savefig(output_prefix.with_suffix(".pdf"), dpi=600, facecolor="white")
    fig.savefig(output_prefix.with_suffix(".svg"), dpi=600, facecolor="white")
    fig.savefig(output_prefix.with_suffix(".png"), dpi=600, facecolor="white")
    fig.savefig(output_prefix.with_suffix(".tiff"), dpi=600, facecolor="white")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metrics", type=Path, default=DEFAULT_METRICS)
    parser.add_argument("--output-prefix", type=Path, required=True)
    args = parser.parse_args()
    render_panel(load_aggregate_rows(args.metrics), args.output_prefix)


if __name__ == "__main__":
    main()

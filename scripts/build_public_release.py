#!/usr/bin/env python3
"""Build a privacy-screened GitHub/Zenodo software release archive."""
from __future__ import annotations

import hashlib
import subprocess
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "deliverables" / "Fe_R2_Revision_Package"
VERSION = "1.1.0"
ARCHIVE_ROOT = f"hypoferremia-icu-mortality-{VERSION}"
OUT_ZIP = OUT / f"hypoferremia-icu-mortality-v{VERSION}-zenodo-ready.zip"

PUBLIC_ADDITIONS = {
    ".zenodo.json",
    "CITATION.cff",
    "RELEASE_NOTES_v1.1.0.md",
    "reference/r2/FIGURE1_SOURCE_DECLARATION.md",
    "reference/r2/README.md",
    "reference/r2/figure1_biorender_updated.png",
    "reference/r2/figure1_biorender_updated.tiff",
    "reference/r2/figure2_within_hypoferremia_dose_response.png",
    "reference/r2/figure2_within_hypoferremia_dose_response.svg",
    "reference/r2/figure4_corrected_cohort_performance.png",
    "reference/r2/figure4_corrected_cohort_performance.svg",
    "reference/r2/figure7_reduced_model_corrected.png",
    "reference/r2/r2_analysis_manifest.json",
    "reference/r2/r2_corrected_mimic3_evaluation.csv",
    "reference/r2/r2_corrected_mimic3_flow_and_niv_missingness.csv",
    "reference/r2/r2_included_vs_excluded.csv",
    "reference/r2/r2_iron_adjusted_effect.csv",
    "reference/r2/r2_iron_incremental_value.csv",
    "reference/r2/r2_locked_matrix_missingness_and_windows.csv",
    "reference/r2/r2_multiple_imputation_per_imputation.csv",
    "reference/r2/r2_multiple_imputation_sensitivity.csv",
    "reference/r2/r2_niv_exclusion_sensitivity.csv",
    "reference/r2/r2_patient_flow.csv",
    "reference/r2/r2_standard_calibration_metrics.csv",
    "reference/r2/r2_table1_mimic4_eligible.csv",
    "scripts/plot_r2_performance_figures.py",
    "scripts/build_public_release.py",
    "scripts/r2_supplementary_analyses.py",
}

EXCLUDED_PARTS = {
    ".cursor",
    ".git",
    "deliverables",
    "result",
    "__pycache__",
}


def tracked_files() -> set[str]:
    output = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT)
    return {x.decode() for x in output.split(b"\0") if x}


def is_public_safe(rel: str) -> bool:
    p = Path(rel)
    if set(p.parts) & EXCLUDED_PARTS:
        return False
    lower = rel.lower()
    if lower.endswith((".xlsx", ".xls", ".parquet", ".npz", ".sav")):
        return False
    if lower.endswith(".pkl") and rel != "model_weights/8_features_model.pkl":
        return False
    risky_names = (
        "_ids.csv",
        "_predictions.csv",
        "_probabilities.csv",
        "patient_level",
        "row_level",
        "mimic_dataset",
    )
    if any(x in lower for x in risky_names):
        return False
    if p.parts and p.parts[0] == "data" and rel != "data/README.md":
        return False
    return True


def main() -> None:
    candidates = tracked_files() | PUBLIC_ADDITIONS
    missing = sorted(rel for rel in candidates if not (ROOT / rel).is_file())
    if missing:
        raise SystemExit(f"Missing release files: {missing}")
    files = sorted(rel for rel in candidates if is_public_safe(rel))
    rejected = sorted(rel for rel in candidates if not is_public_safe(rel))
    if any((ROOT / rel).is_file() and rel in PUBLIC_ADDITIONS for rel in rejected):
        raise SystemExit(f"An allowlisted R2 file failed the safety filter: {rejected}")

    manifest_rows = ["sha256\tbytes\tpath"]
    for rel in files:
        data = (ROOT / rel).read_bytes()
        manifest_rows.append(f"{hashlib.sha256(data).hexdigest()}\t{len(data)}\t{rel}")
    manifest = ("\n".join(manifest_rows) + "\n").encode()

    OUT.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUT_ZIP, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for rel in files:
            zf.write(ROOT / rel, f"{ARCHIVE_ROOT}/{rel}")
        zf.writestr(f"{ARCHIVE_ROOT}/PUBLIC_ARCHIVE_CONTENTS.tsv", manifest)

    digest = hashlib.sha256(OUT_ZIP.read_bytes()).hexdigest()
    report = OUT / "ZENODO_DEPOSIT_README.md"
    report.write_text(
        "\n".join(
            [
                "# Zenodo-ready release v1.1.0",
                "",
                f"- Archive: `{OUT_ZIP.name}`",
                f"- SHA-256: `{digest}`",
                f"- Files: {len(files)} plus `PUBLIC_ARCHIVE_CONTENTS.tsv`",
                "- Metadata: `.zenodo.json` and `CITATION.cff` are included.",
                "- Privacy screen: patient-level records, cohort IDs, row-level labels, row-level "
                "prediction probabilities, local workbooks, and private intermediates are excluded.",
                "- Model reproducibility route: complete analysis code plus the released non-patient-specific "
                "`model_weights/8_features_model.pkl` bundle are included.",
                "",
                "## Publication steps",
                "",
                "1. Push the reviewed v1.1.0 source state to the public GitHub repository.",
                "2. Create GitHub release/tag `v1.1.0`.",
                "3. Publish the release through the repository's Zenodo integration, or upload this archive manually.",
                "4. Copy the assigned version DOI and concept DOI into `CODE_AVAILABILITY.md`, the manuscript, "
                "the response letter, `README.md`, and `CITATION.cff`.",
                "",
                "No DOI is claimed until Zenodo confirms publication.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(f"Created {OUT_ZIP}")
    print(f"SHA-256 {digest}")
    print(f"Included {len(files)} files; safety-filtered {len(rejected)} tracked candidates")


if __name__ == "__main__":
    main()

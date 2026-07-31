#!/usr/bin/env python3
"""Replace Figure 6 image in low_fe_3 manuscripts with 18-predictor locked SHAP composite."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import shutil
import subprocess
import zipfile
from pathlib import Path

from PIL import Image
from docx import Document

ROOT = Path(__file__).resolve().parent.parent
PKG = ROOT / ".cursor" / "low_fe_3"
FIGURE_PATH = ROOT / "result" / "analysis" / "figures" / "figure6_composite.png"
MANIFEST_PATH = ROOT / "result" / "analysis" / "figures" / "figure6_shap_manifest.json"

MANUSCRIPT_FILES = [
    PKG / "Hypoferremia_Manuscript_R1_Clean.docx",
    PKG / "Hypoferremia_Manuscript_R1_Highlighted.docx",
]

MEDIA_IMAGE6 = "word/media/image6.tiff"
FORBIDDEN = frozenset({"platelet_mean", "los_icu", "bun_max"})

TEXT_REPLACEMENTS = [
    (
        "The ranked SHAP feature-importance plot (Figure 6B) confirmed this pattern, placing platelet_1st at the top, "
        "followed by blood-gas–related variables, markers of renal/metabolic dysfunction (BUN), and indicators of organ support.",
        "The ranked SHAP feature-importance plot (Figure 6B) confirmed this pattern, with SpO₂_min and ventilatory "
        "support (is_noninvasive_ventilator) showing the largest mean |SHAP| values, followed by platelet_1st, "
        "other blood-gas–related variables, markers of renal/metabolic dysfunction (BUN_min), and indicators of organ support.",
    ),
    (
        "For the 18-predictor locked benchmark model (Figure 6), variables related to hematologic status (platelet_1st), "
        "disease severity and resource use (los_icu_to_t0), baseline condition (admission age), respiratory/acid–base status "
        "(PCO₂_max, SpO₂_min, base excess), metabolic stress (anion gap, BUN), and the need for noninvasive ventilatory "
        "support had the largest absolute SHAP values.",
        "For the 18-predictor locked benchmark model (Figure 6), mean absolute SHAP values were highest for oxygenation "
        "and ventilatory support (SpO₂_min, is_noninvasive_ventilator), followed by hematologic status (platelet_1st), "
        "additional blood-gas indices (PCO₂_max), metabolic and acid–base stress (aniongap_max, baseexcess_mean, BUN_min), "
        "and age. Although los_icu_to_t0 was retained in the locked predictor matrix, it ranked lowest in this post hoc "
        "SHAP importance ordering.",
    ),
    (
        "(B) Ranked SHAP feature importance plot demonstrating that platelet count, indices of oxygenation/ventilation, "
        "acid–base status, and age were the main drivers of prediction.",
        "(B) Ranked SHAP feature importance plot (mean |SHAP|) showing that SpO₂_min, is_noninvasive_ventilator, and "
        "platelet_1st contributed most strongly, followed by other oxygenation, acid–base, and metabolic predictors.",
    ),
    (
        "On the respiratory axis, lower oxygen saturation (SpO₂_min) together with higher carbon dioxide levels (pCO₂_max) "
        "emerged as the most impactful features, reflecting impaired oxygenation and ventilation—hallmarks of critical "
        "illness associated with hypoferremia.",
        "On the respiratory axis, lower oxygen saturation (SpO₂_min) showed the largest mean |SHAP| contribution in the "
        "18-predictor locked benchmark model, with documented non-invasive ventilation and platelet_1st also ranking among "
        "the leading predictors; pCO₂_max remained among the more influential blood-gas variables, reflecting impaired "
        "oxygenation and ventilation—hallmarks of critical illness associated with hypoferremia.",
    ),
]


def _patch_figure6_text(path: Path) -> int:
    doc = Document(path)
    hits = 0
    for paragraph in doc.paragraphs:
        text = paragraph.text
        new_text = text
        for old, new in TEXT_REPLACEMENTS:
            if old in new_text:
                new_text = new_text.replace(old, new)
        if new_text != text:
            if paragraph.runs:
                paragraph.runs[0].text = new_text
                for run in paragraph.runs[1:]:
                    run.text = ""
            else:
                paragraph.text = new_text
            hits += 1
    if hits:
        doc.save(path)
    return hits


def _run_figure6_plot() -> None:
    script = ROOT / "scripts" / "plot_figure6_shap.py"
    subprocess.run([__import__("sys").executable, str(script)], cwd=ROOT, check=True)


def _figure_to_tiff_bytes(png_path: Path) -> bytes:
    buf = io.BytesIO()
    Image.open(png_path).convert("RGB").save(buf, format="TIFF", compression="tiff_deflate")
    return buf.getvalue()


def _md5(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()


def _replace_docx_image(docx_path: Path, png_path: Path, old_hash: str | None) -> str:
    tiff_bytes = _figure_to_tiff_bytes(png_path)
    new_hash = _md5(tiff_bytes)
    if old_hash and new_hash == old_hash:
        raise SystemExit(f"{docx_path.name}: image6.tiff unchanged after patch")

    tmp_path = docx_path.with_suffix(".tmp.docx")
    with zipfile.ZipFile(docx_path, "r") as zin, zipfile.ZipFile(tmp_path, "w") as zout:
        for info in zin.infolist():
            data = tiff_bytes if info.filename == MEDIA_IMAGE6 else zin.read(info.filename)
            zout.writestr(info, data)
    tmp_path.replace(docx_path)
    return new_hash


def _load_manifest() -> dict:
    if not MANIFEST_PATH.exists():
        raise SystemExit(f"Missing manifest: {MANIFEST_PATH}. Run plot_figure6_shap.py first.")
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if manifest.get("n_features") != 18:
        raise SystemExit("Manifest verify fail: n_features != 18")
    if not manifest.get("forbidden_ok"):
        raise SystemExit(f"Manifest verify fail: forbidden features {manifest.get('forbidden_absent')}")
    overlap = set(manifest.get("features", [])) & FORBIDDEN
    if overlap:
        raise SystemExit(f"Manifest verify fail: features contain {sorted(overlap)}")
    return manifest


def _verify_docx(path: Path, manifest: dict, new_image_hash: str) -> list[str]:
    errors: list[str] = []
    with zipfile.ZipFile(path) as z:
        if MEDIA_IMAGE6 not in z.namelist():
            errors.append(f"{path.name}: missing {MEDIA_IMAGE6}")
            return errors
        embedded_hash = _md5(z.read(MEDIA_IMAGE6))
        if embedded_hash != new_image_hash:
            errors.append(f"{path.name}: embedded image6 hash mismatch")

    if "platelet_1st" not in manifest.get("top3_features", []):
        errors.append(
            f"Warning-level: platelet_1st not in top3 ({manifest.get('top3_features')}); "
            "manuscript text may need review"
        )
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Patch low_fe_3 Figure 6 with 18-predictor SHAP composite")
    parser.add_argument("--regen-figure", action="store_true", help="Run plot_figure6_shap.py first")
    parser.add_argument("--backup", action="store_true", help="Save .bak copies before patching")
    args = parser.parse_args()

    if args.regen_figure:
        _run_figure6_plot()

    if not FIGURE_PATH.exists():
        raise SystemExit(f"Missing figure: {FIGURE_PATH}. Run plot_figure6_shap.py first.")

    manifest = _load_manifest()
    new_tiff_hash = _md5(_figure_to_tiff_bytes(FIGURE_PATH))

    for manuscript in MANUSCRIPT_FILES:
        if not manuscript.exists():
            raise SystemExit(f"Missing manuscript: {manuscript}")

        old_hash = None
        with zipfile.ZipFile(manuscript) as z:
            if MEDIA_IMAGE6 in z.namelist():
                old_hash = _md5(z.read(MEDIA_IMAGE6))

        if args.backup:
            shutil.copy2(manuscript, manuscript.with_suffix(".docx.bak"))

        text_hits = _patch_figure6_text(manuscript)
        patched_hash = _replace_docx_image(manuscript, FIGURE_PATH, old_hash)
        errors = _verify_docx(manuscript, manifest, patched_hash)

        print(f"Patched {manuscript.name}: image6 md5 {old_hash} -> {patched_hash}; text_hits={text_hits}")
        hard_errors = [e for e in errors if not e.startswith("Warning-level")]
        warnings = [e for e in errors if e.startswith("Warning-level")]
        for w in warnings:
            print(f"  {w}")
        if hard_errors:
            for err in hard_errors:
                print(f"  VERIFY FAIL: {err}")
            raise SystemExit(1)
        print(f"  verify OK (Figure 6 = 18-predictor locked; top_feature={manifest.get('top_feature')})")


if __name__ == "__main__":
    main()

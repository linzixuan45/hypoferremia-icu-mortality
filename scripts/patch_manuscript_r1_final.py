#!/usr/bin/env python3
"""Final R1 polish + pre-submit clean pass for low_fe_3 submission package."""
from __future__ import annotations

import re
import shutil
import zipfile
from pathlib import Path

from docx import Document

ROOT = Path(__file__).resolve().parent.parent
PKG = ROOT / ".cursor" / "low_fe_3"

OLD_TITLE = (
    "Machine-Learning Prediction of In-Hospital Mortality in Critically Ill "
    "Patients with Hypoferremia: Multi-Cohort Development, External Evaluation, "
    "and Research Web Demonstration"
)
NEW_TITLE = (
    "Machine-Learning Risk Stratification for Short-Term In-Hospital Mortality "
    "in Critically Ill Patients with Hypoferremia: Multi-Cohort Development "
    "and External Evaluation"
)

CHINESE_LAB_SENTENCE = (
    "Chinese cohort laboratory values were converted to the MIMIC-aligned model "
    "input scale before evaluation: serum creatinine from μmol/L to mg/dL (÷88.4) "
    "and blood urea nitrogen from mmol/L urea to mg/dL BUN (×2.801)."
)
NIV_SENTENCE = (
    "Binary ventilatory support was encoded as is_noninvasive_ventilator "
    "(1 = documented non-invasive ventilation use; 0 = no documented use)."
)
FIG8_UNITS = (
    "All calculator inputs use model-native units (creatinine and BUN in mg/dL; "
    "is_noninvasive_ventilator: 1 = documented non-invasive ventilation use, "
    "0 = no documented use)."
)

# Pre-submit clean pass (P0/P1)
PRESUBMIT_REPLACEMENTS: list[tuple[str, str]] = [
    (
        "one non-training same-institution MIMIC-III same-institution "
        "external/temporal/temporal evaluation cohort",
        "one non-training same-institution external/temporal MIMIC-III evaluation cohort",
    ),
    (
        "based on the 8 most influential SHAP-informed and clinically available predictors",
        "derived separately from the broader LASSO/SHAP-informed candidate feature space "
        "and retrained as a pragmatic derivative model using eight routinely available predictors",
    ),
    (
        "derivation of the 8-feature reduced panel from the most influential predictors",
        "derivation of an 8-feature reduced panel from the broader LASSO/SHAP-informed "
        "candidate feature space, independent of the prespecified 18-predictor locked-matrix exclusions",
    ),
    (
        "20-feature benchmark model scope",
        "20-variable LASSO candidate scope",
    ),
    (
        "the primary locked analysis used balanced class weights without random undersampling",
        "For algorithms supporting class or sample weighting, balanced weights were used; "
        "otherwise, models were trained on the full imbalanced training set without random undersampling",
    ),
    (
        "The 20-feature benchmark-model missingness is reported for MIMIC-IV and MIMIC-III",
        "The 20-variable LASSO candidate missingness is reported for MIMIC-IV and MIMIC-III",
    ),
    (
        "The revised Methods distinguish the LASSO-derived 20-feature benchmark model "
        "from the SHAP-derived 8-feature reduced model",
        "The revised Methods distinguish the 18-predictor locked benchmark model "
        "from the separately derived 8-feature reduced model",
    ),
    (
        "post hoc interpretation of the 20-feature model and pragmatic derivation",
        "post hoc interpretation of the 18-predictor locked benchmark model and pragmatic derivation",
    ),
]

COVER_LETTER_ITEM_10 = (
    "10. We additionally performed a unit-harmonization audit for the Chinese "
    "exploratory cohorts and converted creatinine and BUN into MIMIC-aligned mg/dL "
    "units before locked-model evaluation."
)

TEXT_REPLACEMENTS: list[tuple[str, str]] = [
    (OLD_TITLE, NEW_TITLE),
    (
        "The reduced model yielded AUROCs of 0.810 (95% CI 0.713-0.908) and "
        "0.844 (95% CI 0.760-0.928), respectively.",
        "The reduced model yielded AUROCs of 0.810 (95% CI 0.713-0.908) and "
        "0.898 (95% CI 0.835-0.961) in F3 and NH, respectively.",
    ),
    ("0.844 (95% CI 0.760-0.928)", "0.898 (95% CI 0.835-0.961)"),
    ("0.844 (0.760-0.928)", "0.898 (0.835-0.961)"),
    (
        "For 28-day in-hospital mortality from the t0-proxy origin, the 18-predictor",
        "For 28-day in-hospital mortality, the 18-predictor",
    ),
    (
        "The primary endpoint was 28-day in-hospital mortality from the t0-proxy "
        "origin during the index hospitalization. This time horizon aligned the "
        "outcome with the prespecified index time (t0) and permitted assessment of "
        "short-term prognostic relevance after documented hypoferremia was identified.",
        "The primary endpoint was 28-day in-hospital mortality during the index "
        "hospitalization after documented hypoferremia (locked t0-proxy index time). "
        "This endpoint supports retrospective, admission-proximal risk stratification "
        "rather than fully time-stamped real-time prediction.",
    ),
    (
        "In this multi-cohort study, we developed and externally evaluated an "
        "interpretable machine-learning model to predict 28-day in-hospital mortality "
        "from the t0-proxy origin in ICU patients with hypoferremia.",
        "In this multi-cohort study, we developed and externally evaluated an "
        "interpretable machine-learning framework for retrospective, admission-proximal "
        "risk stratification of 28-day in-hospital mortality among ICU patients with "
        "documented hypoferremia.",
    ),
    (
        "In summary, we developed an interpretable ML framework for 28-day "
        "in-hospital mortality from the t0-proxy origin in ICU patients with "
        "documented hypoferremia compatible with functional iron restriction",
        "In summary, we developed an interpretable ML framework for retrospective "
        "risk stratification of 28-day in-hospital mortality in ICU patients with "
        "documented hypoferremia compatible with functional iron restriction",
    ),
    (
        "Residual temporal leakage and measurement-selection bias cannot be excluded, "
        "especially for aggregate variables such as minima, maxima, and means.",
        "Residual temporal leakage and measurement-selection bias cannot be excluded, "
        "especially for aggregate variables such as minima, maxima, and means. The model "
        "should therefore be interpreted as a retrospective, admission-proximal "
        "risk-stratification model among ICU patients with documented hypoferremia, "
        "rather than a fully time-stamped real-time prediction model.",
    ),
    (
        "The Chinese results are exploratory because of small sample sizes and wide "
        "confidence intervals.",
        "The Chinese results are exploratory because of small sample sizes and wide "
        "confidence intervals. Because the Chinese cohorts lacked the full harmonized "
        "18-predictor matrix, they were used only to explore transportability of the "
        "reduced 8-feature model and should not be interpreted as geographic validation "
        "of the locked benchmark model.",
    ),
    ("MIMIC-III external", "MIMIC-III same-institution external/temporal"),
    *PRESUBMIT_REPLACEMENTS,
]

MODEL_CARD_LIMITATIONS_OLD = (
    "- Excel t₀ proxy; residual temporal-leakage risk for aggregate min/max/mean "
    "without uniform charttime\n"
    "- Serum iron alone does not identify absolute iron deficiency; ferritin/"
    "transferrin saturation not uniformly available\n"
    "- Chinese cohorts (F3/NH) are exploratory geographic validation only "
    "(option β; not re-anchored to MIMIC t₀)"
)
MODEL_CARD_LIMITATIONS_NEW = (
    "- Locked retrospective t₀-proxy definition; residual temporal-leakage risk remains "
    "for aggregate min/max/mean predictors without uniform chart-time anchoring\n"
    "- Serum iron alone does not identify absolute iron deficiency; ferritin/"
    "transferrin saturation not uniformly available\n"
    "- Chinese cohorts (F3/NH) are exploratory geographic evaluations and were not "
    "re-anchored to the MIMIC t₀ definition"
)
MODEL_CARD_CITATION_OLD = (
    "See [CITATION.bib](../CITATION.bib) and [CODE_AVAILABILITY.md]"
    "(../CODE_AVAILABILITY.md)."
)
MODEL_CARD_CITATION_NEW = (
    "See [CITATION.bib](CITATION.bib) and [CODE_AVAILABILITY.md]"
    "(CODE_AVAILABILITY.md)."
)
MODEL_CARD_CLASS_WEIGHT_OLD = (
    "- Class imbalance handled via `class_weight='balanced'` (primary); "
    "random undersampling is sensitivity-only (Supp S9)"
)
MODEL_CARD_CLASS_WEIGHT_NEW = (
    "- Primary locked soft-voting ensemble uses balanced class weights where supported; "
    "random undersampling is sensitivity-only (Supp S9)"
)
MODEL_CARD_CITATION_LINE_OLD = (
    "Li Y, et al. *Scientific Reports* — Machine-learning model for mortality risk "
    "stratification in ICU patients with functional hypoferremia."
)
MODEL_CARD_CITATION_LINE_NEW = (
    "Xie L, Zhang C, et al. *Scientific Reports* — Machine-learning model for mortality "
    "risk stratification in ICU patients with functional hypoferremia."
)

CITATION_AUTHOR_OLD = "author  = {Li, Y. and others},"
CITATION_AUTHOR_NEW = "author  = {Xie, Liangpeng and Zhang, Chang and others},"

README_CLASS_WEIGHT_OLD = (
    "- The final primary training strategy uses balanced class weights; "
    "random undersampling is sensitivity-only."
)
README_CLASS_WEIGHT_NEW = (
    "- The final primary training strategy uses balanced class or sample weights where "
    "supported; random undersampling is sensitivity-only."
)

CODE_AVAIL_ROOT_NOTE = (
    "Repository positioning: **auditable analysis source code** — pipeline logic, "
    "inference, model card, and locked reference metrics are public; patient-level "
    "data are not redistributed. See [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md) "
    "for publication-day steps."
)
CODE_AVAIL_ROOT_NOTE_WITH_REVIEW = (
    "Repository positioning: **auditable analysis source code** — pipeline logic, "
    "inference, model card, and locked reference metrics are public; patient-level "
    "data are not redistributed. See [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md) "
    "for publication-day steps. Review submission bundles may omit internal release "
    "docs; see the GitHub repository for the full file tree."
)

CODE_AVAIL_PKG_HEADER_OLD = (
    "Repository positioning: **auditable analysis source code** — pipeline logic, "
    "inference, model card, and locked reference metrics are public; patient-level "
    "data are not redistributed. See [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md) "
    "for publication-day steps. Review submission bundles may omit internal release "
    "docs; see the GitHub repository for the full file tree."
)
CODE_AVAIL_PKG_HEADER_NEW = (
    "Repository positioning: **auditable analysis source code** — pipeline logic, "
    "inference, model card, and locked reference metrics are public; patient-level "
    "data are not redistributed. Full release documentation is available at "
    "https://github.com/linzixuan45/hypoferremia-icu-mortality."
)

CODE_AVAIL_PKG_WHAT_DEPOSITED_OLD = """## What is deposited

The archived repository includes:

- Analysis pipeline (`scripts/`)
- MIMIC SQL extraction scripts (`sql/`)
- Inference code (`inference.py`)
- Released 8-feature model bundle (`model_weights/8_features_model.pkl`)
- Model card and data dictionary (`MODEL_CARD.md`, `docs/data_dictionary.md`)
- Methods documentation (`docs/FE1_spec.md`, `docs/data_flow_cohorts.md`)
- Locked reference metrics (`reference/manifest.json`)

Raw patient-level data, cohort ID lists, and summary result tables are **not** redistributed because MIMIC and local validation data are access-restricted."""

CODE_AVAIL_PKG_WHAT_DEPOSITED_NEW = """## What is deposited

The public GitHub repository includes the analysis pipeline, MIMIC SQL extraction scripts, inference code, released 8-feature research model bundle, model card, and data dictionary. Raw patient-level data are not redistributed because MIMIC and local validation data are access-restricted. Full repository documentation and locked reference metrics are available at https://github.com/linzixuan45/hypoferremia-icu-mortality."""

CITATION_ZIP_FILES = [
    "CITATION.bib",
    "CODE_AVAILABILITY.md",
    "Hypoferremia_Manuscript_R1_Clean.docx",
    "Hypoferremia_Manuscript_R1_Highlighted.docx",
    "Hypoferremia_Supplementary_R1_Clean.docx",
    "Hypoferremia_Supplementary_R1_Highlighted.docx",
    "Hypoferremia_TRIPOD_AI_Checklist_R1.docx",
    "Letter_to_Editor_R1.docx",
    "MODEL_CARD.md",
    "README.md",
    "Response_to_Reviewers_R1.docx",
    "Response_to_Reviewers_R1_Highlighted.docx",
]


def _dedupe_phrase(text: str, phrase: str) -> str:
    while text.count(phrase) > 1:
        second = text.find(phrase, text.find(phrase) + 1)
        text = (text[:second] + text[second + len(phrase) :]).strip()
        text = re.sub(r"\.\.+", ".", text)
        text = re.sub(r"\s{2,}", " ", text)
    return text


def _normalize_dedupes(text: str) -> str:
    text = _dedupe_phrase(text, CHINESE_LAB_SENTENCE)
    text = _dedupe_phrase(text, NIV_SENTENCE)
    text = _dedupe_phrase(text, FIG8_UNITS)
    text = re.sub(r"\.\.+", ".", text)
    text = re.sub(r"\s+\.", ".", text)
    return text.strip()


def _replace_in_paragraph(paragraph, replacements: list[tuple[str, str]]) -> bool:
    text = _normalize_dedupes(paragraph.text)
    new_text = text
    for old, new in replacements:
        if old in new_text:
            new_text = new_text.replace(old, new)
    if new_text != paragraph.text:
        if paragraph.runs:
            paragraph.runs[0].text = new_text
            for run in paragraph.runs[1:]:
                run.text = ""
        else:
            paragraph.text = new_text
        return True
    return False


def patch_docx(path: Path) -> int:
    doc = Document(path)
    hits = 0
    for p in doc.paragraphs:
        if _replace_in_paragraph(p, TEXT_REPLACEMENTS):
            hits += 1
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    if _replace_in_paragraph(p, TEXT_REPLACEMENTS):
                        hits += 1
    if "Supplementary" in path.name:
        hits += _fix_s10_table(doc)
        hits += _fix_s6a_title(doc)
    if path.name.startswith("Letter_to_Editor"):
        hits += _patch_cover_letter(doc)
    doc.save(path)
    return hits


def _fix_s6a_title(doc: Document) -> int:
    hits = 0
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                if cell.text.strip() == "20-feature benchmark model scope":
                    cell.text = "20-variable LASSO candidate scope"
                    hits += 1
    return hits


def _patch_cover_letter(doc: Document) -> int:
    if any(COVER_LETTER_ITEM_10 in p.text for p in doc.paragraphs):
        return 0
    from docx.oxml import OxmlElement
    from docx.text.paragraph import Paragraph

    for para in doc.paragraphs:
        if para.text.strip().startswith("9. We revised the submission package format"):
            new_el = OxmlElement("w:p")
            para._element.addnext(new_el)
            new_para = Paragraph(new_el, para._parent)
            new_para.text = COVER_LETTER_ITEM_10
            return 1
    return 0


def _fix_s10_table(doc: Document) -> int:
    """Remove duplicate MIMIC rows in S10; normalize cohort labels."""
    for table in doc.tables:
        flat = " ".join(c.text for row in table.rows for c in row.cells)
        if "F3" not in flat or "AUROC" not in flat:
            continue
        seen: set[tuple[str, str, str, str]] = set()
        rows_to_delete: list = []
        for row in table.rows[1:]:
            cells = [c.text.strip() for c in row.cells]
            if len(cells) < 4:
                continue
            cohort = cells[0].replace(
                "MIMIC-III external", "MIMIC-III same-institution external/temporal"
            )
            key = (cohort, cells[1], cells[2], cells[3])
            if key in seen:
                rows_to_delete.append(row)
            else:
                seen.add(key)
                if cells[0] != cohort:
                    row.cells[0].text = cohort
        for row in reversed(rows_to_delete):
            table._tbl.remove(row._tr)
        return len(rows_to_delete)
    return 0


def patch_citation_bib(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    if CITATION_AUTHOR_OLD not in text:
        return False
    path.write_text(text.replace(CITATION_AUTHOR_OLD, CITATION_AUTHOR_NEW), encoding="utf-8")
    return True


def patch_model_card(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = text.replace(MODEL_CARD_LIMITATIONS_OLD, MODEL_CARD_LIMITATIONS_NEW)
    text = text.replace(MODEL_CARD_CITATION_OLD, MODEL_CARD_CITATION_NEW)
    text = text.replace(MODEL_CARD_CLASS_WEIGHT_OLD, MODEL_CARD_CLASS_WEIGHT_NEW)
    text = text.replace(MODEL_CARD_CITATION_LINE_OLD, MODEL_CARD_CITATION_LINE_NEW)
    text = text.replace(OLD_TITLE, NEW_TITLE)
    path.write_text(text, encoding="utf-8")


def patch_readme(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = text.replace(OLD_TITLE, NEW_TITLE)
    text = text.replace(OLD_TITLE + ".", NEW_TITLE + ".")
    text = text.replace(README_CLASS_WEIGHT_OLD, README_CLASS_WEIGHT_NEW)
    path.write_text(text, encoding="utf-8")


def patch_code_availability_root(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if CODE_AVAIL_ROOT_NOTE_WITH_REVIEW not in text:
        text = text.replace(CODE_AVAIL_ROOT_NOTE, CODE_AVAIL_ROOT_NOTE_WITH_REVIEW)
    path.write_text(text, encoding="utf-8")


def patch_code_availability_pkg(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = text.replace(CODE_AVAIL_PKG_HEADER_OLD, CODE_AVAIL_PKG_HEADER_NEW)
    text = text.replace(CODE_AVAIL_PKG_WHAT_DEPOSITED_OLD, CODE_AVAIL_PKG_WHAT_DEPOSITED_NEW)
    if "RELEASE_CHECKLIST.md" in text.split("## What is deposited")[0]:
        text = text.replace(
            "See [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md) for publication-day steps.",
            "See the GitHub repository for full release documentation.",
        )
        text = text.replace(
            "Review submission bundles may omit internal release "
            "docs; see the GitHub repository for the full file tree.",
            "",
        )
    path.write_text(text, encoding="utf-8")


def sync_package_files() -> None:
    for name in ("CITATION.bib", "CODE_AVAILABILITY.md", "MODEL_CARD.md"):
        src = ROOT / name
        dst = PKG / name
        if src.exists():
            shutil.copy2(src, dst)


def rebuild_citation_zip() -> None:
    zip_path = PKG / "CITATION.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name in CITATION_ZIP_FILES:
            src = PKG / name
            if src.exists():
                zf.write(src, arcname=name)
            else:
                print(f"WARNING: missing for CITATION.zip: {name}")


def check_replacements_in_pkg() -> None:
    """Report PRESUBMIT replacement strings not found in any docx (pre-run diagnostic)."""
    import xml.etree.ElementTree as ET

    def docx_text(p: Path) -> str:
        with zipfile.ZipFile(p) as z:
            root = ET.fromstring(z.read("word/document.xml"))
        return "".join(
            (t.text or "") + (t.tail or "")
            for t in root.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t")
        )

    combined = ""
    for path in PKG.glob("*.docx"):
        combined += docx_text(path)

    print("\n--- Replacement miss report (post-patch) ---")
    for old, _new in PRESUBMIT_REPLACEMENTS:
        if old in combined:
            print(f"MISS (still present): {old[:70]}...")
        else:
            print(f"OK (absent): {old[:70]}...")


def main() -> None:
    docx_files = [
        PKG / "Hypoferremia_Manuscript_R1_Clean.docx",
        PKG / "Hypoferremia_Manuscript_R1_Highlighted.docx",
        PKG / "Hypoferremia_Supplementary_R1_Clean.docx",
        PKG / "Hypoferremia_Supplementary_R1_Highlighted.docx",
        PKG / "Response_to_Reviewers_R1.docx",
        PKG / "Response_to_Reviewers_R1_Highlighted.docx",
        PKG / "Letter_to_Editor_R1.docx",
    ]
    for path in docx_files:
        if path.exists():
            n = patch_docx(path)
            print(f"Patched {path.name}: {n} hits")

    patch_citation_bib(ROOT / "CITATION.bib")
    patch_model_card(ROOT / "MODEL_CARD.md")
    patch_code_availability_root(ROOT / "CODE_AVAILABILITY.md")
    sync_package_files()
    patch_code_availability_pkg(PKG / "CODE_AVAILABILITY.md")
    patch_model_card(PKG / "MODEL_CARD.md")
    patch_readme(PKG / "README.md")
    rebuild_citation_zip()
    check_replacements_in_pkg()
    print("Synced MODEL_CARD, README, CITATION.bib, CODE_AVAILABILITY.md; rebuilt CITATION.zip")


if __name__ == "__main__":
    main()

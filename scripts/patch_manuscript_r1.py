#!/usr/bin/env python3
"""Apply R1 resubmit text/table patches to Word manuscripts (harmonization + wording)."""
from __future__ import annotations

from pathlib import Path

from docx import Document

ROOT = Path(__file__).resolve().parent.parent
PKG = ROOT / ".cursor" / "low_fe_3"

# Shared replacements (order: longer / more specific first where needed)
COMMON_REPLACEMENTS: list[tuple[str, str]] = [
    (
        "0.776 (95% CI 0.665-0.888)",
        "0.810 (95% CI 0.713-0.908)",
    ),
    (
        "0.844 (0.760-0.928)",
        "0.898 (0.835-0.961)",
    ),
    (
        "0.776 (0.665-0.888)",
        "0.810 (0.713-0.908)",
    ),
    (
        "0.844 (0.760-0.928)",
        "0.898 (0.835-0.961)",
    ),
    (
        "with AUROCs of 0.796, 0.733, 0.776, and 0.844, respectively",
        "with AUROCs of 0.796 (95% CI 0.718-0.874), 0.733 (0.692-0.775), 0.810 (0.713-0.908), and 0.898 (0.835-0.961), respectively",
    ),
    (
        "demonstrating consistent discrimination (AUC 0.733-0.844)",
        "demonstrating consistent discrimination (AUC 0.733-0.898)",
    ),
    (
        "low SpO₂, high PCO₂, and low BUN_min jointly increase the predicted probability of death",
        "low SpO₂, high PCO₂, and elevated BUN_min jointly increase the predicted probability of death",
    ),
    (
        "Unfavorable values—lower platelet counts, lower SpO₂_min, higher PCO₂_max, higher BUN_min, and the need for noninvasive ventilation—were generally associated with higher predicted risk, whereas higher platelet_1st and preserved creatinine_min shifted the prediction toward lower risk.",
        "Unfavorable values—lower platelet counts, lower SpO₂_min, higher PCO₂_max, and higher BUN_min—were generally associated with higher predicted risk, whereas higher platelet_1st, preserved creatinine_min, and documented non-invasive ventilation (is_noninvasive_ventilator = 1) shifted the prediction toward lower risk. Univariate tables showed higher NIV use among survivors; multivariate SHAP attributions should not be interpreted causally.",
    ),
    (
        "requirement for noninvasive ventilation, metabolic acidosis",
        "absence of documented non-invasive ventilation (is_noninvasive_ventilator = 0), metabolic acidosis",
    ),
    (
        "Predictors were constructed using a t0-proxy framework anchored to the first documented hypoferremia state, as permitted by the locked retrospective export.",
        "Predictors were constructed using a locked t0-proxy framework that primarily reflected admission-documented hypoferremia in MIMIC-IV (admission stratum n=1,338; acquired stratum n=6), as permitted by the locked retrospective export, with residual temporal-leakage risk acknowledged.",
    ),
    (
        "All datasets were harmonized using a common data model to standardize variable definitions, coding, and units before analysis. Chinese cohort laboratory values were converted to the MIMIC-aligned model input scale before evaluation: serum creatinine from μmol/L to mg/dL (÷88.4) and blood urea nitrogen from mmol/L urea to mg/dL BUN (×2.801).",
        "All datasets were harmonized using a common data model to standardize variable definitions, coding, and units before analysis. Chinese cohort laboratory values were converted to the MIMIC-aligned model input scale before evaluation: serum creatinine from μmol/L to mg/dL (÷88.4) and blood urea nitrogen from mmol/L urea to mg/dL BUN (×2.801).",
    ),
    (
        "Binary ventilatory support was encoded as is_noninvasive_ventilator (1 = documented non-invasive ventilation use; 0 = no documented use). Variables with cohort-specific high missingness, particularly non-invasive ventilation in MIMIC-III, were interpreted cautiously",
        "Binary ventilatory support was encoded as is_noninvasive_ventilator (1 = documented non-invasive ventilation use; 0 = no documented use). Variables with cohort-specific high missingness, particularly non-invasive ventilation in MIMIC-III, were interpreted cautiously",
    ),
]

MANUSCRIPT_ONLY: list[tuple[str, str]] = [
    (
        "Figure 8. Research web demonstration of the reduced 8-feature mortality prediction model. All calculator inputs use model-native units (creatinine and BUN in mg/dL; is_noninvasive_ventilator: 1 = documented non-invasive ventilation use, 0 = no documented use).",
        "Figure 8. Research web demonstration of the reduced 8-feature mortality prediction model. All calculator inputs use model-native units (creatinine and BUN in mg/dL; is_noninvasive_ventilator: 1 = documented non-invasive ventilation use, 0 = no documented use).",
    ),
    (
        "Screenshot of the research web application built on the 8-feature Ensemble_Voting model. The upper panel provides input fields",
        "Screenshot of the research web application built on the 8-feature Ensemble_Voting model. All inputs use model-native units (creatinine and BUN in mg/dL). The upper panel provides input fields",
    ),
]


def _patch_table2_interpretation(doc: Document) -> None:
    """Table 2 (internal test): LR interpretation external -> internal."""
    for table in doc.tables:
        for row in table.rows:
            row_text = " ".join(c.text for c in row.cells)
            if "0.846" in row_text and "Comparable external discrimination" in row_text:
                for cell in row.cells:
                    if "Comparable external discrimination" in cell.text:
                        for p in cell.paragraphs:
                            _replace_in_paragraph(
                                p,
                                [("Comparable external discrimination", "Comparable internal discrimination")],
                            )
                return

SUPPLEMENTARY_ONLY: list[tuple[str, str]] = [
    (
        "Note: Supplementary Table S1 is a descriptive subset table among MIMIC-III patients with complete locked predictor profiles (n=399; non-survivors=73, survivors=326) stratified by locked t0-proxy 28-day in-hospital death (outcome_28d_t0). This subset is not the analytic denominator for performance evaluation. The locked MIMIC-III same-institution external/temporal evaluation analysis used all 1,046 eligible patients after applying the training-set-fitted imputation workflow, with 171 t0-proxy 28-day in-hospital death events (Table 3). Supplementary Table S1 is provided for descriptive context only.",
        "Note: Supplementary Table S1 describes MIMIC-III patients with complete 8-feature reduced-model predictor profiles among the 1,046 eligible cohort (n=399; non-survivors=73, survivors=326; complete-case before imputation). This is not the analytic denominator for the 18-predictor benchmark evaluation (n=1,046 after training-set-fitted imputation) nor the 18-predictor complete-case transparency row in Supplementary Table S7 (n=311 after ICU stay ≥48 h filtering). Supplementary Table S1 is provided for descriptive context only.",
    ),
    (
        "Supplementary Table S10. Chinese exploratory cohort performance (locked reduced model).",
        "Supplementary Table S10. Eight-feature reduced model performance across four cohorts.",
    ),
    # F3 harmonized labs (S2)
    ("8.03 (5.52–10.7) (n=26)", "22 (15–30) (n=26)"),
    ("8.03 (5.52-10.7) (n=26)", "22 (15-30) (n=26)"),
    ("5.18 (3.74–8.39) (n=75)", "15 (10–24) (n=75)"),
    ("5.18 (3.74-8.39) (n=75)", "15 (10-24) (n=75)"),
    ("64.5 (46.2–100) (n=26)", "0.73 (0.52–1.1) (n=26)"),
    ("64.5 (46.2-100) (n=26)", "0.73 (0.52-1.1) (n=26)"),
    ("60 (47–100) (n=75)", "0.68 (0.53–1.1) (n=75)"),
    ("60 (47-100) (n=75)", "0.68 (0.53-1.1) (n=75)"),
    # NH harmonized labs (S3)
    ("64 (49–101) (n=37)", "0.72 (0.55–1.1) (n=37)"),
    ("64 (49-101) (n=37)", "0.72 (0.55-1.1) (n=37)"),
    ("59 (44–95) (n=61)", "0.67 (0.5–1.1) (n=61)"),
    ("59 (44-95) (n=61)", "0.67 (0.5-1.1) (n=61)"),
    ("6.75 (4.63–10.1) (n=37)", "19 (13–28) (n=37)"),
    ("6.75 (4.63-10.1) (n=37)", "19 (13-28) (n=37)"),
    ("5.15 (3.85–7.73) (n=61)", "14 (11–22) (n=61)"),
    ("5.15 (3.85-7.73) (n=61)", "14 (11-22) (n=61)"),
]

RESPONSE_ADDITION = """

Additional revision (unit harmonization and variable-definition audit, June 2026):

We thank the internal audit that identified cross-cohort laboratory unit inconsistency in the Chinese exploratory cohorts. The locked export stored F3/NH creatinine in μmol/L and BUN in mmol/L urea, whereas the MIMIC-aligned model expects mg/dL. We now convert creatinine (÷88.4) and BUN (×2.801) before locked-model evaluation, updated Supplementary Tables S2/S3, Methods, the model card, and the analysis code (`external_cohort_data.py`). Re-evaluated 8-feature AUROCs are 0.810 (95% CI 0.713-0.908) for F3 and 0.898 (0.835-0.961) for NH; MIMIC metrics are unchanged because training weights were not refit.

We clarified that is_noninvasive_ventilator = 1 indicates documented non-invasive ventilation use. Univariate tables show higher NIV among survivors; multivariate SHAP for the reduced model associates NIV=1 with lower predicted risk. Manuscript SHAP wording was corrected accordingly.

Supplementary Table S1 now explicitly distinguishes the n=399 descriptive 8-feature complete-case subset from the n=311 18-predictor complete-case transparency row in S7. Supplementary Table S10 now reports all four 8-feature cohorts with 95% CIs.

Figure 8 caption now states that calculator inputs use model-native mg/dL units; the web demo screenshot should be updated manually before resubmission.
"""


def _replace_in_paragraph(paragraph, replacements: list[tuple[str, str]]) -> int:
    text = paragraph.text
    if not text:
        return 0
    new_text = text
    n = 0
    for old, new in replacements:
        if old in new_text:
            new_text = new_text.replace(old, new)
            n += 1
    if new_text != text:
        if paragraph.runs:
            paragraph.runs[0].text = new_text
            for run in paragraph.runs[1:]:
                run.text = ""
        else:
            paragraph.text = new_text
    return n


def patch_document(path: Path, extra: list[tuple[str, str]]) -> int:
    doc = Document(path)
    reps = COMMON_REPLACEMENTS + extra
    count = 0
    for p in doc.paragraphs:
        count += _replace_in_paragraph(p, reps)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    count += _replace_in_paragraph(p, reps)
    doc.save(path)
    return count


def append_response_note(path: Path) -> None:
    doc = Document(path)
    full = "\n".join(p.text for p in doc.paragraphs)
    marker = "Additional revision (unit harmonization and variable-definition audit"
    if marker in full:
        return
    doc.add_paragraph(RESPONSE_ADDITION.strip())
    doc.save(path)


def insert_s10_rows(path: Path) -> None:
    """Append MIMIC-IV/MIMIC-III rows to S10 table if last table has 2 data rows."""
    doc = Document(path)
    if not doc.tables:
        return
    # Find table whose first row contains 'F3' or header 'Cohort'
    target = None
    for table in doc.tables:
        flat = " ".join(c.text for row in table.rows for c in row.cells)
        if "F3" in flat and "AUROC" in flat:
            target = table
            break
    if target is None:
        return
    flat = " ".join(c.text for row in target.rows for c in row.cells)
    if "MIMIC-IV internal test" in flat:
        return
    new_rows = [
        ("MIMIC-IV internal test", "269", "40", "0.796 (0.718-0.874)"),
        ("MIMIC-III same-institution external/temporal", "1046", "171", "0.733 (0.692-0.775)"),
    ]
    for cohort, n, ev, auroc in new_rows:
        cells = target.add_row().cells
        if len(cells) >= 4:
            cells[0].text = cohort
            cells[1].text = n
            cells[2].text = ev
            cells[3].text = auroc
    doc.save(path)


def main() -> None:
    files = {
        "manuscript": [
            PKG / "Hypoferremia_Manuscript_R1_Clean.docx",
            PKG / "Hypoferremia_Manuscript_R1_Highlighted.docx",
        ],
        "supplementary": [
            PKG / "Hypoferremia_Supplementary_R1_Clean.docx",
            PKG / "Hypoferremia_Supplementary_R1_Highlighted.docx",
        ],
        "response": [
            PKG / "Response_to_Reviewers_R1.docx",
            PKG / "Response_to_Reviewers_R1_Highlighted.docx",
        ],
    }
    for path in files["manuscript"]:
        if path.exists():
            doc = Document(path)
            reps = COMMON_REPLACEMENTS + MANUSCRIPT_ONLY
            count = 0
            for p in doc.paragraphs:
                count += _replace_in_paragraph(p, reps)
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        for p in cell.paragraphs:
                            count += _replace_in_paragraph(p, reps)
            _patch_table2_interpretation(doc)
            doc.save(path)
            print(f"Patched manuscript {path.name}: {count} paragraph/cell hits")
    for path in files["supplementary"]:
        if path.exists():
            n = patch_document(path, SUPPLEMENTARY_ONLY)
            insert_s10_rows(path)
            print(f"Patched supplementary {path.name}: {n} paragraph/cell hits")
    for path in files["response"]:
        if path.exists():
            n = patch_document(path, [])
            append_response_note(path)
            print(f"Patched response {path.name}: {n} hits + audit note")
    # Submission MODEL_CARD copy
    mc = PKG / "MODEL_CARD.md"
    if mc.exists():
        src = (ROOT / "MODEL_CARD.md").read_text(encoding="utf-8")
        mc.write_text(src, encoding="utf-8")
        print("Synced .cursor/low_fe_3/MODEL_CARD.md")


if __name__ == "__main__":
    main()

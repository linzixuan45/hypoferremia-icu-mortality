from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    path = ROOT / relative
    if not path.is_file():
        raise AssertionError(f"Required revision file is missing: {relative}")
    return path.read_text(encoding="utf-8")


class RevisionSourceTests(unittest.TestCase):
    def test_riper_and_private_inputs_are_ignored(self) -> None:
        ignore = read(".gitignore")
        self.assertRegex(ignore, r"(?m)^\.trae/$")
        self.assertRegex(ignore, r"(?m)^\.cursor/$")
        self.assertRegex(ignore, r"(?m)^qa_r2_final/$")

    def test_serum_iron_analysis_is_not_ordinal_or_leaky(self) -> None:
        source = read("scripts/r2_supplementary_analyses.py")
        self.assertNotIn('"race_code"', source)
        self.assertNotIn("imputer.fit_transform(frame[numeric])", source)
        self.assertIn("OneHotEncoder", source)
        self.assertIn("ColumnTransformer", source)

    def test_true_restricted_cubic_spline_is_documented_in_code(self) -> None:
        source = read("scripts/r2_supplementary_analyses.py")
        self.assertNotIn('"bs(iron_1st', source)
        self.assertIn("restricted cubic spline", source.lower())
        for percentile in ("0.05", "0.35", "0.65", "0.95"):
            self.assertIn(percentile, source)

    def test_web_ui_always_displays_mortality_probability(self) -> None:
        source = read("webui.py")
        self.assertIn("28-day mortality probability", source)
        self.assertNotIn("28-day survival probability", source)

    def test_sql_uses_mimic_iv_iron_itemid_and_valid_outtime_flow(self) -> None:
        sql = read("sql/export_t0_cohort.sql")
        self.assertRegex(sql, r"\b50952\b")
        self.assertNotRegex(sql, r"\b50998\b|\b50809\b")
        if "t.icu_outtime" in sql:
            t0_match = re.search(r"t0\s+AS\s*\((.*?)\)\s*SELECT", sql, re.I | re.S)
            self.assertIsNotNone(t0_match)
            self.assertIn("icu_outtime", t0_match.group(1))

    def test_public_text_does_not_overclaim_raw_etl(self) -> None:
        paths = [
            "README.md",
            "MODEL_CARD.md",
            "CODE_AVAILABILITY.md",
            "DATA_AVAILABILITY.md",
        ]
        forbidden = [
            "complete raw-mimic etl",
            "complete variable-extraction sql",
            "reproduce the workflow from the controlled source databases",
        ]
        for relative in paths:
            text = read(relative).lower()
            for phrase in forbidden:
                self.assertNotIn(phrase, text, msg=f"{relative}: {phrase}")

    def test_current_manifest_uses_corrected_mimic3_denominator(self) -> None:
        path = ROOT / "reference/r2/r2_analysis_manifest.json"
        self.assertTrue(path.is_file(), "R2 analysis manifest is missing")
        manifest = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["mimic3_corrected_n"], 799)
        self.assertEqual(manifest["mimic3_corrected_events"], 140)


if __name__ == "__main__":
    unittest.main()

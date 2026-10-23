"""Data-free checks for the R3 reporting correction, not model validation."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from plot_figure7b_auroc import AXIS_LABEL, load_aggregate_rows


def test_internal_reduced_interval_is_the_verified_delong_interval() -> None:
    rows = load_aggregate_rows()
    internal = rows[0]
    assert (internal["n"], internal["Events"], internal["CI_method"]) == (269, 40, "DeLong")
    np.testing.assert_allclose(
        [internal["AUROC"], internal["CI_lo"], internal["CI_hi"]],
        [0.7962882096069869, 0.7183612417056014, 0.8742151775083723],
        rtol=0, atol=1e-15,
    )
    with (ROOT / "reference/table2_3_performance.csv").open(encoding="utf-8", newline="") as handle:
        table = list(csv.DictReader(handle))
    internal_table = [r for r in table if r["Model"] == "Post hoc 8-feature derivative" and r["Cohort"] == "MIMIC-IV internal test"]
    assert len(internal_table) == 1
    assert internal_table[0]["AUROC_95CI"] == "0.718-0.874"


def test_non_internal_intervals_follow_the_regenerated_canonical_policy() -> None:
    expected = [
        (799, 140, 0.7154617385649252, 0.6693141664860177, 0.7625798016475178),
        (101, 26, 0.8102564102564103, 0.6994615384615384, 0.9000128205128205),
        (98, 37, 0.898094816127603, 0.8258639787328312, 0.953932210899424),
    ]
    for actual, values in zip(load_aggregate_rows()[1:], expected):
        np.testing.assert_allclose([actual[k] for k in ("n", "Events", "AUROC", "CI_lo", "CI_hi")], values, rtol=0, atol=1e-15)
        assert actual["CI_method"] == "Stratified bootstrap"


def test_calibration_reference_intervals_match_redacted_prediction_audit() -> None:
    audit = json.loads((ROOT / "docs/R3_AGGREGATE_PREDICTION_AUDIT.json").read_text(encoding="utf-8"))
    with (ROOT / "reference/r2/r2_standard_calibration_metrics.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    keys = [
        "benchmark_internal_test", "reduced_internal_test",
        "Third_Xiangya_reduced_exploratory", "USC_FAH_reduced_exploratory",
        "benchmark_temporal_parent_cohort", "reduced_temporal_parent_cohort",
    ]
    assert len(rows) == len(keys)
    for row, key in zip(rows, keys):
        source = audit[key]
        np.testing.assert_allclose(
            [float(row[x]) for x in ("n", "Events", "AUROC", "AUROC_95CI_lo", "AUROC_95CI_hi")],
            [source[x] for x in ("n", "events", "AUROC", "CI_lower", "CI_upper")],
            rtol=0, atol=1e-15,
        )
        expected_method = "DeLong" if key.endswith("internal_test") else "stratified bootstrap"
        assert row["AUROC_CI_method"] == expected_method
    with (ROOT / "reference/r2/r2_corrected_mimic3_evaluation.csv").open(encoding="utf-8", newline="") as handle:
        temporal = list(csv.DictReader(handle))
    assert temporal == rows[-2:]
    assert audit["non_internal_ci_method"]["replicates"] == 2000
    assert audit["non_internal_ci_method"]["random_state"] == 42


def test_candidate_does_not_claim_a_new_public_release() -> None:
    audit = json.loads((ROOT / "docs/R3_CORRECTION_AUDIT.json").read_text(encoding="utf-8"))
    metadata = json.loads((ROOT / ".zenodo.json").read_text(encoding="utf-8"))
    assert audit["new_release_version"] is None
    assert audit["new_version_doi"] is None
    assert audit["training_logic_changed"] is False
    assert audit["primary_model_training_performed"] is False
    assert audit["existing_NIV_sensitivity_verification"]["refitted_for_verification"] is True
    assert audit["source_archive"]["doi"] == "10.5281/zenodo.21772246"
    assert "version" not in metadata
    assert AXIS_LABEL == "AUROC (95% CI)"

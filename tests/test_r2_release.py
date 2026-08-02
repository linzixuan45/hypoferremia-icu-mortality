from __future__ import annotations

import json
import csv
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from metric_intervals import auroc_ci_for_cohort, ci_method_for_cohort


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_release_identity_and_scope() -> None:
    text = read("README.md") + read("CODE_AVAILABILITY.md")
    assert "v1.2.0" in text
    assert "authorized" in text.lower()
    assert "raw-clinical-database-to-modelling-table" in text
    assert "fitted preprocessing" in text


def test_audited_numerical_environment_is_pinned() -> None:
    frozen = read("requirements-frozen.txt")
    assert "scikit-learn==1.8.0" in frozen
    assert "xgboost==3.2.0" in frozen
    lock = read("ENVIRONMENT_LOCK.md")
    assert "XGBoost 3.3.0" in lock


def test_no_fitted_or_patient_level_artifacts_are_tracked() -> None:
    forbidden_suffixes = {".xlsx", ".xls", ".parquet", ".pkl", ".joblib", ".npz"}
    offenders = [
        str(path.relative_to(ROOT))
        for path in ROOT.rglob("*")
        if path.is_file() and ".git" not in path.parts and path.suffix.lower() in forbidden_suffixes
    ]
    assert offenders == []


def test_endpoint_and_corrected_mimic3_are_active() -> None:
    source = read("scripts/build_t0_cohort.py")
    assert "outcome_28d_from_admission" in source
    assert 'm3_external = m3_base' in source
    assert "death_in_hospital_within_28_days_from_hospital_admission" in source
    assert "outcome_28d_t0" not in source


def test_active_pipeline_is_not_silent_partial_success() -> None:
    source = read("scripts/run_r2_analysis.py")
    assert "required step failed" in source
    assert "required outputs are missing" in source
    assert 'run("run_pipeline.py")' in source
    assert 'run("r2_supplementary_analyses.py")' in source


def test_r2_manifest_has_corrected_denominators() -> None:
    manifest = json.loads(read("reference/r2/r2_analysis_manifest.json"))
    assert manifest["mimic4_eligible_n"] == 1487
    assert manifest["mimic4_complete_locked_matrix_n"] == 1344
    assert manifest["mimic3_corrected_n"] == 799
    assert manifest["mimic3_corrected_events"] == 140


def test_locked_round_2_discrimination_values_are_reproduced() -> None:
    path = ROOT / "reference" / "r2" / "r2_standard_calibration_metrics.csv"
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    observed = {(row["Analysis"], row["Cohort"]): round(float(row["AUROC"]), 3) for row in rows}
    assert observed[("Locked 18-predictor soft-voting model", "MIMIC-IV internal test")] == 0.840
    assert observed[("Locked 18-predictor soft-voting model", "MIMIC-III corrected eligibility set (ICU LOS >=48 h)")] == 0.705
    assert observed[("Reduced 8-feature soft-voting model", "MIMIC-IV internal test")] == 0.796
    assert observed[("Reduced 8-feature soft-voting model", "MIMIC-III corrected eligibility set (ICU LOS >=48 h)")] == 0.715
    assert observed[("Reduced 8-feature soft-voting model", "F3 exploratory geographic cohort")] == 0.810
    assert observed[("Reduced 8-feature soft-voting model", "NH exploratory geographic cohort")] == 0.898


def test_ensemble_parameters_match_code_and_metadata() -> None:
    metadata = json.loads(read("reference/r2/model_bundle_metadata.json"))
    ensemble = metadata["ensemble"]
    train = read("scripts/train_models.py")
    benchmark = read("scripts/plot_figure4_benchmark.py")
    for source in (train, benchmark):
        assert "n_estimators=200" in source
        assert "max_depth=6" in source
        assert "n_estimators=120" in source
        assert "max_depth=4" in source
        assert "learning_rate=0.08" in source
    assert ensemble["random_forest"]["n_estimators"] == 200
    assert ensemble["random_forest"]["max_depth"] == 6
    assert ensemble["xgboost"]["n_estimators"] == 120
    assert ensemble["xgboost"]["max_depth"] == 4
    assert ensemble["xgboost"]["learning_rate"] == 0.08


def test_privacy_safe_export_writes_metadata_only() -> None:
    source = read("scripts/export_github_weights.py")
    assert "metadata_only" in source
    assert "public_pickle_exported" in source
    assert "model_weights" not in source


def test_r2_aggregate_outputs_cover_major_audits() -> None:
    required = [
        "r2_patient_flow.csv",
        "r2_multiple_imputation_sensitivity.csv",
        "r2_standard_calibration_metrics.csv",
        "r2_niv_exclusion_sensitivity.csv",
        "r2_iron_adjusted_effect.csv",
        "r2_iron_incremental_value.csv",
        "r2_duration_proxy_exclusion_sensitivity.csv",
        "observation_patient_sensitivity.csv",
        "patient_unit_audit.csv",
    ]
    assert all((ROOT / "reference" / "r2" / name).is_file() for name in required)


def test_research_interface_uses_mortality_direction_and_component_label() -> None:
    for relative in ("webui.py", "web/webui_low_fe.py"):
        text = read(relative)
        assert "28-day mortality probability" in text
        assert "28-day survival probability" not in text
        assert "XGBoost component explanation" in text
        assert "Case-level SHAP dot summary" in text
        assert "Global attribution summary" not in text
        assert "not for clinical decision-making" in text
        assert "ICP_BEIAN" not in text


def test_active_pipeline_does_not_generate_legacy_training_table1() -> None:
    source = read("scripts/run_pipeline.py")
    assert 'run_step("build_table1_baseline"' not in source


def test_figure4_guardrails_match_final_internal_values() -> None:
    source = read("scripts/plot_figure4_benchmark.py")
    assert '"KNN": 0.712' in source
    assert '"Ensemble_Stacking": 0.840' in source


def test_manuscript_table1_aggregate_reports_availability_and_omits_sparse_height() -> None:
    text = read("reference/r2/r2_table1_mimic4_eligible.csv")
    assert "Height, Median" not in text
    assert "[n=1487]" in text
    assert "Any documented ventilatory support" in text
    assert "Ld," not in text
    assert "SpO₂ (%)" in text


def test_ci_method_is_locked_by_evaluation_setting() -> None:
    assert ci_method_for_cohort("MIMIC-IV internal test") == "DeLong"
    assert ci_method_for_cohort("MIMIC-III temporal sensitivity") == "stratified bootstrap"
    assert ci_method_for_cohort("F3 exploratory geographic cohort") == "stratified bootstrap"
    assert ci_method_for_cohort("NH exploratory geographic cohort") == "stratified bootstrap"


def test_stratified_bootstrap_ci_is_deterministic() -> None:
    y = np.array([0] * 20 + [1] * 10)
    score = np.linspace(0.05, 0.95, len(y))
    first = auroc_ci_for_cohort(y, score, "MIMIC-III temporal sensitivity", n_bootstrap=200)
    second = auroc_ci_for_cohort(y, score, "MIMIC-III temporal sensitivity", n_bootstrap=200)
    assert first == second
    assert first[3] == "stratified bootstrap"


def test_active_paths_use_canonical_cohort_specific_ci() -> None:
    train = read("scripts/train_models.py")
    figure4 = read("scripts/plot_figure4_benchmark.py")
    assert "auroc_ci_for_cohort" in train
    assert "auroc_ci_for_cohort" in figure4
    assert "auroc, lo, hi = delong_ci(y, prob)" not in figure4
    supplementary = read("scripts/r2_supplementary_analyses.py")
    assert "AUROC_CI_method" in supplementary
    assert "auroc_ci_for_cohort" in supplementary


def test_niv_is_encoded_before_knn_imputation() -> None:
    train = read("scripts/train_models.py")
    dictionary = read("docs/data_dictionary.md")
    assert "fillna(0)" in train
    assert "before KNN" in train
    assert "not passed to the KNN" in dictionary

#!/usr/bin/env python3
"""
Second-revision supplementary analyses for the hypoferremia ICU study.

The script is intentionally conservative:

* it distinguishes the LOS-filtered screening set (n=1,568) from patients who
  satisfy the fixed study definition of documented hypoferremia (iron <60
  micrograms/dL);
* it never writes patient identifiers, row-level outcomes, or predicted
  probabilities to public-facing output;
* it treats *_min, *_max, and *_mean variables as full-ICU-stay summaries,
  because the available Excel export has no measurement timestamps;
* it labels the multiple-imputation analysis as an out-of-fold sensitivity
  analysis rather than as a replacement external validation.

Required local input (not redistributed):
    data/mimic_dataset.xlsx

Outputs:
    result/r2_analysis/tables/*.csv
    result/r2_analysis/figures/figure2_within_hypoferremia_dose_response.*
    result/r2_analysis/analysis_summary.md
"""
from __future__ import annotations

import json
import math
import pickle
import shutil
import warnings
from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from patsy import build_design_matrices, dmatrix
from scipy import stats
from sklearn.calibration import calibration_curve
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.experimental import enable_iterative_imputer  # noqa: F401
from sklearn.impute import IterativeImputer, KNNImputer, SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, roc_auc_score
from sklearn.model_selection import StratifiedKFold
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from xgboost import XGBClassifier

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "mimic_dataset.xlsx"
RESULT = ROOT / "result" / "r2_analysis"
TABLES = RESULT / "tables"
FIGURES = RESULT / "figures"
PRIVATE = RESULT / "private"
REFERENCE_R2 = ROOT / "reference" / "r2"
LEGACY_RESULT = ROOT / "result" / "analysis"

RANDOM_STATE = 42
IRON_THRESHOLD = 60.0
LOS_MIN_DAYS = 2.0
N_IMPUTATIONS = 5
N_FOLDS = 5

LOCKED_FEATURES = [
    "mch_min",
    "ph_max",
    "mcv_1st",
    "bun_min",
    "pco2_max",
    "creatinine_min",
    "is_noninvasive_ventilator",
    "temperature_max",
    "spo2_min",
    "baseexcess_mean",
    "aniongap_max",
    "platelet_1st",
    "admission_age",
    "dbp_ni_max",
    "dbp_min",
    "wbc_min",
    "los_icu_to_t0",
    "mchc_min",
]

REDUCED_FEATURES = [
    "platelet_mean",
    "wbc_min",
    "bun_min",
    "pco2_max",
    "creatinine_min",
    "is_noninvasive_ventilator",
    "spo2_min",
    "platelet_1st",
]

ASSOCIATION_NUMERIC_COVARIATES = [
    "admission_age",
    "sofa_score",
    "charlson_comorbidity_index",
    "lactate_1st",
]

ASSOCIATION_BINARY_COVARIATES = [
    "female",
    "is_invasive_ventilator",
    "vasoactive",
]

ASSOCIATION_CATEGORICAL_COVARIATES = [
    "race_group",
    *ASSOCIATION_BINARY_COVARIATES,
]

ASSOCIATION_COVARIATES = [
    *ASSOCIATION_NUMERIC_COVARIATES,
    *ASSOCIATION_CATEGORICAL_COVARIATES,
]

RACE_LEVELS = ["White", "Black", "Asian", "Hispanic", "Other"]
SPLINE_QUANTILES = (0.05, 0.35, 0.65, 0.95)


@dataclass
class CalibrationResult:
    n: int
    events: int
    brier: float
    brier_lo: float
    brier_hi: float
    calibration_in_the_large: float
    citl_lo: float
    citl_hi: float
    slope: float
    slope_lo: float
    slope_hi: float


def _numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def _binary(series: pd.Series) -> pd.Series:
    return (_numeric(series) >= 0.5).astype(float).where(series.notna())


def _encode_gender(series: pd.Series) -> pd.Series:
    cleaned = series.astype(str).str.strip().str.upper()
    return cleaned.eq("F").astype(float).where(series.notna())


def _group_race(series: pd.Series) -> pd.Series:
    """Collapse free-text race into unordered analysis categories."""
    cleaned = series.astype(str).str.lower().str.strip()
    out = pd.Series("Other", index=series.index, dtype="object")
    for label in RACE_LEVELS[:-1]:
        out[cleaned.str.startswith(label.lower())] = label
    return out.where(series.notna())


def _outcome_28d_from_hospital_admission(df: pd.DataFrame) -> pd.Series:
    """
    Reproduce the available export's time origin honestly.

    hosp_survival_days is measured from hospital admission. The workbook lacks
    harmonized ICU-admission and iron-measurement timestamps, so this endpoint
    must not be called "28 days from t0".
    """
    expired = _numeric(df["hospital_expire_flag"]).fillna(0).astype(int)
    days = _numeric(df.get("hosp_survival_days", pd.Series(np.nan, index=df.index)))
    if not days.notna().any():
        days = _numeric(df.get("los_hospital", pd.Series(np.nan, index=df.index)))
    return ((expired == 1) & (days <= 28)).astype(int)


def _proxy_los_to_t0(df: pd.DataFrame) -> pd.Series:
    """
    Reproduce the locked proxy only for sensitivity-model comparability.

    This is not a real time-to-event variable. Admission-low-iron rows are
    assigned zero; the rare acquired-low-iron rows are assigned half the ICU
    stay, matching the legacy code.
    """
    iron_first = _numeric(df["iron_1st"])
    los = _numeric(df["los_icu"]).fillna(0)
    return pd.Series(
        np.where(iron_first < IRON_THRESHOLD, 0.0, los / 2.0),
        index=df.index,
    )


def load_mimic4() -> pd.DataFrame:
    if not DATA_PATH.is_file() or DATA_PATH.stat().st_size == 0:
        raise FileNotFoundError(
            f"Protected workbook not found: {DATA_PATH}. "
            "Place an authorized local copy there; do not commit it."
        )
    df = pd.read_excel(DATA_PATH, sheet_name="mimic4_low_fe")
    df["outcome_28d_hospital_admission"] = _outcome_28d_from_hospital_admission(df)
    df["los_icu_to_t0"] = _proxy_los_to_t0(df)
    df["female"] = _encode_gender(df["gender"])
    df["race_group"] = _group_race(df["race"])
    for col in ["is_invasive_ventilator", "is_noninvasive_ventilator", "vasoactive"]:
        if col in df:
            df[col] = _binary(df[col])
    # The protected workbook stores vasoactive treatment as 1 when documented
    # and leaves untreated/no-documented-use rows blank. The baseline table and
    # clinical interpretation use blank as 0, so apply that coding consistently.
    if "vasoactive" in df:
        df["vasoactive"] = df["vasoactive"].fillna(0.0)
    return df


def load_mimic3() -> pd.DataFrame:
    df = pd.read_excel(DATA_PATH, sheet_name="mimic3_low_fe")
    df["outcome_28d_hospital_admission"] = _outcome_28d_from_hospital_admission(df)
    df["los_icu_to_t0"] = _proxy_los_to_t0(df)
    for col in ["is_invasive_ventilator", "is_noninvasive_ventilator", "vasoactive"]:
        if col in df:
            df[col] = _binary(df[col])
    if "vasoactive" in df:
        df["vasoactive"] = df["vasoactive"].fillna(0.0)
    los = _numeric(df["los_icu"])
    iron_first = _numeric(df["iron_1st"])
    iron_min = _numeric(df["iron_min"])
    return df[
        (los >= LOS_MIN_DAYS)
        & ((iron_first < IRON_THRESHOLD) | (iron_min < IRON_THRESHOLD))
    ].copy()


def study_cohorts(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    los = _numeric(df["los_icu"])
    screened = df[los >= LOS_MIN_DAYS].copy()
    iron_first = _numeric(screened["iron_1st"])
    iron_min = _numeric(screened["iron_min"])
    eligible = screened[(iron_first < IRON_THRESHOLD) | (iron_min < IRON_THRESHOLD)].copy()
    complete = eligible.dropna(subset=LOCKED_FEATURES).copy()
    excluded_missing = eligible.loc[~eligible.index.isin(complete.index)].copy()
    threshold_ineligible = screened.loc[~screened.index.isin(eligible.index)].copy()
    return {
        "raw_sheet": df,
        "screened_los_ge_48h": screened,
        "eligible_documented_hypoferremia": eligible,
        "complete_case_locked_matrix": complete,
        "excluded_for_locked_matrix_missingness": excluded_missing,
        "not_hypoferremic_by_fixed_threshold": threshold_ineligible,
    }


def _flow_row(label: str, df: pd.DataFrame) -> dict:
    y28 = df["outcome_28d_hospital_admission"].astype(int)
    hosp = _numeric(df["hospital_expire_flag"]).fillna(0).astype(int)
    return {
        "Step": label,
        "n": len(df),
        "Hospital_deaths": int(hosp.sum()),
        "Hospital_mortality_pct": round(100 * hosp.mean(), 2) if len(df) else np.nan,
        "Deaths_within_28d_of_hospital_admission": int(y28.sum()),
        "28d_in_hospital_mortality_pct": round(100 * y28.mean(), 2) if len(df) else np.nan,
    }


def write_patient_flow(cohorts: dict[str, pd.DataFrame]) -> pd.DataFrame:
    order = [
        ("MIMIC-IV low-iron export before LOS filtering", "raw_sheet"),
        ("ICU length of stay >=48 h (screening set)", "screened_los_ge_48h"),
        (
            "Documented iron <60 micrograms/dL after LOS filtering",
            "eligible_documented_hypoferremia",
        ),
        ("Complete locked 18-predictor matrix", "complete_case_locked_matrix"),
        (
            "Eligible but excluded for locked-matrix missingness",
            "excluded_for_locked_matrix_missingness",
        ),
        (
            "LOS-eligible but not iron <60 by the fixed definition",
            "not_hypoferremic_by_fixed_threshold",
        ),
    ]
    out = pd.DataFrame([_flow_row(label, cohorts[key]) for label, key in order])
    out.to_csv(TABLES / "r2_patient_flow.csv", index=False)
    return out


def write_corrected_table1(eligible: pd.DataFrame) -> pd.DataFrame:
    """Rebuild Table 1 on the fixed-definition eligible MIMIC-IV cohort."""
    from build_table1_baseline import build_table1

    frame = eligible.copy()
    frame["outcome_28d_admission"] = frame["outcome_28d_hospital_admission"].astype(int)
    out = build_table1(frame)
    out.to_csv(TABLES / "r2_table1_mimic4_eligible.csv", index=False)
    return out


def _smd_continuous(a: pd.Series, b: pd.Series) -> float:
    a = _numeric(a).dropna()
    b = _numeric(b).dropna()
    if len(a) < 2 or len(b) < 2:
        return np.nan
    pooled = math.sqrt((a.var(ddof=1) + b.var(ddof=1)) / 2)
    return float((a.mean() - b.mean()) / pooled) if pooled > 0 else 0.0


def _smd_binary(a: pd.Series, b: pd.Series) -> float:
    a = _numeric(a).dropna()
    b = _numeric(b).dropna()
    if len(a) == 0 or len(b) == 0:
        return np.nan
    pa, pb = a.mean(), b.mean()
    pooled = math.sqrt((pa * (1 - pa) + pb * (1 - pb)) / 2)
    return float((pa - pb) / pooled) if pooled > 0 else 0.0


def _fmt_continuous(s: pd.Series) -> str:
    x = _numeric(s).dropna()
    return f"{x.median():.2f} [{x.quantile(.25):.2f}, {x.quantile(.75):.2f}]"


def _fmt_binary(s: pd.Series) -> str:
    x = _numeric(s).dropna()
    return f"{int(x.sum())}/{len(x)} ({100*x.mean():.1f}%)"


def write_selection_comparison(
    included: pd.DataFrame, excluded: pd.DataFrame
) -> pd.DataFrame:
    variables = [
        ("Admission age, years", "admission_age", "continuous"),
        ("Female sex", "female", "binary"),
        ("SOFA score", "sofa_score", "continuous"),
        ("Charlson comorbidity index", "charlson_comorbidity_index", "continuous"),
        ("First serum iron, micrograms/dL", "iron_1st", "continuous"),
        ("First lactate, mmol/L", "lactate_1st", "continuous"),
        ("Invasive ventilation documented", "is_invasive_ventilator", "binary"),
        ("Vasoactive therapy documented", "vasoactive", "binary"),
        ("ICU length of stay, days", "los_icu", "continuous"),
        ("28-day in-hospital death from hospital admission", "outcome_28d_hospital_admission", "binary"),
        ("In-hospital death", "hospital_expire_flag", "binary"),
    ]
    rows = []
    for label, col, kind in variables:
        if col not in included or col not in excluded:
            continue
        if kind == "continuous":
            ai, ae = _numeric(included[col]).dropna(), _numeric(excluded[col]).dropna()
            _, p = stats.mannwhitneyu(ai, ae, alternative="two-sided") if len(ai) and len(ae) else (np.nan, np.nan)
            rows.append(
                {
                    "Characteristic": label,
                    "Included_complete_case": _fmt_continuous(included[col]),
                    "Excluded_for_missingness": _fmt_continuous(excluded[col]),
                    "Absolute_SMD": abs(_smd_continuous(included[col], excluded[col])),
                    "P_value": p,
                }
            )
        else:
            ai = _numeric(included[col]).dropna()
            ae = _numeric(excluded[col]).dropna()
            table = np.array(
                [
                    [int(ai.sum()), int(len(ai) - ai.sum())],
                    [int(ae.sum()), int(len(ae) - ae.sum())],
                ]
            )
            _, p, _, _ = stats.chi2_contingency(table, correction=False) if table.sum() else (np.nan, np.nan, None, None)
            rows.append(
                {
                    "Characteristic": label,
                    "Included_complete_case": _fmt_binary(included[col]),
                    "Excluded_for_missingness": _fmt_binary(excluded[col]),
                    "Absolute_SMD": abs(_smd_binary(included[col], excluded[col])),
                    "P_value": p,
                }
            )
    out = pd.DataFrame(rows)
    out.to_csv(TABLES / "r2_included_vs_excluded.csv", index=False)
    return out


def write_locked_matrix_missingness(eligible: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for feature in LOCKED_FEATURES:
        missing = int(eligible[feature].isna().sum())
        rows.append(
            {
                "Variable": feature,
                "n": len(eligible),
                "Missing_n": missing,
                "Missing_pct": 100 * missing / len(eligible),
                "Observation_window": (
                    "Synthetic legacy proxy; no real timestamp"
                    if feature == "los_icu_to_t0"
                    else "Full ICU stay aggregate"
                    if feature.endswith(("_min", "_max", "_mean"))
                    else "First recorded value during ICU stay"
                    if feature.endswith("_1st")
                    else "Full-stay/documentation-derived or baseline"
                ),
            }
        )
    out = pd.DataFrame(rows)
    out.to_csv(TABLES / "r2_locked_matrix_missingness_and_windows.csv", index=False)
    return out


def _build_soft_voting(seed: int) -> VotingClassifier:
    return VotingClassifier(
        estimators=[
            (
                "lr",
                LogisticRegression(
                    max_iter=2000,
                    random_state=seed,
                    class_weight="balanced",
                ),
            ),
            (
                "rf",
                RandomForestClassifier(
                    n_estimators=200,
                    max_depth=6,
                    random_state=seed,
                    class_weight="balanced",
                    n_jobs=-1,
                ),
            ),
            (
                "xgb",
                XGBClassifier(
                    n_estimators=120,
                    max_depth=4,
                    learning_rate=0.08,
                    random_state=seed,
                    eval_metric="logloss",
                    n_jobs=2,
                ),
            ),
        ],
        voting="soft",
    )


def _fit_calibration(y: np.ndarray, prob: np.ndarray) -> CalibrationResult:
    y = np.asarray(y, dtype=int)
    prob = np.clip(np.asarray(prob, dtype=float), 1e-6, 1 - 1e-6)
    lp = np.log(prob / (1 - prob))

    slope_model = sm.GLM(
        y,
        sm.add_constant(lp),
        family=sm.families.Binomial(),
    ).fit()
    slope_ci = slope_model.conf_int()

    citl_model = sm.GLM(
        y,
        np.ones((len(y), 1)),
        family=sm.families.Binomial(),
        offset=lp,
    ).fit()
    citl_ci = citl_model.conf_int()

    rng = np.random.default_rng(RANDOM_STATE)
    boot = []
    for _ in range(1000):
        idx = rng.integers(0, len(y), len(y))
        if np.unique(y[idx]).size < 2:
            continue
        boot.append(brier_score_loss(y[idx], prob[idx]))
    blo, bhi = np.percentile(boot, [2.5, 97.5])
    return CalibrationResult(
        n=len(y),
        events=int(y.sum()),
        brier=brier_score_loss(y, prob),
        brier_lo=float(blo),
        brier_hi=float(bhi),
        calibration_in_the_large=float(citl_model.params[0]),
        citl_lo=float(citl_ci[0, 0]),
        citl_hi=float(citl_ci[0, 1]),
        slope=float(slope_model.params[1]),
        slope_lo=float(slope_ci[1, 0]),
        slope_hi=float(slope_ci[1, 1]),
    )


def _metric_row(analysis: str, cohort: str, y: np.ndarray, prob: np.ndarray) -> dict:
    cal = _fit_calibration(y, prob)
    return {
        "Analysis": analysis,
        "Cohort": cohort,
        "n": cal.n,
        "Events": cal.events,
        "AUROC": roc_auc_score(y, prob),
        "Brier": cal.brier,
        "Brier_95CI_lo": cal.brier_lo,
        "Brier_95CI_hi": cal.brier_hi,
        "Calibration_in_the_large": cal.calibration_in_the_large,
        "CITL_95CI_lo": cal.citl_lo,
        "CITL_95CI_hi": cal.citl_hi,
        "Calibration_slope": cal.slope,
        "Slope_95CI_lo": cal.slope_lo,
        "Slope_95CI_hi": cal.slope_hi,
    }


def _load_prediction_pickle(path: Path, preferred_model: str = "Ensemble_Voting") -> tuple[np.ndarray, np.ndarray]:
    with path.open("rb") as handle:
        obj = pickle.load(handle)
    candidates = obj if isinstance(obj, list) else [obj]
    selected = None
    for item in candidates:
        if not isinstance(item, dict):
            continue
        if item.get("model_name") == preferred_model:
            selected = item
            break
        if selected is None and ("pred_prob" in item and ("lable" in item or "label" in item)):
            selected = item
    if selected is None:
        raise ValueError(f"No probability/label record found in {path}")
    label_key = "lable" if "lable" in selected else "label"
    return np.asarray(selected[label_key], dtype=int), np.asarray(selected["pred_prob"], dtype=float)


def write_locked_calibration(
    corrected_mimic3: pd.DataFrame,
) -> pd.DataFrame:
    sources = [
        (
            "Locked 18-predictor soft-voting model",
            "MIMIC-IV internal test",
            LEGACY_RESULT / "preds" / "20_features_test_preds.pkl",
        ),
        (
            "Reduced 8-feature soft-voting model",
            "MIMIC-IV internal test",
            LEGACY_RESULT / "preds" / "8_features_test_preds.pkl",
        ),
        (
            "Reduced 8-feature soft-voting model",
            "F3 exploratory geographic cohort",
            LEGACY_RESULT / "preds" / "8_features_F3_preds.pkl",
        ),
        (
            "Reduced 8-feature soft-voting model",
            "NH exploratory geographic cohort",
            LEGACY_RESULT / "preds" / "8_features_NH_preds.pkl",
        ),
    ]
    rows = []
    for analysis, cohort, path in sources:
        if not path.is_file():
            continue
        y, prob = _load_prediction_pickle(path)
        rows.append(_metric_row(analysis, cohort, y, prob))
    rows.extend(corrected_mimic3.to_dict(orient="records"))
    out = pd.DataFrame(rows)
    out.to_csv(TABLES / "r2_standard_calibration_metrics.csv", index=False)
    return out


def write_corrected_mimic3_evaluation(mimic3: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for tag, label in [
        ("20_features", "Locked 18-predictor soft-voting model"),
        ("8_features", "Reduced 8-feature soft-voting model"),
    ]:
        bundle_path = LEGACY_RESULT / "model_weight" / tag / "model_weight.pkl"
        if not bundle_path.is_file():
            continue
        with bundle_path.open("rb") as handle:
            bundle = pickle.load(handle)
        features = bundle["features"]
        X = mimic3[features].apply(pd.to_numeric, errors="coerce")
        if "is_noninvasive_ventilator" in X:
            # Exact legacy coding: undocumented NIV was treated as zero.
            X["is_noninvasive_ventilator"] = (
                X["is_noninvasive_ventilator"].fillna(0).ge(0.5).astype(int)
            )
        X_imputed = pd.DataFrame(
            bundle["imputer"].transform(X),
            columns=features,
        )
        X_scaled = bundle["scaler"].transform(X_imputed)
        prob = bundle["Ensemble_Voting"].predict_proba(X_scaled)[:, 1]
        y = mimic3["outcome_28d_hospital_admission"].astype(int).to_numpy()
        rows.append(
            _metric_row(
                label,
                "MIMIC-III corrected eligibility set (ICU LOS >=48 h)",
                y,
                prob,
            )
        )
    out = pd.DataFrame(rows)
    out.to_csv(TABLES / "r2_corrected_mimic3_evaluation.csv", index=False)
    pd.DataFrame(
        [
            {
                "Cohort": "MIMIC-III corrected eligibility set",
                "n": len(mimic3),
                "Events_28d_in_hospital_from_hospital_admission": int(
                    mimic3["outcome_28d_hospital_admission"].sum()
                ),
                "In_hospital_deaths": int(
                    _numeric(mimic3["hospital_expire_flag"]).fillna(0).sum()
                ),
                "NIV_missing_n": int(
                    mimic3["is_noninvasive_ventilator"].isna().sum()
                ),
                "NIV_missing_pct": 100
                * mimic3["is_noninvasive_ventilator"].isna().mean(),
            }
        ]
    ).to_csv(TABLES / "r2_corrected_mimic3_flow_and_niv_missingness.csv", index=False)
    return out


def multiple_imputation_oof(eligible: pd.DataFrame) -> tuple[pd.DataFrame, np.ndarray]:
    """
    Five-imputation, five-fold out-of-fold sensitivity in all eligible patients.

    Imputation and scaling are fitted inside each training fold. Probabilities
    are averaged across imputations for each held-out patient.
    """
    X = eligible[LOCKED_FEATURES].apply(pd.to_numeric, errors="coerce")
    y = eligible["outcome_28d_hospital_admission"].astype(int).to_numpy()
    cv = StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=RANDOM_STATE)
    predictions = np.zeros((N_IMPUTATIONS, len(eligible)), dtype=float)

    for fold, (train_idx, test_idx) in enumerate(cv.split(X, y), start=1):
        X_train = X.iloc[train_idx]
        X_test = X.iloc[test_idx]
        y_train = y[train_idx]
        for imp_no in range(N_IMPUTATIONS):
            seed = RANDOM_STATE + 100 * fold + imp_no
            imputer = IterativeImputer(
                max_iter=10,
                sample_posterior=True,
                random_state=seed,
                skip_complete=True,
            )
            X_train_i = imputer.fit_transform(X_train)
            X_test_i = imputer.transform(X_test)
            scaler = StandardScaler()
            X_train_s = scaler.fit_transform(X_train_i)
            X_test_s = scaler.transform(X_test_i)
            model = _build_soft_voting(seed)
            model.fit(X_train_s, y_train)
            predictions[imp_no, test_idx] = model.predict_proba(X_test_s)[:, 1]
        print(f"MI sensitivity: completed fold {fold}/{N_FOLDS}", flush=True)

    pooled = predictions.mean(axis=0)
    rows = [
        _metric_row(
            "Five-imputation, five-fold out-of-fold sensitivity",
            "MIMIC-IV all eligible documented-hypoferremia patients",
            y,
            pooled,
        )
    ]
    per_imputation = []
    for imp_no in range(N_IMPUTATIONS):
        per_imputation.append(
            {
                "Imputation": imp_no + 1,
                "n": len(y),
                "Events": int(y.sum()),
                "AUROC": roc_auc_score(y, predictions[imp_no]),
                "Brier": brier_score_loss(y, predictions[imp_no]),
            }
        )
    pd.DataFrame(per_imputation).to_csv(
        TABLES / "r2_multiple_imputation_per_imputation.csv", index=False
    )
    out = pd.DataFrame(rows)
    out.to_csv(TABLES / "r2_multiple_imputation_sensitivity.csv", index=False)

    # Private local artifact for audit only; result/ is git-ignored.
    PRIVATE.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        PRIVATE / "r2_mi_oof_predictions_private.npz",
        y=y,
        pooled_probability=pooled,
        imputation_probabilities=predictions,
    )
    return out, pooled


def _load_locked_splits(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    id_col = "subject_id"
    train_ids = pd.read_csv(LEGACY_RESULT / "cohorts" / "mimic4_train_ids.csv")
    test_ids = pd.read_csv(LEGACY_RESULT / "cohorts" / "mimic4_test_ids.csv")
    train = df.merge(train_ids[[id_col]], on=id_col, how="inner")
    test = df.merge(test_ids[[id_col]], on=id_col, how="inner")
    return train, test


def _fit_locked_split_sensitivity(
    train: pd.DataFrame,
    evaluation: pd.DataFrame,
    features: list[str],
    label: str,
    cohort_label: str,
) -> dict:
    X_train = train[features].apply(pd.to_numeric, errors="coerce")
    X_test = evaluation[features].apply(pd.to_numeric, errors="coerce")
    y_train = train["outcome_28d_hospital_admission"].astype(int).to_numpy()
    y_test = evaluation["outcome_28d_hospital_admission"].astype(int).to_numpy()
    imputer = KNNImputer(n_neighbors=5)
    X_train_i = imputer.fit_transform(X_train)
    X_test_i = imputer.transform(X_test)
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train_i)
    X_test_s = scaler.transform(X_test_i)
    model = _build_soft_voting(RANDOM_STATE)
    model.fit(X_train_s, y_train)
    prob = model.predict_proba(X_test_s)[:, 1]
    return _metric_row(label, cohort_label, y_test, prob)


def write_niv_exclusion_sensitivity(
    eligible: pd.DataFrame,
    mimic3: pd.DataFrame,
) -> pd.DataFrame:
    train, test = _load_locked_splits(eligible)
    rows = []
    for features, label in [
        (
            [f for f in LOCKED_FEATURES if f != "is_noninvasive_ventilator"],
            "17-predictor benchmark excluding NIV documentation variable",
        ),
        (
            [f for f in REDUCED_FEATURES if f != "is_noninvasive_ventilator"],
            "7-feature reduced model excluding NIV documentation variable",
        ),
    ]:
        rows.append(
            _fit_locked_split_sensitivity(
                train,
                test,
                features,
                label,
                "MIMIC-IV locked internal test",
            )
        )
        rows.append(
            _fit_locked_split_sensitivity(
                train,
                mimic3,
                features,
                label,
                "MIMIC-III corrected eligibility set (ICU LOS >=48 h)",
            )
        )
    out = pd.DataFrame(rows)
    out.to_csv(TABLES / "r2_niv_exclusion_sensitivity.csv", index=False)
    return out


def _association_frame(eligible: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "iron_1st",
        "outcome_28d_hospital_admission",
        *ASSOCIATION_COVARIATES,
    ]
    frame = eligible[cols].copy()
    frame["iron_1st"] = _numeric(frame["iron_1st"])
    frame["iron_per_10"] = _numeric(frame["iron_1st"]) / 10.0
    for column in [
        *ASSOCIATION_NUMERIC_COVARIATES,
        *ASSOCIATION_BINARY_COVARIATES,
    ]:
        frame[column] = _numeric(frame[column])
    frame["race_group"] = frame["race_group"].where(
        frame["race_group"].isin(RACE_LEVELS)
    )
    frame["outcome_28d_hospital_admission"] = frame[
        "outcome_28d_hospital_admission"
    ].astype(int)
    return frame.reset_index(drop=True)


def _prepare_association_glm_data(
    frame: pd.DataFrame,
    *,
    complete_case: bool,
) -> pd.DataFrame:
    """
    Prepare an explanatory GLM dataset.

    The primary model uses simple prespecified imputation (numeric median;
    categorical mode). A separate complete-case fit quantifies sensitivity to
    this choice. Predictive cross-validation below does not use this dataset:
    its preprocessing is fitted independently inside each training fold.
    """
    required = [
        "iron_1st",
        "iron_per_10",
        "outcome_28d_hospital_admission",
        *ASSOCIATION_COVARIATES,
    ]
    prepared = frame[required].copy()
    if complete_case:
        prepared = prepared.dropna(subset=required).copy()
    else:
        for column in [
            "iron_1st",
            "iron_per_10",
            *ASSOCIATION_NUMERIC_COVARIATES,
        ]:
            prepared[column] = prepared[column].fillna(prepared[column].median())
        for column in ASSOCIATION_CATEGORICAL_COVARIATES:
            mode = prepared[column].mode(dropna=True)
            fill_value = mode.iloc[0] if not mode.empty else (
                "White" if column == "race_group" else 0.0
            )
            prepared[column] = prepared[column].fillna(fill_value)

    prepared["race_group"] = pd.Categorical(
        prepared["race_group"],
        categories=RACE_LEVELS,
        ordered=False,
    )
    for column in ASSOCIATION_BINARY_COVARIATES:
        prepared[column] = _numeric(prepared[column])
    return prepared.reset_index(drop=True)


def _clinical_covariate_design(frame: pd.DataFrame) -> pd.DataFrame:
    numeric = frame[ASSOCIATION_NUMERIC_COVARIATES].astype(float).reset_index(
        drop=True
    )
    binary = frame[ASSOCIATION_BINARY_COVARIATES].astype(float).reset_index(
        drop=True
    )
    race = pd.get_dummies(
        pd.Categorical(
            frame["race_group"],
            categories=RACE_LEVELS,
            ordered=False,
        ),
        prefix="race",
        drop_first=True,
        dtype=float,
    )
    race.index = numeric.index
    return pd.concat([numeric, binary, race], axis=1)


def _or_row(
    name: str,
    model,
    parameter: str,
    *,
    n: int,
    events: int,
) -> dict:
    beta = float(model.params[parameter])
    ci = model.conf_int().loc[parameter]
    return {
        "Analysis": name,
        "n": n,
        "Events": events,
        "Adjusted_OR": math.exp(beta),
        "OR_95CI_lo": math.exp(float(ci.iloc[0])),
        "OR_95CI_hi": math.exp(float(ci.iloc[1])),
        "P_value": float(model.pvalues[parameter]),
    }


def _incremental_model_pipeline(*, include_iron: bool) -> tuple[Pipeline, list[str]]:
    numeric_features = [
        *ASSOCIATION_NUMERIC_COVARIATES,
        *(["iron_1st"] if include_iron else []),
    ]
    categorical_features = ASSOCIATION_CATEGORICAL_COVARIATES
    preprocessing = ColumnTransformer(
        transformers=[
            (
                "numeric",
                Pipeline(
                    [
                        ("impute", SimpleImputer(strategy="median")),
                        ("scale", StandardScaler()),
                    ]
                ),
                numeric_features,
            ),
            (
                "categorical",
                Pipeline(
                    [
                        ("impute", SimpleImputer(strategy="most_frequent")),
                        (
                            "one_hot",
                            OneHotEncoder(
                                handle_unknown="ignore",
                                drop="first",
                                sparse_output=False,
                            ),
                        ),
                    ]
                ),
                categorical_features,
            ),
        ],
        remainder="drop",
    )
    model = Pipeline(
        [
            ("preprocess", preprocessing),
            (
                "model",
                LogisticRegression(
                    max_iter=2000,
                    class_weight=None,
                    random_state=RANDOM_STATE,
                ),
            ),
        ]
    )
    return model, [*numeric_features, *categorical_features]


def association_and_incremental_value(
    eligible: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    raw_frame = _association_frame(eligible)
    frame = _prepare_association_glm_data(raw_frame, complete_case=False)
    complete_frame = _prepare_association_glm_data(raw_frame, complete_case=True)
    y = frame["outcome_28d_hospital_admission"].astype(int).to_numpy()
    y_complete = complete_frame["outcome_28d_hospital_admission"].astype(int).to_numpy()

    unadjusted = sm.GLM(
        y,
        sm.add_constant(frame[["iron_per_10"]]),
        family=sm.families.Binomial(),
    ).fit()
    covariate_design = _clinical_covariate_design(frame)
    linear_design = pd.concat(
        [
            pd.Series(1.0, index=frame.index, name="const"),
            frame[["iron_per_10"]].reset_index(drop=True),
            covariate_design,
        ],
        axis=1,
    )
    adjusted = sm.GLM(
        y,
        linear_design,
        family=sm.families.Binomial(),
    ).fit()

    complete_covariate_design = _clinical_covariate_design(complete_frame)
    complete_linear_design = pd.concat(
        [
            pd.Series(1.0, index=complete_frame.index, name="const"),
            complete_frame[["iron_per_10"]].reset_index(drop=True),
            complete_covariate_design,
        ],
        axis=1,
    )
    complete_adjusted = sm.GLM(
        y_complete,
        complete_linear_design,
        family=sm.families.Binomial(),
    ).fit()

    # Four-knot restricted cubic spline: the 5th and 95th percentiles are
    # boundary knots; the 35th and 65th percentiles are interior knots.
    knot_values = frame["iron_1st"].quantile(SPLINE_QUANTILES).to_numpy(dtype=float)
    lower_knot, interior_knot_1, interior_knot_2, upper_knot = knot_values
    spline_formula = (
        "cr(iron_1st, "
        f"knots=({interior_knot_1:.17g}, {interior_knot_2:.17g}), "
        f"lower_bound={lower_knot:.17g}, upper_bound={upper_knot:.17g}, "
        "constraints='center') - 1"
    )
    spline_matrix = dmatrix(
        spline_formula,
        frame,
        return_type="dataframe",
    )
    spline_design_info = spline_matrix.design_info
    spline_design = pd.concat(
        [
            pd.Series(1.0, index=frame.index, name="const"),
            spline_matrix.reset_index(drop=True),
            covariate_design,
        ],
        axis=1,
    )
    spline_model = sm.GLM(y, spline_design, family=sm.families.Binomial()).fit()
    lr_stat = 2 * (spline_model.llf - adjusted.llf)
    lr_df = max(1, int(spline_model.df_model - adjusted.df_model))
    nonlinearity_p = stats.chi2.sf(lr_stat, lr_df)

    effect_rows = [
        _or_row(
            "Unadjusted first serum iron, per 10 micrograms/dL",
            unadjusted,
            "iron_per_10",
            n=len(frame),
            events=int(y.sum()),
        ),
        _or_row(
            "Adjusted first serum iron, per 10 micrograms/dL",
            adjusted,
            "iron_per_10",
            n=len(frame),
            events=int(y.sum()),
        ),
        _or_row(
            "Adjusted first serum iron, complete-case sensitivity",
            complete_adjusted,
            "iron_per_10",
            n=len(complete_frame),
            events=int(y_complete.sum()),
        ),
        {
            "Analysis": "Four-knot restricted cubic spline likelihood-ratio test for nonlinearity",
            "n": len(frame),
            "Events": int(y.sum()),
            "Adjusted_OR": np.nan,
            "OR_95CI_lo": np.nan,
            "OR_95CI_hi": np.nan,
            "P_value": nonlinearity_p,
        },
    ]
    effects = pd.DataFrame(effect_rows)
    for percentile, value in zip(("P05", "P35", "P65", "P95"), knot_values):
        effects[f"Spline_knot_{percentile}"] = value
    effects.to_csv(TABLES / "r2_iron_adjusted_effect.csv", index=False)

    predictive_frame = raw_frame.reset_index(drop=True)
    predictive_y = predictive_frame["outcome_28d_hospital_admission"].astype(int).to_numpy()
    cv = StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=RANDOM_STATE)
    oof_base = np.zeros(len(predictive_frame))
    oof_iron = np.zeros(len(predictive_frame))
    for train_idx, test_idx in cv.split(predictive_frame, predictive_y):
        for include_iron, target in [(False, oof_base), (True, oof_iron)]:
            pipe, features = _incremental_model_pipeline(include_iron=include_iron)
            pipe.fit(
                predictive_frame.iloc[train_idx][features],
                predictive_y[train_idx],
            )
            target[test_idx] = pipe.predict_proba(
                predictive_frame.iloc[test_idx][features]
            )[:, 1]

    rng = np.random.default_rng(RANDOM_STATE)
    delta_auc = []
    delta_brier = []
    for _ in range(2000):
        idx = rng.integers(0, len(predictive_y), len(predictive_y))
        if np.unique(predictive_y[idx]).size < 2:
            continue
        delta_auc.append(
            roc_auc_score(predictive_y[idx], oof_iron[idx])
            - roc_auc_score(predictive_y[idx], oof_base[idx])
        )
        delta_brier.append(
            brier_score_loss(predictive_y[idx], oof_iron[idx])
            - brier_score_loss(predictive_y[idx], oof_base[idx])
        )
    incremental = pd.DataFrame(
        [
            {
                "Model": "Clinical covariates only",
                "n": len(predictive_y),
                "Events": int(predictive_y.sum()),
                "OOF_AUROC": roc_auc_score(predictive_y, oof_base),
                "OOF_Brier": brier_score_loss(predictive_y, oof_base),
                "Delta_AUROC_vs_clinical": 0.0,
                "Delta_AUROC_95CI_lo": 0.0,
                "Delta_AUROC_95CI_hi": 0.0,
                "Delta_Brier_vs_clinical": 0.0,
                "Delta_Brier_95CI_lo": 0.0,
                "Delta_Brier_95CI_hi": 0.0,
            },
            {
                "Model": "Clinical covariates plus first serum iron",
                "n": len(predictive_y),
                "Events": int(predictive_y.sum()),
                "OOF_AUROC": roc_auc_score(predictive_y, oof_iron),
                "OOF_Brier": brier_score_loss(predictive_y, oof_iron),
                "Delta_AUROC_vs_clinical": roc_auc_score(predictive_y, oof_iron)
                - roc_auc_score(predictive_y, oof_base),
                "Delta_AUROC_95CI_lo": np.percentile(delta_auc, 2.5),
                "Delta_AUROC_95CI_hi": np.percentile(delta_auc, 97.5),
                "Delta_Brier_vs_clinical": brier_score_loss(predictive_y, oof_iron)
                - brier_score_loss(predictive_y, oof_base),
                "Delta_Brier_95CI_lo": np.percentile(delta_brier, 2.5),
                "Delta_Brier_95CI_hi": np.percentile(delta_brier, 97.5),
            },
        ]
    )
    incremental.to_csv(TABLES / "r2_iron_incremental_value.csv", index=False)

    _plot_dose_response(
        frame,
        spline_model,
        spline_design_info,
        covariate_columns=list(covariate_design.columns),
    )
    return effects, incremental


def _plot_dose_response(
    frame: pd.DataFrame,
    model,
    spline_design_info,
    *,
    covariate_columns: list[str],
) -> None:
    grid = np.linspace(
        frame["iron_1st"].quantile(0.01),
        frame["iron_1st"].quantile(0.99),
        160,
    )
    reference = float(frame["iron_1st"].median())
    fixed = {
        column: float(frame[column].median())
        for column in ASSOCIATION_NUMERIC_COVARIATES
    }
    for column in ASSOCIATION_BINARY_COVARIATES:
        fixed[column] = float(frame[column].mode(dropna=True).iloc[0])
    fixed["race_group"] = "White"

    def design_for(values: np.ndarray) -> pd.DataFrame:
        new = pd.DataFrame({"iron_1st": values})
        spline_new_matrix = build_design_matrices([spline_design_info], new)[0]
        spline_new = pd.DataFrame(
            np.asarray(spline_new_matrix),
            columns=spline_design_info.column_names,
        )
        covariate_frame = pd.DataFrame(
            {column: np.repeat(value, len(new)) for column, value in fixed.items()}
        )
        covariate_new = _clinical_covariate_design(covariate_frame).reindex(
            columns=covariate_columns,
            fill_value=0.0,
        )
        return pd.concat(
            [
                pd.Series(1.0, index=range(len(new)), name="const"),
                spline_new.reset_index(drop=True),
                covariate_new.reset_index(drop=True),
            ],
            axis=1,
        )[model.params.index]

    design_grid = design_for(grid)
    design_ref = design_for(np.array([reference])).iloc[0].to_numpy()
    contrasts = design_grid.to_numpy() - design_ref
    beta = model.params.to_numpy()
    cov = model.cov_params().to_numpy()
    log_or = contrasts @ beta
    se = np.sqrt(np.einsum("ij,jk,ik->i", contrasts, cov, contrasts))
    odds_ratio = np.exp(log_or)
    lo = np.exp(log_or - 1.96 * se)
    hi = np.exp(log_or + 1.96 * se)

    fig, (ax, hist_ax) = plt.subplots(
        2,
        1,
        figsize=(7.2, 6.2),
        sharex=True,
        gridspec_kw={"height_ratios": [4, 1], "hspace": 0.06},
    )
    ax.plot(grid, odds_ratio, color="#1f5a94", linewidth=2.2)
    ax.fill_between(grid, lo, hi, color="#80b1d3", alpha=0.35, linewidth=0)
    ax.axhline(1, color="#555555", linestyle="--", linewidth=1)
    ax.axvline(reference, color="#777777", linestyle=":", linewidth=1)
    ax.set_ylabel("Adjusted odds ratio (95% CI)")
    ax.set_title(
        "First recorded serum iron and 28-day in-hospital mortality\n"
        "among patients meeting the documented-hypoferremia definition"
    )
    ax.grid(axis="y", color="#e6e6e6", linewidth=0.8)
    ax.spines[["top", "right"]].set_visible(False)

    hist_ax.hist(
        frame["iron_1st"],
        bins=np.arange(5, 72, 3),
        color="#b9c7d5",
        edgecolor="white",
    )
    hist_ax.set_xlabel("First recorded serum iron (micrograms/dL)")
    hist_ax.set_ylabel("n")
    hist_ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIGURES / "figure2_within_hypoferremia_dose_response.png", dpi=300)
    fig.savefig(FIGURES / "figure2_within_hypoferremia_dose_response.svg")
    plt.close(fig)


def write_analysis_summary(
    flow: pd.DataFrame,
    selection: pd.DataFrame,
    calibration: pd.DataFrame,
    corrected_mimic3: pd.DataFrame,
    mi: pd.DataFrame,
    niv: pd.DataFrame,
    effects: pd.DataFrame,
    incremental: pd.DataFrame,
) -> None:
    flow_lookup = flow.set_index("Step")
    eligible = flow_lookup.loc[
        "Documented iron <60 micrograms/dL after LOS filtering"
    ]
    complete = flow_lookup.loc["Complete locked 18-predictor matrix"]
    excluded = flow_lookup.loc[
        "Eligible but excluded for locked-matrix missingness"
    ]
    mi_row = mi.iloc[0]
    effect = effects.iloc[1]
    inc = incremental.iloc[1]
    corrected_primary = corrected_mimic3[
        corrected_mimic3["Analysis"].str.contains("18-predictor")
    ].iloc[0]

    lines = [
        "# R2 supplementary analysis summary",
        "",
        "## Cohort accounting",
        "",
        (
            f"The LOS-filtered screening set contained 1,568 records, but only "
            f"{int(eligible['n']):,} satisfied the fixed iron <60 micrograms/dL "
            f"definition. The locked complete-case matrix contained "
            f"{int(complete['n']):,} patients; {int(excluded['n']):,} eligible "
            "patients were excluded because at least one locked predictor was missing."
        ),
        (
            f"Among eligible patients, 28-day in-hospital mortality from hospital "
            f"admission was {int(complete['Deaths_within_28d_of_hospital_admission'])}/"
            f"{int(complete['n'])} in complete cases and "
            f"{int(excluded['Deaths_within_28d_of_hospital_admission'])}/"
            f"{int(excluded['n'])} among missingness exclusions."
        ),
        "",
        "## Multiple-imputation sensitivity",
        "",
        (
            f"Five-imputation, five-fold out-of-fold AUROC was "
            f"{mi_row['AUROC']:.3f}; Brier score was {mi_row['Brier']:.3f}, "
            f"calibration-in-the-large {mi_row['Calibration_in_the_large']:.3f}, "
            f"and calibration slope {mi_row['Calibration_slope']:.3f}."
        ),
        "",
        "## Corrected MIMIC-III eligibility analysis",
        "",
        (
            f"Applying the stated ICU-LOS >=48-hour criterion yielded a MIMIC-III "
            f"temporal sensitivity cohort of {int(corrected_primary['n'])} patients. The "
            f"locked 18-predictor model AUROC was {corrected_primary['AUROC']:.3f}, "
            f"Brier score {corrected_primary['Brier']:.3f}, calibration-in-the-large "
            f"{corrected_primary['Calibration_in_the_large']:.3f}, and calibration "
            f"slope {corrected_primary['Calibration_slope']:.3f}."
        ),
        "",
        "## Serum iron association and incremental value",
        "",
        (
            f"Within the eligible documented-hypoferremia cohort, the adjusted odds "
            f"ratio per 10-micrograms/dL increase in first serum iron was "
            f"{effect['Adjusted_OR']:.3f} (95% CI {effect['OR_95CI_lo']:.3f}-"
            f"{effect['OR_95CI_hi']:.3f}; P={effect['P_value']:.4g})."
        ),
        (
            f"Adding first serum iron to the prespecified clinical covariate model "
            f"changed out-of-fold AUROC by {inc['Delta_AUROC_vs_clinical']:.3f} "
            f"(95% CI {inc['Delta_AUROC_95CI_lo']:.3f} to "
            f"{inc['Delta_AUROC_95CI_hi']:.3f})."
        ),
        "",
        "## Interpretation limits",
        "",
        "- The available workbook does not contain a valid normal-iron comparator from the full MIMIC-IV screening population.",
        "- The available workbook does not contain charttime-level predictor measurements.",
        "- `_min`, `_max`, and `_mean` are full-ICU-stay summaries; the legacy `t0` timing is synthetic and must not be presented as an observed timestamp.",
        "- The dose-response analysis is within a selected documented-hypoferremia cohort and is not an estimate of the causal effect of hypoferremia versus normal iron.",
        "- Public release should include code and non-patient-specific model objects, not the protected workbook or row-level outcomes/probabilities.",
        "",
        "## Generated tables",
        "",
    ]
    for path in sorted(TABLES.glob("*.csv")):
        lines.append(f"- `{path.relative_to(ROOT)}`")
    (RESULT / "analysis_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def publish_aggregate_reference_outputs() -> None:
    """Copy only non-patient-level aggregates and figures into tracked reference/."""
    REFERENCE_R2.mkdir(parents=True, exist_ok=True)
    for path in TABLES.glob("*.csv"):
        shutil.copy2(path, REFERENCE_R2 / path.name)
    for name in [
        "figure2_within_hypoferremia_dose_response.png",
        "figure2_within_hypoferremia_dose_response.svg",
    ]:
        shutil.copy2(FIGURES / name, REFERENCE_R2 / name)
    shutil.copy2(RESULT / "analysis_summary.md", REFERENCE_R2 / "README.md")
    shutil.copy2(
        RESULT / "r2_analysis_manifest.json",
        REFERENCE_R2 / "r2_analysis_manifest.json",
    )


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)
    df = load_mimic4()
    mimic3 = load_mimic3()
    cohorts = study_cohorts(df)
    flow = write_patient_flow(cohorts)
    write_corrected_table1(cohorts["eligible_documented_hypoferremia"])
    selection = write_selection_comparison(
        cohorts["complete_case_locked_matrix"],
        cohorts["excluded_for_locked_matrix_missingness"],
    )
    write_locked_matrix_missingness(cohorts["eligible_documented_hypoferremia"])
    corrected_mimic3 = write_corrected_mimic3_evaluation(mimic3)
    calibration = write_locked_calibration(corrected_mimic3)
    mi, _ = multiple_imputation_oof(cohorts["eligible_documented_hypoferremia"])
    niv = write_niv_exclusion_sensitivity(
        cohorts["eligible_documented_hypoferremia"],
        mimic3,
    )
    effects, incremental = association_and_incremental_value(
        cohorts["eligible_documented_hypoferremia"]
    )
    write_analysis_summary(
        flow,
        selection,
        calibration,
        corrected_mimic3,
        mi,
        niv,
        effects,
        incremental,
    )

    manifest = {
        "script": "scripts/r2_supplementary_analyses.py",
        "random_state": RANDOM_STATE,
        "iron_threshold_micrograms_dl": IRON_THRESHOLD,
        "minimum_icu_los_days": LOS_MIN_DAYS,
        "multiple_imputations": N_IMPUTATIONS,
        "cross_validation_folds": N_FOLDS,
        "mimic4_screened_los_ge_48h_n": len(
            cohorts["screened_los_ge_48h"]
        ),
        "mimic4_eligible_n": len(
            cohorts["eligible_documented_hypoferremia"]
        ),
        "mimic4_complete_locked_matrix_n": len(
            cohorts["complete_case_locked_matrix"]
        ),
        "mimic3_corrected_n": len(mimic3),
        "mimic3_corrected_events": int(
            mimic3["outcome_28d_hospital_admission"].sum()
        ),
        "patient_level_outputs_public": False,
        "time_origin": "hospital admission for the available 28-day outcome",
        "aggregate_window": "full ICU stay for min/max/mean predictors",
        "legacy_t0_status": "synthetic proxy; not an observed timestamp",
    }
    (RESULT / "r2_analysis_manifest.json").write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )
    publish_aggregate_reference_outputs()
    print(f"R2 analysis complete: {RESULT}")


if __name__ == "__main__":
    main()

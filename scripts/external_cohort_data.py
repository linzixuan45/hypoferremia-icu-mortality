from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
EXT_PATH = ROOT / "data" / "external" / "mimic_validation_cohorts.xlsx"
ALT_EXT_PATH = ROOT / "data" / "external" / "mimic论文数据测试集0901.xlsx"

FEATURE_8 = [
    "platelet_mean",
    "wbc_min",
    "bun_min",
    "pco2_max",
    "creatinine_min",
    "is_noninvasive_ventilator",
    "spo2_min",
    "platelet_1st",
]

_F3_SHEET = "low_fe_F3"
_NH_SHEET = "low_fe_NH"
_LABEL_COL = "hospital_expire_flag"

# Chinese cohort LIS exports use μmol/L creatinine and mmol/L urea; model input is mg/dL (MIMIC-aligned).
CREATININE_UMOL_L_TO_MG_DL = 1.0 / 88.4
BUN_MMOL_L_UREA_TO_MG_DL = 2.801

CREATININE_MG_DL_MEDIAN_RANGE = (0.4, 1.5)
BUN_MG_DL_MEDIAN_RANGE = (12.0, 22.0)


def _resolve_ext_path() -> Path | None:
    for path in (EXT_PATH, ALT_EXT_PATH):
        if path.exists():
            return path
    return None


def external_cohorts_available() -> bool:
    return _resolve_ext_path() is not None


def _harmonize_chinese_labs(df: pd.DataFrame, cohort: str) -> pd.DataFrame:
    """Convert F3/USC-FAH lab columns to MIMIC-aligned mg/dL before model input."""
    out = df.copy()
    if "creatinine_min" in out.columns:
        cr = pd.to_numeric(out["creatinine_min"], errors="coerce")
        out["creatinine_min"] = cr * CREATININE_UMOL_L_TO_MG_DL
    if "bun_min" in out.columns:
        bun = pd.to_numeric(out["bun_min"], errors="coerce")
        out["bun_min"] = bun * BUN_MMOL_L_UREA_TO_MG_DL

    cr_med = pd.to_numeric(out.get("creatinine_min"), errors="coerce").median()
    bun_med = pd.to_numeric(out.get("bun_min"), errors="coerce").median()
    lo_cr, hi_cr = CREATININE_MG_DL_MEDIAN_RANGE
    lo_bun, hi_bun = BUN_MG_DL_MEDIAN_RANGE
    if not (lo_cr <= cr_med <= hi_cr):
        raise ValueError(
            f"{cohort} harmonized creatinine_min median {cr_med:.3f} mg/dL "
            f"outside expected range [{lo_cr}, {hi_cr}]"
        )
    if not (lo_bun <= bun_med <= hi_bun):
        raise ValueError(
            f"{cohort} harmonized bun_min median {bun_med:.3f} mg/dL "
            f"outside expected range [{lo_bun}, {hi_bun}]"
        )
    return out


def load_f3_feature_table() -> pd.DataFrame:
    path = _resolve_ext_path()
    if path is None:
        raise FileNotFoundError("External cohort workbook (F3/USC-FAH; legacy key NH) not found under data/external/")
    df = pd.read_excel(path, sheet_name=_F3_SHEET)
    if _LABEL_COL not in df.columns:
        raise ValueError(f"Sheet {_F3_SHEET!r} missing column {_LABEL_COL!r}")
    out = df.copy()
    flags = pd.to_numeric(out[_LABEL_COL], errors="coerce")
    mapped = flags.replace(2, 0)
    out[_LABEL_COL] = mapped.astype(int)
    return out


def load_nh_feature_table() -> pd.DataFrame:
    path = _resolve_ext_path()
    if path is None:
        raise FileNotFoundError("External cohort workbook (F3/USC-FAH; legacy key NH) not found under data/external/")
    df = pd.read_excel(path, sheet_name=_NH_SHEET)
    if _LABEL_COL not in df.columns:
        raise ValueError(f"Sheet {_NH_SHEET!r} missing column {_LABEL_COL!r}")
    return df


def load_corrected_f3_feature_table() -> pd.DataFrame:
    return _harmonize_chinese_labs(load_f3_feature_table(), "F3")


def load_corrected_nh_feature_table(**_kwargs) -> pd.DataFrame:
    return _harmonize_chinese_labs(load_nh_feature_table(), "NH")

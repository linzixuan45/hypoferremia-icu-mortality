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


def _resolve_ext_path() -> Path | None:
    for path in (EXT_PATH, ALT_EXT_PATH):
        if path.exists():
            return path
    return None


def external_cohorts_available() -> bool:
    return _resolve_ext_path() is not None


def load_f3_feature_table() -> pd.DataFrame:
    path = _resolve_ext_path()
    if path is None:
        raise FileNotFoundError("External cohort workbook (F3/NH) not found under data/external/")
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
        raise FileNotFoundError("External cohort workbook (F3/NH) not found under data/external/")
    df = pd.read_excel(path, sheet_name=_NH_SHEET)
    if _LABEL_COL not in df.columns:
        raise ValueError(f"Sheet {_NH_SHEET!r} missing column {_LABEL_COL!r}")
    return df


def load_corrected_f3_feature_table():
    return load_f3_feature_table()


def load_corrected_nh_feature_table(**_kwargs):
    return load_nh_feature_table()

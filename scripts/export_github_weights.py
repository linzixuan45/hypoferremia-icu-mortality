#!/usr/bin/env python3
"""Write privacy-safe model metadata; never export fitted objects publicly.

The fitted KNN imputer stores its training feature matrix in ``_fit_X``.
Serializing that object into the repository would therefore redistribute
patient-level derived data. This compatibility command inspects the locally
fitted bundle and writes aggregate configuration metadata only.
"""
from __future__ import annotations

import json
import pickle
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "result" / "analysis" / "model_weight" / "8_features" / "model_weight.pkl"
DEST = ROOT / "result" / "r2_analysis" / "tables" / "model_bundle_metadata.json"


def _selected_params(model) -> dict[str, object]:
    wanted = {
        "voting",
        "lr__class_weight",
        "lr__max_iter",
        "rf__class_weight",
        "rf__max_depth",
        "rf__n_estimators",
        "xgb__learning_rate",
        "xgb__max_depth",
        "xgb__n_estimators",
    }
    return {k: v for k, v in model.get_params(deep=True).items() if k in wanted}


def main() -> None:
    if not SRC.exists():
        raise FileNotFoundError(
            f"Local fitted artifact not found: {SRC}\n"
            "Run train_models.py (or run_pipeline.py) using authorized data first."
        )
    with SRC.open("rb") as handle:
        bundle = pickle.load(handle)
    model = bundle.get("Ensemble_Voting", bundle.get("Ensemble_Stacking"))
    imputer = bundle["imputer"]
    metadata = {
        "artifact_status": "metadata_only; fitted objects are not publicly distributed",
        "features": bundle["features"],
        "decision_threshold": float(bundle["threshold"]),
        "model_parameters": _selected_params(model),
        "imputer": {
            "class": type(imputer).__name__,
            "n_neighbors": getattr(imputer, "n_neighbors", None),
            "retains_training_matrix": hasattr(imputer, "_fit_X"),
        },
        "scaler": type(bundle["scaler"]).__name__,
        "public_pickle_exported": False,
    }
    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"Privacy-safe metadata -> {DEST}")
    print("Fitted model/imputer/scaler objects remain local and must not be committed.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Export 8-feature model bundle for public release."""
from __future__ import annotations

import pickle
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "result" / "analysis" / "model_weight" / "8_features" / "model_weight.pkl"
DEST_DIR = ROOT / "model_weights"
DEST = DEST_DIR / "8_features_model.pkl"


def main():
    if not SRC.exists():
        raise FileNotFoundError(
            f"Training artifact not found: {SRC}\n"
            "Run train_models.py (or run_pipeline.py) before exporting weights."
        )
    bundle = pickle.load(open(SRC, "rb"))
    out = {
        "model": bundle.get("Ensemble_Voting", bundle.get("Ensemble_Stacking")),
        "imputer": bundle["imputer"],
        "scaler": bundle["scaler"],
        "features": bundle["features"],
        "threshold": bundle["threshold"],
    }
    DEST_DIR.mkdir(parents=True, exist_ok=True)
    with open(DEST, "wb") as f:
        pickle.dump(out, f)
    print(f"Exported -> {DEST}")


if __name__ == "__main__":
    main()

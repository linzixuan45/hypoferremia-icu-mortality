#!/usr/bin/env python3
"""
Hypoferremia 8-feature research web demo (not for clinical use).

Gradio UI with SHAP audit plots. Uses model_weights/8_features_model.pkl.
All lab inputs in model-native units (creatinine & BUN: mg/dL).
"""
from __future__ import annotations

import logging
import os
from pathlib import Path

import gradio as gr
import matplotlib.pyplot as plt
import shap

from src.inference import FEATURES, Inference

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

WEB_DIR = Path(__file__).resolve().parent
ROOT_PATH = os.environ.get("ROOT_PATH", "https://fe.mixaihub.top")
SERVER_PORT = int(os.environ.get("SERVER_PORT", "7788"))
SERVER_NAME = os.environ.get("SERVER_NAME", "0.0.0.0")
ICP_BEIAN = os.environ.get("ICP_BEIAN", "湘ICP备2026024281号")

DEFAULT_VALUES = {
    "platelet_mean": 180.0,
    "wbc_min": 5.0,
    "bun_min": 15.0,
    "pco2_max": 45.0,
    "creatinine_min": 0.9,
    "is_noninvasive_ventilator": 0,
    "spo2_min": 94.0,
    "platelet_1st": 175.0,
}

SHAP_DIR = WEB_DIR / ".shap_cache"
SHAP_PLOTS = {
    "summary": SHAP_DIR / "shap_summary_plot.png",
    "waterfall": SHAP_DIR / "shap_waterfall_plot.png",
    "force": SHAP_DIR / "shap_force_plot.png",
}


class HypoferremiaPredictor:
    def __init__(self):
        SHAP_DIR.mkdir(parents=True, exist_ok=True)
        self.inference = Inference()

    def _generate_shap_plots(self, x_raw, x_scaled) -> None:
        explainer = shap.TreeExplainer(self.inference.xgb)
        shap_values = explainer.shap_values(x_scaled)
        if isinstance(shap_values, list):
            shap_values = shap_values[1]

        shap.summary_plot(
            shap_values, x_scaled, feature_names=list(x_scaled.columns), show=False
        )
        plt.tight_layout()
        plt.savefig(SHAP_PLOTS["summary"])
        plt.close()

        plt.figure(figsize=(12, 8))
        shap.plots.waterfall(
            shap.Explanation(
                values=shap_values[0],
                base_values=explainer.expected_value,
                data=x_raw.iloc[0],
                feature_names=list(x_scaled.columns),
            )
        )
        plt.tight_layout()
        plt.savefig(SHAP_PLOTS["waterfall"])
        plt.close()

        shap.force_plot(
            explainer.expected_value,
            shap_values[0],
            x_raw.iloc[0],
            matplotlib=True,
        )
        plt.gcf().set_size_inches(16, 6)
        plt.tight_layout()
        plt.savefig(SHAP_PLOTS["force"])
        plt.close()

    def predict(self, **kwargs) -> tuple[str, str, str, str]:
        try:
            x_raw, x_scaled = self.inference.preprocess(kwargs)
            prob = self.inference.predict_proba(kwargs)
            pct = round(prob * 100, 1)
            label = int(prob >= self.inference.threshold)
            self._generate_shap_plots(x_raw, x_scaled)
            if label == 1:
                result = f"28-day mortality probability: {pct}%"
            else:
                result = f"28-day survival probability: {round(100 - pct, 1)}%"
            return (
                result,
                str(SHAP_PLOTS["summary"]),
                str(SHAP_PLOTS["waterfall"]),
                str(SHAP_PLOTS["force"]),
            )
        except Exception as e:
            logger.exception("Prediction failed")
            return f"Prediction failed: {e}", "", "", ""


def create_gradio_interface(predictor: HypoferremiaPredictor) -> gr.Blocks:
    def predict_wrapper(*args):
        return predictor.predict(**dict(zip(FEATURES, args)))

    with gr.Blocks(title="Hypoferremia Mortality Prediction (Research Demo)") as demo:
        gr.Markdown("# Hypoferremia 8-Feature Research Demo")
        gr.Markdown(
            "**Not for clinical use.** Inputs use model-native units: "
            "creatinine & BUN in **mg/dL**; platelets in **×10⁹/L**; "
            "SpO₂ in **%**; PCO₂ in **mmHg**. "
            "`is_noninvasive_ventilator`: 1 = documented NIV use, 0 = no documented use."
        )
        with gr.Row():
            platelet_mean = gr.Number(
                label="Platelet mean (×10⁹/L)",
                value=DEFAULT_VALUES["platelet_mean"],
            )
            wbc_min = gr.Number(label="WBC min (×10⁹/L)", value=DEFAULT_VALUES["wbc_min"])
        with gr.Row():
            bun_min = gr.Number(
                label="BUN min (mg/dL)",
                value=DEFAULT_VALUES["bun_min"],
            )
            creatinine_min = gr.Number(
                label="Creatinine min (mg/dL)",
                value=DEFAULT_VALUES["creatinine_min"],
            )
        with gr.Row():
            pco2_max = gr.Number(label="PCO₂ max (mmHg)", value=DEFAULT_VALUES["pco2_max"])
            spo2_min = gr.Number(label="SpO₂ min (%)", value=DEFAULT_VALUES["spo2_min"])
        with gr.Row():
            platelet_1st = gr.Number(
                label="Platelet 1st (×10⁹/L)",
                value=DEFAULT_VALUES["platelet_1st"],
            )
            is_noninvasive_ventilator = gr.Number(
                label="Non-invasive ventilator (0/1)",
                value=DEFAULT_VALUES["is_noninvasive_ventilator"],
                info="1 = documented non-invasive ventilation use; 0 = no documented use",
            )
        predict_button = gr.Button("Predict", variant="primary")
        output_text = gr.Label(label="Prediction Result")
        with gr.Row():
            output_summary = gr.Image(label="SHAP Summary")
            output_waterfall = gr.Image(label="SHAP Waterfall")
        output_force = gr.Image(label="SHAP Force")
        predict_button.click(
            predict_wrapper,
            inputs=[
                platelet_mean,
                wbc_min,
                bun_min,
                pco2_max,
                creatinine_min,
                is_noninvasive_ventilator,
                spo2_min,
                platelet_1st,
            ],
            outputs=[output_text, output_summary, output_waterfall, output_force],
        )
        gr.Markdown(f"---\n[{ICP_BEIAN}](https://beian.miit.gov.cn/)")
    return demo


def main() -> None:
    predictor = HypoferremiaPredictor()
    demo = create_gradio_interface(predictor)
    launch_kwargs = {
        "server_port": SERVER_PORT,
        "server_name": SERVER_NAME,
        "share": False,
    }
    if ROOT_PATH:
        launch_kwargs["root_path"] = ROOT_PATH
    demo.launch(**launch_kwargs)


if __name__ == "__main__":
    main()

# Figure 8 deployment audit

Audit date: 3 August 2026

The hosted demonstration at https://fe.mixaihub.top was opened and the default record was submitted. It returned a 28-day mortality probability of **22.4%**. The SHAP dot summary, waterfall plot, and force plot matched the default-case plots used in manuscript Figure 8.

The hosted deployment displayed the manuscript-aligned headings (`Case-level SHAP dot summary`, `Case-level waterfall`, and `Case-level force plot`), the warning `Research use only—not for clinical decision-making.`, and the browser-title/DOM revision marker `R2-web-2026-08-03`. These visible labels matched the reviewed root deployment source, `webui.py`.

The reviewed Figure 8 rendering is retained as `reference/r2/figure8_reviewed_interface.png`; its SHA-256 and expected default-case probability (22.4%) are locked in `reference/manifest.json`. The image contains no patient-level data.

Local pre-push validation used the protected model bundle without adding it to Git. The root `webui.py` loaded successfully, the default inputs returned **22.4%**, and the three generated plot rasters were pixel-identical to the previously audited hosted plots after decoding (identical dimensions and RGB pixel arrays). Browser inspection confirmed the exact warning, the three case-level labels, the XGBoost-component qualification, and the revision marker. The temporary model copy was moved out of the repository worktree after testing.

Deployment status: **verified**. No further Figure 8 redeployment is required for the v1.2.2 metadata-only cleanup unless the interface source changes after this audit.

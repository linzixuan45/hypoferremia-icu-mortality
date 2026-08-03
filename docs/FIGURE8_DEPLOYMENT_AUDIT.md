# Figure 8 deployment audit

Audit date: 3 August 2026

The hosted demonstration at https://fe.mixaihub.top was opened and the default record was submitted. It returned a 28-day mortality probability of **22.4%**. The SHAP dot summary, waterfall plot, and force plot matched the default-case plots used in manuscript Figure 8.

The hosted deployment nevertheless displayed shorter legacy headings (`SHAP Summary`, `SHAP Waterfall`, and `SHAP Force`) and the warning `Not for clinical use.` The reviewed repository source uses the manuscript-aligned headings (`Case-level SHAP dot summary`, `Case-level waterfall`, and `Case-level force plot`) and the stronger research-only warning.

Required release gate: after the reviewed branch is merged, redeploy/restart the production interface and repeat this audit. Do not claim complete visible-text equivalence until that check passes.

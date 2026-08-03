# Release v1.2.1 — reviewed Round 2 alignment

This public release was created from merge commit `b9beaac` and archived by Zenodo at https://doi.org/10.5281/zenodo.21768779.

## Changes since v1.2.0

- centralizes AUROC interval selection: DeLong for the MIMIC-IV internal test and stratified bootstrap for temporal and exploratory cohorts;
- documents that the legacy binary NIV field is encoded before KNN imputation;
- replaces the inaccurate public `Nanhua/NH` label with the legal institution name, The First Affiliated Hospital of University of South China (`USC-FAH`);
- keeps legacy `NH` identifiers only where necessary for compatibility with protected local files;
- aligns the Figure 8 source with case-level SHAP terminology and adds a deployment verification gate;
- records the published v1.2.0 DOI as a prior snapshot rather than claiming that it contains later R2 commits.

## Archive record

- GitHub release: https://github.com/linzixuan45/hypoferremia-icu-mortality/releases/tag/v1.2.1
- Merge commit: `b9beaac`
- Zenodo version DOI: https://doi.org/10.5281/zenodo.21768779
- Zenodo concept DOI: https://doi.org/10.5281/zenodo.21761212

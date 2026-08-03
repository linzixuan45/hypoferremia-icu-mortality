# Release v1.2.1 — final Round 2 alignment candidate

This release candidate is intended to be created from the reviewed merge commit. It must not move or replace the published v1.2.0 tag.

## Changes since v1.2.0

- centralizes AUROC interval selection: DeLong for the MIMIC-IV internal test and stratified bootstrap for temporal and exploratory cohorts;
- documents that the legacy binary NIV field is encoded before KNN imputation;
- replaces the inaccurate public `Nanhua/NH` label with the legal institution name, The First Affiliated Hospital of University of South China (`USC-FAH`);
- keeps legacy `NH` identifiers only where necessary for compatibility with protected local files;
- aligns the Figure 8 source with case-level SHAP terminology and adds a deployment verification gate;
- records the published v1.2.0 DOI as a prior snapshot rather than claiming that it contains later R2 commits.

## Archive instructions

After review and merge, create tag and GitHub release `v1.2.1` from the merge commit. Archive that exact release as the next version under Zenodo concept DOI `10.5281/zenodo.21761212`, then insert the newly assigned version DOI in the manuscript and submission files.

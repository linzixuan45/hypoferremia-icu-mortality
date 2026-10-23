# Release v1.2.2 — archive metadata cleanup

Version 1.2.2 is a documentation- and manifest-only cleanup of the reviewed Round 2 source released as v1.2.1. It does not change cohort construction, preprocessing, fitted-model specifications, figures, or reported aggregate results.

- GitHub release: https://github.com/linzixuan45/hypoferremia-icu-mortality/releases/tag/v1.2.2
- Zenodo version DOI: https://doi.org/10.5281/zenodo.21772246
- Tagged merge commit: `b9beaac`

## Changes since v1.2.1

- records the current v1.2.2 GitHub release, tagged merge commit `b9beaac`, and Zenodo DOI `10.5281/zenodo.21772246`, while retaining the historical v1.2.1 DOI where provenance requires it;
- records the immutable v1.2.2 Zenodo DOI without misrepresenting the historical v1.2.1 DOI as the DOI for v1.2.2;
- records the completed Figure 8 live-deployment verification and removes the obsolete redeployment warning;
- adds a regression test that prevents the stale release and deployment wording from returning.

## Post-release verification

The DOI-bearing Zenodo archive and GitHub tag must remain mapped to merge commit `b9beaac`. Post-release documentation corrections must not be represented as changes to the immutable archived scientific workflow.

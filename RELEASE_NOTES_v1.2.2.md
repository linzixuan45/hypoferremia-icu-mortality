# Release v1.2.2 — archive metadata cleanup

Version 1.2.2 is a documentation- and manifest-only cleanup of the reviewed Round 2 source released as v1.2.1. It does not change cohort construction, preprocessing, fitted-model specifications, figures, or reported aggregate results.

## Changes since v1.2.1

- replaces stale pre-publication references to v1.2.1 with the verified v1.2.1 GitHub release, merge commit `b9beaac`, and Zenodo DOI `10.5281/zenodo.21768779`;
- prepares citation and Zenodo metadata for v1.2.2 without misrepresenting the v1.2.1 DOI as the DOI for v1.2.2;
- records the completed Figure 8 live-deployment verification and removes the obsolete redeployment warning;
- adds a regression test that prevents the stale release and deployment wording from returning.

## Release gate

Before creating the v1.2.2 tag, obtain the immutable Zenodo version DOI and replace `[INSERT_V1.2.2_VERSION_DOI]` everywhere in the tree. The DOI-bearing commit, GitHub tag, GitHub release, and Zenodo archive must refer to the same source tree.

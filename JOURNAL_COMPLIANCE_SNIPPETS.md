# Journal Compliance Snippets

Companion article: *Retrospective mortality risk stratification in critically ill patients with documented hypoferremia*. The previous computation workflow is archived as v1.2.2 (10.5281/zenodo.21772246; source tree `b9beaac`). The R3 reporting corrections are released as v1.3.1 with immutable DOI 10.5281/zenodo.23608695, under Zenodo concept DOI 10.5281/zenodo.21761212. The snippets below are code-documentation drafts; this release does not edit manuscript files.

## Code Availability

```text
The previous computation workflow and non-patient aggregate outputs are archived as v1.2.2 at https://doi.org/10.5281/zenodo.21772246. The R3 reporting corrections are released as v1.3.1 at https://doi.org/10.5281/zenodo.23608695, under the Zenodo concept DOI https://doi.org/10.5281/zenodo.21761212, updating the article title, documentation and AUROC intervals using the unchanged canonical functions, without retraining primary models or changing their predictions. A bounded verification refit of the existing NIV-exclusion sensitivity reproduced its pre-existing canonical output and resolves inherited manuscript reporting differences. The public repository excludes patient-level records, identifiers, outcomes, individual probabilities, cohort-ID lists and fitted preprocessing or model objects.
```

## Editor response on code deposit

```text
We synchronized confidence intervals to the unchanged canonical computation. The internal reduced-model DeLong 95% interval is 0.718–0.874; AUROC remains 0.796 (269 admissions; 40 events). With 2,000 class-stratified bootstrap resamples and seed 42, MIMIC-III intervals are 0.659–0.752 for the benchmark and 0.669–0.763 for the reduced derivative; Chinese exploratory intervals are 0.699–0.900 and 0.826–0.954. Primary fitted models, predictions, AUROC point estimates and Brier scores are unchanged. We also resolved inherited S11 reporting discrepancies by a bounded refit of the pre-existing NIV-exclusion sensitivity using unchanged archived functions and the locked split. All four rows reproduce the canonical CSV within 1e-10, confirming internal AUROCs 0.814 and 0.785 and temporal AUROCs 0.727 and 0.751. The prior computation archive remains available as v1.2.2; the R3 corrections are released as v1.3.1 at https://doi.org/10.5281/zenodo.23608695.
```

## Placeholder tracking

| Item | Status | Value |
|---|---|---|
| GitHub | Complete | https://github.com/linzixuan45/hypoferremia-icu-mortality |
| Previous computation archive | Published baseline | v1.2.2; 10.5281/zenodo.21772246 |
| Current R3 release | Published | v1.3.1; DOI 10.5281/zenodo.23608695 |
| Zenodo concept DOI | Existing | 10.5281/zenodo.21761212 |

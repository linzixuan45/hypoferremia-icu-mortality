# Release Checklist

Complete on publication day. Repository positioning: **auditable analysis source code** (not bit-exact numeric reproduction).

## Pre-release verification

- [ ] `pip install -r requirements.txt && python inference.py` — prints 28-day mortality probability
- [ ] `grep -r "TODO.md\|numbering_map\|paper_data_overview" docs/` — no broken public links
- [ ] GitHub URL consistent across `README.md`, `CODE_AVAILABILITY.md`, `JOURNAL_COMPLIANCE_SNIPPETS.md`, `CITATION.bib`
- [ ] `reference/manifest.json` AUROC values match manuscript Table 2/3 (8-feature)

## GitHub

- [ ] Repository public at https://github.com/linzixuan45/hypoferremia-icu-mortality
- [ ] Create release tag `v1.0.0` from the commit used for the manuscript
- [ ] Release notes mention: auditable code deposit, online calculator URL, locked reference metrics, no patient data

## Zenodo

- [ ] Enable GitHub integration in Zenodo
- [ ] Trigger archive from GitHub release `v1.0.0`
- [ ] Record concept DOI and version DOI

## Fill placeholders

| File | Field |
|------|-------|
| `CITATION.bib` | authors, journal, volume, issue, pages, DOI |
| `README.md` | Zenodo DOI in Archive table |
| `CODE_AVAILABILITY.md` | Zenodo concept + version DOI |
| `JOURNAL_COMPLIANCE_SNIPPETS.md` | Zenodo version DOI in snippets + tracking table |
| Manuscript | Code Availability paragraph |
| Point-by-point response | GitHub + Zenodo links |

## Post-release

- [ ] If pipeline was re-run for the release, confirm `result/analysis/manifest.json` `git_commit` matches the tag
- [ ] Add Zenodo DOI to Scientific Reports submission

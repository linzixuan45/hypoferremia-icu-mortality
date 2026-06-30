# Journal compliance snippets

Use these drafts when updating the revised manuscript and point-by-point response.
Replace Zenodo placeholders after GitHub release and Zenodo DOI assignment.

---

## 1. Code Availability (Methods or dedicated section)

```text
An HTTPS research demonstration calculator for the 8-feature model is available at https://fe.mixaihub.top (not for clinical use). The underlying code and the released research model bundle are available at https://github.com/linzixuan45/hypoferremia-icu-mortality and will be archived with a DOI at Zenodo upon release. The repository includes the analysis pipeline, SQL extraction scripts, inference code, model card, and data dictionary. Raw patient-level data are not redistributed because access to MIMIC and local validation data is restricted.
```

---

## 2. Ethics / guidelines statement (Methods)

Add after the existing institutional approval statement:

```text
The study was approved by the relevant institutional review board, and all methods were performed in accordance with the relevant guidelines and regulations. Use of MIMIC-III and MIMIC-IV data followed PhysioNet credentialed access and data-use requirements.
```

---

## 3. Point-by-point response — Code deposit (editor requirement)

**Editor comment:** Custom/bespoke computational code must be deposited in a DOI-assigning repository and linked from Methods or Code Availability.

**Response:**

```text
We thank the editor for this reminder. We have deployed an HTTPS research demonstration calculator at https://fe.mixaihub.top (not for clinical use) and deposited the underlying analysis code, SQL extraction scripts, inference code, model card, data dictionary, and the released 8-feature research model bundle in a public GitHub repository (https://github.com/linzixuan45/hypoferremia-icu-mortality), to be archived with a Zenodo DOI upon release. The Code Availability statement in the revised manuscript now provides these links. Raw patient-level data were not redistributed because MIMIC and local validation cohorts are access-restricted.
```

---

## 4. Point-by-point response — Guidelines and regulations (editor requirement)

**Editor comment:** Confirm that all methods were performed in accordance with relevant guidelines and regulations.

**Response:**

```text
We have added an explicit statement to the Methods section confirming that all methods were performed in accordance with the relevant guidelines and regulations, in addition to the existing institutional approval disclosure.
```

---

## 5. Placeholder tracking

| Item | Status | Value |
|------|--------|-------|
| Research demo URL | Done | https://fe.mixaihub.top |
| GitHub URL | Done | https://github.com/linzixuan45/hypoferremia-icu-mortality |
| Zenodo concept DOI | Pending | |
| Zenodo version DOI | Pending | |
| Release tag | Recommended | `v1.0.0` |
| Submission ID | Known | `91406a0b-fc8b-4fcf-95bc-820b99f21793` |

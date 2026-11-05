# Breast Cancer Mammography — Feasibility Study

A bounded, **research-only feasibility audit** for a three-student, 6–7 month graduation project considering breast-mass **classification, detection, and segmentation**, with explainable AI and a prototype. This repository documents data, annotation, licensing, and compute gates. **No model has been trained, and no clinical performance or medical-grade feasibility is claimed.**

## Current decision

**CONDITIONAL GO for a research proposal; no unconditional GO to implement all three tasks.** The main unresolved gates are authorized access to a normal-inclusive detection dataset, complete multi-lesion mask handling, and a credible storage/GPU plan. See the [final feasibility decision](reports/final_feasibility_decision.md).

| Task | What was established | Status |
| --- | --- | --- |
| Classification | The official CBIS-DDSM mass CSVs contain 1,696 lesion-view rows, with no train/test `P_#####` participant overlap. A strict `MALIGNANT` vs `BENIGN` primary definition leaves 1,555 candidate rows; `BENIGN_WITHOUT_CALLBACK` is excluded from the primary analysis. | **CONDITIONAL GO** for ROI-linked, single-view lesion classification. |
| Detection | CBIS-DDSM mass files do not provide a verified normal-exam cohort. Official VinDr-Mammo includes radiologist-assessed BI-RADS-1 breasts and mass boxes, but its access is restricted and its suspicious-finding labels differ from CBIS pathology labels. | **CONDITIONAL GO** for a separate suspicious-mass endpoint after access and negative-cohort checks; **NO-GO** for CBIS-only screening specificity. |
| Segmentation and compute | Twelve official TCIA cases yielded 12/12 decodable, nonempty, full-image-aligned masks and boxes. Local CPU preprocessing took 0.304–1.008 seconds/case after imports, with 310–668 MB peak process RAM. | **CONDITIONAL GO** for source-mask agreement research; mixed-pathology pixels and GPU training cost remain unverified. |

## Audit reports

1. [TASK-01: dataset, permissions, risks, and decision](reports/task01_dataset_audit.md)
2. [TASK-02: 12-case smoke test and visual overlays](reports/task02_smoke_test.md)
3. [TASK-03: annotation integrity and task definitions](reports/task03_feasibility.md)
4. [TASK-04: detection datasets, access terms, and evaluation protocol](reports/task04_detection_feasibility.md)
5. [TASK-05: segmentation and CPU resource benchmark](reports/task05_segmentation_compute.md)
6. [Final feasibility gate](reports/final_feasibility_decision.md)

The `reports/figures/` overlays are **derived from the 12 official CBIS-DDSM cases** and are included as audit evidence. They are not independent clinical annotations. The `scripts/` directory contains the bounded read-only CSV, metadata, DICOM validation, and benchmark scripts. `data/cbis_ddsm/` contains the official mass CSVs plus small derived JSON audit results. The **original DICOM ZIPs and local environments are intentionally excluded** from GitHub; the ZIPs remain untouched in the local workspace and can be reacquired from the official source. This avoids turning a code/report repository into a duplicate DICOM archive.

## Reproducing the audit

Use only the [official TCIA CBIS-DDSM collection](https://www.cancerimagingarchive.net/collection/cbis-ddsm/) and its linked NBIA services. The two mass case-description CSVs are preserved at `data/cbis_ddsm/original/`; their provenance and SHA-256 hashes are recorded in [TASK-02](reports/task02_smoke_test.md). The 12-case selected series and official download method are also documented there. To rerun pixel checks or the CPU benchmark, place the corresponding official series ZIPs under `data/cbis_ddsm/original/series_zips/` without changing their contents. The scripts expect that directory layout. Python dependencies used for pixel work were `pydicom 3.0.2`, `numpy 2.5.4`, and `Pillow 13.0.0`; the TASK-05 memory probe uses Windows APIs. Metadata scripts query the official NBIA API. No training pipeline or model weights are included.

## Data use and limits

CBIS-DDSM is [CC BY 3.0](https://creativecommons.org/licenses/by/3.0/) and should be cited as: Sawyer-Lee, R., Gimenez, F., Hoogi, A., & Rubin, D. (2016). *Curated Breast Imaging Subset of Digital Database for Screening Mammography (CBIS-DDSM)*. The Cancer Imaging Archive. [DOI: 10.7937/K9/TCIA.2016.7O02S9CY](https://doi.org/10.7937/K9/TCIA.2016.7O02S9CY). Follow [TCIA data usage policies](https://wiki.cancerimagingarchive.net/display/Public/Data+Usage+Policies+and+Restrictions), including no re-identification or participant contact.

VinDr-Mammo images were **not downloaded**. Access requires the [PhysioNet Restricted Health Data License](https://physionet.org/content/vindr-mammo/view-license/1.0.0/); its images or annotations are not included here. This repository's reports and figures are for academic feasibility review, not diagnosis, screening, or clinical deployment.

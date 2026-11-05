# TASK-04 — detection dataset and evaluation feasibility

**Review date:** 2026-11-05. **Decision: CONDITIONAL GO** for a bounded **suspicious-mass localization** research task using an officially licensed negative cohort. **NO-GO** for claiming screening detection performance from CBIS-DDSM mass cases alone, or for treating every image without a box as a normal exam.

## VERIFIED — why CBIS-DDSM alone is insufficient

The official [CBIS-DDSM collection](https://www.cancerimagingarchive.net/collection/cbis-ddsm/) provides curated scanned-film mammograms, mass pathology rows, and mass masks. The complete mass CSV audit found 1,696 annotated mass rows and no normal/zero-mass label. TCIA's statement that the **parent DDSM** contained normal cases does not establish a verified normal cohort within the CBIS-DDSM mass manifests. The [TASK-03 audit](task03_feasibility.md) also found mixed-pathology full images and cross-view lesion-ID ambiguity. A non-annotated breast, image region, or contralateral view must **not** be silently declared negative.

## Official candidates

| Source | VERIFIED negative/normal evidence and positive localization | Access and terms | Compatibility / limit |
| --- | --- | --- | --- |
| **VinDr-Mammo v1.0.0**, [PhysioNet](https://physionet.org/content/vindr-mammo/1.0.0/) | 5,000 four-view digital exams (20,000 images), double read with arbitration. Breast-level BI-RADS 1 is a **radiologist-assessed negative breast**; the dataset paper reports 6,703 BI-RADS-1 **breasts**, not 6,703 negative exams. Finding CSV supplies boxes, including 1,226 mass finding annotations. | Registered users must sign the [PhysioNet Restricted Health Data Use Agreement and License 1.5.0](https://physionet.org/content/vindr-mammo/view-license/1.0.0/). The license limits use to lawful scientific research, prohibits re-identification and sharing access, and requires safeguards. The team must resolve individual access and permitted collaboration before obtaining files. | Best candidate for a modern digital, normal-inclusive detection benchmark. Boxes describe **findings needing further examination**; BI-RADS-2 benign findings were intentionally not marked. No pathology-confirmed cancer outcome is supplied. The authors note DICOM compliance problems, so decoding needs a separate smoke test after authorized access. Different acquisition domain and target definition from CBIS-DDSM. |
| **MIAS v1.21**, [University of Cambridge repository](https://www.repository.cam.ac.uk/items/b6a97f0c-3b9b-40ad-8f18-3d121eef1459) | Official record contains 322 digitized-film images (161 pairs) and associated truth data. The [INbreast authors' review of MIAS](https://web.fe.up.pt/~jsc/publications/journals/2012IMoreiraAcRadiology.pdf) describes normal images among the set. | Official repository lists **CC BY 2.0 UK: England & Wales** and a 1.51 GB PGM/truth-data release. Use the repository DOI and license attribution; no third-party mirror is needed. | Film origin is closer to CBIS-DDSM than VinDr. Small, MLO-only, older digitized-film cohort; truth data and approximate lesion location are not interchangeable with CBIS masks or modern digital boxes. Suitable only for a limited external negative/false-alarm sanity check after the truth file is inspected. |
| **OMI-DB / OPTIMAM**, [Royal Surrey / Cancer Research Horizons](https://www.cancerresearchhorizons.com/our-portfolio/our-licensing-opportunities/optimam-mammography-image-database-omi-db) | Official source lists normal, benign, interval, and cancer cases, with expert ROI annotations and longitudinal clinical data. | [Application, committee review, and a negotiated sharing/license agreement](https://medphys.royalsurrey.nhs.uk/omidb/what-is-the-process/) are required; academic applications need a qualified principal investigator. No access was requested. | Potentially strong but **not a near-term dependency** for a three-student 6–7 month project until an institutional PI and agreement are secured. Exact licensed subset, annotations, cost, and lead time are unverified. |

**VinDr qualification:** BI-RADS 1 is a consensus radiology assessment of no suspicious finding, **not pathology or longitudinal proof of cancer absence**. Its [dataset paper](https://doi.org/10.1038/s41597-023-02100-7) says pathology-confirmed ground truth is absent and BI-RADS-2 benign findings were not boxed. Therefore it supports evaluation of **suspicious-mass detection under the reader annotations**, not detection of every benign and malignant physical mass or diagnosis of cancer. [PhysioNet dataset description](https://physionet.org/content/vindr-mammo/1.0.0/).

## INFERRED — defensible detection protocol, contingent on access

1. **Define the target precisely:** a radiologist-marked *suspicious mass requiring further examination*, not “all masses” or “cancer.” A positive is a VinDr `finding_categories` record containing `Mass` and a valid box. Do not relabel CBIS `BENIGN`/`BENIGN_WITHOUT_CALLBACK` masks as equivalent VinDr suspicious-mass positives.
2. **Define negatives from affirmative assessment:** for breast-level false-alarm analysis, require both CC and MLO images of the same breast to have BI-RADS 1, with the breast-level and finding CSVs reconciled. For exam-level normal false-alarm analysis, require **both breasts** to be BI-RADS 1 and no contradictory finding rows. Exclude incomplete, discordant, missing, or ambiguous records. A missing finding row alone is never enough. The published 6,703 BI-RADS-1 count is breast-level; the qualifying exam count must be measured after access.
3. **Keep domains and splits separate:** use VinDr's provided training/test split at the exam (`study_id`) level, make validation from training exams, and audit whether repeated individuals can cross exams/splits. Use CBIS-DDSM only as a separate film-domain localization set or, in a later approved study, as a pretraining source. Never pool pathology labels with VinDr BI-RADS labels as if they share one endpoint. Test any cross-domain transfer separately.
4. **Predeclare evaluation:** report lesion localization sensitivity at one or more prespecified IoU/center-distance thresholds and a FROC-style sensitivity versus false positives per image or exam. Report normal-breast/exam false-alarm rates **on the affirmative BI-RADS-1 subset**, with confidence intervals clustered by exam. Select operating points using training/validation only. Stratify by site/scanner and breast density where permitted. Keep CBIS positive-only localization results separate and do not call them screening specificity.
5. **Publish limits:** all results describe retrospective reader labels; without pathology/follow-up and external clinical validation they cannot establish medical-grade detection or cancer diagnosis.

## UNVERIFIED / blocking issues

- **Access:** no VinDr file, CSV, or DUA acceptance was obtained. Each student's permitted access and whether a shared university workspace satisfies the current license must be resolved through PhysioNet; restricted images must not appear in a public prototype. [Current license](https://physionet.org/content/vindr-mammo/view-license/1.0.0/).
- **Actual negative cohort:** counts of exams with both breasts BI-RADS 1, CSV consistency, repeated-patient linkage, box validity, file size, and DICOM decoder behavior require an authorized metadata/pixel smoke test. The paper's breast-level counts cannot substitute for this audit.
- **Target compatibility:** VinDr omits BI-RADS-2 benign finding boxes, whereas CBIS-DDSM includes benign masses. A universal “mass detector” target across both data sources is not established.
- **MIAS details:** the exact official truth-file normal count, pair grouping, coordinate conventions, and lesion-box conversion were not inspected; do not treat its empty annotation entries as negatives until truth labels are parsed. Its small size and MLO-only design limit primary evaluation.
- **OMI-DB:** approval, license terms, available subset, cost, and timing are unknown. It is an optional route, not a guaranteed fallback.

## Gate

**CONDITIONAL GO** to define and later test a VinDr-based *suspicious-mass* detection endpoint, conditional on authorized access, a verified BI-RADS-1 negative cohort, CSV/image integrity, and a fixed evaluation protocol. **NO-GO** for screening-style detection claims from CBIS-DDSM mass data or from absence of a box. No datasets were downloaded for TASK-04.

### Evidence links

- [TCIA CBIS-DDSM official collection](https://www.cancerimagingarchive.net/collection/cbis-ddsm/)
- [VinDr-Mammo official PhysioNet page, version and access](https://physionet.org/content/vindr-mammo/1.0.0/)
- [VinDr-Mammo authors' data paper](https://doi.org/10.1038/s41597-023-02100-7)
- [Current PhysioNet restricted license](https://physionet.org/content/vindr-mammo/view-license/1.0.0/)
- [Cambridge MIAS v1.21 repository and license](https://www.repository.cam.ac.uk/items/b6a97f0c-3b9b-40ad-8f18-3d121eef1459)
- [Royal Surrey OMI-DB application process](https://medphys.royalsurrey.nhs.uk/omidb/what-is-the-process/)

# TASK-03 — CBIS-DDSM annotation and task-definition feasibility

**Audit date:** 2026-11-05  
**Overall recommendation:** **CONDITIONAL GO** for a research-only, **lesion-in-one-view classification** project. Segmentation remains conditional on a larger pixel-level mask audit. **NO-GO for screening-style detection evaluation using the mass subset alone** because verified normal/negative examinations are not supplied by the mass case descriptions.

This audit reused the two unchanged official mass CSVs and 12 validated image cases from [TASK-02](task02_smoke_test.md). It downloaded **no additional DICOM images**, trained no models, and did not start implementation. Official [TCIA CBIS-DDSM](https://www.cancerimagingarchive.net/collection/cbis-ddsm/) and its [public NBIA metadata API](https://wiki.cancerimagingarchive.net/display/Public/NBIA+Search+REST+API+Guide) were the only external data sources.

**Data attribution:** Sawyer-Lee, R., Gimenez, F., Hoogi, A., & Rubin, D. (2016). *Curated Breast Imaging Subset of Digital Database for Screening Mammography (CBIS-DDSM)* [Data set]. The Cancer Imaging Archive. [DOI: 10.7937/K9/TCIA.2016.7O02S9CY](https://doi.org/10.7937/K9/TCIA.2016.7O02S9CY). License: [CC BY 3.0](https://creativecommons.org/licenses/by/3.0/). This report contains derived counts and estimates, not original images.

## Method and audit boundary

1. **Complete CSV census:** Read all **1,318 training** and **378 test** mass annotation rows. Checked labels, nulls, path structure, patient keys, full-image/ROI-series uniqueness, duplicate annotations, cross-view keys, and train/test overlap. Stripped surrounding CSV field whitespace only in the working index; original files stayed unchanged. The [TASK-02 report](task02_smoke_test.md) contains source URLs and SHA-256 hashes.
2. **Reproducible larger sample:** Selected **96 rows from 96 distinct participants**, eight per `split × source pathology × view` stratum (2 × 3 × 2). Within a stratum, rows were ranked by SHA-256 of the fixed seed `TASK03-CBIS-DDSM-20261105-v1` and the record key. This sample deliberately balances uncommon labels and test cases; it is **not** prevalence representative.
3. **Official metadata check:** Queried `getSeriesMetaData` for the **195 distinct series UIDs** referenced by those 96 rows, including separate crop series where applicable. Checked collection, DICOM subject ID, expected series description, and object count. No image pixels were requested. All **96/96 sampled rows** passed the corrected layout-aware metadata checks; all **195/195 queried series** returned metadata without an API error.
4. **Pixel evidence:** TASK-02's 12 selected training cases remain the only local pixel-level inspection: 12/12 DICOM masks were full-image sized, binary, nonempty, and yielded plausible overlays and boxes. The 96-record metadata audit **does not** raise the measured mask-validity sample from 12 to 96.

Reproducible outputs: [complete CSV audit and selected rows](../data/cbis_ddsm/task03_annotation_audit.json), [official metadata responses and checks](../data/cbis_ddsm/task03_metadata_audit.json), and [planning estimates](../data/cbis_ddsm/task03_estimates.json). Read-only scripts: [CSV audit](../scripts/task03_annotation_audit.py), [metadata check](../scripts/task03_metadata_audit.py), [resource estimates](../scripts/task03_estimates.py).

## VERIFIED — annotation structure and integrity

| Finding | Train | Test | Interpretation |
| --- | ---: | ---: | --- |
| Annotation rows | 1,318 | 378 | A row identifies a mass annotation in one view; it is not an independent participant. |
| Distinct `P_#####` participants | 691 | 201 | Use this key for grouping. |
| Distinct full-image paths/series | 1,231 | 361 | Fewer than rows because some images have multiple annotations. |
| Distinct ROI-series UIDs | 1,318 | 378 | One ROI-series UID per annotation row in these CSVs. |
| Full images with >1 annotated lesion | 58 | 13 | Per-image labels can be ambiguous. |
| Full images with mixed pathology | 6 | 2 | Do not assign the whole image a row's label. |
| Participants with mixed pathology | 13 | 5 | Do not treat participant labels as inherently singular. |
| Exact duplicate annotation records | 0 | 0 | Under the audited composite record key. |
| Missing fields or malformed path shapes | 0 | 0 | Structural check only; it does not prove file/pixel integrity. |
| ROI/crop paths with **different series UIDs** | 92 | 11 | A supported alternative layout, not automatically a bad annotation. |

All **1,696** `ROI mask file path` values in the original CSVs carry outer whitespace/newline; the working index strips it. TCIA warns that DICOM Patient IDs multiply per actual participant, so a DICOM folder is not a safe split key. [Official collection note](https://www.cancerimagingarchive.net/collection/cbis-ddsm/).

For the sampled rows, TCIA metadata showed **96 full-mammogram series with one object each**. Of the ROI/crop paths, **93 rows used one two-object `ROI mask images` series** and **3 used separate one-object `ROI mask images` and `cropped images` series**. All expected subject IDs matched. The latter three examples were P_00294 (train, MLO) and P_00145/P_00699 (test, MLO). Thus a loader must handle both layouts and inspect DICOM descriptions/content rather than presume that crop and mask always share a folder or that filename order identifies the mask. [NBIA API guide](https://wiki.cancerimagingarchive.net/display/Public/NBIA+Search+REST+API+Guide); [TASK-02 pixel checks](task02_smoke_test.md).

**Cross-view identity warning:** A provisional key `(patient_id, laterality, abnormality id)` yields three apparent pathology conflicts. For P_00419 LEFT, CC has `1=BENIGN, 2=MALIGNANT`, while MLO has `1=MALIGNANT, 2=BENIGN`: the ID-label assignments reverse between views. Whether those lesions correspond anatomically is unverified. P_01623 RIGHT has `1=MALIGNANT` in CC and `1=BENIGN` in MLO; correspondence is unresolved. Therefore abnormality ID is **not a verified cross-view lesion identity**. The provisional key is unsuitable for pooling CC/MLO labels without an image/clinical correspondence check. These are mapping ambiguities, not proof of three incorrect source pathology labels.

## Proposed classification task and label policy — INFERRED decision rules

**Primary endpoint:** binary malignancy classification of a **single mass annotation in one mammographic view**. Each example is the ROI-linked crop from one CSV row, identified by `(split, ROI series UID)` and paired with its full mammogram and mask for quality checks. The output means **the source annotation's malignant vs benign label for that localized finding**; it does not mean screening cancer status for the entire image or patient.

| Source `pathology` | Primary analysis | Secondary sensitivity analysis |
| --- | --- | --- |
| `MALIGNANT` | Positive | Positive |
| `BENIGN` | Negative | Negative |
| `BENIGN_WITHOUT_CALLBACK` | **Exclude** | Include as a separately reported nonmalignant subgroup; do not call it a normal image or assume its diagnostic verification equals `BENIGN`. |

This yields **1,555 candidate lesion-view rows** for the primary binary task (784 malignant, 771 benign) before pixel-level quality exclusions. The secondary inclusive mapping would use all **1,696 rows**, but results must be reported separately. The stricter primary rule avoids silently merging source categories whose individual reference standards have not been verified. Neither the CSV field name `pathology` nor this audit proves every benign row has histopathology confirmation.

**Mixed-pathology rule:** Keep each ROI-linked annotation and its own label even when a full mammogram or participant has another lesion with a different label. Never use the full image as a one-label proxy for that row. Quarantine an annotation if its crop/mask identity or pixel mapping cannot be resolved. Do not pair CC and MLO by `abnormality id` alone; a two-view lesion endpoint requires explicit correspondence adjudication. P_00419 and P_01623 are mandatory test cases for any future pairing procedure.

**Evaluation unit and leakage rule:** Keep **every view, lesion, crop, mask, patch, augmentation, and derivative from a `P_#####` participant in one partition**. Use the provided test participants only for final evaluation; form validation groups from training participants. Select any thresholds and preprocessing using training/validation only. Report lesion-view metrics (for example AUROC and sensitivity/specificity at a declared threshold) with confidence intervals clustered by participant, since multiple rows from one participant are correlated. Do not describe these as screening sensitivity or patient-level diagnostic accuracy.

## VERIFIED — split audit; remaining leakage risks

There is **zero overlap** between the official mass train/test CSVs by `P_#####` participant ID, full-image path, full-image Series Instance UID, or ROI Series Instance UID. This is a stronger check than comparing DICOM Patient IDs, but it covers these two mass CSVs only. TCIA describes the published split as case based, and its many-DICOM-IDs-per-participant warning makes independent grouping necessary. [TCIA split description](https://www.cancerimagingarchive.net/collection/cbis-ddsm/).

Remaining leakage risks are **INFERRED**: row-random validation splits would share patients, two views, full images, or multiple lesions; crop extraction before splitting can distribute near-duplicates; augmentation and normalization fitted across partitions can leak information. **UNVERIFIED:** overlap with calcification subsets or any future external data, and duplicate pixel content beyond path/UID identity. Those do not change the measured zero-overlap result for the official mass CSV pair.

## Detection and segmentation task definitions

**Detection — limited research endpoint only.** The 1,696 mass CSV rows all describe annotated masses and contain only `MALIGNANT`, `BENIGN`, or `BENIGN_WITHOUT_CALLBACK`. They supply **no verified normal/zero-mass row**. The [TCIA collection page](https://www.cancerimagingarchive.net/collection/cbis-ddsm/) says the *parent DDSM* included normal cases, while CBIS-DDSM's listed mass downloads are for mass abnormalities; it does not establish a normal evaluation cohort in the mass subset. A detector could be evaluated for localization of known masses on positive mammograms (predeclared IoU or center-distance criterion, recall, and false detections per positive image). It **cannot** establish screening specificity, normal-exam false-positive rate, or clinical detection utility from these CSVs alone. Contralateral or unmarked tissue should not be declared a verified negative. **NO-GO for screening-style detection evaluation** until a properly sourced, licensed, exhaustively reviewed negative cohort and evaluation protocol exist.

**Segmentation — conditional research endpoint.** A row's full-image-aligned binary mass mask can define a lesion instance target and bounding box. Evaluation against supplied masks could use per-lesion Dice/IoU, with participant-grouped uncertainty and separate reporting for multi-lesion images. TASK-02 validated 12 masks; TASK-03 confirmed only metadata for 96 rows. Expert contour fidelity, all-row pixel validity, and whether every apparent ROI is a usable lesion mask remain **UNVERIFIED**. No clinical boundary accuracy claim follows from agreement with these supplied masks.

## INFERRED — storage and compute planning

The 96-row TCIA metadata sample supports a **planning extrapolation**, not a measured mass-subset size: **about 81.9 GB of mass DICOM objects** (estimated 53.2 GB full mammograms and 28.8 GB ROI/crop content). The method averages eight rows within each split/pathology/view stratum, weights by all CSV rows, and corrects full-image estimates for 1,592 distinct full series. A resampling interval over this **metadata sample only** is **75.6–88.8 GB**; it excludes selection bias, data-layout issues, ZIP/cache files, and working copies. The [estimate JSON](../data/cbis_ddsm/task03_estimates.json) records the formula. Do not substitute TCIA's **163.51 GB whole-collection** size for the mass-only estimate. [TCIA size](https://www.cancerimagingarchive.net/collection/cbis-ddsm/).

| Candidate task | Candidate data | Storage and compute implication | Gate |
| --- | --- | --- | --- |
| Primary lesion-view classification | 1,555 strict candidate rows; source crops | The 12 downloaded crop DICOM objects were 41 KB–606 KB (median 149 KB); median × 1,555 is ~0.23 GB of crop objects, **a rough illustration only**. CPU decoding and smaller crop tensors appear manageable; model training time/GPU memory is unmeasured. | Validate crop/mask pairing beyond 12 cases and keep participant-grouped evaluation. |
| Positive-image mass localization | 1,592 distinct full-image series plus lesion masks/boxes | Sample-based full-image DICOM estimate ~53 GB. TASK-02 full images ranged ~9.8–22.8 million pixels. One 22.8-million-pixel image is ~45.7 MB as uint16 or ~91.4 MB as float32 before masks, model activations, and batch copies. | Define negatives and benchmark a declared resolution/tiling approach before a detection commitment. |
| Mass segmentation | Full images plus ROI masks; crops may share the ROI series | Sample-based full+ROI/crop DICOM estimate ~82 GB. Full-resolution masks and activations can multiply RAM/GPU use. | Broader pixel-level mask and expert plausibility audit; benchmark memory on target hardware. |

The D: drive had about **77.4 GB free after TASK-02**. This is below the ~82 GB point estimate for uncompressed mass DICOMs alone. A simple original-plus-one-working-copy scenario would need roughly **164 GB**, before ZIP/cache or model artifacts; streaming and smaller derived images might reduce that, but no such pipeline was evaluated here. **GPU requirement, training time, optimal resolution, and deployment cost are UNVERIFIED.** No training or hardware benchmark was performed.

## Unresolved risks and decision

- **Label meaning:** `BENIGN_WITHOUT_CALLBACK` remains a separate source category; the reference standard for each benign annotation is not individually established here. Primary analysis excludes it; secondary analysis must disclose the inclusive mapping.
- **Cross-view identity:** abnormality IDs can change meaning between views. P_01623's discordance needs adjudication before any paired-view lesion task.
- **Annotation coverage:** metadata checks passed for 96/96 rows, but only 12/12 masks have pixel-level checks. This cannot establish the full dataset's mask or contour quality.
- **Detection negatives:** no verified normal/zero-mass evaluation cohort is identified in the mass CSVs. Screening-style detection claims remain blocked.
- **Resources:** the ~82 GB mass DICOM estimate exceeds current free space as a stand-alone uncompressed acquisition; GPU/time estimates require a later controlled benchmark.
- **External validity:** CBIS-DDSM is a curated subset of scanned-film mammography; performance on contemporary digital mammography or clinical populations is unverified. [TCIA collection description](https://www.cancerimagingarchive.net/collection/cbis-ddsm/).

**CONDITIONAL GO** if the project is narrowed to lesion-view benign-versus-malignant research classification with participant-held-out evaluation, strict primary labels, and a predeclared quality gate. Segmentation may become a secondary research objective after a larger pixel audit and resource benchmark. **NO-GO for screening-style detection evaluation from the mass subset alone.** A full five-part classification/detection/segmentation/XAI/deployment commitment is not justified by this audit.

**Recommended next task for human review:** decide the single primary endpoint and the strict/secondary label policy; if approved, plan a bounded, predeclared pixel-level audit of mixed-pathology and split-series cases plus a separate normal-cohort provenance/permission review for any detection claim. Stop here; no TASK-04 work has started.

### Evidence links

- [Official TCIA CBIS-DDSM collection: version, curation, split description, manifests, citation](https://www.cancerimagingarchive.net/collection/cbis-ddsm/)
- [Official NBIA Search REST API guide: `getSeriesMetaData`](https://wiki.cancerimagingarchive.net/display/Public/NBIA+Search+REST+API+Guide)
- [TASK-02 CSV hashes, DICOM validation, overlays, and observed transfer sizes](task02_smoke_test.md)
- [Dataset authors' publication](https://doi.org/10.1038/sdata.2017.177)

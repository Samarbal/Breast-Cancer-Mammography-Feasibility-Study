# TASK-01 — CBIS-DDSM dataset audit

Audit date: 2026-11-05. Scope: official TCIA CBIS-DDSM collection, mass cases only. This is a source and feasibility audit; no images were downloaded or inspected.

## VERIFIED — official source and contents

- The authoritative collection is [TCIA CBIS-DDSM](https://www.cancerimagingarchive.net/collection/cbis-ddsm/), DOI [10.7937/K9/TCIA.2016.7O02S9CY](https://doi.org/10.7937/K9/TCIA.2016.7O02S9CY). TCIA lists **Version 1, updated 2017-09-14**, as complete. The whole collection is **163.51 GB**, 10,239 DICOM images, and 1,566 actual participants. The 6,671 DICOM “patient” count is not a participant count.
- TCIA offers four mass-only image manifests: **Mass-Training Full Mammogram Images**, **Mass-Training ROI and Cropped Images**, **Mass-Test Full Mammogram Images**, and **Mass-Test ROI and Cropped Images**. The image downloads use the NBIA Data Retriever. It separately offers `mass_case_description_train_set.csv` (754.62 KB; TCIA table lists 691 subjects) and `mass_case_description_test_set.csv` (211.95 KB; 201 subjects). Those subject counts must not be treated as image, lesion, or disjoint participant counts without a CSV audit. [Collection access table](https://www.cancerimagingarchive.net/collection/cbis-ddsm/).
- TCIA says CBIS-DDSM includes decompressed DICOM full images, focused abnormality crops, updated mass ROI segmentation and bounding boxes, and pathology. Its description says the refined segmentation procedure was applied to **masses**, not calcifications. The original mass contours were imprecise, and TCIA removed 254 images in which a mass was not clearly seen. [TCIA detailed description](https://www.cancerimagingarchive.net/collection/cbis-ddsm/).
- TCIA says the supplied train/test split is by **case/abnormality**, approximately 80/20 and stratified by BI-RADS, with CC and MLO views of an abnormality treated as one case. This does **not** establish participant-level separation. [TCIA detailed description](https://www.cancerimagingarchive.net/collection/cbis-ddsm/).
- TCIA explicitly warns that one participant can have multiple DICOM Patient IDs, e.g. `Calc-Test_P_00038_LEFT_CC` and suffixed variants. The participant key is the underlying `P_00038`, not the entire DICOM Patient ID. [TCIA collection note](https://www.cancerimagingarchive.net/collection/cbis-ddsm/).
- NBIA supports selecting series in the [Radiology Portal](https://nbia.cancerimagingarchive.net/nbia-search/?CollectionCriteria=CBIS-DDSM), exporting a `.tcia` manifest, and downloading it with the Data Retriever; the [CLI guide](https://wiki.cancerimagingarchive.net/display/NBIA/NBIA+Data+Retriever+Command-Line+Interface+Guide) documents resumable downloads, classic/descriptive directory naming, and optional MD5 checking. Public-only manifests do not need a credential file per that guide.

## INFERRED — suitability for the proposed tasks

| Task | Technical reading | Gate before relying on it |
| --- | --- | --- |
| Benign vs malignant **mass** classification | Pathology in the mass case descriptions can label an identified lesion or its crop. `BENIGN_WITHOUT_CALLBACK`, if present, needs an explicit mapping policy. | Inspect label values, missingness, multiple lesions, and patient-level separation. State clearly whether the input is a supplied crop or a whole mammogram. |
| Mass detection | A validated full-image binary ROI can yield a bounding box. The mass-only subset may be weak for screening-style false-positive assessment because normal mammograms are not established as present. | Confirm full-image/mask coordinates and inspect negative/background coverage; define what counts as a negative image. |
| Mass segmentation | The refined mass ROIs are plausible research masks. | Confirm each linked DICOM is truly a binary lesion mask, full-image aligned, and anatomically plausible. Reject ambiguous pairs. |
| Grad-CAM and prototype | These are possible downstream engineering activities. | Dataset licensing and annotation availability do not establish model quality, explanation faithfulness, safe clinical use, or deployment suitability. |

## VERIFIED — known path/mapping warning in available implementation evidence

- The [TensorFlow Datasets CBIS-DDSM builder](https://github.com/tensorflow/datasets/blob/master/tensorflow_datasets/image_classification/cbis_ddsm.py#L3084-L3175) reads the CSV `image file path`, `ROI mask file path`, and `cropped image file path` fields. Its code documents frequent apparent **crop/mask column reversals**, checks image dimensions, swaps candidate paths in some cases, and excludes rows with no suitable mask. This is evidence of a real mapping hazard in a named implementation, **not** proof that every TCIA row is wrong or that its heuristic is universally safe.
- NBIA's descriptive and classic layouts differ. Therefore a CSV path should be treated as a logical reference and checked against DICOM metadata and actual downloaded files; blindly concatenating it to a download root is unsafe. The exact failure rate, filenames, and current manifest behavior remain unverified locally. [NBIA CLI guide](https://wiki.cancerimagingarchive.net/display/NBIA/NBIA+Data+Retriever+Command-Line+Interface+Guide).

## UNVERIFIED — practical barriers and questions

- No DICOM or CSV file has been downloaded, so exact mass-only subset sizes, row counts, class balance, path resolution rate, image dimensions, pixel depth, mask validity rate, and train/test participant overlap are unmeasured here. **163.51 GB is the entire collection, not a mass-only estimate.**
- The project will need an NBIA installation, enough disk for original DICOMs plus derived working copies, download bandwidth, a DICOM decoder compatible with the transfer syntax, and compute/RAM for large mammograms. Budget space only after inspecting manifest/portal size; leave headroom for temporary and processed files.
- The clinical meaning of `pathology`, the handling of multiple abnormalities with discordant labels, and any diagnostic reference standard for each CSV row require a direct CSV and publication review before model design.
- Whether TCIA's case-level train/test split also separates every underlying `P_#####` participant is unresolved. Audit overlap before using those splits for evaluation.

## Minimal 10–20-case acquisition plan (proposed; not executed)

1. Download only the two **official mass CSVs** from TCIA. Record source URLs, version/date, byte sizes, and SHA-256 hashes. Read them without editing the originals.
2. Build a read-only index of `patient_id`, view, laterality, abnormality ID, pathology, and the three image paths. Normalize a participant key such as `P_#####`; inspect for train/test participant overlap. Select **10–20 distinct mass cases** from training only, spanning benign/malignant, CC/MLO, and where possible multiple lesions. Keep a fixed manifest of selected rows and reason for selection. This is an engineering smoke test, not an evaluation sample.
3. In the official NBIA portal, search for only the selected full mammogram, ROI, and crop **series**; export a small `.tcia` manifest. Verify estimated bytes before download. Use NBIA Data Retriever with a dedicated staging directory and checksum validation. Do not use a third-party mirror.
4. For each row, match files using participant, view/laterality, series descriptions, and DICOM UIDs; log missing/ambiguous links. Check mask pixel values, dimensions, overlay alignment, nonempty lesion, and a derived bounding box. Review overlays visually. Quarantine failures rather than relabeling a crop as a mask based on filename alone.
5. Record download bytes, parse/mapping success rates, and per-case issues. Stop before any training or full-collection acquisition; use these measurements for TASK-02 planning only after human approval.

## Evidence links

- [TCIA CBIS-DDSM collection, Version 1 and access table](https://www.cancerimagingarchive.net/collection/cbis-ddsm/)
- [Official NBIA Radiology Portal for CBIS-DDSM](https://nbia.cancerimagingarchive.net/nbia-search/?CollectionCriteria=CBIS-DDSM)
- [NBIA Data Retriever CLI guide](https://wiki.cancerimagingarchive.net/display/NBIA/NBIA+Data+Retriever+Command-Line+Interface+Guide)
- [TensorFlow Datasets builder and its path checks](https://github.com/tensorflow/datasets/blob/master/tensorflow_datasets/image_classification/cbis_ddsm.py#L3084-L3175)
- [Dataset authors' publication](https://doi.org/10.1038/sdata.2017.177)

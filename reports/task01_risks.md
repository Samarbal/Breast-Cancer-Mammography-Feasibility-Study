# TASK-01 — risk register

Audit date: 2026-11-05. Ratings indicate potential project impact, not measured failure frequency.

| Risk | Evidence status | Impact | Evidence and required check |
| --- | --- | --- | --- |
| Participant leakage across train/validation/test | **VERIFIED** identifier structure; **UNVERIFIED** actual overlap | High | [TCIA](https://www.cancerimagingarchive.net/collection/cbis-ddsm/) says many DICOM Patient IDs can belong to one participant and describes case-level splitting. Group by underlying `P_#####`; measure overlap across supplied splits and between views/crops before evaluation. |
| Crop/mask path misassignment | **VERIFIED** warning in an implementation; **UNVERIFIED** local rate | High | [TensorFlow Datasets builder](https://github.com/tensorflow/datasets/blob/master/tensorflow_datasets/image_classification/cbis_ddsm.py#L3128-L3175) documents frequent apparent reversals and unusable mask matches. Match with DICOM metadata, shapes, binary pixels, and visual overlay. Do not globally swap columns. |
| Invalid or poorly aligned segmentation targets | **VERIFIED** TCIA states mass refinement; **UNVERIFIED** per-file validity | High | [TCIA](https://www.cancerimagingarchive.net/collection/cbis-ddsm/) describes automated refinement and removal of questionable cases. Inspect every smoke-test ROI; log missing, empty, crop-like, wrong-size, or implausible masks. |
| Confounded classification labels | **INFERRED** from lesion/view structure; **UNVERIFIED** local frequency | High | Multiple abnormalities or views may share images and differ in pathology. Define lesion-level unit and an explicit policy for discordant labels; never silently assign an image one label. |
| Detection false-positive assessment | **INFERRED** | High | Mass-specific cases are centered on known abnormalities; normal/background exam coverage is uncertain. A detector trained/evaluated only on these cases cannot establish screening performance. Audit negatives before claiming detection feasibility. |
| Domain and clinical generalization | **VERIFIED** source is curated scanned-film DDSM; **INFERRED** generalization risk | High | [TCIA](https://www.cancerimagingarchive.net/collection/cbis-ddsm/) describes digitized film and its selection. Performance on current digital mammography, other sites, or clinical populations remains unverified. No medical-grade claim. |
| Storage, bandwidth, and decoding | **VERIFIED** whole collection is 163.51 GB; **UNVERIFIED** mass-only need | Medium–High | Download only selected series; inspect portal size and measure smoke-test bytes. Check DICOM decoder compatibility and working-copy headroom. [TCIA size](https://www.cancerimagingarchive.net/collection/cbis-ddsm/), [NBIA guide](https://wiki.cancerimagingarchive.net/display/NBIA/NBIA+Data+Retriever+Command-Line+Interface+Guide). |
| Privacy and redistribution | **VERIFIED** TCIA policy; **UNVERIFIED** planned deployment controls | High | No identification/contact attempts. Decide ethics review and public prototype image policy before exposure. [TCIA usage policy](https://wiki.cancerimagingarchive.net/display/Public/Data+Usage+Policies+and+Restrictions). |
| Scope in 6–7 months for three students | **INFERRED** | High | Classification, detection, segmentation, XAI, and deployment each need separate validation. Gate scope after smoke-test mapping and compute estimates; prioritize one defensible primary task. |

## Stop conditions for the smoke test

- Any uncertainty about whether the chosen source is TCIA's official material or whether terms can be met.
- No reliable participant key or unresolvable participant overlap in the intended evaluation partition.
- Full-image/ROI alignment cannot be validated for representative cases, or masks cannot be reliably distinguished from crops.
- Available storage or bandwidth cannot accommodate selected series with safe headroom.

## Evidence links

- [Official CBIS-DDSM collection](https://www.cancerimagingarchive.net/collection/cbis-ddsm/)
- [TFDS path and mask checks](https://github.com/tensorflow/datasets/blob/master/tensorflow_datasets/image_classification/cbis_ddsm.py#L3128-L3175)
- [TCIA policy](https://wiki.cancerimagingarchive.net/display/Public/Data+Usage+Policies+and+Restrictions)

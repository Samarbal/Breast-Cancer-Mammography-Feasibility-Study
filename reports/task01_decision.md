# TASK-01 — feasibility decision for human review

Audit date: 2026-11-05. **Decision: CONDITIONAL GO** for a tightly bounded, official-source **10–20-case data smoke test**. This is not a commitment to the graduation project or approval to train or deploy a medical model.

## VERIFIED

- [TCIA](https://www.cancerimagingarchive.net/collection/cbis-ddsm/) supplies a versioned CC BY 3.0 CBIS-DDSM collection, mass train/test CSVs, and separate full-mammogram and ROI/crop image manifests.
- The published material is technically relevant to mass classification and potentially to detection/segmentation, while TCIA warns that DICOM patient IDs overcount actual participants. The [TFDS builder](https://github.com/tensorflow/datasets/blob/master/tensorflow_datasets/image_classification/cbis_ddsm.py#L3128-L3175) documents a mask/crop mapping hazard.
- [TCIA policy](https://wiki.cancerimagingarchive.net/display/Public/Data+Usage+Policies+and+Restrictions) requires dataset/repository attribution and prohibits attempts to identify or contact participants.

## INFERRED

- A small official-source download should reveal whether this team's environment can decode DICOM, resolve CSV references, distinguish masks from crops, and verify ROI alignment at manageable cost. It does not estimate final accuracy.
- The five proposed workstreams are likely too broad without a prioritized primary endpoint and later scope gate.

## UNVERIFIED — blocking issues for a full project GO

1. **Participant split integrity:** actual overlap between train and test, and an enforceable participant-level validation policy.
2. **Annotation integrity:** measured CSV path resolution and accepted, full-image-aligned binary mass mask rate.
3. **Task definition:** lesion-level classification vs whole-image classification; valid negatives for detection; treatment of multiple/discordant lesions.
4. **Resources:** actual mass subset size, local storage/bandwidth, DICOM decoding, and realistic compute/time budget.
5. **Permissions for a public prototype:** institutional ethics determination and whether any images/derivatives would be exposed.

These are blockers to **project commitment and performance claims**, not to the read-only source audit completed here.

## Evidence links

- [Official TCIA collection, Version 1, manifests, citation](https://www.cancerimagingarchive.net/collection/cbis-ddsm/)
- [TCIA usage policy](https://wiki.cancerimagingarchive.net/display/Public/Data+Usage+Policies+and+Restrictions)
- [CC BY 3.0](https://creativecommons.org/licenses/by/3.0/)
- [NBIA Data Retriever guide](https://wiki.cancerimagingarchive.net/display/NBIA/NBIA+Data+Retriever+Command-Line+Interface+Guide)
- [TFDS CBIS-DDSM mapping code](https://github.com/tensorflow/datasets/blob/master/tensorflow_datasets/image_classification/cbis_ddsm.py#L3084-L3175)

## Recommended next task

After human review and **explicit approval**, run a bounded TASK-02 data smoke test: acquire the two official mass CSVs and only 10–20 selected training cases with matching full-image/ROI/crop series; report hashes, bytes, participant overlap, path/mask acceptance rates, and representative overlays. Do not train a model or download the full dataset at that stage.

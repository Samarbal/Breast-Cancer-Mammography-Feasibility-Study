# Final feasibility gate — TASK-04/05

**Review date:** 2026-11-05. **Overall recommendation: CONDITIONAL GO for a research-only graduation project proposal; NO-GO for an unconditional commitment to three equal-weight tasks or a clinical-use claim.** This gate closes the bounded feasibility audit. No model was trained, no full dataset was downloaded, and TASK-04/05 acquired no additional images.

## VERIFIED evidence

| Research task | Evidence established in this workspace | Task gate |
| --- | --- | --- |
| **Classification** | The official CBIS-DDSM mass CSVs contain 1,696 lesion-view rows. Train/test have **zero shared `P_#####` participants**. A strict `MALIGNANT` versus `BENIGN` policy leaves **1,555 candidate rows**; `BENIGN_WITHOUT_CALLBACK` is excluded from the primary endpoint. Some full images contain multiple lesions and mixed pathology, so a whole-image binary label is not justified. [TASK-03](task03_feasibility.md). | **CONDITIONAL GO** for ROI-linked, single-view lesion classification with participant-held-out evaluation and further pixel mapping checks. |
| **Detection** | CBIS-DDSM mass CSVs have no verified normal/zero-mass exam cohort. Official [VinDr-Mammo v1.0.0](https://physionet.org/content/vindr-mammo/1.0.0/) offers radiologist-assessed BI-RADS-1 breasts and mass boxes in a 5,000-exam digital dataset, but access is restricted under the [current PhysioNet license](https://physionet.org/content/vindr-mammo/view-license/1.0.0/). Its annotations target findings needing further examination, with benign BI-RADS-2 findings deliberately unboxed. [TASK-04](task04_detection_feasibility.md). | **CONDITIONAL GO** only for a separately defined *suspicious-mass localization* task after authorized access and a verified normal cohort. **NO-GO** for CBIS-only screening false-positive/specificity claims. |
| **Segmentation** | The 12 locally acquired CBIS cases supplied **12/12 decodable, nonempty, full-image-sized masks** and bounding boxes. A fresh-process CPU probe completed all 12 in **0.304–1.008 s/case** after imports, with **310–668 MB** peak process RAM; all retained nonempty masks at longest side 1,024 pixels. [TASK-05](task05_segmentation_compute.md), [measurements](../data/cbis_ddsm/task05_benchmark.json). | **CONDITIONAL GO** for agreement with source ROI masks, pending broader pixel/contour and multi-lesion audits plus hardware planning. |

**Dataset compatibility:** CBIS-DDSM is digitized film with pathology categories and segmentation masks; VinDr is full-field digital mammography with BI-RADS assessments and finding boxes. Their labels, lesion coverage, imaging domains, and evaluation units differ. A single pooled “mass detection” test set or direct benign/malignant label transfer is **not** established. Any cross-domain analysis must be separate and explicitly exploratory. [TCIA collection](https://www.cancerimagingarchive.net/collection/cbis-ddsm/); [VinDr dataset paper](https://doi.org/10.1038/s41597-023-02100-7).

## INFERRED project definition if gates clear

Treat the three research tasks as **separate, equally reported endpoints**, each with its own data, labels, exclusions, split, and uncertainty estimate:

1. **Classification:** CBIS-DDSM ROI-linked lesion in one view; malignant versus benign source labels; participant-grouped train/validation/test; report `BENIGN_WITHOUT_CALLBACK` only in a named sensitivity analysis. Metrics describe annotation-level classification, not screening diagnosis.
2. **Detection:** VinDr radiologist-marked suspicious masses; affirmative BI-RADS-1 breasts/exams for false-alarm analysis after CSV reconciliation. Use its provided held-out test split, an exam-held-out validation split, predeclared localization matching and FROC/false positives per image or exam, and exam-clustered confidence intervals. Report CBIS localization separately.
3. **Segmentation:** CBIS per-annotation mass ROI overlap, with participant-grouped evaluation and explicit handling of multiple masks on one image. Report Dice/IoU and contour-sensitive metrics against the supplied masks, which are a source annotation reference rather than clinical boundary truth.

Grad-CAM may be used as **qualitative model-behavior inspection** after a later approved implementation; it is not evidence of causal explanation or clinical trustworthiness. A prototype should display research-only outputs and the task/dataset limits. Public access to restricted VinDr images, annotations, or derivatives cannot be assumed under its license. Prototype publication and any clinical-facing use require separate institutional and license review.

## UNVERIFIED / blocking issues for a full project GO

| Blocker | Required evidence or decision before implementation | Failure trigger |
| --- | --- | --- |
| **VinDr access and negative cohort** | Confirm that all three students can lawfully access/work with the restricted data; inspect the authorized CSVs to count complete BI-RADS-1 exams, repeated-patient linkage, box validity, and image decoding. Freeze the suspicious-mass evaluation definition. | If access or a clean affirmative normal cohort is unavailable in the project's early planning window, the three-task equal-weight scope is **NO-GO**; MIAS is too small for a comparable primary digital detection benchmark, and OMI-DB access is unconfirmed. |
| **CBIS annotation completeness** | Conduct a bounded pixel audit of mixed-pathology, multi-lesion, small/edge, and split-series ROI cases. Establish whether all masks for a full image are accounted for before whole-image segmentation scoring. | If crop/mask identity or complete lesion coverage cannot be resolved at a predeclared acceptable rate, narrow to verified ROI cases or **NO-GO** for whole-image segmentation. |
| **Compute and storage** | Identify actual available GPU, RAM, disk, and time; perform a later bounded GPU memory/runtime probe on approved training code. Plan originals plus working space. | The present **~77.4 GB free** is below the TASK-03 **~81.9 GB** mass-DICOM planning estimate before working copies. Without a viable storage/compute plan, a three-task implementation is **NO-GO**. |
| **Reference standard and external validity** | Document benign-label provenance, VinDr's lack of pathology/follow-up confirmation, reader-label limitations, and film-to-digital shift in every analysis and presentation. | Any requirement to claim pathology-confirmed cancer screening performance or medical-grade deployment is **NO-GO** on the audited evidence. |
| **Schedule and scope** | Allocate time for three independent data pipelines/evaluations, annotation QA, XAI review, and a research prototype; define a fallback before starting. | If the team cannot reserve enough time for all three independently valid endpoints within 6–7 months, reduce scope through human review rather than report an invalid endpoint. |

## Final recommendation and next task

**CONDITIONAL GO** to the project *only as a research feasibility proposal* with classification, suspicious-mass detection, and source-mask segmentation as distinct equal-weight endpoints. **Implementation is gated** on authorized VinDr access and confirmed normal-exam metadata, complete CBIS mask policy, and a concrete storage/GPU plan. If those gates fail, the full three-task proposal is **NO-GO**; the team should choose a smaller scope at a new human decision gate. No medical-grade feasibility is claimed.

**Recommended next task, only after human approval:** a short, bounded gate-resolution phase: pursue institutional/individual VinDr access; audit its metadata and a small authorized image sample; review selected CBIS mixed/multi-lesion masks; and run a limited hardware probe. Predeclare acceptance thresholds and stop if the detection access/negative-label gate fails. Do not start model training or prototype implementation from this report alone.

### Evidence links

- [TASK-01 licensing decision](task01_decision.md), [TASK-02 official-source smoke test](task02_smoke_test.md), [TASK-03 annotation audit](task03_feasibility.md)
- [TASK-04 detection source/terms audit](task04_detection_feasibility.md), [TASK-05 measured benchmark](task05_segmentation_compute.md)
- [Official TCIA CBIS-DDSM collection](https://www.cancerimagingarchive.net/collection/cbis-ddsm/)
- [Official VinDr-Mammo v1.0.0](https://physionet.org/content/vindr-mammo/1.0.0/), [PhysioNet restricted license](https://physionet.org/content/vindr-mammo/view-license/1.0.0/), [dataset authors' paper](https://doi.org/10.1038/s41597-023-02100-7)
- [Official Cambridge MIAS v1.21 record](https://www.repository.cam.ac.uk/items/b6a97f0c-3b9b-40ad-8f18-3d121eef1459), [official OMI-DB access process](https://medphys.royalsurrey.nhs.uk/omidb/what-is-the-process/)

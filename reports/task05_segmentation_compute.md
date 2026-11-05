# TASK-05 — segmentation and compute benchmark

**Benchmark date:** 2026-11-05. **Decision: CONDITIONAL GO** for research segmentation prototyping on the validated CBIS-DDSM masks; **NO-GO** for claiming dataset-wide mask quality, mixed-pathology robustness, or GPU training feasibility from this 12-case test.

## Scope, provenance, and method

Reused the **12 official TCIA CBIS-DDSM training cases** and 24 source ZIPs preserved in [TASK-02](task02_smoke_test.md). No new DICOM files were downloaded, original files were not modified, and no model was trained. The read-only benchmark is [task05_benchmark.py](../scripts/task05_benchmark.py); per-case measurements are in [task05_benchmark.json](../data/cbis_ddsm/task05_benchmark.json). The [TASK-02 overlays](figures/task02_contact_sheet.png) provide the existing visual evidence.

Each case ran in a **fresh Windows process** using Python 3.13.14, pydicom 3.0.2, NumPy 2.5.4, and Pillow 13.0.0. Steps: read the full-image and ROI/crop ZIPs; parse DICOMs and decode pixels; identify the mask by DICOM description and full-image dimensions; verify two-valued nonempty mask; derive full-resolution `(x0,y0,x1,y1)` box; percentile-window positive image pixels at 1st/99.5th percentiles to uint8; resize the longest dimension to 1,024 pixels (bilinear image, nearest-neighbor mask); and compare the resized mask box with projected original coordinates. The resize is a **compute probe**, not an endorsed training resolution.

RAM was measured with Windows `GetProcessMemoryInfo`: process **peak working set**, including the Python runtime and NumPy/Pillow allocations. Wall times use `time.perf_counter()` **after imports** with files already in the OS cache. These numbers are local CPU measurements, not cold-download, GPU, training, or concurrent-worker benchmarks.

## VERIFIED — results

| Check | Result |
| --- | --- |
| DICOM read and pixel decode | **12/12 cases**, 36/36 DICOM objects; TASK-02 also verified all 36 supplied MD5 hashes. |
| Full-image to mask dimensions and identity | **12/12** masks matched full-image shape and selected DICOM patient/view; mask values were two-valued and foreground nonempty. |
| Full-resolution bounding box | **12/12** in bounds; foreground occupied **0.0257%–1.3581%** of full pixels. |
| Resize geometry | **12/12** masks stayed nonempty at longest side 1,024 pixels; resized boxes differed from projected full-resolution boxes by **at most 2 pixels**. |
| Per-case CPU time, after imports | **0.304–1.008 s**, median **0.538 s**. Median ZIP/DICOM parse **0.148 s**, pixel decode **0.012 s**, mask/box checks **0.097 s**, window/resize **0.278 s**. |
| Peak process RAM | **310–668 MB** (decimal), median **463 MB**. Peak above post-import baseline ranged **266–624 MB**, median **419 MB**. |
| Largest sampled full image | **6,796 × 3,361 = 22.84 million pixels**; one uint16 array is **45.7 MB**, one float32 array **91.4 MB** before temporary arrays, masks, or model activations. |

The CPU preprocessing peak is much larger than one decoded image because percentile calculation, float32 normalization, uint8 conversion, mask arrays, and resizing can coexist. It is **pipeline-specific** and cannot be read as a GPU training requirement. D: had about **77.4 GB free** at this gate; TASK-03's metadata-based estimate for all mass DICOMs was **~82 GB**, before working copies. [TASK-03 resource method](task03_feasibility.md).

## Challenging existing cases

| Case | Why it matters | Measured observation |
| --- | --- | --- |
| **P_00106 CC** | Small posterior/edge-adjacent `BENIGN_WITHOUT_CALLBACK` lymph-node annotation; its full-image path appears in **3 CSV lesion rows**, but only the selected ROI series was downloaded. | **5,797** foreground pixels (**0.0257%**) at full size; **185** pixels after resize; bbox projection delta **2 px**; peak **651 MB**. Other same-image lesions cannot be treated as background. [Overlay](figures/task02_P_00106_CC_overlay.png). |
| **P_00041 CC** | Another small mass mask. | **14,438** foreground pixels (**0.0640%**); **469** after resize; longest measured preprocessing time **1.008 s**; peak **655 MB**. [Overlay](figures/task02_P_00041_CC_overlay.png). |
| **P_00064 MLO** | Largest mask fraction in the 12-case set. | **175,390** foreground pixels (**1.3581%**); **8,853** after resize; projection delta **2 px**. [Overlay](figures/task02_P_00064_MLO_overlay.png). |
| **P_00026 MLO** | Largest full-resolution image in the sample. | **22.84 million pixels**; highest measured peak **668 MB**; total **0.888 s**. [Overlay](figures/task02_P_00026_MLO_overlay.png). |

**Mixed-pathology gap:** none of the 12 downloaded participants or selected full images has mixed pathology in the official mass training CSV. The [TASK-03 complete CSV audit](task03_feasibility.md) identified **6 training and 2 test full-image paths** with mixed pathology, but their pixels are not in the TASK-02 files. Under the no-new-download instruction, their mask separation and annotation mapping remain **UNVERIFIED**. P_00106 is a **multi-lesion, same-label** example, not a mixed-pathology substitute.

## INFERRED — segmentation task boundary and compute plan

- A defensible research target is **per-annotation mass mask overlap with the supplied CBIS-DDSM ROI**, using one full mammogram and the corresponding mask. Dice/IoU and boundary errors would describe agreement with that source annotation, **not** clinical contour truth. Keep all participant views/lesions in one evaluation split and report patient-clustered uncertainty.
- The 1,024-pixel probe retained every sampled mask, but P_00106 shrank to **185 pixels** of foreground. Fine borders and small lesions may be lost; any final input resolution, tiling, or crop strategy needs a predeclared geometric and visual check. This benchmark does not select a model architecture or training resolution.
- Multiple full-resolution cases processed concurrently can multiply the **310–668 MB** single-worker RAM footprint; training adds model activations and optimizer state. GPU memory, batch size, epoch time, and full-dataset throughput remain **unmeasured**. A storage plan must also account for originals, working copies, and derived masks; the present D: free space is below the ~82 GB mass-only DICOM point estimate.

## UNVERIFIED / blockers

1. **Expert contour quality:** shape equality, binary values, in-bounds boxes, and plausible overlays do not prove radiologist-acceptable boundaries. No expert review occurred.
2. **Dataset-wide mask validity:** only 12 masks were decoded; TASK-03's 96-row additional check was metadata-only. The separate-series ROI/crop layout seen in 3 of those 96 rows was not pixel-tested.
3. **Mixed-pathology and complete multi-lesion targets:** no downloaded mixed-pathology case; only one of P_00106's three same-image ROI series is local. Whole-image segmentation evaluation requires collecting and reconciling **all** relevant lesion masks, not treating missing ones as background.
4. **Training compute:** CPU preprocessing timings do not establish feasible GPU training, hyperparameter search, or deployment latency. Hardware-dependent benchmarking and available GPU memory remain pending.
5. **Generalization:** CBIS-DDSM is digitized film; this test says nothing about contour quality or model performance on modern digital mammography. [Official collection description](https://www.cancerimagingarchive.net/collection/cbis-ddsm/).

## Gate

**CONDITIONAL GO** for a research segmentation task with source-ROI evaluation and explicit data-quality exclusions. Before committing to it as an equal-weight project task, obtain a bounded expert/mixed-lesion pixel audit, a complete-mask policy for multi-lesion images, sufficient storage, and a separate GPU runtime/memory benchmark. No additional images were downloaded for TASK-05.

### Evidence links

- [TASK-02 official-source DICOM integrity and overlays](task02_smoke_test.md)
- [TASK-03 CSV/metadata audit and mass storage estimate](task03_feasibility.md)
- [TCIA CBIS-DDSM mass ROI and curation description](https://www.cancerimagingarchive.net/collection/cbis-ddsm/)

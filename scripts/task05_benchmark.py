"""Bounded, read-only DICOM/segmentation preprocessing benchmark for TASK-02 cases.

Each case runs in a separate process to measure Windows peak working set without
carryover from earlier cases. No model training and no changes to source ZIPs.
"""

import ctypes
import io
import json
import subprocess
import sys
import time
import zipfile
from pathlib import Path

import numpy as np
import pydicom
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data" / "cbis_ddsm"
PLAN = json.loads((BASE / "task02_selection.json").read_text(encoding="utf-8"))["selected"]
ZIP_DIR = BASE / "original" / "series_zips"
OUT = BASE / "task05_benchmark.json"


class ProcessMemoryCounters(ctypes.Structure):
    _fields_ = [
        ("cb", ctypes.c_uint32), ("PageFaultCount", ctypes.c_uint32),
        ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t),
    ]


def memory():
    counters = ProcessMemoryCounters()
    counters.cb = ctypes.sizeof(counters)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    psapi = ctypes.WinDLL("psapi", use_last_error=True)
    kernel.GetCurrentProcess.restype = ctypes.c_void_p
    psapi.GetProcessMemoryInfo.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint32]
    if not psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(), ctypes.byref(counters), counters.cb):
        raise OSError(ctypes.get_last_error(), "GetProcessMemoryInfo failed")
    return {"working_set_bytes": int(counters.WorkingSetSize),
            "peak_working_set_bytes": int(counters.PeakWorkingSetSize)}


def load_zip(uid):
    with zipfile.ZipFile(ZIP_DIR / (uid + ".zip")) as archive:
        return [pydicom.dcmread(io.BytesIO(archive.read(name)))
                for name in archive.namelist() if name.lower().endswith(".dcm")]


def bbox(binary):
    yy, xx = np.where(binary)
    if not yy.size:
        raise ValueError("Empty binary mask")
    return [int(xx.min()), int(yy.min()), int(xx.max()), int(yy.max())]


def work(row):
    start = time.perf_counter()
    baseline = memory()
    full_ds = load_zip(row["full_series_uid"])
    roi_ds = load_zip(row["roi_series_uid"])
    loaded = time.perf_counter()
    if len(full_ds) != 1 or len(roi_ds) != 2:
        raise ValueError("Expected one full DICOM and two ROI/crop DICOMs")
    full = full_ds[0].pixel_array
    candidates = [(ds, ds.pixel_array) for ds in roi_ds]
    decoded = time.perf_counter()
    masks = [(ds, pixels) for ds, pixels in candidates
             if pixels.shape == full.shape and "ROI mask" in str(ds.get("SeriesDescription", ""))]
    if len(masks) != 1:
        raise ValueError(f"Found {len(masks)} mask candidates")
    mask = masks[0][1] > 0
    other = [(ds, pixels) for ds, pixels in candidates if ds is not masks[0][0]]
    if len(other) != 1 or "cropped" not in str(other[0][0].get("SeriesDescription", "")):
        raise ValueError("Missing crop candidate")
    if np.unique(masks[0][1]).size != 2:
        raise ValueError("Mask is not two-valued")
    original_bbox = bbox(mask)
    checked = time.perf_counter()
    after_decode = memory()

    # Controlled preprocessing comparison: full-image percentile window to
    # uint8; shrink longest dimension to 1024; nearest-neighbor for mask.
    positive = full[full > 0]
    low, high = np.percentile(positive, [1, 99.5])
    if high <= low:
        raise ValueError("Degenerate intensity window")
    normalized = np.uint8(np.clip((full.astype(np.float32) - low) * (255.0 / (high - low)), 0, 255))
    scale = 1024 / max(full.shape)
    target_w = max(1, round(full.shape[1] * scale))
    target_h = max(1, round(full.shape[0] * scale))
    small_image = Image.fromarray(normalized).resize((target_w, target_h), Image.Resampling.BILINEAR)
    small_mask = Image.fromarray(np.uint8(mask) * 255).resize((target_w, target_h), Image.Resampling.NEAREST)
    small_binary = np.asarray(small_mask) > 0
    small_bbox = bbox(small_binary)
    processed = time.perf_counter()
    after_preprocess = memory()
    sx, sy = target_w / full.shape[1], target_h / full.shape[0]
    projected = [round(original_bbox[0] * sx), round(original_bbox[1] * sy),
                 round(original_bbox[2] * sx), round(original_bbox[3] * sy)]
    max_bbox_delta = max(abs(a - b) for a, b in zip(projected, small_bbox))
    return {
        "patient_id": row["patient_id"], "view": row["view"], "pathology": row["pathology"],
        "full_shape_hw": list(full.shape), "crop_shape_hw": list(other[0][1].shape),
        "mask_unique_values": [int(x) for x in np.unique(masks[0][1])],
        "mask_area_pixels": int(mask.sum()), "mask_fraction": float(mask.mean()),
        "bbox_xyxy_inclusive": original_bbox,
        "resized_shape_hw": [target_h, target_w], "resized_mask_area_pixels": int(small_binary.sum()),
        "resized_bbox_xyxy_inclusive": small_bbox, "resized_bbox_max_projection_delta_px": max_bbox_delta,
        "intensity_window_p1_p995": [float(low), float(high)],
        "timings_seconds": {"zip_and_dicom_read": loaded - start, "pixel_decode": decoded - loaded,
                            "mask_and_bbox_check": checked - decoded,
                            "normalize_and_resize": processed - checked,
                            "total": processed - start},
        "memory_bytes": {"baseline_working_set": baseline["working_set_bytes"],
                         "after_decode_working_set": after_decode["working_set_bytes"],
                         "after_preprocess_working_set": after_preprocess["working_set_bytes"],
                         "process_peak_working_set": after_preprocess["peak_working_set_bytes"]},
        "status": "pass" if max_bbox_delta <= 2 else "geometry_check_fail",
    }


if len(sys.argv) == 3 and sys.argv[1] == "--worker":
    row = next(x for x in PLAN if x["patient_id"] == sys.argv[2])
    print(json.dumps(work(row)))
elif len(sys.argv) == 1:
    cases = []
    for row in PLAN:
        process = subprocess.run([sys.executable, __file__, "--worker", row["patient_id"]],
                                 capture_output=True, text=True, check=False)
        if process.returncode:
            result = {"patient_id": row["patient_id"], "status": "error", "stderr": process.stderr}
        else:
            result = json.loads(process.stdout)
        cases.append(result)
        print(row["patient_id"], result["status"], result.get("timings_seconds", {}).get("total"), flush=True)
    OUT.write_text(json.dumps({"method": "fresh subprocess per case; cached files; CPU-only in-memory preprocessing",
                               "python": sys.version, "pydicom": pydicom.__version__,
                               "numpy": np.__version__, "pillow": Image.__version__,
                               "cases": cases}, indent=2) + "\n", encoding="utf-8")
    print("PASSED", sum(x["status"] == "pass" for x in cases), "/", len(cases))
else:
    raise SystemExit("Usage: task05_benchmark.py [--worker P_#####]")

"""Planning estimates from TASK-03 official metadata sample and TASK-02 pixels.

These are extrapolations, not measured full-dataset resource requirements.
"""

import json
import random
import statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data" / "cbis_ddsm"
AUDIT = json.loads((BASE / "task03_annotation_audit.json").read_text(encoding="utf-8"))
META = json.loads((BASE / "task03_metadata_audit.json").read_text(encoding="utf-8"))
SMOKE = json.loads((BASE / "task02_validation.json").read_text(encoding="utf-8"))
OUT = BASE / "task03_estimates.json"

series = {uid: value["metadata"] for uid, value in META["series_results"].items()}
strata = defaultdict(list)
for row in AUDIT["sample"]:
    full = int(series[row["full_series_uid"]]["File Size"])
    roi = int(series[row["roi_series_uid"]]["File Size"])
    crop_extra = int(series[row["crop_series_uid"]]["File Size"]) if row["crop_series_uid"] != row["roi_series_uid"] else 0
    strata[(row["split"], row["pathology"], row["view"])].append({"full_bytes": full, "roi_crop_bytes": roi + crop_extra})

by_split = {}
for split in ("train", "test"):
    population_rows = AUDIT["stats"][split]["rows"]
    unique_full = AUDIT["stats"][split]["distinct_full_series"]
    weighted_full_per_row = 0
    roi_total = 0
    for (part, pathology, view), values in strata.items():
        if part != split:
            continue
        count = AUDIT["strata_sizes"]["|".join((part, pathology, view))]
        weighted_full_per_row += count * statistics.mean(x["full_bytes"] for x in values)
        roi_total += count * statistics.mean(x["roi_crop_bytes"] for x in values)
    weighted_full_per_row /= population_rows
    full_total = round(weighted_full_per_row * unique_full)
    by_split[split] = {"population_rows": population_rows, "unique_full_series": unique_full,
                       "estimated_full_bytes": full_total, "estimated_roi_crop_bytes": round(roi_total),
                       "estimated_total_bytes": full_total + round(roi_total)}

# Descriptive resampling interval for the metadata sample only. It excludes
# selection bias, transfer failures, and working-copy/storage overhead.
rng = random.Random(20261105)
bootstrap_totals = []
for _ in range(2000):
    total = 0.0
    for split in ("train", "test"):
        pop_rows = AUDIT["stats"][split]["rows"]
        unique_full = AUDIT["stats"][split]["distinct_full_series"]
        full_weighted = roi_weighted = 0.0
        for key, values in strata.items():
            if key[0] != split:
                continue
            count = AUDIT["strata_sizes"]["|".join(key)]
            chosen = [rng.choice(values) for _ in values]
            full_weighted += count * statistics.mean(x["full_bytes"] for x in chosen)
            roi_weighted += count * statistics.mean(x["roi_crop_bytes"] for x in chosen)
        total += (full_weighted / pop_rows) * unique_full + roi_weighted
    bootstrap_totals.append(total)
bootstrap_totals.sort()

crop_sizes = [next(f for f in row["roi_files"] if f["name"] == row["crop_file"])["bytes"] for row in SMOKE]
full_pixel_counts = [row["full_files"][0]["rows"] * row["full_files"][0]["cols"] for row in SMOKE]
result = {
    "method": "Eight-row mean per split/pathology/view stratum, weighted by all CSV rows; unique full-series correction by split. ROI/crop estimate is row-weighted. This assumes sampled sizes represent each stratum.",
    "sample_rows": len(AUDIT["sample"]),
    "sample_unique_series": META["unique_series"],
    "by_split": by_split,
    "estimated_mass_dicom_bytes": sum(x["estimated_total_bytes"] for x in by_split.values()),
    "metadata_sample_bootstrap_95pct_bytes": [round(bootstrap_totals[50]), round(bootstrap_totals[1949])],
    "task02_crop_bytes": {"min": min(crop_sizes), "median": int(statistics.median(crop_sizes)), "max": max(crop_sizes)},
    "task02_full_pixels": {"min": min(full_pixel_counts), "median": int(statistics.median(full_pixel_counts)), "max": max(full_pixel_counts)},
    "task02_uint16_full_bytes_at_max_pixels": max(full_pixel_counts) * 2,
    "task02_float32_full_bytes_at_max_pixels": max(full_pixel_counts) * 4,
}
OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2))

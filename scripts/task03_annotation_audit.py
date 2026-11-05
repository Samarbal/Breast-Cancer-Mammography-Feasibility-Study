"""Read-only CBIS-DDSM mass CSV audit and deterministic metadata sample.

The 96-row sample is eight distinct participants per split/pathology/view stratum,
ranked by SHA-256 with a fixed seed. No image download or model work.
"""

import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data" / "cbis_ddsm"
ORIGINAL = BASE / "original"
OUTPUT = BASE / "task03_annotation_audit.json"
SEED = "TASK03-CBIS-DDSM-20261105-v1"
UID_RE = re.compile(r"^[0-9]+(?:\.[0-9]+)+$")


def read(split):
    path = ORIGINAL / f"mass_case_description_{split}_set.csv"
    with path.open(newline="", encoding="utf-8-sig") as stream:
        raw = list(csv.DictReader(stream))
    return [{k: v.strip() for k, v in row.items()} for row in raw]


rows_by_split = {split: read(split) for split in ("train", "test")}
all_rows = [(split, row) for split, rows in rows_by_split.items() for row in rows]
keys = ("image file path", "cropped image file path", "ROI mask file path")


def series(path):
    parts = path.split("/")
    if len(parts) != 4 or not UID_RE.fullmatch(parts[-2]) or not UID_RE.fullmatch(parts[-3]):
        return None
    return parts[-2]


def record_key(row):
    return (row["patient_id"], row["left or right breast"], row["image view"],
            row["abnormality id"], row["image file path"], row["ROI mask file path"])


def lesion_key(row):
    return (row["patient_id"], row["left or right breast"], row["abnormality id"])


def stats(rows):
    image_labels, participant_labels, lesion_labels = defaultdict(set), defaultdict(set), defaultdict(set)
    lesion_views = defaultdict(set)
    image_lesions = defaultdict(set)
    lesion_view_rows = defaultdict(list)
    for row in rows:
        image_labels[row["image file path"]].add(row["pathology"])
        participant_labels[row["patient_id"]].add(row["pathology"])
        lesion_labels[lesion_key(row)].add(row["pathology"])
        lesion_views[lesion_key(row)].add(row["image view"])
        image_lesions[row["image file path"]].add(lesion_key(row))
        lesion_view_rows[(lesion_key(row), row["image view"])].append(row)
    strict_lesions = {key: next(iter(labels)) for key, labels in lesion_labels.items()
                      if len(labels) == 1 and not (labels & {"BENIGN_WITHOUT_CALLBACK"})}
    mapped_lesions = {key: {"BENIGN" if label == "BENIGN_WITHOUT_CALLBACK" else label for label in labels}
                      for key, labels in lesion_labels.items()}
    return {
        "rows": len(rows),
        "participants": len(participant_labels),
        "full_images": len(image_labels),
        "candidate_cross_view_lesion_keys": len(lesion_labels),
        "pathology_rows": dict(Counter(row["pathology"] for row in rows)),
        "view_rows": dict(Counter(row["image view"] for row in rows)),
        "candidate_keys_with_both_views": sum(len(v) == 2 for v in lesion_views.values()),
        "candidate_keys_with_conflicting_pathology": sum(len(v) > 1 for v in lesion_labels.values()),
        "candidate_strict_binary_eligible_keys": len(strict_lesions),
        "candidate_strict_binary_by_label": dict(Counter(strict_lesions.values())),
        "candidate_inclusive_binary_eligible_keys": sum(len(v) == 1 for v in mapped_lesions.values()),
        "lesion_view_groups_with_multiple_rows": sum(len(v) > 1 for v in lesion_view_rows.values()),
        "full_images_with_multiple_lesions": sum(len(v) > 1 for v in image_lesions.values()),
        "full_images_with_mixed_pathology": sum(len(v) > 1 for v in image_labels.values()),
        "participants_with_mixed_pathology": sum(len(v) > 1 for v in participant_labels.values()),
        "exact_duplicate_records": len(rows) - len({record_key(row) for row in rows}),
        "empty_fields": {k: sum(not row[k] for row in rows) for k in rows[0]},
        "invalid_path_shapes": {k: sum(series(row[k]) is None for row in rows) for k in keys},
        "roi_crop_series_mismatch": sum(series(row["ROI mask file path"]) != series(row["cropped image file path"]) for row in rows),
        "roi_crop_patient_prefix_mismatch": sum(row["ROI mask file path"].split("/")[0] != row["cropped image file path"].split("/")[0] for row in rows),
        "path_patient_prefix_mismatch": {k: sum(row["patient_id"] not in row[k].split("/")[0] for row in rows) for k in keys},
        "distinct_full_series": len({series(row["image file path"]) for row in rows}),
        "distinct_roi_series": len({series(row["ROI mask file path"]) for row in rows}),
        "distinct_roi_crop_series_union": len({series(row[k]) for row in rows for k in ("ROI mask file path", "cropped image file path")}),
    }


strata = defaultdict(list)
for split, row in all_rows:
    strata[(split, row["pathology"], row["image view"])].append(row)

sample = []
used_participants = set()
for stratum in sorted(strata):
    candidates = sorted(
        strata[stratum],
        key=lambda row: (hashlib.sha256((SEED + "|" + stratum[0] + "|" + "|".join(record_key(row))).encode()).hexdigest(),
                         record_key(row)),
    )
    chosen = []
    for row in candidates:
        if row["patient_id"] in used_participants:
            continue
        chosen.append(row)
        used_participants.add(row["patient_id"])
        if len(chosen) == 8:
            break
    if len(chosen) != 8:
        raise RuntimeError(f"Only {len(chosen)} distinct participants available in {stratum}")
    for row in chosen:
        sample.append({
            "split": stratum[0], "pathology": stratum[1], "view": stratum[2],
            "patient_id": row["patient_id"], "laterality": row["left or right breast"],
            "abnormality_id": row["abnormality id"],
            "full_patient_id": row["image file path"].split("/")[0],
            "roi_patient_id": row["ROI mask file path"].split("/")[0],
            "crop_patient_id": row["cropped image file path"].split("/")[0],
            "full_series_uid": series(row["image file path"]),
            "roi_series_uid": series(row["ROI mask file path"]),
            "crop_series_uid": series(row["cropped image file path"]),
        })

train_ids = {r["patient_id"] for r in rows_by_split["train"]}
test_ids = {r["patient_id"] for r in rows_by_split["test"]}
train_full = {r["image file path"] for r in rows_by_split["train"]}
test_full = {r["image file path"] for r in rows_by_split["test"]}
train_series = {series(r["image file path"]) for r in rows_by_split["train"]}
test_series = {series(r["image file path"]) for r in rows_by_split["test"]}
train_roi_series = {series(r["ROI mask file path"]) for r in rows_by_split["train"]}
test_roi_series = {series(r["ROI mask file path"]) for r in rows_by_split["test"]}
output = {
    "seed": SEED,
    "sample_method": "SHA-256 rank, eight unique participants per split/pathology/view stratum",
    "source_sha256": {split: hashlib.sha256((ORIGINAL / f"mass_case_description_{split}_set.csv").read_bytes()).hexdigest()
                      for split in rows_by_split},
    "stats": {split: stats(rows) for split, rows in rows_by_split.items()},
    "split_overlap": {
        "participant_ids": sorted(train_ids & test_ids),
        "full_paths": sorted(train_full & test_full),
        "full_series_uids": sorted(train_series & test_series),
        "roi_series_uids": sorted(train_roi_series & test_roi_series),
    },
    "strata_sizes": {"|".join(k): len(v) for k, v in sorted(strata.items())},
    "roi_crop_series_mismatch_examples": [
        {"split": split, "patient_id": row["patient_id"], "view": row["image view"],
         "abnormality_id": row["abnormality id"],
         "crop_path": row["cropped image file path"], "roi_path": row["ROI mask file path"]}
        for split, row in all_rows
        if series(row["cropped image file path"]) != series(row["ROI mask file path"])
    ][:10],
    "conflicting_lesion_key_examples": [
        {"split": split, "patient_id": key[0], "laterality": key[1], "abnormality_id": key[2],
         "pathologies": sorted({r["pathology"] for r in rows if lesion_key(r) == key})}
        for split, rows in rows_by_split.items()
        for key in sorted({lesion_key(r) for r in rows})
        if len({r["pathology"] for r in rows if lesion_key(r) == key}) > 1
    ],
    "sample": sample,
}
OUTPUT.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
print(json.dumps({k: output[k] for k in ("stats", "split_overlap", "strata_sizes", "sample_method")}, indent=2))
print("SAMPLED_RECORDS", len(sample), "UNIQUE_PARTICIPANTS", len(used_participants))
print("SAMPLE_ROI_CROP_MISMATCHES", sum(x["roi_series_uid"] != x["crop_series_uid"] for x in sample))

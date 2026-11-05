"""Read-only audit and deterministic small-sample selection of official CBIS-DDSM mass CSVs."""

import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "cbis_ddsm" / "original"
OUTPUT = ROOT / "data" / "cbis_ddsm" / "task02_selection.json"


def load(name):
    path = SOURCE / name
    with path.open(encoding="utf-8-sig", newline="") as stream:
        raw_rows = list(csv.DictReader(stream))
    whitespace_paths = {
        key: sum(r[key] != r[key].strip() for r in raw_rows)
        for key in ("image file path", "cropped image file path", "ROI mask file path")
    }
    rows = [{key: value.strip() for key, value in row.items()} for row in raw_rows]
    return rows, {"bytes": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                  "path_fields_with_outer_whitespace": whitespace_paths}


train, train_file = load("mass_case_description_train_set.csv")
test, test_file = load("mass_case_description_test_set.csv")
train_ids = {r["patient_id"].strip() for r in train}
test_ids = {r["patient_id"].strip() for r in test}


def stats(rows):
    labels_by_image = defaultdict(set)
    labels_by_participant = defaultdict(set)
    for row in rows:
        labels_by_image[row["image file path"]].add(row["pathology"])
        labels_by_participant[row["patient_id"]].add(row["pathology"])
    return {
        "rows": len(rows),
        "participants": len({r["patient_id"] for r in rows}),
        "pathology": dict(Counter(r["pathology"] for r in rows)),
        "view": dict(Counter(r["image view"] for r in rows)),
        "laterality": dict(Counter(r["left or right breast"] for r in rows)),
        "blank_paths": {key: sum(not r[key].strip() for r in rows) for key in ("image file path", "cropped image file path", "ROI mask file path")},
        "unique_full_paths": len({r["image file path"] for r in rows}),
        "unique_crop_paths": len({r["cropped image file path"] for r in rows}),
        "unique_mask_paths": len({r["ROI mask file path"] for r in rows}),
        "mixed_label_full_images": sum(len(v) > 1 for v in labels_by_image.values()),
        "mixed_label_participants": sum(len(v) > 1 for v in labels_by_participant.values()),
    }


# Select one lesion row per distinct participant, balancing three source pathology
# labels and both views. Stable lexicographic order makes the selection reproducible.
targets = {("MALIGNANT", "CC"): 2, ("MALIGNANT", "MLO"): 2,
           ("BENIGN", "CC"): 2, ("BENIGN", "MLO"): 2,
           ("BENIGN_WITHOUT_CALLBACK", "CC"): 2,
           ("BENIGN_WITHOUT_CALLBACK", "MLO"): 2}
selected = []
used = set()
for category, count in targets.items():
    candidates = sorted(
        (r for r in train if (r["pathology"], r["image view"]) == category),
        key=lambda r: (r["patient_id"], r["left or right breast"], r["abnormality id"]),
    )
    for row in candidates:
        if row["patient_id"] in used:
            continue
        selected.append(row)
        used.add(row["patient_id"])
        if sum((r["pathology"], r["image view"]) == category for r in selected) >= count:
            break


def series_uid(path):
    parts = path.split("/")
    return parts[-2] if len(parts) >= 3 else None


summary = {
    "source": {
        "train": {**train_file, **stats(train)},
        "test": {**test_file, **stats(test)},
    },
    "participant_overlap": sorted(train_ids & test_ids),
    "selected": [
        {"patient_id": r["patient_id"], "view": r["image view"],
         "laterality": r["left or right breast"], "abnormality_id": r["abnormality id"],
         "pathology": r["pathology"], "full_path": r["image file path"],
         "crop_path": r["cropped image file path"], "mask_path": r["ROI mask file path"],
         "full_series_uid": series_uid(r["image file path"]),
         "roi_series_uid": series_uid(r["ROI mask file path"])}
        for r in selected
    ],
}
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"source": summary["source"], "participant_overlap": summary["participant_overlap"],
                  "selected": [{k: r[k] for k in ("patient_id", "view", "pathology", "full_series_uid", "roi_series_uid")}
                               for r in summary["selected"]]}, indent=2))

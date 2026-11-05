"""Query official TCIA series metadata for the TASK-03 96-record CSV sample.

Metadata only: no DICOM image objects are downloaded.
"""

import json
import time
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data" / "cbis_ddsm"
AUDIT = json.loads((BASE / "task03_annotation_audit.json").read_text(encoding="utf-8"))
OUT = BASE / "task03_metadata_audit.json"
ENDPOINT = "https://services.cancerimagingarchive.net/nbia-api/services/v1/getSeriesMetaData?SeriesInstanceUID="

refs = {}
for row in AUDIT["sample"]:
    for kind in ("full", "roi", "crop"):
        uid = row[kind + "_series_uid"]
        refs.setdefault(uid, []).append({"split": row["split"], "patient_id": row["patient_id"],
                                         "view": row["view"], "kind": kind,
                                         "expected_subject_id": row[kind + "_patient_id"]})


def fetch(uid):
    error = None
    for attempt in range(3):
        try:
            request = urllib.request.Request(ENDPOINT + uid, headers={"User-Agent": "CBIS-DDSM-TASK03-Research/1.0"})
            with urllib.request.urlopen(request, timeout=90) as response:
                body = json.load(response)
            if len(body) != 1:
                raise ValueError(f"Expected one series metadata record, got {len(body)}")
            return uid, {"metadata": body[0], "error": None}
        except Exception as caught:
            error = str(caught)
            time.sleep(1 + attempt)
    return uid, {"metadata": None, "error": error}


if OUT.exists():
    prior = json.loads(OUT.read_text(encoding="utf-8"))
    if set(prior["series_results"]) == set(refs):
        results = prior["series_results"]
        print(f"Reusing {len(results)} previously fetched official TCIA metadata records", flush=True)
    else:
        raise RuntimeError("Existing metadata set does not match current sample; inspect before overwriting")
else:
    results = {}
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(fetch, uid) for uid in refs]
        for i, future in enumerate(as_completed(futures), 1):
            uid, result = future.result()
            results[uid] = {"references": refs[uid], **result}
            if i % 20 == 0 or result["error"]:
                print(f"{i}/{len(refs)} series checked; latest_error={result['error']}", flush=True)

checked = []
for row in AUDIT["sample"]:
    record = {k: row[k] for k in ("split", "patient_id", "view", "pathology", "laterality", "abnormality_id")}
    checks = []
    for kind in ("full", "roi", "crop"):
        uid = row[kind + "_series_uid"]
        result = results[uid]
        meta = result["metadata"]
        expected_subject = row[kind + "_patient_id"]
        shared_roi_crop_series = row["roi_series_uid"] == row["crop_series_uid"]
        expected_description = ("full mammogram images" if kind == "full" else
                                "ROI mask images" if kind == "roi" or shared_roi_crop_series else "cropped images")
        expected_count = 1 if kind == "full" or (kind == "crop" and not shared_roi_crop_series) or (kind == "roi" and not shared_roi_crop_series) else 2
        checks.append({
            "kind": kind, "uid": uid,
            "exists": meta is not None,
            "collection_ok": bool(meta and meta.get("Collection") == "CBIS-DDSM"),
            "subject_ok": bool(meta and meta.get("Subject ID") == expected_subject),
            "description_ok": bool(meta and meta.get("Series Description", "").lower() == expected_description.lower()),
            "image_count": int(meta.get("Number of Images", 0)) if meta else None,
            "image_count_ok": bool(meta and int(meta.get("Number of Images", 0)) == expected_count),
            "file_size": int(meta.get("File Size", 0)) if meta else None,
            "error": result["error"],
        })
    record["checks"] = checks
    record["all_metadata_checks_ok"] = all(x["exists"] and x["collection_ok"] and
        x["subject_ok"] and x["description_ok"] and x["image_count_ok"] for x in checks)
    checked.append(record)

output = {"endpoint": ENDPOINT, "sample_seed": AUDIT["seed"], "unique_series": len(refs),
          "series_results": results, "sample_checks": checked}
OUT.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
print("SAMPLE_RECORDS_OK", sum(x["all_metadata_checks_ok"] for x in checked), "/", len(checked))
print("SERIES_DESCRIPTIONS", dict(Counter(r["metadata"].get("Series Description") for r in results.values() if r["metadata"])))

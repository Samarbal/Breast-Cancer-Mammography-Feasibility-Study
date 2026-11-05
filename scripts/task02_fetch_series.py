"""Download only selected CBIS-DDSM series from TCIA's official public NBIA API.

Run `sizes` first; run `download` only after reviewing the size plan. Keeps ZIPs
immutable and records hashes. Does not extract or modify original images.
"""

import hashlib
import json
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data" / "cbis_ddsm"
PLAN = json.loads((BASE / "task02_selection.json").read_text(encoding="utf-8"))
SIZES_FILE = BASE / "task02_series_sizes.json"
DOWNLOAD_DIR = BASE / "original" / "series_zips"
API = "https://services.cancerimagingarchive.net/nbia-api/services/v1/"

series = {}
for row in PLAN["selected"]:
    for kind, key in (("full", "full_series_uid"), ("roi_crop", "roi_series_uid")):
        uid = row[key]
        series.setdefault(uid, {"uid": uid, "kind": kind, "patient_id": row["patient_id"]})


def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "CBIS-DDSM-TASK02-Research/1.0"}), timeout=300)


if len(sys.argv) != 2 or sys.argv[1] not in ("sizes", "download"):
    raise SystemExit("Usage: task02_fetch_series.py sizes|download")

if sys.argv[1] == "sizes":
    results = []
    for i, item in enumerate(series.values(), 1):
        with get(API + "getSeriesSize?SeriesInstanceUID=" + item["uid"]) as response:
            values = json.load(response)
        item = {**item, **values[0]}
        results.append(item)
        print(f"{i}/{len(series)} {item['patient_id']} {item['kind']} {item['TotalSizeInBytes']} bytes {item['ObjectCount']} objects", flush=True)
    SIZES_FILE.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print("TOTAL", sum(x["TotalSizeInBytes"] for x in results), "bytes", flush=True)
else:
    results = json.loads(SIZES_FILE.read_text(encoding="utf-8"))
    if {x["uid"] for x in results} != set(series):
        raise SystemExit("Size plan does not match selected series")
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    def download(item):
        path = DOWNLOAD_DIR / (item["uid"] + ".zip")
        if path.exists():
            return f"exists {item['patient_id']} {item['kind']} {path.stat().st_size} bytes"
        temp = path.with_suffix(".zip.partial")
        url = API + "getImageWithMD5Hash?SeriesInstanceUID=" + item["uid"]
        try:
            with get(url) as response, temp.open("wb") as output:
                digest = hashlib.sha256()
                total = 0
                while block := response.read(1024 * 1024):
                    output.write(block)
                    digest.update(block)
                    total += len(block)
            temp.rename(path)
            return f"downloaded {item['patient_id']} {item['kind']} {total} bytes sha256={digest.hexdigest()}"
        except Exception as error:
            if temp.exists():
                temp.unlink()
            return f"FAILED {item['patient_id']} {item['kind']}: {error}"

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(download, item) for item in results]
        for i, future in enumerate(as_completed(futures), 1):
            print(f"{i}/{len(results)} {future.result()}", flush=True)

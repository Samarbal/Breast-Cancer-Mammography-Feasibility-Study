"""Validate selected official TCIA ZIPs without modifying original files."""

import csv
import hashlib
import io
import json
import zipfile
from pathlib import Path

import numpy as np
import pydicom
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data" / "cbis_ddsm"
PLAN = json.loads((BASE / "task02_selection.json").read_text(encoding="utf-8"))
ZIPS = BASE / "original" / "series_zips"
FIGURES = ROOT / "reports" / "figures"
OUT = BASE / "task02_validation.json"
FIGURES.mkdir(parents=True, exist_ok=True)


def load_zip(uid):
    path = ZIPS / (uid + ".zip")
    result = {"zip_path": str(path.relative_to(ROOT)), "zip_bytes": path.stat().st_size,
              "zip_sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "files": []}
    with zipfile.ZipFile(path) as archive:
        listed = {r["Filename"]: r["MD5Hash"].lower()
                  for r in csv.DictReader(io.StringIO(archive.read("md5hashes.csv").decode("utf-8-sig")))}
        for name in sorted(n for n in archive.namelist() if n.lower().endswith(".dcm")):
            raw = archive.read(name)
            ds = pydicom.dcmread(io.BytesIO(raw))
            pixels = ds.pixel_array
            result["files"].append({
                "name": name, "bytes": len(raw), "md5_ok": hashlib.md5(raw).hexdigest() == listed.get(name),
                "patient_id": str(ds.get("PatientID", "")),
                "series_uid": str(ds.get("SeriesInstanceUID", "")),
                "sop_uid": str(ds.get("SOPInstanceUID", "")),
                "instance_number": str(ds.get("InstanceNumber", "")),
                "series_description": str(ds.get("SeriesDescription", "")),
                "rows": int(ds.Rows), "cols": int(ds.Columns),
                "bits_stored": int(ds.get("BitsStored", 0)),
                "transfer_syntax": str(ds.file_meta.TransferSyntaxUID),
                "min": int(pixels.min()), "max": int(pixels.max()),
                "unique_count": int(np.unique(pixels).size) if pixels.size < 35_000_000 else None,
                "array": pixels,
            })
    return result


def display_gray(a, width=650):
    positive = a[a > 0]
    lo, hi = (np.percentile(positive, [1, 99.5]) if positive.size else (0, 1))
    if hi <= lo:
        hi = lo + 1
    gray = np.uint8(np.clip((a.astype(np.float32) - lo) * 255 / (hi - lo), 0, 255))
    image = Image.fromarray(gray, "L")
    height = round(image.height * width / image.width)
    return image.resize((width, height), Image.Resampling.LANCZOS).convert("RGB")


def make_overlay(row, image, mask, box):
    background = display_gray(image)
    rendered_mask = Image.fromarray(np.uint8(mask > 0) * 255, "L").resize(background.size, Image.Resampling.NEAREST)
    overlay = Image.new("RGB", background.size, (255, 60, 45))
    background.paste(Image.blend(background, overlay, 0.45), mask=rendered_mask)
    scale_x, scale_y = background.width / image.shape[1], background.height / image.shape[0]
    draw = ImageDraw.Draw(background)
    x0, y0, x1, y1 = box
    draw.rectangle((round(x0 * scale_x), round(y0 * scale_y), round((x1 + 1) * scale_x), round((y1 + 1) * scale_y)),
                   outline=(30, 255, 80), width=3)
    label = f"{row['patient_id']} {row['view']} {row['pathology']} | red: ROI  green: bbox"
    canvas = Image.new("RGB", (background.width, background.height + 35), "black")
    canvas.paste(background, (0, 35))
    ImageDraw.Draw(canvas).text((8, 10), label, fill="white")
    dest = FIGURES / f"task02_{row['patient_id']}_{row['view']}_overlay.png"
    canvas.save(dest)
    return str(dest.relative_to(ROOT))


results = []
for row in PLAN["selected"]:
    entry = {k: row[k] for k in ("patient_id", "view", "laterality", "abnormality_id", "pathology")}
    try:
        full = load_zip(row["full_series_uid"])
        roi = load_zip(row["roi_series_uid"])
        entry["full_zip"] = {k: v for k, v in full.items() if k != "files"}
        entry["roi_zip"] = {k: v for k, v in roi.items() if k != "files"}
        entry["full_files"] = [{k: v for k, v in f.items() if k != "array"} for f in full["files"]]
        entry["roi_files"] = [{k: v for k, v in f.items() if k != "array"} for f in roi["files"]]
        if len(full["files"]) != 1 or len(roi["files"]) != 2:
            raise ValueError("Expected 1 full image and 2 ROI/crop images")
        if not all(f["md5_ok"] and f["series_uid"] == uid
                   for files, uid in ((full["files"], row["full_series_uid"]), (roi["files"], row["roi_series_uid"]))
                   for f in files):
            raise ValueError("MD5 or series UID mismatch")
        expected_full_id = row["full_path"].split("/")[0]
        expected_roi_id = row["mask_path"].split("/")[0]
        if full["files"][0]["patient_id"] != expected_full_id or any(
            f["patient_id"] != expected_roi_id for f in roi["files"]
        ):
            raise ValueError("DICOM PatientID does not match CSV path patient/view/laterality")
        image = full["files"][0]["array"]
        candidates = roi["files"]
        matches = [f for f in candidates if f["array"].shape == image.shape and
                   f["unique_count"] is not None and f["unique_count"] <= 3 and f["max"] > 0]
        if len(matches) != 1:
            raise ValueError(f"Expected one full-size binary mask, found {len(matches)}")
        mask_file = matches[0]
        crop_file = next(f for f in candidates if f is not mask_file)
        if "ROI mask" not in mask_file["series_description"] or "cropped" not in crop_file["series_description"]:
            raise ValueError("DICOM series descriptions disagree with mask/crop content")
        mask = mask_file["array"] > 0
        yy, xx = np.where(mask)
        box = [int(xx.min()), int(yy.min()), int(xx.max()), int(yy.max())]
        area_fraction = float(mask.mean())
        if not (0 < area_fraction < 0.5):
            raise ValueError(f"Implausible mask area fraction {area_fraction}")
        entry["mask_file"] = mask_file["name"]
        entry["crop_file"] = crop_file["name"]
        entry["bbox_xyxy_inclusive"] = box
        entry["mask_area_pixels"] = int(mask.sum())
        entry["mask_area_fraction"] = area_fraction
        entry["alignment_shape_ok"] = True
        entry["crop_smaller_than_full"] = crop_file["array"].size < image.size
        entry["overlay"] = make_overlay(row, image, mask, box)
        entry["status"] = "pass"
    except Exception as error:
        entry["status"] = "fail"
        entry["error"] = str(error)
    results.append(entry)
    print(row["patient_id"], row["view"], entry["status"], entry.get("error", entry.get("bbox_xyxy_inclusive")), flush=True)

OUT.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
print("RESULTS", sum(r["status"] == "pass" for r in results), "/", len(results), flush=True)

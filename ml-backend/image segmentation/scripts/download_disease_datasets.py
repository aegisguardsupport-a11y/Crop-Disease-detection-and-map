"""Download the per-crop disease-classification datasets (one Kaggle dataset
per crop) into a non-OneDrive staging dir, unzipping each into its own folder.

Each dataset downloads as a single zip (fast), unlike the per-file kernel
output. Resumes: a crop whose folder already has image files is skipped.
"""
from __future__ import annotations

import os
import subprocess
import sys

DEST = r"C:\cpl_datasets\raw"

# crop -> Kaggle dataset slug (best available per-crop source)
SOURCES = {
    "tomato":     "kaustubhb999/tomatoleaf",
    "rice":       "nirmalsankalana/rice-leaf-disease-image",
    "cotton":     "seroshkarim/cotton-leaf-disease-dataset",
    "sugarcane":  "nirmalsankalana/sugarcane-leaf-disease-dataset",
    "chilli":     "taiburrahaman/chillileafdataset-trainvaltest",
    "cauliflower":"shuvokumarbasak2030/cauliflower-disease-multi-transformation-dataset",
    "maize":      "smaranjitghose/corn-or-maize-leaf-disease-dataset",
    "groundnut":  "abhimanuer/peanut-plant-leaf-disease",
    "blackgram":  "andytingzhiwei/black-gram-plant-leaf-disease",
    "brinjal":    "ziya07/solanaceae-family-leaves-dataset",
    "soyabean":   "sivm205/soybean-diseased-leaf-dataset",
    "sunflower":  "noamaanabdulazeem/sunflower-fruits-and-leaves-dataset",
    "wheat":      "olyadgetch/wheat-leaf-dataset",
    "sorghum":    "sanskarparadeshi/sorghum-disease-image-dataset",
}

IMG_EXT = (".jpg", ".jpeg", ".png", ".bmp", ".webp")


def has_images(path: str) -> int:
    n = 0
    for _r, _d, files in os.walk(path):
        for f in files:
            if f.lower().endswith(IMG_EXT):
                n += 1
    return n


def main() -> None:
    os.makedirs(DEST, exist_ok=True)
    ok = fail = skip = 0
    for i, (crop, slug) in enumerate(SOURCES.items(), 1):
        out = os.path.join(DEST, crop)
        if os.path.isdir(out) and has_images(out) > 0:
            print(f"[{i}/{len(SOURCES)}] {crop:12s} SKIP (already has images)", flush=True)
            skip += 1
            continue
        os.makedirs(out, exist_ok=True)
        print(f"[{i}/{len(SOURCES)}] {crop:12s} <- {slug} ...", flush=True)
        r = subprocess.run(
            [sys.executable, "-m", "kaggle", "datasets", "download", "-d", slug, "-p", out, "--unzip"],
            capture_output=True, text=True,
        )
        n = has_images(out)
        if r.returncode == 0 and n > 0:
            print(f"           OK  {crop}: {n} images", flush=True)
            ok += 1
        else:
            print(f"           FAIL {crop} (rc={r.returncode}, images={n})", flush=True)
            print("           " + (r.stderr or r.stdout or "")[-300:], flush=True)
            fail += 1
    print(f"\nDONE per-crop: ok={ok} skip={skip} fail={fail}")


if __name__ == "__main__":
    main()

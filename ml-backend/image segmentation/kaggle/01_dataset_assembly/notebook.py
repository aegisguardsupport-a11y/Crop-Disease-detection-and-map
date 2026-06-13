# %% [markdown]
# # CPL Crop Disease — Dataset Assembly (Stage 1 of 3)
#
# Curate a unified ~10k image pool from the public Kaggle datasets
# attached to this notebook, ready for SAM auto-labelling in stage 2.
#
# **Outputs** (saved to `/kaggle/working/curated_pool/`):
# - `<source>/<filename>.jpg` — copied images
# - `manifest.csv` — one row per kept image with metadata
# - `summary.json` — totals + rejection statistics
# - `preview_grid.png` — 12-image visual sanity check
#
# v2 fix: use dataset *directory name* as the source bucket and split the
# total budget evenly across datasets, so we don't end up with everything
# from one source like the v1 run.

# %%
import csv
import hashlib
import json
import re
import shutil
from collections import Counter, defaultdict
from pathlib import Path

from PIL import Image, UnidentifiedImageError

Image.MAX_IMAGE_PIXELS = None  # silence Pillow's "decompression bomb" warning

# %% [markdown]
# ## 1. Configuration

# %%
INPUT_ROOT = Path("/kaggle/input")
OUTPUT_ROOT = Path("/kaggle/working/curated_pool")

MIN_RESOLUTION = 224  # reject thumbnails — model trains at 640
DEDUP = True  # md5 dedup across all sources
TOTAL_TARGET = 10_000  # roughly the desired pool size

VALID_EXTS = {".jpg", ".jpeg", ".png", ".bmp"}


def sanitise_source_name(raw: str) -> str:
    """Make a directory name safe to use as a folder slug."""
    return re.sub(r"[^a-z0-9]+", "-", raw.lower()).strip("-") or "unknown"

# %% [markdown]
# ## 2. Discover what was attached

# %%
def count_images(p: Path) -> int:
    return sum(1 for f in p.rglob("*") if f.suffix.lower() in VALID_EXTS)


print(f"Free space in /kaggle/working : {shutil.disk_usage('/kaggle/working').free / 1e9:.1f} GB")
print()
print("Datasets attached:")
attached: list[Path] = []
for d in sorted(INPUT_ROOT.iterdir()):
    if not d.is_dir():
        continue
    n = count_images(d)
    print(f"  /kaggle/input/{d.name:50s}  → {n:>7} images")
    if n > 0:
        attached.append(d)

if not attached:
    raise SystemExit(
        "No datasets attached. Add at least PlantDoc + PlantVillage via "
        "the right-hand 'Add Data' panel and re-run."
    )

per_dataset_cap = max(1, TOTAL_TARGET // len(attached))
print(f"\nDistributing {TOTAL_TARGET} images across {len(attached)} datasets")
print(f"  per-dataset cap = {per_dataset_cap}")

# %% [markdown]
# ## 3. Filter, deduplicate, and sample
#
# The source bucket is now the (sanitised) dataset directory name itself,
# so per-source caps and statistics line up with reality.

# %%
def is_valid_image(p: Path, min_res: int) -> tuple[bool, str]:
    try:
        with Image.open(p) as im:
            im.verify()  # cheap corruption check
        with Image.open(p) as im:
            w, h = im.size
            if w < min_res or h < min_res:
                return False, f"too_small_{w}x{h}"
    except (UnidentifiedImageError, OSError, ValueError):
        return False, "unreadable"
    return True, "ok"


seen_hashes: set[str] = set()
collected: dict[str, list[tuple[Path, str]]] = defaultdict(list)
reject_stats: Counter[str] = Counter()

print("\nScanning images (this takes 1–3 minutes)...\n")
for ds_dir in attached:
    src_class = sanitise_source_name(ds_dir.name)
    cap = per_dataset_cap
    kept_for_source = 0

    files = (p for p in ds_dir.rglob("*") if p.suffix.lower() in VALID_EXTS)
    for img_path in files:
        if kept_for_source >= cap:
            reject_stats[f"{src_class}:cap_reached"] += 1
            continue
        ok, reason = is_valid_image(img_path, MIN_RESOLUTION)
        if not ok:
            # Bucket too_small reasons by exact size to keep the report short
            tag = "too_small" if reason.startswith("too_small_") else reason
            reject_stats[f"{src_class}:{tag}"] += 1
            continue
        if DEDUP:
            with open(img_path, "rb") as f:
                hsh = hashlib.md5(f.read(), usedforsecurity=False).hexdigest()
            if hsh in seen_hashes:
                reject_stats[f"{src_class}:duplicate"] += 1
                continue
            seen_hashes.add(hsh)
        else:
            hsh = "x" * 6

        # Filename: <source>__<original_stem>__<6char_hash>.jpg
        dst_name = f"{src_class}__{img_path.stem[:40]}__{hsh[:6]}{img_path.suffix.lower()}"
        collected[src_class].append((img_path, dst_name))
        kept_for_source += 1

    print(f"  {ds_dir.name:50s}  kept {kept_for_source:>5}  (cap {cap})")

# %% [markdown]
# ## 4. Report

# %%
total_kept = 0
print("\n=== KEPT (per source) ===")
for s, items in sorted(collected.items()):
    print(f"  {s:40s}  {len(items):>5}")
    total_kept += len(items)
print(f"  {'TOTAL':40s}  {total_kept:>5}\n")

print("=== TOP REJECTION REASONS ===")
for reason, n in reject_stats.most_common(15):
    print(f"  {reason:50s}  {n:>5}")

# %% [markdown]
# ## 5. Copy curated images to /kaggle/working

# %%
OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

manifest_rows: list[dict[str, str]] = []
for src_class, items in collected.items():
    out_subdir = OUTPUT_ROOT / src_class
    out_subdir.mkdir(parents=True, exist_ok=True)
    for src_path, dst_name in items:
        dst_path = out_subdir / dst_name
        shutil.copy(src_path, dst_path)
        manifest_rows.append(
            {
                "source": src_class,
                "filename": dst_name,
                "relpath": str(dst_path.relative_to(OUTPUT_ROOT)),
                "original_path": str(src_path),
            }
        )

manifest_path = OUTPUT_ROOT / "manifest.csv"
with open(manifest_path, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(manifest_rows[0].keys()))
    writer.writeheader()
    writer.writerows(manifest_rows)

summary = {
    "total_kept": total_kept,
    "per_source": {s: len(v) for s, v in collected.items()},
    "rejections": dict(reject_stats),
    "min_resolution": MIN_RESOLUTION,
    "deduplicated": DEDUP,
    "per_dataset_cap": per_dataset_cap,
    "datasets_attached": [d.name for d in attached],
}
(OUTPUT_ROOT / "summary.json").write_text(json.dumps(summary, indent=2))

bytes_used = sum(p.stat().st_size for p in OUTPUT_ROOT.rglob("*") if p.is_file())
print(f"\nWrote {len(manifest_rows)} images to {OUTPUT_ROOT}")
print(f"Disk used: {bytes_used / 1e9:.2f} GB")
print(f"Free remaining: {shutil.disk_usage('/kaggle/working').free / 1e9:.1f} GB")
print(f"Manifest: {manifest_path}")

# %% [markdown]
# ## 6. Sample preview (sanity check the assembly)
#
# 12 random images stratified across sources so we see at least one from each.

# %%
import matplotlib.pyplot as plt
import random

random.seed(42)
# Pick up to 4 per source to maximise diversity in the grid
preview_rows: list[dict[str, str]] = []
for s, rows in sorted(collected.items()):
    sample = random.sample(rows, k=min(4, len(rows)))
    for src_path, dst_name in sample:
        preview_rows.append(
            {"source": s, "relpath": str((OUTPUT_ROOT / s / dst_name).relative_to(OUTPUT_ROOT))}
        )
preview_rows = preview_rows[:12]

cols = 4
rows = (len(preview_rows) + cols - 1) // cols
fig, axes = plt.subplots(rows, cols, figsize=(4 * cols, 4 * rows))
axes_flat = axes.flat if rows > 1 else axes
for ax, row in zip(axes_flat, preview_rows):
    img = Image.open(OUTPUT_ROOT / row["relpath"])
    ax.imshow(img)
    ax.set_title(row["source"], fontsize=10)
    ax.axis("off")
# Blank any unused axes
for ax in list(axes_flat)[len(preview_rows):]:
    ax.axis("off")
plt.tight_layout()
plt.savefig(OUTPUT_ROOT / "preview_grid.png", dpi=72, bbox_inches="tight")
plt.show()
print(f"Preview saved to {OUTPUT_ROOT / 'preview_grid.png'}")

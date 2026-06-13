# %% [markdown]
# # CPL Crop Disease — Stage 4: GPU clean-leaf extraction + field compositing
#
# Inputs (attached):
# - the organized classification corpus (`manifest.csv` + `<crop>/<disease>/*.jpg`)
# - `best.pt` from the stage-3 leaf segmenter (kernel source `cpl-03-train-yolo`)
#
# For every image, replicate the serving pipeline EXACTLY
# (`cpl_crop.validation`): YOLO seg (conf .25 / iou .45) -> single
# highest-confidence mask -> bbox +5% padding -> black background fill ->
# 260x260 INTER_LINEAR. Train/serve alignment is the whole point.
#
# For TRAIN-split images we additionally synthesize one "field" composite:
# the leaf cutout pasted onto a natural background with random scale,
# rotation, shadow, blur and lighting — closing the lab->field domain gap.
#
# Outputs (kernel output, consumed by stage 5):
# - `clean/<crop>/<disease>/<md5>.jpg`       — clean-leaf 260x260
# - `composite/<crop>/<disease>/<md5>.jpg`   — field composite (train only)
# - `manifest_clean.csv`                     — adds `segmented` + `composite` cols
# - `stats.json`

# %% [markdown]
# ## Step 0 — Environment bootstrap (same torch/ultralytics fix as stage 3)

# %%
import subprocess
import sys

probe = subprocess.run(
    [sys.executable, "-c",
     ("import torch; assert torch.cuda.is_available(), 'no cuda'; "
      "(torch.randn(2,2,device='cuda') @ torch.randn(2,2,device='cuda')).sum().item()")],
    capture_output=True, text=True,
)
if probe.returncode == 0:
    print("Pre-installed torch is GPU-compatible.")
else:
    print("Reinstalling torch 2.5.1+cu121 ...")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "--quiet",
         "torch==2.5.1", "torchvision==0.20.1",
         "--index-url", "https://download.pytorch.org/whl/cu121"],
        check=True,
    )

ult_check = subprocess.run(
    [sys.executable, "-c", "import ultralytics; print(ultralytics.__version__)"],
    capture_output=True, text=True,
)
if ult_check.returncode == 0:
    print(f"Pre-installed ultralytics: {ult_check.stdout.strip()}")
else:
    print("Installing ultralytics ...")
    subprocess.run([sys.executable, "-m", "pip", "install", "--quiet", "ultralytics"],
                   check=True)

# %%
import csv
import json
import random
from pathlib import Path

import cv2
import numpy as np
import torch
from ultralytics import YOLO

SEED = 42
random.seed(SEED)
np.random.seed(SEED)

INPUT_ROOT = Path("/kaggle/input")
OUT = Path("/kaggle/working")
CLEAN = OUT / "clean"
COMP = OUT / "composite"
TARGET = (260, 260)
CONF, IOU, PAD = 0.25, 0.45, 0.05
BATCH = 48

# %% [markdown]
# ## Locate inputs

# %%
manifests = list(INPUT_ROOT.rglob("manifest.csv"))
if not manifests:
    raise SystemExit("Organized corpus not attached (no manifest.csv found)")
MANIFEST = manifests[0]
CORPUS = MANIFEST.parent
print(f"Corpus: {CORPUS}")

weights = sorted(INPUT_ROOT.rglob("best.pt"))
if not weights:
    raise SystemExit("Segmenter weights not attached (no best.pt found)")
WEIGHTS = weights[0]
print(f"Weights: {WEIGHTS}")

DEVICE = 0 if torch.cuda.is_available() else "cpu"
print(f"Device: {DEVICE}")

rows = list(csv.DictReader(open(MANIFEST, encoding="utf-8")))
for r in rows:  # manifest was written on Windows -> normalize separators
    r["relpath"] = r["relpath"].replace("\\", "/")
print(f"Manifest rows: {len(rows):,}")

# fail fast if paths are broken (better than 56k silent imread warnings)
probe_path = MANIFEST.parent / rows[0]["relpath"]
if not probe_path.exists():
    raise SystemExit(f"First manifest path missing: {probe_path}")

# %% [markdown]
# ## Serving-parity extraction (mirrors cpl_crop.validation.extract)

# %%
def bbox_from_mask(mask: np.ndarray) -> tuple[int, int, int, int]:
    ys, xs = np.where(mask)
    if len(xs) == 0:
        h, w = mask.shape
        return 0, 0, w - 1, h - 1
    return int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())


def extract_clean_leaf(img: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """bbox +PAD padding, black fill, resize TARGET — serving parity."""
    h, w = img.shape[:2]
    x0, y0, x1, y1 = bbox_from_mask(mask)
    dx, dy = (x1 - x0) * PAD, (y1 - y0) * PAD
    x0, y0 = int(max(0, x0 - dx)), int(max(0, y0 - dy))
    x1, y1 = int(min(w - 1, x1 + dx)), int(min(h - 1, y1 + dy))
    img_c, mask_c = img[y0:y1 + 1, x0:x1 + 1], mask[y0:y1 + 1, x0:x1 + 1]
    cleaned = np.where(mask_c[..., None], img_c, np.uint8(0)).astype(np.uint8)
    return cv2.resize(cleaned, TARGET[::-1], interpolation=cv2.INTER_LINEAR)


# %% [markdown]
# ## Field-composite synthesis
#
# Backgrounds: any attached natural images outside the corpus; procedural
# soil/foliage textures as fallback so the stage never blocks.

# %%
def procedural_background(size: int = 360) -> np.ndarray:
    earth = np.array([random.uniform(60, 110), random.uniform(70, 110), random.uniform(40, 80)])
    green = np.array([random.uniform(40, 90), random.uniform(90, 140), random.uniform(40, 80)])
    t = cv2.GaussianBlur(np.random.rand(size // 8, size // 8).astype(np.float32), (0, 0), 2)
    t = cv2.resize(t, (size, size))[..., None]
    base = earth * (1 - t) + green * t
    bg = np.clip(base + np.random.normal(0, 12, (size, size, 3)), 0, 255).astype(np.uint8)
    return cv2.GaussianBlur(bg, (5, 5), 0)


bg_paths: list[Path] = []
for p in INPUT_ROOT.rglob("*.jpg"):
    if CORPUS in p.parents or "train-yolo" in str(p):
        continue
    bg_paths.append(p)
    if len(bg_paths) >= 3000:
        break
print(f"Background pool: {len(bg_paths)} real images (procedural fallback active)")


def random_background(size: int = 360) -> np.ndarray:
    if bg_paths and random.random() < 0.85:
        p = random.choice(bg_paths)
        img = cv2.imread(str(p))
        if img is not None and img.shape[0] >= 64 and img.shape[1] >= 64:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            h, w = img.shape[:2]
            s = min(h, w)
            y, x = random.randint(0, h - s), random.randint(0, w - s)
            return cv2.resize(img[y:y + s, x:x + s], (size, size))
    return procedural_background(size)


def composite_leaf(img: np.ndarray, mask: np.ndarray) -> tuple[np.ndarray, np.ndarray] | None:
    """Paste the masked leaf onto a field background with realism jitter.

    Returns the full composite frame + the ground-truth paste mask. The
    caller then runs the REAL segmenter on the composite and extracts with
    the PREDICTED mask, so training samples inherit the segmenter's true
    real-world imperfections (ragged edges, background slivers)."""
    x0, y0, x1, y1 = bbox_from_mask(mask)
    leaf = img[y0:y1 + 1, x0:x1 + 1].copy()
    lmask = mask[y0:y1 + 1, x0:x1 + 1].astype(np.uint8) * 255
    if leaf.shape[0] < 8 or leaf.shape[1] < 8:
        return None

    bg = random_background(360)
    H, W = bg.shape[:2]

    # random scale + rotation
    scale = random.uniform(0.55, 0.9)
    f = (W * scale) / max(1, leaf.shape[1])
    leaf = cv2.resize(leaf, (max(1, int(leaf.shape[1] * f)), max(1, int(leaf.shape[0] * f))))
    lmask = cv2.resize(lmask, (leaf.shape[1], leaf.shape[0]))
    angle = random.uniform(-40, 40)
    M = cv2.getRotationMatrix2D((leaf.shape[1] / 2, leaf.shape[0] / 2), angle, 1.0)
    leaf = cv2.warpAffine(leaf, M, (leaf.shape[1], leaf.shape[0]))
    lmask = cv2.warpAffine(lmask, M, (lmask.shape[1], lmask.shape[0]))
    lh, lw = leaf.shape[:2]
    if lh >= H or lw >= W:
        f = min((H - 2) / lh, (W - 2) / lw)
        leaf = cv2.resize(leaf, (max(1, int(lw * f)), max(1, int(lh * f))))
        lmask = cv2.resize(lmask, (leaf.shape[1], leaf.shape[0]))
        lh, lw = leaf.shape[:2]
    py, px = random.randint(0, H - lh), random.randint(0, W - lw)
    m = lmask > 127

    # soft drop-shadow: darken background under a dilated, shifted mask
    shadow = cv2.dilate(lmask, np.ones((9, 9), np.uint8))
    sy, sx = py + random.randint(2, 8), px + random.randint(2, 8)
    sy2, sx2 = min(H, sy + lh), min(W, sx + lw)
    region = bg[sy:sy2, sx:sx2].astype(np.float32)
    sh = (shadow[: sy2 - sy, : sx2 - sx, None] / 255.0) * random.uniform(0.25, 0.45)
    bg[sy:sy2, sx:sx2] = np.clip(region * (1 - sh), 0, 255).astype(np.uint8)

    # paste leaf
    roi = bg[py:py + lh, px:px + lw]
    roi[m] = leaf[m]
    bg[py:py + lh, px:px + lw] = roi

    # global lighting / blur jitter (phone-photo realism)
    alpha = random.uniform(0.75, 1.25)          # contrast / brightness
    beta = random.uniform(-25, 25)
    bg = np.clip(bg.astype(np.float32) * alpha + beta, 0, 255).astype(np.uint8)
    if random.random() < 0.4:
        bg = cv2.GaussianBlur(bg, (3, 3), 0)

    # full-frame ground-truth mask of where the leaf landed
    full_mask = np.zeros((H, W), bool)
    full_mask[py:py + lh, px:px + lw] = m
    return bg, full_mask


# %% [markdown]
# ## Main pass — batched GPU segmentation over the whole corpus

# %%
model = YOLO(str(WEIGHTS))

stats = {"segmented": 0, "fallback_no_leaf": 0, "composites": 0, "read_errors": 0}
out_rows: list[dict[str, str]] = []
comp_jobs: list[tuple[int, Path, np.ndarray, np.ndarray]] = []

for start in range(0, len(rows), BATCH):
    chunk = rows[start:start + BATCH]
    paths = [CORPUS / r["relpath"] for r in chunk]
    imgs: list[np.ndarray | None] = []
    for p in paths:
        im = cv2.imread(str(p))
        imgs.append(cv2.cvtColor(im, cv2.COLOR_BGR2RGB) if im is not None else None)

    valid_idx = [i for i, im in enumerate(imgs) if im is not None]
    preds = model.predict(
        [imgs[i] for i in valid_idx], imgsz=640, conf=CONF, iou=IOU,
        device=DEVICE, verbose=False,
    ) if valid_idx else []

    for i, r in enumerate(chunk):
        img = imgs[i]
        if img is None:
            stats["read_errors"] += 1
            continue
        mask = None
        if i in valid_idx:
            res = preds[valid_idx.index(i)]
            if res.masks is not None and len(res.masks) > 0:
                confs = res.boxes.conf.cpu().numpy()
                best = int(confs.argmax())
                m = res.masks.data[best].cpu().numpy()
                mask = cv2.resize(m, (img.shape[1], img.shape[0])) > 0.5
                if not mask.any():
                    mask = None

        if mask is not None:
            clean = extract_clean_leaf(img, mask)
            segmented = True
            stats["segmented"] += 1
        else:  # serving would route to retake; for training keep a plain resize
            clean = cv2.resize(img, TARGET[::-1], interpolation=cv2.INTER_LINEAR)
            segmented = False
            stats["fallback_no_leaf"] += 1

        rel = Path(r["relpath"])
        dst = CLEAN / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(dst), cv2.cvtColor(clean, cv2.COLOR_RGB2BGR),
                    [cv2.IMWRITE_JPEG_QUALITY, 92])

        comp_rel = ""
        if mask is not None:
            # composites for ALL splits: train -> random (augmentation variety),
            # val/test -> deterministic per-image seed (reproducible field-proxy
            # sets used for checkpoint selection and honest field-test metrics)
            if r["split"] != "train":
                random.seed(int(r["md5"][:8], 16))
            built = composite_leaf(img, mask)
            if r["split"] != "train":
                random.seed(SEED + start)
            if built is not None:
                comp_jobs.append((len(out_rows), rel, built[0], built[1]))

        out_rows.append({**r, "segmented": str(segmented),
                         "clean_relpath": str(Path("clean") / rel),
                         "composite_relpath": comp_rel})

    # Phase B — run the REAL segmenter on this chunk's composites and
    # extract with the PREDICTED mask (serving-parity incl. segmenter error).
    if comp_jobs:
        cpreds = model.predict([j[2] for j in comp_jobs], imgsz=640, conf=CONF,
                               iou=IOU, device=DEVICE, verbose=False)
        for (row_i, rel, cimg, gt_mask), res in zip(comp_jobs, cpreds):
            pmask = None
            if res.masks is not None and len(res.masks) > 0:
                best = int(res.boxes.conf.cpu().numpy().argmax())
                pm = res.masks.data[best].cpu().numpy()
                pmask = cv2.resize(pm, (cimg.shape[1], cimg.shape[0])) > 0.5
                if not pmask.any():
                    pmask = None
            final = extract_clean_leaf(cimg, pmask if pmask is not None else gt_mask)
            cdst = COMP / rel
            cdst.parent.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(cdst), cv2.cvtColor(final, cv2.COLOR_RGB2BGR),
                        [cv2.IMWRITE_JPEG_QUALITY, 92])
            out_rows[row_i]["composite_relpath"] = str(Path("composite") / rel)
            stats["composites"] += 1
        comp_jobs = []

    if (start // BATCH) % 20 == 0:
        done = start + len(chunk)
        print(f"  {done:,}/{len(rows):,}  seg={stats['segmented']:,} "
              f"fallback={stats['fallback_no_leaf']:,} comp={stats['composites']:,}",
              flush=True)

# %% [markdown]
# ## Write outputs

# %%
with open(OUT / "manifest_clean.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
    w.writeheader()
    w.writerows(out_rows)

(OUT / "stats.json").write_text(json.dumps(stats, indent=2))
print(json.dumps(stats, indent=2))
print("Stage 4 complete.")

# %% [markdown]
# # CPL Crop Disease — SAM Auto-Label (Stage 2 of 3) — v3
#
# v2 hit `CUDA error: no kernel image` because Kaggle assigned a **Tesla P100**
# (sm_60, Pascal) for this run, while the pre-installed PyTorch 2.10+cu128 only
# supports sm_70 and newer. We detect this at startup (in a subprocess so the
# parent process hasn't imported torch yet) and pip-install a compatible
# `torch 2.4.1+cu121` wheel that covers sm_60..sm_90. Works on both T4 and P100.

# %%
# Step 0 — Verify torch works with whatever GPU Kaggle assigned, fix if not.
# IMPORTANT: do not import `torch` in this cell. We need the parent process
# to be torch-free until step 1 so a pip-replace actually takes effect.
import subprocess
import sys

probe = subprocess.run(
    [
        sys.executable,
        "-c",
        (
            "import torch; "
            "assert torch.cuda.is_available(), 'no cuda'; "
            "(torch.randn(2,2,device='cuda') @ torch.randn(2,2,device='cuda')).sum().item()"
        ),
    ],
    capture_output=True,
    text=True,
)
if probe.returncode == 0:
    print("Pre-installed torch is GPU-compatible with this kernel's GPU.")
else:
    err_tail = (probe.stderr or "")[-400:]
    print("Pre-installed torch is NOT compatible with this GPU. Tail of error:")
    print(err_tail)
    print("\nInstalling torch 2.4.1+cu121 (supports sm_60..sm_90) ...")
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--quiet",
            "torch==2.4.1",
            "torchvision==0.19.1",
            "--index-url",
            "https://download.pytorch.org/whl/cu121",
        ],
        check=True,
    )
    # Re-probe to be sure the replacement took
    re_probe = subprocess.run(
        [
            sys.executable,
            "-c",
            "import torch; print(torch.__version__); "
            "(torch.randn(2,2,device='cuda') @ torch.randn(2,2,device='cuda')).sum().item()",
        ],
        capture_output=True,
        text=True,
    )
    if re_probe.returncode != 0:
        raise SystemExit(f"torch reinstall failed: {re_probe.stderr[-400:]}")
    print(f"Reinstalled OK: {re_probe.stdout.strip()}")

# %%
# Step 1 — Now we can safely import torch and run our matmul sanity check.
import torch

print(f"Torch: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
if not torch.cuda.is_available():
    raise SystemExit("CUDA not available; enable GPU and re-run.")
print(f"CUDA: {torch.version.cuda}")
print(f"GPU: {torch.cuda.get_device_name(0)}  capability={torch.cuda.get_device_capability(0)}")
_ = (torch.randn(8, 8, device="cuda") @ torch.randn(8, 8, device="cuda")).sum().item()
print("CUDA matmul OK.")

# %%
import gc
import hashlib
import json
import os
import shutil
import time
import warnings
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from transformers import SamModel, SamProcessor

warnings.filterwarnings("ignore", category=FutureWarning)

DEVICE = "cuda"

# %% [markdown]
# ## 1. Locate the curated pool from stage 1

# %%
INPUT_ROOT = Path("/kaggle/input")
OUTPUT_ROOT = Path("/kaggle/working/yolo_dataset")
PREVIEW_DIR = OUTPUT_ROOT / "preview"

candidates = list(INPUT_ROOT.rglob("curated_pool"))
if not candidates:
    print("Looking in /kaggle/input/ for the curated pool ...")
    for d in INPUT_ROOT.iterdir():
        print(f"  {d}")
    raise SystemExit("Could not find curated_pool/. Make sure stage 1 finished and is attached.")
POOL = candidates[0]
print(f"Curated pool: {POOL}")

all_images = sorted(
    p for p in POOL.rglob("*") if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp"}
)
print(f"Found {len(all_images)} images to label")

# %% [markdown]
# ## 2. Load SAM

# %%
SAM_MODEL_ID = "facebook/sam-vit-base"  # ~360 MB, fast on T4
print(f"Loading SAM ({SAM_MODEL_ID}) ...")
sam_processor = SamProcessor.from_pretrained(SAM_MODEL_ID)
sam_model = SamModel.from_pretrained(SAM_MODEL_ID).to(DEVICE).eval()
print("SAM ready.")

# %% [markdown]
# ## 3. Inference + mask helpers

# %%
MIN_MASK_AREA = 0.02  # 2% — reject tiny masks (probably wrong objects)
MAX_MASK_AREA = 0.95  # 95% — reject masks covering ~the whole image
SIMPLIFY_EPSILON_REL = 0.002  # contour simplification: % of perimeter


@torch.inference_mode()
def segment_at_center(image_pil: Image.Image) -> tuple[np.ndarray, float]:
    """Return ``(mask, predicted_iou)`` for the highest-IoU SAM mask at the image centre."""
    w, h = image_pil.size
    input_points = [[[w // 2, h // 2]]]  # batch=1, n_points=1, xy
    input_labels = [[1]]  # 1 = foreground
    inputs = sam_processor(
        image_pil,
        input_points=input_points,
        input_labels=input_labels,
        return_tensors="pt",
    ).to(DEVICE)
    outputs = sam_model(**inputs, multimask_output=True)
    # post_process_masks returns list[batch] -> tensor (n_points, M, H, W)
    masks = sam_processor.image_processor.post_process_masks(
        outputs.pred_masks.cpu(),
        inputs["original_sizes"].cpu(),
        inputs["reshaped_input_sizes"].cpu(),
    )
    mask_set = masks[0][0].numpy()  # (M=3, H, W)
    iou_scores = outputs.iou_scores[0, 0].detach().cpu().numpy()  # (M=3,)
    best = int(iou_scores.argmax())
    return mask_set[best].astype(bool), float(iou_scores[best])


def mask_to_yolo_polygon(mask: np.ndarray) -> str | None:
    """Convert a (H, W) bool mask to a single-line YOLO segmentation label."""
    h, w = mask.shape
    mask_u8 = mask.astype(np.uint8) * 255
    contours, _ = cv2.findContours(mask_u8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    contour = max(contours, key=cv2.contourArea)
    if cv2.contourArea(contour) < 50:
        return None
    epsilon = SIMPLIFY_EPSILON_REL * cv2.arcLength(contour, True)
    contour = cv2.approxPolyDP(contour, epsilon, True)
    pts = contour.reshape(-1, 2)
    if len(pts) < 3:
        return None
    parts = ["0"]
    for x, y in pts:
        parts.append(f"{x / w:.6f}")
        parts.append(f"{y / h:.6f}")
    return " ".join(parts) + "\n"


def split_for(filename: str, train_pct: int = 80, val_pct: int = 15) -> str:
    """Hash-based deterministic split."""
    h = int(hashlib.md5(filename.encode("utf-8"), usedforsecurity=False).hexdigest(), 16)
    bucket = h % 100
    if bucket < train_pct:
        return "train"
    if bucket < train_pct + val_pct:
        return "valid"
    return "test"


# %% [markdown]
# ## 4. Smoke test on 3 images before committing to the full run

# %%
print("\nSmoke test on 3 images...")
ok = 0
for img_path in all_images[:3]:
    with Image.open(img_path) as im:
        image_pil = im.convert("RGB")
    mask, iou = segment_at_center(image_pil)
    area = mask.sum() / mask.size
    print(f"  {img_path.name:50s}  mask area={area*100:5.1f}%  iou={iou:.3f}")
    if area > 0.01:
        ok += 1
if ok == 0:
    raise SystemExit("Smoke test produced 0 valid masks — aborting.")
print("Smoke test passed; starting full run.\n")

# %% [markdown]
# ## 5. Auto-label all 10k images

# %%
for split in ("train", "valid", "test"):
    (OUTPUT_ROOT / "images" / split).mkdir(parents=True, exist_ok=True)
    (OUTPUT_ROOT / "labels" / split).mkdir(parents=True, exist_ok=True)
PREVIEW_DIR.mkdir(parents=True, exist_ok=True)

stats = {
    "processed": 0,
    "labeled": 0,
    "rejected_mask_area": 0,
    "rejected_polygon": 0,
    "errors": 0,
    "by_split": {"train": 0, "valid": 0, "test": 0},
}
PREVIEW_KEEP = 12
preview_saved = 0
preview_every = max(1, len(all_images) // (PREVIEW_KEEP + 5))
LOG_EVERY = 250
t0 = time.time()


def save_preview(idx: int, image_pil: Image.Image, mask: np.ndarray) -> None:
    img_np = np.asarray(image_pil)
    overlay = img_np.copy()
    overlay[mask] = (overlay[mask] * 0.4 + np.array([255, 80, 80]) * 0.6).astype(np.uint8)
    triple = np.concatenate(
        [img_np, np.repeat((mask * 255)[..., None].astype(np.uint8), 3, axis=2), overlay],
        axis=1,
    )
    Image.fromarray(triple).save(PREVIEW_DIR / f"preview_{idx:03d}.png")


for idx, img_path in enumerate(all_images):
    stats["processed"] += 1
    if stats["processed"] % LOG_EVERY == 0:
        elapsed = time.time() - t0
        rate = stats["processed"] / max(elapsed, 1e-6)
        eta = (len(all_images) - stats["processed"]) / max(rate, 0.01)
        print(
            f"  [{stats['processed']:>5}/{len(all_images)}]  "
            f"labeled={stats['labeled']}  rate={rate:.1f} img/s  "
            f"eta={eta / 60:.1f} min"
        )

    try:
        with Image.open(img_path) as im:
            image_pil = im.convert("RGB")
    except Exception as e:
        stats["errors"] += 1
        if stats["errors"] < 10:
            print(f"  read-error {img_path.name}: {type(e).__name__}: {e}")
        continue

    try:
        mask, iou = segment_at_center(image_pil)
    except Exception as e:
        stats["errors"] += 1
        if stats["errors"] < 10:
            print(f"  sam-error {img_path.name}: {type(e).__name__}: {e}")
        continue

    area_ratio = float(mask.sum()) / float(mask.size)
    if not (MIN_MASK_AREA <= area_ratio <= MAX_MASK_AREA):
        stats["rejected_mask_area"] += 1
        continue

    polygon_line = mask_to_yolo_polygon(mask)
    if polygon_line is None:
        stats["rejected_polygon"] += 1
        continue

    split = split_for(img_path.name)
    stats["by_split"][split] += 1
    stats["labeled"] += 1

    dst_image = OUTPUT_ROOT / "images" / split / img_path.name
    dst_label = OUTPUT_ROOT / "labels" / split / (img_path.stem + ".txt")
    shutil.copy(img_path, dst_image)
    dst_label.write_text(polygon_line, encoding="utf-8")

    if preview_saved < PREVIEW_KEEP and stats["labeled"] % preview_every == 0:
        try:
            save_preview(preview_saved, image_pil, mask)
            preview_saved += 1
        except Exception as e:
            print(f"    preview save failed: {e}")

elapsed = time.time() - t0
print(f"\nDone. {stats['labeled']}/{stats['processed']} labeled in {elapsed/60:.1f} min")
print("Stats:", json.dumps(stats, indent=2))

del sam_model, sam_processor
gc.collect()
torch.cuda.empty_cache()

# %% [markdown]
# ## 6. Write data.yaml + stats.json

# %%
data_yaml = OUTPUT_ROOT / "data.yaml"
data_yaml.write_text(
    "# Generated by stage 2 (SAM auto-labelling, center-point prompt)\n"
    "path: .\n"
    "train: images/train\n"
    "val: images/valid\n"
    "test: images/test\n"
    "names:\n"
    "  0: leaf\n",
    encoding="utf-8",
)
print(f"Wrote {data_yaml}")

(OUTPUT_ROOT / "stats.json").write_text(json.dumps(stats, indent=2), encoding="utf-8")

print("\nFiles in /kaggle/working/yolo_dataset/:")
for split in ("train", "valid", "test"):
    n_img = len(list((OUTPUT_ROOT / "images" / split).glob("*")))
    n_lbl = len(list((OUTPUT_ROOT / "labels" / split).glob("*")))
    print(f"  {split:6s}  images={n_img:>5}  labels={n_lbl:>5}")
print(f"  preview/      images={preview_saved}")

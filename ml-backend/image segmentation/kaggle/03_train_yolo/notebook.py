# %% [markdown]
# # CPL Crop Disease — Train YOLOv8-seg (Stage 3 of 3)
#
# Trains a YOLOv8n-seg leaf segmenter on the 9,010 SAM-labelled images from
# stage 2. The trained `best.pt` and exported `best.onnx` are saved to
# `/kaggle/working/` so we can pull them locally and drop them into the
# main FastAPI pipeline.
#
# **Outputs**:
# - `runs/segment/leaf_v1/weights/best.pt`   — Ultralytics PyTorch weights
# - `runs/segment/leaf_v1/weights/best.onnx` — ONNX export (CPU-friendly)
# - `runs/segment/leaf_v1/results.csv`       — per-epoch loss / mAP curves
# - `eval_grid.png`                          — qualitative test predictions
# - `metrics.json`                           — final test-set mAP numbers
#
# **Runtime**: 60–120 min on Kaggle T4 / P100, depending on GPU.

# %% [markdown]
# ## Step 0 — Compatible torch (P100 vs T4 fix, same as stage 2)

# %%
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
    print("Pre-installed torch is GPU-compatible.")
else:
    # torch 2.5.1+cu121 is the sweet spot:
    #   - built against numpy 2.x  -> doesn't break Kaggle's pre-installed scipy/pandas/etc.
    #   - still supports sm_50..sm_90 -> works on Pascal P100, T4, A100, L4
    print("Reinstalling torch 2.5.1+cu121 ...")
    subprocess.run(
        [
            sys.executable, "-m", "pip", "install", "--quiet",
            "torch==2.5.1", "torchvision==0.20.1",
            "--index-url", "https://download.pytorch.org/whl/cu121",
        ],
        check=True,
    )
    re_probe = subprocess.run(
        [sys.executable, "-c",
         "import torch; print(torch.__version__); "
         "(torch.randn(2,2,device='cuda') @ torch.randn(2,2,device='cuda')).sum().item()"],
        capture_output=True, text=True,
    )
    if re_probe.returncode != 0:
        raise SystemExit(f"torch reinstall failed: {re_probe.stderr[-400:]}")
    print(f"OK: {re_probe.stdout.strip()}")

# Use Kaggle's pre-installed ultralytics if present (already binary-compatible
# with the system numpy/scipy). Only install if missing.
ult_check = subprocess.run(
    [sys.executable, "-c", "import ultralytics; print(ultralytics.__version__)"],
    capture_output=True, text=True,
)
if ult_check.returncode == 0:
    print(f"Pre-installed ultralytics: {ult_check.stdout.strip()}")
else:
    print("Installing ultralytics ...")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "--quiet", "ultralytics"],
        check=True,
    )

# Final sanity: torch + numpy + ultralytics all importable in a clean subprocess
final_probe = subprocess.run(
    [sys.executable, "-c",
     "import numpy, torch, ultralytics; "
     "print(f'numpy={numpy.__version__} torch={torch.__version__} "
     "ultralytics={ultralytics.__version__}'); "
     "(torch.randn(2,2,device='cuda') @ torch.randn(2,2,device='cuda')).sum().item(); "
     "_ = numpy.random.default_rng().random(4)"],
    capture_output=True, text=True,
)
if final_probe.returncode != 0:
    raise SystemExit(f"Final probe failed: {final_probe.stderr[-600:]}")
print(f"Final probe OK: {final_probe.stdout.strip()}")

# %% [markdown]
# ## Step 1 — Imports + GPU sanity

# %%
import json
from pathlib import Path

import torch
import yaml
from ultralytics import YOLO

print(f"Torch: {torch.__version__} | CUDA: {torch.cuda.is_available()}")
print(f"GPU: {torch.cuda.get_device_name(0)}  capability={torch.cuda.get_device_capability(0)}")

# %% [markdown]
# ## Step 2 — Locate the YOLO dataset from stage 2

# %%
INPUT_ROOT = Path("/kaggle/input")
candidates = list(INPUT_ROOT.rglob("yolo_dataset"))
candidates = [c for c in candidates if (c / "data.yaml").exists()]
if not candidates:
    print("Looking under /kaggle/input/ for yolo_dataset/data.yaml ...")
    for d in INPUT_ROOT.iterdir():
        print(f"  {d}")
    raise SystemExit("Stage 2 output not found. Make sure 02_sam_autolabel is attached.")
DATASET_DIR = candidates[0]
print(f"Dataset dir: {DATASET_DIR}")

# Re-emit data.yaml at /kaggle/working/data.yaml with ABSOLUTE paths.
# Ultralytics is finicky about relative paths when the dataset lives on a
# read-only mount; absolute is the safe route.
data_yaml_out = Path("/kaggle/working/data.yaml")
data_yaml_out.write_text(
    yaml.safe_dump(
        {
            "path": str(DATASET_DIR),
            "train": "images/train",
            "val": "images/valid",
            "test": "images/test",
            "names": {0: "leaf"},
        }
    )
)
print(f"Wrote {data_yaml_out}:")
print(data_yaml_out.read_text())

# Quick label sanity
for split in ("train", "valid", "test"):
    n_img = len(list((DATASET_DIR / "images" / split).glob("*")))
    n_lbl = len(list((DATASET_DIR / "labels" / split).glob("*")))
    print(f"  {split:6s}  images={n_img:>5}  labels={n_lbl:>5}")

# %% [markdown]
# ## Step 3 — Train YOLOv8n-seg

# %%
PROJECT = "/kaggle/working/runs/segment"
NAME = "leaf_v2"
EPOCHS = 80
IMGSZ = 640
BATCH = 16
PATIENCE = 15

# v2: upgrade nano -> small backbone (T4 16GB handles it easily) and add
# field-robustness augmentation: copy_paste pastes leaf instances across
# images (clutter robustness), degrees/perspective simulate phone angles.
model = YOLO("yolov8s-seg.pt")  # ImageNet-pretrained small backbone

results = model.train(
    data=str(data_yaml_out),
    epochs=EPOCHS,
    imgsz=IMGSZ,
    batch=BATCH,
    patience=PATIENCE,
    optimizer="AdamW",
    lr0=0.001,
    cos_lr=True,
    close_mosaic=10,         # turn off mosaic in last 10 epochs for clean final loss
    copy_paste=0.3,          # instance cut-paste across images (field clutter)
    degrees=15.0,            # random rotation (phone camera angles)
    perspective=0.0005,      # mild perspective warp
    project=PROJECT,
    name=NAME,
    exist_ok=True,
    plots=True,              # auto-saves training curves under runs/segment/leaf_v2/
    verbose=True,
)

best_pt = Path(PROJECT) / NAME / "weights" / "best.pt"
print(f"\nBest weights: {best_pt}  ({best_pt.stat().st_size / 1e6:.1f} MB)")

# %% [markdown]
# ## Step 4 — Test-set evaluation

# %%
best_model = YOLO(str(best_pt))
metrics = best_model.val(
    data=str(data_yaml_out),
    split="test",
    imgsz=IMGSZ,
    project=PROJECT,
    name=f"{NAME}_test",
    exist_ok=True,
)

# Extract the headline numbers
m = {
    "box_map50": float(metrics.box.map50) if hasattr(metrics, "box") else None,
    "box_map50_95": float(metrics.box.map) if hasattr(metrics, "box") else None,
    "seg_map50": float(metrics.seg.map50) if hasattr(metrics, "seg") else None,
    "seg_map50_95": float(metrics.seg.map) if hasattr(metrics, "seg") else None,
    "test_set_size": len(list((DATASET_DIR / "images" / "test").glob("*"))),
}
print("\n=== TEST METRICS ===")
print(json.dumps(m, indent=2))

Path("/kaggle/working/metrics.json").write_text(json.dumps(m, indent=2))

# %% [markdown]
# ## Step 5 — Qualitative spot-check on 12 test images

# %%
import random

import cv2
import numpy as np
from PIL import Image

random.seed(42)
test_images = sorted((DATASET_DIR / "images" / "test").glob("*"))
sample = random.sample(test_images, k=min(12, len(test_images)))

eval_panels: list[np.ndarray] = []
for img_path in sample:
    pred = best_model.predict(str(img_path), imgsz=IMGSZ, conf=0.25, verbose=False)[0]
    img = cv2.cvtColor(cv2.imread(str(img_path)), cv2.COLOR_BGR2RGB)
    h, w = img.shape[:2]

    if pred.masks is not None and len(pred.masks) > 0:
        mask = pred.masks.data[0].cpu().numpy()
        # Resize mask to original image size if needed
        if mask.shape != (h, w):
            mask = cv2.resize(mask, (w, h), interpolation=cv2.INTER_NEAREST)
        mask = mask.astype(bool)
        overlay = img.copy()
        overlay[mask] = (overlay[mask] * 0.4 + np.array([255, 80, 80]) * 0.6).astype(np.uint8)
    else:
        overlay = img.copy()
        cv2.putText(overlay, "no detection", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

    side_by_side = np.concatenate([img, overlay], axis=1)
    side_by_side = cv2.resize(side_by_side, (640, 320))
    eval_panels.append(side_by_side)

# Stitch into a 4x3 grid
rows = []
for i in range(0, len(eval_panels), 3):
    row = np.concatenate(eval_panels[i:i + 3], axis=1)
    rows.append(row)
grid = np.concatenate(rows, axis=0)
Image.fromarray(grid).save("/kaggle/working/eval_grid.png")
print(f"Saved /kaggle/working/eval_grid.png ({grid.shape})")

# %% [markdown]
# ## Step 6 — Export to ONNX (smaller, CPU-friendly for deployment)

# %%
print("Exporting to ONNX ...")
onnx_path = best_model.export(format="onnx", imgsz=IMGSZ, opset=12, simplify=True)
print(f"ONNX: {onnx_path}")

# %% [markdown]
# ## Step 7 — Recap of artifacts saved to /kaggle/working/

# %%
print("Files in /kaggle/working/ matching our expected outputs:")
for p in sorted(Path("/kaggle/working").rglob("*")):
    if not p.is_file():
        continue
    name = p.name
    if name in {"best.pt", "best.onnx", "metrics.json", "eval_grid.png", "results.csv"}:
        size_mb = p.stat().st_size / 1e6
        print(f"  {size_mb:>7.2f} MB  {p.relative_to(Path('/kaggle/working'))}")

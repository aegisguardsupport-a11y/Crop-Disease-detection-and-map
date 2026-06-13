# CPL — Leaf Segmentation Pipeline

Trains a custom YOLOv8-seg model for leaf segmentation, used as the
validation gate (Stage 4 in the technical-approach diagram) of the
crop-disease prediction service.

The whole training pipeline runs on **Kaggle's free T4 GPU**. Your
laptop only stores ~80 MB at the very end (the trained `.pt` file).

## Pipeline

Three notebooks, each pushed to Kaggle and run there:

```
┌──────────────────────────┐    ┌──────────────────────────┐    ┌──────────────────────────┐
│ 01_dataset_assembly      │ -> │ 02_sam_autolabel         │ -> │ 03_train_yolo            │
│  Curate ~10k images from │    │  Grounding DINO + SAM    │    │  Train YOLOv8n-seg on    │
│  PlantDoc, PlantVillage, │    │  auto-label every image  │    │  auto-labelled data,     │
│  New Plant Diseases.     │    │  with a leaf polygon.    │    │  export best.pt + .onnx  │
│  GPU: not needed.        │    │  GPU: yes (~5-7 hrs).    │    │  GPU: yes (~1-2 hrs).    │
└──────────────────────────┘    └──────────────────────────┘    └──────────────────────────┘
```

Each stage stores its output as a Kaggle Dataset that the next stage attaches via `kernel_sources`.

## Layout

```
.
├── kaggle/
│   ├── 01_dataset_assembly/
│   │   ├── kernel-metadata.json    # which datasets to attach, GPU on/off, etc.
│   │   └── notebook.py             # the actual code (uses # %% cell markers)
│   ├── 02_sam_autolabel/
│   │   └── ...
│   └── 03_train_yolo/
│       └── ...
├── scripts/
│   └── kaggle_run.py               # CLI wrapper around `kaggle kernels ...`
├── outputs/                        # downloaded outputs (gitignored)
├── requirements.txt
├── .gitignore
└── README.md
```

## One-time setup

1. **Install the kaggle CLI** (we'll do this from kiro-cli):
   ```powershell
   pip install -r requirements.txt
   ```
2. **Place `kaggle.json`** at `C:\Users\<you>\.kaggle\kaggle.json`
   (NOT inside this project folder).
3. **Verify auth**:
   ```powershell
   python scripts/kaggle_run.py verify
   ```
   If this prints a list of (or "no") kernels without errors, auth works.

## Running each stage

```powershell
# Stage 1: curate the public datasets into a unified pool
python scripts/kaggle_run.py run 01_dataset_assembly

# Stage 2: SAM auto-labels every image (GPU, takes hours)
python scripts/kaggle_run.py run 02_sam_autolabel

# Stage 3: train YOLOv8-seg + export weights
python scripts/kaggle_run.py run 03_train_yolo
```

Each `run` command:
1. Pushes the notebook to Kaggle
2. Polls status until the kernel finishes
3. Downloads only the output files we care about into `./outputs/<stage>/`

For stage 3, the final output is `outputs/03_train_yolo/best.pt`. That's
the file we copy into the main classification project.

## Available sub-commands

```powershell
python scripts/kaggle_run.py verify          # auth check
python scripts/kaggle_run.py push <stage>    # push only, don't wait
python scripts/kaggle_run.py status <stage>  # one-shot status check
python scripts/kaggle_run.py output <stage>  # download output of a finished kernel
python scripts/kaggle_run.py run <stage>     # push + poll + download
```

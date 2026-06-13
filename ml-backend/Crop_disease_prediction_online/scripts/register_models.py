"""One-shot script: register all 3 models in MLflow.

Usage:

    python scripts/register_models.py

This creates an experiment named ``cpl_crop_disease`` (configurable via
``CPL_MLFLOW_EXPERIMENT_NAME``) and one MLflow run per model:

  1. ``efficientnetb2_disease_v1``  – the primary 139-class classifier.
  2. ``yolov8n_leaf_seg_v1``        – the YOLO leaf segmenter we trained
                                       on Kaggle (mAP@50 = 0.949).
  3. ``hierarchical_b0_router_v1``  – the cross-check classifier
                                       (EfficientNet-B0 + 20 LR heads).

Each run logs:
  - hyperparameters / metadata via ``mlflow.log_params``
  - benchmark metrics via ``mlflow.log_metrics``
  - the model file(s) as artifacts via ``mlflow.log_artifact*``
  - a tag describing the model's role in the pipeline.

The MLflow tracking UI can then visualise these:

    mlflow ui --backend-store-uri file:./mlruns

…and load it in your browser at http://127.0.0.1:5000.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow running ``python scripts/register_models.py`` from the project root.
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import mlflow  # noqa: E402

from cpl_crop.config import get_settings  # noqa: E402


def register_efficientnetb2(*, log_artifacts: bool) -> str:
    """Register the primary B2 SavedModel. Returns the run_id."""
    settings = get_settings()
    saved_model_dir = settings.saved_model_dir
    labels_path = settings.labels_path
    preproc_path = settings.preprocessing_path

    if not saved_model_dir.exists():
        raise FileNotFoundError(f"SavedModel not found at {saved_model_dir}")

    with mlflow.start_run(run_name="efficientnetb2_disease_v1") as run:
        mlflow.set_tag("model_role", "primary_disease_classifier")
        mlflow.set_tag("framework", "tensorflow")
        mlflow.log_params(
            {
                "backbone": "EfficientNetB2",
                "input_size": 260,
                "num_classes": 139,
                "preprocessing": "raw 0..255 (built-in normalisation)",
            }
        )
        mlflow.log_metrics(
            {
                "test_top1_accuracy": 0.9361,
                "test_top3_accuracy": 0.994,
            }
        )
        if log_artifacts:
            mlflow.log_artifacts(str(saved_model_dir), artifact_path="saved_model")
            if labels_path.exists():
                mlflow.log_artifact(str(labels_path))
            if preproc_path.exists():
                mlflow.log_artifact(str(preproc_path))
        return run.info.run_id


def register_yolo_leaf_seg(*, log_artifacts: bool) -> str:
    """Register the YOLOv8n-seg leaf segmenter. Returns the run_id."""
    settings = get_settings()
    weights = settings.yolo_weights_path

    if not weights.exists():
        raise FileNotFoundError(f"YOLO weights not found at {weights}")

    with mlflow.start_run(run_name="yolov8n_leaf_seg_v1") as run:
        mlflow.set_tag("model_role", "leaf_segmenter")
        mlflow.set_tag("framework", "ultralytics_yolov8")
        mlflow.log_params(
            {
                "backbone": "yolov8n-seg",
                "input_size": 640,
                "num_classes": 1,
                "epochs": 80,
                "training_data": "PlantDoc + PlantVillage + new-plant-diseases (~10k images, SAM-distilled labels)",
                "split": "train=7182 / valid=1394 / test=434",
            }
        )
        mlflow.log_metrics(
            {
                "mask_mAP50": 0.949,
                "mask_mAP50_95": 0.848,
            }
        )
        if log_artifacts:
            mlflow.log_artifact(str(weights))
        return run.info.run_id


def register_hierarchical_bundle(*, log_artifacts: bool) -> str:
    """Register the hierarchical cross-check bundle. Returns the run_id."""
    settings = get_settings()
    bundle_dir = settings.hierarchical_bundle_dir

    if not bundle_dir.exists():
        raise FileNotFoundError(f"Hierarchical bundle not found at {bundle_dir}")

    with mlflow.start_run(run_name="hierarchical_b0_router_v1") as run:
        mlflow.set_tag("model_role", "cross_check_classifier")
        mlflow.set_tag("framework", "torch+sklearn")
        mlflow.log_params(
            {
                "backbone": "EfficientNetB0",
                "input_size": 224,
                "num_crops": 20,
                "num_classes": 134,
                "router": "logistic_regression",
                "per_crop_heads": "logistic_regression x 20",
            }
        )
        # Reported metrics from the bundle's own metadata. Populate from
        # bundle_dir/metadata/*.json if present in your local copy.
        mlflow.log_metrics(
            {
                # placeholder; real metrics live in metadata/*.json
                "router_top1_accuracy": 0.0,
                "within_crop_top1_accuracy": 0.0,
            }
        )
        if log_artifacts:
            mlflow.log_artifacts(str(bundle_dir), artifact_path="bundle")
        return run.info.run_id


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--no-artifacts",
        action="store_true",
        help="Skip copying heavy weight files into mlruns/. Just record metadata + metrics.",
    )
    args = parser.parse_args()
    log_artifacts = not args.no_artifacts

    settings = get_settings()
    mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
    mlflow.set_experiment(settings.mlflow_experiment_name)

    print(f"[mlflow] tracking_uri = {settings.mlflow_tracking_uri}")
    print(f"[mlflow] experiment   = {settings.mlflow_experiment_name}")
    print(f"[mlflow] log_artifacts = {log_artifacts}")
    print()

    runs: list[tuple[str, str | None, str | None]] = []
    for name, fn in [
        ("efficientnetb2_disease_v1", register_efficientnetb2),
        ("yolov8n_leaf_seg_v1", register_yolo_leaf_seg),
        ("hierarchical_b0_router_v1", register_hierarchical_bundle),
    ]:
        try:
            run_id = fn(log_artifacts=log_artifacts)
            print(f"  OK  {name:<32}  run_id={run_id}")
            runs.append((name, run_id, None))
        except FileNotFoundError as e:
            print(f"  SKIP {name:<32}  {e}")
            runs.append((name, None, str(e)))

    print()
    print("Done. Inspect runs with:")
    print("    mlflow ui --backend-store-uri", settings.mlflow_tracking_uri)
    return 0 if any(r[1] for r in runs) else 1


if __name__ == "__main__":
    raise SystemExit(main())

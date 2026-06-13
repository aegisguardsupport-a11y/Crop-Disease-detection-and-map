"""Application configuration loaded from environment / .env file.

All settings use the ``CPL_`` prefix. The model bundle is described by
``CPL_BUNDLE_DIR`` and the per-file paths are derived from it; this means
the same bundle can be relocated by changing one variable.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Process-wide configuration."""

    model_config = SettingsConfigDict(
        env_prefix="CPL_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        protected_namespaces=(),  # allow fields whose names start with `model_`
    )

    bundle_dir: Path = Field(
        default=Path("exports"),
        description="Root directory of the extracted model bundle.",
    )
    log_level: str = Field(default="INFO", description="Python logging level.")

    # ----- API settings ---------------------------------------------------
    api_host: str = Field(default="127.0.0.1", description="Bind host for uvicorn.")
    api_port: int = Field(default=8000, ge=1, le=65535)
    api_workers: int = Field(default=1, ge=1, le=64)
    api_log_json: bool = Field(
        default=True,
        description="Render logs as JSON (production) or human-readable (dev).",
    )
    cors_origins: str = Field(
        default="*",
        description=(
            "Comma-separated list of allowed CORS origins. Use '*' for fully open "
            "(hackathon default). Example: 'https://my-app.vercel.app,https://...'."
        ),
    )
    api_max_image_bytes: int = Field(
        default=10 * 1024 * 1024,
        ge=1024,
        description="Reject /predict uploads larger than this.",
    )
    api_max_topk: int = Field(
        default=10,
        ge=1,
        le=139,
        description="Hard cap on the topk query parameter.",
    )
    api_default_topk: int = Field(default=3, ge=1, le=139)
    model_version: str = Field(
        default="0.1.0-efficientnetb2-260",
        description="Reported in API responses; replaced by registry version in Phase 5.",
    )

    # ----- Explainability ------------------------------------------------
    explain_default_num_samples: int = Field(
        default=8,
        ge=1,
        le=64,
        description="Default number of SmoothGrad noisy samples (1 = vanilla saliency).",
    )
    explain_max_num_samples: int = Field(default=32, ge=1, le=128)
    explain_default_noise_level: float = Field(default=0.10, ge=0.0, lt=1.0)
    explain_overlay_alpha: float = Field(default=0.5, ge=0.0, le=1.0)

    # ----- Phase 3.5 validation pipeline ---------------------------------
    # YOLO leaf segmenter
    yolo_weights_path: Path = Field(default=Path("models/leaf_seg/best.pt"))
    yolo_conf_threshold: float = Field(default=0.25, ge=0.0, le=1.0)
    yolo_iou_threshold: float = Field(default=0.45, ge=0.0, le=1.0)

    # OpenCV image-quality thresholds
    quality_min_resolution: int = Field(default=224, ge=32)
    quality_min_blur: float = Field(default=100.0, ge=0.0)
    quality_min_brightness: float = Field(default=40.0, ge=0.0, le=255.0)
    quality_max_brightness: float = Field(default=220.0, ge=0.0, le=255.0)
    quality_min_contrast: float = Field(default=25.0, ge=0.0)

    # Leaf-area validation
    validation_min_leaf_area: float = Field(default=0.05, ge=0.0, le=1.0)
    validation_max_leaf_area: float = Field(default=0.95, ge=0.0, le=1.0)
    validation_optimal_min_area: float = Field(default=0.20, ge=0.0, le=1.0)
    validation_optimal_max_area: float = Field(default=0.70, ge=0.0, le=1.0)

    # Background removal / clean-leaf extraction
    extract_bbox_padding: float = Field(default=0.05, ge=0.0, le=0.5)
    extract_bg_fill: str = Field(default="black")  # "black" | "white" | "mean"

    # Confidence engine weights. Routes renormalize these over only the
    # ACTIVE signals (weights for disabled components are dropped), so a
    # turned-off cross-check never dilutes the score. Relative size is what
    # matters; they need not sum to 1.0. Prediction-reliability (top1 + gap)
    # dominates because image-quality signals are also hard router gates.
    confidence_weight_quality: float = Field(default=0.10, ge=0.0, le=1.0)
    confidence_weight_seg: float = Field(default=0.12, ge=0.0, le=1.0)
    confidence_weight_area: float = Field(default=0.08, ge=0.0, le=1.0)
    confidence_weight_top1: float = Field(default=0.40, ge=0.0, le=1.0)
    confidence_weight_gap: float = Field(default=0.15, ge=0.0, le=1.0)
    confidence_weight_crop_router: float = Field(default=0.06, ge=0.0, le=1.0)
    confidence_weight_per_crop_head: float = Field(default=0.04, ge=0.0, le=1.0)
    confidence_weight_crop_agreement: float = Field(default=0.05, ge=0.0, le=1.0)

    # Decision router thresholds
    router_high_threshold: float = Field(default=0.85, ge=0.0, le=1.0)
    router_medium_threshold: float = Field(default=0.50, ge=0.0, le=1.0)
    # Open-set guard: top-1 below this -> forced retake ("not a recognized crop
    # leaf"), regardless of fused score. Stops sharp non-leaf photos (keyboard,
    # hand, wall) from being confidently mis-diagnosed.
    router_min_top1: float = Field(default=0.45, ge=0.0, le=1.0)

    # Reported in API responses
    leaf_segmenter_version: str = Field(default="cpl-leaf-yolov8n-v1")

    # ----- Crop verifier (CLIP zero-shot) ---------------------------------
    crop_verifier_enabled: bool = Field(default=True)
    # Open-set leaf gate: if CLIP P(image is a crop leaf) < this, force retake
    # ("not a recognized crop leaf"). Rejects keyboards/hands/walls that the
    # closed-world classifier would otherwise confidently mis-label.
    crop_verifier_leaf_min_prob: float = Field(default=0.5, ge=0.0, le=1.0)
    crop_verifier_model: str = Field(default="openai/clip-vit-base-patch32")
    crop_verifier_topk: int = Field(default=5, ge=1, le=20)
    crop_verifier_prompt_template: str = Field(
        default="a photograph of a {crop} leaf",
    )

    # ----- Hierarchical bundle (primary classifier for /predict-v2) -------
    hierarchical_enabled: bool = Field(default=True)
    hierarchical_bundle_dir: Path = Field(default=Path("models/hierarchical"))
    hierarchical_within_crop_topk: int = Field(default=5, ge=1, le=20)
    hierarchical_version: str = Field(default="cpl-hierarchical-effb0-20260422")

    # ----- Phase 5: monitoring + drift ------------------------------------
    monitoring_log_path: Path = Field(
        default=Path("monitoring/requests.jsonl"),
        description="JSONL log of per-request features for drift detection.",
    )
    monitoring_drift_ref_size: int = Field(
        default=20,
        ge=1,
        description="Number of records reserved as the reference window.",
    )
    monitoring_drift_report_path: Path = Field(
        default=Path("monitoring/drift_report.html"),
        description="Where /monitoring/drift-report writes the Evidently HTML.",
    )
    mlflow_tracking_uri: str = Field(
        default="file:./mlruns",
        description="MLflow tracking backend (file path or http://...).",
    )
    mlflow_experiment_name: str = Field(default="cpl_crop_disease")

    # ----- Phase 6: crop-disease RAG advisory ---------------------------
    rag_enabled: bool = Field(
        default=True,
        description="Enable final Gemini+RAG advisory generation when configured.",
    )
    rag_chroma_dir: Path = Field(default=Path("rag/chroma_db"))
    rag_collection_name: str = Field(default="crop_disease_advisory")
    rag_top_k: int = Field(default=6, ge=1, le=20)
    rag_embedding_model: str = Field(default="chroma-default")
    rag_embedding_dimensionality: int = Field(default=768, ge=128, le=3072)
    rag_generation_model: str = Field(default="gemini-2.5-flash")
    gemini_api_key: str | None = Field(
        default=None,
        description=(
            "Gemini key for RAG. Can also be provided as GEMINI_API_KEY "
            "or CPL_GEMINI_API_KEY."
        ),
    )

    # ----- derived paths --------------------------------------------------
    @property
    def saved_model_dir(self) -> Path:
        return self.bundle_dir / "saved_model"

    @property
    def tflite_path(self) -> Path:
        return self.bundle_dir / "cpl_crop_disease_finetuned.tflite"

    @property
    def labels_path(self) -> Path:
        return self.bundle_dir / "cpl_id_to_label.json"

    @property
    def preprocessing_path(self) -> Path:
        return self.bundle_dir / "cpl_preprocessing_config.json"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()

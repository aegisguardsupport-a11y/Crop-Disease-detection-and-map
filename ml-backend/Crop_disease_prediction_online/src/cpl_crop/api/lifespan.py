"""FastAPI lifespan: preload the model and pre-compute hot-path state.

Loading TF + the SavedModel takes 5-15s, so we do it once at startup
rather than on the first request. The bundle, labels, image_size, and
settings end up on ``app.state`` for routes to read.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import TypedDict, cast

import structlog
from fastapi import FastAPI

from cpl_crop.config import Settings, get_settings
from cpl_crop.explain import SmoothGradExplainer
from cpl_crop.hierarchical import HierarchicalBundleRuntime
from cpl_crop.labels import load_labels
from cpl_crop.model_loader import ModelBundle, get_bundle, reset_bundle
from cpl_crop.monitoring import MonitoringLogger
from cpl_crop.preprocessing import load_preprocessing_config
from cpl_crop.rag import AdvisoryService
from cpl_crop.validation import CropVerifier, LeafSegmenter

logger = structlog.get_logger(__name__)


class AppState(TypedDict):
    """Strongly typed view of ``app.state``.

    FastAPI/Starlette stores this as a dynamic ``State`` object; we use
    this TypedDict only for documentation and ``cast`` in handlers.
    """

    settings: Settings
    bundle: ModelBundle
    labels: dict[int, str]
    image_size: tuple[int, int]
    explainer: SmoothGradExplainer
    leaf_segmenter: LeafSegmenter | None  # None if weights file is missing
    crop_verifier: CropVerifier | None  # None if disabled or fails to load
    hierarchical: HierarchicalBundleRuntime | None  # None if disabled or bundle missing
    advisory_service: AdvisoryService | None  # None if RAG index/key/deps are unavailable
    monitoring_logger: MonitoringLogger


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    logger.info(
        "startup.begin",
        bundle_dir=str(settings.bundle_dir),
        model_version=settings.model_version,
    )

    bundle = get_bundle(settings.saved_model_dir)
    labels = load_labels(settings.labels_path)
    cfg = load_preprocessing_config(settings.preprocessing_path)
    h, w = cfg["image_size"]
    image_size: tuple[int, int] = (int(h), int(w))

    if bundle.num_classes != len(labels):
        raise RuntimeError(
            f"Model output dim ({bundle.num_classes}) does not match "
            f"label-map size ({len(labels)})"
        )

    explainer = SmoothGradExplainer(bundle)

    # Phase 3.5: optional YOLO leaf segmenter. If best.pt isn't present,
    # we still serve /predict and /explain — only /predict-v2 fails.
    leaf_segmenter: LeafSegmenter | None
    try:
        leaf_segmenter = LeafSegmenter(
            weights_path=settings.yolo_weights_path,
            conf_threshold=settings.yolo_conf_threshold,
            iou_threshold=settings.yolo_iou_threshold,
        )
    except FileNotFoundError as e:
        leaf_segmenter = None
        logger.warning(
            "leaf_segmenter.unavailable",
            error=str(e),
            note="/predict-v2 will return 503 until best.pt is in place",
        )

    # Phase 3.7: optional CLIP crop verifier. Heavy first-load (~600 MB),
    # but per-request inference is fast (~100 ms CPU).
    crop_verifier: CropVerifier | None = None
    if settings.crop_verifier_enabled:
        try:
            # Bundle's distinct crops, in label-id order
            unique_crops: list[str] = []
            seen: set[str] = set()
            for cid in sorted(labels.keys()):
                crop = labels[cid].split("::", 1)[0]
                if crop not in seen:
                    seen.add(crop)
                    unique_crops.append(crop)
            crop_verifier = CropVerifier(
                crops=unique_crops,
                model_name=settings.crop_verifier_model,
                prompt_template=settings.crop_verifier_prompt_template,
            )
            logger.info("crop_verifier.ready", num_crops=len(unique_crops))
        except Exception as e:
            crop_verifier = None
            logger.warning(
                "crop_verifier.unavailable",
                error=f"{type(e).__name__}: {e}",
                note="/predict-v2 will simply omit crop_verifier_predictions",
            )

    # Phase 3.8: optional hierarchical bundle (primary disease classifier
    # for /predict-v2). Falls back to the B2 SavedModel for /predict and
    # /explain regardless.
    hierarchical: HierarchicalBundleRuntime | None = None
    if settings.hierarchical_enabled:
        try:
            hierarchical = HierarchicalBundleRuntime(settings.hierarchical_bundle_dir)
            logger.info(
                "hierarchical.ready",
                num_crops=len(hierarchical.crops),
                num_classes=hierarchical.num_classes,
            )
        except Exception as e:
            hierarchical = None
            logger.warning(
                "hierarchical.unavailable",
                error=f"{type(e).__name__}: {e}",
                note="/predict-v2 will fall back to the B2 SavedModel classifier",
            )

    advisory_service = AdvisoryService.from_settings(settings)
    if advisory_service is None:
        logger.warning(
            "rag_advisory.unavailable",
            note=(
                "RAG advisories disabled until GEMINI_API_KEY/CPL_GEMINI_API_KEY "
                "and rag/chroma_db are available"
            ),
        )
    else:
        logger.info("rag_advisory.ready", collection=settings.rag_collection_name)

    app.state.settings = settings
    app.state.bundle = bundle
    app.state.labels = labels
    app.state.image_size = image_size
    app.state.explainer = explainer
    app.state.leaf_segmenter = leaf_segmenter
    app.state.crop_verifier = crop_verifier
    app.state.hierarchical = hierarchical
    app.state.advisory_service = advisory_service
    app.state.monitoring_logger = MonitoringLogger(settings.monitoring_log_path)

    logger.info(
        "startup.complete",
        num_classes=bundle.num_classes,
        image_size=list(image_size),
    )
    try:
        yield
    finally:
        logger.info("shutdown")
        reset_bundle()


def get_app_state(app: FastAPI) -> AppState:
    """Return ``app.state`` as a typed mapping (helper for handlers/tests)."""
    return cast(
        AppState,
        {
            "settings": app.state.settings,
            "bundle": app.state.bundle,
            "labels": app.state.labels,
            "image_size": app.state.image_size,
            "explainer": app.state.explainer,
            "leaf_segmenter": app.state.leaf_segmenter,
            "crop_verifier": app.state.crop_verifier,
            "hierarchical": app.state.hierarchical,
            "advisory_service": app.state.advisory_service,
            "monitoring_logger": app.state.monitoring_logger,
        },
    )

"""HTTP routes for the crop-disease API."""

from __future__ import annotations

import io
import time
from dataclasses import asdict
from typing import Annotated

import numpy as np
import structlog
from fastapi import APIRouter, File, HTTPException, Query, Request, UploadFile, status
from PIL import Image, UnidentifiedImageError

from cpl_crop.api.schemas import (
    AdvisoryResponse,
    ConfidenceSignalsSchema,
    CropPredictionItem,
    CropRouterItem,
    CropVerifierItem,
    DiseasePredictionItem,
    DiseaseSeverity,
    DiseaseWithinCropItem,
    ExplainResponse,
    HealthResponse,
    ImageQualityReport,
    LatencyBreakdown,
    LeafAreaReportSchema,
    LeafSegmentationReport,
    ModelVersions,
    PossibleDiseaseItem,
    PredictDiseaseResponse,
    PredictionItem,
    PredictResponse,
    PredictV2Response,
    PrimaryDiagnosis,
    RagExplanation,
    ValidationReport,
)
from cpl_crop.config import Settings
from cpl_crop.explain import (
    SmoothGradExplainer,
    encode_png_base64,
    make_overlay,
    upsample_heatmap,
)
from cpl_crop.explain.overlay import apply_jet_colormap
from cpl_crop.hierarchical import HierarchicalBundleRuntime
from cpl_crop.inference import marginalize_crops, predict_topk
from cpl_crop.labels import load_labels, split_label
from cpl_crop.model_loader import ModelBundle
from cpl_crop.preprocessing import preprocess_image
from cpl_crop.rag import AdvisoryService, build_retake_advisory
from cpl_crop.validation import (
    CropVerifier,
    LeafSegmenter,
    assess_image_quality,
    extract_clean_leaf,
    fuse_confidence,
    route,
    validate_leaf_area,
)

logger = structlog.get_logger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Health / readiness
# ---------------------------------------------------------------------------
@router.get(
    "/health",
    include_in_schema=False,
    response_model=HealthResponse,
    tags=["meta"],
    summary="Liveness probe.",
)
async def health() -> HealthResponse:
    """Always returns 200 if the process is alive."""
    return HealthResponse(status="ok", model_loaded=False)


@router.get(
    "/ready",
    include_in_schema=False,
    response_model=HealthResponse,
    tags=["meta"],
    summary="Readiness probe.",
    responses={503: {"description": "Model not loaded yet."}},
)
async def ready(request: Request) -> HealthResponse:
    """Returns 200 only when the model is loaded into ``app.state``."""
    bundle: ModelBundle | None = getattr(request.app.state, "bundle", None)
    settings: Settings | None = getattr(request.app.state, "settings", None)
    if bundle is None or settings is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model not loaded",
        )
    return HealthResponse(
        status="ok",
        model_loaded=True,
        model_version=settings.model_version,
        num_classes=bundle.num_classes,
    )


# ---------------------------------------------------------------------------
# Predict
# ---------------------------------------------------------------------------
@router.post(
    "/predict",
    include_in_schema=False,
    response_model=PredictResponse,
    tags=["predict"],
    summary="Classify a leaf image into a crop::disease label.",
    responses={
        400: {"description": "Image is empty or undecodable."},
        413: {"description": "File exceeds the configured size limit."},
        422: {"description": "Validation failed (e.g. missing file)."},
    },
)
async def predict(
    request: Request,
    file: Annotated[UploadFile, File(description="Leaf image (JPEG/PNG/etc.).")],
    topk: Annotated[
        int | None,
        Query(ge=1, description="Number of predictions to return. Capped server-side."),
    ] = None,
) -> PredictResponse:
    settings: Settings = request.app.state.settings
    bundle: ModelBundle = request.app.state.bundle
    labels: dict[int, str] = request.app.state.labels
    image_size: tuple[int, int] = request.app.state.image_size

    effective_topk = topk if topk is not None else settings.api_default_topk
    if effective_topk > settings.api_max_topk:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"topk must be <= {settings.api_max_topk}",
        )

    raw = await file.read()
    if not raw:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty file uploaded",
        )
    if len(raw) > settings.api_max_image_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds {settings.api_max_image_bytes} bytes",
        )

    started = time.perf_counter()
    try:
        preds = predict_topk(
            bundle=bundle,
            image=raw,
            image_size=image_size,
            labels=labels,
            topk=effective_topk,
        )
    except (UnidentifiedImageError, OSError) as exc:
        # Pillow raises UnidentifiedImageError for unknown formats and
        # OSError for truncated / unreadable streams.
        logger.warning("predict.bad_image", error=str(exc), filename=file.filename)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot decode image: {exc}",
        ) from exc

    latency_ms = (time.perf_counter() - started) * 1000.0
    rid: str = request.state.request_id

    logger.info(
        "predict.ok",
        topk=effective_topk,
        top1_label=preds[0].label,
        top1_confidence=round(preds[0].confidence, 4),
        latency_ms=round(latency_ms, 2),
        bytes=len(raw),
    )

    return PredictResponse(
        request_id=rid,
        model_version=settings.model_version,
        num_classes=bundle.num_classes,
        latency_ms=latency_ms,
        predictions=[PredictionItem(**asdict(p)) for p in preds],
    )


# Re-exporting load_labels keeps `from cpl_crop.api.routes import *` light;
# real code should import from cpl_crop.labels directly.
__all__ = ["load_labels", "router"]


# ---------------------------------------------------------------------------
# Explain
# ---------------------------------------------------------------------------
@router.post(
    "/explain",
    include_in_schema=False,
    response_model=ExplainResponse,
    tags=["explain"],
    summary="Classify + return a saliency heatmap (SmoothGrad on the SavedModel).",
    responses={
        400: {"description": "Image is empty or undecodable."},
        413: {"description": "File exceeds the configured size limit."},
        422: {"description": "Validation failed (e.g. parameter out of range)."},
    },
)
async def explain(
    request: Request,
    file: Annotated[UploadFile, File(description="Leaf image (JPEG/PNG/etc.).")],
    topk: Annotated[
        int | None,
        Query(ge=1, description="Number of predictions to return."),
    ] = None,
    target_class: Annotated[
        int | None,
        Query(ge=0, description="Class id to explain (default: predicted top-1)."),
    ] = None,
    num_samples: Annotated[
        int | None,
        Query(ge=1, description="SmoothGrad samples (1 = vanilla saliency)."),
    ] = None,
    noise_level: Annotated[
        float | None,
        Query(ge=0.0, lt=1.0, description="Gaussian noise std as fraction of input range."),
    ] = None,
) -> ExplainResponse:
    settings: Settings = request.app.state.settings
    bundle: ModelBundle = request.app.state.bundle
    labels: dict[int, str] = request.app.state.labels
    image_size: tuple[int, int] = request.app.state.image_size
    explainer: SmoothGradExplainer = request.app.state.explainer

    eff_topk = topk if topk is not None else settings.api_default_topk
    if eff_topk > settings.api_max_topk:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"topk must be <= {settings.api_max_topk}",
        )
    eff_n = num_samples if num_samples is not None else settings.explain_default_num_samples
    if eff_n > settings.explain_max_num_samples:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"num_samples must be <= {settings.explain_max_num_samples}",
        )
    eff_noise = noise_level if noise_level is not None else settings.explain_default_noise_level
    if target_class is not None and target_class >= bundle.num_classes:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"target_class must be < {bundle.num_classes}",
        )

    raw = await file.read()
    if not raw:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty file uploaded",
        )
    if len(raw) > settings.api_max_image_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds {settings.api_max_image_bytes} bytes",
        )

    started = time.perf_counter()
    try:
        # Top-k predictions (cheap; one forward pass).
        preds = predict_topk(
            bundle=bundle,
            image=raw,
            image_size=image_size,
            labels=labels,
            topk=eff_topk,
        )

        # Re-decode and preprocess for saliency input. We could share with
        # predict_topk but the cost is tiny relative to gradient computation.
        with Image.open(io.BytesIO(raw)) as im:
            base_img = im.convert("RGB").resize(image_size, Image.Resampling.BILINEAR)
        x = preprocess_image(base_img, image_size)

        result = explainer.explain(
            x,
            class_id=target_class,
            num_samples=eff_n,
            noise_level=eff_noise,
        )
    except (UnidentifiedImageError, OSError) as exc:
        logger.warning("explain.bad_image", error=str(exc), filename=file.filename)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot decode image: {exc}",
        ) from exc

    # Rendering
    upsampled = upsample_heatmap(result.heatmap, image_size)
    heatmap_only = apply_jet_colormap(upsampled)
    overlay = make_overlay(base_img, upsampled, alpha=settings.explain_overlay_alpha)

    latency_ms = (time.perf_counter() - started) * 1000.0
    rid: str = request.state.request_id

    explained_label = labels[result.class_id]
    crop, disease = split_label(explained_label)

    logger.info(
        "explain.ok",
        topk=eff_topk,
        num_samples=eff_n,
        noise_level=eff_noise,
        explained_class=explained_label,
        explained_score=round(result.class_score, 4),
        latency_ms=round(latency_ms, 2),
        bytes=len(raw),
    )

    return ExplainResponse(
        request_id=rid,
        model_version=settings.model_version,
        num_classes=bundle.num_classes,
        latency_ms=latency_ms,
        predictions=[PredictionItem(**asdict(p)) for p in preds],
        explained_class_id=result.class_id,
        explained_class_label=f"{crop}::{disease}",
        method="smoothgrad" if eff_n > 1 and eff_noise > 0 else "saliency",
        num_samples=result.num_samples,
        noise_level=result.noise_level,
        heatmap_png_b64=encode_png_base64(heatmap_only),
        overlay_png_b64=encode_png_base64(overlay),
    )


# ---------------------------------------------------------------------------
# /predict-v2 — restructured pipeline:
#   1) Leaf check (YOLO: is it a real leaf?)
#   2) Crop prediction (hierarchical crop router on original image)
#   3) Segmentation + masking (extract clean leaf with crop name)
#   4) Disease prediction (per-crop head on masked image)
# ---------------------------------------------------------------------------
@router.post(
    "/predict-v2",
    include_in_schema=False,
    response_model=PredictV2Response,
    tags=["predict"],
    summary="Pipeline: leaf check -> crop prediction -> segmentation+masking -> disease prediction.",
    responses={
        400: {"description": "Image is empty or undecodable."},
        413: {"description": "File exceeds the configured size limit."},
        503: {"description": "Leaf segmenter weights not loaded on the server."},
    },
)
async def predict_v2(
    request: Request,
    file: Annotated[UploadFile, File(description="Leaf image (JPEG/PNG/etc.).")],
    topk: Annotated[
        int | None,
        Query(ge=1, description="Number of top predictions to return."),
    ] = None,
    explain: Annotated[
        bool,
        Query(description="If true, also generate a SmoothGrad heatmap overlay."),
    ] = True,
) -> PredictV2Response:
    settings: Settings = request.app.state.settings
    bundle: ModelBundle = request.app.state.bundle
    labels: dict[int, str] = request.app.state.labels
    image_size: tuple[int, int] = request.app.state.image_size
    explainer: SmoothGradExplainer = request.app.state.explainer
    leaf_segmenter: LeafSegmenter | None = request.app.state.leaf_segmenter
    crop_verifier: CropVerifier | None = request.app.state.crop_verifier
    hierarchical: HierarchicalBundleRuntime | None = request.app.state.hierarchical
    advisory_service: AdvisoryService | None = request.app.state.advisory_service

    if leaf_segmenter is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Leaf segmenter is not loaded. Place best.pt at "
                f"{settings.yolo_weights_path} and restart the server."
            ),
        )

    rid: str = request.state.request_id
    eff_topk = topk if topk is not None else settings.api_default_topk
    if eff_topk > settings.api_max_topk:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"topk must be <= {settings.api_max_topk}",
        )

    # ---- Stage 1: file validation (bytes + size) -----------------------
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file uploaded")
    if len(raw) > settings.api_max_image_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds {settings.api_max_image_bytes} bytes",
        )

    pipeline_started = time.perf_counter()

    # Decode the image once into a numpy array
    try:
        with Image.open(io.BytesIO(raw)) as im:
            # Apply EXIF rotation; force RGB to handle RGBA/P/CMYK/L modes safely
            from PIL import ImageOps  # local import keeps top-level lean

            im = ImageOps.exif_transpose(im)
            original_pil = im.convert("RGB")
    except (UnidentifiedImageError, OSError) as exc:
        logger.warning("predictv2.bad_image", error=str(exc), filename=file.filename)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot decode image: {exc}",
        ) from exc

    image_rgb = np.asarray(original_pil, dtype=np.uint8)

    # Defensive size cap. Multi-megapixel uploads (Kaggle 4000x6000, phone
    # cameras, etc.) can OOM the YOLO/torch C extensions and crash uvicorn.
    max_dim = 2048
    h0, w0 = image_rgb.shape[:2]
    if max(h0, w0) > max_dim:
        import cv2 as _cv2  # local import; opencv already a dep

        scale = max_dim / float(max(h0, w0))
        new_w, new_h = round(w0 * scale), round(h0 * scale)
        image_rgb = _cv2.resize(image_rgb, (new_w, new_h), interpolation=_cv2.INTER_AREA).astype(
            np.uint8
        )
        logger.info(
            "predictv2.image_resized",
            original_hw=[h0, w0],
            new_hw=[new_h, new_w],
            scale=round(scale, 3),
        )

    logger.info(
        "predictv2.image_decoded",
        shape=list(image_rgb.shape),
        dtype=str(image_rgb.dtype),
        bytes=len(raw),
    )

    # ---- STAGE 1: Is it a real leaf? (YOLO segmentation) ---------------
    t = time.perf_counter()
    seg = leaf_segmenter.segment(image_rgb)
    segmentation_ms = (time.perf_counter() - t) * 1000.0

    seg_report = LeafSegmentationReport(
        detected=seg.detected,
        confidence=seg.confidence,
        bbox_xyxy=list(seg.bbox_xyxy) if seg.bbox_xyxy else None,
        num_detections=seg.num_detections,
        leaf_area_ratio=seg.leaf_area_ratio,
    )

    # Image quality (run in parallel for reporting, doesn't gate the pipeline)
    t = time.perf_counter()
    quality = assess_image_quality(
        image_rgb,
        min_resolution=settings.quality_min_resolution,
        min_blur=settings.quality_min_blur,
        min_brightness=settings.quality_min_brightness,
        max_brightness=settings.quality_max_brightness,
        min_contrast=settings.quality_min_contrast,
    )
    quality_ms = (time.perf_counter() - t) * 1000.0
    quality_report = ImageQualityReport(**quality.to_json())

    # ---- Stages 5 + 6: leaf-area validation + clean leaf extraction ----
    leaf_area_report_schema: LeafAreaReportSchema | None = None
    clean_leaf_b64: str | None = None
    mask_overlay_b64: str | None = None
    extract_ms = 0.0

    classifier_top1 = 0.0
    prediction_gap = 0.0
    predictions: list[PredictionItem] = []
    top_crops_items: list[CropPredictionItem] = []
    crop_router_items: list[CropRouterItem] = []
    disease_within_top_crop_items: list[DiseaseWithinCropItem] = []
    crop_verifier_items: list[CropVerifierItem] = []
    crop_verifier_agreement: bool | None = None
    classifier_used = "efficientnetb2"
    crop_router_top1_confidence = 0.0
    per_crop_head_top1_confidence = 0.0
    explanation_b64: str | None = None
    classification_ms = 0.0
    explain_ms = 0.0
    advisory_ms = 0.0
    advisory: AdvisoryResponse | None = None

    if seg.detected and seg.mask is not None:
        leaf_area = validate_leaf_area(
            seg.leaf_area_ratio,
            hard_min=settings.validation_min_leaf_area,
            hard_max=settings.validation_max_leaf_area,
            optimal_min=settings.validation_optimal_min_area,
            optimal_max=settings.validation_optimal_max_area,
        )
        leaf_area_report_schema = LeafAreaReportSchema(**leaf_area.to_json())

        # Build a mask-overlay PNG for the UI step "Leaf detected".
        overlay_arr = image_rgb.copy()
        overlay_arr[seg.mask] = (
            overlay_arr[seg.mask].astype(np.float32) * 0.45
            + np.array([255, 80, 80], dtype=np.float32) * 0.55
        ).astype(np.uint8)
        mask_overlay_b64 = encode_png_base64(overlay_arr)

        if leaf_area.ok:
            t = time.perf_counter()
            clean = extract_clean_leaf(
                image_rgb,
                seg.mask,
                target_size=image_size,
                padding=settings.extract_bbox_padding,
                fill=settings.extract_bg_fill,  # type: ignore[arg-type]
            )
            extract_ms = (time.perf_counter() - t) * 1000.0
            clean_leaf_b64 = encode_png_base64(clean.image)

            # ---- Stage 7: PRIMARY classifier — Crop_disease_prediction_online's
            # EfficientNetB2 SavedModel. This is the headline disease prediction.
            t = time.perf_counter()
            x = clean.image.astype(np.float32)[None, ...]
            probs = bundle.predict(x)[0]  # (139,)
            classification_ms = (time.perf_counter() - t) * 1000.0
            classifier_used = "efficientnetb2"

            order = np.argsort(-probs)[: max(eff_topk, 2)]
            classifier_top1 = float(probs[int(order[0])])
            prediction_gap = float(probs[int(order[0])] - probs[int(order[1])])

            for rank, idx in enumerate(order[:eff_topk], start=1):
                lbl = labels[int(idx)]
                crop_, disease_ = split_label(lbl)
                predictions.append(
                    PredictionItem(
                        rank=rank,
                        label=lbl,
                        crop=crop_,
                        disease=disease_,
                        confidence=float(probs[int(idx)]),
                    )
                )

            # B2's implicit crop ranking via marginalisation (the bundle's own crop view)
            unique_crops = {c.split("::")[0] for c in labels.values()}
            crop_marginals = marginalize_crops(probs, labels, topk=min(5, len(unique_crops)))
            top_crops_items = [
                CropPredictionItem(
                    rank=cp.rank,
                    crop=cp.crop,
                    confidence=cp.confidence,
                    top_disease=cp.top_disease,
                    top_disease_label=cp.top_disease_label,
                    top_disease_conditional=cp.top_disease_conditional,
                    top_disease_joint=cp.top_disease_joint,
                )
                for cp in crop_marginals
            ]

            # ---- Stage 7b: SECONDARY (cross-check only) — hierarchical bundle.
            # Provides an independent crop opinion via the trained router. Its
            # disease predictions are NOT used as the headline; B2's are.
            if hierarchical is not None:
                try:
                    hres = hierarchical.predict(
                        clean.image,
                        topk=eff_topk,
                        within_crop_topk=settings.hierarchical_within_crop_topk,
                    )
                    for cr in hres.crop_router:
                        crop_router_items.append(
                            CropRouterItem(rank=cr.rank, crop=cr.crop, confidence=cr.confidence)
                        )
                    if crop_router_items:
                        crop_router_top1_confidence = crop_router_items[0].confidence

                    for dw in hres.within_top_crop:
                        disease_within_top_crop_items.append(
                            DiseaseWithinCropItem(
                                rank=dw.rank,
                                crop=dw.crop,
                                disease=dw.disease,
                                label=dw.label,
                                confidence=dw.confidence,
                            )
                        )
                    if disease_within_top_crop_items:
                        per_crop_head_top1_confidence = disease_within_top_crop_items[0].confidence
                except Exception as e:
                    logger.warning(
                        "predictv2.hierarchical_failed", error=f"{type(e).__name__}: {e}"
                    )

            # ---- Stage 7c: TERTIARY (cross-check only) — CLIP zero-shot.
            if crop_verifier is not None:
                try:
                    matches = crop_verifier.verify(clean.image, topk=settings.crop_verifier_topk)
                    crop_verifier_items = [
                        CropVerifierItem(rank=m.rank, crop=m.crop, similarity=m.similarity)
                        for m in matches
                    ]
                    if matches:
                        # Strongest agreement: B2's top-1 crop should appear in CLIP's top-3
                        # AND in the hierarchical router's top-1 if hierarchical is loaded.
                        b2_top_crop = predictions[0].crop if predictions else None
                        clip_top_crops_3 = [c.crop for c in matches[:3]]
                        clip_agrees_with_b2 = b2_top_crop in clip_top_crops_3
                        if crop_router_items and b2_top_crop is not None:
                            router_agrees_with_b2 = crop_router_items[0].crop == b2_top_crop
                            crop_verifier_agreement = clip_agrees_with_b2 and router_agrees_with_b2
                        else:
                            crop_verifier_agreement = clip_agrees_with_b2
                except Exception as e:
                    logger.warning(
                        "predictv2.crop_verifier_failed", error=f"{type(e).__name__}: {e}"
                    )

            # ---- Stage 7d (optional): SmoothGrad explanation on B2 ----
            if explain:
                t = time.perf_counter()
                exp_result = explainer.explain(
                    x,
                    class_id=int(order[0]),
                    num_samples=settings.explain_default_num_samples,
                    noise_level=settings.explain_default_noise_level,
                )
                upsampled = upsample_heatmap(exp_result.heatmap, image_size)
                explanation_overlay = make_overlay(
                    Image.fromarray(clean.image),
                    upsampled,
                    alpha=settings.explain_overlay_alpha,
                )
                explanation_b64 = encode_png_base64(explanation_overlay)
                explain_ms = (time.perf_counter() - t) * 1000.0

    # ---- Stage 8: confidence engine ------------------------------------
    crop_agreement_signal = 1.0 if crop_verifier_agreement else 0.0
    signals = fuse_confidence(
        quality_score=quality.score,
        seg_confidence=seg.confidence,
        leaf_area_score=leaf_area_report_schema.score if leaf_area_report_schema else 0.0,
        classifier_top1=classifier_top1,
        prediction_gap=prediction_gap,
        crop_router_confidence=crop_router_top1_confidence,
        per_crop_head_confidence=per_crop_head_top1_confidence,
        crop_agreement=crop_agreement_signal,
    )

    # ---- Stage 9: decision routing -------------------------------------
    routing = route(
        signals,
        high_threshold=settings.router_high_threshold,
        medium_threshold=settings.router_medium_threshold,
        quality_failures=quality.failures,
        seg_detected=seg.detected,
        leaf_area_failure=(leaf_area_report_schema.failure if leaf_area_report_schema else None),
    )

    # ---- Stage 10: RAG/Gemini final advisory ---------------------------
    t = time.perf_counter()
    if routing.decision.value == "retake":
        advisory_result = build_retake_advisory(
            reason=routing.reason.value if routing.reason else None,
            guidance=routing.guidance,
        )
        advisory = AdvisoryResponse(**advisory_result.to_json())
    elif advisory_service is not None and predictions:
        try:
            top = predictions[0]
            advisory_result = advisory_service.advise(
                label=top.label,
                crop=top.crop,
                disease=top.disease,
                decision=routing.decision.value,
                confidence=signals.final,
            )
            advisory = AdvisoryResponse(**advisory_result.to_json())
        except Exception as e:
            logger.warning("rag_advisory.failed", error=f"{type(e).__name__}: {e}")
    advisory_ms = (time.perf_counter() - t) * 1000.0

    total_ms = (time.perf_counter() - pipeline_started) * 1000.0

    logger.info(
        "predictv2.done",
        decision=routing.decision.value,
        confidence=round(signals.final, 4),
        top1=predictions[0].label if predictions else None,
        top1_conf=round(predictions[0].confidence, 4) if predictions else None,
        retake_reason=routing.reason.value if routing.reason else None,
        total_ms=round(total_ms, 2),
    )

    # ---- Phase 5: monitoring log (per-request features for drift) ------
    monitoring_logger = getattr(request.app.state, "monitoring_logger", None)
    if monitoring_logger is not None:
        try:
            from cpl_crop.monitoring import extract_features

            features = extract_features(
                request_id=rid,
                image_shape=(image_rgb.shape[0], image_rgb.shape[1]),
                quality={
                    "brightness": quality.brightness,
                    "contrast": quality.contrast,
                    "blur_score": quality.blur,
                },
                segmentation_score=seg.confidence,
                area_fraction=(leaf_area_report_schema.ratio if leaf_area_report_schema else 0.0),
                top1_confidence=classifier_top1,
                confidence_gap=prediction_gap,
                fused_confidence=signals.final,
                decision=routing.decision.value,
                top1_label=predictions[0].label if predictions else "unknown::unknown",
                crop_agreement=bool(crop_verifier_agreement),
                latency_ms=total_ms,
            )
            monitoring_logger.log(features)
        except Exception as e:  # logging must never crash the request
            logger.warning("monitoring.log_failed", error=f"{type(e).__name__}: {e}")

    return PredictV2Response(
        request_id=rid,
        decision=routing.decision.value,
        confidence=signals.final,
        predictions=predictions,
        top_crops=top_crops_items,
        crop_verifier_predictions=crop_verifier_items,
        crop_router_predictions=crop_router_items,
        disease_within_top_crop=disease_within_top_crop_items,
        crop_verifier_agreement=crop_verifier_agreement,
        classifier_used=classifier_used,
        explanation_overlay_png_b64=explanation_b64,
        validation=ValidationReport(
            image_quality=quality_report,
            leaf_segmentation=seg_report,
            leaf_area=leaf_area_report_schema,
        ),
        confidence_signals=ConfidenceSignalsSchema(**signals.to_json()),
        mask_overlay_png_b64=mask_overlay_b64,
        clean_leaf_png_b64=clean_leaf_b64,
        retake_reason=routing.reason.value if routing.reason else None,
        retake_guidance=routing.guidance,
        latency=LatencyBreakdown(
            quality_ms=quality_ms,
            segmentation_ms=segmentation_ms,
            extract_ms=extract_ms,
            classification_ms=classification_ms,
            explain_ms=explain_ms,
            advisory_ms=advisory_ms,
            total_ms=total_ms,
        ),
        model_versions=ModelVersions(
            leaf_segmenter=settings.leaf_segmenter_version,
            disease_classifier=settings.model_version,
        ),
        advisory=advisory,
    )


@router.post(
    "/predictdisease",
    response_model=PredictDiseaseResponse,
    tags=["predict"],
    summary="Slim disease prediction response with RAG advisory.",
    responses={
        400: {"description": "Image is empty or undecodable."},
        413: {"description": "File exceeds the configured size limit."},
        503: {"description": "Leaf segmenter weights not loaded on the server."},
    },
)
async def predict_disease(
    request: Request,
    file: Annotated[UploadFile, File(description="Leaf image (JPEG/PNG/etc.).")],
) -> PredictDiseaseResponse:
    """Run the full /predict-v2 pipeline and return only disease advisory fields."""
    full_response = await predict_v2(
        request=request,
        file=file,
        topk=3,
        explain=False,
    )
    return _to_predict_disease_response(full_response)


def _to_predict_disease_response(response: PredictV2Response) -> PredictDiseaseResponse:
    top_predictions = [
        DiseasePredictionItem(
            rank=pred.rank,
            label=pred.label,
            crop=pred.crop,
            disease=pred.disease,
            confidence=pred.confidence,
        )
        for pred in response.predictions[:3]
    ]
    crop_name = _resolve_crop_name(response)
    advisory = _to_rag_explanation(response)
    severity = _derive_disease_severity(response)
    primary_diagnosis = _to_primary_diagnosis(response)

    return PredictDiseaseResponse(
        crop_name=crop_name,
        primary_diagnosis=primary_diagnosis,
        top_3_predictions=top_predictions,
        possible_other_diseases=_to_possible_other_diseases(response),
        severity=severity,
        urgency=_derive_urgency(response=response, severity=severity, primary=primary_diagnosis),
        symptoms_to_confirm=_take_items(advisory.symptoms_to_check, limit=6),
        what_to_do_now=_farmer_action_steps(response=response, advisory=advisory),
        prevention_tips=_farmer_prevention_tips(advisory),
        when_to_call_expert=_when_to_call_expert(
            response=response, severity=severity, advisory=advisory
        ),
        retake_image_guidance=(response.retake_guidance if response.decision == "retake" else None),
        rag_explanation=advisory,
    )


def _to_primary_diagnosis(response: PredictV2Response) -> PrimaryDiagnosis:
    if not response.predictions:
        crop_name = _resolve_crop_name(response)
        return PrimaryDiagnosis(
            label=None,
            crop=crop_name,
            disease=None,
            display_name="No reliable disease diagnosis",
            is_healthy=False,
            confidence=response.confidence,
            confidence_badge=_confidence_badge(response.confidence),
        )

    top = response.predictions[0]
    return PrimaryDiagnosis(
        label=top.label,
        crop=top.crop,
        disease=top.disease,
        display_name=f"{_humanize_label_part(top.crop)} - {_humanize_label_part(top.disease)}",
        is_healthy=_is_healthy_label(top.disease),
        confidence=top.confidence,
        confidence_badge=_confidence_badge(top.confidence),
    )


def _to_possible_other_diseases(
    response: PredictV2Response,
) -> list[PossibleDiseaseItem]:
    return [
        PossibleDiseaseItem(
            rank=pred.rank,
            label=pred.label,
            crop=pred.crop,
            disease=pred.disease,
            confidence=pred.confidence,
            confidence_badge=_confidence_badge(pred.confidence),
        )
        for pred in response.predictions[1:3]
    ]


def _confidence_badge(confidence: float) -> str:
    if confidence >= 0.80:
        return "High"
    if confidence >= 0.50:
        return "Medium"
    return "Low"


def _humanize_label_part(value: str | None) -> str:
    if not value:
        return "Unknown"
    return value.replace("_", " ").strip().title()


def _is_healthy_label(disease: str | None) -> bool:
    if not disease:
        return False
    normalized = disease.lower().replace("_", " ")
    return "healthy" in normalized or normalized in {"normal", "no disease"}


def _derive_urgency(
    *,
    response: PredictV2Response,
    severity: DiseaseSeverity,
    primary: PrimaryDiagnosis,
) -> str:
    if response.decision == "retake":
        return "Retake image"
    if primary.is_healthy:
        return "Monitor"
    if severity.level == "high":
        return "Act immediately"
    if severity.level == "medium":
        return "Act soon"
    return "Monitor"


def _farmer_action_steps(
    *,
    response: PredictV2Response,
    advisory: RagExplanation,
) -> list[str]:
    if response.decision == "retake":
        return [
            response.retake_guidance
            or "Retake the photo in daylight with one clear leaf filling most of the frame."
        ]
    if advisory.immediate_actions:
        return _take_items(advisory.immediate_actions, limit=5)
    return [
        "Confirm the visible symptoms on the plant before applying any treatment.",
        "Check nearby plants for similar symptoms and separate heavily affected leaves if possible.",
    ]


def _farmer_prevention_tips(advisory: RagExplanation) -> list[str]:
    tips = _dedupe_items([*advisory.prevention, *advisory.precautions])
    if tips:
        return _take_items(tips, limit=6)
    return [
        "Keep the crop well spaced and avoid excess moisture on leaves.",
        "Remove old infected plant debris after harvest.",
        "Use locally recommended seed treatment and resistant varieties where available.",
    ]


def _when_to_call_expert(
    *,
    response: PredictV2Response,
    severity: DiseaseSeverity,
    advisory: RagExplanation,
) -> str:
    if response.decision == "retake":
        return (
            "Call an expert if repeated clear photos still fail or if the crop is "
            "visibly wilting, drying, or spreading symptoms quickly."
        )
    if advisory.expert_advice:
        return advisory.expert_advice
    if severity.level == "high":
        return (
            "Call an expert if symptoms are spreading to nearby plants, grain/fruit is "
            "affected, or a spray decision is needed."
        )
    return (
        "Call an expert if symptoms spread after 2-3 days, cover many leaves, or you are "
        "unsure before using chemicals."
    )


def _take_items(items: list[str], *, limit: int) -> list[str]:
    return _dedupe_items(items)[:limit]


def _dedupe_items(items: list[str]) -> list[str]:
    seen: set[str] = set()
    cleaned: list[str] = []
    for item in items:
        normalized = " ".join(item.strip().split())
        key = normalized.lower()
        if normalized and key not in seen:
            seen.add(key)
            cleaned.append(normalized)
    return cleaned


def _resolve_crop_name(response: PredictV2Response) -> str | None:
    if response.predictions:
        return response.predictions[0].crop
    if response.advisory is not None and response.advisory.crop:
        return response.advisory.crop
    if response.top_crops:
        return response.top_crops[0].crop
    return None


def _derive_disease_severity(response: PredictV2Response) -> DiseaseSeverity:
    confidence = response.confidence
    if response.decision == "retake":
        return DiseaseSeverity(
            level="unknown",
            confidence=confidence,
            decision=response.decision,
            basis=(
                response.retake_guidance
                or "The image did not pass the validation checks, so disease severity cannot be estimated."
            ),
        )

    if response.decision == "expert_review":
        return DiseaseSeverity(
            level="medium",
            confidence=confidence,
            decision=response.decision,
            basis=(
                "The model found a plausible disease signal, but confidence or validation "
                "signals are not strong enough for a high-confidence result. Please confirm "
                "with close visual inspection or an expert."
            ),
        )

    if confidence >= 0.85:
        level = "high"
        basis = (
            "The pipeline produced a high-confidence disease result. Treat this as an "
            "urgent advisory and inspect nearby plants for spread."
        )
    elif confidence >= 0.65:
        level = "medium"
        basis = (
            "The pipeline produced a moderate-confidence disease result. Start basic "
            "precautions and confirm symptoms before applying treatment."
        )
    else:
        level = "low"
        basis = (
            "The pipeline confidence is low. Use the RAG guidance only as a checklist "
            "and retake the image if symptoms are unclear."
        )

    return DiseaseSeverity(
        level=level,
        confidence=confidence,
        decision=response.decision,
        basis=basis,
    )


def _to_rag_explanation(response: PredictV2Response) -> RagExplanation:
    advisory = response.advisory
    if advisory is None:
        return RagExplanation(
            status="unavailable",
            source="none",
            summary=(
                "RAG advisory is not available for this request because the vector "
                "database or Gemini configuration is not loaded on the server."
            ),
            safety_note=(
                "Use the model prediction only as a screening signal and confirm "
                "symptoms before applying any treatment."
            ),
        )
    return RagExplanation(
        status=advisory.status,
        source=advisory.source,
        summary=advisory.summary,
        symptoms_to_check=advisory.symptoms_to_check,
        immediate_actions=advisory.immediate_actions,
        precautions=advisory.precautions,
        prevention=advisory.prevention,
        similar_diseases=advisory.similar_diseases,
        expert_advice=advisory.expert_advice,
        safety_note=advisory.safety_note,
    )


# ============================================================================
# Phase 5 — Monitoring & drift endpoints
# ============================================================================


@router.get(
    "/monitoring/stats",
    include_in_schema=False,
    summary="Per-request monitoring log statistics",
    description=(
        "Returns the size of the monitoring log, the most recent records, "
        "and counts by decision class. Use this to verify that requests "
        "are being captured for drift analysis."
    ),
    tags=["monitoring"],
)
def monitoring_stats(
    request: Request, n_recent: int = Query(default=10, ge=1, le=100)
) -> dict[str, object]:
    """Expose the JSONL log size + recent activity for the demo UI / ops."""
    monitoring_logger = getattr(request.app.state, "monitoring_logger", None)
    if monitoring_logger is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="monitoring is not enabled on this instance",
        )
    total = monitoring_logger.count()
    recent = monitoring_logger.tail(n_recent)
    decisions: dict[str, int] = {}
    for r in recent:
        d = str(r.get("decision", "unknown"))
        decisions[d] = decisions.get(d, 0) + 1
    return {
        "log_path": str(monitoring_logger.path),
        "total_records": total,
        "recent_count": len(recent),
        "recent_decision_breakdown": decisions,
        "recent": recent,
    }


@router.post(
    "/monitoring/drift-report",
    include_in_schema=False,
    summary="Generate an Evidently drift report",
    description=(
        "Splits the monitoring log into a reference window (the first "
        "``ref_size`` records) and a current window (the rest), runs an "
        "Evidently DataDriftPreset, and writes an HTML report. "
        "Returns a small JSON status with row counts and the file path. "
        "Open the HTML in a browser for the full visualisation."
    ),
    tags=["monitoring"],
)
def monitoring_drift_report(
    request: Request,
    ref_size: int = Query(
        default=20,
        ge=1,
        description="Number of leading records to use as the drift reference.",
    ),
) -> dict[str, object]:
    """Run drift detection on the current monitoring log."""
    monitoring_logger = getattr(request.app.state, "monitoring_logger", None)
    settings: Settings = request.app.state.settings
    if monitoring_logger is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="monitoring is not enabled on this instance",
        )

    from cpl_crop.monitoring.drift import generate_drift_report

    records = list(monitoring_logger.iter_records())
    out_path = settings.monitoring_drift_report_path
    result = generate_drift_report(records, out_path, ref_size=ref_size)
    return result

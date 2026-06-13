"""Pydantic request / response models for the API."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class PredictionItem(BaseModel):
    """One ranked prediction in a /predict response."""

    model_config = ConfigDict(frozen=True)

    rank: int = Field(ge=1, description="1-based rank, 1 = highest confidence.")
    label: str = Field(
        description="Full crop::disease label, e.g. 'tomato::Late_blight'.",
    )
    crop: str = Field(description="Crop part of the label.")
    disease: str = Field(description="Disease part of the label.")
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Softmax probability (NOT calibrated).",
    )


class PredictResponse(BaseModel):
    """Body of a successful /predict call."""

    request_id: str = Field(description="Echoed request id (also on X-Request-ID header).")
    model_version: str = Field(description="Identifier of the served model.")
    num_classes: int = Field(description="Output dimensionality of the model.")
    latency_ms: float = Field(
        ge=0.0,
        description="Server-side inference latency, excluding network/IO.",
    )
    predictions: list[PredictionItem]


class HealthResponse(BaseModel):
    """Body of /health and /ready."""

    status: str = "ok"
    model_loaded: bool
    model_version: str | None = None
    num_classes: int | None = None


class ErrorResponse(BaseModel):
    """Generic error body returned by the exception handlers."""

    request_id: str
    detail: str
    code: str


class ExplainResponse(BaseModel):
    """Body of /explain. Includes top-k predictions plus a heatmap overlay."""

    request_id: str
    model_version: str
    num_classes: int
    latency_ms: float
    predictions: list[PredictionItem]

    # The class whose attention the heatmap visualises (default: top-1).
    explained_class_id: int
    explained_class_label: str

    # SmoothGrad parameters used for this run.
    method: str = Field(default="smoothgrad")
    num_samples: int
    noise_level: float

    # Base64-encoded PNGs (data only, no "data:image/png;base64," prefix).
    heatmap_png_b64: str = Field(
        description="Heatmap-only PNG, jet colormap, same dimensions as the input.",
    )
    overlay_png_b64: str = Field(
        description="Heatmap alpha-blended onto the original image.",
    )


# ---------------------------------------------------------------------------
# /predict-v2 — full validation pipeline
# ---------------------------------------------------------------------------
class ImageQualityReport(BaseModel):
    ok: bool
    score: float
    resolution: list[int]
    blur: float
    brightness: float
    contrast: float
    failures: list[str]


class LeafSegmentationReport(BaseModel):
    detected: bool
    confidence: float
    bbox_xyxy: list[float] | None = None
    num_detections: int
    leaf_area_ratio: float


class LeafAreaReportSchema(BaseModel):
    ratio: float
    score: float
    ok: bool
    failure: str | None = None


class ConfidenceSignalsSchema(BaseModel):
    final: float
    quality_score: float
    seg_confidence: float
    leaf_area_score: float
    classifier_top1: float
    prediction_gap: float
    crop_router_confidence: float = 0.0
    per_crop_head_confidence: float = 0.0
    crop_agreement: float = 0.0
    weights: dict[str, float]


class ValidationReport(BaseModel):
    image_quality: ImageQualityReport
    leaf_segmentation: LeafSegmentationReport
    leaf_area: LeafAreaReportSchema | None = None


class LatencyBreakdown(BaseModel):
    quality_ms: float = 0.0
    segmentation_ms: float = 0.0
    extract_ms: float = 0.0
    classification_ms: float = 0.0
    explain_ms: float = 0.0
    advisory_ms: float = 0.0
    total_ms: float = 0.0


class ModelVersions(BaseModel):
    leaf_segmenter: str
    disease_classifier: str


class AdvisoryResponse(BaseModel):
    """Final farmer-facing RAG advisory attached to /predict-v2."""

    status: str
    source: str
    label: str | None = None
    crop: str | None = None
    disease: str | None = None
    summary: str
    symptoms_to_check: list[str] = Field(default_factory=list)
    immediate_actions: list[str] = Field(default_factory=list)
    precautions: list[str] = Field(default_factory=list)
    prevention: list[str] = Field(default_factory=list)
    similar_diseases: list[str] = Field(default_factory=list)
    expert_advice: str = ""
    safety_note: str = ""
    retrieved_chunks: list[dict[str, object]] = Field(default_factory=list)


class DiseasePredictionItem(BaseModel):
    """One ranked disease prediction in the slim /predictdisease response."""

    rank: int = Field(ge=1)
    label: str = Field(description="Full crop::disease label.")
    crop: str
    disease: str
    confidence: float = Field(ge=0.0, le=1.0)


class PrimaryDiagnosis(BaseModel):
    """Farmer-facing top diagnosis summary."""

    label: str | None = Field(default=None, description="Full crop::disease label.")
    crop: str | None = None
    disease: str | None = None
    display_name: str
    is_healthy: bool
    confidence: float = Field(ge=0.0, le=1.0)
    confidence_badge: str = Field(description="High | Medium | Low")


class PossibleDiseaseItem(BaseModel):
    """Alternative diagnosis shown as a caution, not the primary answer."""

    rank: int = Field(ge=2)
    label: str
    crop: str
    disease: str
    confidence: float = Field(ge=0.0, le=1.0)
    confidence_badge: str = Field(description="High | Medium | Low")


class DiseaseSeverity(BaseModel):
    """Triage severity derived from the validation pipeline decision."""

    level: str = Field(description="low | medium | high | unknown")
    confidence: float = Field(ge=0.0, le=1.0)
    decision: str
    basis: str = Field(
        description=(
            "Short explanation of how the triage severity was derived. This is "
            "not a measured field infection percentage."
        ),
    )


class RagExplanation(BaseModel):
    """Clean farmer-facing advisory without retrieval internals."""

    status: str
    source: str
    summary: str
    symptoms_to_check: list[str] = Field(default_factory=list)
    immediate_actions: list[str] = Field(default_factory=list)
    precautions: list[str] = Field(default_factory=list)
    prevention: list[str] = Field(default_factory=list)
    similar_diseases: list[str] = Field(default_factory=list)
    expert_advice: str = ""
    safety_note: str = ""


class PredictDiseaseResponse(BaseModel):
    """Slim response for disease prediction plus RAG advisory."""

    crop_name: str | None = Field(default=None)
    primary_diagnosis: PrimaryDiagnosis
    top_3_predictions: list[DiseasePredictionItem] = Field(default_factory=list)
    possible_other_diseases: list[PossibleDiseaseItem] = Field(default_factory=list)
    severity: DiseaseSeverity
    urgency: str = Field(description="Monitor | Act soon | Act immediately | Retake image")
    symptoms_to_confirm: list[str] = Field(default_factory=list)
    what_to_do_now: list[str] = Field(default_factory=list)
    prevention_tips: list[str] = Field(default_factory=list)
    when_to_call_expert: str
    retake_image_guidance: str | None = None
    rag_explanation: RagExplanation


class CropPredictionItem(BaseModel):
    """One entry of the marginalised crop ranking."""

    rank: int = Field(ge=1)
    crop: str
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="P(crop) = sum over diseases of P(crop::disease)",
    )
    top_disease: str = Field(description="Most-likely disease within this crop.")
    top_disease_label: str = Field(description="Full crop::disease label.")
    top_disease_conditional: float = Field(
        ge=0.0,
        le=1.0,
        description="P(disease | crop) = P(crop::disease) / P(crop)",
    )
    top_disease_joint: float = Field(
        ge=0.0,
        le=1.0,
        description="P(crop::disease) — same number /predict would report for that class.",
    )


class CropVerifierItem(BaseModel):
    """One entry of the CLIP zero-shot crop ranking (independent second opinion)."""

    rank: int = Field(ge=1)
    crop: str
    similarity: float = Field(
        ge=0.0,
        le=1.0,
        description="Softmax over CLIP image-text similarities across the bundle's crops.",
    )


class CropRouterItem(BaseModel):
    """One entry of the trained crop router's ranking (P(crop) over 20 crops)."""

    rank: int = Field(ge=1)
    crop: str
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Router output: softmax over 20 crops from the LR head.",
    )


class DiseaseWithinCropItem(BaseModel):
    """Disease ranked inside the router's top-1 crop (per-crop head output)."""

    rank: int = Field(ge=1)
    crop: str
    disease: str
    label: str
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Per-crop head output: softmax over that crop's disease classes.",
    )


class PredictV2Response(BaseModel):
    """Body of /predict-v2 — the full validation + classification pipeline."""

    request_id: str
    decision: str  # "high_confidence" | "expert_review" | "retake"
    confidence: float

    predictions: list[PredictionItem] = Field(
        default_factory=list,
        description="Empty when decision='retake' and the pipeline aborted before classifying.",
    )

    top_crops: list[CropPredictionItem] = Field(
        default_factory=list,
        description=(
            "Crop-level marginals computed from the joint 139-class softmax. "
            "Surfaces the model's implicit crop ranking independent of the "
            "joint argmax (which is biased by per-crop class count)."
        ),
    )

    crop_verifier_predictions: list[CropVerifierItem] = Field(
        default_factory=list,
        description=(
            "Independent zero-shot crop ranking from CLIP. Catches systematic "
            "biases in the joint classifier (e.g., narrow-leaf -> onion). "
            "Empty if the verifier is disabled or failed to load at startup."
        ),
    )

    crop_router_predictions: list[CropRouterItem] = Field(
        default_factory=list,
        description=(
            "Trained crop router output (P(crop) over 20 crops) from the "
            "hierarchical bundle. Independent of the joint disease softmax."
        ),
    )

    disease_within_top_crop: list[DiseaseWithinCropItem] = Field(
        default_factory=list,
        description=(
            "Disease ranking from the per-crop head for the router's top-1 crop. "
            "Renormalised over only that crop's diseases."
        ),
    )

    crop_verifier_agreement: bool | None = Field(
        default=None,
        description=(
            "True if CLIP's top-1 crop matches the trained crop router's top-1 crop. "
            "False if the two disagree. Null if either signal didn't run."
        ),
    )

    classifier_used: str = Field(
        default="hierarchical",
        description="Which classifier produced the predictions: 'hierarchical' or 'efficientnetb2'.",
    )

    # Optional explanation overlay (Phase 3 SmoothGrad).
    explanation_overlay_png_b64: str | None = None

    validation: ValidationReport
    confidence_signals: ConfidenceSignalsSchema

    # Intermediate visualisations the UI can show as a step-by-step timeline.
    mask_overlay_png_b64: str | None = Field(
        default=None,
        description="Original image with the YOLO mask drawn on top (red).",
    )
    clean_leaf_png_b64: str | None = Field(
        default=None,
        description="The 260x260 background-removed leaf the classifier actually saw.",
    )

    # Retake guidance — populated only when decision='retake'.
    retake_reason: str | None = None
    retake_guidance: str | None = None

    # Final farmer-facing explanation from the RAG/Gemini layer.
    advisory: AdvisoryResponse | None = None

    latency: LatencyBreakdown
    model_versions: ModelVersions

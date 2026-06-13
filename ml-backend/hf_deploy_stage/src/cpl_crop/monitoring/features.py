"""Per-request feature extraction for monitoring.

Each ``/predict-v2`` call produces one :class:`RequestFeatures` record.
Records are flat (numerical or categorical scalars) so they slot
directly into pandas / Evidently without any reshaping.

Why these features?
- ``brightness`` / ``contrast`` / ``blur_score`` capture the *input
  distribution* — drift here flags lighting / camera changes.
- ``area_fraction`` / ``segmentation_score`` capture leaf detection
  health.
- ``top1_confidence`` / ``confidence_gap`` / ``fused_confidence``
  capture model behaviour — drift here flags out-of-distribution
  inputs even if the input statistics look unchanged.
- ``decision`` / ``predicted_crop`` are categorical labels for
  per-segment drift slicing.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass(slots=True)
class RequestFeatures:
    """One row of the per-request monitoring log.

    Field types deliberately use only Python primitives so the record
    serialises straight to JSON / parquet without custom encoders.
    """

    # Identity / time
    timestamp: str  # ISO-8601 UTC
    request_id: str

    # Input image stats (from quality.py)
    image_height: int
    image_width: int
    brightness: float
    contrast: float
    blur_score: float

    # Pipeline stage signals
    segmentation_score: float
    area_fraction: float

    # Model output signals
    top1_confidence: float
    confidence_gap: float
    fused_confidence: float

    # Categorical
    decision: str          # high_confidence | expert_review | retake
    predicted_crop: str    # B2 top-1 crop part (or 'unknown')
    predicted_disease: str  # B2 top-1 disease part (or 'unknown')
    crop_agreement: bool   # B2 vs CLIP vs hierarchical agreement

    # Latency for ops dashboards
    latency_ms: float

    def to_dict(self) -> dict[str, Any]:
        """Return a plain-dict representation suitable for JSON / parquet."""
        return asdict(self)


def _split_label(label: str) -> tuple[str, str]:
    """Split a ``crop::disease`` label into (crop, disease)."""
    if "::" in label:
        crop, disease = label.split("::", 1)
        return crop.strip().lower(), disease.strip()
    return "unknown", label


def extract_features(
    *,
    request_id: str,
    image_shape: tuple[int, int],
    quality: dict[str, float],
    segmentation_score: float,
    area_fraction: float,
    top1_confidence: float,
    confidence_gap: float,
    fused_confidence: float,
    decision: str,
    top1_label: str,
    crop_agreement: bool,
    latency_ms: float,
) -> RequestFeatures:
    """Build a :class:`RequestFeatures` from raw pipeline inputs.

    The keyword-only signature is deliberately strict so callers cannot
    silently swap arguments by position.
    """
    crop, disease = _split_label(top1_label)
    h, w = image_shape
    return RequestFeatures(
        timestamp=datetime.now(UTC).isoformat(timespec="seconds"),
        request_id=request_id,
        image_height=int(h),
        image_width=int(w),
        brightness=float(quality.get("brightness", 0.0)),
        contrast=float(quality.get("contrast", 0.0)),
        blur_score=float(quality.get("blur_score", 0.0)),
        segmentation_score=float(segmentation_score),
        area_fraction=float(area_fraction),
        top1_confidence=float(top1_confidence),
        confidence_gap=float(confidence_gap),
        fused_confidence=float(fused_confidence),
        decision=str(decision),
        predicted_crop=crop,
        predicted_disease=disease,
        crop_agreement=bool(crop_agreement),
        latency_ms=float(latency_ms),
    )


# Column-type metadata used by drift.py to build the Evidently
# DataDefinition. Keep in sync with RequestFeatures.
NUMERICAL_COLUMNS: tuple[str, ...] = (
    "image_height",
    "image_width",
    "brightness",
    "contrast",
    "blur_score",
    "segmentation_score",
    "area_fraction",
    "top1_confidence",
    "confidence_gap",
    "fused_confidence",
    "latency_ms",
)
CATEGORICAL_COLUMNS: tuple[str, ...] = (
    "decision",
    "predicted_crop",
    "predicted_disease",
    "crop_agreement",
)

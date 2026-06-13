"""Stage 8 — confidence engine.

Combines five independent quality signals into a single calibrated
confidence number. The router uses this number to decide auto-accept,
expert review, or retake.

Weights are config-driven so we can tune without code changes; defaults
are documented in :class:`cpl_crop.config.Settings`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ConfidenceSignals:
    """The eight raw signals fed into the confidence engine.

    The original five (Phase 3.5) plus three added in Phase 3.8:
    crop_router_confidence, per_crop_head_confidence, crop_agreement.
    """

    quality_score: float       # 0..1 from cpl_crop.validation.quality
    seg_confidence: float      # 0..1 from YOLO
    leaf_area_score: float     # 0..1 from cpl_crop.validation.extract
    classifier_top1: float     # 0..1 softmax of the predicted class (joint)
    prediction_gap: float      # top1 - top2 (clamped to 0 if < 0)
    crop_router_confidence: float = 0.0  # P(crop) from the trained router
    per_crop_head_confidence: float = 0.0  # P(disease | top crop) from per-crop head
    crop_agreement: float = 0.0  # 1.0 if router top-1 == CLIP top-1, else 0.0

    weights: dict[str, float] = field(default_factory=dict)
    final: float = 0.0

    def to_json(self) -> dict[str, Any]:
        return {
            "final": round(self.final, 4),
            "quality_score": round(self.quality_score, 4),
            "seg_confidence": round(self.seg_confidence, 4),
            "leaf_area_score": round(self.leaf_area_score, 4),
            "classifier_top1": round(self.classifier_top1, 4),
            "prediction_gap": round(self.prediction_gap, 4),
            "crop_router_confidence": round(self.crop_router_confidence, 4),
            "per_crop_head_confidence": round(self.per_crop_head_confidence, 4),
            "crop_agreement": round(self.crop_agreement, 4),
            "weights": {k: round(v, 4) for k, v in self.weights.items()},
        }


def fuse_confidence(
    *,
    quality_score: float,
    seg_confidence: float,
    leaf_area_score: float,
    classifier_top1: float,
    prediction_gap: float,
    crop_router_confidence: float = 0.0,
    per_crop_head_confidence: float = 0.0,
    crop_agreement: float = 0.0,
    weight_quality: float = 0.10,
    weight_seg: float = 0.15,
    weight_area: float = 0.05,
    weight_top1: float = 0.25,
    weight_gap: float = 0.10,
    weight_crop_router: float = 0.15,
    weight_per_crop_head: float = 0.10,
    weight_crop_agreement: float = 0.10,
) -> ConfidenceSignals:
    """Compute the weighted-average final confidence.

    The 8 weights above sum to 1.0 by default. The newer signals
    (Phase 3.8) — crop_router, per_crop_head, crop_agreement — are
    independent of the joint softmax and so add real information:
    a confident router AND an agreeing CLIP make the final score
    rise meaningfully even if classifier_top1 is moderate.

    The ``prediction_gap`` is amplified by *4 then clipped to 1.0, so a
    gap of >= 0.25 between top-1 and top-2 contributes the full weight.
    """
    quality_score = float(max(0.0, min(1.0, quality_score)))
    seg_confidence = float(max(0.0, min(1.0, seg_confidence)))
    leaf_area_score = float(max(0.0, min(1.0, leaf_area_score)))
    classifier_top1 = float(max(0.0, min(1.0, classifier_top1)))
    crop_router_confidence = float(max(0.0, min(1.0, crop_router_confidence)))
    per_crop_head_confidence = float(max(0.0, min(1.0, per_crop_head_confidence)))
    crop_agreement = float(max(0.0, min(1.0, crop_agreement)))
    gap_amplified = float(max(0.0, min(1.0, prediction_gap * 4.0)))

    weights = {
        "quality": weight_quality,
        "seg": weight_seg,
        "area": weight_area,
        "top1": weight_top1,
        "gap": weight_gap,
        "crop_router": weight_crop_router,
        "per_crop_head": weight_per_crop_head,
        "crop_agreement": weight_crop_agreement,
    }
    final = (
        weights["quality"] * quality_score
        + weights["seg"] * seg_confidence
        + weights["area"] * leaf_area_score
        + weights["top1"] * classifier_top1
        + weights["gap"] * gap_amplified
        + weights["crop_router"] * crop_router_confidence
        + weights["per_crop_head"] * per_crop_head_confidence
        + weights["crop_agreement"] * crop_agreement
    )
    final = float(max(0.0, min(1.0, final)))

    return ConfidenceSignals(
        quality_score=quality_score,
        seg_confidence=seg_confidence,
        leaf_area_score=leaf_area_score,
        classifier_top1=classifier_top1,
        prediction_gap=float(max(0.0, min(1.0, prediction_gap))),
        crop_router_confidence=crop_router_confidence,
        per_crop_head_confidence=per_crop_head_confidence,
        crop_agreement=crop_agreement,
        weights=weights,
        final=final,
    )

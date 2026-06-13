"""Stage 9 — decision router.

Maps a final confidence score to one of three outcomes:
* ``high_confidence`` — return the prediction as-is
* ``expert_review`` — return the prediction but flag it
* ``retake`` — don't show the prediction; tell the user what to fix

The retake branch picks specific guidance text based on which signal
fired the lowest score, so the response is actionable.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from cpl_crop.validation.confidence import ConfidenceSignals


class Decision(StrEnum):
    HIGH_CONFIDENCE = "high_confidence"
    EXPERT_REVIEW = "expert_review"
    RETAKE = "retake"


class RetakeReason(StrEnum):
    BLURRY = "image_too_blurry"
    DARK = "image_too_dark"
    BRIGHT = "image_too_bright"
    LOW_CONTRAST = "image_low_contrast"
    LOW_RESOLUTION = "image_resolution_too_low"
    NO_LEAF = "no_leaf_detected"
    LEAF_TOO_SMALL = "leaf_too_small_in_frame"
    LEAF_TOO_LARGE = "leaf_too_large_or_no_background"
    UNCERTAIN_CLASSIFIER = "classifier_low_confidence"
    UNRECOGNIZED = "unrecognized_or_not_a_crop_leaf"
    GENERIC = "uncertain_prediction"


_RETAKE_TEXT: dict[RetakeReason, str] = {
    RetakeReason.BLURRY: "The image is blurry. Hold the camera steady and retake.",
    RetakeReason.DARK: "The image is too dark. Move into better light and retake.",
    RetakeReason.BRIGHT: "The image is overexposed. Move out of direct sunlight and retake.",
    RetakeReason.LOW_CONTRAST: "The image is too washed out. Try better lighting and retake.",
    RetakeReason.LOW_RESOLUTION: "The image is too small. Use a higher-resolution photo.",
    RetakeReason.NO_LEAF: "We couldn't find a leaf in the photo. Center the leaf in the frame and retake.",
    RetakeReason.LEAF_TOO_SMALL: "The leaf is too small in the frame. Move closer and retake.",
    RetakeReason.LEAF_TOO_LARGE: "The leaf fills the entire frame. Step back so we can see its full outline.",
    RetakeReason.UNCERTAIN_CLASSIFIER: "We are not confident in the diagnosis. Try a different angle or better light.",
    RetakeReason.UNRECOGNIZED: "We couldn't recognize a known crop leaf or disease in this photo. Please photograph a single, clearly-visible crop leaf.",
    RetakeReason.GENERIC: "We couldn't make a confident diagnosis. Please retake the photo.",
}


@dataclass(frozen=True)
class RoutingResult:
    """Output of :func:`route`."""

    decision: Decision
    reason: RetakeReason | None
    guidance: str | None


def _pick_retake_reason(
    *,
    quality_failures: list[str],
    seg_detected: bool,
    leaf_area_failure: str | None,
    classifier_top1: float,
) -> RetakeReason:
    """Return the most specific retake reason given which signals failed.

    Priority order:
        no leaf > image quality > leaf area > classifier uncertainty.
    """
    if not seg_detected:
        return RetakeReason.NO_LEAF

    for f in quality_failures:
        if f.startswith("blurry_"):
            return RetakeReason.BLURRY
        if f.startswith("too_dark_"):
            return RetakeReason.DARK
        if f.startswith("too_bright_"):
            return RetakeReason.BRIGHT
        if f.startswith("low_contrast_"):
            return RetakeReason.LOW_CONTRAST
        if f.startswith("resolution_below_"):
            return RetakeReason.LOW_RESOLUTION

    if leaf_area_failure == "leaf_too_small_in_frame":
        return RetakeReason.LEAF_TOO_SMALL
    if leaf_area_failure == "leaf_too_large_or_no_background":
        return RetakeReason.LEAF_TOO_LARGE

    if classifier_top1 < 0.30:
        return RetakeReason.UNCERTAIN_CLASSIFIER

    return RetakeReason.GENERIC


def route(
    signals: ConfidenceSignals,
    *,
    high_threshold: float = 0.85,
    medium_threshold: float = 0.50,
    min_top1: float = 0.45,
    is_crop_leaf: bool = True,
    quality_failures: list[str] | None = None,
    seg_detected: bool = True,
    leaf_area_failure: str | None = None,
) -> RoutingResult:
    """Map a fused confidence score to a Decision + retake guidance.

    Open-set guards (a closed-world classifier always emits *some* class, so a
    sharp out-of-domain photo can score high and slip through):
    1. ``is_crop_leaf`` — CLIP says the image is NOT a crop leaf (keyboard,
       hand, wall). This is the strong, semantic guard.
    2. ``min_top1`` — a HARD top-1 floor as a backstop when CLIP is off.
    Either firing forces a retake regardless of the fused score.
    """
    if not is_crop_leaf or signals.classifier_top1 < min_top1:
        return RoutingResult(
            decision=Decision.RETAKE,
            reason=RetakeReason.UNRECOGNIZED,
            guidance=_RETAKE_TEXT[RetakeReason.UNRECOGNIZED],
        )

    if signals.final >= high_threshold:
        return RoutingResult(decision=Decision.HIGH_CONFIDENCE, reason=None, guidance=None)
    if signals.final >= medium_threshold:
        return RoutingResult(decision=Decision.EXPERT_REVIEW, reason=None, guidance=None)

    reason = _pick_retake_reason(
        quality_failures=quality_failures or [],
        seg_detected=seg_detected,
        leaf_area_failure=leaf_area_failure,
        classifier_top1=signals.classifier_top1,
    )
    return RoutingResult(decision=Decision.RETAKE, reason=reason, guidance=_RETAKE_TEXT[reason])

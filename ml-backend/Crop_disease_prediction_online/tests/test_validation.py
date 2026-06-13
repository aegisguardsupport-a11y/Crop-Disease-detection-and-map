"""Fast unit tests for the validation pipeline (no TF, no YOLO).

These cover the deterministic pieces: quality assessment, leaf-area
validation/scoring, clean-leaf extraction, confidence fusion, and
decision routing.
"""

from __future__ import annotations

import numpy as np
import pytest

from cpl_crop.validation.confidence import fuse_confidence
from cpl_crop.validation.extract import (
    extract_clean_leaf,
    leaf_area_score,
    validate_leaf_area,
)
from cpl_crop.validation.quality import assess_image_quality
from cpl_crop.validation.router import Decision, RetakeReason, route


# ---------------------------------------------------------------------------
# Quality
# ---------------------------------------------------------------------------
def _make_image(shape, fill=(120, 80, 50), noise: int = 30) -> np.ndarray:
    rng = np.random.default_rng(0)
    img = np.full((*shape, 3), fill, dtype=np.uint8)
    if noise > 0:
        img = (img.astype(np.int16) + rng.integers(-noise, noise, img.shape)).clip(
            0, 255
        ).astype(np.uint8)
    return img


def test_quality_passes_on_normal_image() -> None:
    img = _make_image((400, 600), fill=(120, 100, 80), noise=80)
    rep = assess_image_quality(img)
    assert rep.ok
    assert rep.score >= 0.5
    assert rep.failures == []


def test_quality_flags_low_resolution() -> None:
    img = _make_image((100, 100))
    rep = assess_image_quality(img)
    assert not rep.ok
    assert any(f.startswith("resolution_below_") for f in rep.failures)


def test_quality_flags_too_dark() -> None:
    img = np.full((400, 400, 3), 5, dtype=np.uint8)
    rep = assess_image_quality(img)
    assert not rep.ok
    assert any(f.startswith("too_dark_") for f in rep.failures)


def test_quality_flags_too_bright() -> None:
    img = np.full((400, 400, 3), 250, dtype=np.uint8)
    rep = assess_image_quality(img)
    assert not rep.ok
    assert any(f.startswith("too_bright_") for f in rep.failures)


def test_quality_flags_low_contrast_and_blur() -> None:
    img = np.full((400, 400, 3), 128, dtype=np.uint8)  # uniform → no blur, no contrast
    rep = assess_image_quality(img)
    assert not rep.ok
    failures = " ".join(rep.failures)
    assert "low_contrast" in failures
    assert "blurry" in failures


def test_quality_rejects_non_rgb() -> None:
    with pytest.raises(ValueError):
        assess_image_quality(np.zeros((10, 10), dtype=np.uint8))


# ---------------------------------------------------------------------------
# Leaf area
# ---------------------------------------------------------------------------
def test_leaf_area_score_optimum() -> None:
    score = leaf_area_score(0.40, optimal_min=0.20, optimal_max=0.70, hard_min=0.05, hard_max=0.95)
    assert score == 1.0


def test_leaf_area_score_decays_outside_optimum() -> None:
    # Below optimum
    s1 = leaf_area_score(0.10, optimal_min=0.20, optimal_max=0.70, hard_min=0.05, hard_max=0.95)
    # Above optimum
    s2 = leaf_area_score(0.85, optimal_min=0.20, optimal_max=0.70, hard_min=0.05, hard_max=0.95)
    # Outside hard bounds
    s3 = leaf_area_score(0.02, optimal_min=0.20, optimal_max=0.70, hard_min=0.05, hard_max=0.95)
    s4 = leaf_area_score(0.99, optimal_min=0.20, optimal_max=0.70, hard_min=0.05, hard_max=0.95)
    assert 0.0 < s1 < 1.0
    assert 0.0 < s2 < 1.0
    assert s3 == 0.0
    assert s4 == 0.0


def test_validate_leaf_area_rejects_too_small() -> None:
    rep = validate_leaf_area(0.02)
    assert not rep.ok
    assert rep.failure == "leaf_too_small_in_frame"


def test_validate_leaf_area_rejects_too_large() -> None:
    rep = validate_leaf_area(0.99)
    assert not rep.ok
    assert rep.failure == "leaf_too_large_or_no_background"


def test_validate_leaf_area_accepts_normal() -> None:
    rep = validate_leaf_area(0.42)
    assert rep.ok
    assert rep.failure is None
    assert rep.score == 1.0


# ---------------------------------------------------------------------------
# Clean leaf extraction
# ---------------------------------------------------------------------------
def test_extract_clean_leaf_basic() -> None:
    img = _make_image((400, 400), fill=(50, 200, 50))
    mask = np.zeros((400, 400), dtype=bool)
    mask[100:300, 100:300] = True

    result = extract_clean_leaf(img, mask, target_size=(128, 128), padding=0.0, fill="black")
    assert result.image.shape == (128, 128, 3)
    assert result.image.dtype == np.uint8
    # The bbox without padding is 100..299 inclusive on both axes
    assert result.bbox_xyxy_padded == (100, 100, 299, 299)


def test_extract_clean_leaf_pads_bbox() -> None:
    img = _make_image((400, 400))
    mask = np.zeros((400, 400), dtype=bool)
    mask[100:300, 100:300] = True
    res = extract_clean_leaf(img, mask, target_size=(64, 64), padding=0.10, fill="white")
    x0, y0, x1, y1 = res.bbox_xyxy_padded
    assert x0 < 100 and y0 < 100 and x1 > 299 and y1 > 299


def test_extract_clean_leaf_black_fill_replaces_background() -> None:
    img = np.full((100, 100, 3), 200, dtype=np.uint8)  # bright background
    mask = np.zeros((100, 100), dtype=bool)
    mask[40:60, 40:60] = True
    res = extract_clean_leaf(img, mask, target_size=(20, 20), padding=0.5, fill="black")
    # Edges of the resized image should be black background, center should be ~200
    assert res.image[0, 0].max() < 30
    assert res.image[10, 10].mean() > 150


def test_extract_clean_leaf_rejects_shape_mismatch() -> None:
    img = _make_image((100, 100))
    mask = np.zeros((50, 50), dtype=bool)
    with pytest.raises(ValueError, match="Mask shape"):
        extract_clean_leaf(img, mask)


# ---------------------------------------------------------------------------
# Confidence fusion
# ---------------------------------------------------------------------------
def test_confidence_perfect_signals() -> None:
    s = fuse_confidence(
        quality_score=1.0, seg_confidence=1.0, leaf_area_score=1.0,
        classifier_top1=1.0, prediction_gap=0.5,
        crop_router_confidence=1.0, per_crop_head_confidence=1.0, crop_agreement=1.0,
    )
    assert s.final == 1.0


def test_confidence_zero_signals() -> None:
    s = fuse_confidence(
        quality_score=0.0, seg_confidence=0.0, leaf_area_score=0.0,
        classifier_top1=0.0, prediction_gap=0.0,
        crop_router_confidence=0.0, per_crop_head_confidence=0.0, crop_agreement=0.0,
    )
    assert s.final == 0.0


def test_confidence_one_weak_signal_pulls_score_down() -> None:
    # All strong except quality=0; default quality weight is 0.10
    s = fuse_confidence(
        quality_score=0.0, seg_confidence=1.0, leaf_area_score=1.0,
        classifier_top1=1.0, prediction_gap=0.5,
        crop_router_confidence=1.0, per_crop_head_confidence=1.0, crop_agreement=1.0,
    )
    # final should be ~ 1.0 - 0.10 = 0.90
    assert 0.85 <= s.final <= 0.95


def test_confidence_clips_inputs_to_unit() -> None:
    s = fuse_confidence(
        quality_score=2.0, seg_confidence=-1.0, leaf_area_score=0.5,
        classifier_top1=0.5, prediction_gap=0.5,
        crop_router_confidence=2.0, per_crop_head_confidence=-0.5, crop_agreement=0.5,
    )
    assert 0.0 <= s.final <= 1.0
    assert s.quality_score == 1.0
    assert s.seg_confidence == 0.0
    assert s.crop_router_confidence == 1.0
    assert s.per_crop_head_confidence == 0.0


def test_confidence_weights_sum_documented_in_output() -> None:
    s = fuse_confidence(
        quality_score=0.5, seg_confidence=0.5, leaf_area_score=0.5,
        classifier_top1=0.5, prediction_gap=0.5,
        crop_router_confidence=0.5, per_crop_head_confidence=0.5, crop_agreement=1.0,
    )
    assert set(s.weights.keys()) == {
        "quality", "seg", "area", "top1", "gap",
        "crop_router", "per_crop_head", "crop_agreement",
    }
    assert abs(sum(s.weights.values()) - 1.0) < 1e-6


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------
def _signals(final: float) -> object:
    """Build a minimal ConfidenceSignals stand-in (route only reads .final and .classifier_top1)."""
    s = fuse_confidence(
        quality_score=final, seg_confidence=final, leaf_area_score=final,
        classifier_top1=final, prediction_gap=final / 2,
    )
    # Force the final value exactly
    object.__setattr__(s, "final", final)
    return s


def test_router_high_confidence() -> None:
    s = _signals(0.92)
    r = route(s)  # type: ignore[arg-type]
    assert r.decision == Decision.HIGH_CONFIDENCE
    assert r.reason is None


def test_router_expert_review() -> None:
    s = _signals(0.65)
    r = route(s)  # type: ignore[arg-type]
    assert r.decision == Decision.EXPERT_REVIEW


def test_router_retake_no_leaf() -> None:
    s = _signals(0.20)
    r = route(s, seg_detected=False)  # type: ignore[arg-type]
    assert r.decision == Decision.RETAKE
    assert r.reason == RetakeReason.NO_LEAF
    assert r.guidance is not None


def test_router_retake_blurry() -> None:
    s = _signals(0.20)
    r = route(s, quality_failures=["blurry_below_100"])  # type: ignore[arg-type]
    assert r.decision == Decision.RETAKE
    assert r.reason == RetakeReason.BLURRY


def test_router_retake_leaf_too_small() -> None:
    s = _signals(0.30)
    r = route(s, leaf_area_failure="leaf_too_small_in_frame")  # type: ignore[arg-type]
    assert r.decision == Decision.RETAKE
    assert r.reason == RetakeReason.LEAF_TOO_SMALL

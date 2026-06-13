"""Stage 3 — OpenCV-based image-quality assessment.

Cheap, deterministic checks that run *before* expensive segmentation +
classification. Catches blurry / dark / overexposed / tiny images so
we can reject them with helpful retake guidance.

All thresholds are config-driven via :class:`cpl_crop.config.Settings`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import cv2
import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class QualityReport:
    """Result of :func:`assess_image_quality`. All numeric fields are populated."""

    ok: bool
    score: float  # 0..1, where 1 = all checks pass cleanly
    resolution: tuple[int, int]  # (height, width)
    blur: float  # Laplacian variance — higher = sharper
    brightness: float  # 0..255 mean grayscale
    contrast: float  # std of grayscale pixels
    leaf_ratio: float  # proportion of leaf-colored pixels (green/yellow/brown)
    failures: list[str] = field(default_factory=list)

    def to_json(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "score": round(self.score, 4),
            "resolution": list(self.resolution),
            "blur": round(self.blur, 2),
            "brightness": round(self.brightness, 2),
            "contrast": round(self.contrast, 2),
            "leaf_ratio": round(self.leaf_ratio, 4),
            "failures": list(self.failures),
        }


def _normalize_to_unit(value: float, lo: float, hi: float) -> float:
    """Linear ramp clamped to [0, 1]."""
    if hi <= lo:
        return 1.0 if value >= hi else 0.0
    return float(max(0.0, min(1.0, (value - lo) / (hi - lo))))


def assess_image_quality(
    image_rgb: NDArray[np.uint8],
    *,
    min_resolution: int = 224,
    min_blur: float = 100.0,
    min_brightness: float = 40.0,
    max_brightness: float = 220.0,
    min_contrast: float = 25.0,
    min_leaf_ratio: float = 0.05,  # At least 5% of the image must be leaf-colored
) -> QualityReport:
    """Compute a quality report for an RGB uint8 image.

    The overall ``score`` is a soft average of four sub-scores so the
    confidence engine can use it directly. ``ok`` is the AND of hard
    pass/fail predicates.
    """
    if image_rgb.ndim != 3 or image_rgb.shape[-1] != 3:
        raise ValueError(f"Expected (H, W, 3) RGB image; got shape {image_rgb.shape}")

    h, w = image_rgb.shape[:2]
    gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)

    blur = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    brightness = float(gray.mean())
    contrast = float(gray.std())

    # --- Leaf Color (Green/Yellow/Brown) Detection ---
    hsv = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2HSV)
    # Hue: 10 (brown/orange) to 85 (green)
    # Saturation: > 30 (ignore grays/whites)
    # Value: > 30 (ignore dark blacks)
    lower_leaf = np.array([10, 30, 30])
    upper_leaf = np.array([85, 255, 255])
    leaf_mask = cv2.inRange(hsv, lower_leaf, upper_leaf)
    leaf_ratio = float(cv2.countNonZero(leaf_mask)) / (h * w)

    failures: list[str] = []
    if min(h, w) < min_resolution:
        failures.append(f"resolution_below_{min_resolution}")
    if blur < min_blur:
        failures.append(f"blurry_below_{min_blur:.0f}")
    if brightness < min_brightness:
        failures.append(f"too_dark_below_{min_brightness:.0f}")
    elif brightness > max_brightness:
        failures.append(f"too_bright_above_{max_brightness:.0f}")
    if contrast < min_contrast:
        failures.append(f"low_contrast_below_{min_contrast:.0f}")
    if leaf_ratio < min_leaf_ratio:
        failures.append(f"not_a_leaf_ratio_{leaf_ratio:.2f}")

    # Soft sub-scores in [0, 1]
    res_score = _normalize_to_unit(min(h, w), min_resolution, min_resolution * 2)
    blur_score = _normalize_to_unit(blur, min_blur, min_blur * 4)
    if min_brightness <= brightness <= max_brightness:
        bright_score = 1.0
    elif brightness < min_brightness:
        bright_score = _normalize_to_unit(brightness, 0.0, min_brightness)
    else:
        bright_score = _normalize_to_unit(255.0 - brightness, 0.0, 255.0 - max_brightness)
    contrast_score = _normalize_to_unit(contrast, min_contrast, min_contrast * 2)
    leaf_score = _normalize_to_unit(leaf_ratio, min_leaf_ratio, min_leaf_ratio * 3)

    score = float(np.mean([res_score, blur_score, bright_score, contrast_score, leaf_score]))

    return QualityReport(
        ok=not failures,
        score=score,
        resolution=(h, w),
        blur=blur,
        brightness=brightness,
        contrast=contrast,
        leaf_ratio=leaf_ratio,
        failures=failures,
    )

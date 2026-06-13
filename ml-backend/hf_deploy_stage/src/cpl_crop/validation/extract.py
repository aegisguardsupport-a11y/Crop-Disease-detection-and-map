"""Stages 5 + 6 — leaf-area validation + clean leaf extraction.

After YOLO gives us a mask, we:
1. Validate that the mask area sits in a sensible band (Stage 5).
2. Crop to the mask's bounding box with padding, replace background
   pixels with a neutral fill, and resize to the classifier's input
   size (Stage 6).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

import cv2
import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class LeafAreaReport:
    """Output of :func:`validate_leaf_area`."""

    ratio: float  # mask.sum() / mask.size
    score: float  # 0..1, peak at the optimal range
    ok: bool  # within [min, max]
    failure: str | None  # human-readable reason if not ok

    def to_json(self) -> dict[str, Any]:
        return {
            "ratio": round(self.ratio, 4),
            "score": round(self.score, 4),
            "ok": self.ok,
            "failure": self.failure,
        }


def leaf_area_score(
    ratio: float,
    *,
    optimal_min: float,
    optimal_max: float,
    hard_min: float,
    hard_max: float,
) -> float:
    """Map a leaf-area ratio to a [0, 1] score.

    Plateau at 1.0 inside ``[optimal_min, optimal_max]``; linearly decays
    to 0.0 at ``hard_min`` and ``hard_max``.
    """
    if ratio <= hard_min or ratio >= hard_max:
        return 0.0
    if optimal_min <= ratio <= optimal_max:
        return 1.0
    if ratio < optimal_min:
        return float((ratio - hard_min) / max(1e-6, optimal_min - hard_min))
    return float((hard_max - ratio) / max(1e-6, hard_max - optimal_max))


def validate_leaf_area(
    ratio: float,
    *,
    hard_min: float = 0.05,
    hard_max: float = 0.95,
    optimal_min: float = 0.20,
    optimal_max: float = 0.70,
) -> LeafAreaReport:
    """Apply hard + soft leaf-area checks."""
    score = leaf_area_score(
        ratio,
        optimal_min=optimal_min,
        optimal_max=optimal_max,
        hard_min=hard_min,
        hard_max=hard_max,
    )
    if ratio < hard_min:
        return LeafAreaReport(
            ratio=ratio, score=0.0, ok=False, failure="leaf_too_small_in_frame",
        )
    if ratio > hard_max:
        return LeafAreaReport(
            ratio=ratio, score=0.0, ok=False, failure="leaf_too_large_or_no_background",
        )
    return LeafAreaReport(ratio=ratio, score=score, ok=True, failure=None)


# ---------------------------------------------------------------------------
# Clean leaf extraction
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class CleanLeafResult:
    """Output of :func:`extract_clean_leaf`."""

    image: NDArray[np.uint8]  # (target_h, target_w, 3) uint8
    bbox_xyxy_padded: tuple[int, int, int, int]  # the padded crop region
    fill: str  # "black" | "white" | "mean"


def _bbox_from_mask(mask: NDArray[np.bool_]) -> tuple[int, int, int, int]:
    ys, xs = np.where(mask)
    if len(xs) == 0 or len(ys) == 0:
        h, w = mask.shape
        return 0, 0, w - 1, h - 1
    return int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())


def _expand_bbox(
    x0: int, y0: int, x1: int, y1: int, h: int, w: int, padding: float
) -> tuple[int, int, int, int]:
    """Symmetric padding by ``padding`` fraction of the bbox's larger side, clipped."""
    dx = (x1 - x0) * padding
    dy = (y1 - y0) * padding
    x0 = int(max(0, x0 - dx))
    y0 = int(max(0, y0 - dy))
    x1 = int(min(w - 1, x1 + dx))
    y1 = int(min(h - 1, y1 + dy))
    return x0, y0, x1, y1


def extract_clean_leaf(
    image_rgb: NDArray[np.uint8],
    mask: NDArray[np.bool_],
    *,
    target_size: tuple[int, int] | None = (260, 260),
    padding: float = 0.05,
    fill: Literal["black", "white", "mean"] = "black",
) -> CleanLeafResult:
    """Crop to the mask bbox, fill background, optionally resize.

    Args:
        image_rgb: original (H, W, 3) uint8 image.
        mask: (H, W) boolean mask from the segmenter.
        target_size: ``(height, width)`` to resize to. ``None`` skips resize
            and returns the leaf at its natural cropped size — useful when
            a downstream model has its own preprocessing (e.g. the
            hierarchical bundle's torchvision transform).
        padding: fraction of bbox to pad each side by.
        fill: replacement colour for background pixels.

    Returns:
        :class:`CleanLeafResult` with the cleaned RGB image.
    """
    if image_rgb.ndim != 3 or image_rgb.shape[-1] != 3:
        raise ValueError(f"Expected (H, W, 3) RGB; got {image_rgb.shape}")
    if mask.shape != image_rgb.shape[:2]:
        raise ValueError(f"Mask shape {mask.shape} != image {image_rgb.shape[:2]}")

    h, w = image_rgb.shape[:2]
    x0, y0, x1, y1 = _bbox_from_mask(mask)
    x0, y0, x1, y1 = _expand_bbox(x0, y0, x1, y1, h, w, padding)

    img_crop = image_rgb[y0 : y1 + 1, x0 : x1 + 1]
    mask_crop = mask[y0 : y1 + 1, x0 : x1 + 1]

    if fill == "black":
        fill_color = np.array([0, 0, 0], dtype=np.uint8)
    elif fill == "white":
        fill_color = np.array([255, 255, 255], dtype=np.uint8)
    elif fill == "mean":
        if mask_crop.any():
            fill_color = img_crop[mask_crop].mean(axis=0).astype(np.uint8)
        else:
            fill_color = np.array([0, 0, 0], dtype=np.uint8)
    else:
        raise ValueError(f"Unknown fill mode: {fill!r}")

    cleaned = np.where(mask_crop[..., None], img_crop, fill_color).astype(np.uint8)

    if target_size is None:
        result_image = np.asarray(cleaned, dtype=np.uint8)
    else:
        th, tw = target_size
        resized = cv2.resize(cleaned, (tw, th), interpolation=cv2.INTER_LINEAR)
        result_image = np.asarray(resized, dtype=np.uint8)

    return CleanLeafResult(
        image=result_image,
        bbox_xyxy_padded=(x0, y0, x1, y1),
        fill=fill,
    )

"""Stage 4 — YOLOv8-seg leaf detector.

Loads ``best.pt`` once and runs it on incoming RGB images. We pick the
single highest-confidence detection (we trained a 1-class "leaf" model,
so multi-leaf scenes get the most prominent leaf).

The model is held by a :class:`LeafSegmenter` that we instantiate once
in the FastAPI lifespan and share across requests.
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from numpy.typing import NDArray

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SegmentationResult:
    """Single leaf segmentation result."""

    detected: bool
    mask: NDArray[np.bool_] | None  # (H, W), full image resolution
    confidence: float  # 0..1
    bbox_xyxy: tuple[float, float, float, float] | None  # in original image coords
    num_detections: int  # how many leaves YOLO found (we only use the best)
    leaf_area_ratio: float  # mask.sum() / mask.size, or 0.0 if no detection

    def to_json(self) -> dict[str, Any]:
        return {
            "detected": self.detected,
            "confidence": round(self.confidence, 4),
            "bbox_xyxy": [round(v, 1) for v in self.bbox_xyxy] if self.bbox_xyxy else None,
            "num_detections": self.num_detections,
            "leaf_area_ratio": round(self.leaf_area_ratio, 4),
        }


class LeafSegmenter:
    """Thread-safe wrapper around an Ultralytics YOLOv8-seg checkpoint."""

    def __init__(
        self,
        weights_path: Path,
        conf_threshold: float = 0.25,
        iou_threshold: float = 0.45,
    ) -> None:
        if not Path(weights_path).exists():
            raise FileNotFoundError(f"YOLO weights not found: {weights_path}")
        # Defer the heavy import so importing this module is cheap.
        from ultralytics import YOLO  # type: ignore[attr-defined]

        logger.info("Loading YOLO leaf segmenter from %s", weights_path)
        self._model = YOLO(str(weights_path))
        self._conf_threshold = conf_threshold
        self._iou_threshold = iou_threshold
        # Ultralytics models aren't documented as thread-safe under .predict;
        # serialize predict calls just in case (we expect ~1 RPS for demo).
        self._lock = threading.Lock()
        logger.info("YOLO ready (conf=%.2f, iou=%.2f)", conf_threshold, iou_threshold)

    def segment(self, image_rgb: NDArray[np.uint8]) -> SegmentationResult:
        """Run inference on an (H, W, 3) RGB uint8 image."""
        if image_rgb.ndim != 3 or image_rgb.shape[-1] != 3:
            raise ValueError(f"Expected (H, W, 3) RGB image; got shape {image_rgb.shape}")
        if image_rgb.dtype != np.uint8:
            raise ValueError(f"Expected uint8 image; got dtype {image_rgb.dtype}")

        h, w = image_rgb.shape[:2]
        with self._lock:
            results = self._model.predict(
                source=image_rgb,
                conf=self._conf_threshold,
                iou=self._iou_threshold,
                verbose=False,
            )
        if not results:
            return _no_detection(h, w)
        result = results[0]
        if result.masks is None or len(result.masks) == 0:
            return _no_detection(h, w)

        confs: NDArray[np.float32] = result.boxes.conf.cpu().numpy().astype(np.float32)  # type: ignore[union-attr]
        masks_raw: NDArray[np.float32] = result.masks.data.cpu().numpy().astype(np.float32)  # type: ignore[union-attr]
        boxes: NDArray[np.float32] = result.boxes.xyxy.cpu().numpy().astype(np.float32)  # type: ignore[union-attr]

        best = int(np.argmax(confs))
        # YOLO masks are at the model's internal resolution (e.g., 640x640).
        # Resize to the original image resolution before returning.
        mask = masks_raw[best]
        if mask.shape != (h, w):
            mask = cv2.resize(mask, (w, h), interpolation=cv2.INTER_NEAREST)
        mask_bool = mask > 0.5

        bbox = tuple(float(v) for v in boxes[best])
        ratio = float(mask_bool.sum()) / float(mask_bool.size)

        return SegmentationResult(
            detected=True,
            mask=mask_bool,
            confidence=float(confs[best]),
            bbox_xyxy=bbox,  # type: ignore[arg-type]
            num_detections=len(confs),
            leaf_area_ratio=ratio,
        )


def _no_detection(h: int, w: int) -> SegmentationResult:
    return SegmentationResult(
        detected=False,
        mask=None,
        confidence=0.0,
        bbox_xyxy=None,
        num_detections=0,
        leaf_area_ratio=0.0,
    )

"""Phase 3.5 validation pipeline.

Modules:

* :mod:`cpl_crop.validation.quality`    — OpenCV image-quality checks (Stage 3).
* :mod:`cpl_crop.validation.segmenter`  — YOLOv8-seg leaf detector (Stage 4).
* :mod:`cpl_crop.validation.extract`    — leaf-area validation + bg removal (Stages 5-6).
* :mod:`cpl_crop.validation.confidence` — multi-signal confidence engine (Stage 8).
* :mod:`cpl_crop.validation.router`     — high/medium/low decision router (Stage 9).
"""

from __future__ import annotations

from cpl_crop.validation.confidence import ConfidenceSignals, fuse_confidence
from cpl_crop.validation.crop_verifier import CropMatch, CropVerifier
from cpl_crop.validation.extract import (
    CleanLeafResult,
    LeafAreaReport,
    extract_clean_leaf,
    leaf_area_score,
    validate_leaf_area,
)
from cpl_crop.validation.quality import QualityReport, assess_image_quality
from cpl_crop.validation.router import Decision, RetakeReason, route
from cpl_crop.validation.segmenter import LeafSegmenter, SegmentationResult

__all__ = [
    "CleanLeafResult",
    "ConfidenceSignals",
    "CropMatch",
    "CropVerifier",
    "Decision",
    "LeafAreaReport",
    "LeafSegmenter",
    "QualityReport",
    "RetakeReason",
    "SegmentationResult",
    "assess_image_quality",
    "extract_clean_leaf",
    "fuse_confidence",
    "leaf_area_score",
    "route",
    "validate_leaf_area",
]

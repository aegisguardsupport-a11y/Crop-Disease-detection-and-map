"""Explainable-AI subpackage for the CPL classifier.

We use SmoothGrad-style input-space saliency (rather than Grad-CAM++)
because it works directly on the original SavedModel without requiring
a Keras-side architecture rebuild. See ``saliency.py`` for the rationale.
"""

from __future__ import annotations

from cpl_crop.explain.overlay import (
    apply_jet_colormap,
    encode_png_base64,
    make_overlay,
    upsample_heatmap,
)
from cpl_crop.explain.saliency import SaliencyResult, SmoothGradExplainer

__all__ = [
    "SaliencyResult",
    "SmoothGradExplainer",
    "apply_jet_colormap",
    "encode_png_base64",
    "make_overlay",
    "upsample_heatmap",
]

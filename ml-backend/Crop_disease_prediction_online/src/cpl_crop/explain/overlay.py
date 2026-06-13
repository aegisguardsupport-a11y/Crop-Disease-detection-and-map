"""Visualisation helpers: colormap, upsampling, alpha blend, PNG encode.

Pure NumPy + PIL — no matplotlib dependency. Two reasons:

* Keeps the runtime image small.
* Lets us tightly control how the LUT is built so the colormap is
  exactly the same in tests, the API, and the (future) Streamlit UI.
"""

from __future__ import annotations

import base64
import io
from typing import Any, Final

import numpy as np
from numpy.typing import NDArray
from PIL import Image


def _build_jet_lut() -> NDArray[np.uint8]:
    """Build a 256-entry uint8 LUT approximating matplotlib's "jet"."""
    x = np.linspace(0.0, 1.0, 256, dtype=np.float32)
    r = np.clip(np.minimum(4.0 * x - 1.5, -4.0 * x + 4.5), 0.0, 1.0)
    g = np.clip(np.minimum(4.0 * x - 0.5, -4.0 * x + 3.5), 0.0, 1.0)
    b = np.clip(np.minimum(4.0 * x + 0.5, -4.0 * x + 2.5), 0.0, 1.0)
    lut = (np.stack([r, g, b], axis=-1) * 255.0).astype(np.uint8)
    return np.asarray(lut, dtype=np.uint8)


JET_LUT: Final[NDArray[np.uint8]] = _build_jet_lut()


def upsample_heatmap(
    heatmap: NDArray[np.floating[Any]],
    target_size: tuple[int, int],
) -> NDArray[np.float32]:
    """Bilinearly upsample a 2-D heatmap to ``(height, width)``.

    Args:
        heatmap: ``(h, w)`` float array, expected to already lie in [0, 1].
        target_size: ``(height, width)``.

    Returns:
        ``(height, width)`` float32 array clipped to [0, 1].
    """
    if heatmap.ndim != 2:
        raise ValueError(f"Expected 2-D heatmap; got shape {heatmap.shape}")
    th, tw = target_size
    if th <= 0 or tw <= 0:
        raise ValueError(f"target_size must be positive; got {target_size}")

    img = Image.fromarray((np.clip(heatmap, 0.0, 1.0) * 255.0).astype(np.uint8))
    img = img.resize((tw, th), Image.Resampling.BILINEAR)
    arr = np.asarray(img, dtype=np.float32) / 255.0
    return np.asarray(arr, dtype=np.float32)


def apply_jet_colormap(heatmap_01: NDArray[np.floating[Any]]) -> NDArray[np.uint8]:
    """Convert a ``(H, W)`` heatmap in ``[0, 1]`` to an ``(H, W, 3)`` RGB."""
    if heatmap_01.ndim != 2:
        raise ValueError(f"Expected 2-D heatmap; got shape {heatmap_01.shape}")
    idx = np.clip(np.round(heatmap_01 * 255.0), 0, 255).astype(np.uint8)
    return np.asarray(JET_LUT[idx], dtype=np.uint8)


def make_overlay(
    base_image: Image.Image | NDArray[np.uint8],
    heatmap_01: NDArray[np.floating[Any]],
    alpha: float = 0.45,
) -> NDArray[np.uint8]:
    """Alpha-blend a ``(H, W)`` heatmap on top of ``base_image``.

    Args:
        base_image: input leaf image (PIL Image or HxWx3 uint8 array).
            Will be resized to match the heatmap if shapes disagree.
        heatmap_01: ``(H, W)`` float in [0, 1].
        alpha: weight given to the heatmap; 0 = base only, 1 = heatmap only.

    Returns:
        ``(H, W, 3)`` uint8 RGB array.
    """
    if not 0.0 <= alpha <= 1.0:
        raise ValueError(f"alpha must be in [0, 1]; got {alpha}")

    if isinstance(base_image, Image.Image):
        base_pil = base_image.convert("RGB")
    else:
        base_pil = Image.fromarray(np.asarray(base_image, dtype=np.uint8)).convert("RGB")

    h, w = heatmap_01.shape
    if (base_pil.height, base_pil.width) != (h, w):
        base_pil = base_pil.resize((w, h), Image.Resampling.BILINEAR)
    base_arr = np.asarray(base_pil, dtype=np.float32)

    color = apply_jet_colormap(heatmap_01).astype(np.float32)

    # Modulate alpha by heatmap intensity so background pixels stay clean.
    intensity = np.clip(heatmap_01, 0.0, 1.0)[..., None]
    eff_alpha = alpha * intensity  # (H, W, 1)
    blended = base_arr * (1.0 - eff_alpha) + color * eff_alpha
    return np.clip(blended, 0, 255).astype(np.uint8)


def encode_png_base64(rgb: NDArray[np.uint8]) -> str:
    """Encode an ``(H, W, 3)`` uint8 RGB array as a base64 PNG string."""
    if rgb.ndim != 3 or rgb.shape[-1] != 3:
        raise ValueError(f"Expected (H, W, 3) uint8 RGB; got shape {rgb.shape}")
    if rgb.dtype != np.uint8:
        rgb = rgb.astype(np.uint8, copy=False)
    img = Image.fromarray(rgb)
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode("ascii")

"""Fast tests for the overlay / colormap helpers.

These don't load TensorFlow and run in <1 s.
"""

from __future__ import annotations

import base64
import io

import numpy as np
import pytest
from PIL import Image

from cpl_crop.explain.overlay import (
    JET_LUT,
    apply_jet_colormap,
    encode_png_base64,
    make_overlay,
    upsample_heatmap,
)


# ---------------------------------------------------------------------------
# JET LUT
# ---------------------------------------------------------------------------
def test_jet_lut_shape_and_dtype() -> None:
    assert JET_LUT.shape == (256, 3)
    assert JET_LUT.dtype == np.uint8


def test_jet_lut_lowest_is_blueish_highest_is_redish() -> None:
    low = JET_LUT[0]  # ~ blue
    high = JET_LUT[-1]  # ~ red
    assert low[2] > low[0]  # B > R at low
    assert high[0] > high[2]  # R > B at high


# ---------------------------------------------------------------------------
# upsample_heatmap
# ---------------------------------------------------------------------------
def test_upsample_returns_target_size_and_range() -> None:
    h = np.zeros((9, 9), dtype=np.float32)
    h[4, 4] = 1.0
    out = upsample_heatmap(h, (260, 260))
    assert out.shape == (260, 260)
    assert out.dtype == np.float32
    assert 0.0 <= out.min() <= out.max() <= 1.0
    # Center of upsampled map should be brighter than the corners
    assert out[130, 130] > out[0, 0]


def test_upsample_clips_inputs_outside_unit_range() -> None:
    h = np.array([[2.0, -3.0], [0.5, 0.5]], dtype=np.float32)
    out = upsample_heatmap(h, (8, 8))
    assert out.min() >= 0.0
    assert out.max() <= 1.0


def test_upsample_rejects_3d_input() -> None:
    with pytest.raises(ValueError, match="2-D"):
        upsample_heatmap(np.zeros((3, 3, 3), dtype=np.float32), (10, 10))


def test_upsample_rejects_zero_target() -> None:
    with pytest.raises(ValueError, match="positive"):
        upsample_heatmap(np.zeros((3, 3), dtype=np.float32), (0, 10))


# ---------------------------------------------------------------------------
# apply_jet_colormap
# ---------------------------------------------------------------------------
def test_apply_colormap_shape_and_dtype() -> None:
    h = np.linspace(0.0, 1.0, 100, dtype=np.float32).reshape(10, 10)
    out = apply_jet_colormap(h)
    assert out.shape == (10, 10, 3)
    assert out.dtype == np.uint8


def test_apply_colormap_zero_is_blueish_one_is_redish() -> None:
    h = np.array([[0.0, 1.0]], dtype=np.float32)
    out = apply_jet_colormap(h)
    z, o = out[0, 0], out[0, 1]
    assert z[2] > z[0]
    assert o[0] > o[2]


# ---------------------------------------------------------------------------
# make_overlay
# ---------------------------------------------------------------------------
def test_make_overlay_returns_image_shaped_array() -> None:
    base = Image.new("RGB", (32, 32), color=(100, 100, 100))
    h = np.zeros((32, 32), dtype=np.float32)
    h[10:20, 10:20] = 1.0  # bright square
    out = make_overlay(base, h, alpha=0.5)
    assert out.shape == (32, 32, 3)
    assert out.dtype == np.uint8
    # Hot region should differ from background; cold region should equal base
    assert not np.array_equal(out[15, 15], np.array([100, 100, 100], dtype=np.uint8))
    assert np.array_equal(out[0, 0], np.array([100, 100, 100], dtype=np.uint8))


def test_make_overlay_resizes_base_when_shapes_disagree() -> None:
    base = Image.new("RGB", (10, 10), color=(50, 50, 50))
    h = np.zeros((20, 20), dtype=np.float32)
    out = make_overlay(base, h)
    assert out.shape == (20, 20, 3)


def test_make_overlay_alpha_zero_returns_base_unchanged() -> None:
    base = Image.new("RGB", (16, 16), color=(123, 45, 67))
    h = np.ones((16, 16), dtype=np.float32)
    out = make_overlay(base, h, alpha=0.0)
    assert np.array_equal(out, np.full((16, 16, 3), [123, 45, 67], dtype=np.uint8))


def test_make_overlay_rejects_invalid_alpha() -> None:
    base = Image.new("RGB", (16, 16))
    h = np.zeros((16, 16), dtype=np.float32)
    with pytest.raises(ValueError, match="alpha"):
        make_overlay(base, h, alpha=1.5)


# ---------------------------------------------------------------------------
# encode_png_base64
# ---------------------------------------------------------------------------
def test_encode_png_base64_roundtrips() -> None:
    rgb = (np.random.RandomState(0).rand(64, 64, 3) * 255).astype(np.uint8)
    b64 = encode_png_base64(rgb)
    raw = base64.b64decode(b64)
    decoded = np.asarray(Image.open(io.BytesIO(raw)))
    assert decoded.shape == rgb.shape
    assert decoded.dtype == np.uint8


def test_encode_png_base64_rejects_non_rgb() -> None:
    with pytest.raises(ValueError, match=r"\(H, W, 3\)"):
        encode_png_base64(np.zeros((10, 10), dtype=np.uint8))

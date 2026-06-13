"""Tests for image preprocessing."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from cpl_crop.config import Settings
from cpl_crop.preprocessing import load_preprocessing_config, preprocess_image


@pytest.fixture
def image_size(settings: Settings) -> tuple[int, int]:
    cfg = load_preprocessing_config(settings.preprocessing_path)
    h, w = cfg["image_size"]
    return (h, w)


def test_load_preprocessing_config_matches_bundle(settings: Settings) -> None:
    cfg = load_preprocessing_config(settings.preprocessing_path)
    assert cfg["model_backbone"] == "efficientnetb2"
    assert cfg["image_size"] == [260, 260]


def test_preprocess_pil_input(image_size: tuple[int, int]) -> None:
    img = Image.new("RGB", (500, 400), color=(120, 80, 50))
    out = preprocess_image(img, image_size)
    assert out.shape == (1, image_size[0], image_size[1], 3)
    assert out.dtype == np.float32
    assert 0.0 <= out.min() <= out.max() <= 255.0


def test_preprocess_grayscale_promoted_to_rgb(image_size: tuple[int, int]) -> None:
    img = Image.new("L", (200, 200), color=128)
    out = preprocess_image(img, image_size)
    assert out.shape == (1, image_size[0], image_size[1], 3)
    # All three channels should be ~128 after RGB conversion
    np.testing.assert_allclose(out[..., 0], out[..., 1])
    np.testing.assert_allclose(out[..., 1], out[..., 2])


def test_preprocess_bytes_input(image_size: tuple[int, int]) -> None:
    img = Image.new("RGB", (300, 300), color=(10, 200, 30))
    buf = BytesIO()
    img.save(buf, format="PNG")
    out = preprocess_image(buf.getvalue(), image_size)
    assert out.shape == (1, image_size[0], image_size[1], 3)


def test_preprocess_path_input(tmp_path: Path, image_size: tuple[int, int]) -> None:
    p = tmp_path / "leaf.jpg"
    Image.new("RGB", (300, 300), color=(50, 150, 50)).save(p, format="JPEG")
    out = preprocess_image(p, image_size)
    assert out.shape == (1, image_size[0], image_size[1], 3)


def test_preprocess_rejects_unsupported_type(image_size: tuple[int, int]) -> None:
    with pytest.raises(TypeError):
        preprocess_image(12345, image_size)  # type: ignore[arg-type]


def test_preprocess_value_range_is_zero_to_255(image_size: tuple[int, int]) -> None:
    """Critical: model expects 0..255, NOT 0..1."""
    img = Image.new("RGB", (100, 100), color=(255, 255, 255))
    out = preprocess_image(img, image_size)
    assert out.max() == pytest.approx(255.0)

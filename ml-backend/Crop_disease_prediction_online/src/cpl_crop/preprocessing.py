"""Image preprocessing for the EfficientNetB2 crop-disease model.

The model contract (see ``exports/README.md``):
    * resize bilinear to 260x260 RGB
    * dtype float32, values in ``[0, 255]`` (NOT 0..1; the backbone
      includes its own normalisation layer)
    * leading batch axis  ->  shape ``(1, 260, 260, 3)``
"""

from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path
from typing import TypedDict, cast

import numpy as np
from numpy.typing import NDArray
from PIL import Image


class PreprocessingConfig(TypedDict):
    model_backbone: str
    image_size: list[int]  # [height, width]
    batch_size: int
    use_tf_data_disk_cache: bool


def load_preprocessing_config(path: str | Path) -> PreprocessingConfig:
    """Read and validate ``cpl_preprocessing_config.json``."""
    p = Path(path)
    raw = json.loads(p.read_text(encoding="utf-8"))
    if "image_size" not in raw or len(raw["image_size"]) != 2:
        raise ValueError(f"Invalid preprocessing config at {p}: {raw}")
    h, w = raw["image_size"]
    if not (isinstance(h, int) and isinstance(w, int) and h > 0 and w > 0):
        raise ValueError(f"image_size must be two positive ints, got {raw['image_size']}")
    return cast(PreprocessingConfig, raw)


ImageSource = bytes | bytearray | str | Path | Image.Image


def preprocess_image(
    source: ImageSource,
    image_size: tuple[int, int],
) -> NDArray[np.float32]:
    """Decode + resize + format an image into a model-ready tensor.

    Args:
        source: raw image bytes, a path-like, or a PIL ``Image``.
        image_size: ``(height, width)`` to resize to (e.g. ``(260, 260)``).

    Returns:
        A ``(1, H, W, 3)`` float32 array with values in ``[0, 255]``.

    Raises:
        TypeError: source is not one of the supported types.
        OSError: the bytes/path cannot be decoded as an image.
    """
    raw_img: Image.Image
    if isinstance(source, (bytes, bytearray)):
        raw_img = Image.open(BytesIO(bytes(source)))
    elif isinstance(source, (str, Path)):
        raw_img = Image.open(source)
    elif isinstance(source, Image.Image):
        raw_img = source
    else:
        raise TypeError(f"Unsupported source type: {type(source).__name__}")

    rgb_img = raw_img.convert("RGB").resize(image_size, Image.Resampling.BILINEAR)
    arr = np.asarray(rgb_img, dtype=np.float32)
    return arr[None, ...]

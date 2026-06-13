"""End-to-end smoke test: load the SavedModel and run a synthetic image.

Marked ``@slow`` because it loads the full SavedModel (~10 s, ~250 MB RAM).
Run with: ``pytest -m slow``.
"""

from __future__ import annotations

import numpy as np
import pytest
from PIL import Image

from cpl_crop.config import Settings
from cpl_crop.labels import load_labels
from cpl_crop.model_loader import get_bundle, reset_bundle
from cpl_crop.preprocessing import load_preprocessing_config, preprocess_image


@pytest.fixture(autouse=True)
def _reset_singleton():
    reset_bundle()
    yield
    reset_bundle()


@pytest.mark.slow
def test_model_loads_and_predicts_synthetic_image(settings: Settings) -> None:
    bundle = get_bundle(settings.saved_model_dir)
    labels = load_labels(settings.labels_path)
    cfg = load_preprocessing_config(settings.preprocessing_path)

    # Sanity on the loaded model
    assert bundle.num_classes == len(labels) == 139

    # Preprocess a synthetic green-leaf-like image
    img = Image.new("RGB", (300, 300), color=(80, 140, 60))
    h, w = cfg["image_size"]
    x = preprocess_image(img, (h, w))
    assert x.shape == (1, h, w, 3)
    assert x.dtype == np.float32

    probs = bundle.predict(x)
    # Output contract: (1, 139), softmax, dtype float32
    assert probs.shape == (1, 139)
    assert probs.dtype == np.float32
    assert (probs >= 0).all() and (probs <= 1).all()
    np.testing.assert_allclose(probs.sum(axis=1), 1.0, atol=1e-4)

    # Top-1 must be a valid class id
    top1 = int(probs.argmax(axis=1)[0])
    assert top1 in labels
    print(f"\nSmoke test top-1 on synthetic image: {labels[top1]} ({probs[0, top1] * 100:.2f}%)")


@pytest.mark.slow
def test_predict_rejects_non_4d_input(settings: Settings) -> None:
    bundle = get_bundle(settings.saved_model_dir)
    with pytest.raises(ValueError, match="4-D"):
        bundle.predict(np.zeros((260, 260, 3), dtype=np.float32))


@pytest.mark.slow
def test_get_bundle_returns_singleton(settings: Settings) -> None:
    a = get_bundle(settings.saved_model_dir)
    b = get_bundle(settings.saved_model_dir)
    assert a is b

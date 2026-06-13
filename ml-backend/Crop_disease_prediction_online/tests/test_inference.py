"""Fast unit tests for ``cpl_crop.inference.predict_topk`` using a fake bundle.

These tests don't load TF/SavedModel; they use a stub object that satisfies
the small subset of :class:`ModelBundle` the function actually calls.
"""

from __future__ import annotations

import numpy as np
import pytest
from PIL import Image

from cpl_crop.inference import marginalize_crops, predict_topk


class FakeBundle:
    """Minimal stand-in for :class:`cpl_crop.model_loader.ModelBundle`."""

    def __init__(self, probs: np.ndarray) -> None:
        if probs.ndim != 1:
            raise ValueError("FakeBundle expects a 1-D probability vector")
        self._probs = probs.astype(np.float32, copy=False)
        self.num_classes = int(probs.shape[0])

    def predict(self, batch: np.ndarray) -> np.ndarray:
        n = int(batch.shape[0])
        return np.tile(self._probs, (n, 1)).astype(np.float32)


@pytest.fixture
def labels() -> dict[int, str]:
    return {
        0: "tomato::Late_blight",
        1: "tomato::Early_blight",
        2: "potato::Late_blight",
        3: "tomato::healthy",
    }


@pytest.fixture
def synthetic_image() -> Image.Image:
    return Image.new("RGB", (100, 100), color=(50, 100, 50))


def test_predict_topk_returns_descending_confidence(
    labels: dict[int, str], synthetic_image: Image.Image
) -> None:
    # Class 2 wins, then 0, then 1, then 3
    probs = np.array([0.3, 0.05, 0.6, 0.05], dtype=np.float32)
    bundle = FakeBundle(probs)

    result = predict_topk(bundle, synthetic_image, (32, 32), labels, topk=3)

    assert [p.rank for p in result] == [1, 2, 3]
    assert [p.label for p in result] == [
        "potato::Late_blight",
        "tomato::Late_blight",
        "tomato::Early_blight",
    ]
    assert result[0].confidence == pytest.approx(0.6)
    assert result[0].crop == "potato"
    assert result[0].disease == "Late_blight"


def test_predict_topk_default_k_is_3(labels, synthetic_image) -> None:
    bundle = FakeBundle(np.array([0.4, 0.3, 0.2, 0.1], dtype=np.float32))
    result = predict_topk(bundle, synthetic_image, (32, 32), labels)
    assert len(result) == 3


def test_predict_topk_returns_all_when_k_equals_classes(labels, synthetic_image) -> None:
    bundle = FakeBundle(np.array([0.4, 0.3, 0.2, 0.1], dtype=np.float32))
    result = predict_topk(bundle, synthetic_image, (32, 32), labels, topk=4)
    assert len(result) == 4


def test_predict_topk_rejects_zero(labels, synthetic_image) -> None:
    bundle = FakeBundle(np.array([0.4, 0.3, 0.2, 0.1], dtype=np.float32))
    with pytest.raises(ValueError, match="topk"):
        predict_topk(bundle, synthetic_image, (32, 32), labels, topk=0)


def test_predict_topk_rejects_too_large(labels, synthetic_image) -> None:
    bundle = FakeBundle(np.array([0.4, 0.3, 0.2, 0.1], dtype=np.float32))
    with pytest.raises(ValueError, match="topk"):
        predict_topk(bundle, synthetic_image, (32, 32), labels, topk=5)


def test_predict_topk_rejects_empty_labels(synthetic_image) -> None:
    bundle = FakeBundle(np.array([0.5, 0.5], dtype=np.float32))
    with pytest.raises(ValueError, match="labels map is empty"):
        predict_topk(bundle, synthetic_image, (32, 32), {}, topk=1)


# ---------------------------------------------------------------------------
# Crop marginalization
# ---------------------------------------------------------------------------
def test_marginalize_crops_sums_by_crop() -> None:
    labels = {
        0: "tomato::Late_blight",
        1: "tomato::Early_blight",
        2: "tomato::Healthy",
        3: "potato::Late_blight",
        4: "potato::Healthy",
        5: "wheat::LeafBlight",
    }
    probs = np.array([0.20, 0.15, 0.05, 0.30, 0.05, 0.25], dtype=np.float32)
    # Expected:
    #   tomato = 0.40, best within = Late_blight (0.20), conditional = 0.50
    #   potato = 0.35, best within = Late_blight (0.30), conditional ≈ 0.857
    #   wheat  = 0.25, best within = LeafBlight (0.25), conditional = 1.00
    crops = marginalize_crops(probs, labels, topk=3)
    assert [c.crop for c in crops] == ["tomato", "potato", "wheat"]
    assert crops[0].confidence == pytest.approx(0.40, abs=1e-5)
    assert crops[0].top_disease == "Late_blight"
    assert crops[0].top_disease_conditional == pytest.approx(0.50, abs=1e-5)
    assert crops[1].confidence == pytest.approx(0.35, abs=1e-5)
    assert crops[1].top_disease_conditional == pytest.approx(0.857, abs=1e-3)
    assert crops[2].confidence == pytest.approx(0.25, abs=1e-5)
    assert crops[2].top_disease_conditional == pytest.approx(1.0, abs=1e-5)


def test_marginalize_crops_recovers_winner_with_class_imbalance() -> None:
    """When one crop has many small probs, marginalization can outvote a crop
    with a single big prob — exactly the wheat-vs-onion failure mode."""
    labels = {
        # onion: 5 classes, small per-class probs
        0: "onion::A", 1: "onion::B", 2: "onion::C", 3: "onion::D", 4: "onion::E",
        # wheat: 1 class with the model's biggest single prob
        5: "wheat::LeafBlight",
    }
    probs = np.array([0.10, 0.10, 0.10, 0.10, 0.10, 0.50], dtype=np.float32)
    # Joint argmax: wheat::LeafBlight (0.50)
    # Crop marginal: onion=0.50, wheat=0.50 — tie at the marginal level
    # In this case both crops have P(crop)=0.50; ordering is by sort, but
    # we don't rely on tie-breaking.
    crops = marginalize_crops(probs, labels, topk=2)
    assert {c.crop for c in crops} == {"onion", "wheat"}
    assert crops[0].confidence == pytest.approx(0.50, abs=1e-5)
    assert crops[1].confidence == pytest.approx(0.50, abs=1e-5)


def test_marginalize_crops_validates_input() -> None:
    labels = {0: "tomato::A", 1: "tomato::B"}
    with pytest.raises(ValueError, match="1-D"):
        marginalize_crops(np.zeros((2, 2), dtype=np.float32), labels, topk=1)
    with pytest.raises(ValueError, match="!="):
        marginalize_crops(np.array([0.5], dtype=np.float32), labels, topk=1)
    with pytest.raises(ValueError, match="topk"):
        marginalize_crops(np.array([0.5, 0.5], dtype=np.float32), labels, topk=5)

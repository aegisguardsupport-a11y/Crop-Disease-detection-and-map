"""Tests for the label-map loader."""

from __future__ import annotations

import json

import pytest

from cpl_crop.config import Settings
from cpl_crop.labels import load_labels, split_label


def test_load_labels_returns_complete_dense_map(settings: Settings) -> None:
    labels = load_labels(settings.labels_path)
    assert len(labels) == 139
    assert set(labels.keys()) == set(range(139))
    assert all(isinstance(v, str) and "::" in v for v in labels.values())


def test_load_labels_caches(settings: Settings) -> None:
    a = load_labels(settings.labels_path)
    b = load_labels(settings.labels_path)
    assert a is b  # @lru_cache returns the same dict instance


def test_split_label_valid() -> None:
    crop, disease = split_label("tomato::Late_blight")
    assert crop == "tomato"
    assert disease == "Late_blight"


def test_split_label_handles_double_colons_in_disease() -> None:
    # tomato::Tomato___Late_blight is a real label format in the bundle
    crop, disease = split_label("tomato::Tomato___Late_blight")
    assert crop == "tomato"
    assert disease == "Tomato___Late_blight"


def test_split_label_rejects_unseparated_string() -> None:
    with pytest.raises(ValueError, match="separator"):
        split_label("not_a_label")


def test_load_labels_rejects_non_dense(tmp_path) -> None:
    p = tmp_path / "broken.json"
    p.write_text(json.dumps({"0": "a::b", "2": "c::d"}))  # missing 1
    with pytest.raises(ValueError, match="not dense"):
        load_labels(p)


def test_load_labels_rejects_empty(tmp_path) -> None:
    p = tmp_path / "empty.json"
    p.write_text("{}")
    with pytest.raises(ValueError, match="Empty"):
        load_labels(p)

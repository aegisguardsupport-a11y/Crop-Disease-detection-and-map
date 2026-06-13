"""High-level inference: image source -> top-k predictions.

This wraps :mod:`cpl_crop.preprocessing` + :class:`cpl_crop.model_loader.ModelBundle`
into a single call so HTTP routes / CLI / Streamlit don't have to repeat the
plumbing.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from cpl_crop.labels import split_label
from cpl_crop.model_loader import ModelBundle
from cpl_crop.preprocessing import ImageSource, preprocess_image


@dataclass(frozen=True)
class Prediction:
    """One ranked classification result."""

    rank: int
    label: str  # full "crop::disease"
    crop: str
    disease: str
    confidence: float  # 0..1


@dataclass(frozen=True)
class CropPrediction:
    """One ranked crop result, marginalised across all of that crop's diseases.

    ``confidence`` here is ``P(crop) = sum_d P(crop::d)``.
    ``top_disease_conditional`` is ``P(disease | crop)`` — the relative
    rank of the most-likely disease *within* this crop's classes.
    """

    rank: int
    crop: str
    confidence: float                 # P(crop) — marginal
    top_disease: str                  # disease string only, e.g. "Late_blight"
    top_disease_label: str            # full "crop::disease"
    top_disease_conditional: float    # P(disease | crop)
    top_disease_joint: float          # P(crop::disease) — for cross-checking with /predict


def predict_topk(
    bundle: ModelBundle,
    image: ImageSource,
    image_size: tuple[int, int],
    labels: dict[int, str],
    topk: int = 3,
) -> list[Prediction]:
    """Run inference and return the top-k predictions, ranked by confidence.

    Args:
        bundle: a loaded :class:`ModelBundle`.
        image: bytes / path / PIL Image.
        image_size: (height, width) the model expects.
        labels: dense {class_id: "crop::disease"} map.
        topk: number of predictions to return (must be 1..len(labels)).

    Returns:
        A list of :class:`Prediction` of length ``topk``, descending by
        confidence.

    Raises:
        ValueError: ``topk`` is out of range, or ``labels`` is empty.
    """
    if not labels:
        raise ValueError("labels map is empty")
    n_classes = len(labels)
    if not 1 <= topk <= n_classes:
        raise ValueError(f"topk must be in [1, {n_classes}], got {topk}")

    x = preprocess_image(image, image_size)
    probs = bundle.predict(x)[0]  # (num_classes,)

    # argpartition is faster than full argsort for small k, but we still need
    # the top-k themselves sorted, so we sort just those k indices.
    top_idx = np.argpartition(-probs, topk - 1)[:topk]
    top_idx = top_idx[np.argsort(-probs[top_idx])]

    results: list[Prediction] = []
    for rank, idx in enumerate(top_idx, start=1):
        i = int(idx)
        label = labels[i]
        crop, disease = split_label(label)
        results.append(
            Prediction(
                rank=rank,
                label=label,
                crop=crop,
                disease=disease,
                confidence=float(probs[i]),
            )
        )
    return results




def marginalize_crops(
    probs: NDArray[np.float32],
    labels: dict[int, str],
    topk: int = 5,
) -> list[CropPrediction]:
    """Marginalise a 139-d softmax to per-crop probabilities.

    Given ``P(crop::disease)`` over all classes, computes
    ``P(crop) = sum_d P(crop::d)`` and the conditional best disease
    ``argmax_d P(crop::d) / P(crop)`` for each crop, then returns the
    top-``k`` crops sorted by marginal probability.

    This decouples the crop decision from the disease decision and
    surfaces the model's "soft votes" — useful when the joint argmax
    picks a high-class-count crop (e.g. onion has 13 classes, wheat
    has 5) just because of class imbalance.

    Args:
        probs: ``(num_classes,)`` float array (softmax probabilities).
        labels: dense ``{class_id: "crop::disease"}`` map.
        topk: number of top crops to return.

    Returns:
        A list of :class:`CropPrediction`, descending by ``confidence``,
        of length up to ``topk``.

    Raises:
        ValueError: ``probs`` shape doesn't match ``len(labels)``, or
            ``topk`` is out of range.
    """
    if probs.ndim != 1:
        raise ValueError(f"Expected 1-D probs; got shape {probs.shape}")
    if probs.shape[0] != len(labels):
        raise ValueError(
            f"probs length {probs.shape[0]} != #labels {len(labels)}"
        )

    # Group class ids by crop.
    crop_to_class_ids: dict[str, list[int]] = {}
    for class_id, label in labels.items():
        crop, _ = split_label(label)
        crop_to_class_ids.setdefault(crop, []).append(class_id)

    if not 1 <= topk <= len(crop_to_class_ids):
        raise ValueError(
            f"topk must be in [1, {len(crop_to_class_ids)}]; got {topk}"
        )

    # Marginal P(crop) and best disease within each crop.
    crop_records: list[tuple[str, float, int, float]] = []
    for crop, ids in crop_to_class_ids.items():
        ids_arr = np.asarray(ids)
        crop_probs = probs[ids_arr]
        p_crop = float(crop_probs.sum())
        best_within = int(np.argmax(crop_probs))
        best_class_id = int(ids_arr[best_within])
        joint = float(crop_probs[best_within])
        crop_records.append((crop, p_crop, best_class_id, joint))

    crop_records.sort(key=lambda r: r[1], reverse=True)

    results: list[CropPrediction] = []
    for rank, (crop, p_crop, best_id, joint) in enumerate(crop_records[:topk], start=1):
        full_label = labels[best_id]
        _, disease = split_label(full_label)
        conditional = joint / p_crop if p_crop > 0 else 0.0
        results.append(
            CropPrediction(
                rank=rank,
                crop=crop,
                confidence=p_crop,
                top_disease=disease,
                top_disease_label=full_label,
                top_disease_conditional=float(conditional),
                top_disease_joint=joint,
            )
        )
    return results

"""Phase 3.8 — Hierarchical Crop-Disease Bundle.

Wraps the trained hierarchical bundle:

* **EfficientNet-B0 backbone** — produces a 1280-d penultimate feature vector.
* **Crop router** (sklearn LogisticRegression on the standardised features) —
  produces ``log P(crop)`` over 20 crops.
* **Per-crop disease heads** (one sklearn LogisticRegression per crop) —
  each produces ``log P(disease | crop)`` over its crop's diseases only.

Final score for class ``c::d`` is:

    score[c::d] = crop_scale * log_P(crop_of_c) + log_P(disease | crop_of_c)

then softmax across all 134 classes. ``crop_scale`` is read from the
bundle's manifest; the project trained with 0.4.

The whole bundle (backbone, router, all 20 heads, all metadata) is loaded
once at FastAPI startup and shared across requests.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import torch
from numpy.typing import NDArray
from PIL import Image
from torchvision import models as tv_models
from torchvision import transforms

logger = logging.getLogger(__name__)

CHECKPOINT_KEY = "model_state_dict"


# ---------------------------------------------------------------------------
# Result dataclasses
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class HierarchicalPrediction:
    """One ranked class prediction (134-class softmax output)."""

    rank: int
    class_id: int
    label: str            # full crop::disease
    crop: str
    disease: str
    confidence: float     # final softmax probability


@dataclass(frozen=True)
class CropRouterPrediction:
    """One ranked crop from the trained router (P(crop))."""

    rank: int
    crop: str
    confidence: float     # softmax of router logits


@dataclass(frozen=True)
class WithinCropDisease:
    """Disease ranked within a single crop, from that crop's per-crop head."""

    rank: int
    crop: str
    disease: str
    label: str            # full crop::disease
    confidence: float     # softmax over the per-crop head's class set


@dataclass(frozen=True)
class HierarchicalResult:
    """Full output of one image through the bundle."""

    predictions: list[HierarchicalPrediction]
    crop_router: list[CropRouterPrediction]
    within_top_crop: list[WithinCropDisease]    # diseases ranked inside the router's top-1 crop
    backbone_features: NDArray[np.float32]      # (1280,) for downstream re-use (e.g. SmoothGrad)


# ---------------------------------------------------------------------------
# Backbone wrapper
# ---------------------------------------------------------------------------
class _EfficientNetB0Features(torch.nn.Module):
    """EfficientNet-B0 modified to expose penultimate pooled features.

    Mirrors the architecture in the bundle's reference inference script.
    """

    def __init__(self, num_classes: int) -> None:
        super().__init__()
        self.model = tv_models.efficientnet_b0(weights=None)
        in_features = self.model.classifier[1].in_features
        self.model.classifier = torch.nn.Sequential(
            torch.nn.Dropout(p=0.30, inplace=True),
            torch.nn.Linear(in_features, num_classes),
        )

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        x = self.model.features(x)
        x = self.model.avgpool(x)
        features = torch.flatten(x, 1)
        logits = self.model.classifier(features)
        return features, logits


# ---------------------------------------------------------------------------
# Runtime
# ---------------------------------------------------------------------------
class HierarchicalBundleRuntime:
    """Loads the bundle once and runs the full hierarchical inference."""

    def __init__(self, bundle_root: Path, device: str | None = None) -> None:
        self._bundle_root = Path(bundle_root)
        if not self._bundle_root.is_dir():
            raise FileNotFoundError(
                f"Hierarchical bundle root not found: {self._bundle_root}"
            )

        self._device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        logger.info("HierarchicalBundleRuntime: loading from %s on %s",
                    self._bundle_root, self._device)

        # Read manifest + metadata
        meta = self._bundle_root / "metadata"
        models_dir = self._bundle_root / "models"
        with (meta / "bundle_manifest.json").open(encoding="utf-8") as f:
            self._manifest: dict[str, Any] = json.load(f)
        with (meta / "id_to_label.json").open(encoding="utf-8") as f:
            self._id_to_label: dict[int, str] = {int(k): v for k, v in json.load(f).items()}
        with (meta / "crop_order.json").open(encoding="utf-8") as f:
            self._crop_order: list[str] = list(json.load(f))
        with (meta / "preprocessing_config.json").open(encoding="utf-8") as f:
            self._preprocessing: dict[str, Any] = json.load(f)

        self._num_classes = len(self._id_to_label)
        self._crop_scale = float(
            self._manifest.get("selected_inference_settings", {}).get("crop_scale", 0.4)
        )

        # Group class ids by crop (in id-ascending order) and build crop column index
        self._crop_to_class_ids: dict[str, list[int]] = {}
        for class_id in sorted(self._id_to_label.keys()):
            crop = self._id_to_label[class_id].split("::", 1)[0]
            self._crop_to_class_ids.setdefault(crop, []).append(class_id)
        # Sorted crop names == column order used by the router (it was trained with sorted crops)
        self._crops_sorted = sorted(self._crop_to_class_ids.keys())
        self._crop_to_router_col = {c: i for i, c in enumerate(self._crops_sorted)}

        # Build preprocessing pipeline (224x224, ImageNet normalisation)
        cfg = self._preprocessing
        self._transform = transforms.Compose(
            [
                transforms.Resize(int(cfg["resize_shorter_side"])),
                transforms.CenterCrop(int(cfg["image_size"])),
                transforms.ToTensor(),
                transforms.Normalize(cfg["normalize_mean"], cfg["normalize_std"]),
            ]
        )

        # Load backbone weights
        self._backbone = _EfficientNetB0Features(num_classes=self._num_classes).to(self._device)
        backbone_path = models_dir / "best_model.pt"
        ckpt = torch.load(backbone_path, map_location=self._device, weights_only=False)
        self._backbone.model.load_state_dict(ckpt[CHECKPOINT_KEY])
        self._backbone.eval()

        # Load crop router
        router_payload = joblib.load(models_dir / "crop_router_refinement.joblib")
        self._router_scaler = router_payload.get("scaler")
        self._router_classifier = router_payload["classifier"]

        # Load each per-crop disease head
        head_dir = models_dir / "per_crop_heads"
        self._head_payloads: dict[str, dict[str, Any]] = {}
        for path in sorted(head_dir.glob("*_disease_head.joblib")):
            crop_name = path.name.removesuffix("_disease_head.joblib")
            self._head_payloads[crop_name] = joblib.load(path)

        missing = set(self._crops_sorted) - set(self._head_payloads.keys())
        if missing:
            raise RuntimeError(f"Missing per-crop heads for: {sorted(missing)}")

        logger.info(
            "HierarchicalBundleRuntime ready: %d crops, %d classes, crop_scale=%.2f",
            len(self._crops_sorted), self._num_classes, self._crop_scale,
        )

    # --- public API -------------------------------------------------------
    @property
    def num_classes(self) -> int:
        return self._num_classes

    @property
    def crops(self) -> list[str]:
        return list(self._crops_sorted)

    @property
    def id_to_label(self) -> dict[int, str]:
        return dict(self._id_to_label)

    @property
    def manifest(self) -> dict[str, Any]:
        return dict(self._manifest)

    def predict_crop(
        self,
        image: Image.Image | NDArray[np.uint8],
        topk: int = 5,
    ) -> tuple[list[CropRouterPrediction], NDArray[np.float32]]:
        """Run backbone + crop router only. Returns (crop_rankings, features).

        Use this for the split pipeline where crop prediction happens
        before segmentation/masking, and disease prediction happens after.
        """
        if isinstance(image, np.ndarray):
            if image.ndim != 3 or image.shape[-1] != 3:
                raise ValueError(f"Expected (H, W, 3) RGB; got shape {image.shape}")
            pil_image = Image.fromarray(image.astype(np.uint8))
        elif isinstance(image, Image.Image):
            pil_image = image.convert("RGB")
        else:
            raise TypeError(f"Unsupported image type {type(image).__name__}")

        tensor = self._transform(pil_image).unsqueeze(0).to(self._device)
        with torch.inference_mode():
            features_t, _ = self._backbone(tensor)
        features = features_t.detach().cpu().numpy().astype(np.float32)  # (1, 1280)

        x_router = features
        if self._router_scaler is not None:
            x_router = self._router_scaler.transform(features)
        crop_log_probs = self._router_classifier.predict_log_proba(x_router)
        router_probs = _softmax(crop_log_probs)[0]
        router_order = np.argsort(-router_probs)[: min(topk, len(self._crops_sorted))]

        crop_router_items: list[CropRouterPrediction] = []
        for rank, idx in enumerate(router_order, start=1):
            crop_router_items.append(
                CropRouterPrediction(
                    rank=rank,
                    crop=self._crops_sorted[int(idx)],
                    confidence=float(router_probs[int(idx)]),
                )
            )
        return crop_router_items, features[0].astype(np.float32)

    def predict_disease(
        self,
        image: Image.Image | NDArray[np.uint8],
        crop_name: str,
        topk: int = 5,
    ) -> list[WithinCropDisease]:
        """Run backbone + per-crop disease head on a (masked) image for a known crop.

        This is the second half of the split pipeline: given the crop name
        from predict_crop(), run the disease head on the segmented/masked image.
        """
        if crop_name not in self._head_payloads:
            raise ValueError(
                f"Unknown crop '{crop_name}'. Available: {self._crops_sorted}"
            )

        if isinstance(image, np.ndarray):
            if image.ndim != 3 or image.shape[-1] != 3:
                raise ValueError(f"Expected (H, W, 3) RGB; got shape {image.shape}")
            pil_image = Image.fromarray(image.astype(np.uint8))
        elif isinstance(image, Image.Image):
            pil_image = image.convert("RGB")
        else:
            raise TypeError(f"Unsupported image type {type(image).__name__}")

        tensor = self._transform(pil_image).unsqueeze(0).to(self._device)
        with torch.inference_mode():
            features_t, _ = self._backbone(tensor)
        features = features_t.detach().cpu().numpy().astype(np.float32)  # (1, 1280)

        class_ids = self._crop_to_class_ids[crop_name]
        payload = self._head_payloads[crop_name]
        kind = payload.get("kind")
        if kind == "constant":
            disease_log_probs = np.full((1, len(class_ids)), -1e9, dtype=np.float64)
            disease_log_probs[:, int(payload["constant_local_class"])] = 0.0
        else:
            scaler = payload["scaler"]
            clf = payload["classifier"]
            x_scaled = scaler.transform(features)
            raw = clf.predict_log_proba(x_scaled)
            disease_log_probs = np.full((1, len(class_ids)), -1e9, dtype=np.float64)
            seen = payload.get("seen_local_classes", list(range(raw.shape[1])))
            for col_idx, local_idx in enumerate(seen):
                disease_log_probs[:, int(local_idx)] = raw[:, col_idx]

        disease_probs = _softmax(disease_log_probs)[0]
        order = np.argsort(-disease_probs)[: min(topk, len(class_ids))]

        results: list[WithinCropDisease] = []
        for rank, local_idx in enumerate(order, start=1):
            cid = class_ids[int(local_idx)]
            label = self._id_to_label[cid]
            _, _, disease = label.partition("::")
            results.append(
                WithinCropDisease(
                    rank=rank,
                    crop=crop_name,
                    disease=disease,
                    label=label,
                    confidence=float(disease_probs[int(local_idx)]),
                )
            )
        return results

    def predict(
        self,
        image: Image.Image | NDArray[np.uint8],
        topk: int = 5,
        within_crop_topk: int = 5,
    ) -> HierarchicalResult:
        """Run the full pipeline on a single image."""
        if isinstance(image, np.ndarray):
            if image.ndim != 3 or image.shape[-1] != 3:
                raise ValueError(f"Expected (H, W, 3) RGB; got shape {image.shape}")
            pil_image = Image.fromarray(image.astype(np.uint8))
        elif isinstance(image, Image.Image):
            pil_image = image.convert("RGB")
        else:
            raise TypeError(f"Unsupported image type {type(image).__name__}")

        # 1. Preprocess
        tensor = self._transform(pil_image).unsqueeze(0).to(self._device)

        # 2. Backbone -> features
        with torch.inference_mode():
            features_t, _ = self._backbone(tensor)
        features = features_t.detach().cpu().numpy().astype(np.float32)  # (1, 1280)

        # 3. Crop router -> log_P(crop) over 20 sorted crops
        x_router = features
        if self._router_scaler is not None:
            x_router = self._router_scaler.transform(features)
        crop_log_probs = self._router_classifier.predict_log_proba(x_router)  # (1, 20)

        # 4. Per-crop heads -> log_P(disease | crop) for each crop
        # 5. Combine into full 134-class scores
        scores = np.full((1, self._num_classes), -1e9, dtype=np.float64)
        within_crop_disease_log_probs: dict[str, NDArray[np.float64]] = {}

        for crop, class_ids in self._crop_to_class_ids.items():
            payload = self._head_payloads[crop]
            kind = payload.get("kind")
            if kind == "constant":
                disease_log_probs = np.full((1, len(class_ids)), -1e9, dtype=np.float64)
                disease_log_probs[:, int(payload["constant_local_class"])] = 0.0
            else:
                scaler = payload["scaler"]
                clf = payload["classifier"]
                x_scaled = scaler.transform(features)
                raw = clf.predict_log_proba(x_scaled)  # (1, n_seen_local)
                disease_log_probs = np.full((1, len(class_ids)), -1e9, dtype=np.float64)
                seen = payload.get("seen_local_classes", list(range(raw.shape[1])))
                for col_idx, local_idx in enumerate(seen):
                    disease_log_probs[:, int(local_idx)] = raw[:, col_idx]

            within_crop_disease_log_probs[crop] = disease_log_probs[0]
            crop_col = self._crop_to_router_col[crop]
            for local_idx, class_id in enumerate(class_ids):
                scores[:, class_id] = (
                    self._crop_scale * crop_log_probs[:, crop_col]
                    + disease_log_probs[:, local_idx]
                )

        # 6. Softmax over 134 -> joint top-K
        joint_probs = _softmax(scores)[0]  # (134,)
        joint_order = np.argsort(-joint_probs)[:topk]
        predictions: list[HierarchicalPrediction] = []
        for rank, cid in enumerate(joint_order, start=1):
            cid = int(cid)
            label = self._id_to_label[cid]
            crop, _, disease = label.partition("::")
            predictions.append(
                HierarchicalPrediction(
                    rank=rank,
                    class_id=cid,
                    label=label,
                    crop=crop,
                    disease=disease,
                    confidence=float(joint_probs[cid]),
                )
            )

        # 7. Crop router top-K (independent of joint scores)
        router_probs = _softmax(crop_log_probs)[0]  # (20,)
        router_order = np.argsort(-router_probs)[: min(topk, len(self._crops_sorted))]
        crop_router_items: list[CropRouterPrediction] = []
        for rank, idx in enumerate(router_order, start=1):
            crop_router_items.append(
                CropRouterPrediction(
                    rank=rank,
                    crop=self._crops_sorted[int(idx)],
                    confidence=float(router_probs[int(idx)]),
                )
            )

        # 8. Within the router's top-1 crop, surface that head's top-K diseases
        top_crop = crop_router_items[0].crop if crop_router_items else None
        within_items: list[WithinCropDisease] = []
        if top_crop is not None:
            class_ids = self._crop_to_class_ids[top_crop]
            disease_log_probs = within_crop_disease_log_probs[top_crop]
            disease_probs = _softmax(disease_log_probs[None, :])[0]
            order = np.argsort(-disease_probs)[: min(within_crop_topk, len(class_ids))]
            for rank, local_idx in enumerate(order, start=1):
                cid = class_ids[int(local_idx)]
                label = self._id_to_label[cid]
                _, _, disease = label.partition("::")
                within_items.append(
                    WithinCropDisease(
                        rank=rank,
                        crop=top_crop,
                        disease=disease,
                        label=label,
                        confidence=float(disease_probs[int(local_idx)]),
                    )
                )

        return HierarchicalResult(
            predictions=predictions,
            crop_router=crop_router_items,
            within_top_crop=within_items,
            backbone_features=features[0].astype(np.float32),
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _softmax(x: NDArray[np.floating[Any]]) -> NDArray[np.float64]:
    """Numerically stable softmax over the last axis."""
    x = np.asarray(x, dtype=np.float64)
    x = x - x.max(axis=-1, keepdims=True)
    e = np.exp(x)
    result = e / e.sum(axis=-1, keepdims=True)
    return np.asarray(result, dtype=np.float64)

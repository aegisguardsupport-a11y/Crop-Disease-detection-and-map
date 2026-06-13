"""Stage A — CLIP-based zero-shot crop verifier.

Independent "second opinion" on the crop. We encode a list of text
prompts ("a photograph of a tomato leaf", "a photograph of a wheat leaf",
...) once at startup and cache the embeddings. Per request we encode the
image with CLIP and rank the prompts by cosine similarity.

This catches systematic crop confusions in the joint 139-class
classifier (e.g., elongated-narrow-leaf bias toward onion). The
verifier's top-1 crop becomes a separate vote; disagreement with the
classifier is fed back to the confidence engine.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import numpy as np
from numpy.typing import NDArray

logger = logging.getLogger(__name__)

# Default prompt template — keeping it neutral and consistent across crops.
DEFAULT_PROMPT_TEMPLATE = "a photograph of a {crop} leaf"

# Open-set gate: a separate prompt set of NON-leaf categories. We softmax the
# image over [crop-leaf prompts + these negatives]; if the probability mass on
# the leaf prompts is low, the image is not a crop leaf (keyboard, hand, wall,
# random object) and the pipeline routes it to "retake". Validated to cleanly
# separate real leaves (>0.77) from non-leaves (<0.39).
LEAF_GATE_TEMPLATE = "a close-up photograph of a {crop} plant leaf"
NEGATIVE_PROMPTS = [
    "a photograph of a computer keyboard",
    "a photograph of a human hand",
    "a photograph of an indoor object or furniture",
    "a random everyday object",
    "a photograph of electronics or plastic",
    "a plain colored shape or texture",
    "a photograph of the ground, floor, or wall",
]


@dataclass(frozen=True)
class CropMatch:
    """One ranked crop hypothesis from the verifier."""

    rank: int
    crop: str
    similarity: float  # post-softmax over the prompt set, in [0, 1]

    def to_json(self) -> dict[str, Any]:
        return {
            "rank": self.rank,
            "crop": self.crop,
            "similarity": round(self.similarity, 4),
        }


class CropVerifier:
    """Zero-shot crop classifier built on a pretrained CLIP model.

    Loaded once at FastAPI startup. Text embeddings for all crop prompts
    are computed eagerly so per-request work is just one image-encoder
    pass + a small matmul.
    """

    def __init__(
        self,
        crops: list[str],
        model_name: str = "openai/clip-vit-base-patch32",
        prompt_template: str = DEFAULT_PROMPT_TEMPLATE,
        device: str | None = None,
    ) -> None:
        if not crops:
            raise ValueError("crops list is empty")
        # Heavy imports deferred so importing this module is cheap.
        import torch
        from transformers import CLIPModel, CLIPProcessor

        self._torch = torch
        self._device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self._crops: list[str] = list(crops)
        self._prompts: list[str] = [prompt_template.format(crop=c) for c in self._crops]

        logger.info("Loading CLIP model %s on %s ...", model_name, self._device)
        self._processor = CLIPProcessor.from_pretrained(model_name)
        self._model = CLIPModel.from_pretrained(model_name).to(self._device).eval()

        # Pre-compute and L2-normalise text embeddings for all crops.
        with torch.inference_mode():
            text_inputs = self._processor(
                text=self._prompts,
                return_tensors="pt",
                padding=True,
            ).to(self._device)
            text_features = self._model.get_text_features(**text_inputs)
            text_features = text_features / text_features.norm(dim=-1, keepdim=True)
            self._text_embeds = text_features  # shape: (n_crops, embed_dim)

            # Open-set leaf gate: leaf prompts + negative prompts.
            self._n_leaf_gate = len(self._crops)
            gate_prompts = [LEAF_GATE_TEMPLATE.format(crop=c) for c in self._crops] + NEGATIVE_PROMPTS
            gate_inputs = self._processor(
                text=gate_prompts, return_tensors="pt", padding=True
            ).to(self._device)
            gate_features = self._model.get_text_features(**gate_inputs)
            gate_features = gate_features / gate_features.norm(dim=-1, keepdim=True)
            self._gate_embeds = gate_features  # (n_crops + n_negatives, embed_dim)
        logger.info(
            "CLIP ready (%d crop prompts + %d gate negatives, embed dim=%d)",
            len(self._crops), len(NEGATIVE_PROMPTS), int(self._text_embeds.shape[-1]),
        )

    @property
    def crops(self) -> list[str]:
        return list(self._crops)

    @property
    def model_id(self) -> str:
        return getattr(
            self._model.config, "_name_or_path", "openai/clip-vit-base-patch32"
        )

    def verify(
        self,
        image_rgb: NDArray[np.uint8],
        topk: int = 5,
    ) -> list[CropMatch]:
        """Return the top-k crops by CLIP image-to-prompt similarity."""
        if image_rgb.ndim != 3 or image_rgb.shape[-1] != 3:
            raise ValueError(
                f"Expected (H, W, 3) RGB uint8 image; got shape {image_rgb.shape}"
            )
        if not 1 <= topk <= len(self._crops):
            raise ValueError(f"topk must be in [1, {len(self._crops)}]; got {topk}")

        torch = self._torch
        with torch.inference_mode():
            inputs = self._processor(images=image_rgb, return_tensors="pt").to(self._device)
            image_features = self._model.get_image_features(**inputs)
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)
            # CLIP's logit_scale is exp(t); softmax(t * x @ y.T) is the
            # canonical zero-shot classification head.
            logit_scale = self._model.logit_scale.exp().clamp(max=100.0)
            logits = (logit_scale * image_features @ self._text_embeds.T).float()
            probs = logits.softmax(dim=-1)[0].cpu().numpy()  # (n_crops,)

        order = np.argsort(-probs)[:topk]
        return [
            CropMatch(rank=i + 1, crop=self._crops[int(idx)], similarity=float(probs[int(idx)]))
            for i, idx in enumerate(order)
        ]

    def leaf_probability(self, image_rgb: NDArray[np.uint8]) -> float:
        """Open-set gate: P(image is a crop leaf) in [0, 1].

        Softmaxes the image over [crop-leaf prompts + NEGATIVE_PROMPTS] and
        returns the probability mass on the leaf prompts. Low values mean the
        image is not a crop leaf (keyboard, hand, wall, random object).
        """
        if image_rgb.ndim != 3 or image_rgb.shape[-1] != 3:
            raise ValueError(f"Expected (H, W, 3) RGB uint8; got {image_rgb.shape}")
        torch = self._torch
        with torch.inference_mode():
            inputs = self._processor(images=image_rgb, return_tensors="pt").to(self._device)
            image_features = self._model.get_image_features(**inputs)
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)
            logit_scale = self._model.logit_scale.exp().clamp(max=100.0)
            logits = (logit_scale * image_features @ self._gate_embeds.T).float()
            probs = logits.softmax(dim=-1)[0].cpu().numpy()
        return float(probs[: self._n_leaf_gate].sum())

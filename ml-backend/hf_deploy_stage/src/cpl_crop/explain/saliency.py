"""SmoothGrad-style saliency explainer for the CPL SavedModel.

We can't get *intermediate* activations from the shipped SavedModel
(Keras 3 + the bundle's saved format don't expose layer outputs), so a
proper Grad-CAM++ that targets the last conv layer would require
rebuilding the architecture, and Keras 3's ``EfficientNetB2`` produces
numerically different outputs from the trained model even with identical
weights. To guarantee ``/predict`` and ``/explain`` always agree, we
instead use **input-space gradients** on the original SavedModel.

The method (Smilkov et al. 2017, "SmoothGrad"):

1. For ``N`` noisy versions of the input ``x_i = x + eps_i`` (Gaussian
   noise with std proportional to the input range), compute
   ``g_i = abs(d score_c / d x_i) * x_i``.
2. Average across samples: ``G = mean_i g_i``.
3. Aggregate the 3 colour channels (max gives sharper edges than sum):
   ``saliency = G.max(axis=-1)``.
4. Normalise to ``[0, 1]``.

For ``N=1`` and ``noise=0`` this degenerates into vanilla
``Gradient * Input`` saliency, which is the cheapest setting and good
enough for a live demo. Higher ``N`` (10-25) gives noticeably cleaner
maps at proportional cost.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np
import tensorflow as tf
from numpy.typing import NDArray

from cpl_crop.model_loader import ModelBundle

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SaliencyResult:
    """One run of the saliency explainer."""

    heatmap: NDArray[np.float32]  # shape (H, W), float32 in [0, 1]
    class_id: int
    class_score: float
    num_samples: int
    noise_level: float


class SmoothGradExplainer:
    """SmoothGrad saliency on top of a :class:`ModelBundle`.

    Stateless w.r.t. inputs; safe to share across requests.
    """

    def __init__(self, bundle: ModelBundle) -> None:
        self._bundle = bundle

    @property
    def num_classes(self) -> int:
        return self._bundle.num_classes

    def explain(
        self,
        x: NDArray[np.float32],
        class_id: int | None = None,
        num_samples: int = 8,
        noise_level: float = 0.10,
    ) -> SaliencyResult:
        """Compute a saliency heatmap for the given image.

        Args:
            x: ``(1, H, W, 3)`` float32 array, values in ``[0, 255]``
               (same contract as :class:`ModelBundle.predict`).
            class_id: which class to explain. ``None`` uses the
               predicted top-1.
            num_samples: number of noisy gradient samples to average.
               1 = plain Gradient*Input, 8-16 = SmoothGrad. Bigger ==
               cleaner but proportionally slower.
            noise_level: Gaussian noise std as a fraction of the input
               range (255). 0.0 disables noise (vanilla saliency).

        Returns:
            :class:`SaliencyResult` with heatmap shape ``(H, W)``.
        """
        if x.ndim != 4 or x.shape[0] != 1 or x.shape[-1] != 3:
            raise ValueError(f"Expected (1, H, W, 3) input; got {x.shape}")
        if num_samples < 1:
            raise ValueError(f"num_samples must be >= 1; got {num_samples}")
        if not 0.0 <= noise_level < 1.0:
            raise ValueError(f"noise_level must be in [0, 1); got {noise_level}")
        if x.dtype != np.float32:
            x = x.astype(np.float32, copy=False)

        infer = self._bundle.signature
        out_key = self._bundle.output_key

        # Identify the target class on the clean input first.
        if class_id is None:
            preds = infer(tf.constant(x))[out_key].numpy()
            class_id = int(preds[0].argmax())
            class_score = float(preds[0, class_id])
        else:
            if not 0 <= class_id < self._bundle.num_classes:
                raise ValueError(
                    f"class_id {class_id} out of range [0, {self._bundle.num_classes})"
                )
            preds = infer(tf.constant(x))[out_key].numpy()
            class_score = float(preds[0, class_id])

        # Stack N noisy variants into one batch so we pay one forward
        # + one backward pass instead of N.
        noise_std = noise_level * 255.0
        if num_samples == 1 and noise_level == 0.0:
            batch_np = x  # (1, H, W, 3)
        else:
            rng = np.random.default_rng(seed=None)
            tile = np.repeat(x, num_samples, axis=0)  # (N, H, W, 3)
            if noise_std > 0.0:
                noise_arr = rng.normal(loc=0.0, scale=noise_std, size=tile.shape)
                noise = np.asarray(noise_arr, dtype=np.float32)
                # Keep the noisy inputs in [0, 255] so the model sees realistic values.
                clipped = np.clip(tile + noise, 0.0, 255.0)
                batch_np = np.asarray(clipped, dtype=np.float32)
            else:
                batch_np = tile

        batch = tf.constant(batch_np)
        with tf.GradientTape() as tape:
            tape.watch(batch)
            out = infer(batch)[out_key]  # (N, num_classes)
            scores = out[:, class_id]  # (N,)

        # Per-sample gradient w.r.t. its own input (off-diagonal entries
        # of the Jacobian are zero because samples are independent in the
        # batch dimension).
        grads = tape.gradient(scores, batch)  # (N, H, W, 3)
        if grads is None:
            raise RuntimeError("Gradient is None — the SavedModel may not be differentiable.")

        grads_np = grads.numpy()
        sample_inputs = batch_np  # (N, H, W, 3)

        # Gradient * Input -> abs -> mean across samples -> max across channels.
        attribution = np.abs(grads_np * sample_inputs)  # (N, H, W, 3)
        attribution = attribution.mean(axis=0)  # (H, W, 3)
        saliency = attribution.max(axis=-1)  # (H, W)

        s_max = float(saliency.max())
        if s_max > 0.0:
            saliency = saliency / s_max
        else:
            logger.warning("Saliency is uniformly zero for class_id=%d", class_id)
            saliency = np.zeros_like(saliency, dtype=np.float32)

        return SaliencyResult(
            heatmap=saliency.astype(np.float32),
            class_id=int(class_id),
            class_score=class_score,
            num_samples=int(num_samples),
            noise_level=float(noise_level),
        )

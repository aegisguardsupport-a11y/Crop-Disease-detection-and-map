"""Lazy, thread-safe SavedModel loader.

The TF SavedModel takes several seconds to load and ~250 MB of RAM, so we
cache one bundle per process. A small lock guards the first-time load to
avoid two requests racing through ``tf.saved_model.load`` simultaneously.

Usage::

    from cpl_crop.config import get_settings
    from cpl_crop.model_loader import get_bundle

    bundle = get_bundle(get_settings().saved_model_dir)
    probs = bundle.predict(x)            # x: (B, H, W, 3) float32
"""

from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np
from numpy.typing import NDArray

if TYPE_CHECKING:  # pragma: no cover
    pass

logger = logging.getLogger(__name__)


class ModelBundle:
    """Wrapper around a loaded TF SavedModel.

    Exposes a single :meth:`predict` method that takes a 4-D float32 batch
    and returns the softmax probability matrix.
    """

    def __init__(self, saved_model_dir: Path) -> None:
        # Defer the heavy import so simply importing the module is cheap.
        import tensorflow as tf  # intentional lazy import — heavy module

        path = Path(saved_model_dir)
        if not path.exists():
            raise FileNotFoundError(f"SavedModel dir not found: {path}")

        logger.info("Loading SavedModel from %s", path)
        self._tf = tf
        self._model: Any = tf.saved_model.load(str(path))
        if "serving_default" not in self._model.signatures:
            raise RuntimeError(
                f"SavedModel at {path} has no 'serving_default' signature; "
                f"available: {list(self._model.signatures.keys())}"
            )
        self._infer = self._model.signatures["serving_default"]
        keys = list(self._infer.structured_outputs.keys())
        if not keys:
            raise RuntimeError(f"SavedModel at {path} has no structured outputs")
        self._output_key: str = keys[0]
        logger.info(
            "SavedModel ready (output_key=%s, num_classes=%d)",
            self._output_key,
            self.num_classes,
        )

    @property
    def num_classes(self) -> int:
        spec = self._infer.structured_outputs[self._output_key]
        return int(spec.shape[-1])

    @property
    def output_key(self) -> str:
        return self._output_key

    @property
    def signature(self) -> Any:
        """Underlying ConcreteFunction; lets explainers run the model inside a GradientTape."""
        return self._infer

    def predict(self, batch: NDArray[np.float32]) -> NDArray[np.float32]:
        """Run inference on a ``(B, H, W, 3)`` float32 array.

        Returns a ``(B, num_classes)`` softmax matrix.
        """
        if batch.ndim != 4:
            raise ValueError(f"Expected 4-D input (B,H,W,3); got shape {batch.shape}")
        if batch.shape[-1] != 3:
            raise ValueError(f"Expected 3 channels last; got shape {batch.shape}")
        if batch.dtype != np.float32:
            batch = batch.astype(np.float32, copy=False)

        out = self._infer(self._tf.constant(batch))[self._output_key].numpy()
        return np.asarray(out, dtype=np.float32)


# ---------------------------------------------------------------------------
# Process-wide singleton
# ---------------------------------------------------------------------------

_lock = threading.Lock()
_bundle: ModelBundle | None = None


def get_bundle(saved_model_dir: Path) -> ModelBundle:
    """Return a process-wide :class:`ModelBundle`, loading on first call."""
    global _bundle
    if _bundle is None:
        with _lock:
            if _bundle is None:
                _bundle = ModelBundle(saved_model_dir)
    return _bundle


def reset_bundle() -> None:
    """Drop the cached bundle. Intended for tests only."""
    global _bundle
    with _lock:
        _bundle = None

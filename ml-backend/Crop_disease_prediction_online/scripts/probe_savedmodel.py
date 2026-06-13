"""Investigate how to access intermediate layer activations on the bundle.

Tries Keras-style load first, falls back to inspecting the generic
``tf.saved_model.load`` object. Prints the last few conv layers — we
need the deepest one before global pooling for Grad-CAM++.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Quiet TF chatter
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

import tensorflow as tf  # noqa: E402

BUNDLE = Path(__file__).resolve().parents[1] / "exports" / "saved_model"


def try_keras_load() -> bool:
    print(f"\n--- Trying tf.keras.models.load_model({BUNDLE}) ---")
    try:
        model = tf.keras.models.load_model(BUNDLE)
    except Exception as e:
        print(f"FAILED: {type(e).__name__}: {e}")
        return False

    print(f"OK. type={type(model).__name__}")
    print(f"  inputs : {[i.shape for i in model.inputs]}")
    print(f"  outputs: {[o.shape for o in model.outputs]}")

    # Find the last Conv2D layer in the model (or nested inside a wrapped backbone)
    convs: list[tuple[str, tuple[int | None, ...]]] = []

    def walk(layer: tf.keras.layers.Layer, prefix: str = "") -> None:
        for sub in getattr(layer, "layers", []):
            full = f"{prefix}{sub.name}"
            if isinstance(sub, tf.keras.layers.Conv2D):
                try:
                    out_shape = tuple(sub.output.shape)
                except Exception:
                    out_shape = ()
                convs.append((full, out_shape))
            walk(sub, prefix=f"{full}/")

    walk(model)
    print(f"  Conv2D layers found: {len(convs)}")
    if convs:
        print("  Last 5:")
        for name, shape in convs[-5:]:
            print(f"    {name:<60s} -> {shape}")
    return True


def try_saved_model_load() -> None:
    print(f"\n--- tf.saved_model.load({BUNDLE}) ---")
    obj = tf.saved_model.load(str(BUNDLE))
    print(f"  type: {type(obj).__name__}")
    print(f"  signatures: {list(obj.signatures.keys())}")
    sig = obj.signatures["serving_default"]
    print(f"  serving_default inputs : {sig.structured_input_signature}")
    print(f"  serving_default outputs: {list(sig.structured_outputs.keys())}")
    # Look for nested attributes that might expose layers
    for attr in ("layers", "model", "signatures", "_layers"):
        val = getattr(obj, attr, None)
        if val is not None:
            print(f"  has .{attr}: {type(val).__name__}")


if __name__ == "__main__":
    ok = try_keras_load()
    if not ok:
        try_saved_model_load()
    sys.exit(0)

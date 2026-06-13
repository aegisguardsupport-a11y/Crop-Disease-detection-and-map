"""Find which layer first diverges between the SavedModel and our rebuild."""

from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

import numpy as np
import tensorflow as tf

from cpl_crop.explain.keras_loader import _build_architecture, _transfer_weights

BUNDLE = Path(__file__).resolve().parents[1] / "exports" / "saved_model"


def main() -> None:
    keras_model = _build_architecture()
    _transfer_weights(BUNDLE, keras_model)

    sm = tf.saved_model.load(str(BUNDLE))
    infer = sm.signatures["serving_default"]
    out_key = list(infer.structured_outputs.keys())[0]

    rng = np.random.default_rng(seed=0)
    probe = rng.uniform(0.0, 255.0, size=(1, 260, 260, 3)).astype(np.float32)

    sm_out = infer(tf.constant(probe))[out_key].numpy()[0]
    kr_out = keras_model(probe, training=False).numpy()[0]
    print(f"Final probs: max |diff| = {np.abs(sm_out - kr_out).max():.6e}")
    print(f"  sm top-3: {np.argsort(-sm_out)[:3]} -> {sm_out[np.argsort(-sm_out)[:3]]}")
    print(f"  kr top-3: {np.argsort(-kr_out)[:3]} -> {kr_out[np.argsort(-kr_out)[:3]]}")
    print()

    # Walk through Keras layers, extract intermediate outputs
    interesting = [
        "rescaling",
        "normalization",
        "stem_conv",
        "stem_bn",
        "stem_activation",
        "block1a_dwconv",
        "block1a_bn",
        "block1a_activation",
        "top_conv",
        "top_bn",
        "top_activation",
        "head_global_avg_pool",
        "head_batch_norm",
        "crop_disease_prediction",
    ]

    print("Layer-by-layer activation stats from rebuilt Keras model:")
    print(f"{'layer':<30s} {'shape':<25s} {'mean':>10s} {'std':>10s} {'min':>10s} {'max':>10s}")
    for name in interesting:
        try:
            layer = keras_model.get_layer(name)
        except ValueError:
            continue
        sub = tf.keras.Model(inputs=keras_model.inputs, outputs=layer.output)
        out = sub(probe, training=False).numpy()
        print(
            f"{name:<30s} {str(out.shape):<25s} "
            f"{out.mean():>10.4f} {out.std():>10.4f} "
            f"{out.min():>10.4f} {out.max():>10.4f}"
        )


if __name__ == "__main__":
    main()

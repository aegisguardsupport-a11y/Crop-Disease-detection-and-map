"""Predict crop+disease for a single image using the SavedModel bundle.

Requires only TensorFlow (any 2.x version >= 2.11) and Pillow. No
architecture code is needed -- the SavedModel is fully self-contained.

Usage:
    python predict_savedmodel.py path/to/leaf.jpg
    python predict_savedmodel.py path/to/leaf.jpg --topk 5
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
import numpy as np
import tensorflow as tf
from PIL import Image

HERE = Path(__file__).resolve().parent
SAVED_MODEL = HERE / "saved_model"
ID_TO_LABEL = HERE / "cpl_id_to_label.json"
PREP = HERE / "cpl_preprocessing_config.json"


def load_image(path: Path, size: tuple[int, int]) -> np.ndarray:
    with Image.open(path) as img:
        img = img.convert("RGB").resize(size, Image.BILINEAR)
        arr = np.asarray(img, dtype=np.float32)  # EfficientNet expects 0..255
    return arr[None, ...]  # (1, H, W, 3)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("image", type=Path)
    p.add_argument("--topk", type=int, default=3)
    p.add_argument("--json", action="store_true")
    args = p.parse_args()

    image_size = tuple(json.loads(PREP.read_text())["image_size"])
    id_to_label = {int(k): v for k, v in json.loads(ID_TO_LABEL.read_text()).items()}

    print(f"Loading SavedModel from {SAVED_MODEL} ...", file=sys.stderr)
    model = tf.saved_model.load(str(SAVED_MODEL))
    infer = model.signatures["serving_default"]
    out_key = list(infer.structured_outputs.keys())[0]

    x = load_image(args.image, image_size)
    probs = infer(tf.constant(x))[out_key].numpy()[0]  # (num_classes,)
    top = np.argsort(-probs)[: args.topk]
    preds = [{"rank": int(i + 1),
              "crop_disease_label": id_to_label[int(j)],
              "confidence": float(probs[j])} for i, j in enumerate(top)]

    if args.json:
        print(json.dumps({"image": str(args.image), "predictions": preds}, indent=2))
    else:
        print(f"Image: {args.image}")
        print(f"Top {args.topk} predictions:")
        for pred in preds:
            crop, _, disease = pred["crop_disease_label"].partition("::")
            print(f"  {pred['rank']}. {crop:20s} {disease:35s} {pred['confidence']*100:6.2f}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())

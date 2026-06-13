"""Predict crop+disease using the TFLite bundle.

Works on any platform that has the TFLite runtime (mobile, edge, plain
Python with `tflite_runtime` or full `tensorflow`). No SavedModel needed.

Usage:
    python predict_tflite.py path/to/leaf.jpg
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
import numpy as np
from PIL import Image

# Prefer the small tflite_runtime if available, fall back to tensorflow.
try:
    from tflite_runtime.interpreter import Interpreter
except ImportError:  # pragma: no cover
    from tensorflow.lite.python.interpreter import Interpreter

HERE = Path(__file__).resolve().parent
TFLITE = HERE / "cpl_crop_disease_finetuned.tflite"
ID_TO_LABEL = HERE / "cpl_id_to_label.json"
PREP = HERE / "cpl_preprocessing_config.json"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("image", type=Path)
    p.add_argument("--topk", type=int, default=3)
    p.add_argument("--json", action="store_true")
    args = p.parse_args()

    image_size = tuple(json.loads(PREP.read_text())["image_size"])
    id_to_label = {int(k): v for k, v in json.loads(ID_TO_LABEL.read_text()).items()}

    interp = Interpreter(model_path=str(TFLITE))
    interp.allocate_tensors()
    in_det = interp.get_input_details()[0]
    out_det = interp.get_output_details()[0]

    with Image.open(args.image) as img:
        img = img.convert("RGB").resize(image_size, Image.BILINEAR)
        arr = np.asarray(img, dtype=np.float32)[None, ...]

    interp.set_tensor(in_det["index"], arr)
    interp.invoke()
    probs = interp.get_tensor(out_det["index"])[0]
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

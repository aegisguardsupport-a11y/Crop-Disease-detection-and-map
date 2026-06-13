# CPL Crop Disease Detection — Portable Model Bundle

Self-contained inference bundle for the fine-tuned EfficientNetB2 crop-disease
classifier. Trained for 20 head-only epochs + 8 fine-tuning epochs on a
balanced 139-class plant-disease dataset.

**Test-set performance:**
- Top-1 accuracy: **93.61%**
- Top-3 accuracy: **99.35%**
- Macro F1: 0.9328  /  Weighted F1: 0.9359

## Contents

| Path | What it is | Use when |
|---|---|---|
| `saved_model/` | TF SavedModel directory | Python with TensorFlow, TF Serving, TF.js (after conversion) |
| `cpl_crop_disease_finetuned.tflite` | TFLite flatbuffer | Mobile (Android/iOS), edge devices, Raspberry Pi, anywhere with TFLite runtime |
| `cpl_id_to_label.json` | `{class_id: "crop::disease"}` | Required by both predict scripts |
| `cpl_preprocessing_config.json` | input image size + batch size | Required by both predict scripts |
| `predict_savedmodel.py` | minimal SavedModel CLI | reference Python implementation |
| `predict_tflite.py` | minimal TFLite CLI | reference mobile/edge implementation |
| `README.md` | this file | |

## Input contract

- **Image format:** any common format readable by Pillow (JPEG, PNG, BMP, etc.). For WebP, decode with Pillow before passing to the model.
- **Resize:** bilinear to **260 × 260** RGB.
- **Pixel range:** float32 in **0..255** (NOT 0..1). The EfficientNetB2 backbone has a built-in normalisation layer that expects raw pixel values.
- **Batch dimension:** add a leading axis → shape `(1, 260, 260, 3)`.

## Output contract

- **Tensor:** shape `(batch, 139)`, dtype float32.
- **Values:** softmax probabilities summing to 1.0 across the 139 classes.
- **Class names:** look up via `cpl_id_to_label.json`. Format is `crop::disease`, e.g. `tomato::Late_blight`. The class id is the column index.

## Quick start — Python with TensorFlow

```bash
pip install tensorflow>=2.11 pillow numpy
python predict_savedmodel.py path/to/leaf.jpg --topk 3
```

Sample output:
```
Image: leaf.jpg
Top 3 predictions:
  1. tomato               Late_blight                          92.71%
  2. potato               Late_blight                           4.53%
  3. tomato               Early_blight                          1.18%
```

In your own code:
```python
import json, numpy as np, tensorflow as tf
from PIL import Image

model = tf.saved_model.load("./saved_model")
infer = model.signatures["serving_default"]
labels = {int(k): v for k, v in json.load(open("cpl_id_to_label.json")).items()}

img = Image.open("leaf.jpg").convert("RGB").resize((260, 260), Image.BILINEAR)
x = np.asarray(img, dtype=np.float32)[None, ...]
probs = list(infer(tf.constant(x)).values())[0].numpy()[0]
top1 = labels[int(probs.argmax())]
print(f"{top1}: {probs.max()*100:.1f}%")
```

## Quick start — TFLite (mobile / edge / lightweight)

```bash
pip install tflite-runtime pillow numpy   # or: pip install tensorflow
python predict_tflite.py path/to/leaf.jpg
```

The TFLite file is ~32 MB. For mobile distribution, run `tflite_convert
--optimizations=DEFAULT` on it to apply weight quantisation (~8 MB).

## Quick start — TF Serving

```bash
docker run -p 8501:8501 \
  -v "$PWD/saved_model:/models/cpl_crop_disease/1" \
  -e MODEL_NAME=cpl_crop_disease \
  tensorflow/serving:2.11.0
```

Then POST a JSON request:
```bash
# img_b64 is your image, base64-encoded after preprocessing to (260,260,3) float32
curl -X POST http://localhost:8501/v1/models/cpl_crop_disease:predict \
  -d '{"instances": [<your-260x260x3-array>]}'
```

## Quick start — TensorFlow.js (browser)

```bash
pip install tensorflowjs
tensorflowjs_converter --input_format=tf_saved_model \
  ./saved_model ./tfjs_model
```

Load in the browser:
```js
const model = await tf.loadGraphModel('tfjs_model/model.json');
const input = tf.browser.fromPixels(imgElement)
                .resizeBilinear([260, 260])
                .expandDims(0)
                .toFloat();         // 0..255 already
const probs = model.predict(input).dataSync();
```

## Limitations

This is a closed-world classifier over 139 specific (crop, disease) pairs.
It will confidently mis-label any input outside that set — non-plant
images, unfamiliar crops, or extreme lighting. Use the predicted
probability as a soft confidence indicator only; it is not calibrated.

For full training details and per-class accuracy, see the `MODEL_CARD.md`
in the project repository.

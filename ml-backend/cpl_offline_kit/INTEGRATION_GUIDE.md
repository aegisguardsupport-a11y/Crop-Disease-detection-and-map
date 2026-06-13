# 🛠️ Integration Guide — CPL Crop Doctor Offline Kit (React Native + Expo)

For the app developer. Follow top to bottom. Estimated time: **1–2 days** for
classifier-only mode. Every code block is copy-paste ready.

---

## 0. Prerequisites & the ONE big gotcha

- Node 18+, an Expo app (SDK 50+), Xcode (iOS) and/or Android Studio.
- **⚠️ You CANNOT use Expo Go.** On-device ML needs a native module Expo Go
  doesn't ship. You must use an **Expo Development Build** (one-time setup,
  step 1). You keep writing normal Expo code — you just install your own build.

---

## 1. Switch to an Expo Development Build

```bash
npx expo install expo-dev-client
# build & install the dev client on a device/emulator:
npx expo run:android      # or: npx expo run:ios
# (or use EAS: eas build --profile development --platform android)
```
From now on, run `npx expo start --dev-client` instead of plain `expo start`.

---

## 2. Install dependencies

```bash
npx expo install react-native-fast-tflite     # runs the .tflite model
npx expo install expo-image-manipulator       # resize images to 224x224
npx expo install expo-image-picker            # or expo-camera, to get a photo
```

Add the TFLite asset type to **metro.config.js** so the model bundles:
```js
// metro.config.js
const { getDefaultConfig } = require("expo/metro-config");
const config = getDefaultConfig(__dirname);
config.resolver.assetExts.push("tflite");
module.exports = config;
```

---

## 3. Drop the kit into your project

Copy the kit's folders into your app, e.g.:
```
your-app/
├── assets/models/cpl_student_int8.tflite     ← from kit models/
├── src/cpl/                                   ← from kit pipeline/ (the .ts files)
├── src/cpl/labels.json                        ← from kit models/labels.json
└── src/cpl/advisories.json                    ← from kit data/advisories.json
```
Delete `classifier.example.ts` after you copy its logic into your own
`classifier.ts` (it references a relative model path you'll adjust).

---

## 4. Load the model once (app start)

```ts
// src/cpl/classifier.ts
import { loadTensorflowModel, type TensorflowModel } from "react-native-fast-tflite";

let model: TensorflowModel | null = null;

export async function loadClassifier() {
  if (!model) {
    model = await loadTensorflowModel(require("../../assets/models/cpl_student_int8.tflite"));
  }
}

export function classify(rgbFloat224: Float32Array): Float32Array {
  if (!model) throw new Error("loadClassifier() not called");
  const out = model.runSync([rgbFloat224]);
  return out[0] as Float32Array;   // 72 softmax probabilities
}
```
Call `loadClassifier()` in a top-level `useEffect` so it's ready before the
first photo.

---

## 5. Photo → model input (resize to 224×224, get pixels)

The model wants **224×224, RGB, float 0..255** (see `models/preprocessing.json`).
Resize with `expo-image-manipulator`, then read pixels. Easiest reliable way to
get raw pixels is a tiny helper using `expo-image-manipulator` + base64 + a JPEG
decoder, OR the `vision-camera` frame processor if you use that. Minimal example
using a decoded RGBA buffer:

```ts
import * as ImageManipulator from "expo-image-manipulator";

// returns 224x224 RGBA Uint8Array — implementation depends on your pixel source.
// With expo-image-manipulator you resize; to read raw pixels many teams use
// `@shopify/react-native-skia` (Skia Image -> readPixels) which is robust:
//   const img = Skia.Image.MakeImageFromEncoded(data);
//   const pixels = img.readPixels(); // RGBA Uint8Array
```

Then convert RGBA → the model's RGB float input:
```ts
function rgbaToInput(rgba: Uint8Array): Float32Array {
  const out = new Float32Array(224 * 224 * 3);
  for (let i = 0; i < 224 * 224; i++) {
    out[i*3] = rgba[i*4]; out[i*3+1] = rgba[i*4+1]; out[i*3+2] = rgba[i*4+2];
  }
  return out;   // 0..255 floats, NO division by 255
}
```
> 📌 **Do NOT normalize/÷255.** MobileNetV3 normalizes internally. Feed raw 0..255.

---

## 5b. ⚠️ Segmentation — REQUIRED before the classifier

The classifier only works on a **background-removed leaf**. Feeding a raw photo
gives garbage. So step 1 of every prediction is leaf segmentation.

**Model:** `models/leaf_segmenter.onnx` (YOLOv8-seg, input **640×640 RGB 0..1**).
**Run it with `onnxruntime-react-native`:**
```bash
npx expo install onnxruntime-react-native
```
```ts
import { InferenceSession, Tensor } from "onnxruntime-react-native";
const seg = await InferenceSession.create(require("../models/leaf_segmenter.onnx"));
// input: Float32 [1,3,640,640], RGB, normalized 0..1
const out = await seg.run({ images: new Tensor("float32", chw640, [1,3,640,640]) });
```
**Then (standard YOLOv8-seg post-processing):**
1. Decode detections; take the **highest-confidence** leaf box + its mask
   coefficients, combine with the mask prototypes → a binary leaf mask.
2. Crop the original image to the mask's bounding box (+5% padding).
3. Set non-leaf pixels to **black (0,0,0)**.
4. Resize that to **224×224** → this is the input to `classify()`.

> This YOLOv8-seg mask decoding is the hardest part of going offline. Reference
> implementations: search "YOLOv8 segmentation postprocess onnxruntime js".
> If this is too much for your timeline, use the **hybrid** approach (online API
> does segmentation server-side) and treat full-offline as a later milestone.

If the segmenter finds **no leaf**, route to "retake" (set `leafDetected: false`
in `runDiagnosis`).

---

## 6. Run the full diagnosis (one call)

```ts
import { runDiagnosis } from "./cpl";              // the kit's index.ts
import labels from "./cpl/labels.json";
import advisories from "./cpl/advisories.json";
import { classify } from "./cpl/classifier";

async function diagnose(rgba224: Uint8Array, rgbaFull: Uint8Array, fullW: number, fullH: number) {
  // 1) run the model
  const probs = classify(rgbaToInput(rgba224));

  // 2) one call does quality + confidence + routing + advisory lookup
  const result = runDiagnosis({
    classifierProbs: probs,
    labels,
    advisories,
    // for the quality gate, pass the ORIGINAL photo pixels + dims:
    rgba: rgbaFull,
    imgWidth: fullW,
    imgHeight: fullH,
    origMinSide: Math.min(fullW, fullH),
    topK: 3,
    // (classifier-only mode: omit segConfidence/leafAreaScore — auto-handled)
  });

  return result;   // PipelineResult — see pipeline/types.ts
}
```

---

## 7. Render the result

```tsx
// result.decision: "high_confidence" | "expert_review" | "retake"
// result.confidence: 0..1   result.predictions[0]: top guess
// result.advisory: { summary, symptoms, organic_treatment, chemical_treatment, prevention, safety_note }

if (result.decision === "retake") {
  return <RetakeCard message={result.retakeGuidance} />;
}
const top = result.predictions[0];
return (
  <DiagnosisCard
    crop={top.crop}
    disease={top.disease}
    confidence={Math.round(result.confidence * 100)}
    needsReview={result.decision === "expert_review"}   // show a "verify" badge
    advisory={result.advisory}
  />
);
```
**Always show the confidence number and the expert-review badge** — that honesty
is a feature, not a bug.

---

## 8. Test checklist (before you ship)
- [ ] A clear in-crop leaf (tomato/rice/cotton) → `high_confidence` + advice
- [ ] A blurry/dark photo → `retake` with guidance
- [ ] A non-leaf photo (a hand, a wall) → low confidence → `retake`/`expert_review`
- [ ] A crop you don't cover → low confidence (won't crash)
- [ ] Airplane mode ON the whole time → everything still works

---

## Troubleshooting
| Symptom | Fix |
|---|---|
| `loadTensorflowModel` fails / asset not found | Confirm `metro.config.js` has `assetExts.push("tflite")` and the `require()` path is correct; restart Metro with `-c` |
| Wrong/garbage predictions | You normalized pixels — **remove the ÷255**; feed 0..255 floats. Confirm RGB order (not BGR) and 224×224 size. |
| Model returns ≠72 values | You loaded the wrong file; use `cpl_student_int8.tflite` |
| Crash on int8 model | Swap to `cpl_student_float.tflite` (some older devices dislike int8) |
| Everything routes to "retake" | Your quality thresholds are too strict, or you passed normalized pixels to the quality check too |
| Build fails on Expo Go | You must use a **dev build** (step 1), not Expo Go |

---

## What you do NOT need to build
The kit already provides, **type-checked**: the confidence math, the decision
router, the quality gate, the advisory lookup, and all types. You only write:
camera capture → resize → pixels → `classify()` → `runDiagnosis()` → UI.

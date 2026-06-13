/**
 * CPL Crop Doctor — Classifier inference EXAMPLE (the one native piece).
 *
 * This shows how to run the bundled TFLite classifier on-device with
 * `react-native-fast-tflite`. Adapt the image-to-tensor step to whatever
 * camera/image library you use. Everything AFTER this (confidence, router,
 * advisory) is handled by runDiagnosis() — see index.ts.
 *
 * Install (in your Expo dev build, NOT Expo Go):
 *   npx expo install react-native-fast-tflite
 *   npx expo install expo-image-manipulator   // resize images
 *
 * Model contract (see models/preprocessing.json):
 *   input : 1 x 224 x 224 x 3, float32, RGB, pixel range 0..255 (NO /255)
 *   output: 1 x 72 float32 softmax probabilities
 */

import { loadTensorflowModel, type TensorflowModel } from "react-native-fast-tflite";

const INPUT_SIZE = 224;
const NUM_CLASSES = 72;

let model: TensorflowModel | null = null;

/** Load once at app start (e.g. in a useEffect). */
export async function loadClassifier(): Promise<void> {
  if (model) return;
  // bundle the file under assets/ and reference it via require()
  // NOTE: use the FLOAT model — it is meaningfully more accurate than int8
  // on this task, and barely larger (~1.1 MB). Only switch to int8 if you
  // need an NN-accelerator path and have verified accuracy is acceptable.
  model = await loadTensorflowModel(require("../models/cpl_student_float.tflite"));
}

/**
 * @param rgb  a Float32Array of length 224*224*3, RGB, values 0..255,
 *             row-major (you produce this from the resized camera image).
 * @returns    72-length softmax probability array.
 */
export async function classify(rgb: Float32Array): Promise<Float32Array> {
  if (!model) throw new Error("Call loadClassifier() first.");
  if (rgb.length !== INPUT_SIZE * INPUT_SIZE * 3) {
    throw new Error(`Expected ${INPUT_SIZE * INPUT_SIZE * 3} values, got ${rgb.length}`);
  }
  // fast-tflite runs synchronously; output[0] is the probabilities tensor
  const outputs = model.runSync([rgb]);
  const probs = outputs[0] as Float32Array;
  if (probs.length !== NUM_CLASSES) {
    throw new Error(`Model returned ${probs.length} classes, expected ${NUM_CLASSES}`);
  }
  return probs;
}

/* ---------------------------------------------------------------------------
 * Example: turn a resized 224x224 RGBA buffer into the RGB float input.
 * (Drop the alpha channel; keep 0..255 floats.)
 * ------------------------------------------------------------------------- */
export function rgbaToModelInput(rgba: Uint8Array | Uint8ClampedArray): Float32Array {
  const out = new Float32Array(INPUT_SIZE * INPUT_SIZE * 3);
  for (let i = 0; i < INPUT_SIZE * INPUT_SIZE; i++) {
    out[i * 3] = rgba[i * 4];        // R
    out[i * 3 + 1] = rgba[i * 4 + 1]; // G
    out[i * 3 + 2] = rgba[i * 4 + 2]; // B
  }
  return out;
}

/**
 * Offline AI inference — on-device crop-disease classifier.
 *
 * Runs the bundled CPL MobileNetV3-Small TFLite model fully offline via
 * react-native-fast-tflite (JSI / Nitro, GPU-accelerated where available).
 * No network calls happen in this path.
 *
 *   ┌──────────────┐                ┌────────────────────┐
 *   │ report-flow  │ —— online ──▶ │ Cloudinary + server │
 *   │ (cloud first)│                │ AI                  │
 *   └──────┬───────┘                └────────────────────┘
 *          │
 *          └── fallback ─▶ ┌────────────────────────────┐
 *                          │ offlineAiClient (this file) │
 *                          │   - bundled .tflite model   │
 *                          │   - 224x224 float32 input   │
 *                          │   - 139 crop::disease classes│
 *                          └────────────────────────────┘
 *
 * Model contract (see assets/models/):
 *   input  : (1, 224, 224, 3) float32, pixels in [0, 255], bilinear resize
 *   output : (1, 139) float32 softmax over crop::disease classes
 *
 * The native module is loaded lazily and defensively: if the binary was built
 * without react-native-fast-tflite (e.g. plain Expo Go), or the model asset is
 * missing, `isAvailable()` resolves false and `analyze()` returns a typed
 * failure instead of crashing the upload flow.
 */

import {
  loadTensorflowModel,
  type TensorflowModel,
  type TensorflowModelDelegate,
} from 'react-native-fast-tflite';

import type { Severity } from '@/features/upload-report/types';
import { logger } from '@/utils/logger';

import { resolveDiseaseInfo } from './disease-info';
import { prettyDisease, topKPredictions, type Prediction } from './labels';
import { preprocessImage } from './preprocess';

export interface OfflineAnalysisRequest {
  /** Local file URI of the (compressed) image. */
  localImageUri: string;
  cropType: string;
  notes?: string;
}

export interface OfflineAnalysisSuccess {
  ok: true;
  disease: string;
  confidence: number;
  severity: Severity;
  recommendations: string[];
  /** Always true — distinguishes from server-side results downstream. */
  fromOnDevice: true;
  /** Top-k predictions, useful for a low-confidence candidate picker. */
  candidates?: { disease: string; confidence: number }[];
}

export interface OfflineAnalysisFailure {
  ok: false;
  error: string;
  errorCode: 'UNAVAILABLE' | 'MODEL_NOT_LOADED' | 'INFERENCE_FAILED';
}

export type OfflineAnalysisResult = OfflineAnalysisSuccess | OfflineAnalysisFailure;

export interface OfflineAiClient {
  readonly name: string;
  /** Returns true when the model is bundled and ready to run. */
  isAvailable(): Promise<boolean>;
  /** Runs the model on a local image. */
  analyze(request: OfflineAnalysisRequest): Promise<OfflineAnalysisResult>;
}

// The bundled model asset. Metro resolves this to an on-device file path
// because `tflite` is registered in metro.config.js `resolver.assetExts`.
// A relative path is used (not the `@/assets` alias) because Metro's asset
// resolver does not reliably apply tsconfig path aliases to binary requires.
// eslint-disable-next-line @typescript-eslint/no-require-imports
const MODEL_ASSET = require('../../../assets/models/cpl_crop_disease.tflite');

// CoreML on iOS, Android GPU where available; falls back to CPU automatically.
const DELEGATES: TensorflowModelDelegate[] = ['core-ml', 'android-gpu'];

let modelPromise: Promise<TensorflowModel> | null = null;
let modelLoadFailed = false;

/**
 * Lazily load + cache the TFLite model. Tries the hardware delegates first and
 * transparently falls back to CPU-only if delegate setup fails.
 */
function loadModel(): Promise<TensorflowModel> {
  if (!modelPromise) {
    modelPromise = (async () => {
      try {
        return await loadTensorflowModel(MODEL_ASSET, DELEGATES);
      } catch (delegateErr) {
        logger.warn(
          '[offline-ai] delegate load failed, retrying CPU-only',
          delegateErr,
        );
        return loadTensorflowModel(MODEL_ASSET, []);
      }
    })().catch((err) => {
      // Reset so a later attempt can retry; mark failed for isAvailable().
      modelPromise = null;
      modelLoadFailed = true;
      throw err;
    });
  }
  return modelPromise;
}

export const offlineAiClient: OfflineAiClient = {
  name: 'offline-tflite',

  async isAvailable(): Promise<boolean> {
    if (modelLoadFailed) return false;
    try {
      await loadModel();
      return true;
    } catch (err) {
      logger.warn('[offline-ai] model unavailable', err);
      return false;
    }
  },

  async analyze(request: OfflineAnalysisRequest): Promise<OfflineAnalysisResult> {
    let model: TensorflowModel;
    try {
      model = await loadModel();
    } catch (err) {
      return {
        ok: false,
        error: `On-device model failed to load: ${String(err)}`,
        errorCode: 'MODEL_NOT_LOADED',
      };
    }

    try {
      const { data } = await preprocessImage(request.localImageUri);

      const t0 = Date.now();
      // v3 API: run takes an array of ArrayBuffers, returns ArrayBuffer[].
      const outputs = await model.run([data.buffer as ArrayBuffer]);
      const probs = new Float32Array(outputs[0] as ArrayBuffer);
      logger.info(`[offline-ai] inference ${Date.now() - t0}ms`);

      const predictions = topKPredictions(probs, 3);
      if (predictions.length === 0) {
        return {
          ok: false,
          error: 'Model returned no predictions.',
          errorCode: 'INFERENCE_FAILED',
        };
      }

      const top = predictions[0];
      const info = resolveDiseaseInfo(top.disease);

      return {
        ok: true,
        disease: formatPrediction(top),
        confidence: top.confidence,
        severity: info.severity,
        recommendations: info.recommendations,
        fromOnDevice: true,
        candidates: predictions.map((p) => ({
          disease: formatPrediction(p),
          confidence: p.confidence,
        })),
      };
    } catch (err) {
      logger.warn('[offline-ai] inference failed', err);
      return {
        ok: false,
        error: `On-device inference failed: ${String(err)}`,
        errorCode: 'INFERENCE_FAILED',
      };
    }
  },
};

/** "tomato::Tomato___Late_blight" -> "Tomato — Late blight". */
function formatPrediction(p: Prediction): string {
  const crop = p.crop.charAt(0).toUpperCase() + p.crop.slice(1);
  const disease = prettyDisease(p.crop, p.disease);
  return `${crop} \u2014 ${disease}`;
}

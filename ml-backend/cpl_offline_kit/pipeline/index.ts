/**
 * CPL Crop Doctor — Offline Pipeline Orchestrator
 *
 * One function, `runDiagnosis()`, wires together the parts this kit provides
 * (quality gate → confidence engine → decision router → advisory lookup).
 *
 * YOU provide the ONE native piece: the classifier softmax output from the
 * TFLite model (see classifier.example.ts / INTEGRATION_GUIDE.md). Everything
 * else here is pure TypeScript with no native dependencies.
 *
 * Two modes:
 *   • classifier-only (Phase 1): omit the segmentation fields. Faster, simpler,
 *     slightly lower accuracy on cluttered photos.
 *   • full pipeline (Phase 2): also pass segConfidence / leafAreaScore / etc.
 */

import { assessImageQuality, rgbaToGrayscale } from "./quality";
import { fuseConfidence } from "./confidence";
import { route, ROUTER_DEFAULTS, type RouterConfig } from "./router";
import type {
  Advisory, PipelineResult, Prediction, QualityReport, RetakeReason,
} from "./types";

export interface DiagnoseInput {
  /** 72-length softmax probabilities from the TFLite classifier (REQUIRED) */
  classifierProbs: number[] | Float32Array;
  /** index -> "crop::disease", from models/labels.json (REQUIRED) */
  labels: Record<string, string> | string[];
  /** label -> Advisory, from data/advisories.json (REQUIRED) */
  advisories: Record<string, Advisory>;

  /** Pre-computed quality report (run assessImageQuality yourself), OR pass
   *  rgba+dims below and we compute it. */
  quality?: QualityReport;
  rgba?: Uint8Array | Uint8ClampedArray;
  imgWidth?: number;
  imgHeight?: number;
  origMinSide?: number;

  /** topK predictions to return (default 3) */
  topK?: number;
  routerConfig?: RouterConfig;

  // ---- full-pipeline (Phase 2) extras — omit for classifier-only ----
  segConfidence?: number;
  leafAreaScore?: number;
  leafDetected?: boolean;
  leafAreaFailure?: RetakeReason | null;
}

function labelAt(labels: Record<string, string> | string[], i: number): string {
  return Array.isArray(labels) ? labels[i] : labels[String(i)];
}

export function runDiagnosis(input: DiagnoseInput): PipelineResult {
  const t0 = Date.now();
  const probs = Array.from(input.classifierProbs);
  const topK = input.topK ?? 3;

  // ---- quality (use provided, or compute from rgba) ----
  let quality = input.quality;
  if (!quality) {
    if (!input.rgba || !input.imgWidth || !input.imgHeight) {
      throw new Error("Provide `quality`, or `rgba`+`imgWidth`+`imgHeight` to compute it.");
    }
    const gray = rgbaToGrayscale(input.rgba, input.imgWidth, input.imgHeight);
    quality = assessImageQuality(gray, input.imgWidth, input.imgHeight);
  }

  // ---- top-k predictions ----
  const order = probs
    .map((p, i) => ({ p, i }))
    .sort((a, b) => b.p - a.p);
  const predictions: Prediction[] = order.slice(0, topK).map((o, rank) => {
    const label = labelAt(input.labels, o.i);
    const [crop, disease] = label.split("::");
    return { rank: rank + 1, label, crop, disease, confidence: o.p };
  });

  const top1 = order[0]?.p ?? 0;
  const top2 = order[1]?.p ?? 0;
  const gap = Math.max(0, top1 - top2);

  // ---- confidence (renormalizes if seg fields are absent) ----
  const signals = fuseConfidence({
    qualityScore: quality.score,
    classifierTop1: top1,
    predictionGap: gap,
    segConfidence: input.segConfidence,
    leafAreaScore: input.leafAreaScore,
  });

  // ---- decision (top1 passed for the open-set guard) ----
  const routing = route(signals.final, top1, {
    quality,
    leafDetected: input.leafDetected,
    leafAreaFailure: input.leafAreaFailure ?? null,
  }, input.routerConfig ?? ROUTER_DEFAULTS);

  // ---- advisory (only when we actually diagnose) ----
  const top = predictions[0];
  const advisory: Advisory | null =
    routing.decision === "retake" ? null : (input.advisories[top.label] ?? null);

  return {
    decision: routing.decision,
    confidence: signals.final,
    predictions,
    quality,
    segmentationConfidence: input.segConfidence ?? 0,
    leafAreaRatio: input.leafAreaScore ?? 0,
    retakeReason: routing.reason,
    retakeGuidance: routing.guidance,
    advisory,
    latencyMs: Date.now() - t0,
  };
}

// Re-export the building blocks so the app can use them individually if needed.
export * from "./types";
export { assessImageQuality, rgbaToGrayscale } from "./quality";
export { fuseConfidence, CONFIDENCE_WEIGHTS } from "./confidence";
export { route, ROUTER_DEFAULTS } from "./router";

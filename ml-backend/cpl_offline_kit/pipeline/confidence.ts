/**
 * CPL Crop Doctor — Offline Confidence Engine
 *
 * Direct TypeScript port of: cpl_crop.validation.confidence.py
 *
 * Fuses the available signals into one calibrated confidence in [0, 1].
 * IMPORTANT: it RENORMALIZES over only the signals available for the mode
 * you run. In classifier-only mode (no segmenter) the seg + area weights are
 * dropped and the score is NOT diluted — this is the exact server bug fix.
 *
 * Pure math, no dependencies.
 */

import type { ConfidenceSignals, ConfidenceWeights } from "./types";

// Relative weights (same proportions as the server config). They do not need
// to sum to 1 — fuseConfidence renormalizes over whatever signals are present.
export const CONFIDENCE_WEIGHTS: ConfidenceWeights = {
  quality: 0.1,
  seg: 0.12,
  area: 0.08,
  top1: 0.4,
  gap: 0.15,
};

const clamp01 = (x: number): number => Math.max(0, Math.min(1, x));

export interface FuseInput {
  qualityScore: number;     // 0..1
  classifierTop1: number;   // 0..1
  predictionGap: number;    // 0..1 (top1 - top2)
  /** segmenter confidence 0..1 — pass undefined in classifier-only mode */
  segConfidence?: number;
  /** leaf-area score 0..1 — pass undefined in classifier-only mode */
  leafAreaScore?: number;
}

/**
 * Compute the fused confidence and the per-signal breakdown.
 * Omit segConfidence/leafAreaScore to run classifier-only (Phase 1).
 */
export function fuseConfidence(input: FuseInput): ConfidenceSignals {
  const gapAmplified = clamp01(input.predictionGap * 4); // >=0.25 margin => full credit

  // (name, weight, value) for every signal we actually have
  const present: Array<[keyof ConfidenceWeights, number]> = [
    ["top1", clamp01(input.classifierTop1)],
    ["gap", gapAmplified],
    ["quality", clamp01(input.qualityScore)],
  ];
  if (input.segConfidence !== undefined) present.push(["seg", clamp01(input.segConfidence)]);
  if (input.leafAreaScore !== undefined) present.push(["area", clamp01(input.leafAreaScore)]);

  const wsum = present.reduce((s, [name]) => s + CONFIDENCE_WEIGHTS[name], 0) || 1;
  const usedWeights: ConfidenceWeights = { quality: 0, seg: 0, area: 0, top1: 0, gap: 0 };
  let final = 0;
  for (const [name, value] of present) {
    const nw = CONFIDENCE_WEIGHTS[name] / wsum;
    usedWeights[name] = nw;
    final += nw * value;
  }

  return {
    qualityScore: clamp01(input.qualityScore),
    segConfidence: input.segConfidence ?? 0,
    leafAreaScore: input.leafAreaScore ?? 0,
    classifierTop1: clamp01(input.classifierTop1),
    predictionGap: clamp01(input.predictionGap),
    weights: usedWeights,
    final: clamp01(final),
  };
}

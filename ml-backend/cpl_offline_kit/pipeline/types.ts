/**
 * CPL Crop Doctor — Offline Pipeline Type Definitions
 *
 * Shared types used across the quality, confidence, and router modules.
 * These are direct TypeScript equivalents of the Python dataclasses in
 * cpl_crop.validation.*.
 */

// ─── Quality Assessment ──────────────────────────────────────────────

export interface QualityReport {
  ok: boolean;
  score: number; // 0..1, where 1 = all checks pass cleanly
  resolution: [number, number]; // [height, width]
  blur: number; // Laplacian variance — higher = sharper
  brightness: number; // 0..255 mean grayscale
  contrast: number; // std of grayscale pixels
  failures: string[];
}

// ─── Confidence Engine ───────────────────────────────────────────────

export interface ConfidenceWeights {
  quality: number;
  seg: number;
  area: number;
  top1: number;
  gap: number;
}

export interface ConfidenceSignals {
  qualityScore: number;
  segConfidence: number;
  leafAreaScore: number;
  classifierTop1: number;
  predictionGap: number;
  weights: ConfidenceWeights;
  final: number;
}

// ─── Decision Router ─────────────────────────────────────────────────

export type Decision = "high_confidence" | "expert_review" | "retake";

export type RetakeReason =
  | "image_too_blurry"
  | "image_too_dark"
  | "image_too_bright"
  | "image_low_contrast"
  | "image_resolution_too_low"
  | "no_leaf_detected"
  | "leaf_too_small_in_frame"
  | "leaf_too_large_or_no_background"
  | "classifier_low_confidence"
  | "unrecognized_or_not_a_crop_leaf"
  | "uncertain_prediction";

export interface RoutingResult {
  decision: Decision;
  reason: RetakeReason | null;
  guidance: string | null;
}

// ─── Classification ──────────────────────────────────────────────────

export interface Prediction {
  rank: number;
  label: string; // "crop::disease"
  crop: string;
  disease: string;
  confidence: number;
}

// ─── Advisory ────────────────────────────────────────────────────────

export interface Advisory {
  crop: string;
  disease: string;
  summary: string;
  symptoms: string[];
  organic_treatment: string[];
  chemical_treatment: string[];
  prevention: string[];
  safety_note: string;
}

// ─── Full Pipeline Result ────────────────────────────────────────────

export interface PipelineResult {
  decision: Decision;
  confidence: number;
  predictions: Prediction[];
  quality: QualityReport;
  segmentationConfidence: number;
  leafAreaRatio: number;
  retakeReason: RetakeReason | null;
  retakeGuidance: string | null;
  advisory: Advisory | null;
  latencyMs: number;
}

/**
 * CPL Crop Doctor — Offline Decision Router
 *
 * Direct TypeScript port of: cpl_crop.validation.router.py
 *
 * Turns the fused confidence + hard input gates into one of three honest
 * outcomes. Hard gates (bad photo / no leaf) always win, so a junk image is
 * told to "retake" no matter how confident the classifier is.
 */

import type { Decision, QualityReport, RetakeReason, RoutingResult } from "./types";

export interface RouterConfig {
  highThreshold: number;   // server default 0.78
  mediumThreshold: number; // server default 0.55
  /** Open-set guard: top-1 below this -> forced retake regardless of fused
   *  score. Stops sharp non-leaf photos (keyboard, hand) being mis-diagnosed. */
  minTop1: number;         // server default 0.45
}

export const ROUTER_DEFAULTS: RouterConfig = { highThreshold: 0.78, mediumThreshold: 0.55, minTop1: 0.45 };

export interface RouterGates {
  quality: QualityReport;
  /** undefined in classifier-only mode (no segmenter) */
  leafDetected?: boolean;
  leafAreaFailure?: RetakeReason | null; // e.g. "leaf_too_small_in_frame"
}

// map a quality failure string (from quality.ts) to a typed RetakeReason
function qualityToReason(failures: string[]): RetakeReason | null {
  const f = failures[0] ?? "";
  if (f.startsWith("blurry")) return "image_too_blurry";
  if (f.startsWith("too_dark")) return "image_too_dark";
  if (f.startsWith("too_bright")) return "image_too_bright";
  if (f.startsWith("low_contrast")) return "image_low_contrast";
  if (f.startsWith("resolution")) return "image_resolution_too_low";
  return null;
}

const GUIDANCE: Record<RetakeReason, string> = {
  image_too_blurry: "Photo is blurry. Hold steady and tap to focus on the leaf.",
  image_too_dark: "Too dark. Move to better light or turn on the flash.",
  image_too_bright: "Overexposed. Avoid direct glare; shade the leaf slightly.",
  image_low_contrast: "Low contrast. Place the leaf against a plainer background.",
  image_resolution_too_low: "Image is too small. Move closer and retake.",
  no_leaf_detected: "No leaf found. Fill the frame with a single leaf.",
  leaf_too_small_in_frame: "Leaf is too small. Move closer to the leaf.",
  leaf_too_large_or_no_background: "Leaf fills the whole frame. Step back a little.",
  classifier_low_confidence: "Not confident. Retake a clearer, closer photo.",
  unrecognized_or_not_a_crop_leaf: "We couldn't recognize a known crop leaf or disease in this photo. Please photograph a single, clearly-visible crop leaf.",
  uncertain_prediction: "Diagnosis uncertain — have an expert confirm before treating.",
};

export function route(
  fusedConfidence: number,
  classifierTop1: number,
  gates: RouterGates,
  cfg: RouterConfig = ROUTER_DEFAULTS,
): RoutingResult {
  const mk = (decision: Decision, reason: RetakeReason | null): RoutingResult => ({
    decision, reason, guidance: reason ? GUIDANCE[reason] : null,
  });

  // ---- hard gates first ----
  if (!gates.quality.ok) {
    return mk("retake", qualityToReason(gates.quality.failures) ?? "image_too_blurry");
  }
  if (gates.leafDetected === false) {
    return mk("retake", "no_leaf_detected");
  }
  if (gates.leafAreaFailure) {
    return mk("retake", gates.leafAreaFailure);
  }

  // ---- open-set guard: weak top-1 => the model doesn't recognize the image ----
  if (classifierTop1 < cfg.minTop1) {
    return mk("retake", "unrecognized_or_not_a_crop_leaf");
  }

  // ---- confidence-based routing ----
  if (fusedConfidence >= cfg.highThreshold) return mk("high_confidence", null);
  if (fusedConfidence >= cfg.mediumThreshold) return mk("expert_review", "uncertain_prediction");
  return mk("retake", "classifier_low_confidence");
}

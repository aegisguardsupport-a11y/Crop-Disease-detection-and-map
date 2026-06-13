/**
 * CPL Crop Doctor — Offline Image Quality Assessment
 *
 * Direct TypeScript port of: cpl_crop.validation.quality.py
 *
 * Runs cheap, deterministic checks on an image BEFORE expensive
 * segmentation + classification. Catches blurry / dark / overexposed /
 * tiny images so we reject them with helpful retake guidance.
 *
 * USAGE IN EXPO:
 *   This module operates on raw RGBA pixel data from the camera.
 *   Use expo-image-manipulator or react-native-image-crop-picker to
 *   get image pixel data, then convert to a grayscale Uint8Array.
 *
 *   Alternatively, if you're using a canvas (e.g., react-native-canvas),
 *   you can call getImageData() and pass the RGBA data directly.
 */

import type { QualityReport } from "./types";

// ─── Default Thresholds (matching Python config.py) ──────────────────

export const QUALITY_DEFAULTS = {
  minResolution: 224,
  minBlur: 100.0,
  minBrightness: 40.0,
  maxBrightness: 220.0,
  minContrast: 25.0,
} as const;

// ─── Helper: clamp a value to [0, 1] with linear ramp ────────────────

function normalizeToUnit(value: number, lo: number, hi: number): number {
  if (hi <= lo) return value >= hi ? 1.0 : 0.0;
  return Math.max(0.0, Math.min(1.0, (value - lo) / (hi - lo)));
}

// ─── Core: Convert RGBA pixel buffer to grayscale Uint8Array ─────────

/**
 * Convert an RGBA Uint8Array (from canvas getImageData or camera)
 * to a single-channel grayscale Uint8Array.
 *
 * Formula: gray = 0.299*R + 0.587*G + 0.114*B (standard luminance)
 */
export function rgbaToGrayscale(
  rgba: Uint8Array | Uint8ClampedArray,
  width: number,
  height: number
): Uint8Array {
  const gray = new Uint8Array(width * height);
  for (let i = 0; i < width * height; i++) {
    const r = rgba[i * 4];
    const g = rgba[i * 4 + 1];
    const b = rgba[i * 4 + 2];
    gray[i] = Math.round(0.299 * r + 0.587 * g + 0.114 * b);
  }
  return gray;
}

// ─── Blur: Laplacian variance approximation ──────────────────────────

/**
 * Compute an approximate Laplacian variance (sharpness metric).
 *
 * This is the variance of a 3x3 Laplacian kernel convolved over the
 * grayscale image. Higher values = sharper image. The Python version
 * uses cv2.Laplacian(gray, cv2.CV_64F).var() — this is equivalent.
 *
 * Kernel:  [0  1  0]
 *          [1 -4  1]
 *          [0  1  0]
 */
function laplacianVariance(
  gray: Uint8Array,
  width: number,
  height: number
): number {
  let sum = 0;
  let sumSq = 0;
  let count = 0;

  // Skip 1px border (kernel needs neighbors)
  for (let y = 1; y < height - 1; y++) {
    for (let x = 1; x < width - 1; x++) {
      const idx = y * width + x;
      const lap =
        gray[idx - width] + // top
        gray[idx - 1] + // left
        -4 * gray[idx] + // center
        gray[idx + 1] + // right
        gray[idx + width]; // bottom

      sum += lap;
      sumSq += lap * lap;
      count++;
    }
  }

  if (count === 0) return 0;
  const mean = sum / count;
  return sumSq / count - mean * mean; // variance
}

// ─── Main: Assess image quality ──────────────────────────────────────

export interface QualityOptions {
  minResolution?: number;
  minBlur?: number;
  minBrightness?: number;
  maxBrightness?: number;
  minContrast?: number;
}

/**
 * Compute a quality report for an image.
 *
 * @param gray - Grayscale Uint8Array (use rgbaToGrayscale to convert)
 * @param width - Image width in pixels
 * @param height - Image height in pixels
 * @param opts - Optional threshold overrides
 * @returns QualityReport with ok, score, and individual metrics
 */
export function assessImageQuality(
  gray: Uint8Array,
  width: number,
  height: number,
  opts?: QualityOptions
): QualityReport {
  const minRes = opts?.minResolution ?? QUALITY_DEFAULTS.minResolution;
  const minBlur = opts?.minBlur ?? QUALITY_DEFAULTS.minBlur;
  const minBright = opts?.minBrightness ?? QUALITY_DEFAULTS.minBrightness;
  const maxBright = opts?.maxBrightness ?? QUALITY_DEFAULTS.maxBrightness;
  const minContrast = opts?.minContrast ?? QUALITY_DEFAULTS.minContrast;

  // --- Compute metrics ---

  const blur = laplacianVariance(gray, width, height);

  // Brightness = mean grayscale value
  let brightnessSum = 0;
  for (let i = 0; i < gray.length; i++) brightnessSum += gray[i];
  const brightness = brightnessSum / gray.length;

  // Contrast = standard deviation of grayscale values
  let varianceSum = 0;
  for (let i = 0; i < gray.length; i++) {
    const diff = gray[i] - brightness;
    varianceSum += diff * diff;
  }
  const contrast = Math.sqrt(varianceSum / gray.length);

  // --- Hard fail checks ---

  const failures: string[] = [];
  if (Math.min(height, width) < minRes) {
    failures.push(`resolution_below_${minRes}`);
  }
  if (blur < minBlur) {
    failures.push(`blurry_below_${minBlur}`);
  }
  if (brightness < minBright) {
    failures.push(`too_dark_below_${minBright}`);
  } else if (brightness > maxBright) {
    failures.push(`too_bright_above_${maxBright}`);
  }
  if (contrast < minContrast) {
    failures.push(`low_contrast_below_${minContrast}`);
  }

  // --- Soft sub-scores in [0, 1] ---

  const resScore = normalizeToUnit(Math.min(height, width), minRes, minRes * 2);
  const blurScore = normalizeToUnit(blur, minBlur, minBlur * 4);

  let brightScore: number;
  if (brightness >= minBright && brightness <= maxBright) {
    brightScore = 1.0;
  } else if (brightness < minBright) {
    brightScore = normalizeToUnit(brightness, 0, minBright);
  } else {
    brightScore = normalizeToUnit(255 - brightness, 0, 255 - maxBright);
  }

  const contrastScore = normalizeToUnit(contrast, minContrast, minContrast * 2);

  const score = (resScore + blurScore + brightScore + contrastScore) / 4;

  return {
    ok: failures.length === 0,
    score,
    resolution: [height, width],
    blur,
    brightness,
    contrast,
    failures,
  };
}

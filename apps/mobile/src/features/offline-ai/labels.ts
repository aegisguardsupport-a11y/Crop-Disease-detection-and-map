/**
 * Label decoder for the CPL crop-disease classifier.
 *
 * The model outputs a 139-vector of softmax probabilities. Index -> label is
 * defined in assets/models/cpl_id_to_label.json, where each label has the
 * format `crop::disease`, e.g. `tomato::Tomato___Late_blight`.
 */

import labelsRaw from '@/assets/models/cpl_id_to_label.json';

/** Ordered array where index === class id. */
const labelsByIndex: string[] = (() => {
  const entries = Object.entries(labelsRaw as Record<string, string>);
  const arr = new Array<string>(entries.length);
  for (const [k, v] of entries) {
    arr[Number(k)] = v;
  }
  return arr;
})();

export const NUM_CLASSES = labelsByIndex.length;

export interface Prediction {
  /** 1-based rank within the top-k list. */
  rank: number;
  /** Raw model class id (argmax index). */
  classId: number;
  /** Full `crop::disease` label. */
  label: string;
  /** Crop portion of the label, e.g. `tomato`. */
  crop: string;
  /** Disease portion of the label, e.g. `Late_blight`. */
  disease: string;
  /** Softmax probability in [0, 1]. */
  confidence: number;
}

/**
 * Convert a 139-vector of softmax probabilities into the top-k named
 * predictions, sorted by descending confidence. `topK` defaults to 3.
 */
export function topKPredictions(
  probs: Float32Array | number[],
  topK = 3,
): Prediction[] {
  const indexed: [number, number][] = [];
  for (let i = 0; i < probs.length; i++) {
    indexed.push([i, probs[i] as number]);
  }
  indexed.sort((a, b) => b[1] - a[1]);

  return indexed.slice(0, topK).map(([classId, confidence], i) => {
    const label = labelsByIndex[classId] ?? `class_${classId}`;
    const [crop, disease] = label.split('::');
    return {
      rank: i + 1,
      classId,
      label,
      crop: crop ?? label,
      disease: disease ?? '',
      confidence,
    };
  });
}

/**
 * True when a label represents a healthy / disease-free leaf. The dataset is
 * inconsistent across crops ("Healthy", "healthy", "Healthy Leaf",
 * "Maize healthy", "Fresh Leaf", "Soybean Healthy", etc.), so we match
 * loosely on the disease segment.
 */
export function isHealthyLabel(diseaseSegment: string): boolean {
  const d = diseaseSegment.toLowerCase();
  return (
    d.includes('healthy') ||
    d.includes('fresh leaf') ||
    d.includes('fresh_leaf') ||
    d === 'onion1'
  );
}

/**
 * Humanise a raw disease segment for display:
 *   `Tomato___Late_blight`         -> `Late blight`
 *   `early_leaf_spot_1`            -> `Early leaf spot`
 *   `Maize leaf blight`            -> `Maize leaf blight`
 */
export function prettyDisease(crop: string, diseaseSegment: string): string {
  let d = diseaseSegment;

  // Drop a leading "Crop___" prefix some labels carry (e.g. tomato classes).
  d = d.replace(/^[A-Za-z]+___/, '');
  // Underscores / triple-underscores -> spaces.
  d = d.replace(/_+/g, ' ');
  // Trailing dataset artefacts like a stray "t" or "-D"/"-P" suffixes.
  d = d.replace(/-[A-Z]$/, '').trim();
  // Collapse whitespace.
  d = d.replace(/\s+/g, ' ').trim();

  if (!d) return 'Unknown condition';
  // Capitalise first letter only; keep the rest as-authored.
  return d.charAt(0).toUpperCase() + d.slice(1);
}

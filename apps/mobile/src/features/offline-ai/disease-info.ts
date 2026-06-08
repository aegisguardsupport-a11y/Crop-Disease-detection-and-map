/**
 * Curated disease knowledge base for the offline classifier.
 *
 * The TFLite model only outputs a `crop::disease` label + confidence. The app's
 * OfflineAnalysisSuccess contract additionally needs a `severity`
 * (LOW | MEDIUM | HIGH) and a list of `recommendations`. This module maps every
 * one of the 139 trained classes to that information.
 *
 * Rather than 139 hand-copied blocks, classes are matched by an ordered list of
 * keyword rules grouped by disease type (blight, rust, mildew, virus, rot,
 * etc.). Each rule carries real agronomic guidance. The first matching rule
 * wins; a generic fallback guarantees every label resolves to something useful.
 * Healthy / fresh-leaf classes are handled explicitly first.
 *
 * Guidance is general best-practice and intentionally conservative — it is a
 * starting point for the grower, not a substitute for local extension advice.
 */

import type { Severity } from '@/features/upload-report/types';

import { isHealthyLabel } from './labels';

export interface DiseaseInfo {
  severity: Severity;
  recommendations: string[];
}

interface DiseaseRule {
  /** Matches against the lowercased disease segment of the label. */
  test: RegExp;
  severity: Severity;
  recommendations: string[];
}

const HEALTHY_INFO: DiseaseInfo = {
  severity: 'LOW',
  recommendations: [
    'No disease detected — the leaf looks healthy.',
    'Keep monitoring weekly for early signs of spots, wilting or discoloration.',
    'Maintain balanced irrigation and nutrition to keep the crop resilient.',
  ],
};

const GENERIC_INFO: DiseaseInfo = {
  severity: 'MEDIUM',
  recommendations: [
    'Isolate affected plants and remove badly damaged leaves to slow spread.',
    'Avoid overhead watering; keep foliage dry and improve air circulation.',
    'Consult a local agronomist to confirm and choose a suitable treatment.',
    'Re-scan in a few days to track whether the condition is worsening.',
  ],
};

/**
 * Ordered rules — more specific / more severe conditions are listed first so
 * they win over broad matches (e.g. "late blight" before generic "blight").
 */
const RULES: DiseaseRule[] = [
  // ---- Viruses & virus-like (systemic, usually incurable, vector-driven) ----
  {
    test: /lethal necrosis/,
    severity: 'HIGH',
    recommendations: [
      'Maize Lethal Necrosis spreads fast and has no cure — act immediately.',
      'Uproot and destroy infected plants; do not compost them.',
      'Control insect vectors (thrips, leaf beetles) that transmit the viruses.',
      'Rotate out of maize for a season and plant certified clean seed.',
    ],
  },
  {
    test: /mosaic|mossaic|virus|curl virus|curly virus|leaf curl|yellow leaf curl|streak|virosis|viral|sterilic|crinckle|crinkle|mottle/,
    severity: 'HIGH',
    recommendations: [
      'Likely a viral infection — there is no curative spray once a plant is infected.',
      'Remove and destroy infected plants to protect the rest of the field.',
      'Control the insect vectors (whiteflies, aphids, thrips) that spread it.',
      'Use virus-resistant varieties and certified clean seed next season.',
      'Disinfect tools and wash hands between plants to avoid mechanical spread.',
    ],
  },

  // ---- Bacterial diseases (blights, spots, rots, wilts) ----
  {
    test: /bacterial wilt|bacterial_wilt/,
    severity: 'HIGH',
    recommendations: [
      'Bacterial wilt is soil-borne and aggressive — infected plants rarely recover.',
      'Remove and destroy wilted plants along with nearby soil.',
      'Avoid waterlogging and improve drainage; the bacteria thrive in wet soil.',
      'Rotate with non-host crops (cereals) for 2–3 seasons.',
    ],
  },
  {
    test: /bacterial soft rot|soft rot/,
    severity: 'HIGH',
    recommendations: [
      'Bacterial soft rot spreads quickly in warm, humid, wet conditions.',
      'Remove and destroy affected plants and avoid handling them when wet.',
      'Improve drainage and air flow; avoid injuries that let bacteria enter.',
      'Apply copper-based bactericides as a preventive on healthy plants.',
    ],
  },
  {
    test: /black rot/,
    severity: 'HIGH',
    recommendations: [
      'Black rot is a serious bacterial disease of brassicas.',
      'Remove infected leaves; destroy crop debris after harvest.',
      'Use hot-water-treated or certified disease-free seed.',
      'Rotate away from brassicas for at least two years.',
    ],
  },
  {
    test: /bacterial (leaf )?blight|bacterialblight|xanthomonas/,
    severity: 'HIGH',
    recommendations: [
      'Bacterial leaf blight is favoured by warm, humid weather and standing water.',
      'Drain excess water and avoid excessive nitrogen fertiliser.',
      'Remove infected debris; use resistant varieties where available.',
      'Copper-based sprays can limit spread but will not cure infected tissue.',
    ],
  },
  {
    test: /bacterial spot|bacterial_spot/,
    severity: 'MEDIUM',
    recommendations: [
      'Bacterial spot spreads via water splash and contaminated tools.',
      'Avoid overhead irrigation; work plants only when foliage is dry.',
      'Remove affected leaves and apply copper-based sprays preventively.',
      'Use certified disease-free seed and rotate crops.',
    ],
  },

  // ---- Blights (oomycete / fungal) ----
  {
    test: /late blight|late_blight/,
    severity: 'HIGH',
    recommendations: [
      'Late blight can destroy a crop within days in cool, wet weather — act now.',
      'Remove and destroy infected foliage immediately; do not compost.',
      'Apply a protectant fungicide (e.g. mancozeb) or systemic where permitted.',
      'Avoid overhead watering and increase spacing for airflow.',
      'Scout daily during humid spells; the disease moves extremely fast.',
    ],
  },
  {
    test: /early blight|early_blight/,
    severity: 'MEDIUM',
    recommendations: [
      'Early blight starts on older, lower leaves as concentric "target" rings.',
      'Remove affected lower leaves and mulch to stop soil splash.',
      'Apply a protectant fungicide on a 7–10 day schedule in wet weather.',
      'Maintain balanced nutrition; stressed plants are more susceptible.',
    ],
  },
  {
    test: /blast/,
    severity: 'HIGH',
    recommendations: [
      'Blast is a destructive fungal disease favoured by humidity and dense canopies.',
      'Avoid excess nitrogen and overly dense planting.',
      'Apply recommended fungicides at early symptom onset.',
      'Use resistant varieties and treated seed next season.',
    ],
  },
  {
    test: /leaf blight|leafblight|stemphylium|botrytis leaf blight/,
    severity: 'MEDIUM',
    recommendations: [
      'Leaf blight is driven by prolonged leaf wetness and high humidity.',
      'Improve air circulation and avoid overhead watering late in the day.',
      'Remove infected leaves and apply a protectant fungicide if it spreads.',
      'Rotate crops and clear infected residue after harvest.',
    ],
  },

  // ---- Rusts ----
  {
    test: /rust|ferrugen/,
    severity: 'MEDIUM',
    recommendations: [
      'Rust appears as orange/brown pustules on leaves and spreads by wind.',
      'Remove heavily infected leaves and avoid working in the field when wet.',
      'Apply a labelled fungicide early if pustules are spreading.',
      'Plant rust-tolerant varieties and avoid dense, humid canopies.',
    ],
  },

  // ---- Mildews ----
  {
    test: /downy mildew|downy|downey/,
    severity: 'MEDIUM',
    recommendations: [
      'Downy mildew thrives in cool, humid, wet conditions.',
      'Improve airflow and drainage; avoid overhead irrigation.',
      'Remove infected leaves and apply a protectant fungicide preventively.',
      'Space plants adequately and avoid working among wet foliage.',
    ],
  },
  {
    test: /powdery mildew|powdery_mildew/,
    severity: 'MEDIUM',
    recommendations: [
      'Powdery mildew shows as white powder on leaf surfaces.',
      'Improve air circulation and avoid excess nitrogen.',
      'Apply sulphur or a labelled fungicide at first signs.',
      'Remove and destroy badly affected leaves.',
    ],
  },

  // ---- Molds & rots ----
  {
    test: /white mold|gray mold|grey mold|cereal grain mold|grain mold/,
    severity: 'MEDIUM',
    recommendations: [
      'Mold is favoured by dense, humid canopies and poor air movement.',
      'Increase spacing and ventilation; avoid overhead watering.',
      'Remove and destroy affected tissue promptly.',
      'Apply a labelled fungicide if the problem expands.',
    ],
  },
  {
    test: /sett rot|southern blight|foot rot|footrot|red rot/,
    severity: 'HIGH',
    recommendations: [
      'This rot is soil/residue-borne and can kill plants outright.',
      'Remove and destroy affected plants and surrounding debris.',
      'Improve drainage and avoid mechanical injury to stems and setts.',
      'Use disease-free planting material and rotate crops.',
    ],
  },

  // ---- Smuts ----
  {
    test: /smut/,
    severity: 'MEDIUM',
    recommendations: [
      'Smut produces dark spore masses and is mainly seed/soil-borne.',
      'Remove and destroy smutted heads/plants before spores release.',
      'Use certified, fungicide-treated seed.',
      'Rotate crops and avoid carrying spores on tools or equipment.',
    ],
  },
  {
    test: /anthracnose/,
    severity: 'MEDIUM',
    recommendations: [
      'Anthracnose causes sunken dark lesions and spreads in wet weather.',
      'Remove infected plant parts and avoid overhead irrigation.',
      'Apply a protectant fungicide during prolonged wet periods.',
      'Use clean seed and rotate away from host crops.',
    ],
  },

  // ---- Leaf spots (broad fungal group) ----
  {
    test: /target spot|target_spot/,
    severity: 'MEDIUM',
    recommendations: [
      'Target spot forms concentric lesions and thrives in humid conditions.',
      'Remove affected leaves and improve canopy airflow.',
      'Apply a protectant fungicide if lesions are spreading.',
      'Avoid overhead watering and clear infected debris.',
    ],
  },
  {
    test: /leaf mold|leaf_mold/,
    severity: 'MEDIUM',
    recommendations: [
      'Leaf mold thrives in high humidity, especially in enclosed spaces.',
      'Lower humidity and increase ventilation around plants.',
      'Remove infected leaves and avoid wetting foliage.',
      'Use resistant varieties and apply fungicide if it persists.',
    ],
  },
  {
    test: /leaf spot|leaf_spot|leafspot|cercospora|alternaria|septoria|phyllosticta|brown spot|brownspot|black spot|black_spot|blackpoint|black point|white spot|purple blotch|purple tinge|banded chlorosis|leaf scars/,
    severity: 'MEDIUM',
    recommendations: [
      'Leaf-spot fungi spread by water splash and persist on crop debris.',
      'Remove spotted leaves and avoid overhead irrigation.',
      'Mulch to reduce soil splash and improve air circulation.',
      'Apply a protectant fungicide if spots multiply rapidly.',
      'Rotate crops and clear residue after harvest.',
    ],
  },

  // ---- Wilts (fungal/soil-borne) ----
  {
    test: /fusarium|wilt|sudden death/,
    severity: 'HIGH',
    recommendations: [
      'Wilt diseases are soil-borne and block the plant\u2019s water transport.',
      'Remove and destroy wilted plants; avoid spreading infested soil.',
      'Improve drainage and avoid overwatering.',
      'Rotate with non-host crops and use resistant varieties.',
    ],
  },

  // ---- Insect pests & pest damage ----
  {
    test: /spider mite|two-spotted/,
    severity: 'MEDIUM',
    recommendations: [
      'Spider mites cause fine stippling and webbing, worsening in hot, dry weather.',
      'Spray plants with water to dislodge mites and raise humidity.',
      'Introduce predatory mites or apply a labelled miticide if severe.',
      'Avoid broad-spectrum insecticides that kill natural predators.',
    ],
  },
  {
    test: /armyworm|grasshoper|grasshopper|leaf beetle|caterpillar|leaf_webber|leaf webber|leaf hopper|jassid|insect pest|insect_pest/,
    severity: 'MEDIUM',
    recommendations: [
      'This is insect-pest damage rather than a pathogen.',
      'Scout and hand-pick larvae where practical; destroy egg masses.',
      'Use pheromone traps and encourage natural predators.',
      'Apply a targeted, labelled insecticide only if thresholds are exceeded.',
    ],
  },

  // ---- Nutritional / abiotic / physiological ----
  {
    test: /nutrition deficiency|nutrition_deficiency|nutritional/,
    severity: 'LOW',
    recommendations: [
      'Symptoms point to a nutrient deficiency, not an infectious disease.',
      'Check leaf color pattern to identify the likely nutrient (N, K, Mg, Fe).',
      'Do a soil/leaf test and correct with the appropriate fertiliser.',
      'Maintain proper soil pH so nutrients stay available to roots.',
    ],
  },
  {
    test: /herbicide|growth damage|variegation|redding|dried leaves|yellow leaf|grassy shoot|small leaf|seedling/,
    severity: 'LOW',
    recommendations: [
      'This looks like abiotic or physiological stress rather than a pathogen.',
      'Review recent herbicide use, watering and temperature swings.',
      'Correct irrigation and nutrition; remove badly damaged leaves.',
      'Monitor new growth — healthy new leaves indicate recovery.',
    ],
  },
  {
    test: /pokkah boeng/,
    severity: 'MEDIUM',
    recommendations: [
      'Pokkah Boeng is a fungal disorder of sugarcane favoured by humid weather.',
      'Remove affected top leaves and improve field drainage.',
      'Avoid excess nitrogen and use clean planting material.',
      'Apply a labelled fungicide if young plants are heavily affected.',
    ],
  },
  {
    test: /bulb_blight|bulb blight/,
    severity: 'MEDIUM',
    recommendations: [
      'Bulb blight rots storage tissue and spreads in wet, poorly drained soil.',
      'Improve drainage and avoid bruising bulbs at harvest.',
      'Remove and destroy affected bulbs; cure properly before storage.',
      'Rotate crops and use clean seed/sets.',
    ],
  },
];

/**
 * Resolve severity + recommendations for a classified label.
 *
 * @param diseaseSegment the disease portion of the `crop::disease` label.
 */
export function resolveDiseaseInfo(diseaseSegment: string): DiseaseInfo {
  if (isHealthyLabel(diseaseSegment)) {
    return HEALTHY_INFO;
  }

  // Normalize so underscore-separated labels (e.g. `Bacterial_leaf_blight`,
  // `Tomato___Late_blight`) match the same space-based keyword rules.
  const normalized = diseaseSegment
    .toLowerCase()
    .replace(/_+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();

  for (const rule of RULES) {
    if (rule.test.test(normalized)) {
      return { severity: rule.severity, recommendations: rule.recommendations };
    }
  }

  return GENERIC_INFO;
}

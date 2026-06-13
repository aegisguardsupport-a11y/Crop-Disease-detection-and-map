"""Load, audit, and chunk crop-disease RAG source files.

The uploaded RAG data is mostly JSON arrays, but a few files are wrapped in
Markdown fences or have small JSON punctuation issues. The parser below extracts
balanced JSON objects so ingestion remains robust without manually editing the
source material.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from cpl_crop.labels import split_label

CROP_FILENAMES: dict[str, str] = {
    "bhindi": "Bhindi.txt",
    "blackgram": "Blackgram.txt",
    "brinjal": "Brinjal.txt",
    "cabbage": "Cabbage.txt",
    "cauliflower": "Cauliflower.txt",
    "chilli": "Chilli.txt",
    "cotton": "Cotton.txt",
    "cowpea": "Cowpea.txt",
    "groundnut": "Groundnut.txt",
    "maize": "Maize.txt",
    "onion": "Onion.txt",
    "pigeonpea": "Pigeonpea.txt",
    "ragi": "Ragi.txt",
    "rice": "Rice.txt",
    "sorghum": "Sorghum.txt",
    "soyabean": "Soyabean.txt",
    "sugarcane": "Sugarcane.txt",
    "sunflower": "Sunflower.txt",
    "tomato": "Tomato.txt",
    "wheat": "Wheat.txt",
}

MANUAL_ALIASES: dict[str, str] = {
    "blackgram::Leaf_Crinckle": "Leaf Crinkle",
    "brinjal::Insect Pest Disease": "Insect Pest Disease (Shoot and Fruit Borer)",
    "cotton::Leaf Hopper Jassids": "Leaf Hopper Jassids",
    "cotton::Leaf Redding": "Leaf Redding",
    "cowpea::Bacterial_wilt": "Bacterial wilt",
    "groundnut::early_leaf_spot_1": "early_leaf_spot_1",
    "groundnut::early_rust_1": "early_rust_1",
    "groundnut::late_leaf_spot_1": "late_leaf_spot_1",
    "groundnut::nutrition_deficiency_1": "nutrition_deficiency_1",
    "groundnut::rust_1": "rust_1",
    "maize::Maize grasshoper": "Maize Grasshopper Infestation",
    "onion::Alternaria_D": "Purple Blotch",
    "onion::Botrytis Leaf Blight": "Botrytis Leaf Blight",
    "onion::Bulb_blight-D": "Bulb Blight",
    "onion::Caterpillar-P": "Caterpillar",
    "onion::Fusarium-D": "Fusarium",
    "onion::Virosis-D": "Virosis",
    "onion::stemphylium Leaf Blight": "Stemphylium Leaf Blight",
    "pigeonpea::Leaf_Spot": "Cercospora Leaf Spot",
    "pigeonpea::Leaf_webber": "Leaf Webber",
    "pigeonpea::Sterilic_mosaic": "Sterility Mosaic",
    "ragi::downy": "Downy Mildew / Green Ear",
    "ragi::mottle": "Ragi Mottle / Mosaic Virus",
    "ragi::seedling": "Seedling Blight / Foot Rot",
    "ragi::smut": "Ragi Smut",
    "ragi::wilt": "Fusarium Wilt / Sclerotium Wilt",
    "rice::Bacterial_leaf_blight": "Bacterial Leaf Blight",
    "rice::Bacterialblight": "Bacterial Leaf Blight",
    "rice::Brown_spot": "Brown Spot",
    "rice::Brownspot": "Brown Spot",
    "rice::Leaf_smut": "Leaf Smut",
    "rice::Leafsmut": "Leaf Smut",
    "sorghum::AnthracnoseRed Rot": "Anthracnose and Red Rot",
    "sorghum::Cereal Grain molds (White Fungi)t": (
        "Cereal Grain Molds (White and Pink Fungi)"
    ),
    "sorghum::Covered Kernel smut (sori creamy)t": (
        "Covered Kernel Smut (Sori Creamy / Grain Smut)"
    ),
    "sorghum::Head Smut (White Spreaded)t": (
        "Head Smut (White Spreaded / Panicle Destruction)"
    ),
    "sorghum::loose smut (black)": "Loose Smut (Black / Spontaneous Rupture)",
    "soyabean::Mossaic Virus": "Soybean Mosaic Virus",
    "soyabean::Sudden Death Syndrone": "Sudden Death Syndrome",
    "soyabean::Yellow Mosaic": "Yellow Mosaic Virus",
    "soyabean::bacterial_blight": "Bacterial Blight",
    "soyabean::brown_spot": "Septoria Brown Spot",
    "soyabean::septoria": "Septoria Brown Spot",
    "sugarcane::Pokkah Boeng": "Pokkah Boeng",
    "sugarcane::smut": "Sugarcane Smut",
    "sugarcane::Grassy shoot": "Grassy Shoot Disease",
    "sunflower::Gray mold": "Gray Mold (Head Rot phase)",
    "tomato::Tomato___Bacterial_spot": "Bacterial Spot",
    "tomato::Tomato___Early_blight": "Early Blight",
    "tomato::Tomato___Late_blight": "Late Blight",
    "tomato::Tomato___Leaf_Mold": "Leaf Mold",
    "tomato::Tomato___Septoria_leaf_spot": "Septoria Leaf Spot",
    "tomato::Tomato___Spider_mites Two-spotted_spider_mite": (
        "Two-Spotted Spider Mite"
    ),
    "tomato::Tomato___Target_Spot": "Target Spot",
    "tomato::Tomato___Tomato_Yellow_Leaf_Curl_Virus": (
        "Tomato Yellow Leaf Curl Virus"
    ),
    "tomato::Tomato___Tomato_mosaic_virus": "Tomato Mosaic Virus",
    "wheat::BlackPoint": "Black Point / Kernel Smudge",
    "wheat::FusariumFootRot": "Fusarium Foot Rot and Crown Rot",
    "wheat::LeafBlight": "Leaf Blight / Helminthosporium Leaf Blight Complex",
    "wheat::WheatBlast": "Wheat Blast",
}

HEALTHY_MARKERS = ("healthy", "fresh leaf", "healthy leaf", "healthy leaves")


@dataclass(frozen=True)
class RagRecord:
    """One disease fact sheet extracted from a crop source file."""

    source_file: str
    record_id: str
    crop: str
    crop_display: str
    disease_name: str
    disease_key: str
    data: dict[str, Any]


@dataclass(frozen=True)
class RagChunk:
    """One text chunk ready for embedding and vector storage."""

    chunk_id: str
    text: str
    metadata: dict[str, str | int | float | bool]


def display_disease_name(disease: str) -> str:
    """Convert model labels such as ``Tomato___Late_blight`` to readable text."""
    clean = disease.replace("___", " ")
    clean = clean.replace("_", " ").replace("-", " ")
    clean = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", clean)
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean


def normalize_name(text: str) -> str:
    """Normalize labels and RAG disease names for fuzzy matching."""
    value = display_disease_name(text).lower()
    replacements = {
        "crinckle": "crinkle",
        "mossaic": "mosaic",
        "syndrone": "syndrome",
        "brownrust": "brown rust",
        "blackpoint": "black point",
        "fusariumfootrot": "fusarium foot rot",
        "healthyleaf": "healthy leaf",
        "wheatblast": "wheat blast",
        "soybean": "soyabean",
        "two spotted": "two-spotted",
    }
    for old, new in replacements.items():
        value = value.replace(old, new)
    value = re.sub(r"\b(tomato|maize|ragi|rice|wheat|sugarcane|soyabean)\b", " ", value)
    value = re.sub(r"\b(disease|phase|complex)\b", " ", value)
    value = re.sub(r"\b1\b", " ", value)
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def _strip_code_fences(text: str) -> str:
    value = text.strip()
    if value.startswith("```"):
        value = re.sub(r"^```(?:json)?\s*", "", value, flags=re.IGNORECASE)
        value = re.sub(r"\s*```$", "", value)
    return value.strip()


def _remove_trailing_commas(text: str) -> str:
    return re.sub(r",(\s*[}\]])", r"\1", text)


def _extract_balanced_objects(text: str) -> list[str]:
    """Extract top-level JSON objects from imperfect JSON/Markdown text."""
    objects: list[str] = []
    start: int | None = None
    depth = 0
    in_string = False
    escaped = False

    for i, char in enumerate(text):
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
            continue
        if char == "{":
            if depth == 0:
                start = i
            depth += 1
            continue
        if char == "}" and depth:
            depth -= 1
            if depth == 0 and start is not None:
                objects.append(text[start : i + 1])
                start = None
    return objects


def parse_rag_file(path: Path, crop_key: str | None = None) -> list[RagRecord]:
    """Parse one crop RAG file into records."""
    text = _strip_code_fences(path.read_text(encoding="utf-8-sig"))
    parsed_items: list[dict[str, Any]] = []

    try:
        raw = json.loads(_remove_trailing_commas(text))
        if isinstance(raw, dict):
            parsed_items = [raw]
        elif isinstance(raw, list):
            parsed_items = [item for item in raw if isinstance(item, dict)]
    except json.JSONDecodeError:
        for obj_text in _extract_balanced_objects(text):
            try:
                parsed_items.append(json.loads(_remove_trailing_commas(obj_text)))
            except json.JSONDecodeError:
                continue

    crop = crop_key or path.stem.lower()
    records: list[RagRecord] = []
    for idx, item in enumerate(parsed_items):
        crop_info = item.get("crop", {})
        disease_info = item.get("disease", {})
        crop_display = (
            crop_info.get("common_name")
            or crop_info.get("english_name")
            or display_disease_name(crop)
        )
        disease_name = disease_info.get("name") or item.get("name") or f"Record {idx + 1}"
        record_id = str(item.get("id") or f"{path.stem}-{idx + 1}")
        records.append(
            RagRecord(
                source_file=path.name,
                record_id=record_id,
                crop=crop,
                crop_display=str(crop_display),
                disease_name=str(disease_name),
                disease_key=normalize_name(str(disease_name)),
                data=item,
            )
        )
    return records


def load_rag_records(rag_dir: Path) -> dict[str, list[RagRecord]]:
    """Load every crop source file into a crop -> records mapping."""
    by_crop: dict[str, list[RagRecord]] = {}
    for crop, filename in CROP_FILENAMES.items():
        path = rag_dir / filename
        if not path.exists():
            by_crop[crop] = []
            continue
        by_crop[crop] = parse_rag_file(path, crop)
    return by_crop


def is_healthy_disease(disease: str) -> bool:
    key = normalize_name(disease)
    return any(marker in key for marker in HEALTHY_MARKERS)


def _score_match(label_disease: str, record: RagRecord) -> float:
    label_key = normalize_name(label_disease)
    record_key = record.disease_key
    if not label_key or not record_key:
        return 0.0
    if label_key == record_key:
        return 1.0
    label_tokens = set(label_key.split())
    record_tokens = set(record_key.split())
    if label_tokens and label_tokens <= record_tokens:
        return 0.92
    if record_tokens and record_tokens <= label_tokens:
        return 0.88
    jaccard = len(label_tokens & record_tokens) / max(len(label_tokens | record_tokens), 1)
    seq = SequenceMatcher(None, label_key, record_key).ratio()
    return max(jaccard, seq * 0.82)


def match_record_for_label(
    label: str,
    records_by_crop: dict[str, list[RagRecord]],
) -> tuple[RagRecord | None, str, float]:
    """Match a model label to the best RAG record for the same crop."""
    crop, disease = split_label(label)
    records = records_by_crop.get(crop, [])
    if not records:
        return None, "missing_crop_file", 0.0

    manual = MANUAL_ALIASES.get(label)
    if manual:
        manual_key = normalize_name(manual)
        for record in records:
            if record.disease_key == manual_key or manual_key in record.disease_key:
                return record, "manual", 1.0

    if is_healthy_disease(disease):
        return None, "healthy_synthetic", 1.0

    best: tuple[RagRecord | None, float] = (None, 0.0)
    for record in records:
        score = _score_match(disease, record)
        if score > best[1]:
            best = (record, score)

    if best[0] is not None and best[1] >= 0.56:
        return best[0], "fuzzy", best[1]
    return None, "unmatched", best[1]


def build_label_aliases(
    labels: dict[int, str],
    records_by_crop: dict[str, list[RagRecord]],
) -> dict[str, dict[str, Any]]:
    """Build an audit-friendly alias map for all model labels."""
    aliases: dict[str, dict[str, Any]] = {}
    for class_id, label in sorted(labels.items()):
        crop, disease = split_label(label)
        record, match_type, score = match_record_for_label(label, records_by_crop)
        aliases[label] = {
            "class_id": class_id,
            "crop": crop,
            "disease": disease,
            "display_name": display_disease_name(disease),
            "match_type": match_type,
            "match_score": round(score, 4),
            "source_file": CROP_FILENAMES.get(crop),
            "record_id": record.record_id if record else None,
            "record_disease": record.disease_name if record else None,
        }
    return aliases


def audit_aliases(aliases: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Summarize alias coverage."""
    counts: dict[str, int] = {}
    unmatched: list[str] = []
    for label, meta in aliases.items():
        match_type = str(meta["match_type"])
        counts[match_type] = counts.get(match_type, 0) + 1
        if match_type in {"unmatched", "missing_crop_file"}:
            unmatched.append(label)
    return {
        "total_labels": len(aliases),
        "counts_by_match_type": counts,
        "unmatched_labels": unmatched,
        "unmatched_count": len(unmatched),
    }


def _flatten_value(value: Any, *, indent: int = 0) -> list[str]:
    prefix = "  " * indent
    if isinstance(value, dict):
        lines: list[str] = []
        for key, nested in value.items():
            title = display_disease_name(str(key)).title()
            if isinstance(nested, dict | list):
                lines.append(f"{prefix}{title}:")
                lines.extend(_flatten_value(nested, indent=indent + 1))
            else:
                lines.append(f"{prefix}{title}: {nested}")
        return lines
    if isinstance(value, list):
        lines = []
        for item in value:
            if isinstance(item, dict):
                lines.extend(_flatten_value(item, indent=indent))
            else:
                lines.append(f"{prefix}- {item}")
        return lines
    return [f"{prefix}{value}"]


def _section_text(section: str, value: Any) -> str:
    lines = [display_disease_name(section).title()]
    lines.extend(_flatten_value(value))
    return "\n".join(lines)


def _healthy_chunks(label: str, class_id: int, crop: str, disease: str) -> list[RagChunk]:
    text = (
        f"Crop: {crop}\n"
        f"Disease label: {label}\n"
        "Section: Healthy guidance\n\n"
        "The model detected a healthy or fresh leaf class. This means no supported disease "
        "pattern was confidently visible in the uploaded leaf image. Continue field scouting, "
        "keep irrigation balanced, avoid wet foliage for long periods, remove crop residues "
        "after harvest, and retake/upload another image if new spots, curling, yellowing, "
        "wilting, pest marks, or mold-like growth appears."
    )
    return [
        RagChunk(
            chunk_id=f"{label}::healthy",
            text=text,
            metadata={
                "label": label,
                "class_id": class_id,
                "crop": crop,
                "disease": disease,
                "display_name": display_disease_name(disease),
                "section": "healthy_guidance",
                "source_file": "synthetic",
                "record_id": "healthy_synthetic",
                "match_type": "healthy_synthetic",
            },
        )
    ]


def _fallback_chunks(
    label: str,
    class_id: int,
    crop: str,
    disease: str,
    source_file: str | None,
    match_type: str,
) -> list[RagChunk]:
    text = (
        f"Crop: {crop}\n"
        f"Disease label: {label}\n"
        f"Readable disease: {display_disease_name(disease)}\n"
        "Section: Safe fallback advisory\n\n"
        "No dedicated fact sheet was matched for this exact model label. Give cautious "
        "farmer guidance only: verify the visible symptoms, compare with nearby plants, "
        "avoid chemical dosage claims, improve sanitation and airflow, and recommend a "
        "local agriculture expert or KVK confirmation before treatment decisions."
    )
    return [
        RagChunk(
            chunk_id=f"{label}::fallback",
            text=text,
            metadata={
                "label": label,
                "class_id": class_id,
                "crop": crop,
                "disease": disease,
                "display_name": display_disease_name(disease),
                "section": "safe_fallback",
                "source_file": source_file or "unknown",
                "record_id": "unmatched",
                "match_type": match_type,
            },
        )
    ]


def chunks_for_label(
    label: str,
    alias: dict[str, Any],
    records_by_crop: dict[str, list[RagRecord]],
) -> list[RagChunk]:
    """Create labelled chunks for one model label."""
    crop = str(alias["crop"])
    disease = str(alias["disease"])
    class_id = int(alias["class_id"])
    match_type = str(alias["match_type"])

    if match_type == "healthy_synthetic":
        return _healthy_chunks(label, class_id, crop, disease)
    if match_type in {"unmatched", "missing_crop_file"}:
        return _fallback_chunks(
            label,
            class_id,
            crop,
            disease,
            alias.get("source_file"),
            match_type,
        )

    record_id = alias.get("record_id")
    record = next(
        (r for r in records_by_crop.get(crop, []) if r.record_id == record_id),
        None,
    )
    if record is None:
        return _fallback_chunks(label, class_id, crop, disease, alias.get("source_file"), "missing_record")

    chunks: list[RagChunk] = []
    base_metadata: dict[str, str | int | float | bool] = {
        "label": label,
        "class_id": class_id,
        "crop": crop,
        "disease": disease,
        "display_name": display_disease_name(disease),
        "source_file": record.source_file,
        "record_id": record.record_id,
        "record_disease": record.disease_name,
        "match_type": match_type,
    }

    priority_sections = [
        "crop",
        "disease",
        "symptoms",
        "visual_identification",
        "similar_diseases_or_issues",
        "favorable_conditions",
        "spread",
        "severity_levels",
        "management",
        "farmer_advice",
        "source_metadata",
    ]
    seen: set[str] = set()
    for section in priority_sections:
        if section not in record.data:
            continue
        seen.add(section)
        section_text = _section_text(section, record.data[section])
        text = (
            f"Crop: {record.crop_display} ({crop})\n"
            f"Model label: {label}\n"
            f"Disease: {record.disease_name}\n"
            f"Section: {display_disease_name(section)}\n\n"
            f"{section_text}"
        )
        chunks.append(
            RagChunk(
                chunk_id=f"{label}::{section}",
                text=text,
                metadata={**base_metadata, "section": section},
            )
        )

    for section, value in record.data.items():
        if section in seen or section == "rag_chunks":
            continue
        text = (
            f"Crop: {record.crop_display} ({crop})\n"
            f"Model label: {label}\n"
            f"Disease: {record.disease_name}\n"
            f"Section: {display_disease_name(section)}\n\n"
            f"{_section_text(section, value)}"
        )
        chunks.append(
            RagChunk(
                chunk_id=f"{label}::{section}",
                text=text,
                metadata={**base_metadata, "section": str(section)},
            )
        )

    for i, extra in enumerate(record.data.get("rag_chunks", []) or [], start=1):
        if not isinstance(extra, dict):
            continue
        title = str(extra.get("title") or f"Extra RAG chunk {i}")
        content = str(extra.get("content") or "")
        if not content.strip():
            continue
        chunks.append(
            RagChunk(
                chunk_id=f"{label}::rag_chunk_{i}",
                text=(
                    f"Crop: {record.crop_display} ({crop})\n"
                    f"Model label: {label}\n"
                    f"Disease: {record.disease_name}\n"
                    f"Section: {title}\n\n{content}"
                ),
                metadata={**base_metadata, "section": f"rag_chunk_{i}"},
            )
        )

    return chunks


def build_chunks(
    labels: dict[int, str],
    records_by_crop: dict[str, list[RagRecord]],
    aliases: dict[str, dict[str, Any]] | None = None,
) -> list[RagChunk]:
    """Build all chunks for the model label map."""
    alias_map = aliases or build_label_aliases(labels, records_by_crop)
    chunks: list[RagChunk] = []
    for _, label in sorted(labels.items()):
        chunks.extend(chunks_for_label(label, alias_map[label], records_by_crop))
    return chunks

"""Runtime RAG retrieval and Gemini advisory generation."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class AdvisoryResult:
    """Farmer-facing advisory returned by the RAG layer."""

    status: str
    source: str
    label: str | None
    crop: str | None
    disease: str | None
    summary: str
    symptoms_to_check: list[str]
    immediate_actions: list[str]
    precautions: list[str]
    prevention: list[str]
    similar_diseases: list[str]
    expert_advice: str
    safety_note: str
    retrieved_chunks: list[dict[str, Any]]

    def to_json(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "source": self.source,
            "label": self.label,
            "crop": self.crop,
            "disease": self.disease,
            "summary": self.summary,
            "symptoms_to_check": self.symptoms_to_check,
            "immediate_actions": self.immediate_actions,
            "precautions": self.precautions,
            "prevention": self.prevention,
            "similar_diseases": self.similar_diseases,
            "expert_advice": self.expert_advice,
            "safety_note": self.safety_note,
            "retrieved_chunks": self.retrieved_chunks,
        }


def build_retake_advisory(*, reason: str | None, guidance: str | None) -> AdvisoryResult:
    """Return a non-disease advisory for retake decisions."""
    summary = guidance or "The image could not be diagnosed reliably. Please retake the photo."
    return AdvisoryResult(
        status="retake",
        source="decision_router",
        label=None,
        crop=None,
        disease=None,
        summary=summary,
        symptoms_to_check=[],
        immediate_actions=[
            "Retake the photo in clear natural light.",
            "Center one affected leaf in the frame.",
            "Avoid blurry, very dark, or overexposed images.",
        ],
        precautions=[],
        prevention=[],
        similar_diseases=[],
        expert_advice="Upload a clearer image before making disease treatment decisions.",
        safety_note="No treatment recommendation is made because the image needs to be retaken.",
        retrieved_chunks=[],
    )


class AdvisoryService:
    """Retrieve exact disease chunks from Chroma and ask Gemini for an advisory."""

    def __init__(
        self,
        *,
        chroma_dir: Path,
        collection_name: str,
        api_key: str,
        generation_model: str,
        top_k: int,
    ) -> None:
        self.chroma_dir = chroma_dir
        self.collection_name = collection_name
        self.api_key = api_key
        self.generation_model = generation_model
        self.top_k = top_k

        import chromadb
        from google import genai

        self._genai = genai
        self._client = genai.Client(api_key=api_key)
        self._chroma = chromadb.PersistentClient(path=str(chroma_dir))
        self._collection = self._chroma.get_collection(collection_name)

    @classmethod
    def from_settings(cls, settings: Any) -> AdvisoryService | None:
        """Create the service if configuration, packages, API key, and index exist."""
        if not getattr(settings, "rag_enabled", True):
            return None

        key = (
            getattr(settings, "gemini_api_key", None)
            or os.getenv("GEMINI_API_KEY")
            or os.getenv("CPL_GEMINI_API_KEY")
        )
        if not key:
            return None

        chroma_dir = Path(settings.rag_chroma_dir)
        if not chroma_dir.exists():
            return None

        try:
            return cls(
                chroma_dir=chroma_dir,
                collection_name=str(settings.rag_collection_name),
                api_key=key,
                generation_model=str(settings.rag_generation_model),
                top_k=int(settings.rag_top_k),
            )
        except Exception:
            return None

    def retrieve(self, *, label: str, crop: str, disease: str) -> list[dict[str, Any]]:
        """Retrieve exact-label chunks for a prediction."""
        query = (
            f"{crop} {disease} crop disease symptoms immediate actions precautions "
            "prevention similar diseases farmer advisory"
        )
        result = self._collection.query(
            query_texts=[query],
            n_results=self.top_k,
            where={"label": label},
        )
        documents_nested = result.get("documents") or [[]]
        metadatas_nested = result.get("metadatas") or [[]]
        distances_nested = result.get("distances") or [[]]
        docs = documents_nested[0] if documents_nested else []
        metas = metadatas_nested[0] if metadatas_nested else []
        distances = distances_nested[0] if distances_nested else []

        chunks: list[dict[str, Any]] = []
        for i, doc in enumerate(docs):
            meta = metas[i] if i < len(metas) else {}
            distance = distances[i] if i < len(distances) else None
            chunks.append({"text": doc, "metadata": meta, "distance": distance})

        priority = self._priority_chunks(label=label)
        return _merge_chunks(priority + chunks, limit=max(self.top_k, 10))

    def _priority_chunks(self, *, label: str) -> list[dict[str, Any]]:
        """Fetch must-have exact-label sections before semantic ranking."""
        priority_sections = [
            "farmer_advice",
            "symptoms",
            "management",
            "similar_diseases_or_issues",
            "severity_levels",
            "visual_identification",
            "disease",
        ]
        try:
            result = self._collection.get(
                where={"label": label},
                include=["documents", "metadatas"],
            )
        except Exception:
            return []

        docs = result.get("documents") or []
        metas = result.get("metadatas") or []
        by_section: dict[str, dict[str, Any]] = {}
        for i, doc in enumerate(docs):
            meta = metas[i] if i < len(metas) else {}
            section = str(meta.get("section") or "")
            if section and section not in by_section:
                by_section[section] = {"text": doc, "metadata": meta, "distance": None}
        return [by_section[section] for section in priority_sections if section in by_section]

    def generate(
        self,
        *,
        label: str,
        crop: str,
        disease: str,
        decision: str,
        confidence: float,
        chunks: list[dict[str, Any]],
    ) -> AdvisoryResult:
        """Generate a grounded advisory from retrieved context."""
        if not chunks:
            return _fallback_advisory(
                label=label,
                crop=crop,
                disease=disease,
                status="no_context",
                summary="No RAG context was found for this exact model label.",
                chunks=[],
            )

        context = "\n\n---\n\n".join(str(chunk["text"]) for chunk in chunks)
        prompt = f"""
You are an agricultural disease advisory assistant for Indian farmers.

Use ONLY the retrieved context. Do not invent pesticide names, doses, or sources.
If the API decision is expert_review, write cautiously and ask the farmer to verify
visible symptoms or consult a local agriculture expert/KVK before treatment.

Prediction:
- label: {label}
- crop: {crop}
- disease: {disease}
- decision: {decision}
- fused confidence: {confidence:.4f}

Retrieved context:
{context}

Return strict JSON with these keys:
summary: string
symptoms_to_check: string[]
immediate_actions: string[]
precautions: string[]
prevention: string[]
similar_diseases: string[]
expert_advice: string
safety_note: string
"""
        try:
            response = self._client.models.generate_content(
                model=self.generation_model,
                contents=prompt,
            )
            parsed = _parse_json_response(response.text or "")
        except Exception:
            return _local_context_advisory(
                label=label,
                crop=crop,
                disease=disease,
                chunks=chunks,
            )

        return AdvisoryResult(
            status="ok",
            source="gemini_rag",
            label=label,
            crop=crop,
            disease=disease,
            summary=_as_string(parsed.get("summary")),
            symptoms_to_check=_as_string_list(parsed.get("symptoms_to_check")),
            immediate_actions=_as_string_list(parsed.get("immediate_actions")),
            precautions=_as_string_list(parsed.get("precautions")),
            prevention=_as_string_list(parsed.get("prevention")),
            similar_diseases=_as_string_list(parsed.get("similar_diseases")),
            expert_advice=_as_string(parsed.get("expert_advice")),
            safety_note=_as_string(parsed.get("safety_note"))
            or "Use chemicals only according to locally approved labels and expert advice.",
            retrieved_chunks=_chunk_citations(chunks),
        )

    def advise(
        self,
        *,
        label: str,
        crop: str,
        disease: str,
        decision: str,
        confidence: float,
    ) -> AdvisoryResult:
        chunks = self.retrieve(label=label, crop=crop, disease=disease)
        return self.generate(
            label=label,
            crop=crop,
            disease=disease,
            decision=decision,
            confidence=confidence,
            chunks=chunks,
        )


def _parse_json_response(text: str) -> dict[str, Any]:
    value = text.strip()
    if value.startswith("```"):
        value = re.sub(r"^```(?:json)?\s*", "", value, flags=re.IGNORECASE)
        value = re.sub(r"\s*```$", "", value)
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", value, flags=re.DOTALL)
        if match is None:
            return {}
        parsed = json.loads(match.group(0))
    return parsed if isinstance(parsed, dict) else {}


def _as_string(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def _as_string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [_as_string(item) for item in value if _as_string(item)]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _chunk_citations(chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    citations: list[dict[str, Any]] = []
    for chunk in chunks:
        meta = chunk.get("metadata") or {}
        citations.append(
            {
                "section": meta.get("section"),
                "source_file": meta.get("source_file"),
                "record_id": meta.get("record_id"),
                "distance": chunk.get("distance"),
            }
        )
    return citations


def _merge_chunks(chunks: list[dict[str, Any]], *, limit: int) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for chunk in chunks:
        meta = chunk.get("metadata") or {}
        key = (str(meta.get("label") or ""), str(meta.get("section") or ""))
        text = str(chunk.get("text") or "")
        if key in seen or not text:
            continue
        seen.add(key)
        merged.append(chunk)
        if len(merged) >= limit:
            break
    return merged


def _local_context_advisory(
    *,
    label: str,
    crop: str,
    disease: str,
    chunks: list[dict[str, Any]],
) -> AdvisoryResult:
    """Build a deterministic advisory from retrieved chunks when Gemini is blocked."""
    section_text: dict[str, str] = {}
    for chunk in chunks:
        meta = chunk.get("metadata") or {}
        section = str(meta.get("section") or "")
        text = str(chunk.get("text") or "")
        if section and text:
            section_text[section] = text

    farmer = section_text.get("farmer_advice", "")
    management = section_text.get("management", "")
    symptoms = section_text.get("symptoms", "")
    similar = section_text.get("similar_diseases_or_issues", "")
    severity = section_text.get("severity_levels", "")

    summary = (
        _field_value(farmer, "Simple Explanation")
        or _field_value(severity, "Risk Warning")
        or f"Retrieved advisory context for {crop} - {disease}."
    )
    immediate_actions = (
        _field_list(farmer, "What To Do Now")
        or _field_list(management, "Immediate Action")
        or ["Verify the symptoms on multiple plants before treatment decisions."]
    )
    symptoms_to_check = (
        _field_list(symptoms, "Early Stage")
        + _field_list(symptoms, "Middle Stage")
        + _field_list(symptoms, "Visible Signs")
    )[:8]
    precautions = (
        _field_list(farmer, "What Not To Do")
        or _field_list(management, "Cultural Control")
        or ["Avoid unnecessary chemical application before field confirmation."]
    )
    prevention = (
        _field_list(management, "Cultural Control") + _field_list(management, "Organic Control")
    )[:8]
    similar_diseases = _similar_names(similar)
    expert_advice = (
        "; ".join(_field_list(farmer, "When To Call Expert"))
        or "Consult a local agriculture expert or KVK if symptoms spread or treatment is needed."
    )

    return AdvisoryResult(
        status="local_context_fallback",
        source="local_rag",
        label=label,
        crop=crop,
        disease=disease,
        summary=summary,
        symptoms_to_check=symptoms_to_check,
        immediate_actions=immediate_actions,
        precautions=precautions,
        prevention=prevention,
        similar_diseases=similar_diseases,
        expert_advice=expert_advice,
        safety_note=(
            "This advisory is based on retrieved crop-disease guidance. Confirm symptoms "
            "in the field and use chemicals only according to locally approved labels and "
            "expert advice."
        ),
        retrieved_chunks=_chunk_citations(chunks),
    )


def _field_value(text: str, field: str) -> str:
    pattern = re.compile(rf"^{re.escape(field)}:\s*(.+)$", flags=re.MULTILINE)
    match = pattern.search(text)
    return match.group(1).strip() if match else ""


def _field_list(text: str, field: str) -> list[str]:
    lines = text.splitlines()
    items: list[str] = []
    capture = False
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith(f"{field}:"):
            capture = True
            value = stripped.split(":", 1)[1].strip()
            if value:
                items.append(value)
            continue
        if capture:
            if re.match(r"^[A-Z][A-Za-z0-9 /_-]+:", stripped):
                break
            if stripped.startswith("- "):
                items.append(stripped[2:].strip())
    return _dedupe(items)


def _similar_names(text: str) -> list[str]:
    names: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("Name:"):
            names.append(stripped.split(":", 1)[1].strip())
    return _dedupe(names)[:6]


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for item in items:
        key = item.lower()
        if key in seen:
            continue
        seen.add(key)
        output.append(item)
    return output


def _fallback_advisory(
    *,
    label: str,
    crop: str,
    disease: str,
    status: str,
    summary: str,
    chunks: list[dict[str, Any]],
) -> AdvisoryResult:
    return AdvisoryResult(
        status=status,
        source="rag_fallback",
        label=label,
        crop=crop,
        disease=disease,
        summary=summary,
        symptoms_to_check=[],
        immediate_actions=[
            "Verify symptoms on multiple plants before taking treatment action.",
            "Improve sanitation, airflow, and avoid overhead irrigation where possible.",
        ],
        precautions=[
            "Do not apply chemical treatment only from a low-context AI response.",
        ],
        prevention=[],
        similar_diseases=[],
        expert_advice="Consult a local agriculture expert or KVK for confirmation.",
        safety_note="Use chemicals only according to locally approved labels and expert advice.",
        retrieved_chunks=_chunk_citations(chunks),
    )

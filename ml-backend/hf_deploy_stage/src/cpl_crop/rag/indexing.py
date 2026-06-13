"""Offline Chroma index builder for crop-disease RAG chunks."""

from __future__ import annotations

import json
from contextlib import suppress
from pathlib import Path
from typing import Any

from cpl_crop.labels import load_labels
from cpl_crop.rag.documents import (
    audit_aliases,
    build_chunks,
    build_label_aliases,
    load_rag_records,
)

DEFAULT_COLLECTION = "crop_disease_advisory"


def write_audit_files(
    *,
    labels_path: Path,
    rag_dir: Path,
    out_dir: Path,
) -> dict[str, Any]:
    """Write label aliases and an audit report to ``out_dir``."""
    labels = load_labels(labels_path)
    records_by_crop = load_rag_records(rag_dir)
    aliases = build_label_aliases(labels, records_by_crop)
    report = audit_aliases(aliases)

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "label_aliases.json").write_text(
        json.dumps(aliases, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (out_dir / "audit_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return report


def build_chroma_index(
    *,
    labels_path: Path,
    rag_dir: Path,
    chroma_dir: Path,
    audit_dir: Path,
    collection_name: str = DEFAULT_COLLECTION,
) -> dict[str, Any]:
    """Chunk RAG records and persist a free local Chroma vector DB.

    Chroma's local default embedding function is used here, so no API key is
    needed for embedding/index creation. Gemini is reserved for runtime answer
    generation after retrieval.
    """
    try:
        import chromadb
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise RuntimeError("Install chromadb before building the RAG index.") from exc

    labels = load_labels(labels_path)
    records_by_crop = load_rag_records(rag_dir)
    aliases = build_label_aliases(labels, records_by_crop)
    chunks = build_chunks(labels, records_by_crop, aliases)
    report = audit_aliases(aliases)

    audit_dir.mkdir(parents=True, exist_ok=True)
    (audit_dir / "label_aliases.json").write_text(
        json.dumps(aliases, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (audit_dir / "audit_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (audit_dir / "chunk_manifest.json").write_text(
        json.dumps(
            [
                {
                    "chunk_id": chunk.chunk_id,
                    "metadata": chunk.metadata,
                    "chars": len(chunk.text),
                }
                for chunk in chunks
            ],
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    chroma_dir.mkdir(parents=True, exist_ok=True)
    chroma = chromadb.PersistentClient(path=str(chroma_dir))
    with suppress(Exception):
        chroma.delete_collection(collection_name)
    collection = chroma.get_or_create_collection(
        collection_name,
        metadata={
            "hnsw:space": "cosine",
            "embedding_model": "chroma-default",
        },
    )

    collection.add(
        ids=[chunk.chunk_id for chunk in chunks],
        documents=[chunk.text for chunk in chunks],
        metadatas=[chunk.metadata for chunk in chunks],
    )

    index_meta = {
        "collection": collection_name,
        "chunk_count": len(chunks),
        "label_count": len(labels),
        "embedding_model": "chroma-default",
        "audit": report,
    }
    (audit_dir / "index_metadata.json").write_text(
        json.dumps(index_meta, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return index_meta

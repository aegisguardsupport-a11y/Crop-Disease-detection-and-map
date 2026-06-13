from __future__ import annotations

from pathlib import Path

from cpl_crop.labels import load_labels
from cpl_crop.rag.documents import (
    audit_aliases,
    build_chunks,
    build_label_aliases,
    load_rag_records,
)


def test_rag_sources_cover_all_model_labels(project_root: Path) -> None:
    labels = load_labels(project_root / "exports" / "cpl_id_to_label.json")
    rag_dir = project_root.parent / "RAG"
    records = load_rag_records(rag_dir)

    aliases = build_label_aliases(labels, records)
    report = audit_aliases(aliases)
    chunks = build_chunks(labels, records, aliases)

    assert report["total_labels"] == 139
    assert set(labels.values()) == set(aliases)
    assert len(chunks) >= len(labels)
    assert {chunk.metadata["label"] for chunk in chunks} == set(labels.values())


def test_tolerant_parser_reads_markdown_fenced_json(project_root: Path) -> None:
    rag_dir = project_root.parent / "RAG"
    records = load_rag_records(rag_dir)

    assert any(record.disease_name == "Purple Blotch" for record in records["onion"])
    assert any(
        record.disease_name == "Cercospora Leaf Spot"
        for record in records["pigeonpea"]
    )

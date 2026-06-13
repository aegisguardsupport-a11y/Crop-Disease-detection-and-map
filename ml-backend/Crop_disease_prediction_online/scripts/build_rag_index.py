"""Build the local Chroma vector DB for crop-disease RAG advisories.

Run from ``Crop_disease_prediction_online``:

    python scripts/build_rag_index.py --rag-dir ../RAG
"""

from __future__ import annotations

import argparse
from pathlib import Path

from cpl_crop.rag.indexing import build_chroma_index


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--labels", type=Path, default=Path("exports/cpl_id_to_label.json"))
    parser.add_argument("--rag-dir", type=Path, default=Path("../RAG"))
    parser.add_argument("--chroma-dir", type=Path, default=Path("rag/chroma_db"))
    parser.add_argument("--audit-dir", type=Path, default=Path("rag"))
    parser.add_argument("--collection", default="crop_disease_advisory")
    args = parser.parse_args()

    result = build_chroma_index(
        labels_path=args.labels,
        rag_dir=args.rag_dir,
        chroma_dir=args.chroma_dir,
        audit_dir=args.audit_dir,
        collection_name=args.collection,
    )
    print(
        "Built RAG index: "
        f"{result['chunk_count']} chunks, {result['label_count']} labels, "
        f"collection={result['collection']}"
    )


if __name__ == "__main__":
    main()

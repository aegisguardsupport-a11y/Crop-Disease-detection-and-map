"""Audit uploaded RAG data against the model's 139 crop-disease labels."""

from __future__ import annotations

import argparse
from pathlib import Path

from cpl_crop.rag.indexing import write_audit_files


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--labels", type=Path, default=Path("exports/cpl_id_to_label.json"))
    parser.add_argument("--rag-dir", type=Path, default=Path("../RAG"))
    parser.add_argument("--out-dir", type=Path, default=Path("rag"))
    args = parser.parse_args()

    report = write_audit_files(
        labels_path=args.labels,
        rag_dir=args.rag_dir,
        out_dir=args.out_dir,
    )
    print(f"Audited {report['total_labels']} labels")
    print(f"Coverage: {report['counts_by_match_type']}")
    if report["unmatched_count"]:
        print("Unmatched labels:")
        for label in report["unmatched_labels"]:
            print(f"  - {label}")


if __name__ == "__main__":
    main()

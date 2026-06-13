"""List every variable in the SavedModel so we can reconstruct the
Keras architecture and copy weights for Grad-CAM++.
"""

from __future__ import annotations

import os
from collections import Counter
from pathlib import Path

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

import tensorflow as tf  # noqa: E402

BUNDLE = Path(__file__).resolve().parents[1] / "exports" / "saved_model"


def main() -> None:
    obj = tf.saved_model.load(str(BUNDLE))
    print(f"#variables: {len(obj.variables)}")
    print(f"#trainable: {len(obj.trainable_variables)}")

    # Group by toplevel prefix
    prefixes: Counter[str] = Counter()
    for v in obj.variables:
        prefix = v.name.split("/")[0]
        prefixes[prefix] += 1
    print("\nTop-level prefixes:")
    for p, c in prefixes.most_common(20):
        print(f"  {c:4d}  {p}")

    # Show the LAST 20 variables — usually the head + final dense
    print("\nLast 25 variables:")
    for v in obj.variables[-25:]:
        print(f"  {tuple(v.shape)!s:<30s}  dtype={v.dtype.name:<12s} {v.name}")

    # Show first 15 too — usually the stem
    print("\nFirst 15 variables:")
    for v in obj.variables[:15]:
        print(f"  {tuple(v.shape)!s:<30s}  dtype={v.dtype.name:<12s} {v.name}")


if __name__ == "__main__":
    main()

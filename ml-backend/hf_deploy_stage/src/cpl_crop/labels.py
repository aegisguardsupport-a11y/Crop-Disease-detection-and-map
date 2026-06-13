"""Load and validate the ``crop::disease`` label map shipped with the bundle."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=4)
def load_labels(path: str | Path) -> dict[int, str]:
    """Load the integer→label map and verify it is dense from 0..N-1.

    Args:
        path: filesystem path to ``cpl_id_to_label.json``.

    Returns:
        Mapping of class id (int) to its ``crop::disease`` string.

    Raises:
        FileNotFoundError: the file does not exist.
        ValueError: the map is empty or has missing/duplicate ids.
    """
    p = Path(path)
    raw = json.loads(p.read_text(encoding="utf-8"))
    labels = {int(k): str(v) for k, v in raw.items()}

    if not labels:
        raise ValueError(f"Empty label map at {p}")

    expected = set(range(len(labels)))
    actual = set(labels.keys())
    if expected != actual:
        missing = sorted(expected - actual)[:10]
        extra = sorted(actual - expected)[:10]
        raise ValueError(
            f"Label map {p} is not dense [0..{len(labels) - 1}]. "
            f"Missing={missing} Extra={extra}"
        )
    return labels


def split_label(label: str) -> tuple[str, str]:
    """Split a ``crop::disease`` label into its parts.

    >>> split_label("tomato::Late_blight")
    ('tomato', 'Late_blight')
    """
    crop, sep, disease = label.partition("::")
    if not sep:
        raise ValueError(f"Label {label!r} is missing the '::' separator")
    return crop, disease

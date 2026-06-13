"""Convert a Python script with ``# %%`` cell markers to a ``.ipynb`` notebook.

Used by ``scripts/kaggle_run.py`` to auto-convert before pushing to Kaggle,
because Kaggle's ``kernels push`` with ``kernel_type: "notebook"`` requires
``.ipynb`` JSON, not ``.py``.

Cell-marker rules (compatible with VS Code / Spyder / jupytext):

* ``# %%``                              → start of a code cell
* ``# %% [markdown]``                   → start of a markdown cell
* Lines inside a markdown cell starting with ``# `` lose the prefix.
* Trailing/leading blank lines in cells are trimmed.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Literal


def _make_cell(cell_type: Literal["code", "markdown"], lines: list[str]) -> dict:
    # Trim leading/trailing blank lines so cells don't look weird
    while lines and lines[0].strip() == "":
        lines.pop(0)
    while lines and lines[-1].strip() == "":
        lines.pop()

    if cell_type == "markdown":
        cleaned: list[str] = []
        for line in lines:
            if line.startswith("# "):
                cleaned.append(line[2:])
            elif line == "#":
                cleaned.append("")
            else:
                cleaned.append(line)
        source_lines = [(ln + "\n") for ln in cleaned[:-1]] + (
            [cleaned[-1]] if cleaned else []
        )
        return {"cell_type": "markdown", "metadata": {}, "source": source_lines}

    # code cell
    source_lines = [(ln + "\n") for ln in lines[:-1]] + ([lines[-1]] if lines else [])
    return {
        "cell_type": "code",
        "metadata": {},
        "execution_count": None,
        "outputs": [],
        "source": source_lines,
    }


def py_to_ipynb(py_path: Path, ipynb_path: Path | None = None) -> Path:
    """Convert ``py_path`` to a Jupyter notebook. Returns the output path."""
    if ipynb_path is None:
        ipynb_path = py_path.with_suffix(".ipynb")

    text = py_path.read_text(encoding="utf-8")
    cells: list[dict] = []
    current: list[str] = []
    current_type: Literal["code", "markdown"] = "code"
    seen_first_marker = False

    for raw_line in text.splitlines():
        # Strip only the trailing newline; leading whitespace is significant
        line = raw_line
        if line.startswith("# %% [markdown]"):
            if seen_first_marker and current:
                cells.append(_make_cell(current_type, current))
            current = []
            current_type = "markdown"
            seen_first_marker = True
        elif line.startswith("# %%"):
            if seen_first_marker and current:
                cells.append(_make_cell(current_type, current))
            current = []
            current_type = "code"
            seen_first_marker = True
        else:
            current.append(line)

    # Flush the final cell
    if current:
        if not seen_first_marker:
            # No markers at all — treat the whole file as one code cell
            cells.append(_make_cell("code", current))
        else:
            cells.append(_make_cell(current_type, current))

    nb = {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "version": "3.10"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    ipynb_path.write_text(json.dumps(nb, indent=1), encoding="utf-8")
    return ipynb_path


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("py_file", type=Path, help="Source .py with # %% markers")
    ap.add_argument("-o", "--output", type=Path, default=None, help="Output .ipynb path")
    args = ap.parse_args()
    out = py_to_ipynb(args.py_file, args.output)
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()

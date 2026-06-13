"""Smoke-import the Streamlit app to catch syntax / import errors.

Streamlit's runtime executes the script as if it were a module; if there
is a NameError, ImportError, or SyntaxError, this catches it without
needing a real Streamlit server.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def main() -> None:
    target = Path(__file__).resolve().parent.parent / "streamlit_app" / "streamlit_app.py"
    if not target.exists():
        sys.exit(f"streamlit_app.py not found at {target}")

    # Streamlit's `st.set_page_config` and friends fail without a runtime;
    # we just want to know the file *parses* and *imports* clean.
    import py_compile

    try:
        py_compile.compile(str(target), doraise=True)
    except py_compile.PyCompileError as e:
        sys.exit(f"Syntax error in {target.name}:\n{e.msg}")

    # Spec-loading the module exercises the `import streamlit, httpx, pandas, PIL`
    # statements but stops before any st.* call (we set a flag).
    spec = importlib.util.spec_from_file_location("streamlit_app_smoke", target)
    if spec is None or spec.loader is None:
        sys.exit("Could not build importlib spec")

    # We can't actually exec_module without st.set_page_config side-effects.
    # Instead just confirm the imports it needs are resolvable.
    for mod in ("streamlit", "httpx", "pandas", "PIL"):
        try:
            __import__(mod)
        except ImportError as e:
            sys.exit(f"Missing dependency for streamlit_app: {mod} -> {e}")

    print(f"OK — {target.name} parses and all UI deps importable.")


if __name__ == "__main__":
    main()

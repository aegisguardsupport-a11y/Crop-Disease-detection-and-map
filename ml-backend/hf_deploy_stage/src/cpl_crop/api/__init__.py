"""HTTP API for the CPL crop-disease classifier.

Public surface:

* :func:`cpl_crop.api.app.create_app` — FastAPI factory.
* ``python -m cpl_crop.api`` — start uvicorn with the configured app.
"""

from __future__ import annotations

from cpl_crop.api.app import create_app

__all__ = ["create_app"]

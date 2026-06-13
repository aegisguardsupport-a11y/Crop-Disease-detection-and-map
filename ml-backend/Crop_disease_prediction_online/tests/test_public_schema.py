"""Public API schema contract tests."""

from __future__ import annotations

from cpl_crop.api.app import create_app


def test_openapi_only_exposes_predictdisease() -> None:
    app = create_app()
    schema = app.openapi()

    assert set(schema["paths"].keys()) == {"/predictdisease"}

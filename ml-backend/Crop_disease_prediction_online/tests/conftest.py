"""Shared pytest fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

from cpl_crop.config import Settings


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Repo root (parent of ``tests/``)."""
    return Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session")
def settings(project_root: Path) -> Settings:
    """Settings pointing at the local extracted bundle.

    Tests should never load .env so they stay deterministic; we override
    the bundle path explicitly here.
    """
    return Settings(bundle_dir=project_root / "exports", _env_file=None)  # type: ignore[call-arg]

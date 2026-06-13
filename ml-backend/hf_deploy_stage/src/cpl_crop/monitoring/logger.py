"""Thread-safe JSONL logger for per-request monitoring records.

We use JSONL (one JSON object per line) instead of parquet because
appends are atomic at the OS level for line-oriented files smaller
than the page size, and the file stays human-inspectable. The drift
script later loads it into a pandas DataFrame with ``read_json(lines=True)``.

A single :class:`MonitoringLogger` instance is created in the FastAPI
lifespan and shared across requests. The internal lock keeps multiple
worker threads from interleaving writes.
"""

from __future__ import annotations

import json
import threading
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import structlog

from cpl_crop.monitoring.features import RequestFeatures

logger = structlog.get_logger(__name__)


class MonitoringLogger:
    """Append-only JSONL logger for :class:`RequestFeatures` records."""

    def __init__(self, log_path: Path) -> None:
        self._path = Path(log_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        # Touch the file so /monitoring/stats can stat it on day 0.
        self._path.touch(exist_ok=True)
        logger.info("monitoring_logger.init", path=str(self._path))

    @property
    def path(self) -> Path:
        return self._path

    def log(self, record: RequestFeatures) -> None:
        """Append one record to the JSONL file."""
        line = json.dumps(record.to_dict(), separators=(",", ":"))
        with self._lock, self._path.open("a", encoding="utf-8") as fp:
            fp.write(line + "\n")

    def count(self) -> int:
        """Return the number of records currently logged."""
        if not self._path.exists():
            return 0
        with self._path.open("r", encoding="utf-8") as fp:
            return sum(1 for _ in fp)

    def tail(self, n: int = 10) -> list[dict[str, Any]]:
        """Return the most recent ``n`` records as plain dicts."""
        if not self._path.exists():
            return []
        # Small files only — for hackathon scale this is fine.
        with self._path.open("r", encoding="utf-8") as fp:
            lines = fp.readlines()
        out: list[dict[str, Any]] = []
        for line in lines[-n:]:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return out

    def iter_records(self) -> Iterable[dict[str, Any]]:
        """Yield every record as a dict. Used by drift.py."""
        if not self._path.exists():
            return
        with self._path.open("r", encoding="utf-8") as fp:
            for line in fp:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    continue

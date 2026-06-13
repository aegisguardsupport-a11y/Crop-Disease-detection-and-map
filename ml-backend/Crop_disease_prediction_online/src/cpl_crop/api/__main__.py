"""Entry point: ``python -m cpl_crop.api``.

Reads host/port/workers from settings and starts uvicorn in factory mode
so the app is built fresh per worker process.
"""

from __future__ import annotations

import uvicorn

from cpl_crop.config import get_settings


def main() -> None:
    settings = get_settings()
    uvicorn.run(
        "cpl_crop.api.app:create_app",
        factory=True,
        host=settings.api_host,
        port=settings.api_port,
        workers=settings.api_workers,
        log_level=settings.log_level.lower(),
        access_log=False,  # we emit our own structured access log
    )


if __name__ == "__main__":
    main()

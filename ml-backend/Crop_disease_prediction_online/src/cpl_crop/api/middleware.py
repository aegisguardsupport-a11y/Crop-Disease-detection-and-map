"""HTTP middleware: request id + access logging."""

from __future__ import annotations

import time
import uuid
from collections.abc import Awaitable, Callable

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

REQUEST_ID_HEADER = "X-Request-ID"

logger = structlog.get_logger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Assign / propagate ``X-Request-ID`` and emit a structured access log.

    * If the client sent ``X-Request-ID`` we honor it; otherwise we mint one.
    * The id is bound to structlog contextvars so every log line emitted
      while handling the request includes it automatically.
    * The id is stored on ``request.state.request_id`` for handlers.
    * The id is echoed back in the response header.
    * On the way out we log status + duration.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        rid = request.headers.get(REQUEST_ID_HEADER) or uuid.uuid4().hex
        request.state.request_id = rid

        # Skip access logs for noisy housekeeping endpoints
        is_noisy = request.url.path in {"/metrics", "/health", "/ready"}

        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=rid,
            method=request.method,
            path=request.url.path,
        )

        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = (time.perf_counter() - start) * 1000
            logger.exception(
                "request.failed",
                duration_ms=round(duration_ms, 2),
            )
            raise
        else:
            duration_ms = (time.perf_counter() - start) * 1000
            response.headers[REQUEST_ID_HEADER] = rid
            if not is_noisy:
                logger.info(
                    "request.completed",
                    status_code=response.status_code,
                    duration_ms=round(duration_ms, 2),
                )
            return response
        finally:
            structlog.contextvars.clear_contextvars()

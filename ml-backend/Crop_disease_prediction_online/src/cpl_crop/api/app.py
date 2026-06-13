"""FastAPI application factory.

The factory pattern lets tests build an isolated app without the
side-effect of starting uvicorn at import time.
"""

from __future__ import annotations

import structlog
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from starlette.exceptions import HTTPException as StarletteHTTPException

from cpl_crop.api.lifespan import lifespan
from cpl_crop.api.logging_setup import configure_logging
from cpl_crop.api.middleware import RequestIDMiddleware
from cpl_crop.api.routes import router
from cpl_crop.api.schemas import ErrorResponse
from cpl_crop.config import get_settings

API_TITLE = "CPL Crop-Disease API"
API_DESCRIPTION = (
    "Inference + (eventually) explainability service for the fine-tuned "
    "EfficientNetB2 crop-disease classifier (139 classes)."
)


def create_app() -> FastAPI:
    """Build and return the FastAPI application."""
    settings = get_settings()
    configure_logging(level=settings.log_level, json=settings.api_log_json)

    log = structlog.get_logger(__name__)
    log.info(
        "app.create",
        model_version=settings.model_version,
        log_json=settings.api_log_json,
    )

    app = FastAPI(
        title=API_TITLE,
        description=API_DESCRIPTION,
        version=settings.model_version,
        lifespan=lifespan,
    )

    app.add_middleware(RequestIDMiddleware)

    # CORS — required for browser-based frontends (teammate apps) to call
    # this API across origins. Configurable via CPL_CORS_ORIGINS (comma-
    # separated list, defaults to "*" for hackathon-grade openness).
    cors_origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins or ["*"],
        allow_credentials=False,  # incompatible with allow_origins=["*"]
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )

    app.include_router(router)

    _register_exception_handlers(app)

    # Prometheus /metrics. excluded_handlers prevents /metrics itself from
    # being instrumented (otherwise scrapes increase their own counter).
    Instrumentator(
        excluded_handlers=["/metrics", "/health", "/ready"],
    ).instrument(app).expose(app, include_in_schema=False, tags=["meta"])

    return app


def _register_exception_handlers(app: FastAPI) -> None:
    log = structlog.get_logger(__name__)

    @app.exception_handler(StarletteHTTPException)
    async def http_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        rid = getattr(request.state, "request_id", "unknown")
        body = ErrorResponse(
            request_id=rid,
            detail=str(exc.detail),
            code=f"http_{exc.status_code}",
        ).model_dump()
        return JSONResponse(status_code=exc.status_code, content=body)

    @app.exception_handler(RequestValidationError)
    async def validation_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        rid = getattr(request.state, "request_id", "unknown")
        body = ErrorResponse(
            request_id=rid,
            detail=exc.errors()[0]["msg"] if exc.errors() else "Validation failed",
            code="validation_error",
        ).model_dump()
        body["errors"] = exc.errors()
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content=body,
        )

    @app.exception_handler(Exception)
    async def unhandled_handler(request: Request, exc: Exception) -> JSONResponse:
        rid = getattr(request.state, "request_id", "unknown")
        log.exception("request.unhandled_exception", request_id=rid)
        body = ErrorResponse(
            request_id=rid,
            detail="Internal server error",
            code="internal_error",
        ).model_dump()
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=body,
        )

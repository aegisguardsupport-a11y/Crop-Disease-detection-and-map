# syntax=docker/dockerfile:1.7
#
# Multi-stage Dockerfile for the CPL crop-disease FastAPI service.
#
# Stage 1 (builder)  : install pinned Python deps into a venv
# Stage 2 (runtime)  : slim runtime image with the venv + source + models
#
# The final image is large (~3-4 GB) because it bundles tensorflow, torch,
# torchvision, ultralytics, transformers, and ~80 MB of model artifacts.
# That's the cost of running 4 different models in one container.
# A separate Phase 4.5 could split the API into per-model microservices.

ARG PYTHON_VERSION=3.12-slim


# =============================================================================
# 1. Builder
# =============================================================================
FROM python:${PYTHON_VERSION} AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

# Build deps for some Python wheels (h5py, etc.) plus libgl/glib for opencv.
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libgl1 \
        libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Create an isolated venv so Stage 2 just has to copy /opt/venv across.
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies first (cache-friendly layer).
COPY requirements.txt ./
RUN pip install --upgrade pip \
 && pip install -r requirements.txt

# Install the package metadata so cpl_crop is importable.
COPY pyproject.toml ./
COPY src/ ./src/
RUN pip install --no-deps -e .


# =============================================================================
# 2. Runtime
# =============================================================================
FROM python:${PYTHON_VERSION} AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONUTF8=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PATH="/opt/venv/bin:$PATH" \
    CPL_API_HOST=0.0.0.0 \
    CPL_API_PORT=8000 \
    CPL_LOG_LEVEL=INFO \
    CPL_API_LOG_JSON=true \
    HF_HOME=/home/appuser/.cache/huggingface \
    TRANSFORMERS_CACHE=/home/appuser/.cache/huggingface

# Runtime libs only (libgl/glib for opencv; everything else comes from the venv).
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgl1 \
        libglib2.0-0 \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy the prebuilt venv from the builder stage.
COPY --from=builder /opt/venv /opt/venv

WORKDIR /app

# Copy source + model artifacts.
# Order matters: copy stable things first to maximise layer cache.
COPY pyproject.toml ./
COPY src/ ./src/
COPY exports/saved_model/ ./exports/saved_model/
COPY exports/cpl_id_to_label.json ./exports/cpl_id_to_label.json
COPY exports/cpl_preprocessing_config.json ./exports/cpl_preprocessing_config.json
COPY models/ ./models/

# Non-root user. Pre-create cache dir so HF model downloads on first request
# don't choke on a missing directory.
RUN useradd -m -u 1000 appuser \
 && mkdir -p /home/appuser/.cache/huggingface \
 && chown -R appuser:appuser /home/appuser /app
USER appuser

EXPOSE 8000

# /health is a cheap probe: always 200 if the process is alive. /ready
# requires the SavedModel to be fully loaded so it's better as the orchestrator
# readiness probe; we keep /health here for liveness.
HEALTHCHECK --interval=30s --timeout=5s --start-period=120s --retries=3 \
    CMD python -c "import urllib.request,sys; \
import json; r=urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3); \
sys.exit(0 if json.loads(r.read())['status']=='ok' else 1)"

CMD ["uvicorn", "cpl_crop.api.app:create_app", \
     "--factory", "--host", "0.0.0.0", "--port", "8000"]

# syntax=docker/dockerfile:1.7
#
# Hugging Face Spaces Dockerfile.
#
# Differences from the local Dockerfile at the repo root:
#   - Listens on port 7860 (HF Spaces convention)
#   - No multi-stage build (HF builds inside their environment)
#   - Skips MLflow + Evidently to keep the image lean (~700 MB smaller)
#   - Configures HF cache at /data so CLIP weights persist across restarts
#   - User is `user` (uid 1000) — HF Spaces convention

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONUTF8=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    CPL_API_HOST=0.0.0.0 \
    CPL_API_PORT=7860 \
    CPL_API_LOG_JSON=true \
    CPL_LOG_LEVEL=INFO \
    CPL_CORS_ORIGINS="*" \
    HF_HOME=/data/huggingface \
    TRANSFORMERS_CACHE=/data/huggingface \
    XDG_CACHE_HOME=/data/cache

# OS deps for opencv + ca-certs
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgl1 \
        libglib2.0-0 \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Non-root user (HF Spaces requires uid 1000)
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

WORKDIR $HOME/app

# Install Python deps. Use the lean requirements file for HF Spaces.
COPY --chown=user:user requirements.hfspaces.txt ./requirements.txt
RUN pip install --user --upgrade pip \
 && pip install --user -r requirements.txt

# Copy application source + model artefacts.
COPY --chown=user:user pyproject.toml ./
COPY --chown=user:user src/ ./src/
COPY --chown=user:user exports/saved_model/ ./exports/saved_model/
COPY --chown=user:user exports/cpl_id_to_label.json ./exports/cpl_id_to_label.json
COPY --chown=user:user exports/cpl_preprocessing_config.json ./exports/cpl_preprocessing_config.json
COPY --chown=user:user models/ ./models/
COPY --chown=user:user rag/ ./rag/

# Install the package itself
RUN pip install --user --no-deps -e .

# HF persistent storage. /data is the only writable dir on HF free tier.
USER root
RUN mkdir -p /data/huggingface /data/cache && chown -R user:user /data
USER user

EXPOSE 7860

# uvicorn entrypoint — HF expects the app to listen on app_port (7860).
CMD ["uvicorn", "cpl_crop.api.app:create_app", "--factory", \
     "--host", "0.0.0.0", "--port", "7860"]

# syntax=docker/dockerfile:1.7
#
# Lightweight Dockerfile for the Streamlit demo UI.
# It just needs to render the page and call the FastAPI service over HTTP.

ARG PYTHON_VERSION=3.12-slim


FROM python:${PYTHON_VERSION} AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    API_BASE_URL=http://api:8000

WORKDIR /app

# Install just the UI deps (streamlit, httpx, pandas, pillow). Tiny image.
COPY streamlit_app/requirements.txt ./streamlit_app/requirements.txt
RUN pip install --upgrade pip \
 && pip install -r streamlit_app/requirements.txt

# Copy the app source.
COPY streamlit_app/ ./streamlit_app/

# Non-root user
RUN useradd -m -u 1000 appuser \
 && chown -R appuser:appuser /app
USER appuser

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request,sys; \
urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health', timeout=3); \
sys.exit(0)"

CMD ["streamlit", "run", "streamlit_app/streamlit_app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--browser.gatherUsageStats=false"]

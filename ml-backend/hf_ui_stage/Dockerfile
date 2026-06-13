# syntax=docker/dockerfile:1.7
# Lightweight Streamlit UI for HF Spaces (Docker SDK, port 7860).

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    API_BASE_URL=https://prateek712-cpl-crop-disease-api.hf.space

# Non-root user (HF Spaces convention: uid 1000)
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

WORKDIR $HOME/app

COPY --chown=user:user requirements.txt ./
RUN pip install --user --upgrade pip \
 && pip install --user -r requirements.txt

COPY --chown=user:user streamlit_app.py ./

EXPOSE 7860

# NOTE: XSRF + CORS are disabled because Streamlit runs behind the HF Spaces
# reverse proxy. With XSRF protection on (the default), st.file_uploader's
# POST to /_stcore/upload_file fails the token check and returns 403, which
# the browser surfaces as "AxiosError: Request failed with status code 403".
CMD ["streamlit", "run", "streamlit_app.py", \
     "--server.port=7860", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--server.enableCORS=false", \
     "--server.enableXsrfProtection=false", \
     "--browser.gatherUsageStats=false"]

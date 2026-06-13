---
title: CPL Crop Disease UI
emoji: 🌿
colorFrom: green
colorTo: yellow
sdk: docker
app_port: 7860
pinned: false
license: mit
short_description: Streamlit demo for the CPL Crop Disease API
---

# CPL Crop Disease UI

Streamlit demo client for the **CPL Crop Disease API**.

Drop a leaf photo → see the full validation pipeline render step by step:

- Image quality gate
- YOLOv8n-seg leaf segmentation (mAP@50 = 0.95)
- Background removal + clean-leaf extraction
- EfficientNetB2 disease classification (139 classes)
- CLIP zero-shot crop verification (cross-check)
- Hierarchical bundle classifier (cross-check)
- 8-signal confidence engine + decision routing

## Companion API

This UI calls a separately-deployed FastAPI service:

> <https://huggingface.co/spaces/prateek712/cpl-crop-disease-api>

The `API_BASE_URL` is baked into the Docker image. You can override it via the sidebar input on the UI itself.

## Notes

- First request after sleep takes ~60-120s (the API Space cold-starts).
- Sleep is independent for each Space — keeping the API warm doesn't keep the UI warm and vice-versa.

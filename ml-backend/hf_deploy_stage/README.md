---
title: CPL Crop Disease API
emoji: 🌿
colorFrom: green
colorTo: yellow
sdk: docker
app_port: 7860
pinned: false
license: mit
short_description: Multi-model crop disease classifier with safety pipeline
---

# CPL Crop Disease API

Production-grade inference service for **Indian agricultural crop disease detection** (20 crops, 139 `crop::disease` classes) wrapping a fine-tuned EfficientNetB2 classifier.

## What this Space provides

A single HTTPS endpoint your frontend / mobile app can call:

```
POST  /predict-v2
GET   /health
GET   /ready
GET   /docs           ← interactive Swagger UI
```

**Pipeline per request** (image upload → JSON):
1. Quality gate (resolution / blur / brightness / contrast)
2. **YOLOv8n-seg** leaf segmentation (custom-trained, mAP@50 = 0.95)
3. Background removal + clean-leaf extraction
4. **EfficientNetB2** disease classification (139 classes)
5. **CLIP** zero-shot crop verification (cross-check)
6. **Hierarchical bundle** (B0 + crop router + 20 per-crop heads, cross-check)
7. Multi-signal confidence engine (8 signals)
8. Decision router → `high_confidence` / `expert_review` / `retake`

## Quick test

```bash
curl -X POST "https://YOUR-SPACE.hf.space/predict-v2?topk=3" \
  -F "file=@leaf.jpg;type=image/jpeg" \
  | jq
```

See [`API.md`](./API.md) for the full request/response schema and integration examples (curl, JavaScript fetch, Python httpx).

## Notes

- Free CPU Space — first request after sleep takes ~60-120s for the SavedModel + CLIP first-load.
- The B2 classifier is trained on PlantVillage-style images. On out-of-distribution field photos the validation pipeline correctly drops confidence and routes to `expert_review`.
- This Space hosts the inference endpoint only. The full project (training pipelines, MLflow, drift monitoring, Streamlit demo) lives in the parent repo.

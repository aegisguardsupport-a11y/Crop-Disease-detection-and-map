# CPL Crop Disease API — Integration Guide for Teammates

A single HTTPS endpoint your app calls with a leaf image. The API returns:

- Top-K disease predictions with confidence
- Crop-level confidence (top crops with marginalised probabilities)
- Hierarchical-bundle cross-check (separate trained classifier for crop type)
- CLIP zero-shot crop verification
- Per-stage validation (image quality, leaf segmentation, area)
- 8-signal fused confidence + decision (`high_confidence` | `expert_review` | `retake`)
- Optional Grad-CAM-style heatmap overlay
- Latency breakdown
- Mask overlay PNG + clean-leaf PNG (base64)

> **Endpoint**: `https://prateek712-cpl-crop-disease-api.hf.space`
>
> Once the Space is built and running, this URL is live and reachable from any frontend.

---

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | Liveness probe (returns instantly) |
| `GET` | `/ready` | Readiness probe (returns once models loaded) |
| `POST` | `/predict-v2` | **Main inference endpoint — use this** |
| `GET` | `/docs` | Interactive Swagger UI |
| `GET` | `/redoc` | ReDoc-rendered API documentation |
| `GET` | `/metrics` | Prometheus metrics |

---

## `POST /predict-v2`

### Request

| Part | Type | Required | Description |
|---|---|---|---|
| `file` | `file` (multipart) | yes | Leaf image. JPEG/PNG/WebP, RGB. Server caps at 2048 px max-dimension. |
| `topk` | `int` (query) | no | Top-K predictions to return. Default 3, max 10. |
| `explain` | `bool` (query) | no | Return SmoothGrad explanation overlay. Default `false`. Adds ~2-5 s latency. |

### Example responses

`high_confidence` decision (lab-style image):

```json
{
  "request_id": "f52e5eaea6204fff8e537bd1a67ef0a5",
  "decision": "high_confidence",
  "confidence": 0.91,
  "predictions": [
    { "rank": 1, "label": "tomato::Late Blight",
      "crop": "tomato", "disease": "Late Blight", "confidence": 0.94 }
  ],
  "top_crops": [
    { "rank": 1, "crop": "tomato", "confidence": 0.96,
      "top_disease": "Late Blight", "top_disease_conditional": 0.98 }
  ],
  "crop_router_predictions": [
    { "rank": 1, "crop": "tomato", "confidence": 0.92 }
  ],
  "crop_verifier_predictions": [
    { "rank": 1, "crop": "tomato", "similarity": 0.62 }
  ],
  "crop_verifier_agreement": true,
  "classifier_used": "efficientnetb2",
  "validation": {
    "image_quality": { "ok": true, "score": 0.98, "blur": 540.2,
                       "brightness": 138.4, "contrast": 51.8 },
    "leaf_segmentation": { "detected": true, "confidence": 0.93,
                           "leaf_area_ratio": 0.41 },
    "leaf_area": { "ratio": 0.41, "score": 0.95, "ok": true }
  },
  "confidence_signals": {
    "final": 0.91,
    "weights": { "quality": 0.10, "seg": 0.15, "area": 0.05,
                 "top1": 0.25, "gap": 0.10, "crop_router": 0.15,
                 "per_crop_head": 0.10, "crop_agreement": 0.10 }
  },
  "model_versions": {
    "leaf_segmenter": "cpl-leaf-yolov8n-v1",
    "disease_classifier": "0.1.0-efficientnetb2-260"
  },
  "latency": { "total_ms": 2840.5, "segmentation_ms": 410.1,
               "classification_ms": 280.6, "explain_ms": 0 },
  "mask_overlay_png_b64": "iVBORw0KGgoA...",
  "clean_leaf_png_b64": "iVBORw0KGgoA..."
}
```

### Decision routing

| Decision | Meaning | What your UI should do |
|---|---|---|
| `high_confidence` | All checks passed; top-1 prediction is reliable | Show prediction + confidence badge |
| `expert_review` | Models disagree or confidence is moderate | Show prediction *with caveats*, offer "ask an expert" CTA |
| `retake` | Image quality / leaf detection failed | Show `retake_reason`, prompt user to take a new photo |

When `decision == "retake"`, also surface `retake_reason` and `retake_guidance`.

### Error format

```json
{
  "request_id": "...",
  "detail": "Cannot decode image: ...",
  "code": "http_400"
}
```

---

## Code examples

### curl

```bash
curl -X POST "https://prateek712-cpl-crop-disease-api.hf.space/predict-v2?topk=3" \
  -F "file=@leaf.jpg;type=image/jpeg" \
  | jq
```

### JavaScript / TypeScript (browser fetch)

```typescript
async function predict(file: File) {
  const form = new FormData();
  form.append("file", file);

  const url = "https://prateek712-cpl-crop-disease-api.hf.space/predict-v2?topk=3";
  const res = await fetch(url, { method: "POST", body: form });

  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${await res.text()}`);
  }
  return res.json();
}

// Usage:
const fileInput = document.querySelector<HTMLInputElement>("#leaf-upload");
fileInput?.addEventListener("change", async (e) => {
  const file = (e.target as HTMLInputElement).files?.[0];
  if (!file) return;
  const result = await predict(file);
  console.log(result.decision, result.predictions[0]);
});
```

### React Native / Expo

```typescript
import * as FileSystem from "expo-file-system";

async function predict(localUri: string) {
  const url = "https://prateek712-cpl-crop-disease-api.hf.space/predict-v2?topk=3";
  const res = await FileSystem.uploadAsync(url, localUri, {
    httpMethod: "POST",
    uploadType: FileSystem.FileSystemUploadType.MULTIPART,
    fieldName: "file",
    mimeType: "image/jpeg",
  });
  return JSON.parse(res.body);
}
```

### Python (httpx)

```python
import httpx

with open("leaf.jpg", "rb") as f:
    files = {"file": ("leaf.jpg", f, "image/jpeg")}
    r = httpx.post(
        "https://prateek712-cpl-crop-disease-api.hf.space/predict-v2",
        params={"topk": 3, "explain": False},
        files=files,
        timeout=120.0,   # cold start can take a while
    )
    r.raise_for_status()
    body = r.json()
    print(body["decision"], body["predictions"][0]["label"])
```

### Python (requests)

```python
import requests

with open("leaf.jpg", "rb") as f:
    r = requests.post(
        "https://prateek712-cpl-crop-disease-api.hf.space/predict-v2",
        params={"topk": 3},
        files={"file": ("leaf.jpg", f, "image/jpeg")},
        timeout=120,
    )
    r.raise_for_status()
    print(r.json())
```

---

## CORS

CORS is enabled with `allow_origins=["*"]`. Any browser-based frontend can call the
endpoint without proxying. If we tighten this later you'll need to send your
frontend origin to the project lead so it can be allow-listed.

The custom header `X-Request-ID` is exposed — you can read `res.headers.get("x-request-id")` to correlate with server logs.

---

## Cold-start & sleep behaviour

The Space is on the free CPU tier:

- **First request after sleep**: takes ~60-120 s (TensorFlow + CLIP load).
- **Subsequent requests within session**: ~2-6 s per call (CPU inference).
- **Sleep**: after ~48 h of no traffic, the Space sleeps.

To keep it awake during a demo window, hit `/health` every 10-15 min (e.g. UptimeRobot or `setInterval` on a hidden iframe).

When implementing the client, **always set a generous timeout** (~120 s) on the first request and a tighter one (~30 s) on subsequent calls.

---

## Rate limits

- HF free tier doesn't enforce explicit rate limits, but the Space runs on 2 vCPU.
- Concurrent requests are queued — there's no built-in worker pool on free CPU.
- For demo: 1 request at a time is comfortable. Don't run load tests against the public Space.

---

## Versioning

Inspect `model_versions` in the response to know what classifier built each prediction:

```json
{
  "model_versions": {
    "leaf_segmenter": "cpl-leaf-yolov8n-v1",
    "disease_classifier": "0.1.0-efficientnetb2-260"
  }
}
```

If we deploy a new model, the value changes — your UI can show "Model: v0.1.0" and
warn users if they're caching old responses.

---

## Questions / issues

DM the project lead with the `request_id` from the response. We can correlate with
server logs to debug any specific call.

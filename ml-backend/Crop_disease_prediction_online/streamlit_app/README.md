# Streamlit Demo UI

A drag-and-drop frontend for the `/predict-v2` endpoint that renders the
**full validation pipeline** as a step-by-step timeline:

- Image quality (OpenCV) + per-metric values
- Leaf segmentation (YOLOv8-seg) + mask overlay thumbnail
- Leaf-area validation
- Cleaned background-removed leaf (what the classifier actually saw)
- Top-K disease predictions (table + bar chart)
- SmoothGrad explanation overlay
- Confidence-engine signal decomposition table
- Decision banner + retake guidance
- Latency breakdown + model versions
- Raw API response (debug)

## Quick start

In one terminal — start the API server:

```powershell
cd Crop_disease_prediction_online
.\.venv\Scripts\Activate.ps1
inv serve
```

In another terminal — start the UI:

```powershell
cd Crop_disease_prediction_online
.\.venv\Scripts\Activate.ps1
inv ui
```

Then open the URL Streamlit prints (typically `http://localhost:8501`).
The sidebar lets you point it at a different API URL if needed.

## Standalone install

If you want to run only the UI (e.g., on a different machine pointing
at a deployed API):

```powershell
pip install -r streamlit_app/requirements.txt
streamlit run streamlit_app/streamlit_app.py
```

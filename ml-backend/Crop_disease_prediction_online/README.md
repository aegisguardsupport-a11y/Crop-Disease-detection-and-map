# CPL Crop-Disease Prediction — MLOps Service

Production-grade serving + explainability stack around the
fine-tuned EfficientNetB2 crop-disease classifier
(139 `crop::disease` classes, 93.6% top-1 / 99.4% top-3 on test set).

## Project status

| Phase | Scope | State |
|---|---|---|
| 1 | Project skeleton, packaging, model loader, smoke test | **done** |
| 2 | FastAPI inference service with Prometheus + structured logs | **done** |
| 3 | SmoothGrad explainability via `/explain` | **done** |
| 3.5 | Validation pipeline: YOLO leaf segmenter + quality + confidence + decision router (`/predict-v2`) | **done** |
| 3.7 | CLIP zero-shot crop verifier (cross-check) | **done** |
| 3.8 | Hierarchical bundle integration (cross-check classifier) | **done** |
| 4 | Docker, docker-compose, GitHub Actions CI | **done** |
| 5 | MLflow registry + Evidently drift monitoring | **done** |

## Layout

```
.
├── exports/                       # the model bundle (extracted from zip)
│   ├── saved_model/               # TF SavedModel
│   ├── cpl_crop_disease_finetuned.tflite
│   ├── cpl_id_to_label.json
│   └── cpl_preprocessing_config.json
├── src/
│   └── cpl_crop/                  # importable Python package
│       ├── config.py              # pydantic-settings configuration
│       ├── labels.py              # label-map loader
│       ├── preprocessing.py       # PIL → numpy preprocessing
│       └── model_loader.py        # singleton SavedModel wrapper
├── tests/                         # pytest suite (incl. @slow smoke test)
├── configs/                       # per-environment env files
├── notebooks/                     # exploratory notebooks
├── pyproject.toml                 # build + tool config
├── requirements*.txt              # pinned ranges
├── Makefile / tasks.py            # task runner (Linux/Win)
└── .env.example                   # environment template
```

## Getting started (Phase 1)

The repo ships with a Python 3.12 virtualenv at `./.venv`.

```powershell
# Activate venv
.\.venv\Scripts\Activate.ps1

# Install dev dependencies
pip install -r requirements-dev.txt
pip install -e .

# Quick checks
ruff check src tests
mypy src
pytest -m "not slow"

# Full smoke test (loads the SavedModel; ~10s on CPU)
pytest -m slow -v
```

Or with the cross-platform task runner:

```powershell
inv install
inv check       # lint + typecheck + fast tests
inv smoke       # full model-loading test
```

## Model bundle

The bundle is **not** committed to git (it is large and should be
distributed via a model registry). The expected layout under `./exports/`
matches the upstream zip — see `exports/README.md` for full input/output
contract.

Input: 260×260 RGB float32, values in `[0, 255]` (no `/255` — the
EfficientNetB2 backbone has its own normalisation layer).

Output: shape `(1, 139)`, softmax probabilities over `crop::disease`
labels.

## Docker / docker-compose

The full stack (FastAPI service + Streamlit demo UI) ships as two images
behind a single `docker compose` command.

```bash
# Build and start API + UI
docker compose up --build

# Check status
docker compose ps

# Tail logs
docker compose logs -f api
docker compose logs -f ui

# Stop
docker compose down
```

After startup:
- **API**       — http://localhost:8000  (Swagger at `/docs`, ReDoc at `/redoc`, metrics at `/metrics`)
- **Streamlit** — http://localhost:8501

Notes:
- The first `docker compose up` will take a while: the API image pulls in
  TensorFlow + PyTorch + Ultralytics + Transformers (~3-4 GB final image).
- The HuggingFace model cache is persisted in a named volume
  (`hf_cache`) so CLIP doesn't re-download its 600 MB of weights on each
  restart.
- Healthcheck on the API uses `/ready` (model loaded) — first startup
  takes ~120-180s for the SavedModel + CLIP first-load.
- The UI talks to the API over the docker network as `http://api:8000`.
  The `API_BASE_URL` environment variable in `streamlit_app.py` controls
  this.

### Running just the API (no UI)

```bash
docker compose up --build api
```

### Building the API image directly

```bash
docker build -t cpl-crop-disease-api:dev .
docker run --rm -p 8000:8000 cpl-crop-disease-api:dev
```

## Continuous integration

GitHub Actions workflow at `.github/workflows/ci.yml` runs on every push
and PR:

1. **Lint** — `ruff check src tests`
2. **Format check** — `ruff format --check` (informational)
3. **Type check** — `mypy src` (strict)
4. **Fast tests** — `pytest -m "not slow"` (the slow tests load real
   models and aren't suitable for CI without GPU/large runners)

Slow tests (those that load the full TF SavedModel, YOLO weights, or
HuggingFace CLIP) run locally before pushing:

```powershell
inv check    # lint + typecheck + fast tests
pytest -m slow -v
```

## Monitoring & drift detection (Phase 5)

The service captures a small set of features for every `/predict-v2`
request (image stats, segmentation score, top-1 confidence, decision,
predicted crop, latency) into an append-only JSONL log at
`monitoring/requests.jsonl`. Two tools turn that log into operational
signal:

### MLflow model registry

Register all three models (B2 SavedModel, YOLO leaf segmenter,
hierarchical bundle) into a local file-backed MLflow tracking store:

```powershell
inv install                       # if you haven't already
python scripts/register_models.py # registers all 3 models
mlflow ui --backend-store-uri ./mlruns
# then open http://127.0.0.1:5000
```

Each run logs hyperparameters, benchmark metrics, a model-role tag
(`primary_disease_classifier` / `leaf_segmenter` /
`cross_check_classifier`), and the model artefacts. Use
`--no-artifacts` to record metadata only and skip copying the heavy
weight files.

### Evidently drift report

After the service has handled a few requests, generate an HTML drift
report comparing a reference window (the first N records) to a current
window (the rest):

```powershell
# CLI
python scripts/run_drift_report.py --ref-size 20

# Or via the API
curl -X POST "http://127.0.0.1:8000/monitoring/drift-report?ref_size=20"
# then open monitoring/drift_report.html
```

The report uses Evidently's `DataDriftPreset` over the per-request
feature columns. Useful for the demo: feed the system PlantVillage-style
images first (reference), then field photos (current), and the drift
report visualises the domain shift directly.

### Monitoring stats endpoint

```powershell
curl http://127.0.0.1:8000/monitoring/stats
```

Returns total log size, the most recent records, and a decision
breakdown.

## License

Proprietary — internal hackathon project.

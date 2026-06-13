"""Integration tests for the FastAPI app.

Marked ``@slow`` because every test in this module starts the lifespan
(which loads the SavedModel). We use a single session-scoped TestClient
so we pay the load cost once.
"""

from __future__ import annotations

import io
from collections.abc import Iterator
from pathlib import Path

import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from cpl_crop.api.app import create_app
from cpl_crop.config import Settings
from cpl_crop.model_loader import reset_bundle

pytestmark = pytest.mark.slow


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def _env(monkeypatch_module: pytest.MonkeyPatch, project_root: Path) -> None:
    """Pin Settings to the local bundle for the duration of this module."""
    monkeypatch_module.setenv("CPL_BUNDLE_DIR", str(project_root / "exports"))
    # Disable JSON logs in tests so failures show readable output.
    monkeypatch_module.setenv("CPL_API_LOG_JSON", "false")
    # Bust the cached Settings so the env vars take effect.
    from cpl_crop.config import get_settings

    get_settings.cache_clear()


@pytest.fixture(scope="module")
def monkeypatch_module() -> Iterator[pytest.MonkeyPatch]:
    mp = pytest.MonkeyPatch()
    yield mp
    mp.undo()


@pytest.fixture(scope="module")
def client(_env: None) -> Iterator[TestClient]:
    reset_bundle()
    app = create_app()
    with TestClient(app) as c:
        yield c
    reset_bundle()


@pytest.fixture
def jpeg_bytes() -> bytes:
    img = Image.new("RGB", (300, 300), color=(80, 140, 60))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


@pytest.fixture
def settings(project_root: Path) -> Settings:
    return Settings(bundle_dir=project_root / "exports", _env_file=None)  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# /health and /ready
# ---------------------------------------------------------------------------
def test_health_returns_200(client: TestClient) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"


def test_ready_reports_model_loaded(client: TestClient) -> None:
    r = client.get("/ready")
    assert r.status_code == 200
    body = r.json()
    assert body["model_loaded"] is True
    assert body["num_classes"] == 139
    assert body["model_version"]


# ---------------------------------------------------------------------------
# /predict — success paths
# ---------------------------------------------------------------------------
def test_predict_default_topk(client: TestClient, jpeg_bytes: bytes) -> None:
    r = client.post(
        "/predict",
        files={"file": ("leaf.jpg", jpeg_bytes, "image/jpeg")},
    )
    assert r.status_code == 200, r.text
    body = r.json()

    assert body["num_classes"] == 139
    assert body["model_version"]
    assert body["latency_ms"] > 0
    assert len(body["predictions"]) == 3  # default topk

    p1 = body["predictions"][0]
    assert p1["rank"] == 1
    assert "::" in p1["label"]
    assert p1["crop"]
    assert p1["disease"]
    assert 0.0 <= p1["confidence"] <= 1.0
    # Predictions must be in descending confidence order
    confidences = [p["confidence"] for p in body["predictions"]]
    assert confidences == sorted(confidences, reverse=True)


def test_predict_custom_topk(client: TestClient, jpeg_bytes: bytes) -> None:
    r = client.post(
        "/predict?topk=5",
        files={"file": ("leaf.jpg", jpeg_bytes, "image/jpeg")},
    )
    assert r.status_code == 200, r.text
    assert len(r.json()["predictions"]) == 5


# ---------------------------------------------------------------------------
# /predict — error paths
# ---------------------------------------------------------------------------
def test_predict_rejects_topk_above_max(client: TestClient, jpeg_bytes: bytes) -> None:
    r = client.post(
        "/predict?topk=999",
        files={"file": ("leaf.jpg", jpeg_bytes, "image/jpeg")},
    )
    # FastAPI Query(le=...) is not set on the route (the route enforces it
    # against settings.api_max_topk), so we expect 422 with our error envelope.
    assert r.status_code == 422
    body = r.json()
    assert body["code"] == "validation_error" or body["code"] == "http_422"


def test_predict_rejects_empty_file(client: TestClient) -> None:
    r = client.post(
        "/predict",
        files={"file": ("empty.jpg", b"", "image/jpeg")},
    )
    assert r.status_code == 400
    body = r.json()
    assert body["code"] == "http_400"


def test_predict_rejects_undecodable_bytes(client: TestClient) -> None:
    r = client.post(
        "/predict",
        files={"file": ("not-an-image.bin", b"this is not an image", "image/jpeg")},
    )
    assert r.status_code == 400


def test_predict_requires_file(client: TestClient) -> None:
    r = client.post("/predict")
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# Cross-cutting: request id, metrics
# ---------------------------------------------------------------------------
def test_predict_propagates_provided_request_id(client: TestClient, jpeg_bytes: bytes) -> None:
    rid = "test-rid-1234567890"
    r = client.post(
        "/predict",
        headers={"X-Request-ID": rid},
        files={"file": ("leaf.jpg", jpeg_bytes, "image/jpeg")},
    )
    assert r.status_code == 200
    assert r.headers.get("X-Request-ID") == rid
    assert r.json()["request_id"] == rid


def test_predict_generates_request_id_when_absent(client: TestClient, jpeg_bytes: bytes) -> None:
    r = client.post(
        "/predict",
        files={"file": ("leaf.jpg", jpeg_bytes, "image/jpeg")},
    )
    assert r.status_code == 200
    rid_header = r.headers.get("X-Request-ID")
    assert rid_header
    assert r.json()["request_id"] == rid_header
    assert len(rid_header) >= 16  # hex uuid


def test_metrics_endpoint_exposes_prometheus_format(client: TestClient) -> None:
    r = client.get("/metrics")
    assert r.status_code == 200
    body = r.text
    # Prometheus exposition format always starts with HELP/TYPE comments
    assert "# HELP" in body
    assert "# TYPE" in body


# ---------------------------------------------------------------------------
# /explain
# ---------------------------------------------------------------------------
def _decode_b64_png(b64: str) -> tuple[int, int, int]:
    """Return (H, W, channels) of a base64-encoded PNG."""
    import base64
    import io as _io

    raw = base64.b64decode(b64)
    img = Image.open(_io.BytesIO(raw))
    arr = np.asarray(img)
    return arr.shape  # type: ignore[return-value]


def test_explain_returns_predictions_and_overlay(client: TestClient, jpeg_bytes: bytes) -> None:
    r = client.post(
        "/explain?topk=3&num_samples=2&noise_level=0.05",
        files={"file": ("leaf.jpg", jpeg_bytes, "image/jpeg")},
    )
    assert r.status_code == 200, r.text
    body = r.json()

    # Top-k structure same as /predict
    assert len(body["predictions"]) == 3
    assert "::" in body["predictions"][0]["label"]
    assert 0.0 <= body["predictions"][0]["confidence"] <= 1.0

    # Explainer-specific fields
    assert body["method"] in {"saliency", "smoothgrad"}
    assert body["num_samples"] == 2
    assert body["noise_level"] == pytest.approx(0.05)

    # When target_class is omitted, the explained class should be the top-1.
    top1_label = body["predictions"][0]["label"]
    assert body["explained_class_label"] == top1_label
    assert isinstance(body["explained_class_id"], int)

    # Both PNGs decode to 260x260x3
    h_h, h_w, h_c = _decode_b64_png(body["heatmap_png_b64"])
    o_h, o_w, o_c = _decode_b64_png(body["overlay_png_b64"])
    assert (h_h, h_w, h_c) == (260, 260, 3)
    assert (o_h, o_w, o_c) == (260, 260, 3)


def test_explain_target_class_overrides_top1(client: TestClient, jpeg_bytes: bytes) -> None:
    # Pick a class that is unlikely to be top-1 on a green square
    r = client.post(
        "/explain?topk=1&num_samples=1&noise_level=0.0&target_class=42",
        files={"file": ("leaf.jpg", jpeg_bytes, "image/jpeg")},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["explained_class_id"] == 42


def test_explain_rejects_target_class_out_of_range(client: TestClient, jpeg_bytes: bytes) -> None:
    r = client.post(
        "/explain?target_class=139",
        files={"file": ("leaf.jpg", jpeg_bytes, "image/jpeg")},
    )
    assert r.status_code == 422


def test_explain_rejects_num_samples_above_max(client: TestClient, jpeg_bytes: bytes) -> None:
    r = client.post(
        "/explain?num_samples=999",
        files={"file": ("leaf.jpg", jpeg_bytes, "image/jpeg")},
    )
    assert r.status_code == 422


def test_explain_rejects_undecodable_bytes(client: TestClient) -> None:
    r = client.post(
        "/explain",
        files={"file": ("noise.bin", b"definitely not an image", "image/jpeg")},
    )
    assert r.status_code == 400


def test_explain_propagates_request_id(client: TestClient, jpeg_bytes: bytes) -> None:
    rid = "explain-rid-abcdef"
    r = client.post(
        "/explain?num_samples=1&noise_level=0.0",
        headers={"X-Request-ID": rid},
        files={"file": ("leaf.jpg", jpeg_bytes, "image/jpeg")},
    )
    assert r.status_code == 200
    assert r.headers.get("X-Request-ID") == rid
    assert r.json()["request_id"] == rid


def test_explain_predictions_match_predict(client: TestClient, jpeg_bytes: bytes) -> None:
    """Critical guarantee: /predict and /explain produce identical top-1.

    Both endpoints share the same SavedModel signature, so the top-1
    class must agree byte-for-byte on the same input.
    """
    p = client.post(
        "/predict?topk=1",
        files={"file": ("leaf.jpg", jpeg_bytes, "image/jpeg")},
    )
    e = client.post(
        "/explain?topk=1&num_samples=1&noise_level=0.0",
        files={"file": ("leaf.jpg", jpeg_bytes, "image/jpeg")},
    )
    assert p.status_code == 200 and e.status_code == 200

    p_top1 = p.json()["predictions"][0]
    e_top1 = e.json()["predictions"][0]
    assert p_top1["label"] == e_top1["label"]
    assert p_top1["confidence"] == pytest.approx(e_top1["confidence"], abs=1e-5)


# ---------------------------------------------------------------------------
# /predict-v2 (Phase 3.5 full validation pipeline)
# ---------------------------------------------------------------------------
def _yolo_weights_present() -> bool:
    return Path(__file__).resolve().parent.parent.joinpath("models", "leaf_seg", "best.pt").exists()


_skip_no_yolo = pytest.mark.skipif(
    not _yolo_weights_present(),
    reason="models/leaf_seg/best.pt not present; skipping /predict-v2 tests",
)


@_skip_no_yolo
def test_predict_v2_synthetic_image_returns_full_pipeline(
    client: TestClient, jpeg_bytes: bytes
) -> None:
    r = client.post(
        "/predict-v2?topk=3&explain=false",
        files={"file": ("leaf.jpg", jpeg_bytes, "image/jpeg")},
    )
    assert r.status_code == 200, r.text
    body = r.json()

    # Top-level fields all present
    assert body["decision"] in {"high_confidence", "expert_review", "retake"}
    assert 0.0 <= body["confidence"] <= 1.0

    # Validation report has every sub-section
    v = body["validation"]
    assert "image_quality" in v
    assert "leaf_segmentation" in v
    assert {"ok", "score", "resolution", "blur", "brightness", "contrast", "failures"} <= set(
        v["image_quality"].keys()
    )
    assert {"detected", "confidence", "num_detections", "leaf_area_ratio"} <= set(
        v["leaf_segmentation"].keys()
    )

    # Confidence signals decomposition
    cs = body["confidence_signals"]
    assert {
        "final",
        "quality_score",
        "seg_confidence",
        "leaf_area_score",
        "classifier_top1",
        "prediction_gap",
        "weights",
    } <= set(cs.keys())

    # Latency breakdown is present and reasonable
    lat = body["latency"]
    assert lat["total_ms"] > 0
    assert lat["quality_ms"] >= 0
    assert lat["segmentation_ms"] >= 0


@_skip_no_yolo
def test_predict_disease_returns_slim_advisory_payload(
    client: TestClient, project_root: Path
) -> None:
    sample = project_root / "scripts" / "wheat_test.jpg"
    if not sample.exists():
        pytest.skip("scripts/wheat_test.jpg not present")

    r = client.post(
        "/predictdisease",
        files={"file": ("wheat_test.jpg", sample.read_bytes(), "image/jpeg")},
    )
    assert r.status_code == 200, r.text
    body = r.json()

    assert set(body.keys()) == {
        "crop_name",
        "primary_diagnosis",
        "top_3_predictions",
        "possible_other_diseases",
        "severity",
        "urgency",
        "symptoms_to_confirm",
        "what_to_do_now",
        "prevention_tips",
        "when_to_call_expert",
        "retake_image_guidance",
        "rag_explanation",
    }
    assert not {"request_id", "validation", "latency", "model_versions"} & set(body.keys())

    predictions = body["top_3_predictions"]
    assert len(predictions) == 3
    for idx, pred in enumerate(predictions, start=1):
        assert pred["rank"] == idx
        assert set(pred.keys()) == {"rank", "label", "crop", "disease", "confidence"}
        assert "::" in pred["label"]
        assert pred["crop"]
        assert pred["disease"]
        assert 0.0 <= pred["confidence"] <= 1.0

    assert body["crop_name"] == predictions[0]["crop"]
    primary = body["primary_diagnosis"]
    assert set(primary.keys()) == {
        "label",
        "crop",
        "disease",
        "display_name",
        "is_healthy",
        "confidence",
        "confidence_badge",
    }
    assert primary["label"] == predictions[0]["label"]
    assert primary["crop"] == predictions[0]["crop"]
    assert primary["disease"] == predictions[0]["disease"]
    assert primary["display_name"]
    assert isinstance(primary["is_healthy"], bool)
    assert 0.0 <= primary["confidence"] <= 1.0
    assert primary["confidence_badge"] in {"High", "Medium", "Low"}

    alternatives = body["possible_other_diseases"]
    assert len(alternatives) == 2
    for alternative in alternatives:
        assert set(alternative.keys()) == {
            "rank",
            "label",
            "crop",
            "disease",
            "confidence",
            "confidence_badge",
        }
        assert alternative["rank"] in {2, 3}
        assert alternative["confidence_badge"] in {"High", "Medium", "Low"}

    severity = body["severity"]
    assert set(severity.keys()) == {"level", "confidence", "decision", "basis"}
    assert severity["level"] in {"low", "medium", "high", "unknown"}
    assert severity["decision"] in {"high_confidence", "expert_review", "retake"}
    assert 0.0 <= severity["confidence"] <= 1.0
    assert severity["basis"]

    assert body["urgency"] in {"Monitor", "Act soon", "Act immediately", "Retake image"}
    assert isinstance(body["symptoms_to_confirm"], list)
    assert isinstance(body["what_to_do_now"], list)
    assert body["what_to_do_now"]
    assert isinstance(body["prevention_tips"], list)
    assert body["prevention_tips"]
    assert body["when_to_call_expert"]

    rag = body["rag_explanation"]
    assert rag is not None
    assert set(rag.keys()) == {
        "status",
        "source",
        "summary",
        "symptoms_to_check",
        "immediate_actions",
        "precautions",
        "prevention",
        "similar_diseases",
        "expert_advice",
        "safety_note",
    }
    assert rag["summary"]


@_skip_no_yolo
def test_predict_v2_explain_true_includes_overlay_png(
    client: TestClient, jpeg_bytes: bytes
) -> None:
    r = client.post(
        "/predict-v2?topk=1&explain=true",
        files={"file": ("leaf.jpg", jpeg_bytes, "image/jpeg")},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    # If we got a high/medium decision, predictions exist and explanation should be present.
    if body["decision"] != "retake":
        assert body["explanation_overlay_png_b64"] is not None
        assert len(body["explanation_overlay_png_b64"]) > 100
        assert body["clean_leaf_png_b64"] is not None


@_skip_no_yolo
def test_predict_v2_rejects_empty_file(client: TestClient) -> None:
    r = client.post(
        "/predict-v2",
        files={"file": ("empty.jpg", b"", "image/jpeg")},
    )
    assert r.status_code == 400


@_skip_no_yolo
def test_predict_v2_rejects_undecodable_bytes(client: TestClient) -> None:
    r = client.post(
        "/predict-v2",
        files={"file": ("noise.bin", b"definitely not an image", "image/jpeg")},
    )
    assert r.status_code == 400


@_skip_no_yolo
def test_predict_v2_propagates_request_id(client: TestClient, jpeg_bytes: bytes) -> None:
    rid = "v2-rid-xyz"
    r = client.post(
        "/predict-v2?explain=false",
        headers={"X-Request-ID": rid},
        files={"file": ("leaf.jpg", jpeg_bytes, "image/jpeg")},
    )
    assert r.status_code == 200
    assert r.headers.get("X-Request-ID") == rid
    assert r.json()["request_id"] == rid


@_skip_no_yolo
def test_predict_v2_rejects_topk_above_max(client: TestClient, jpeg_bytes: bytes) -> None:
    r = client.post(
        "/predict-v2?topk=999",
        files={"file": ("leaf.jpg", jpeg_bytes, "image/jpeg")},
    )
    assert r.status_code == 422

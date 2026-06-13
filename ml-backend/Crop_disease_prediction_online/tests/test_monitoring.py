"""Fast unit tests for the monitoring package.

These do not load any models; they just exercise the feature extraction,
JSONL logger, and drift-report helpers.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cpl_crop.monitoring.drift import generate_drift_report
from cpl_crop.monitoring.features import (
    CATEGORICAL_COLUMNS,
    NUMERICAL_COLUMNS,
    RequestFeatures,
    extract_features,
)
from cpl_crop.monitoring.logger import MonitoringLogger

# ---------- features.extract_features --------------------------------------


def test_extract_features_splits_label() -> None:
    f = extract_features(
        request_id="req-1",
        image_shape=(260, 260),
        quality={"brightness": 100.0, "contrast": 50.0, "blur_score": 200.0},
        segmentation_score=0.9,
        area_fraction=0.4,
        top1_confidence=0.85,
        confidence_gap=0.6,
        fused_confidence=0.78,
        decision="high_confidence",
        top1_label="wheat::FusariumFootRot",
        crop_agreement=True,
        latency_ms=320.5,
    )
    assert isinstance(f, RequestFeatures)
    assert f.predicted_crop == "wheat"
    assert f.predicted_disease == "FusariumFootRot"
    assert f.image_height == 260
    assert f.image_width == 260
    assert f.crop_agreement is True
    # ISO timestamp ends in +00:00 or has timezone marker
    assert "T" in f.timestamp


def test_extract_features_handles_missing_separator() -> None:
    f = extract_features(
        request_id="r",
        image_shape=(100, 100),
        quality={},
        segmentation_score=0.0,
        area_fraction=0.0,
        top1_confidence=0.0,
        confidence_gap=0.0,
        fused_confidence=0.0,
        decision="retake",
        top1_label="totally_unstructured_label",
        crop_agreement=False,
        latency_ms=0.0,
    )
    assert f.predicted_crop == "unknown"
    assert f.predicted_disease == "totally_unstructured_label"
    assert f.brightness == 0.0  # default when quality dict is empty


def test_features_columns_lists_match_dataclass_fields() -> None:
    """Every numerical/categorical column name must exist on RequestFeatures."""
    field_names = set(RequestFeatures.__dataclass_fields__)
    for col in NUMERICAL_COLUMNS:
        assert col in field_names, f"NUMERICAL_COLUMNS lists '{col}' which is not on RequestFeatures"
    for col in CATEGORICAL_COLUMNS:
        assert col in field_names, f"CATEGORICAL_COLUMNS lists '{col}' which is not on RequestFeatures"


# ---------- logger ---------------------------------------------------------


def _make_record(idx: int, decision: str = "high_confidence") -> RequestFeatures:
    return extract_features(
        request_id=f"req-{idx}",
        image_shape=(260, 260),
        quality={"brightness": 100.0 + idx, "contrast": 40.0, "blur_score": 150.0},
        segmentation_score=0.8,
        area_fraction=0.3,
        top1_confidence=0.7,
        confidence_gap=0.4,
        fused_confidence=0.65,
        decision=decision,
        top1_label="rice::Brown_spot",
        crop_agreement=True,
        latency_ms=100.0 + idx,
    )


def test_logger_appends_jsonl(tmp_path: Path) -> None:
    log_path = tmp_path / "requests.jsonl"
    log = MonitoringLogger(log_path)
    log.log(_make_record(1))
    log.log(_make_record(2, decision="expert_review"))

    assert log.count() == 2
    lines = log_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    parsed = [json.loads(line) for line in lines]
    assert parsed[0]["request_id"] == "req-1"
    assert parsed[1]["decision"] == "expert_review"


def test_logger_tail_returns_recent_records(tmp_path: Path) -> None:
    log = MonitoringLogger(tmp_path / "requests.jsonl")
    for i in range(5):
        log.log(_make_record(i))
    tail = log.tail(n=3)
    assert len(tail) == 3
    assert [r["request_id"] for r in tail] == ["req-2", "req-3", "req-4"]


def test_logger_iter_records_skips_blank_lines(tmp_path: Path) -> None:
    log_path = tmp_path / "requests.jsonl"
    log_path.write_text(
        json.dumps(_make_record(0).to_dict()) + "\n\n" + json.dumps(_make_record(1).to_dict()) + "\n",
        encoding="utf-8",
    )
    log = MonitoringLogger(log_path)
    records = list(log.iter_records())
    assert len(records) == 2
    assert records[0]["request_id"] == "req-0"


def test_logger_initialises_missing_parent_dir(tmp_path: Path) -> None:
    deep = tmp_path / "nested" / "sub" / "requests.jsonl"
    log = MonitoringLogger(deep)
    log.log(_make_record(0))
    assert deep.exists()
    assert log.count() == 1


# ---------- drift report ---------------------------------------------------


def test_drift_empty_log_writes_stub(tmp_path: Path) -> None:
    out = tmp_path / "drift.html"
    result = generate_drift_report([], out)
    assert result["status"] == "empty"
    assert out.exists()
    text = out.read_text(encoding="utf-8")
    assert "No records logged yet" in text


def test_drift_insufficient_data_writes_stub(tmp_path: Path) -> None:
    out = tmp_path / "drift.html"
    records = [_make_record(i).to_dict() for i in range(3)]
    result = generate_drift_report(records, out, ref_size=20)
    assert result["status"] == "insufficient_data"
    assert out.exists()
    assert "Not enough data" in out.read_text(encoding="utf-8")


@pytest.mark.slow
def test_drift_with_enough_data_generates_html(tmp_path: Path) -> None:
    """End-to-end drift report. Marked slow because evidently is heavy to import."""
    out = tmp_path / "drift.html"
    records: list[dict] = []
    # 20 reference + 10 current with different distributions
    for i in range(20):
        rec = _make_record(i, decision="high_confidence").to_dict()
        records.append(rec)
    for i in range(10):
        rec = _make_record(i + 100, decision="expert_review").to_dict()
        # Skew the brightness so drift is detectable
        rec["brightness"] = float(rec["brightness"] + 80.0)
        rec["top1_confidence"] = 0.3
        records.append(rec)

    result = generate_drift_report(records, out, ref_size=20)
    assert result["status"] == "ok"
    assert result["ref_rows"] == 20
    assert result["cur_rows"] == 10
    assert out.exists()
    # Evidently writes a real HTML doc, not a stub
    text = out.read_text(encoding="utf-8")
    assert "<html" in text.lower()
    # Stub message is absent
    assert "No records logged yet" not in text

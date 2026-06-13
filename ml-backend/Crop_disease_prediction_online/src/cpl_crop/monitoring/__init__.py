"""Monitoring package: per-request feature logging + drift detection.

The runtime exposes :class:`MonitoringLogger` which appends a small,
flat JSONL record for every ``/predict-v2`` request. The
``scripts/run_drift_report.py`` helper turns those records into an
Evidently HTML report comparing a reference window (the first N
records the system ever saw) to a current window (the rest).
"""

from cpl_crop.monitoring.features import RequestFeatures, extract_features
from cpl_crop.monitoring.logger import MonitoringLogger

__all__ = ["MonitoringLogger", "RequestFeatures", "extract_features"]

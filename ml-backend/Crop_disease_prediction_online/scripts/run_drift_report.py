"""Generate an Evidently drift report from the monitoring log.

Usage:

    python scripts/run_drift_report.py
    python scripts/run_drift_report.py --ref-size 30 --out custom.html

Defaults are pulled from the project ``Settings`` (env-prefix ``CPL_``).
The HTML output can be opened directly in a browser.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from cpl_crop.config import get_settings  # noqa: E402
from cpl_crop.monitoring.drift import generate_drift_report  # noqa: E402
from cpl_crop.monitoring.logger import MonitoringLogger  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    settings = get_settings()
    parser.add_argument(
        "--log",
        type=Path,
        default=settings.monitoring_log_path,
        help=f"Path to the JSONL monitoring log (default: {settings.monitoring_log_path}).",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=settings.monitoring_drift_report_path,
        help=f"Output HTML path (default: {settings.monitoring_drift_report_path}).",
    )
    parser.add_argument(
        "--ref-size",
        type=int,
        default=settings.monitoring_drift_ref_size,
        help=f"Number of leading records to use as the reference window (default: {settings.monitoring_drift_ref_size}).",
    )
    args = parser.parse_args()

    log_logger = MonitoringLogger(args.log)
    records = list(log_logger.iter_records())
    print(f"[drift] loaded {len(records)} records from {args.log}")

    result = generate_drift_report(records, args.out, ref_size=args.ref_size)
    print(f"[drift] status={result['status']}  ref_rows={result['ref_rows']}  cur_rows={result['cur_rows']}")
    print(f"[drift] wrote {result['out_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

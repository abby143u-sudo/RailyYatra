from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
APP_DIR = REPO_ROOT / "app"
sys.path.insert(0, str(APP_DIR))

from backend.ingestion import (  # noqa: E402
    IngestionInspectionError,
    inspect_raw_railway_data,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect RailYatra raw railway data without writing to SQLite."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Inspect raw data without database writes (default and only mode).",
    )
    parser.add_argument(
        "--report-json",
        action="store_true",
        help="Print the dry-run report as JSON.",
    )
    return parser.parse_args()


def build_cli_report(inspection: dict[str, Any]) -> dict[str, Any]:
    raw_dir = Path(inspection["raw_dir"])
    issues = inspection["issues"]

    return {
        "mode": "dry-run",
        "raw_files": {
            "stations": str(raw_dir / "stations.json"),
            "trains": str(raw_dir / "trains.json"),
            "schedules": str(raw_dir / "schedules.json"),
        },
        "counts": inspection["counts"],
        "issues": {
            "stations_missing_coordinates": issues["stations_missing_coordinates"],
            "stations_missing_state": issues["stations_missing_state"],
            "trains_missing_source": issues["trains_missing_source"],
            "trains_missing_destination": issues["trains_missing_destination"],
        },
        "database_write_skipped": True,
    }


def format_text_report(report: dict[str, Any]) -> str:
    files = report["raw_files"]
    counts = report["counts"]
    issues = report["issues"]

    return "\n".join(
        [
            "RailYatra railway data import CLI",
            "Mode: dry-run (read-only)",
            "Raw files used:",
            f"  stations: {files['stations']}",
            f"  trains: {files['trains']}",
            f"  schedules: {files['schedules']}",
            "Counts:",
            f"  stations: {counts['stations']}",
            f"  trains: {counts['trains']}",
            f"  schedules/stops: {counts['schedules_or_stops']}",
            "Data quality issues:",
            "  missing station coordinates: "
            f"{issues['stations_missing_coordinates']}",
            f"  missing station state: {issues['stations_missing_state']}",
            f"  trains missing source: {issues['trains_missing_source']}",
            "  trains missing destination: "
            f"{issues['trains_missing_destination']}",
            "Database write skipped: yes",
        ]
    )


def main() -> int:
    args = parse_args()

    try:
        inspection = inspect_raw_railway_data()
    except IngestionInspectionError as exc:
        if args.report_json:
            print(
                json.dumps(
                    {
                        "mode": "dry-run",
                        "database_write_skipped": True,
                        "error": str(exc),
                    },
                    indent=2,
                ),
                file=sys.stderr,
            )
        else:
            print(f"FAIL: railway data inspection failed: {exc}", file=sys.stderr)
        return 1

    report = build_cli_report(inspection)

    if args.report_json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(format_text_report(report))
        print("PASS: dry-run inspection completed without database writes")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

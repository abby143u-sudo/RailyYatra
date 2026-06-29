from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
APP_DIR = REPO_ROOT / "app"
sys.path.insert(0, str(APP_DIR))

from backend.ingestion import (  # noqa: E402
    IngestionInspectionError,
    format_inspection_report,
    inspect_raw_railway_data,
)


def main() -> int:
    try:
        report = inspect_raw_railway_data()
    except IngestionInspectionError as exc:
        print(f"FAIL: railway data inspection failed: {exc}", file=sys.stderr)
        return 1

    print(format_inspection_report(report))
    print("PASS: required raw railway files are readable and contain records")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

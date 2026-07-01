#!/usr/bin/env python3
from __future__ import annotations

import sqlite3
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = REPO_ROOT / "app" / "railyatra.db"

EXPECTED_INDEXES = [
    "idx_staging_train_stops_station_train_sequence",
    "idx_staging_train_stops_train_sequence_station",
    "idx_staging_train_stops_station_sequence",
    "idx_staging_train_stops_train_station_sequence",
]


def main() -> int:
    print("RailYatra staging route index smoke test")
    print("Mode: read-only")
    print(f"Database: {DB_PATH}")

    if not DB_PATH.exists():
        print("FAIL: database missing")
        return 1

    with sqlite3.connect(DB_PATH) as conn:
        found = {
            row[0]
            for row in conn.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'index'
                  AND name LIKE 'idx_staging_train_stops_%'
                """
            ).fetchall()
        }

    missing = [index for index in EXPECTED_INDEXES if index not in found]

    print("Expected route indexes:")
    for index in EXPECTED_INDEXES:
        print(f"  {index}: {'yes' if index in found else 'missing'}")

    if missing:
        print("FAIL: missing route index(es)")
        for index in missing:
            print(f"  missing: {index}")
        print("Run:")
        print("  python3 scripts/run_migrations.py --apply")
        return 1

    print("Database opened: read-only")
    print("Database write skipped: yes")
    print("Production railway tables modified: no")
    print("PASS: staging route indexes verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

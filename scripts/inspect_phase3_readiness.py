#!/usr/bin/env python3
from __future__ import annotations

import sqlite3
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = REPO_ROOT / "app" / "railyatra.db"
BACKEND_API = REPO_ROOT / "app" / "backend" / "api" / "main.py"

REQUIRED_STAGING_TABLES = [
    "staging_stations",
    "staging_trains",
    "staging_train_stops",
]

EXPECTED_MIN_COUNTS = {
    "staging_stations": 8000,
    "staging_trains": 5000,
    "staging_train_stops": 400000,
}


def table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table,),
    ).fetchone()
    return row is not None


def table_count(conn: sqlite3.Connection, table: str) -> int:
    return int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])


def inspect_backend_api() -> dict[str, bool]:
    text = BACKEND_API.read_text(encoding="utf-8")

    return {
        "has_search_endpoint": "/search" in text or "def search" in text,
        "has_direct_endpoint": "/direct" in text or "def direct" in text,
        "has_transfer_endpoint": "/transfer" in text or "def transfer" in text,
        "mentions_staging_tables": "staging_" in text,
        "mentions_train_stops": "train_stops" in text,
        "mentions_sqlite": "sqlite" in text.lower() or "sqlite3" in text,
    }


def main() -> int:
    print("RailYatra Phase 3 readiness inspector")
    print("Mode: read-only")
    print(f"Database: {DB_PATH}")
    print(f"Backend API: {BACKEND_API}")

    if not DB_PATH.exists():
        print("FAIL: database missing")
        return 1

    if not BACKEND_API.exists():
        print("FAIL: backend API file missing")
        return 1

    with sqlite3.connect(DB_PATH) as conn:
        missing_tables = [
            table for table in REQUIRED_STAGING_TABLES
            if not table_exists(conn, table)
        ]

        if missing_tables:
            print("FAIL: missing staging table(s)")
            for table in missing_tables:
                print(f"  missing: {table}")
            return 1

        print("Staging table counts:")
        count_failures = []

        for table in REQUIRED_STAGING_TABLES:
            count = table_count(conn, table)
            minimum = EXPECTED_MIN_COUNTS[table]
            print(f"  {table}: {count}")

            if count < minimum:
                count_failures.append(f"{table} has {count}, expected at least {minimum}")

        if count_failures:
            print("FAIL: staging data not ready")
            for failure in count_failures:
                print(f"  {failure}")
            print("Run this if staging rows are missing:")
            print("  python3 scripts/apply_staging_import.py --apply --confirm-staging-write")
            return 1

    backend = inspect_backend_api()

    print("Backend search/graph status:")
    for key, value in backend.items():
        print(f"  {key}: {'yes' if value else 'no'}")

    if backend["mentions_staging_tables"]:
        print("Phase 3 integration status: backend already references staging tables")
    else:
        print("Phase 3 integration status: backend does not yet reference staging tables")

    print("Database opened: read-only inspection")
    print("Database write skipped: yes")
    print("Production railway tables modified: no")
    print("PASS: Phase 3 readiness inspection completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

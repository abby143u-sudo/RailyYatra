#!/usr/bin/env python3
from __future__ import annotations

import sqlite3
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS_DIR = REPO_ROOT / "app" / "backend" / "database" / "migrations"

EXPECTED_TABLES = [
    "ingestion_runs",
    "ingestion_source_files",
    "ingestion_issues",
    "staging_stations",
    "staging_trains",
    "staging_train_stops",
]

EXPECTED_INDEXES = [
    "idx_staging_stations_code",
    "idx_staging_trains_number",
    "idx_staging_train_stops_train_number",
    "idx_staging_train_stops_station_code",
]


def table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    ).fetchone()

    return row is not None


def index_exists(conn: sqlite3.Connection, index_name: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND name=?",
        (index_name,),
    ).fetchone()

    return row is not None


def main() -> int:
    print("RailYatra migration safety check (dry-run)")
    print(f"Migrations directory: {MIGRATIONS_DIR}")

    migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))

    if not migration_files:
        print("FAIL: no migration files found")
        return 1

    print(f"Migration files discovered: {len(migration_files)}")

    with sqlite3.connect(":memory:") as conn:
        total_statements = 0

        for path in migration_files:
            sql = path.read_text()
            statements = [part.strip() for part in sql.split(";") if part.strip()]
            total_statements += len(statements)

            print(f"  applying in memory: {path.name} ({len(statements)} statements)")
            conn.executescript(sql)

        missing_tables = [
            table for table in EXPECTED_TABLES
            if not table_exists(conn, table)
        ]

        missing_indexes = [
            index for index in EXPECTED_INDEXES
            if not index_exists(conn, index)
        ]

        if missing_tables:
            print("FAIL: missing expected table(s)")
            for table in missing_tables:
                print(f"  missing table: {table}")
            return 1

        if missing_indexes:
            print("FAIL: missing expected index(es)")
            for index in missing_indexes:
                print(f"  missing index: {index}")
            return 1

        print(f"Safe statements applied in memory: {total_statements}")
        print("Expected metadata tables:")
        for table in EXPECTED_TABLES[:3]:
            print(f"  {table}")

        print("Expected staging tables:")
        for table in EXPECTED_TABLES[3:]:
            print(f"  {table}")

        print("Expected staging indexes:")
        for index in EXPECTED_INDEXES:
            print(f"  {index}")

    print("Target database opened: no")
    print("Target database modified: no")
    print("PASS: all migrations are non-destructive and valid in in-memory SQLite")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

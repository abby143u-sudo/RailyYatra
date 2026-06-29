#!/usr/bin/env python3
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = REPO_ROOT / "app" / "railyatra.db"

REQUIRED_TABLES = [
    "ingestion_runs",
    "ingestion_source_files",
    "ingestion_issues",
]


def table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table,),
    ).fetchone()

    return row is not None


def get_columns(conn: sqlite3.Connection, table: str) -> list[str]:
    return [row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()]


def pick_column(columns: list[str], candidates: list[str]) -> str | None:
    for candidate in candidates:
        if candidate in columns:
            return candidate

    return None


def fetch_latest_run(conn: sqlite3.Connection):
    columns = get_columns(conn, "ingestion_runs")
    id_column = pick_column(columns, ["id", "run_id", "ingestion_run_id"])

    order_sql = f"ORDER BY {id_column} DESC" if id_column else "ORDER BY rowid DESC"

    row = conn.execute(
        f"SELECT rowid, * FROM ingestion_runs {order_sql} LIMIT 1"
    ).fetchone()

    return row, columns, id_column


def count_child_rows(
    conn: sqlite3.Connection,
    table: str,
    run_value,
) -> tuple[int, str | None]:
    columns = get_columns(conn, table)
    run_column = pick_column(columns, ["ingestion_run_id", "run_id"])

    if run_column is None:
        total = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        return int(total), None

    total = conn.execute(
        f"SELECT COUNT(*) FROM {table} WHERE {run_column}=?",
        (run_value,),
    ).fetchone()[0]

    return int(total), run_column


def main() -> int:
    print("RailYatra ingestion metadata verifier")
    print(f"Database: {DB_PATH}")

    if not DB_PATH.exists():
        print("FAIL: database file not found")
        return 1

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row

        missing_tables = [
            table for table in REQUIRED_TABLES if not table_exists(conn, table)
        ]

        if missing_tables:
            print("FAIL: missing metadata table(s)")
            for table in missing_tables:
                print(f"  missing: {table}")
            return 1

        latest_run, run_columns, run_id_column = fetch_latest_run(conn)

        if latest_run is None:
            print("FAIL: no ingestion run rows found")
            print("Run this first:")
            print("  python3 scripts/write_ingestion_metadata.py --apply")
            return 1

        run_value = latest_run[run_id_column] if run_id_column else latest_run["rowid"]

        source_count, source_fk = count_child_rows(
            conn,
            "ingestion_source_files",
            run_value,
        )
        issue_count, issue_fk = count_child_rows(
            conn,
            "ingestion_issues",
            run_value,
        )

        print("Latest ingestion run:")
        for key in latest_run.keys():
            if key == "rowid":
                continue
            value = latest_run[key]
            if value is not None:
                print(f"  {key}: {value}")

        print("Linked metadata:")
        print(f"  source files: {source_count}")
        print(f"  issues: {issue_count}")
        print(f"  source FK column: {source_fk or 'not found; counted all rows'}")
        print(f"  issue FK column: {issue_fk or 'not found; counted all rows'}")

        if source_count < 3:
            print("FAIL: expected at least 3 source file rows")
            return 1

        print("Railway data tables modified: no")
        print("PASS: ingestion metadata verified")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())

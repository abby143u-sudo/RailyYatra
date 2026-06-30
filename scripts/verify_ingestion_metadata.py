#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = REPO_ROOT / "app" / "railyatra.db"
MIGRATIONS_DIR = REPO_ROOT / "app" / "backend" / "database" / "migrations"

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


def apply_metadata_migrations_in_memory() -> tuple[bool, str]:
    migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))

    if not migration_files:
        return False, f"no migration files found in {MIGRATIONS_DIR}"

    try:
        with sqlite3.connect(":memory:") as conn:
            for path in migration_files:
                sql = path.read_text()
                conn.executescript(sql)

            missing_tables = [
                table for table in REQUIRED_TABLES
                if not table_exists(conn, table)
            ]

            if missing_tables:
                return False, "missing metadata table(s): " + ", ".join(missing_tables)

            for table in REQUIRED_TABLES:
                columns = get_columns(conn, table)
                if not columns:
                    return False, f"metadata table has no columns: {table}"

        return True, f"metadata schema valid across {len(migration_files)} migration file(s)"

    except sqlite3.Error as error:
        return False, f"in-memory metadata verification failed: {error}"


def verify_dry_run() -> int:
    print("RailYatra ingestion metadata verifier")
    print("Mode: dry-run")
    print(f"Migrations directory: {MIGRATIONS_DIR}")

    ok, message = apply_metadata_migrations_in_memory()

    if not ok:
        print(f"FAIL: {message}")
        return 1

    print(f"PASS: {message}")
    print("Database opened: no")
    print("Database write skipped: yes")
    print("Railway data tables modified: no")
    print("PASS: ingestion metadata verifier dry-run completed")
    return 0


def verify_live_database() -> int:
    print("RailYatra ingestion metadata verifier")
    print("Mode: live database check")
    print(f"Database: {DB_PATH}")

    if not DB_PATH.exists():
        print("FAIL: database file not found")
        return 1

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row

        missing_tables = [
            table for table in REQUIRED_TABLES
            if not table_exists(conn, table)
        ]

        if missing_tables:
            print("FAIL: missing metadata table(s)")
            for table in missing_tables:
                print(f"  missing: {table}")
            return 1

        run_columns = get_columns(conn, "ingestion_runs")
        id_column = pick_column(run_columns, ["id", "run_id", "ingestion_run_id"])
        order_sql = f"ORDER BY {id_column} DESC" if id_column else "ORDER BY rowid DESC"

        latest_run = conn.execute(
            f"SELECT rowid, * FROM ingestion_runs {order_sql} LIMIT 1"
        ).fetchone()

        if latest_run is None:
            print("FAIL: no ingestion run rows found")
            print("Run this first:")
            print("  python3 scripts/write_ingestion_metadata.py --apply")
            return 1

        run_value = latest_run[id_column] if id_column else latest_run["rowid"]

        source_columns = get_columns(conn, "ingestion_source_files")
        issue_columns = get_columns(conn, "ingestion_issues")

        source_fk = pick_column(source_columns, ["ingestion_run_id", "run_id"])
        issue_fk = pick_column(issue_columns, ["ingestion_run_id", "run_id"])

        if source_fk:
            source_count = conn.execute(
                f"SELECT COUNT(*) FROM ingestion_source_files WHERE {source_fk}=?",
                (run_value,),
            ).fetchone()[0]
        else:
            source_count = conn.execute(
                "SELECT COUNT(*) FROM ingestion_source_files"
            ).fetchone()[0]

        if issue_fk:
            issue_count = conn.execute(
                f"SELECT COUNT(*) FROM ingestion_issues WHERE {issue_fk}=?",
                (run_value,),
            ).fetchone()[0]
        else:
            issue_count = conn.execute(
                "SELECT COUNT(*) FROM ingestion_issues"
            ).fetchone()[0]

        print("Latest ingestion run found: yes")
        print(f"Linked source file rows: {source_count}")
        print(f"Linked issue rows: {issue_count}")
        print(f"source FK column: {source_fk or 'not found; counted all rows'}")
        print(f"issue FK column: {issue_fk or 'not found; counted all rows'}")

        if source_count < 3:
            print("FAIL: expected at least 3 source file rows")
            return 1

        print("Railway data tables modified: no")
        print("PASS: ingestion metadata verified")
        return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify RailYatra ingestion metadata safely."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate metadata schema in memory without opening or writing project database.",
    )

    args = parser.parse_args()

    if args.dry_run:
        return verify_dry_run()

    return verify_live_database()


if __name__ == "__main__":
    raise SystemExit(main())

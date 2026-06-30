#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sqlite3
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = REPO_ROOT / "app" / "railyatra.db"
MIGRATIONS_DIR = REPO_ROOT / "app" / "backend" / "database" / "migrations"

ALLOWED_PREFIXES = ("ingestion_", "staging_")
ALLOWED_INDEX_PREFIXES = ("idx_ingestion_", "idx_staging_")
BLOCKED_WORDS = ("DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE", "REPLACE")


def split_statements(sql: str) -> list[str]:
    statements = []

    for part in sql.split(";"):
        statement = part.strip()

        if not statement:
            continue

        cleaned_lines = []
        for line in statement.splitlines():
            stripped = line.strip()
            if stripped.startswith("--"):
                continue
            cleaned_lines.append(line)

        cleaned = "\n".join(cleaned_lines).strip()

        if cleaned:
            statements.append(cleaned)

    return statements


def table_name_from_create_table(statement: str) -> str | None:
    match = re.search(
        r"CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS\s+([A-Za-z_][A-Za-z0-9_]*)",
        statement,
        re.IGNORECASE,
    )

    return match.group(1) if match else None


def index_info_from_create_index(statement: str) -> tuple[str, str] | None:
    match = re.search(
        r"CREATE\s+INDEX\s+IF\s+NOT\s+EXISTS\s+([A-Za-z_][A-Za-z0-9_]*)\s+ON\s+([A-Za-z_][A-Za-z0-9_]*)",
        statement,
        re.IGNORECASE,
    )

    if not match:
        return None

    return match.group(1), match.group(2)


def validate_statement(statement: str) -> tuple[bool, str]:
    upper = statement.upper()

    for blocked in BLOCKED_WORDS:
        if re.search(rf"\b{blocked}\b", upper):
            return False, f"blocked SQL keyword found: {blocked}"

    table_name = table_name_from_create_table(statement)

    if table_name:
        if not table_name.startswith(ALLOWED_PREFIXES):
            return False, f"table must use ingestion_ or staging_ prefix: {table_name}"
        return True, f"CREATE TABLE {table_name}"

    index_info = index_info_from_create_index(statement)

    if index_info:
        index_name, table_name = index_info

        if not index_name.startswith(ALLOWED_INDEX_PREFIXES):
            return False, f"index must use idx_ingestion_ or idx_staging_ prefix: {index_name}"

        if not table_name.startswith(ALLOWED_PREFIXES):
            return False, f"index target table must use ingestion_ or staging_ prefix: {table_name}"

        return True, f"CREATE INDEX {index_name}"

    return False, "only CREATE TABLE IF NOT EXISTS and CREATE INDEX IF NOT EXISTS are allowed"


def discover_migrations() -> list[Path]:
    if not MIGRATIONS_DIR.exists():
        return []

    return sorted(MIGRATIONS_DIR.glob("*.sql"))


def validate_migration(path: Path) -> tuple[bool, list[str], list[str]]:
    sql = path.read_text()
    statements = split_statements(sql)
    ok_messages = []
    errors = []

    if not statements:
        errors.append("migration has no SQL statements")
        return False, ok_messages, errors

    for statement in statements:
        ok, message = validate_statement(statement)

        if ok:
            ok_messages.append(message)
        else:
            errors.append(message)

    return not errors, ok_messages, errors


def backup_database() -> int:
    backup_script = REPO_ROOT / "scripts" / "backup_database.py"

    if not backup_script.exists():
        print(f"FAIL: backup script missing: {backup_script}")
        return 1

    result = subprocess.run(
        [sys.executable, str(backup_script)],
        cwd=REPO_ROOT,
        text=True,
    )

    return result.returncode


def run_dry_run() -> int:
    migrations = discover_migrations()

    print("RailYatra migration runner")
    print("Mode: dry-run")
    print(f"Discovered migration files: {len(migrations)}")

    if not migrations:
        print("FAIL: no migration files found")
        return 1

    total_statements = 0

    for path in migrations:
        ok, ok_messages, errors = validate_migration(path)
        total_statements += len(ok_messages)

        if not ok:
            for error in errors:
                print(f"FAIL: {path.name} {error}")
            return 1

        print(f"  SAFE: {path} ({len(ok_messages)} statements)")

    print("Database opened: no")
    print("Database write skipped: yes")
    print(f"Safe statements: {total_statements}")
    print("PASS: all migrations are safe; dry-run completed")
    return 0


def run_apply() -> int:
    migrations = discover_migrations()

    print("RailYatra migration runner")
    print("Mode: apply")
    print(f"Discovered migration files: {len(migrations)}")

    if not migrations:
        print("FAIL: no migration files found")
        return 1

    for path in migrations:
        ok, ok_messages, errors = validate_migration(path)

        if not ok:
            for error in errors:
                print(f"FAIL: {path.name} {error}")
            return 1

        print(f"  SAFE: {path} ({len(ok_messages)} statements)")

    print("Creating backup before applying migrations...")
    backup_code = backup_database()

    if backup_code != 0:
        print("FAIL: backup failed; migrations not applied")
        return backup_code

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("BEGIN")

        for path in migrations:
            sql = path.read_text()
            conn.executescript(sql)
            print(f"Applied: {path.name}")

        conn.commit()

    print("Database write completed: metadata/staging schema only")
    print("PASS: migrations applied safely")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Run safe RailYatra SQLite migrations.")
    parser.add_argument("--dry-run", action="store_true", help="Validate migrations without opening or writing the database.")
    parser.add_argument("--apply", action="store_true", help="Apply safe migrations after backup.")

    args = parser.parse_args()

    if args.dry_run and args.apply:
        print("FAIL: choose either --dry-run or --apply, not both")
        return 2

    if args.apply:
        return run_apply()

    return run_dry_run()


if __name__ == "__main__":
    raise SystemExit(main())

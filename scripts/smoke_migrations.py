from __future__ import annotations

import re
import sqlite3
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
APP_DIR = REPO_ROOT / "app"
sys.path.insert(0, str(APP_DIR))

from backend.database.migrations import get_migration_path  # noqa: E402


EXPECTED_TABLES = {
    "ingestion_runs",
    "ingestion_source_files",
    "ingestion_issues",
}

CREATE_TABLE_PATTERN = re.compile(
    r"^CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(",
    re.IGNORECASE | re.DOTALL,
)

FORBIDDEN_PATTERN = re.compile(
    r"\b(DROP|ALTER|DELETE|UPDATE|INSERT|REPLACE|TRUNCATE|ATTACH|DETACH|"
    r"VACUUM|REINDEX)\b",
    re.IGNORECASE,
)


def load_migration_sql(path: Path) -> str:
    if not path.is_file():
        raise RuntimeError(f"migration file is missing: {path}")

    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise RuntimeError(f"could not read migration file: {exc}") from exc


def validate_statements(sql: str) -> list[str]:
    if FORBIDDEN_PATTERN.search(sql):
        token = FORBIDDEN_PATTERN.search(sql).group(1).upper()
        raise RuntimeError(f"forbidden SQL operation found: {token}")

    statements = [statement.strip() for statement in sql.split(";") if statement.strip()]
    if not statements:
        raise RuntimeError("migration contains no SQL statements")

    table_names = []
    for statement in statements:
        match = CREATE_TABLE_PATTERN.match(statement)
        if not match:
            raise RuntimeError(
                "every migration statement must start with CREATE TABLE IF NOT EXISTS"
            )
        table_names.append(match.group(1))

    discovered_tables = set(table_names)
    if discovered_tables != EXPECTED_TABLES:
        raise RuntimeError(
            "migration table set does not match expected metadata tables: "
            f"{sorted(discovered_tables)}"
        )

    if len(table_names) != len(discovered_tables):
        raise RuntimeError("migration defines a metadata table more than once")

    return table_names


def verify_in_memory(sql: str) -> set[str]:
    connection = sqlite3.connect(":memory:")

    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(sql)
        rows = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    except sqlite3.Error as exc:
        raise RuntimeError(f"migration failed against in-memory SQLite: {exc}") from exc
    finally:
        connection.close()

    return {row[0] for row in rows if not row[0].startswith("sqlite_")}


def main() -> int:
    migration_path = get_migration_path()

    try:
        sql = load_migration_sql(migration_path)
        declared_tables = validate_statements(sql)
        in_memory_tables = verify_in_memory(sql)

        if in_memory_tables != EXPECTED_TABLES:
            raise RuntimeError(
                "in-memory migration produced an unexpected table set: "
                f"{sorted(in_memory_tables)}"
            )
    except RuntimeError as exc:
        print(f"FAIL: migration safety check failed: {exc}", file=sys.stderr)
        return 1

    print("RailYatra migration safety check (dry-run)")
    print(f"Migration file: {migration_path}")
    print(f"Safe statements: {len(declared_tables)}")
    print("Metadata tables:")
    for table_name in declared_tables:
        print(f"  {table_name}")
    print("Target database opened: no")
    print("Target database modified: no")
    print("PASS: migration is non-destructive and valid in in-memory SQLite")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

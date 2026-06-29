from __future__ import annotations

import argparse
import re
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
APP_DIR = REPO_ROOT / "app"
sys.path.insert(0, str(APP_DIR))

from backend.database.connection import get_database_path  # noqa: E402
from backend.database.migrations import MIGRATIONS_DIR  # noqa: E402
from backup_database import create_backup, verify_backup  # noqa: E402


FORBIDDEN_PATTERN = re.compile(
    r"\b(DROP|DELETE|UPDATE|INSERT|ALTER|TRUNCATE|REPLACE)\b",
    re.IGNORECASE,
)
CREATE_TABLE_PATTERN = re.compile(
    r"^CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS\s+"
    r"([A-Za-z_][A-Za-z0-9_]*)\s*\(",
    re.IGNORECASE | re.DOTALL,
)
CREATE_INDEX_PATTERN = re.compile(
    r"^CREATE\s+INDEX\s+IF\s+NOT\s+EXISTS\s+"
    r"([A-Za-z_][A-Za-z0-9_]*)\s+ON\s+"
    r"([A-Za-z_][A-Za-z0-9_]*)\s*\(",
    re.IGNORECASE | re.DOTALL,
)
METADATA_PREFIX = "ingestion_"


@dataclass(frozen=True)
class MigrationPlan:
    path: Path
    statements: list[str]
    objects: list[tuple[str, str]]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect or apply approved non-destructive RailYatra migrations."
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate migrations without opening the target database (default).",
    )
    mode.add_argument(
        "--apply",
        action="store_true",
        help="Back up the database and apply safe migrations transactionally.",
    )
    return parser.parse_args()


def discover_migrations() -> list[Path]:
    if not MIGRATIONS_DIR.is_dir():
        raise RuntimeError(f"migration directory is missing: {MIGRATIONS_DIR}")

    migrations = sorted(MIGRATIONS_DIR.glob("*.sql"))
    if not migrations:
        raise RuntimeError(f"no SQL migrations found in {MIGRATIONS_DIR}")

    return migrations


def validate_migration(path: Path) -> MigrationPlan:
    try:
        sql = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise RuntimeError(f"could not read {path}: {exc}") from exc

    forbidden = FORBIDDEN_PATTERN.search(sql)
    if forbidden:
        raise RuntimeError(
            f"{path.name} contains forbidden SQL operation: {forbidden.group(1).upper()}"
        )

    statements = [statement.strip() for statement in sql.split(";") if statement.strip()]
    if not statements:
        raise RuntimeError(f"{path.name} contains no SQL statements")

    objects = []
    for statement in statements:
        table_match = CREATE_TABLE_PATTERN.match(statement)
        if table_match:
            table_name = table_match.group(1)
            require_metadata_name(path, table_name, "table")
            objects.append(("table", table_name))
            continue

        index_match = CREATE_INDEX_PATTERN.match(statement)
        if index_match:
            index_name, table_name = index_match.groups()
            require_metadata_name(path, index_name, "index")
            require_metadata_name(path, table_name, "index target table")
            objects.append(("index", index_name))
            continue

        raise RuntimeError(
            f"{path.name} contains unsupported SQL; only CREATE TABLE IF NOT EXISTS "
            "and CREATE INDEX IF NOT EXISTS are allowed"
        )

    return MigrationPlan(path=path, statements=statements, objects=objects)


def require_metadata_name(path: Path, name: str, object_type: str) -> None:
    if not name.lower().startswith(METADATA_PREFIX):
        raise RuntimeError(
            f"{path.name} {object_type} must use the '{METADATA_PREFIX}' prefix: {name}"
        )


def apply_migrations(plans: list[MigrationPlan]) -> tuple[Path, int]:
    backup_path = create_backup()
    verify_backup(backup_path)

    database_path = get_database_path()
    connection = sqlite3.connect(database_path)
    statement_count = 0

    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("BEGIN IMMEDIATE")

        for plan in plans:
            for statement in plan.statements:
                connection.execute(statement)
                statement_count += 1

        connection.commit()
    except sqlite3.Error as exc:
        if connection.in_transaction:
            connection.rollback()
        raise RuntimeError(f"migration transaction failed and was rolled back: {exc}") from exc
    finally:
        connection.close()

    verify_applied_objects(database_path, plans)
    return backup_path, statement_count


def verify_applied_objects(database_path: Path, plans: list[MigrationPlan]) -> None:
    expected = {item for plan in plans for item in plan.objects}
    connection = sqlite3.connect(f"{database_path.resolve().as_uri()}?mode=ro", uri=True)

    try:
        rows = connection.execute(
            "SELECT type, name FROM sqlite_master WHERE type IN ('table', 'index')"
        ).fetchall()
    finally:
        connection.close()

    existing = {(object_type, name) for object_type, name in rows}
    missing = sorted(expected - existing)
    if missing:
        raise RuntimeError(f"applied migration objects are missing: {missing}")


def main() -> int:
    args = parse_args()
    apply_requested = bool(args.apply)
    mode = "apply" if apply_requested else "dry-run"

    print("RailYatra migration runner")
    print(f"Mode: {mode}")

    try:
        migration_paths = discover_migrations()
        print(f"Discovered migration files: {len(migration_paths)}")

        plans = []
        for path in migration_paths:
            plan = validate_migration(path)
            plans.append(plan)
            print(f"  SAFE: {path} ({len(plan.statements)} statements)")

        if not apply_requested:
            print("Database opened: no")
            print("Database write skipped: yes")
            print("PASS: all migrations are safe; dry-run completed")
            return 0

        backup_path, statement_count = apply_migrations(plans)
    except RuntimeError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    print(f"Backup: {backup_path}")
    print(f"Applied migration files: {len(plans)}")
    print(f"Applied statements: {statement_count}")
    print("Transaction committed: yes")
    print("PASS: safe migrations applied after verified backup")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

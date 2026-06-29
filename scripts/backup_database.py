from __future__ import annotations

import sqlite3
import sys
from datetime import datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_DATABASE = REPO_ROOT / "app" / "railyatra.db"
BACKUP_DIRECTORY = REPO_ROOT / "backups"


def create_backup() -> Path:
    if not SOURCE_DATABASE.is_file():
        raise RuntimeError(f"database file is missing: {SOURCE_DATABASE}")

    BACKUP_DIRECTORY.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIRECTORY / f"railyatra_{timestamp}.db"

    if backup_path.exists():
        raise RuntimeError(f"backup already exists: {backup_path}")

    source_connection = None
    backup_connection = None

    try:
        source_uri = f"{SOURCE_DATABASE.resolve().as_uri()}?mode=ro"
        source_connection = sqlite3.connect(source_uri, uri=True)
        backup_connection = sqlite3.connect(backup_path)
        source_connection.backup(backup_connection)
    except (OSError, sqlite3.Error) as exc:
        if backup_connection is not None:
            backup_connection.close()
            backup_connection = None
        backup_path.unlink(missing_ok=True)
        raise RuntimeError(f"database backup failed: {exc}") from exc
    finally:
        if backup_connection is not None:
            backup_connection.close()
        if source_connection is not None:
            source_connection.close()

    return backup_path


def verify_backup(backup_path: Path) -> None:
    connection = None

    try:
        backup_uri = f"{backup_path.resolve().as_uri()}?mode=ro"
        connection = sqlite3.connect(backup_uri, uri=True)
        result = connection.execute("PRAGMA quick_check").fetchone()
    except sqlite3.Error as exc:
        raise RuntimeError(f"backup verification failed: {exc}") from exc
    finally:
        if connection is not None:
            connection.close()

    if not result or result[0] != "ok":
        raise RuntimeError(f"backup verification failed: {result}")


def main() -> int:
    try:
        backup_path = create_backup()
        verify_backup(backup_path)
    except RuntimeError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    file_size = backup_path.stat().st_size
    print("RailYatra SQLite database backup")
    print(f"Source: {SOURCE_DATABASE}")
    print(f"Backup: {backup_path}")
    print(f"File size: {file_size} bytes")
    print("PASS: database backup created and verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any


SQLITE_DB_PATH = Path(__file__).resolve().parents[2] / "railyatra.db"


def configured_database_url() -> str:
    return (
        os.environ.get("DATABASE_URL")
        or os.environ.get("RAILYATRA_DEMO_DATABASE_URL")
        or os.environ.get("RAILYATRA_FEEDBACK_DATABASE_URL")
        or ""
    ).strip()


def postgres_enabled() -> bool:
    return configured_database_url().startswith(
        ("postgres://", "postgresql://")
    )


@contextmanager
def database_connection():
    if postgres_enabled():
        import psycopg2

        connection = psycopg2.connect(configured_database_url())
    else:
        SQLITE_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(SQLITE_DB_PATH)

    try:
        yield connection
    finally:
        connection.close()


def beta_feedback_store_status() -> dict[str, Any]:
    return {
        "mode": "postgresql" if postgres_enabled() else "sqlite",
        "database_url_configured": bool(configured_database_url()),
        "sqlite_path": str(SQLITE_DB_PATH),
    }


def ensure_beta_feedback_table() -> None:
    if postgres_enabled():
        with database_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS beta_feedback (
                        id BIGSERIAL PRIMARY KEY,
                        message TEXT NOT NULL,
                        page TEXT,
                        route TEXT,
                        severity TEXT,
                        name TEXT,
                        contact TEXT,
                        user_agent TEXT,
                        status TEXT NOT NULL DEFAULT 'new',
                        created_at TEXT NOT NULL
                    )
                    """
                )
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_beta_feedback_created_at
                    ON beta_feedback (created_at DESC)
                    """
                )
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_beta_feedback_status
                    ON beta_feedback (status)
                    """
                )
            connection.commit()
        return

    with database_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS beta_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message TEXT NOT NULL,
                page TEXT,
                route TEXT,
                severity TEXT,
                name TEXT,
                contact TEXT,
                user_agent TEXT,
                status TEXT NOT NULL DEFAULT 'new',
                created_at TEXT NOT NULL
            )
            """
        )

        columns = {
            row[1]
            for row in connection.execute(
                "PRAGMA table_info(beta_feedback)"
            ).fetchall()
        }

        if "status" not in columns:
            connection.execute(
                """
                ALTER TABLE beta_feedback
                ADD COLUMN status TEXT NOT NULL DEFAULT 'new'
                """
            )

        connection.commit()


def count_beta_feedback() -> int:
    ensure_beta_feedback_table()

    with database_connection() as connection:
        if postgres_enabled():
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM beta_feedback")
                return int(cursor.fetchone()[0])

        row = connection.execute(
            "SELECT COUNT(*) FROM beta_feedback"
        ).fetchone()

        return int(row[0])


def save_beta_feedback(entry: dict[str, Any]) -> int:
    ensure_beta_feedback_table()

    values = (
        str(entry.get("message") or ""),
        entry.get("page"),
        entry.get("route"),
        str(entry.get("severity") or "normal"),
        entry.get("name"),
        entry.get("contact"),
        str(entry.get("user_agent") or ""),
        str(entry.get("status") or "new"),
        str(entry.get("created_at") or ""),
    )

    with database_connection() as connection:
        if postgres_enabled():
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO beta_feedback (
                        message,
                        page,
                        route,
                        severity,
                        name,
                        contact,
                        user_agent,
                        status,
                        created_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    values,
                )
                feedback_id = int(cursor.fetchone()[0])

            connection.commit()
            return feedback_id

        cursor = connection.execute(
            """
            INSERT INTO beta_feedback (
                message,
                page,
                route,
                severity,
                name,
                contact,
                user_agent,
                status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            values,
        )

        connection.commit()
        return int(cursor.lastrowid)


def list_beta_feedback_entries(
    limit: int = 50,
) -> list[dict[str, Any]]:
    ensure_beta_feedback_table()

    safe_limit = max(1, min(int(limit or 50), 500))

    query = """
        SELECT
            id,
            message,
            page,
            route,
            severity,
            status,
            name,
            contact,
            created_at
        FROM beta_feedback
        ORDER BY id DESC
    """

    with database_connection() as connection:
        if postgres_enabled():
            with connection.cursor() as cursor:
                cursor.execute(
                    query + " LIMIT %s",
                    (safe_limit,),
                )
                rows = cursor.fetchall()
        else:
            rows = connection.execute(
                query + " LIMIT ?",
                (safe_limit,),
            ).fetchall()

    return [
        {
            "id": row[0],
            "message": row[1],
            "page": row[2],
            "route": row[3],
            "severity": row[4] or "normal",
            "status": row[5] or "new",
            "name": row[6],
            "contact": row[7],
            "created_at": row[8],
        }
        for row in rows
    ]



def beta_feedback_status_counts() -> dict[str, int]:
    ensure_beta_feedback_table()

    query = """
        SELECT status, COUNT(*)
        FROM beta_feedback
        GROUP BY status
    """

    with database_connection() as connection:
        if postgres_enabled():
            with connection.cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
        else:
            rows = connection.execute(query).fetchall()

    counts = {
        "total": 0,
        "new": 0,
        "reviewed": 0,
        "resolved": 0,
    }

    for raw_status, raw_count in rows:
        status = str(raw_status or "new").strip().lower()
        count = int(raw_count or 0)

        counts["total"] += count

        if status in {"new", "reviewed", "resolved"}:
            counts[status] = count

    return counts


def set_beta_feedback_status(
    feedback_id: int,
    status: str,
) -> bool:
    ensure_beta_feedback_table()

    with database_connection() as connection:
        if postgres_enabled():
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE beta_feedback
                    SET status = %s
                    WHERE id = %s
                    """,
                    (status, feedback_id),
                )
                updated = cursor.rowcount > 0

            connection.commit()
            return updated

        cursor = connection.execute(
            """
            UPDATE beta_feedback
            SET status = ?
            WHERE id = ?
            """,
            (status, feedback_id),
        )

        connection.commit()
        return cursor.rowcount > 0

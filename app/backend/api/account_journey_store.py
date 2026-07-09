from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from backend.api.demo_store import (
    postgres_connect,
    postgres_enabled,
    sqlite_connect,
)


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _row_to_dict(cursor, row) -> dict[str, Any] | None:
    if row is None:
        return None

    if hasattr(row, "keys"):
        return dict(row)

    columns = []

    for description in cursor.description or []:
        columns.append(
            getattr(description, "name", description[0])
        )

    return dict(zip(columns, row))


def _public_journey(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": int(row["id"]),
        "user_id": int(row["user_id"]),
        "source": str(row["source"]),
        "destination": str(row["destination"]),
        "journey_date": str(
            row.get("journey_date") or ""
        ),
        "class_code": str(row["class_code"]),
        "quota": str(row["quota"]),
        "label": str(row.get("label") or ""),
        "note": str(row.get("note") or ""),
        "created_at": str(row["created_at"]),
        "updated_at": str(row["updated_at"]),
    }


def init_saved_journey_store() -> None:
    if postgres_enabled():
        with postgres_connect() as database:
            with database.cursor() as cursor:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS saved_journeys (
                        id BIGSERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL
                            REFERENCES users(id)
                            ON DELETE CASCADE,
                        source VARCHAR(12) NOT NULL,
                        destination VARCHAR(12) NOT NULL,
                        journey_date VARCHAR(10) NOT NULL
                            DEFAULT '',
                        class_code VARCHAR(8) NOT NULL
                            DEFAULT 'SL',
                        quota VARCHAR(8) NOT NULL
                            DEFAULT 'GN',
                        label VARCHAR(120) NOT NULL
                            DEFAULT 'Saved journey',
                        note VARCHAR(500) NOT NULL
                            DEFAULT '',
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        UNIQUE (
                            user_id,
                            source,
                            destination,
                            journey_date,
                            class_code,
                            quota
                        )
                    )
                    """
                )

                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS
                        idx_saved_journeys_user_updated
                    ON saved_journeys (
                        user_id,
                        updated_at DESC
                    )
                    """
                )

            database.commit()

        return

    with sqlite_connect() as database:
        database.execute(
            """
            CREATE TABLE IF NOT EXISTS saved_journeys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                source TEXT NOT NULL,
                destination TEXT NOT NULL,
                journey_date TEXT NOT NULL DEFAULT '',
                class_code TEXT NOT NULL DEFAULT 'SL',
                quota TEXT NOT NULL DEFAULT 'GN',
                label TEXT NOT NULL DEFAULT 'Saved journey',
                note TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE,
                UNIQUE (
                    user_id,
                    source,
                    destination,
                    journey_date,
                    class_code,
                    quota
                )
            )
            """
        )

        database.execute(
            """
            CREATE INDEX IF NOT EXISTS
                idx_saved_journeys_user_updated
            ON saved_journeys (
                user_id,
                updated_at DESC
            )
            """
        )

        database.commit()


def list_saved_journeys(
    user_id: int,
    limit: int = 50,
) -> list[dict[str, Any]]:
    init_saved_journey_store()

    safe_limit = max(1, min(int(limit), 100))

    if postgres_enabled():
        with postgres_connect() as database:
            with database.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        id,
                        user_id,
                        source,
                        destination,
                        journey_date,
                        class_code,
                        quota,
                        label,
                        note,
                        created_at,
                        updated_at
                    FROM saved_journeys
                    WHERE user_id = %s
                    ORDER BY updated_at DESC, id DESC
                    LIMIT %s
                    """,
                    (
                        int(user_id),
                        safe_limit,
                    ),
                )

                rows = cursor.fetchall()

                return [
                    _public_journey(
                        _row_to_dict(cursor, row) or {}
                    )
                    for row in rows
                ]

    with sqlite_connect() as database:
        cursor = database.execute(
            """
            SELECT
                id,
                user_id,
                source,
                destination,
                journey_date,
                class_code,
                quota,
                label,
                note,
                created_at,
                updated_at
            FROM saved_journeys
            WHERE user_id = ?
            ORDER BY updated_at DESC, id DESC
            LIMIT ?
            """,
            (
                int(user_id),
                safe_limit,
            ),
        )

        rows = cursor.fetchall()

        return [
            _public_journey(
                _row_to_dict(cursor, row) or {}
            )
            for row in rows
        ]


def upsert_saved_journey(
    user_id: int,
    journey: dict[str, Any],
) -> dict[str, Any]:
    init_saved_journey_store()

    timestamp = utc_timestamp()

    values = (
        int(user_id),
        journey["source"],
        journey["destination"],
        journey["journey_date"],
        journey["class_code"],
        journey["quota"],
        journey["label"],
        journey["note"],
        timestamp,
        timestamp,
    )

    if postgres_enabled():
        with postgres_connect() as database:
            with database.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO saved_journeys (
                        user_id,
                        source,
                        destination,
                        journey_date,
                        class_code,
                        quota,
                        label,
                        note,
                        created_at,
                        updated_at
                    )
                    VALUES (
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (
                        user_id,
                        source,
                        destination,
                        journey_date,
                        class_code,
                        quota
                    )
                    DO UPDATE SET
                        label = EXCLUDED.label,
                        note = EXCLUDED.note,
                        updated_at = EXCLUDED.updated_at
                    RETURNING
                        id,
                        user_id,
                        source,
                        destination,
                        journey_date,
                        class_code,
                        quota,
                        label,
                        note,
                        created_at,
                        updated_at
                    """,
                    values,
                )

                row = _row_to_dict(
                    cursor,
                    cursor.fetchone(),
                )

            database.commit()

        if not row:
            raise RuntimeError(
                "Saved journey could not be returned."
            )

        return _public_journey(row)

    with sqlite_connect() as database:
        database.execute(
            """
            INSERT INTO saved_journeys (
                user_id,
                source,
                destination,
                journey_date,
                class_code,
                quota,
                label,
                note,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (
                user_id,
                source,
                destination,
                journey_date,
                class_code,
                quota
            )
            DO UPDATE SET
                label = excluded.label,
                note = excluded.note,
                updated_at = excluded.updated_at
            """,
            values,
        )

        cursor = database.execute(
            """
            SELECT
                id,
                user_id,
                source,
                destination,
                journey_date,
                class_code,
                quota,
                label,
                note,
                created_at,
                updated_at
            FROM saved_journeys
            WHERE
                user_id = ?
                AND source = ?
                AND destination = ?
                AND journey_date = ?
                AND class_code = ?
                AND quota = ?
            LIMIT 1
            """,
            (
                int(user_id),
                journey["source"],
                journey["destination"],
                journey["journey_date"],
                journey["class_code"],
                journey["quota"],
            ),
        )

        row = _row_to_dict(
            cursor,
            cursor.fetchone(),
        )

        database.commit()

    if not row:
        raise RuntimeError(
            "Saved journey could not be returned."
        )

    return _public_journey(row)


def delete_saved_journey(
    user_id: int,
    journey_id: int,
) -> bool:
    init_saved_journey_store()

    if postgres_enabled():
        with postgres_connect() as database:
            with database.cursor() as cursor:
                cursor.execute(
                    """
                    DELETE FROM saved_journeys
                    WHERE id = %s AND user_id = %s
                    """,
                    (
                        int(journey_id),
                        int(user_id),
                    ),
                )

                deleted = cursor.rowcount > 0

            database.commit()

        return deleted

    with sqlite_connect() as database:
        cursor = database.execute(
            """
            DELETE FROM saved_journeys
            WHERE id = ? AND user_id = ?
            """,
            (
                int(journey_id),
                int(user_id),
            ),
        )

        database.commit()

        return cursor.rowcount > 0

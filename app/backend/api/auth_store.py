from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any

from backend.api.demo_store import (
    postgres_connect,
    postgres_enabled,
    sqlite_connect,
)


SESSION_DAYS = max(
    1,
    min(
        int(
            os.environ.get(
                "RAILYATRA_SESSION_DAYS",
                "30",
            )
        ),
        365,
    ),
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_datetime(value: datetime) -> str:
    return value.astimezone(
        timezone.utc
    ).isoformat()


def _postgres_row(cursor, row) -> dict[str, Any] | None:
    if row is None:
        return None

    columns = [
        description[0]
        for description in cursor.description
    ]

    return dict(zip(columns, row))


def public_user(
    row: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if not row:
        return None

    return {
        "id": int(row["id"]),
        "email": str(row["email"]),
        "display_name": str(row["display_name"]),
        "is_active": bool(row["is_active"]),
        "created_at": str(row["created_at"]),
        "updated_at": str(row["updated_at"]),
        "last_login_at": (
            str(row["last_login_at"])
            if row.get("last_login_at")
            else None
        ),
    }


def init_sqlite_auth_store() -> None:
    with sqlite_connect() as database:
        database.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL COLLATE NOCASE UNIQUE,
                display_name TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                last_login_at TEXT
            )
            """
        )

        database.execute(
            """
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token_hash TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                revoked_at TEXT,
                user_agent TEXT,
                ip_address TEXT,
                FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE
            )
            """
        )

        database.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_user_sessions_user_id
            ON user_sessions (user_id)
            """
        )

        database.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_user_sessions_token_hash
            ON user_sessions (token_hash)
            """
        )

        database.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_user_sessions_expires_at
            ON user_sessions (expires_at)
            """
        )

        database.commit()


def init_postgres_auth_store() -> None:
    with postgres_connect() as database:
        with database.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id BIGSERIAL PRIMARY KEY,
                    email TEXT NOT NULL,
                    display_name TEXT NOT NULL,
                    password_hash TEXT NOT NULL,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    last_login_at TEXT
                )
                """
            )

            cursor.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS
                idx_users_email_lower_unique
                ON users (LOWER(email))
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS user_sessions (
                    id BIGSERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL
                        REFERENCES users(id)
                        ON DELETE CASCADE,
                    token_hash TEXT NOT NULL UNIQUE,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    revoked_at TEXT,
                    user_agent TEXT,
                    ip_address TEXT
                )
                """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_user_sessions_user_id
                ON user_sessions (user_id)
                """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_user_sessions_token_hash
                ON user_sessions (token_hash)
                """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_user_sessions_expires_at
                ON user_sessions (expires_at)
                """
            )

        database.commit()


def init_auth_store() -> None:
    if postgres_enabled():
        init_postgres_auth_store()
    else:
        init_sqlite_auth_store()


def auth_store_status() -> dict[str, Any]:
    return {
        "ok": True,
        "storage": (
            "postgresql"
            if postgres_enabled()
            else "sqlite"
        ),
        "session_days": SESSION_DAYS,
        "raw_session_tokens_stored": False,
        "password_storage": "scrypt",
    }


def get_user_by_email(
    email: str,
    include_password: bool = False,
) -> dict[str, Any] | None:
    init_auth_store()

    fields = (
        "id, email, display_name, password_hash, "
        "is_active, created_at, updated_at, "
        "last_login_at"
    )

    if postgres_enabled():
        with postgres_connect() as database:
            with database.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT {fields}
                    FROM users
                    WHERE LOWER(email) = LOWER(%s)
                    LIMIT 1
                    """,
                    (email,),
                )

                row = _postgres_row(
                    cursor,
                    cursor.fetchone(),
                )
    else:
        with sqlite_connect() as database:
            sqlite_row = database.execute(
                f"""
                SELECT {fields}
                FROM users
                WHERE email = ? COLLATE NOCASE
                LIMIT 1
                """,
                (email,),
            ).fetchone()

            row = (
                dict(sqlite_row)
                if sqlite_row is not None
                else None
            )

    if not row:
        return None

    if include_password:
        return row

    return public_user(row)


def get_user_by_id(
    user_id: int,
) -> dict[str, Any] | None:
    init_auth_store()

    fields = (
        "id, email, display_name, is_active, "
        "created_at, updated_at, last_login_at"
    )

    if postgres_enabled():
        with postgres_connect() as database:
            with database.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT {fields}
                    FROM users
                    WHERE id = %s
                    LIMIT 1
                    """,
                    (user_id,),
                )

                row = _postgres_row(
                    cursor,
                    cursor.fetchone(),
                )
    else:
        with sqlite_connect() as database:
            sqlite_row = database.execute(
                f"""
                SELECT {fields}
                FROM users
                WHERE id = ?
                LIMIT 1
                """,
                (user_id,),
            ).fetchone()

            row = (
                dict(sqlite_row)
                if sqlite_row is not None
                else None
            )

    return public_user(row)


def create_user(
    email: str,
    display_name: str,
    password_hash: str,
) -> dict[str, Any]:
    init_auth_store()

    current_time = iso_datetime(utc_now())

    if postgres_enabled():
        with postgres_connect() as database:
            with database.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO users (
                        email,
                        display_name,
                        password_hash,
                        is_active,
                        created_at,
                        updated_at
                    )
                    VALUES (%s, %s, %s, TRUE, %s, %s)
                    RETURNING
                        id,
                        email,
                        display_name,
                        is_active,
                        created_at,
                        updated_at,
                        last_login_at
                    """,
                    (
                        email,
                        display_name,
                        password_hash,
                        current_time,
                        current_time,
                    ),
                )

                row = _postgres_row(
                    cursor,
                    cursor.fetchone(),
                )

            database.commit()
    else:
        with sqlite_connect() as database:
            cursor = database.execute(
                """
                INSERT INTO users (
                    email,
                    display_name,
                    password_hash,
                    is_active,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, 1, ?, ?)
                """,
                (
                    email,
                    display_name,
                    password_hash,
                    current_time,
                    current_time,
                ),
            )

            database.commit()

            sqlite_row = database.execute(
                """
                SELECT
                    id,
                    email,
                    display_name,
                    is_active,
                    created_at,
                    updated_at,
                    last_login_at
                FROM users
                WHERE id = ?
                """,
                (cursor.lastrowid,),
            ).fetchone()

            row = dict(sqlite_row)

    user = public_user(row)

    if user is None:
        raise RuntimeError(
            "User creation did not return a user."
        )

    return user


def update_last_login(user_id: int) -> None:
    current_time = iso_datetime(utc_now())

    if postgres_enabled():
        with postgres_connect() as database:
            with database.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE users
                    SET
                        last_login_at = %s,
                        updated_at = %s
                    WHERE id = %s
                    """,
                    (
                        current_time,
                        current_time,
                        user_id,
                    ),
                )

            database.commit()
    else:
        with sqlite_connect() as database:
            database.execute(
                """
                UPDATE users
                SET
                    last_login_at = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    current_time,
                    current_time,
                    user_id,
                ),
            )

            database.commit()


def create_session(
    user_id: int,
    token_hash: str,
    user_agent: str = "",
    ip_address: str = "",
) -> dict[str, Any]:
    init_auth_store()

    created_at = utc_now()
    expires_at = created_at + timedelta(
        days=SESSION_DAYS
    )

    created_value = iso_datetime(created_at)
    expires_value = iso_datetime(expires_at)

    if postgres_enabled():
        with postgres_connect() as database:
            with database.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO user_sessions (
                        user_id,
                        token_hash,
                        created_at,
                        expires_at,
                        user_agent,
                        ip_address
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        user_id,
                        token_hash,
                        created_value,
                        expires_value,
                        user_agent[:500],
                        ip_address[:100],
                    ),
                )

                session_id = cursor.fetchone()[0]

            database.commit()
    else:
        with sqlite_connect() as database:
            cursor = database.execute(
                """
                INSERT INTO user_sessions (
                    user_id,
                    token_hash,
                    created_at,
                    expires_at,
                    user_agent,
                    ip_address
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    token_hash,
                    created_value,
                    expires_value,
                    user_agent[:500],
                    ip_address[:100],
                ),
            )

            database.commit()
            session_id = cursor.lastrowid

    return {
        "id": int(session_id),
        "user_id": int(user_id),
        "created_at": created_value,
        "expires_at": expires_value,
    }


def get_session_user(
    token_hash: str,
) -> dict[str, Any] | None:
    init_auth_store()

    current_time = iso_datetime(utc_now())

    query_fields = """
        s.id AS session_id,
        s.created_at AS session_created_at,
        s.expires_at AS session_expires_at,
        u.id,
        u.email,
        u.display_name,
        u.is_active,
        u.created_at,
        u.updated_at,
        u.last_login_at
    """

    if postgres_enabled():
        with postgres_connect() as database:
            with database.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT {query_fields}
                    FROM user_sessions AS s
                    INNER JOIN users AS u
                        ON u.id = s.user_id
                    WHERE
                        s.token_hash = %s
                        AND s.revoked_at IS NULL
                        AND s.expires_at > %s
                        AND u.is_active = TRUE
                    LIMIT 1
                    """,
                    (
                        token_hash,
                        current_time,
                    ),
                )

                row = _postgres_row(
                    cursor,
                    cursor.fetchone(),
                )
    else:
        with sqlite_connect() as database:
            sqlite_row = database.execute(
                f"""
                SELECT {query_fields}
                FROM user_sessions AS s
                INNER JOIN users AS u
                    ON u.id = s.user_id
                WHERE
                    s.token_hash = ?
                    AND s.revoked_at IS NULL
                    AND s.expires_at > ?
                    AND u.is_active = 1
                LIMIT 1
                """,
                (
                    token_hash,
                    current_time,
                ),
            ).fetchone()

            row = (
                dict(sqlite_row)
                if sqlite_row is not None
                else None
            )

    if not row:
        return None

    return {
        "session": {
            "id": int(row["session_id"]),
            "created_at": str(
                row["session_created_at"]
            ),
            "expires_at": str(
                row["session_expires_at"]
            ),
        },
        "user": public_user(row),
    }


def revoke_session(token_hash: str) -> bool:
    init_auth_store()

    revoked_at = iso_datetime(utc_now())

    if postgres_enabled():
        with postgres_connect() as database:
            with database.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE user_sessions
                    SET revoked_at = %s
                    WHERE
                        token_hash = %s
                        AND revoked_at IS NULL
                    """,
                    (
                        revoked_at,
                        token_hash,
                    ),
                )

                changed = cursor.rowcount > 0

            database.commit()

        return changed

    with sqlite_connect() as database:
        cursor = database.execute(
            """
            UPDATE user_sessions
            SET revoked_at = ?
            WHERE
                token_hash = ?
                AND revoked_at IS NULL
            """,
            (
                revoked_at,
                token_hash,
            ),
        )

        database.commit()

        return cursor.rowcount > 0


def update_user_password(
    user_id: int,
    password_hash: str,
) -> bool:
    init_auth_store()
    updated_at = iso_datetime(utc_now())

    if postgres_enabled():
        with postgres_connect() as database:
            with database.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE users
                    SET
                        password_hash = %s,
                        updated_at = %s
                    WHERE
                        id = %s
                        AND is_active = TRUE
                    """,
                    (
                        password_hash,
                        updated_at,
                        user_id,
                    ),
                )
                changed = cursor.rowcount > 0

            database.commit()

        return changed

    with sqlite_connect() as database:
        cursor = database.execute(
            """
            UPDATE users
            SET
                password_hash = ?,
                updated_at = ?
            WHERE
                id = ?
                AND is_active = 1
            """,
            (
                password_hash,
                updated_at,
                user_id,
            ),
        )
        database.commit()

        return cursor.rowcount > 0


def revoke_user_sessions(user_id: int) -> int:
    init_auth_store()
    revoked_at = iso_datetime(utc_now())

    if postgres_enabled():
        with postgres_connect() as database:
            with database.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE user_sessions
                    SET revoked_at = %s
                    WHERE
                        user_id = %s
                        AND revoked_at IS NULL
                    """,
                    (
                        revoked_at,
                        user_id,
                    ),
                )
                changed = cursor.rowcount

            database.commit()

        return int(changed)

    with sqlite_connect() as database:
        cursor = database.execute(
            """
            UPDATE user_sessions
            SET revoked_at = ?
            WHERE
                user_id = ?
                AND revoked_at IS NULL
            """,
            (
                revoked_at,
                user_id,
            ),
        )
        database.commit()

        return int(cursor.rowcount)


def delete_user_account(user_id: int) -> bool:
    init_auth_store()

    if postgres_enabled():
        with postgres_connect() as database:
            with database.cursor() as cursor:
                cursor.execute(
                    """
                    DELETE FROM users
                    WHERE id = %s
                    """,
                    (user_id,),
                )
                deleted = cursor.rowcount > 0

            database.commit()

        return deleted

    with sqlite_connect() as database:
        database.execute("PRAGMA foreign_keys = ON")

        saved_journeys_exists = database.execute(
            """
            SELECT 1
            FROM sqlite_master
            WHERE
                type = 'table'
                AND name = 'saved_journeys'
            LIMIT 1
            """
        ).fetchone()

        if saved_journeys_exists:
            database.execute(
                """
                DELETE FROM saved_journeys
                WHERE user_id = ?
                """,
                (user_id,),
            )

        database.execute(
            """
            DELETE FROM user_sessions
            WHERE user_id = ?
            """,
            (user_id,),
        )

        cursor = database.execute(
            """
            DELETE FROM users
            WHERE id = ?
            """,
            (user_id,),
        )

        database.commit()

        return cursor.rowcount > 0

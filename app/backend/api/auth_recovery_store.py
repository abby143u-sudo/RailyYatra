from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any

from backend.api.demo_store import (
    postgres_connect,
    postgres_enabled,
    sqlite_connect,
)


EMAIL_VERIFICATION_PURPOSE = "verify_email"
PASSWORD_RESET_PURPOSE = "reset_password"

EMAIL_VERIFICATION_SECONDS = max(
    60 * 60,
    min(
        int(
            os.environ.get(
                "RAILYATRA_EMAIL_VERIFICATION_SECONDS",
                str(24 * 60 * 60),
            )
        ),
        7 * 24 * 60 * 60,
    ),
)
PASSWORD_RESET_SECONDS = max(
    5 * 60,
    min(
        int(
            os.environ.get(
                "RAILYATRA_PASSWORD_RESET_SECONDS",
                str(30 * 60),
            )
        ),
        2 * 60 * 60,
    ),
)

_ALLOWED_PURPOSES = {
    EMAIL_VERIFICATION_PURPOSE,
    PASSWORD_RESET_PURPOSE,
}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_datetime(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


def _postgres_row(cursor, row) -> dict[str, Any] | None:
    if row is None:
        return None

    columns = [
        description[0]
        for description in cursor.description
    ]

    return dict(zip(columns, row))


def validate_purpose(purpose: str) -> str:
    value = str(purpose or "").strip()

    if value not in _ALLOWED_PURPOSES:
        raise ValueError("Unsupported authentication token purpose.")

    return value


def init_sqlite_auth_recovery_store() -> None:
    with sqlite_connect() as database:
        database.execute(
            """
            CREATE TABLE IF NOT EXISTS user_email_status (
                user_id INTEGER PRIMARY KEY,
                verified_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE
            )
            """
        )
        database.execute(
            """
            CREATE TABLE IF NOT EXISTS auth_action_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                purpose TEXT NOT NULL,
                token_hash TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                consumed_at TEXT,
                requested_ip TEXT,
                FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE
            )
            """
        )
        database.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_auth_action_tokens_lookup
            ON auth_action_tokens (
                token_hash,
                purpose,
                expires_at
            )
            """
        )
        database.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_auth_action_tokens_user_purpose
            ON auth_action_tokens (user_id, purpose)
            """
        )
        database.commit()


def init_postgres_auth_recovery_store() -> None:
    with postgres_connect() as database:
        with database.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS user_email_status (
                    user_id BIGINT PRIMARY KEY
                        REFERENCES users(id)
                        ON DELETE CASCADE,
                    verified_at TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS auth_action_tokens (
                    id BIGSERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL
                        REFERENCES users(id)
                        ON DELETE CASCADE,
                    purpose TEXT NOT NULL,
                    token_hash TEXT NOT NULL UNIQUE,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    consumed_at TEXT,
                    requested_ip TEXT
                )
                """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_auth_action_tokens_lookup
                ON auth_action_tokens (
                    token_hash,
                    purpose,
                    expires_at
                )
                """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_auth_action_tokens_user_purpose
                ON auth_action_tokens (user_id, purpose)
                """
            )

        database.commit()


def init_auth_recovery_store() -> None:
    if postgres_enabled():
        init_postgres_auth_recovery_store()
    else:
        init_sqlite_auth_recovery_store()


def auth_recovery_store_status() -> dict[str, Any]:
    return {
        "storage": (
            "postgresql"
            if postgres_enabled()
            else "sqlite"
        ),
        "raw_action_tokens_stored": False,
        "email_verification_seconds": (
            EMAIL_VERIFICATION_SECONDS
        ),
        "password_reset_seconds": PASSWORD_RESET_SECONDS,
    }


def email_verification_status(user_id: int) -> dict[str, Any]:
    init_auth_recovery_store()

    if postgres_enabled():
        with postgres_connect() as database:
            with database.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT verified_at
                    FROM user_email_status
                    WHERE user_id = %s
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
                """
                SELECT verified_at
                FROM user_email_status
                WHERE user_id = ?
                LIMIT 1
                """,
                (user_id,),
            ).fetchone()
            row = (
                dict(sqlite_row)
                if sqlite_row is not None
                else None
            )

    verified_at = (
        str(row["verified_at"])
        if row and row.get("verified_at")
        else None
    )

    return {
        "email_verified": bool(verified_at),
        "email_verified_at": verified_at,
    }


def mark_email_verified(user_id: int) -> dict[str, Any]:
    init_auth_recovery_store()
    current_time = iso_datetime(utc_now())

    if postgres_enabled():
        with postgres_connect() as database:
            with database.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO user_email_status (
                        user_id,
                        verified_at,
                        created_at,
                        updated_at
                    )
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (user_id)
                    DO UPDATE SET
                        verified_at = COALESCE(
                            user_email_status.verified_at,
                            EXCLUDED.verified_at
                        ),
                        updated_at = EXCLUDED.updated_at
                    """,
                    (
                        user_id,
                        current_time,
                        current_time,
                        current_time,
                    ),
                )

            database.commit()
    else:
        with sqlite_connect() as database:
            database.execute(
                """
                INSERT INTO user_email_status (
                    user_id,
                    verified_at,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id)
                DO UPDATE SET
                    verified_at = COALESCE(
                        user_email_status.verified_at,
                        excluded.verified_at
                    ),
                    updated_at = excluded.updated_at
                """,
                (
                    user_id,
                    current_time,
                    current_time,
                    current_time,
                ),
            )
            database.commit()

    return email_verification_status(user_id)


def issue_auth_action_token(
    user_id: int,
    purpose: str,
    token_hash: str,
    ttl_seconds: int,
    requested_ip: str = "",
) -> dict[str, Any]:
    init_auth_recovery_store()
    safe_purpose = validate_purpose(purpose)
    created_at = utc_now()
    expires_at = created_at + timedelta(
        seconds=max(1, int(ttl_seconds))
    )
    created_value = iso_datetime(created_at)
    expires_value = iso_datetime(expires_at)
    requested_ip_value = str(requested_ip or "")[:100]

    if postgres_enabled():
        with postgres_connect() as database:
            with database.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE auth_action_tokens
                    SET consumed_at = %s
                    WHERE
                        user_id = %s
                        AND purpose = %s
                        AND consumed_at IS NULL
                    """,
                    (
                        created_value,
                        user_id,
                        safe_purpose,
                    ),
                )
                cursor.execute(
                    """
                    INSERT INTO auth_action_tokens (
                        user_id,
                        purpose,
                        token_hash,
                        created_at,
                        expires_at,
                        requested_ip
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        user_id,
                        safe_purpose,
                        token_hash,
                        created_value,
                        expires_value,
                        requested_ip_value,
                    ),
                )
                token_id = cursor.fetchone()[0]

            database.commit()
    else:
        with sqlite_connect() as database:
            database.execute(
                """
                UPDATE auth_action_tokens
                SET consumed_at = ?
                WHERE
                    user_id = ?
                    AND purpose = ?
                    AND consumed_at IS NULL
                """,
                (
                    created_value,
                    user_id,
                    safe_purpose,
                ),
            )
            cursor = database.execute(
                """
                INSERT INTO auth_action_tokens (
                    user_id,
                    purpose,
                    token_hash,
                    created_at,
                    expires_at,
                    requested_ip
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    safe_purpose,
                    token_hash,
                    created_value,
                    expires_value,
                    requested_ip_value,
                ),
            )
            database.commit()
            token_id = cursor.lastrowid

    return {
        "id": int(token_id),
        "user_id": int(user_id),
        "purpose": safe_purpose,
        "created_at": created_value,
        "expires_at": expires_value,
    }


def consume_auth_action_token(
    token_hash: str,
    purpose: str,
) -> dict[str, Any] | None:
    init_auth_recovery_store()
    safe_purpose = validate_purpose(purpose)
    current_time = iso_datetime(utc_now())

    if postgres_enabled():
        with postgres_connect() as database:
            with database.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        id,
                        user_id,
                        purpose,
                        created_at,
                        expires_at
                    FROM auth_action_tokens
                    WHERE
                        token_hash = %s
                        AND purpose = %s
                        AND consumed_at IS NULL
                        AND expires_at > %s
                    LIMIT 1
                    FOR UPDATE
                    """,
                    (
                        token_hash,
                        safe_purpose,
                        current_time,
                    ),
                )
                row = _postgres_row(
                    cursor,
                    cursor.fetchone(),
                )

                if row:
                    cursor.execute(
                        """
                        UPDATE auth_action_tokens
                        SET consumed_at = %s
                        WHERE
                            id = %s
                            AND consumed_at IS NULL
                        """,
                        (
                            current_time,
                            row["id"],
                        ),
                    )
                    consumed = cursor.rowcount > 0
                else:
                    consumed = False

            database.commit()
    else:
        with sqlite_connect() as database:
            database.execute("BEGIN IMMEDIATE")
            sqlite_row = database.execute(
                """
                SELECT
                    id,
                    user_id,
                    purpose,
                    created_at,
                    expires_at
                FROM auth_action_tokens
                WHERE
                    token_hash = ?
                    AND purpose = ?
                    AND consumed_at IS NULL
                    AND expires_at > ?
                LIMIT 1
                """,
                (
                    token_hash,
                    safe_purpose,
                    current_time,
                ),
            ).fetchone()
            row = (
                dict(sqlite_row)
                if sqlite_row is not None
                else None
            )

            if row:
                cursor = database.execute(
                    """
                    UPDATE auth_action_tokens
                    SET consumed_at = ?
                    WHERE
                        id = ?
                        AND consumed_at IS NULL
                    """,
                    (
                        current_time,
                        row["id"],
                    ),
                )
                consumed = cursor.rowcount > 0
            else:
                consumed = False

            database.commit()

    if not row or not consumed:
        return None

    return {
        "id": int(row["id"]),
        "user_id": int(row["user_id"]),
        "purpose": str(row["purpose"]),
        "created_at": str(row["created_at"]),
        "expires_at": str(row["expires_at"]),
        "consumed_at": current_time,
    }


def revoke_auth_action_tokens(
    user_id: int,
    purpose: str | None = None,
) -> int:
    init_auth_recovery_store()
    current_time = iso_datetime(utc_now())
    safe_purpose = (
        validate_purpose(purpose)
        if purpose is not None
        else None
    )

    if postgres_enabled():
        with postgres_connect() as database:
            with database.cursor() as cursor:
                if safe_purpose:
                    cursor.execute(
                        """
                        UPDATE auth_action_tokens
                        SET consumed_at = %s
                        WHERE
                            user_id = %s
                            AND purpose = %s
                            AND consumed_at IS NULL
                        """,
                        (
                            current_time,
                            user_id,
                            safe_purpose,
                        ),
                    )
                else:
                    cursor.execute(
                        """
                        UPDATE auth_action_tokens
                        SET consumed_at = %s
                        WHERE
                            user_id = %s
                            AND consumed_at IS NULL
                        """,
                        (
                            current_time,
                            user_id,
                        ),
                    )
                changed = cursor.rowcount

            database.commit()

        return int(changed)

    with sqlite_connect() as database:
        if safe_purpose:
            cursor = database.execute(
                """
                UPDATE auth_action_tokens
                SET consumed_at = ?
                WHERE
                    user_id = ?
                    AND purpose = ?
                    AND consumed_at IS NULL
                """,
                (
                    current_time,
                    user_id,
                    safe_purpose,
                ),
            )
        else:
            cursor = database.execute(
                """
                UPDATE auth_action_tokens
                SET consumed_at = ?
                WHERE
                    user_id = ?
                    AND consumed_at IS NULL
                """,
                (
                    current_time,
                    user_id,
                ),
            )
        database.commit()

        return int(cursor.rowcount)

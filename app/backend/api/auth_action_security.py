from __future__ import annotations

import hashlib
import secrets


def hash_auth_action_token(token: str) -> str:
    return hashlib.sha256(
        str(token or "").encode("utf-8")
    ).hexdigest()


def create_auth_action_token() -> tuple[str, str]:
    raw_token = secrets.token_urlsafe(48)

    return (
        raw_token,
        hash_auth_action_token(raw_token),
    )

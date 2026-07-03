import os
from fastapi import HTTPException, Request

ADMIN_TOKEN_ENV = "RAILYATRA_ADMIN_TOKEN"

def admin_auth_status() -> dict:
    token = os.environ.get(ADMIN_TOKEN_ENV, "").strip()
    return {
        "admin_auth_enabled": bool(token),
        "admin_token_env": ADMIN_TOKEN_ENV,
        "accepted_headers": ["X-RailYatra-Admin-Token", "Authorization: Bearer <token>"],
        "token_is_exposed": False,
    }

def bearer_token(value: str) -> str:
    clean = (value or "").strip()
    if clean.lower().startswith("bearer "):
        return clean[7:].strip()
    return ""

def require_admin_request(request: Request) -> dict:
    expected = os.environ.get(ADMIN_TOKEN_ENV, "").strip()
    status = admin_auth_status()

    if not expected:
        return {
            **status,
            "admin_id": "open_preview_admin",
            "auth_mode": "open_until_RAILYATRA_ADMIN_TOKEN_is_set",
        }

    header_token = (request.headers.get("X-RailYatra-Admin-Token") or "").strip()
    auth_token = bearer_token(request.headers.get("Authorization") or "")
    provided = header_token or auth_token

    if provided != expected:
        raise HTTPException(status_code=401, detail="Admin token required")

    return {
        **status,
        "admin_id": "token_admin",
        "auth_mode": "protected_admin_token",
    }

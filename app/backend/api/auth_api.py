from __future__ import annotations

import os

from fastapi import (
    APIRouter,
    HTTPException,
    Request,
    Response,
)
from pydantic import BaseModel, Field

from backend.api.auth_security import (
    create_session_token,
    hash_password,
    hash_session_token,
    normalize_display_name,
    normalize_email,
    validate_password,
    verify_password,
)
from backend.api.auth_store import (
    SESSION_DAYS,
    auth_store_status,
    create_session,
    create_user,
    get_session_user,
    get_user_by_email,
    revoke_session,
    update_last_login,
)


router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
)

COOKIE_NAME = os.environ.get(
    "RAILYATRA_SESSION_COOKIE_NAME",
    "railyatra_session",
).strip() or "railyatra_session"

DUMMY_PASSWORD_HASH = hash_password(
    "RailYatraDummyPassword123"
)


class RegisterPayload(BaseModel):
    email: str = Field(
        ...,
        min_length=3,
        max_length=254,
    )
    display_name: str = Field(
        ...,
        min_length=2,
        max_length=80,
    )
    password: str = Field(
        ...,
        min_length=10,
        max_length=128,
    )


class LoginPayload(BaseModel):
    email: str = Field(
        ...,
        min_length=3,
        max_length=254,
    )
    password: str = Field(
        ...,
        min_length=1,
        max_length=128,
    )


def production_environment() -> bool:
    return (
        os.environ.get(
            "RAILYATRA_ENV",
            "development",
        )
        .strip()
        .lower()
        == "production"
    )


def cookie_secure() -> bool:
    configured = os.environ.get(
        "RAILYATRA_SESSION_COOKIE_SECURE",
        "",
    ).strip()

    if configured:
        return configured.lower() == "true"

    return production_environment()


def request_ip(request: Request) -> str:
    forwarded = (
        request.headers.get("x-forwarded-for")
        or ""
    ).strip()

    if forwarded:
        return forwarded.split(",")[0].strip()

    if request.client:
        return request.client.host or ""

    return ""


def bearer_token(request: Request) -> str:
    authorization = (
        request.headers.get("authorization")
        or ""
    ).strip()

    if authorization.lower().startswith("bearer "):
        return authorization[7:].strip()

    return ""


def request_session_token(
    request: Request,
) -> str:
    return (
        bearer_token(request)
        or request.cookies.get(COOKIE_NAME, "")
    ).strip()


def set_session_cookie(
    response: Response,
    raw_token: str,
) -> None:
    secure = cookie_secure()

    response.set_cookie(
        key=COOKIE_NAME,
        value=raw_token,
        max_age=SESSION_DAYS * 24 * 60 * 60,
        path="/",
        secure=secure,
        httponly=True,
        samesite="none" if secure else "lax",
    )


def delete_session_cookie(
    response: Response,
) -> None:
    secure = cookie_secure()

    response.delete_cookie(
        key=COOKIE_NAME,
        path="/",
        secure=secure,
        httponly=True,
        samesite="none" if secure else "lax",
    )


def require_authenticated_session(
    request: Request,
) -> dict:
    raw_token = request_session_token(request)

    if not raw_token:
        raise HTTPException(
            status_code=401,
            detail="Authentication required.",
        )

    authenticated = get_session_user(
        hash_session_token(raw_token)
    )

    if not authenticated:
        raise HTTPException(
            status_code=401,
            detail="Session is invalid or expired.",
        )

    return authenticated


@router.get("/health")
def auth_health():
    return {
        **auth_store_status(),
        "service": "authentication",
        "cookie_name": COOKIE_NAME,
        "cookie_secure": cookie_secure(),
        "supports_http_only_cookie": True,
        "supports_bearer_token": True,
    }


@router.post("/register", status_code=201)
def register_user(
    payload: RegisterPayload,
    request: Request,
    response: Response,
):
    try:
        email = normalize_email(payload.email)
        display_name = normalize_display_name(
            payload.display_name
        )
        password = validate_password(
            payload.password
        )
    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    if get_user_by_email(email):
        raise HTTPException(
            status_code=409,
            detail=(
                "An account with this email already exists."
            ),
        )

    try:
        user = create_user(
            email=email,
            display_name=display_name,
            password_hash=hash_password(password),
        )
    except Exception as error:
        if get_user_by_email(email):
            raise HTTPException(
                status_code=409,
                detail=(
                    "An account with this email already exists."
                ),
            ) from error

        raise HTTPException(
            status_code=503,
            detail="Account storage is temporarily unavailable.",
        ) from error

    raw_token, token_hash = create_session_token()

    session = create_session(
        user_id=user["id"],
        token_hash=token_hash,
        user_agent=request.headers.get(
            "user-agent",
            "",
        ),
        ip_address=request_ip(request),
    )

    update_last_login(user["id"])
    set_session_cookie(response, raw_token)

    return {
        "ok": True,
        "message": "Account created.",
        "user": get_user_by_email(email),
        "session": session,
    }


@router.post("/login")
def login_user(
    payload: LoginPayload,
    request: Request,
    response: Response,
):
    try:
        email = normalize_email(payload.email)
    except ValueError:
        email = str(payload.email or "").strip().casefold()

    user_record = get_user_by_email(
        email,
        include_password=True,
    )

    encoded_password = (
        user_record["password_hash"]
        if user_record
        else DUMMY_PASSWORD_HASH
    )

    password_valid = verify_password(
        payload.password,
        encoded_password,
    )

    if (
        not user_record
        or not password_valid
        or not bool(user_record["is_active"])
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password.",
        )

    raw_token, token_hash = create_session_token()

    session = create_session(
        user_id=int(user_record["id"]),
        token_hash=token_hash,
        user_agent=request.headers.get(
            "user-agent",
            "",
        ),
        ip_address=request_ip(request),
    )

    update_last_login(int(user_record["id"]))
    set_session_cookie(response, raw_token)

    return {
        "ok": True,
        "message": "Login successful.",
        "user": get_user_by_email(email),
        "session": session,
    }


@router.get("/me")
def current_user(request: Request):
    authenticated = require_authenticated_session(
        request
    )

    return {
        "ok": True,
        **authenticated,
    }


@router.post("/logout")
def logout_user(
    request: Request,
    response: Response,
):
    raw_token = request_session_token(request)

    revoked = False

    if raw_token:
        revoked = revoke_session(
            hash_session_token(raw_token)
        )

    delete_session_cookie(response)

    return {
        "ok": True,
        "message": "Logged out.",
        "session_revoked": revoked,
    }

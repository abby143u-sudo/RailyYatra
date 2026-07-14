from __future__ import annotations

import os

from fastapi import (
    APIRouter,
    HTTPException,
    Request,
    Response,
)
from pydantic import BaseModel, Field

from backend.api.cors_public_middleware import (
    configured_allowed_origins,
)

from backend.api.auth_rate_limit import (
    auth_rate_limit_status,
    clear_login_failures,
    consume_login_ip_attempt,
    consume_registration_attempt,
    login_failure_retry_after,
    record_login_failure,
)

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
    delete_user_account,
    get_session_user,
    get_user_by_email,
    get_user_by_id,
    revoke_session,
    revoke_user_sessions,
    update_last_login,
    update_user_password,
)
from backend.api.auth_action_security import (
    create_auth_action_token,
    hash_auth_action_token,
)
from backend.api.auth_email_delivery import (
    send_password_reset_email,
    send_verification_email,
)
from backend.api.auth_recovery_rate_limit import (
    auth_recovery_rate_limit_status,
    consume_password_reset_attempt,
    consume_verification_resend_attempt,
)
from backend.api.auth_recovery_store import (
    EMAIL_VERIFICATION_PURPOSE,
    EMAIL_VERIFICATION_SECONDS,
    PASSWORD_RESET_PURPOSE,
    PASSWORD_RESET_SECONDS,
    auth_recovery_store_status,
    consume_auth_action_token,
    email_verification_status,
    issue_auth_action_token,
    mark_email_verified,
    revoke_auth_action_tokens,
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



class ChangePasswordPayload(BaseModel):
    current_password: str = Field(
        ...,
        min_length=1,
        max_length=128,
    )
    new_password: str = Field(
        ...,
        min_length=10,
        max_length=128,
    )


class DeleteAccountPayload(BaseModel):
    password: str = Field(
        ...,
        min_length=1,
        max_length=128,
    )
    confirmation: str = Field(
        ...,
        min_length=1,
        max_length=40,
    )


class EmailVerificationTokenPayload(BaseModel):
    token: str = Field(
        ...,
        min_length=20,
        max_length=500,
    )


class ForgotPasswordPayload(BaseModel):
    email: str = Field(
        ...,
        min_length=3,
        max_length=254,
    )


class ResetPasswordPayload(BaseModel):
    token: str = Field(
        ...,
        min_length=20,
        max_length=500,
    )
    new_password: str = Field(
        ...,
        min_length=10,
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



def require_safe_write_origin(
    request: Request,
) -> None:
    origin = str(
        request.headers.get("origin") or ""
    ).strip().rstrip("/")

    # CLI, native and server-to-server clients may omit Origin.
    if not origin:
        return

    allowed = {
        item.rstrip("/")
        for item in configured_allowed_origins()
    }

    hostname = request.url.hostname

    if hostname:
        allowed.add(f"https://{hostname}")
        allowed.add(f"http://{hostname}")

    if origin not in allowed:
        raise HTTPException(
            status_code=403,
            detail="Request origin is not allowed.",
        )



def raise_auth_rate_limit(
    message: str,
    retry_after: int,
) -> None:
    raise HTTPException(
        status_code=429,
        detail=message,
        headers={
            "Retry-After": str(
                max(1, int(retry_after))
            ),
        },
    )


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


def user_with_email_status(
    user: dict | None,
) -> dict | None:
    if not user:
        return None

    enriched = dict(user)
    enriched.update(
        email_verification_status(int(user["id"]))
    )
    return enriched


def issue_verification_for_user(
    user: dict,
    request: Request,
) -> bool:
    raw_token, token_hash = create_auth_action_token()

    issue_auth_action_token(
        user_id=int(user["id"]),
        purpose=EMAIL_VERIFICATION_PURPOSE,
        token_hash=token_hash,
        ttl_seconds=EMAIL_VERIFICATION_SECONDS,
        requested_ip=request_ip(request),
    )

    return send_verification_email(
        str(user["email"]),
        str(user["display_name"]),
        raw_token,
    )


@router.get("/health")
def auth_health():
    return {
        **auth_store_status(),
        "service": "authentication",
        "cookie_name": COOKIE_NAME,
        "cookie_secure": cookie_secure(),
        "supports_http_only_cookie": True,
        "supports_bearer_token": True,
        "rate_limits": auth_rate_limit_status(),
        "recovery": {
            **auth_recovery_store_status(),
            "rate_limits": (
                auth_recovery_rate_limit_status()
            ),
        },
    }


@router.post("/register", status_code=201)
def register_user(
    payload: RegisterPayload,
    request: Request,
    response: Response,
):
    require_safe_write_origin(request)

    registration_retry_after = (
        consume_registration_attempt(
            request_ip(request)
        )
    )

    if registration_retry_after:
        raise_auth_rate_limit(
            (
                "Too many account creation attempts. "
                "Please wait and try again."
            ),
            registration_retry_after,
        )

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

    verification_email_sent = issue_verification_for_user(
        user,
        request,
    )

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
        "user": user_with_email_status(
            get_user_by_email(email)
        ),
        "session": session,
        "verification_email_sent": (
            verification_email_sent
        ),
    }


@router.post("/login")
def login_user(
    payload: LoginPayload,
    request: Request,
    response: Response,
):
    require_safe_write_origin(request)

    client_ip = request_ip(request)

    login_retry_after = (
        consume_login_ip_attempt(client_ip)
    )

    if login_retry_after:
        raise_auth_rate_limit(
            (
                "Too many login attempts. "
                "Please wait and try again."
            ),
            login_retry_after,
        )

    try:
        email = normalize_email(payload.email)
    except ValueError:
        email = str(payload.email or "").strip().casefold()

    failure_retry_after = (
        login_failure_retry_after(
            client_ip,
            email,
        )
    )

    if failure_retry_after:
        raise_auth_rate_limit(
            (
                "Too many failed login attempts. "
                "Please wait before trying again."
            ),
            failure_retry_after,
        )

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
        failure_retry_after = (
            record_login_failure(
                client_ip,
                email,
            )
        )

        if failure_retry_after:
            raise_auth_rate_limit(
                (
                    "Too many failed login attempts. "
                    "Please wait before trying again."
                ),
                failure_retry_after,
            )

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password.",
        )

    clear_login_failures(
        client_ip,
        email,
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
        "user": user_with_email_status(
            get_user_by_email(email)
        ),
        "session": session,
    }


@router.get("/me")
def current_user(request: Request):
    authenticated = require_authenticated_session(
        request
    )

    authenticated = dict(authenticated)
    authenticated["user"] = user_with_email_status(
        authenticated["user"]
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
    require_safe_write_origin(request)

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


@router.post("/change-password")
def change_password(
    payload: ChangePasswordPayload,
    request: Request,
    response: Response,
):
    require_safe_write_origin(request)

    authenticated = require_authenticated_session(
        request
    )
    user = authenticated["user"]

    user_record = get_user_by_email(
        user["email"],
        include_password=True,
    )

    if (
        not user_record
        or not verify_password(
            payload.current_password,
            user_record["password_hash"],
        )
    ):
        raise HTTPException(
            status_code=401,
            detail="Current password is incorrect.",
        )

    try:
        new_password = validate_password(
            payload.new_password
        )
    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    if verify_password(
        new_password,
        user_record["password_hash"],
    ):
        raise HTTPException(
            status_code=422,
            detail=(
                "New password must be different "
                "from the current password."
            ),
        )

    user_id = int(user_record["id"])

    updated = update_user_password(
        user_id=user_id,
        password_hash=hash_password(new_password),
    )

    if not updated:
        raise HTTPException(
            status_code=503,
            detail="Password could not be updated.",
        )

    sessions_revoked = revoke_user_sessions(user_id)

    raw_token, token_hash = create_session_token()

    session = create_session(
        user_id=user_id,
        token_hash=token_hash,
        user_agent=request.headers.get(
            "user-agent",
            "",
        ),
        ip_address=request_ip(request),
    )

    set_session_cookie(response, raw_token)

    return {
        "ok": True,
        "message": "Password changed successfully.",
        "user": user_with_email_status(
            get_user_by_email(user["email"])
        ),
        "session": session,
        "sessions_revoked": sessions_revoked,
    }


@router.post("/logout-all")
def logout_all_devices(
    request: Request,
    response: Response,
):
    require_safe_write_origin(request)

    authenticated = require_authenticated_session(
        request
    )

    sessions_revoked = revoke_user_sessions(
        int(authenticated["user"]["id"])
    )

    delete_session_cookie(response)

    return {
        "ok": True,
        "message": "Logged out from all devices.",
        "sessions_revoked": sessions_revoked,
    }


@router.delete("/account")
def remove_current_account(
    payload: DeleteAccountPayload,
    request: Request,
    response: Response,
):
    require_safe_write_origin(request)

    authenticated = require_authenticated_session(
        request
    )
    user = authenticated["user"]

    if payload.confirmation.strip() != "DELETE MY ACCOUNT":
        raise HTTPException(
            status_code=422,
            detail=(
                'Confirmation must exactly match '
                '"DELETE MY ACCOUNT".'
            ),
        )

    user_record = get_user_by_email(
        user["email"],
        include_password=True,
    )

    if (
        not user_record
        or not verify_password(
            payload.password,
            user_record["password_hash"],
        )
    ):
        raise HTTPException(
            status_code=401,
            detail="Password is incorrect.",
        )

    deleted = delete_user_account(
        int(user_record["id"])
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Account was not found.",
        )

    delete_session_cookie(response)

    return {
        "ok": True,
        "message": "Account permanently deleted.",
        "account_deleted": True,
    }

@router.get("/email-verification/status")
def current_email_verification_status(
    request: Request,
):
    authenticated = require_authenticated_session(
        request
    )
    user = authenticated["user"]

    return {
        "ok": True,
        **email_verification_status(int(user["id"])),
    }


@router.post("/email-verification/resend")
def resend_email_verification(
    request: Request,
):
    require_safe_write_origin(request)

    authenticated = require_authenticated_session(
        request
    )
    user = authenticated["user"]
    user_id = int(user["id"])
    status = email_verification_status(user_id)

    if status["email_verified"]:
        return {
            "ok": True,
            "message": "Email address is already verified.",
            **status,
        }

    retry_after = consume_verification_resend_attempt(
        request_ip(request),
        user_id,
    )

    if retry_after:
        raise_auth_rate_limit(
            (
                "Too many verification email requests. "
                "Please wait and try again."
            ),
            retry_after,
        )

    email_sent = issue_verification_for_user(
        user,
        request,
    )

    return {
        "ok": True,
        "message": "Verification email requested.",
        "verification_email_sent": email_sent,
        **email_verification_status(user_id),
    }


@router.post("/email-verification/confirm")
def confirm_email_verification(
    payload: EmailVerificationTokenPayload,
    request: Request,
):
    require_safe_write_origin(request)

    token_record = consume_auth_action_token(
        hash_auth_action_token(payload.token),
        EMAIL_VERIFICATION_PURPOSE,
    )

    if not token_record:
        raise HTTPException(
            status_code=400,
            detail=(
                "Verification link is invalid or expired."
            ),
        )

    status = mark_email_verified(
        int(token_record["user_id"])
    )

    return {
        "ok": True,
        "message": "Email address verified.",
        **status,
    }


@router.post("/forgot-password", status_code=202)
def request_password_reset(
    payload: ForgotPasswordPayload,
    request: Request,
):
    require_safe_write_origin(request)

    try:
        email = normalize_email(payload.email)
    except ValueError:
        email = str(payload.email or "").strip().casefold()

    retry_after = consume_password_reset_attempt(
        request_ip(request),
        email,
    )

    if retry_after:
        raise_auth_rate_limit(
            (
                "Too many password reset requests. "
                "Please wait and try again."
            ),
            retry_after,
        )

    user = get_user_by_email(email)

    if user and bool(user["is_active"]):
        raw_token, token_hash = create_auth_action_token()

        issue_auth_action_token(
            user_id=int(user["id"]),
            purpose=PASSWORD_RESET_PURPOSE,
            token_hash=token_hash,
            ttl_seconds=PASSWORD_RESET_SECONDS,
            requested_ip=request_ip(request),
        )

        send_password_reset_email(
            str(user["email"]),
            str(user["display_name"]),
            raw_token,
        )

    return {
        "ok": True,
        "message": (
            "If an active account exists for that email, "
            "a password reset link has been requested."
        ),
    }


@router.post("/reset-password")
def reset_password(
    payload: ResetPasswordPayload,
    request: Request,
    response: Response,
):
    require_safe_write_origin(request)

    try:
        new_password = validate_password(
            payload.new_password
        )
    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    token_record = consume_auth_action_token(
        hash_auth_action_token(payload.token),
        PASSWORD_RESET_PURPOSE,
    )

    if not token_record:
        raise HTTPException(
            status_code=400,
            detail="Reset link is invalid or expired.",
        )

    user_id = int(token_record["user_id"])
    user = get_user_by_id(user_id)

    if not user or not bool(user["is_active"]):
        raise HTTPException(
            status_code=400,
            detail="Reset link is invalid or expired.",
        )

    updated = update_user_password(
        user_id=user_id,
        password_hash=hash_password(new_password),
    )

    if not updated:
        raise HTTPException(
            status_code=503,
            detail="Password could not be updated.",
        )

    sessions_revoked = revoke_user_sessions(user_id)
    revoke_auth_action_tokens(
        user_id,
        PASSWORD_RESET_PURPOSE,
    )
    delete_session_cookie(response)

    return {
        "ok": True,
        "message": "Password reset successfully.",
        "sessions_revoked": sessions_revoked,
    }

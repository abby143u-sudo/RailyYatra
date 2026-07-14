from __future__ import annotations

import math
import os
import time
from collections import deque
from threading import Lock


def env_integer(
    name: str,
    default: int,
    maximum: int,
) -> int:
    try:
        value = int(os.environ.get(name, str(default)))
    except (TypeError, ValueError):
        value = default

    return max(1, min(value, maximum))


RECOVERY_WINDOW_SECONDS = env_integer(
    "RAILYATRA_AUTH_RECOVERY_WINDOW_SECONDS",
    60 * 60,
    7 * 24 * 60 * 60,
)
PASSWORD_RESET_IP_MAX = env_integer(
    "RAILYATRA_AUTH_PASSWORD_RESET_IP_MAX",
    10,
    1000,
)
PASSWORD_RESET_EMAIL_MAX = env_integer(
    "RAILYATRA_AUTH_PASSWORD_RESET_EMAIL_MAX",
    3,
    100,
)
VERIFICATION_RESEND_IP_MAX = env_integer(
    "RAILYATRA_AUTH_VERIFICATION_RESEND_IP_MAX",
    10,
    1000,
)
VERIFICATION_RESEND_USER_MAX = env_integer(
    "RAILYATRA_AUTH_VERIFICATION_RESEND_USER_MAX",
    3,
    100,
)


_password_reset_ip_attempts: dict[str, deque[float]] = {}
_password_reset_email_attempts: dict[str, deque[float]] = {}
_verification_ip_attempts: dict[str, deque[float]] = {}
_verification_user_attempts: dict[str, deque[float]] = {}

_rate_limit_lock = Lock()


def normalized_key(value: object) -> str:
    return str(value or "unknown").strip()[:300] or "unknown"


def _prune(
    bucket: deque[float],
    current_time: float,
) -> None:
    cutoff = current_time - RECOVERY_WINDOW_SECONDS

    while bucket and bucket[0] <= cutoff:
        bucket.popleft()


def _retry_after(
    bucket: deque[float],
    current_time: float,
) -> int:
    if not bucket:
        return 1

    remaining = (
        bucket[0]
        + RECOVERY_WINDOW_SECONDS
        - current_time
    )

    return max(1, int(math.ceil(remaining)))


def _consume(
    storage: dict[str, deque[float]],
    key: object,
    maximum: int,
) -> int:
    current_time = time.time()
    safe_key = normalized_key(key)

    with _rate_limit_lock:
        bucket = storage.setdefault(
            safe_key,
            deque(),
        )
        _prune(bucket, current_time)

        if len(bucket) >= maximum:
            return _retry_after(bucket, current_time)

        bucket.append(current_time)

    return 0


def consume_password_reset_attempt(
    ip_address: str,
    email: str,
) -> int:
    ip_retry = _consume(
        _password_reset_ip_attempts,
        ip_address,
        PASSWORD_RESET_IP_MAX,
    )
    email_retry = _consume(
        _password_reset_email_attempts,
        str(email or "").casefold(),
        PASSWORD_RESET_EMAIL_MAX,
    )

    return max(ip_retry, email_retry)


def consume_verification_resend_attempt(
    ip_address: str,
    user_id: int,
) -> int:
    ip_retry = _consume(
        _verification_ip_attempts,
        ip_address,
        VERIFICATION_RESEND_IP_MAX,
    )
    user_retry = _consume(
        _verification_user_attempts,
        user_id,
        VERIFICATION_RESEND_USER_MAX,
    )

    return max(ip_retry, user_retry)


def auth_recovery_rate_limit_status() -> dict:
    return {
        "mode": "in_process",
        "window_seconds": RECOVERY_WINDOW_SECONDS,
        "password_reset_ip_max": PASSWORD_RESET_IP_MAX,
        "password_reset_email_max": (
            PASSWORD_RESET_EMAIL_MAX
        ),
        "verification_resend_ip_max": (
            VERIFICATION_RESEND_IP_MAX
        ),
        "verification_resend_user_max": (
            VERIFICATION_RESEND_USER_MAX
        ),
    }


def reset_auth_recovery_rate_limits() -> None:
    """Used only by isolated automated tests."""
    with _rate_limit_lock:
        _password_reset_ip_attempts.clear()
        _password_reset_email_attempts.clear()
        _verification_ip_attempts.clear()
        _verification_user_attempts.clear()

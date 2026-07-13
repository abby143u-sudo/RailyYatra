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


LOGIN_FAILURE_MAX = env_integer(
    "RAILYATRA_AUTH_LOGIN_FAILURE_MAX",
    5,
    100,
)
LOGIN_WINDOW_SECONDS = env_integer(
    "RAILYATRA_AUTH_LOGIN_WINDOW_SECONDS",
    15 * 60,
    24 * 60 * 60,
)
LOGIN_IP_MAX = env_integer(
    "RAILYATRA_AUTH_LOGIN_IP_MAX",
    30,
    1000,
)
REGISTER_IP_MAX = env_integer(
    "RAILYATRA_AUTH_REGISTER_IP_MAX",
    10,
    1000,
)
REGISTER_WINDOW_SECONDS = env_integer(
    "RAILYATRA_AUTH_REGISTER_WINDOW_SECONDS",
    60 * 60,
    7 * 24 * 60 * 60,
)


_login_ip_attempts: dict[str, deque[float]] = {}
_login_failures: dict[str, deque[float]] = {}
_registration_attempts: dict[str, deque[float]] = {}

_rate_limit_lock = Lock()


def normalized_key(value: str) -> str:
    return str(value or "unknown").strip()[:300] or "unknown"


def login_failure_key(
    ip_address: str,
    email: str,
) -> str:
    return (
        f"{normalized_key(ip_address)}|"
        f"{normalized_key(email).casefold()}"
    )


def prune_bucket(
    bucket: deque[float],
    current_time: float,
    window_seconds: int,
) -> None:
    cutoff = current_time - window_seconds

    while bucket and bucket[0] <= cutoff:
        bucket.popleft()


def retry_after_seconds(
    bucket: deque[float],
    current_time: float,
    window_seconds: int,
) -> int:
    if not bucket:
        return 1

    remaining = (
        bucket[0]
        + window_seconds
        - current_time
    )

    return max(1, int(math.ceil(remaining)))


def consume_attempt(
    storage: dict[str, deque[float]],
    key: str,
    maximum: int,
    window_seconds: int,
) -> int:
    current_time = time.time()
    safe_key = normalized_key(key)

    with _rate_limit_lock:
        bucket = storage.setdefault(
            safe_key,
            deque(),
        )

        prune_bucket(
            bucket,
            current_time,
            window_seconds,
        )

        if len(bucket) >= maximum:
            return retry_after_seconds(
                bucket,
                current_time,
                window_seconds,
            )

        bucket.append(current_time)

    return 0


def blocked_retry_after(
    storage: dict[str, deque[float]],
    key: str,
    maximum: int,
    window_seconds: int,
) -> int:
    current_time = time.time()
    safe_key = normalized_key(key)

    with _rate_limit_lock:
        bucket = storage.setdefault(
            safe_key,
            deque(),
        )

        prune_bucket(
            bucket,
            current_time,
            window_seconds,
        )

        if len(bucket) >= maximum:
            return retry_after_seconds(
                bucket,
                current_time,
                window_seconds,
            )

    return 0


def consume_login_ip_attempt(
    ip_address: str,
) -> int:
    return consume_attempt(
        storage=_login_ip_attempts,
        key=ip_address,
        maximum=LOGIN_IP_MAX,
        window_seconds=LOGIN_WINDOW_SECONDS,
    )


def login_failure_retry_after(
    ip_address: str,
    email: str,
) -> int:
    return blocked_retry_after(
        storage=_login_failures,
        key=login_failure_key(
            ip_address,
            email,
        ),
        maximum=LOGIN_FAILURE_MAX,
        window_seconds=LOGIN_WINDOW_SECONDS,
    )


def record_login_failure(
    ip_address: str,
    email: str,
) -> int:
    key = login_failure_key(
        ip_address,
        email,
    )
    current_time = time.time()

    with _rate_limit_lock:
        bucket = _login_failures.setdefault(
            key,
            deque(),
        )

        prune_bucket(
            bucket,
            current_time,
            LOGIN_WINDOW_SECONDS,
        )

        bucket.append(current_time)

        if len(bucket) >= LOGIN_FAILURE_MAX:
            return retry_after_seconds(
                bucket,
                current_time,
                LOGIN_WINDOW_SECONDS,
            )

    return 0


def clear_login_failures(
    ip_address: str,
    email: str,
) -> None:
    key = login_failure_key(
        ip_address,
        email,
    )

    with _rate_limit_lock:
        _login_failures.pop(key, None)


def consume_registration_attempt(
    ip_address: str,
) -> int:
    return consume_attempt(
        storage=_registration_attempts,
        key=ip_address,
        maximum=REGISTER_IP_MAX,
        window_seconds=REGISTER_WINDOW_SECONDS,
    )


def auth_rate_limit_status() -> dict:
    return {
        "mode": "in_process",
        "login_failure_max": LOGIN_FAILURE_MAX,
        "login_window_seconds": (
            LOGIN_WINDOW_SECONDS
        ),
        "login_ip_max": LOGIN_IP_MAX,
        "register_ip_max": REGISTER_IP_MAX,
        "register_window_seconds": (
            REGISTER_WINDOW_SECONDS
        ),
    }


def reset_auth_rate_limits() -> None:
    """Used only by isolated automated tests."""
    with _rate_limit_lock:
        _login_ip_attempts.clear()
        _login_failures.clear()
        _registration_attempts.clear()

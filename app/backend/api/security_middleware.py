import os
import time
from collections import defaultdict, deque

from fastapi import Request
from fastapi.responses import JSONResponse


RATE_LIMIT_WINDOW_SECONDS = int(
    os.environ.get(
        "RAILYATRA_RATE_LIMIT_WINDOW_SECONDS",
        "60",
    )
)
RATE_LIMIT_MAX_REQUESTS = int(
    os.environ.get(
        "RAILYATRA_RATE_LIMIT_MAX_REQUESTS",
        "180",
    )
)
RATE_LIMIT_WRITE_MAX_REQUESTS = int(
    os.environ.get(
        "RAILYATRA_RATE_LIMIT_WRITE_MAX_REQUESTS",
        "40",
    )
)
ADMIN_TOKEN = os.environ.get(
    "RAILYATRA_ADMIN_TOKEN",
    "",
).strip()


_request_log = defaultdict(deque)
_write_request_log = defaultdict(deque)


def client_key(request: Request) -> str:
    forwarded_for = request.headers.get(
        "x-forwarded-for",
        "",
    )

    if forwarded_for:
        return (
            forwarded_for.split(",")[0].strip()
            or "unknown"
        )

    if request.client and request.client.host:
        return request.client.host

    return "unknown"


def clean_old_entries(
    bucket,
    current_time: float,
) -> None:
    cutoff = (
        current_time
        - RATE_LIMIT_WINDOW_SECONDS
    )

    while bucket and bucket[0] < cutoff:
        bucket.popleft()


def rate_limited(
    storage,
    key: str,
    max_requests: int,
) -> bool:
    current_time = time.time()
    bucket = storage[key]

    clean_old_entries(
        bucket,
        current_time,
    )

    if len(bucket) >= max_requests:
        return True

    bucket.append(current_time)
    return False


def error_response(
    code: str,
    message: str,
    status_code: int,
    path: str,
    headers: dict[str, str] | None = None,
):
    return JSONResponse(
        status_code=status_code,
        headers=headers,
        content={
            "ok": False,
            "error": {
                "code": code,
                "message": message,
                "status_code": status_code,
                "path": path,
                "details": None,
                "timestamp": time.strftime(
                    "%Y-%m-%dT%H:%M:%SZ",
                    time.gmtime(),
                ),
            },
        },
    )


def request_has_valid_admin_token(
    request: Request,
) -> bool:
    if not ADMIN_TOKEN:
        return True

    header_token = request.headers.get(
        "x-railyatra-admin-token",
        "",
    ).strip()

    auth_header = request.headers.get(
        "authorization",
        "",
    ).strip()

    bearer_token = ""

    if auth_header.lower().startswith(
        "bearer "
    ):
        bearer_token = auth_header[7:].strip()

    return (
        header_token == ADMIN_TOKEN
        or bearer_token == ADMIN_TOKEN
    )


def register_security_middleware(app):
    @app.middleware("http")
    async def security_middleware(
        request: Request,
        call_next,
    ):
        path = request.url.path
        method = request.method.upper()

        if (
            path.startswith("/admin")
            and not request_has_valid_admin_token(
                request
            )
        ):
            return error_response(
                "admin_auth_required",
                "Admin token is required",
                401,
                path,
            )

        key = client_key(request)

        if rate_limited(
            _request_log,
            key,
            RATE_LIMIT_MAX_REQUESTS,
        ):
            return error_response(
                "rate_limit_exceeded",
                (
                    "Too many requests. "
                    "Please wait and try again."
                ),
                429,
                path,
                headers={
                    "Retry-After": str(
                        RATE_LIMIT_WINDOW_SECONDS
                    ),
                },
            )

        if method in {
            "POST",
            "PUT",
            "PATCH",
            "DELETE",
        }:
            write_key = f"{key}:{path}"

            if rate_limited(
                _write_request_log,
                write_key,
                RATE_LIMIT_WRITE_MAX_REQUESTS,
            ):
                return error_response(
                    "write_rate_limit_exceeded",
                    (
                        "Too many write requests. "
                        "Please wait and try again."
                    ),
                    429,
                    path,
                    headers={
                        "Retry-After": str(
                            RATE_LIMIT_WINDOW_SECONDS
                        ),
                    },
                )

        response = await call_next(request)

        response.headers[
            "X-RailYatra-RateLimit-Window"
        ] = str(RATE_LIMIT_WINDOW_SECONDS)

        response.headers[
            "X-RailYatra-Admin-Protection"
        ] = (
            "enabled"
            if ADMIN_TOKEN
            else "optional"
        )

        return response

    return app

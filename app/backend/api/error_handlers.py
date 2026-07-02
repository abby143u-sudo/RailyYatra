from datetime import datetime, timezone
from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()

def build_error_payload(code: str, message: str, status_code: int, path: str, details: Any | None = None) -> dict[str, Any]:
    return {
        "ok": False,
        "error": {
            "code": code,
            "message": message,
            "status_code": status_code,
            "path": path,
            "details": details,
            "timestamp": utc_now(),
        },
    }

def register_error_handlers(app):
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        detail = exc.detail
        message = detail if isinstance(detail, str) else "HTTP error"
        return JSONResponse(
            status_code=exc.status_code,
            content=build_error_payload(
                code="http_error",
                message=message,
                status_code=exc.status_code,
                path=str(request.url.path),
                details=detail if not isinstance(detail, str) else None,
            ),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content=build_error_payload(
                code="validation_error",
                message="Request validation failed",
                status_code=422,
                path=str(request.url.path),
                details=exc.errors(),
            ),
        )

    @app.exception_handler(Exception)
    async def unexpected_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content=build_error_payload(
                code="internal_server_error",
                message="Internal server error",
                status_code=500,
                path=str(request.url.path),
                details={"type": exc.__class__.__name__},
            ),
        )

    return app

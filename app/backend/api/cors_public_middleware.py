import os
from fastapi import Request, Response
from fastapi.responses import JSONResponse

DEFAULT_ALLOWED_ORIGINS = {
    "https://raily-yatra.vercel.app",
    "https://rail-yatra.vercel.app",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
}

def configured_allowed_origins() -> set[str]:
    raw = os.environ.get("RAILYATRA_ALLOWED_ORIGINS", "")
    values = {item.strip() for item in raw.split(",") if item.strip()}
    return values | DEFAULT_ALLOWED_ORIGINS

def is_allowed_origin(origin: str | None) -> bool:
    if not origin:
        return False
    if origin in configured_allowed_origins():
        return True
    return origin.endswith(".vercel.app") and origin.startswith("https://")

def cors_headers(origin: str | None) -> dict[str, str]:
    headers = {
        "Access-Control-Allow-Methods": "GET,POST,PUT,PATCH,DELETE,OPTIONS",
        "Access-Control-Allow-Headers": "Authorization,Content-Type,X-RailYatra-Admin-Token,X-Requested-With",
        "Access-Control-Max-Age": "86400",
    }
    if is_allowed_origin(origin):
        headers["Access-Control-Allow-Origin"] = origin or ""
        headers["Vary"] = "Origin"
    return headers

async def railyatra_cors_middleware(request: Request, call_next):
    origin = request.headers.get("origin")
    headers = cors_headers(origin)

    if request.method.upper() == "OPTIONS":
        return Response(status_code=204, headers=headers)

    try:
        response = await call_next(request)
    except Exception as error:
        response = JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "error": {
                    "code": "internal_server_error",
                    "message": "Backend request failed.",
                    "details": {"type": type(error).__name__},
                },
            },
        )

    for key, value in headers.items():
        response.headers[key] = value
    return response

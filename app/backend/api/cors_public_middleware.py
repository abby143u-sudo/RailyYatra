import os
from fastapi import Request, Response

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

def cors_headers(origin: str | None) -> dict[str, str]:
    allowed = configured_allowed_origins()
    selected_origin = origin if origin in allowed else ""
    headers = {
        "Access-Control-Allow-Methods": "GET,POST,PUT,PATCH,DELETE,OPTIONS",
        "Access-Control-Allow-Headers": "Authorization,Content-Type,X-RailYatra-Admin-Token,X-Requested-With",
        "Access-Control-Max-Age": "86400",
    }
    if selected_origin:
        headers["Access-Control-Allow-Origin"] = selected_origin
        headers["Vary"] = "Origin"
    return headers

async def railyatra_cors_middleware(request: Request, call_next):
    origin = request.headers.get("origin")
    headers = cors_headers(origin)

    if request.method.upper() == "OPTIONS":
        return Response(status_code=204, headers=headers)

    response = await call_next(request)
    for key, value in headers.items():
        response.headers[key] = value
    return response

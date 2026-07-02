import os
from urllib.parse import urlparse

def mask_database_url(value: str) -> str:
    if not value:
        return ""

    parsed = urlparse(value)
    if not parsed.scheme:
        return "configured"

    host = parsed.hostname or "unknown-host"
    port = f":{parsed.port}" if parsed.port else ""
    database = parsed.path.lstrip("/") or "unknown-db"
    return f"{parsed.scheme}://***:***@{host}{port}/{database}"

def get_database_status() -> dict:
    database_url = os.environ.get("DATABASE_URL", "").strip()
    demo_database_url = os.environ.get("RAILYATRA_DEMO_DATABASE_URL", "").strip()

    configured_url = database_url or demo_database_url
    mode = "postgresql" if configured_url.startswith(("postgres://", "postgresql://")) else "sqlite"

    return {
        "ok": True,
        "mode": mode,
        "database_url_configured": bool(configured_url),
        "masked_database_url": mask_database_url(configured_url),
        "runtime_store": "managed_postgresql" if mode == "postgresql" else "runtime_sqlite",
        "recommendation": "Use managed PostgreSQL for production feedback, analytics, users and admin audit logs.",
    }

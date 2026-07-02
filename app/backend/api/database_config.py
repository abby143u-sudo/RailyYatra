from backend.api.demo_store import get_store_status

def get_database_status() -> dict:
    status = get_store_status()
    return {
        "ok": True,
        "mode": status["mode"],
        "database_url_configured": status["database_url_configured"],
        "masked_database_url": status["masked_database_url"],
        "runtime_store": status["runtime_store"],
        "sqlite_path": status["sqlite_path"],
        "store_module": "backend.api.demo_store",
        "recommendation": "Use managed PostgreSQL for production feedback, analytics, users and admin audit logs.",
    }

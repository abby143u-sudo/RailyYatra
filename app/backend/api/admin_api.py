from collections import Counter

from fastapi import APIRouter, Request

from backend.api.admin_auth import admin_auth_status, require_admin_request
from backend.api.admin_audit import read_admin_audit_logs, save_admin_audit_log
from backend.api.database_config import get_database_status
from backend.api.demo_store import read_analytics_entries, read_feedback_entries

router = APIRouter()

def count_by_type(entries: list[dict], default_type: str) -> dict:
    counter = Counter()
    for entry in entries:
        counter[str(entry.get("type") or default_type)] += 1
    return dict(counter)

def safe_limit(limit: int, default: int = 50, maximum: int = 200) -> int:
    try:
        value = int(limit or default)
    except Exception:
        value = default
    return max(1, min(value, maximum))

@router.get("/admin/health")
async def admin_health():
    return {
        "ok": True,
        "service": "admin",
        "status": "ok",
        "scope": "internal_demo_summary",
        **admin_auth_status(),
    }

@router.get("/admin/feedback-summary")
async def feedback_summary(request: Request, limit: int = 50):
    auth = require_admin_request(request)
    entries = read_feedback_entries(safe_limit(limit))
    save_admin_audit_log("admin_feedback_summary_read", "/admin/feedback-summary", request, auth.get("admin_id", "unknown_admin"), {"limit": limit})
    return {
        "ok": True,
        "count": len(entries),
        "by_type": count_by_type(entries, "general"),
        "latest": entries,
    }

@router.get("/admin/analytics-summary")
async def analytics_summary(request: Request, limit: int = 50):
    auth = require_admin_request(request)
    entries = read_analytics_entries(safe_limit(limit, 50, 500))
    save_admin_audit_log("admin_analytics_summary_read", "/admin/analytics-summary", request, auth.get("admin_id", "unknown_admin"), {"limit": limit})
    return {
        "ok": True,
        "count": len(entries),
        "by_type": count_by_type(entries, "custom_event"),
        "latest": entries,
    }

@router.get("/admin/demo-summary")
async def demo_summary(request: Request, limit: int = 50):
    auth = require_admin_request(request)
    feedback_entries = read_feedback_entries(safe_limit(limit))
    analytics_entries = read_analytics_entries(safe_limit(limit, 50, 500))
    save_admin_audit_log("admin_demo_summary_read", "/admin/demo-summary", request, auth.get("admin_id", "unknown_admin"), {"limit": limit})
    return {
        "ok": True,
        "product": "RailYatra",
        "mode": "real railway route recommendation preview",
        "feedback": {
            "count": len(feedback_entries),
            "by_type": count_by_type(feedback_entries, "general"),
            "latest": feedback_entries,
        },
        "analytics": {
            "count": len(analytics_entries),
            "by_type": count_by_type(analytics_entries, "custom_event"),
            "latest": analytics_entries,
        },
        "live_feature_boundary": {
            "booking": False,
            "payment": False,
            "pnr": False,
            "live_fare": False,
            "live_availability": False,
        },
    }

@router.get("/admin/database-status")
async def database_status(request: Request):
    auth = require_admin_request(request)
    save_admin_audit_log("admin_database_status_read", "/admin/database-status", request, auth.get("admin_id", "unknown_admin"), {})
    return get_database_status()

@router.get("/admin/auth-status")
async def get_admin_auth_status(request: Request):
    auth = require_admin_request(request)
    audit_result = save_admin_audit_log("admin_auth_status", "/admin/auth-status", request, auth.get("admin_id", "unknown_admin"), {"auth_enabled": auth.get("admin_auth_enabled")})
    return {
        "ok": True,
        **admin_auth_status(),
        "auth_mode": auth.get("auth_mode"),
        "audit_saved": audit_result.get("ok", False),
    }

@router.get("/admin/audit-logs")
async def get_admin_audit_logs(request: Request, limit: int = 50):
    auth = require_admin_request(request)
    audit_result = save_admin_audit_log("admin_audit_logs_read", "/admin/audit-logs", request, auth.get("admin_id", "unknown_admin"), {"limit": limit})
    logs = read_admin_audit_logs(safe_limit(limit))
    return {
        "ok": True,
        "count": len(logs),
        "logs": logs,
        "auth": admin_auth_status(),
        "audit_saved": audit_result.get("ok", False),
    }

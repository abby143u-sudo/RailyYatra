from collections import Counter
from typing import Any

from fastapi import APIRouter

from backend.api.feedback_api import read_feedback_entries
from backend.api.analytics_api import read_analytics_entries
from backend.api.database_config import get_database_status

router = APIRouter(tags=["admin"])

def summarize_by_type(entries: list[dict[str, Any]]) -> dict[str, int]:
    counter = Counter(str(entry.get("type") or "unknown") for entry in entries)
    return dict(counter)

@router.get("/admin/health")
async def admin_health():
    return {
        "ok": True,
        "service": "admin",
        "status": "ok",
        "scope": "internal_demo_summary",
    }

@router.get("/admin/feedback-summary")
async def feedback_summary(limit: int = 50):
    safe_limit = max(1, min(int(limit or 50), 200))
    entries = read_feedback_entries(safe_limit)

    return {
        "ok": True,
        "type": "feedback_summary",
        "count": len(entries),
        "by_type": summarize_by_type(entries),
        "latest": entries[:10],
    }

@router.get("/admin/analytics-summary")
async def analytics_summary(limit: int = 100):
    safe_limit = max(1, min(int(limit or 100), 500))
    entries = read_analytics_entries(safe_limit)

    return {
        "ok": True,
        "type": "analytics_summary",
        "count": len(entries),
        "by_type": summarize_by_type(entries),
        "latest": entries[:10],
    }

@router.get("/admin/demo-summary")
async def demo_summary():
    feedback_entries = read_feedback_entries(100)
    analytics_entries = read_analytics_entries(200)

    return {
        "ok": True,
        "product": "RailYatra",
        "mode": "real railway route recommendation preview",
        "feedback": {
            "count": len(feedback_entries),
            "by_type": summarize_by_type(feedback_entries),
            "latest": feedback_entries[:5],
        },
        "analytics": {
            "count": len(analytics_entries),
            "by_type": summarize_by_type(analytics_entries),
            "latest": analytics_entries[:5],
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
async def database_status():
    return get_database_status()


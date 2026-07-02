from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.api.demo_store import get_store_status, read_analytics_entries, save_analytics_entry

router = APIRouter(tags=["analytics"])

class AnalyticsEventPayload(BaseModel):
    type: str = Field(..., min_length=1, max_length=80)
    details: dict[str, Any] = Field(default_factory=dict)
    page: str = Field(default="", max_length=500)
    created_at: str | None = None

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def safe_event_type(value: str) -> str:
    allowed = {"page_view", "main_search_submit", "feedback_view", "saved_route_apply", "feedback_submit"}
    cleaned = str(value or "").strip().lower()
    return cleaned if cleaned in allowed else "custom_event"

@router.get("/analytics/health")
async def analytics_health():
    store_status = get_store_status()
    return {"ok": True, "service": "analytics", "status": "ok", "storage": store_status["mode"], "database_url_configured": store_status["database_url_configured"], "path": store_status["sqlite_path"], "runtime_store": store_status["runtime_store"]}

@router.post("/analytics/event")
async def create_analytics_event(payload: AnalyticsEventPayload):
    entry: dict[str, Any] = {"type": safe_event_type(payload.type), "details": payload.details if isinstance(payload.details, dict) else {}, "page": payload.page.strip(), "client_created_at": payload.created_at, "server_created_at": now_iso(), "source": "public_demo"}
    try:
        saved_entry = save_analytics_entry(entry)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Analytics storage failed: {error}") from error
    return {"ok": True, "message": "Analytics event saved", "event": saved_entry}

@router.get("/analytics/events")
async def list_analytics_events(limit: int = 50):
    safe_limit = max(1, min(int(limit or 50), 200))
    entries = read_analytics_entries(safe_limit)
    return {"ok": True, "count": len(entries), "limit": safe_limit, "events": entries}

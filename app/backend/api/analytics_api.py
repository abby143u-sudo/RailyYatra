from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(tags=["analytics"])

ANALYTICS_FILE = Path(__file__).resolve().parents[2] / "data" / "analytics" / "events.jsonl"

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

def read_analytics_entries(limit: int = 50) -> list[dict[str, Any]]:
    if not ANALYTICS_FILE.exists():
        return []

    entries: list[dict[str, Any]] = []
    import json
    for line in ANALYTICS_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            item = json.loads(line)
            if isinstance(item, dict):
                entries.append(item)
        except Exception:
            continue

    return list(reversed(entries))[: max(1, min(limit, 200))]

@router.get("/analytics/health")
async def analytics_health():
    return {
        "service": "analytics",
        "status": "ok",
        "storage": "jsonl",
        "path": str(ANALYTICS_FILE),
    }

@router.post("/analytics/event")
async def create_analytics_event(payload: AnalyticsEventPayload):
    entry = {
        "type": safe_event_type(payload.type),
        "details": payload.details if isinstance(payload.details, dict) else {},
        "page": payload.page.strip(),
        "client_created_at": payload.created_at,
        "server_created_at": now_iso(),
        "source": "public_demo",
    }

    try:
        import json
        ANALYTICS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with ANALYTICS_FILE.open("a", encoding="utf-8") as file:
            file.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Analytics storage failed: {error}") from error

    return {
        "ok": True,
        "message": "Analytics event saved",
        "event": entry,
    }

@router.get("/analytics/events")
async def list_analytics_events(limit: int = 50):
    safe_limit = max(1, min(int(limit or 50), 200))
    entries = read_analytics_entries(safe_limit)

    return {
        "ok": True,
        "count": len(entries),
        "limit": safe_limit,
        "events": entries,
    }

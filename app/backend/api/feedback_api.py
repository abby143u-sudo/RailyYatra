from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.api.demo_store import get_store_status, read_feedback_entries, save_feedback_entry

router = APIRouter(tags=["feedback"])

class FeedbackPayload(BaseModel):
    type: str = Field(default="general", max_length=50)
    message: str = Field(..., min_length=1, max_length=2000)
    page: str = Field(default="", max_length=500)
    created_at: str | None = None

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def safe_feedback_type(value: str) -> str:
    allowed = {"general", "bug", "route_quality", "ui", "product_idea"}
    cleaned = str(value or "general").strip().lower()
    return cleaned if cleaned in allowed else "general"

@router.get("/feedback/health")
async def feedback_health():
    store_status = get_store_status()
    return {"ok": True, "service": "feedback", "status": "ok", "storage": store_status["mode"], "database_url_configured": store_status["database_url_configured"], "path": store_status["sqlite_path"], "runtime_store": store_status["runtime_store"]}

@router.post("/feedback")
async def create_feedback(payload: FeedbackPayload):
    message = payload.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Feedback message is required")
    entry: dict[str, Any] = {"type": safe_feedback_type(payload.type), "message": message, "page": payload.page.strip(), "client_created_at": payload.created_at, "server_created_at": now_iso(), "source": "public_demo"}
    try:
        saved_entry = save_feedback_entry(entry)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Feedback storage failed: {error}") from error
    return {"ok": True, "message": "Feedback saved", "feedback": saved_entry}

@router.get("/feedback")
async def list_feedback(limit: int = 20):
    safe_limit = max(1, min(int(limit or 20), 100))
    entries = read_feedback_entries(safe_limit)
    return {"ok": True, "count": len(entries), "limit": safe_limit, "feedback": entries}

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(tags=["feedback"])

FEEDBACK_FILE = Path(__file__).resolve().parents[2] / "data" / "feedback" / "feedback.jsonl"

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

def read_feedback_entries(limit: int = 20) -> list[dict[str, Any]]:
    if not FEEDBACK_FILE.exists():
        return []

    entries: list[dict[str, Any]] = []
    for line in FEEDBACK_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            import json
            item = json.loads(line)
            if isinstance(item, dict):
                entries.append(item)
        except Exception:
            continue

    return list(reversed(entries))[: max(1, min(limit, 100))]

@router.get("/feedback/health")
async def feedback_health():
    return {
        "service": "feedback",
        "status": "ok",
        "storage": "jsonl",
        "path": str(FEEDBACK_FILE),
    }

@router.post("/feedback")
async def create_feedback(payload: FeedbackPayload):
    message = payload.message.strip()

    if not message:
        raise HTTPException(status_code=400, detail="Feedback message is required")

    entry = {
        "type": safe_feedback_type(payload.type),
        "message": message,
        "page": payload.page.strip(),
        "client_created_at": payload.created_at,
        "server_created_at": now_iso(),
        "source": "public_demo",
    }

    try:
        import json
        FEEDBACK_FILE.parent.mkdir(parents=True, exist_ok=True)
        with FEEDBACK_FILE.open("a", encoding="utf-8") as file:
            file.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Feedback storage failed: {error}") from error

    return {
        "ok": True,
        "message": "Feedback saved",
        "feedback": entry,
    }

@router.get("/feedback")
async def list_feedback(limit: int = 20):
    safe_limit = max(1, min(int(limit or 20), 100))
    entries = read_feedback_entries(safe_limit)

    return {
        "ok": True,
        "count": len(entries),
        "limit": safe_limit,
        "feedback": entries,
    }

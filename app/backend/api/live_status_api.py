from datetime import datetime, timezone
import os

from fastapi import APIRouter, Query

router = APIRouter()

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()

@router.get("/live-status/health")
async def live_status_health():
    provider_url = os.environ.get("RAILYATRA_LIVE_STATUS_PROVIDER_URL", "").strip()
    return {
        "ok": True,
        "service": "live_train_status",
        "provider_configured": bool(provider_url),
        "real_live_status_enabled": bool(provider_url),
        "mode": "provider_live" if provider_url else "provider_not_configured",
        "checked_at": utc_now(),
    }

@router.get("/live-status")
async def get_live_status(train_no: str = Query(..., min_length=3, max_length=10)):
    return {
        "ok": False,
        "connected": False,
        "live": False,
        "train_no": train_no.strip().upper(),
        "status": "official_live_status_provider_not_configured",
        "message": "Real live train status needs an official or licensed provider API. No fake live status is returned.",
        "checked_at": utc_now(),
    }

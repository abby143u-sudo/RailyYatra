from __future__ import annotations

import re
from datetime import date

from fastapi import (
    APIRouter,
    HTTPException,
    Request,
)
from pydantic import BaseModel, Field

from backend.api.account_journey_store import (
    delete_saved_journey,
    list_saved_journeys,
    upsert_saved_journey,
)
from backend.api.auth_api import (
    require_authenticated_session,
)
from backend.api.cors_public_middleware import (
    configured_allowed_origins,
)


router = APIRouter(
    prefix="/account",
    tags=["account"],
)

STATION_CODE_PATTERN = re.compile(
    r"^[A-Z0-9]{2,12}$"
)
TRAVEL_CODE_PATTERN = re.compile(
    r"^[A-Z0-9]{1,8}$"
)


class SavedJourneyPayload(BaseModel):
    source: str
    destination: str
    journey_date: str | None = ""
    class_code: str = "SL"
    quota: str = "GN"
    label: str = Field(
        default="Saved journey",
        max_length=120,
    )
    note: str = Field(
        default="",
        max_length=500,
    )


class SavedJourneyImportPayload(BaseModel):
    journeys: list[SavedJourneyPayload]


def require_safe_write_origin(
    request: Request,
) -> None:
    origin = str(
        request.headers.get("origin") or ""
    ).strip().rstrip("/")

    # CLI, native applications and server-to-server clients
    # may legitimately omit the Origin header.
    if not origin:
        return

    allowed = {
        item.rstrip("/")
        for item in configured_allowed_origins()
    }

    hostname = request.url.hostname

    if hostname:
        allowed.add(f"https://{hostname}")
        allowed.add(f"http://{hostname}")

    if origin not in allowed:
        raise HTTPException(
            status_code=403,
            detail="Request origin is not allowed.",
        )


def authenticated_user(
    request: Request,
) -> dict:
    authenticated = (
        require_authenticated_session(request)
    )

    return authenticated["user"]


def normalize_station_code(
    value: str,
    field_name: str,
) -> str:
    code = str(value or "").strip().upper()

    if not STATION_CODE_PATTERN.fullmatch(code):
        raise ValueError(
            f"{field_name} must be a valid station code."
        )

    return code


def normalize_travel_code(
    value: str,
    field_name: str,
    default: str,
) -> str:
    code = str(value or default).strip().upper()

    if not TRAVEL_CODE_PATTERN.fullmatch(code):
        raise ValueError(
            f"{field_name} contains invalid characters."
        )

    return code


def normalize_journey(
    payload: SavedJourneyPayload,
) -> dict:
    source = normalize_station_code(
        payload.source,
        "Source",
    )
    destination = normalize_station_code(
        payload.destination,
        "Destination",
    )

    if source == destination:
        raise ValueError(
            "Source and destination must be different."
        )

    journey_date = str(
        payload.journey_date or ""
    ).strip()

    if journey_date:
        try:
            date.fromisoformat(journey_date)
        except ValueError as error:
            raise ValueError(
                "Journey date must use YYYY-MM-DD format."
            ) from error

    label = str(
        payload.label or "Saved journey"
    ).strip()[:120]

    note = str(
        payload.note or ""
    ).strip()[:500]

    return {
        "source": source,
        "destination": destination,
        "journey_date": journey_date,
        "class_code": normalize_travel_code(
            payload.class_code,
            "Class code",
            "SL",
        ),
        "quota": normalize_travel_code(
            payload.quota,
            "Quota",
            "GN",
        ),
        "label": label or "Saved journey",
        "note": note,
    }


@router.get("/saved-journeys")
def get_saved_journeys(
    request: Request,
):
    user = authenticated_user(request)

    try:
        journeys = list_saved_journeys(
            user_id=int(user["id"])
        )
    except Exception as error:
        raise HTTPException(
            status_code=503,
            detail=(
                "Saved journeys are temporarily unavailable."
            ),
        ) from error

    return {
        "ok": True,
        "count": len(journeys),
        "journeys": journeys,
    }


@router.post(
    "/saved-journeys",
    status_code=201,
)
def save_journey(
    payload: SavedJourneyPayload,
    request: Request,
):
    require_safe_write_origin(request)
    user = authenticated_user(request)

    try:
        normalized = normalize_journey(payload)
    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    try:
        journey = upsert_saved_journey(
            user_id=int(user["id"]),
            journey=normalized,
        )
    except Exception as error:
        raise HTTPException(
            status_code=503,
            detail=(
                "Journey could not be saved right now."
            ),
        ) from error

    return {
        "ok": True,
        "message": "Journey saved.",
        "journey": journey,
    }


@router.delete(
    "/saved-journeys/{journey_id}"
)
def remove_saved_journey(
    journey_id: int,
    request: Request,
):
    require_safe_write_origin(request)
    user = authenticated_user(request)

    try:
        deleted = delete_saved_journey(
            user_id=int(user["id"]),
            journey_id=journey_id,
        )
    except Exception as error:
        raise HTTPException(
            status_code=503,
            detail=(
                "Journey could not be removed right now."
            ),
        ) from error

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Saved journey not found.",
        )

    return {
        "ok": True,
        "message": "Saved journey removed.",
        "journey_id": journey_id,
    }


@router.post("/saved-journeys/import")
def import_saved_journeys(
    payload: SavedJourneyImportPayload,
    request: Request,
):
    require_safe_write_origin(request)
    user = authenticated_user(request)

    if len(payload.journeys) > 50:
        raise HTTPException(
            status_code=422,
            detail=(
                "A maximum of 50 journeys can be "
                "imported at once."
            ),
        )

    normalized_journeys = []

    try:
        for journey_payload in payload.journeys:
            normalized_journeys.append(
                normalize_journey(journey_payload)
            )
    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    try:
        for journey in normalized_journeys:
            upsert_saved_journey(
                user_id=int(user["id"]),
                journey=journey,
            )

        saved = list_saved_journeys(
            user_id=int(user["id"])
        )
    except Exception as error:
        raise HTTPException(
            status_code=503,
            detail=(
                "Journeys could not be imported right now."
            ),
        ) from error

    return {
        "ok": True,
        "message": "Saved journeys imported.",
        "processed_count": len(
            normalized_journeys
        ),
        "account_count": len(saved),
        "journeys": saved,
    }

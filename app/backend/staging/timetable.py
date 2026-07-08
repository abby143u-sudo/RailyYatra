from __future__ import annotations

from datetime import date, datetime, time, timedelta
from typing import Any


def parse_clock(value: Any) -> time | None:
    if value in (None, ""):
        return None

    parts = str(value).strip().split(":")

    if len(parts) < 2:
        return None

    try:
        hour = int(parts[0])
        minute = int(parts[1])
        second = int(parts[2]) if len(parts) >= 3 else 0
    except (TypeError, ValueError):
        return None

    if not 0 <= hour <= 23:
        return None

    if not 0 <= minute <= 59:
        return None

    if not 0 <= second <= 59:
        return None

    return time(
        hour=hour,
        minute=minute,
        second=second,
    )


def duration_label(total_minutes: int | None) -> str:
    if total_minutes is None:
        return "Unavailable"

    total_minutes = max(0, int(total_minutes))
    hours, minutes = divmod(total_minutes, 60)

    if hours:
        return f"{hours}h {minutes}m"

    return f"{minutes}m"


def day_span(
    from_day_offset: Any,
    to_day_offset: Any,
) -> int:
    try:
        start = int(from_day_offset or 0)
        end = int(to_day_offset or 0)
    except (TypeError, ValueError):
        return 0

    return max(0, end - start)


def build_arrival_datetime(
    departure_datetime: datetime,
    arrival_clock: Any,
    relative_days: int,
) -> datetime | None:
    parsed_arrival = parse_clock(arrival_clock)

    if parsed_arrival is None:
        return None

    arrival_date = (
        departure_datetime.date()
        + timedelta(days=max(0, relative_days))
    )

    arrival_datetime = datetime.combine(
        arrival_date,
        parsed_arrival,
    )

    if arrival_datetime < departure_datetime:
        arrival_datetime += timedelta(days=1)

    return arrival_datetime


def connection_risk(
    wait_minutes: int | None,
) -> tuple[str, str]:
    if wait_minutes is None:
        return (
            "unknown",
            "Transfer timing is unavailable.",
        )

    if wait_minutes < 30:
        return (
            "risky",
            "Estimated transfer wait is below 30 minutes.",
        )

    if wait_minutes < 60:
        return (
            "tight",
            "Estimated transfer wait is below one hour.",
        )

    if wait_minutes <= 240:
        return (
            "comfortable",
            "Estimated transfer wait is between one and four hours.",
        )

    return (
        "long_wait",
        "Estimated transfer wait is longer than four hours.",
    )


def enrich_route_timing(
    route: dict[str, Any],
    journey_date: str | None,
) -> dict[str, Any]:
    enriched = dict(route)
    legs = [
        dict(leg)
        for leg in (route.get("legs") or [])
    ]
    enriched["legs"] = legs

    if not journey_date:
        enriched["journey_timing"] = {
            "status": "not_requested",
            "journey_date": None,
            "operating_day_validation": {
                "status": "unknown",
                "reason": (
                    "Journey date was not supplied."
                ),
            },
        }
        return enriched

    try:
        boarding_date = date.fromisoformat(journey_date)
    except ValueError:
        enriched["journey_timing"] = {
            "status": "invalid_date",
            "journey_date": journey_date,
            "message": (
                "Journey date must use YYYY-MM-DD format."
            ),
        }
        return enriched

    if not legs:
        enriched["journey_timing"] = {
            "status": "unavailable",
            "journey_date": boarding_date.isoformat(),
            "message": "No train legs are available.",
        }
        return enriched

    first_leg = legs[0]
    first_departure_clock = parse_clock(
        first_leg.get("departure")
    )

    if first_departure_clock is None:
        enriched["journey_timing"] = {
            "status": "unavailable",
            "journey_date": boarding_date.isoformat(),
            "message": (
                "Source departure time is unavailable."
            ),
            "operating_day_validation": {
                "status": "unknown",
                "reason": (
                    "The railway source does not provide "
                    "running-day metadata for most trains."
                ),
            },
        }
        return enriched

    first_departure = datetime.combine(
        boarding_date,
        first_departure_clock,
    )

    first_arrival = build_arrival_datetime(
        departure_datetime=first_departure,
        arrival_clock=first_leg.get("arrival"),
        relative_days=day_span(
            first_leg.get("from_day_offset"),
            first_leg.get("to_day_offset"),
        ),
    )

    first_leg["departure_datetime"] = (
        first_departure.isoformat()
    )
    first_leg["arrival_datetime"] = (
        first_arrival.isoformat()
        if first_arrival
        else None
    )

    first_duration = None

    if first_arrival:
        first_duration = int(
            (
                first_arrival - first_departure
            ).total_seconds()
            // 60
        )

    first_leg["duration_minutes"] = first_duration
    first_leg["duration_label"] = duration_label(
        first_duration
    )

    final_arrival = first_arrival
    transfer_wait = None

    if len(legs) >= 2 and first_arrival:
        second_leg = legs[1]
        second_departure_clock = parse_clock(
            second_leg.get("departure")
        )

        second_departure = None

        if second_departure_clock:
            second_departure = datetime.combine(
                first_arrival.date(),
                second_departure_clock,
            )

            if second_departure <= first_arrival:
                second_departure += timedelta(days=1)

        second_arrival = None

        if second_departure:
            second_arrival = build_arrival_datetime(
                departure_datetime=second_departure,
                arrival_clock=second_leg.get("arrival"),
                relative_days=day_span(
                    second_leg.get("from_day_offset"),
                    second_leg.get("to_day_offset"),
                ),
            )

            transfer_wait = int(
                (
                    second_departure - first_arrival
                ).total_seconds()
                // 60
            )

        second_leg["departure_datetime"] = (
            second_departure.isoformat()
            if second_departure
            else None
        )
        second_leg["arrival_datetime"] = (
            second_arrival.isoformat()
            if second_arrival
            else None
        )

        second_duration = None

        if second_departure and second_arrival:
            second_duration = int(
                (
                    second_arrival - second_departure
                ).total_seconds()
                // 60
            )

        second_leg["duration_minutes"] = second_duration
        second_leg["duration_label"] = duration_label(
            second_duration
        )

        risk_level, risk_reason = connection_risk(
            transfer_wait
        )

        existing_connection = dict(
            enriched.get("transfer_connection") or {}
        )

        existing_connection.update(
            {
                "status": "estimated",
                "estimated": True,
                "arrival": (
                    first_arrival.isoformat()
                    if first_arrival
                    else None
                ),
                "departure": (
                    second_departure.isoformat()
                    if second_departure
                    else None
                ),
                "wait_minutes": transfer_wait,
                "wait_label": duration_label(
                    transfer_wait
                ),
                "risk_level": risk_level,
                "rolls_to_next_day": (
                    bool(
                        second_departure
                        and second_departure.date()
                        > first_arrival.date()
                    )
                ),
                "reason": risk_reason,
            }
        )

        enriched["transfer_connection"] = (
            existing_connection
        )

        final_arrival = second_arrival

    total_duration = None

    if final_arrival:
        total_duration = int(
            (
                final_arrival - first_departure
            ).total_seconds()
            // 60
        )

    enriched["journey_timing"] = {
        "status": "estimated",
        "journey_date": boarding_date.isoformat(),
        "departure_datetime": (
            first_departure.isoformat()
        ),
        "arrival_datetime": (
            final_arrival.isoformat()
            if final_arrival
            else None
        ),
        "total_duration_minutes": total_duration,
        "total_duration_label": duration_label(
            total_duration
        ),
        "operating_day_validation": {
            "status": "unknown",
            "reason": (
                "The current railway source does not provide "
                "running-day metadata for most trains. "
                "The date is used for timetable and duration "
                "estimation only."
            ),
        },
    }

    return enriched

from __future__ import annotations

from typing import Any

from backend.staging.route_engine import search_staging_routes


def safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def get_confidence_label(score: int) -> str:
    if score >= 900:
        return "very_high"

    if score >= 760:
        return "high"

    if score >= 600:
        return "medium"

    return "low"


def get_transfer_safety(
    route: dict[str, Any],
) -> dict[str, Any]:
    route_type = route.get("route_type")

    if route_type == "direct":
        return {
            "level": "safe",
            "label": "No transfer risk",
            "reason": "Direct route with one train leg.",
        }

    connection = route.get("transfer_connection") or {}
    risk_level = connection.get("risk_level")
    wait_label = connection.get("wait_label")

    if risk_level == "risky":
        return {
            "level": "risky",
            "label": "Risky connection",
            "reason": (
                f"Estimated transfer wait is {wait_label}. "
                "This connection may be too short."
            ),
        }

    if risk_level == "tight":
        return {
            "level": "caution",
            "label": "Tight connection",
            "reason": (
                f"Estimated transfer wait is {wait_label}. "
                "Extra caution is recommended."
            ),
        }

    if risk_level == "comfortable":
        return {
            "level": "safe",
            "label": "Comfortable connection",
            "reason": (
                f"Estimated transfer wait is {wait_label}."
            ),
        }

    if risk_level == "long_wait":
        return {
            "level": "moderate",
            "label": "Long transfer wait",
            "reason": (
                f"Estimated transfer wait is {wait_label}."
            ),
        }

    return {
        "level": "caution",
        "label": "Transfer time unknown",
        "reason": (
            "Arrival or departure timing is unavailable, "
            "so transfer wait cannot be estimated."
        ),
    }



def build_reasons(route: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    route_type = route.get("route_type")
    stop_count = safe_int(route.get("total_stop_count"))
    distance = safe_int(route.get("total_distance"))
    score = safe_int(route.get("score"))

    if route_type == "direct":
        reasons.append("Direct train route found from staging railway data.")
    elif route_type == "one_transfer":
        reasons.append(
            f"One-transfer route via "
            f"{route.get('transfer_station')} found from "
            f"staging railway data."
        )

        connection = route.get("transfer_connection") or {}
        wait_label = connection.get("wait_label")

        if wait_label:
            reasons.append(
                f"Estimated transfer wait at "
                f"{route.get('transfer_station')}: "
                f"{wait_label}."
            )
    else:
        reasons.append("Route found from staging railway data.")

    if score >= 850:
        reasons.append("Strong route score based on fewer stops and simpler journey structure.")

    if stop_count > 0:
        reasons.append(f"Total stop count estimated from staging stop sequence: {stop_count}.")

    if distance > 0:
        reasons.append(f"Approximate route distance from staging data: {distance} km.")

    if route.get("warnings"):
        reasons.append("Some timetable fields are missing, so timing confidence is limited.")

    ranking = route.get("ranking") or {}

    for ranking_reason in (
        ranking.get("reasons") or []
    ):
        if ranking_reason not in reasons:
            reasons.append(ranking_reason)

    return reasons


def enrich_route(route: dict[str, Any], rank: int) -> dict[str, Any]:
    score = safe_int(route.get("score"))
    enriched = dict(route)

    enriched["recommendation_rank"] = rank
    enriched["confidence"] = {
        "score": score,
        "level": get_confidence_label(score),
    }
    enriched["transfer_safety"] = get_transfer_safety(route)
    enriched["reasons"] = build_reasons(route)
    enriched["booking_status"] = {
        "live_availability_connected": False,
        "live_fare_connected": False,
        "note": "Static staging route engine only. Live fare, seat availability, PNR and booking are not connected yet.",
    }

    return enriched


def optional_int(value: Any) -> int | None:
    try:
        if value is None or value == "":
            return None
        return int(float(value))
    except (TypeError, ValueError):
        return None


def rank_and_validate_routes(
    routes: list[dict[str, Any]],
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    ranked_routes: list[dict[str, Any]] = []
    rejected_routes: list[dict[str, Any]] = []

    for route in routes:
        candidate = dict(route)
        route_type = candidate.get("route_type")

        timing = candidate.get("journey_timing") or {}
        connection = (
            candidate.get("transfer_connection") or {}
        )

        duration_minutes = optional_int(
            timing.get("total_duration_minutes")
        )
        wait_minutes = optional_int(
            connection.get("wait_minutes")
        )
        risk_level = connection.get("risk_level")

        if (
            route_type == "one_transfer"
            and wait_minutes is not None
            and wait_minutes < 30
        ):
            rejected = dict(candidate)
            rejected["rejection"] = {
                "code": "transfer_below_minimum",
                "reason": (
                    "Connection has less than "
                    "30 minutes transfer time."
                ),
                "wait_minutes": wait_minutes,
            }
            rejected_routes.append(rejected)
            continue

        base_score = safe_int(
            candidate.get("score"),
            100,
        )

        if duration_minutes is None:
            duration_penalty = 90
        else:
            duration_penalty = min(
                max(duration_minutes - 600, 0)
                // 30
                * 4,
                160,
            )

        direct_bonus = 0
        transfer_adjustment = 0
        ranking_reasons: list[str] = []

        if route_type == "direct":
            direct_bonus = 35
            ranking_reasons.append(
                "Direct journey received a simplicity bonus."
            )

        elif risk_level == "comfortable":
            transfer_adjustment = 40
            ranking_reasons.append(
                "Comfortable transfer received a safety bonus."
            )

        elif risk_level == "tight":
            transfer_adjustment = -60
            ranking_reasons.append(
                "Tight transfer reduced the final route score."
            )

        elif risk_level == "long_wait":
            transfer_adjustment = -100
            ranking_reasons.append(
                "Long transfer wait reduced the final score."
            )

        elif risk_level == "unknown":
            transfer_adjustment = -140
            ranking_reasons.append(
                "Missing transfer timing reduced ranking confidence."
            )

        elif risk_level == "risky":
            transfer_adjustment = -220
            ranking_reasons.append(
                "Risky transfer received a major score penalty."
            )

        if duration_minutes is None:
            ranking_reasons.append(
                "Total duration is unavailable, so the "
                "route received a timing-confidence penalty."
            )
        else:
            ranking_reasons.append(
                "Date-aware total journey duration was "
                "used in final ranking."
            )

        final_score = (
            base_score
            + direct_bonus
            + transfer_adjustment
            - duration_penalty
        )

        final_score = max(
            50,
            min(1000, final_score),
        )

        candidate["base_score"] = base_score
        candidate["score"] = final_score
        candidate["ranking"] = {
            "base_score": base_score,
            "final_score": final_score,
            "direct_bonus": direct_bonus,
            "transfer_adjustment": (
                transfer_adjustment
            ),
            "duration_penalty": duration_penalty,
            "duration_minutes": duration_minutes,
            "minimum_transfer_minutes": 30,
            "reasons": ranking_reasons,
        }

        ranked_routes.append(candidate)

    risk_priority = {
        "comfortable": 0,
        "tight": 1,
        "long_wait": 2,
        "unknown": 3,
        "risky": 4,
    }

    def route_sort_key(
        route: dict[str, Any],
    ) -> tuple[Any, ...]:
        timing = route.get("journey_timing") or {}
        connection = (
            route.get("transfer_connection") or {}
        )

        duration = optional_int(
            timing.get("total_duration_minutes")
        )

        trains = tuple(
            str(leg.get("train_number") or "")
            for leg in route.get("legs", [])
        )

        return (
            -safe_int(route.get("score")),
            route.get("route_type") != "direct",
            risk_priority.get(
                connection.get("risk_level"),
                5,
            ),
            duration is None,
            duration if duration is not None else 999999,
            safe_int(
                route.get("total_stop_count"),
                9999,
            ),
            trains,
        )

    ranked_routes.sort(key=route_sort_key)

    return ranked_routes, rejected_routes



def canonical_train_number(value: Any) -> str:
    number = str(value or "").strip().upper()

    for suffix in ("-SLIP", " SLIP", "/SLIP"):
        if number.endswith(suffix):
            number = number[:-len(suffix)].strip()

    return number


def route_duplicate_key(
    route: dict[str, Any],
) -> tuple[Any, ...]:
    legs = tuple(
        (
            canonical_train_number(
                leg.get("train_number")
            ),
            str(
                leg.get("from_station_code") or ""
            ).upper(),
            str(
                leg.get("to_station_code") or ""
            ).upper(),
            str(leg.get("departure") or ""),
            str(leg.get("arrival") or ""),
        )
        for leg in route.get("legs") or []
    )

    return (
        route.get("route_type"),
        str(route.get("source") or "").upper(),
        str(
            route.get("transfer_station") or ""
        ).upper(),
        str(
            route.get("destination") or ""
        ).upper(),
        legs,
    )


def deduplicate_ranked_routes(
    routes: list[dict[str, Any]],
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    unique_routes = []
    duplicate_routes = []
    seen = set()

    for route in routes:
        key = route_duplicate_key(route)

        if key in seen:
            duplicate_routes.append(route)
            continue

        seen.add(key)
        unique_routes.append(route)

    return unique_routes, duplicate_routes


def recommend_staging_routes(
    source_station_code: str,
    destination_station_code: str,
    direct_limit: int = 8,
    transfer_limit: int = 2,
    journey_date: str | None = None,
) -> dict[str, Any]:
    result = search_staging_routes(
        source_station_code=source_station_code,
        destination_station_code=destination_station_code,
        direct_limit=direct_limit,
        transfer_limit=transfer_limit,
        journey_date=journey_date,
    )

    routes = result.get("routes", [])

    ranked_routes, rejected_routes = (
        rank_and_validate_routes(routes)
    )

    deduplicated_routes, duplicate_routes = (
        deduplicate_ranked_routes(
            ranked_routes
        )
    )

    enriched_routes = [
        enrich_route(
            route=route,
            rank=index + 1,
        )
        for index, route in enumerate(
            deduplicated_routes
        )
    ]

    direct_count = sum(1 for route in enriched_routes if route.get("route_type") == "direct")
    transfer_count = sum(1 for route in enriched_routes if route.get("route_type") == "one_transfer")

    return {
        "status": "ok",
        "endpoint": "/recommend-v2",
        "engine": "phase_4_recommendation_engine",
        "source": result.get("source"),
        "destination": result.get("destination"),
        "journey_date": result.get("journey_date"),
        "count": len(enriched_routes),
        "direct_count": direct_count,
        "one_transfer_count": transfer_count,
        "rejected_transfer_count": len(
            rejected_routes
        ),
        "duplicate_route_count": len(
            duplicate_routes
        ),
        "deduplication_policy": {
            "enabled": True,
            "slip_suffix_normalized": True,
            "highest_ranked_route_kept": True,
        },
        "ranking_policy": {
            "minimum_transfer_minutes": 30,
            "risky_connections_rejected": True,
            "unknown_timing_penalized": True,
            "long_wait_penalized": True,
            "duration_used_for_ranking": True,
        },
        "recommendations": enriched_routes,
        "summary": {
            "best_available": enriched_routes[0] if enriched_routes else None,
            "live_booking_ready": False,
            "legacy_search_unchanged": True,
        },
        "database_write_skipped": True,
        "production_railway_tables_modified": False,
    }

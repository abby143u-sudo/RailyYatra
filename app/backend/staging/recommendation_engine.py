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


def get_transfer_safety(route: dict[str, Any]) -> dict[str, Any]:
    route_type = route.get("route_type")

    if route_type == "direct":
        return {
            "level": "safe",
            "label": "No transfer risk",
            "reason": "Direct route with one train leg.",
        }

    warnings = route.get("warnings") or []

    if "transfer_time_unknown" in warnings:
        return {
            "level": "caution",
            "label": "Transfer time unknown",
            "reason": "Arrival or departure data is missing for at least one transfer leg.",
        }

    return {
        "level": "moderate",
        "label": "Transfer required",
        "reason": "Route requires changing trains once.",
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
        reasons.append(f"One-transfer route via {route.get('transfer_station')} found from staging railway data.")
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


def recommend_staging_routes(
    source_station_code: str,
    destination_station_code: str,
    direct_limit: int = 8,
    transfer_limit: int = 2,
) -> dict[str, Any]:
    result = search_staging_routes(
        source_station_code=source_station_code,
        destination_station_code=destination_station_code,
        direct_limit=direct_limit,
        transfer_limit=transfer_limit,
    )

    routes = result.get("routes", [])
    enriched_routes = [
        enrich_route(route=route, rank=index + 1)
        for index, route in enumerate(routes)
    ]

    direct_count = sum(1 for route in enriched_routes if route.get("route_type") == "direct")
    transfer_count = sum(1 for route in enriched_routes if route.get("route_type") == "one_transfer")

    return {
        "status": "ok",
        "endpoint": "/recommend-v2",
        "engine": "phase_4_recommendation_engine",
        "source": result.get("source"),
        "destination": result.get("destination"),
        "count": len(enriched_routes),
        "direct_count": direct_count,
        "one_transfer_count": transfer_count,
        "recommendations": enriched_routes,
        "summary": {
            "best_available": enriched_routes[0] if enriched_routes else None,
            "live_booking_ready": False,
            "legacy_search_unchanged": True,
        },
        "database_write_skipped": True,
        "production_railway_tables_modified": False,
    }

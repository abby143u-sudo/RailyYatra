from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from backend.staging.timetable import enrich_route_timing


APP_DIR = Path(__file__).resolve().parents[2]
DB_PATH = APP_DIR / "railyatra.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def rows_to_dicts(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    return [dict(row) for row in rows]


def safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def find_direct_routes(
    source_station_code: str,
    destination_station_code: str,
    limit: int = 10,
    journey_date: str | None = None,
) -> list[dict[str, Any]]:
    source = source_station_code.upper().strip()
    destination = destination_station_code.upper().strip()
    safe_limit = max(1, min(limit, 50))

    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT
                s1.train_number AS train_number,
                t.train_name AS train_name,
                t.train_type AS train_type,
                s1.station_code AS source_station_code,
                s2.station_code AS destination_station_code,
                s1.stop_sequence AS source_sequence,
                s2.stop_sequence AS destination_sequence,
                s1.departure AS departure,
                s2.arrival AS arrival,
                s1.day_offset AS source_day_offset,
                s2.day_offset AS destination_day_offset,
                COALESCE(s2.distance, 0) - COALESCE(s1.distance, 0) AS distance,
                s2.stop_sequence - s1.stop_sequence AS stop_count
            FROM staging_train_stops s1
            JOIN staging_train_stops s2
                ON s1.train_number = s2.train_number
               AND s2.stop_sequence > s1.stop_sequence
            LEFT JOIN staging_trains t
                ON t.train_number = s1.train_number
            WHERE s1.station_code = ?
              AND s2.station_code = ?
            ORDER BY stop_count ASC, distance ASC, s1.train_number
            LIMIT ?
            """,
            (source, destination, safe_limit),
        ).fetchall()

    routes: list[dict[str, Any]] = []

    for row in rows_to_dicts(rows):
        routes.append(
            {
                "route_type": "direct",
                "score": score_direct_route(row),
                "source": source,
                "destination": destination,
                "transfer_station": None,
                "legs": [
                    {
                        "train_number": row["train_number"],
                        "train_name": row["train_name"],
                        "train_type": row["train_type"],
                        "from_station_code": row["source_station_code"],
                        "to_station_code": row["destination_station_code"],
                        "from_sequence": row["source_sequence"],
                        "to_sequence": row["destination_sequence"],
                        "departure": row["departure"],
                        "arrival": row["arrival"],
                        "from_day_offset": safe_int(
                            row["source_day_offset"]
                        ),
                        "to_day_offset": safe_int(
                            row["destination_day_offset"]
                        ),
                        "distance": safe_int(row["distance"]),
                        "stop_count": safe_int(row["stop_count"]),
                    }
                ],
                "total_stop_count": safe_int(row["stop_count"]),
                "total_distance": safe_int(row["distance"]),
                "warnings": [],
            }
        )

    return [
        enrich_route_timing(route, journey_date)
        for route in routes
    ]


def load_first_leg_candidates(
    conn: sqlite3.Connection,
    source: str,
    destination: str,
    row_limit: int = 250,
) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT
            s1.train_number AS first_train_number,
            t.train_name AS first_train_name,
            t.train_type AS first_train_type,
            s1.station_code AS source_station_code,
            s2.station_code AS transfer_station_code,
            s1.stop_sequence AS source_sequence,
            s2.stop_sequence AS transfer_arrival_sequence,
            s1.departure AS first_departure,
            s2.arrival AS first_arrival,
            s1.day_offset AS first_departure_day_offset,
            s2.day_offset AS first_arrival_day_offset,
            COALESCE(s2.distance, 0) - COALESCE(s1.distance, 0) AS first_distance,
            s2.stop_sequence - s1.stop_sequence AS first_stop_count
        FROM staging_train_stops s1
        JOIN staging_train_stops s2
            ON s1.train_number = s2.train_number
           AND s2.stop_sequence > s1.stop_sequence
        LEFT JOIN staging_trains t
            ON t.train_number = s1.train_number
        WHERE s1.station_code = ?
          AND s2.station_code NOT IN (?, ?)
        ORDER BY first_stop_count ASC, first_distance ASC, s1.train_number
        LIMIT ?
        """,
        (source, source, destination, row_limit),
    ).fetchall()

    return rows_to_dicts(rows)


def load_second_leg_candidates(
    conn: sqlite3.Connection,
    transfer_stations: list[str],
    destination: str,
    row_limit: int = 600,
) -> list[dict[str, Any]]:
    if not transfer_stations:
        return []

    placeholders = ",".join("?" for _ in transfer_stations)

    rows = conn.execute(
        f"""
        SELECT
            s3.train_number AS second_train_number,
            t.train_name AS second_train_name,
            t.train_type AS second_train_type,
            s3.station_code AS transfer_station_code,
            s4.station_code AS destination_station_code,
            s3.stop_sequence AS transfer_departure_sequence,
            s4.stop_sequence AS destination_sequence,
            s3.departure AS second_departure,
            s4.arrival AS second_arrival,
            s3.day_offset AS second_departure_day_offset,
            s4.day_offset AS second_arrival_day_offset,
            COALESCE(s4.distance, 0) - COALESCE(s3.distance, 0) AS second_distance,
            s4.stop_sequence - s3.stop_sequence AS second_stop_count
        FROM staging_train_stops s3
        JOIN staging_train_stops s4
            ON s3.train_number = s4.train_number
           AND s4.stop_sequence > s3.stop_sequence
        LEFT JOIN staging_trains t
            ON t.train_number = s3.train_number
        WHERE s3.station_code IN ({placeholders})
          AND s4.station_code = ?
        ORDER BY second_stop_count ASC, second_distance ASC, s3.train_number
        LIMIT ?
        """,
        [*transfer_stations, destination, row_limit],
    ).fetchall()

    return rows_to_dicts(rows)


def parse_clock_minutes(value: Any) -> int | None:
    if value in (None, ""):
        return None

    parts = str(value).strip().split(":")

    if len(parts) < 2:
        return None

    try:
        hours = int(parts[0])
        minutes = int(parts[1])
    except (TypeError, ValueError):
        return None

    if not 0 <= hours <= 23 or not 0 <= minutes <= 59:
        return None

    return hours * 60 + minutes


def build_transfer_connection(
    first_arrival: Any,
    second_departure: Any,
) -> dict[str, Any]:
    arrival_minutes = parse_clock_minutes(first_arrival)
    departure_minutes = parse_clock_minutes(second_departure)

    if arrival_minutes is None or departure_minutes is None:
        return {
            "status": "unknown",
            "estimated": True,
            "arrival": first_arrival,
            "departure": second_departure,
            "wait_minutes": None,
            "wait_label": "Timing unavailable",
            "risk_level": "unknown",
            "rolls_to_next_day": False,
            "reason": (
                "Transfer wait cannot be estimated because an "
                "arrival or departure time is missing."
            ),
        }

    wait_minutes = departure_minutes - arrival_minutes
    rolls_to_next_day = wait_minutes < 0

    if rolls_to_next_day:
        wait_minutes += 24 * 60

    hours, minutes = divmod(wait_minutes, 60)

    if hours:
        wait_label = f"{hours}h {minutes}m"
    else:
        wait_label = f"{minutes}m"

    if wait_minutes < 30:
        risk_level = "risky"
        reason = "Estimated transfer wait is below 30 minutes."
    elif wait_minutes < 60:
        risk_level = "tight"
        reason = "Estimated transfer wait is below one hour."
    elif wait_minutes <= 240:
        risk_level = "comfortable"
        reason = "Estimated transfer wait is between one and four hours."
    else:
        risk_level = "long_wait"
        reason = "Estimated transfer wait is longer than four hours."

    return {
        "status": "estimated",
        "estimated": True,
        "arrival": first_arrival,
        "departure": second_departure,
        "wait_minutes": wait_minutes,
        "wait_label": wait_label,
        "risk_level": risk_level,
        "rolls_to_next_day": rolls_to_next_day,
        "reason": reason,
    }


def find_one_transfer_routes(
    source_station_code: str,
    destination_station_code: str,
    limit: int = 10,
    journey_date: str | None = None,
) -> list[dict[str, Any]]:
    source = source_station_code.upper().strip()
    destination = destination_station_code.upper().strip()
    safe_limit = max(0, min(limit, 20))

    if safe_limit == 0:
        return []

    with get_connection() as conn:
        first_legs = load_first_leg_candidates(
            conn=conn,
            source=source,
            destination=destination,
            row_limit=250,
        )

        transfer_stations: list[str] = []
        seen_transfers: set[str] = set()

        for first_leg in first_legs:
            transfer = str(first_leg["transfer_station_code"])
            if transfer not in seen_transfers:
                seen_transfers.add(transfer)
                transfer_stations.append(transfer)

            if len(transfer_stations) >= 60:
                break

        second_legs = load_second_leg_candidates(
            conn=conn,
            transfer_stations=transfer_stations,
            destination=destination,
            row_limit=600,
        )

    second_by_transfer: dict[str, list[dict[str, Any]]] = {}

    for second_leg in second_legs:
        second_by_transfer.setdefault(str(second_leg["transfer_station_code"]), []).append(second_leg)

    routes: list[dict[str, Any]] = []

    for first_leg in first_legs:
        transfer = str(first_leg["transfer_station_code"])

        for second_leg in second_by_transfer.get(transfer, [])[:10]:
            if str(first_leg["first_train_number"]) == str(second_leg["second_train_number"]):
                continue

            warnings: list[str] = []

            transfer_connection = build_transfer_connection(
                first_arrival=first_leg["first_arrival"],
                second_departure=second_leg["second_departure"],
            )

            transfer_risk = transfer_connection["risk_level"]

            if transfer_risk == "unknown":
                warnings.append("transfer_time_unknown")
            elif transfer_risk == "risky":
                warnings.append("transfer_too_tight")
            elif transfer_risk == "tight":
                warnings.append("transfer_tight")
            elif transfer_risk == "long_wait":
                warnings.append("transfer_long_wait")

            first_distance = safe_int(first_leg["first_distance"])
            second_distance = safe_int(second_leg["second_distance"])
            first_stop_count = safe_int(first_leg["first_stop_count"])
            second_stop_count = safe_int(second_leg["second_stop_count"])

            route = {
                "route_type": "one_transfer",
                "source": source,
                "destination": destination,
                "transfer_station": transfer,
                "legs": [
                    {
                        "train_number": first_leg["first_train_number"],
                        "train_name": first_leg["first_train_name"],
                        "train_type": first_leg["first_train_type"],
                        "from_station_code": first_leg["source_station_code"],
                        "to_station_code": first_leg["transfer_station_code"],
                        "from_sequence": first_leg["source_sequence"],
                        "to_sequence": first_leg["transfer_arrival_sequence"],
                        "departure": first_leg["first_departure"],
                        "arrival": first_leg["first_arrival"],
                        "from_day_offset": safe_int(
                            first_leg[
                                "first_departure_day_offset"
                            ]
                        ),
                        "to_day_offset": safe_int(
                            first_leg[
                                "first_arrival_day_offset"
                            ]
                        ),
                        "distance": first_distance,
                        "stop_count": first_stop_count,
                    },
                    {
                        "train_number": second_leg["second_train_number"],
                        "train_name": second_leg["second_train_name"],
                        "train_type": second_leg["second_train_type"],
                        "from_station_code": second_leg["transfer_station_code"],
                        "to_station_code": second_leg["destination_station_code"],
                        "from_sequence": second_leg["transfer_departure_sequence"],
                        "to_sequence": second_leg["destination_sequence"],
                        "departure": second_leg["second_departure"],
                        "arrival": second_leg["second_arrival"],
                        "from_day_offset": safe_int(
                            second_leg[
                                "second_departure_day_offset"
                            ]
                        ),
                        "to_day_offset": safe_int(
                            second_leg[
                                "second_arrival_day_offset"
                            ]
                        ),
                        "distance": second_distance,
                        "stop_count": second_stop_count,
                    },
                ],
                "total_stop_count": first_stop_count + second_stop_count,
                "total_distance": first_distance + second_distance,
                "transfer_connection": transfer_connection,
                "warnings": warnings,
            }

            route["score"] = score_transfer_route(route)
            routes.append(route)

            if len(routes) >= safe_limit * 5:
                break

        if len(routes) >= safe_limit * 5:
            break

    routes.sort(
        key=lambda route: (
            -safe_int(route.get("score")),
            safe_int(route.get("total_stop_count"), 9999),
            safe_int(route.get("total_distance"), 999999),
        )
    )

    return [
        enrich_route_timing(route, journey_date)
        for route in routes[:safe_limit]
    ]


def score_direct_route(row: dict[str, Any]) -> int:
    stop_count = safe_int(row.get("stop_count"))
    distance = safe_int(row.get("distance"))

    score = 1000
    score -= min(stop_count * 8, 250)

    if distance > 0:
        score -= min(distance // 25, 120)

    return max(score, 100)


def score_transfer_route(route: dict[str, Any]) -> int:
    stop_count = safe_int(route.get("total_stop_count"))
    distance = safe_int(route.get("total_distance"))

    score = 850
    score -= min(stop_count * 8, 260)

    if distance > 0:
        score -= min(distance // 25, 140)

    if route.get("warnings"):
        score -= 80

    return max(score, 80)


def search_staging_routes(
    source_station_code: str,
    destination_station_code: str,
    direct_limit: int = 10,
    transfer_limit: int = 10,
    journey_date: str | None = None,
) -> dict[str, Any]:
    source = source_station_code.upper().strip()
    destination = destination_station_code.upper().strip()

    direct_routes = find_direct_routes(
        source_station_code=source,
        destination_station_code=destination,
        limit=direct_limit,
        journey_date=journey_date,
    )

    transfer_routes = find_one_transfer_routes(
        source_station_code=source,
        destination_station_code=destination,
        limit=transfer_limit,
        journey_date=journey_date,
    )

    all_routes = direct_routes + transfer_routes
    all_routes.sort(
        key=lambda route: (
            -safe_int(route.get("score")),
            safe_int(route.get("total_stop_count"), 9999),
            route.get("route_type") != "direct",
        )
    )

    return {
        "mode": "staging_read_only",
        "engine": "phase_3_staging_route_engine",
        "source": source,
        "destination": destination,
        "journey_date": journey_date,
        "count": len(all_routes),
        "direct_count": len(direct_routes),
        "one_transfer_count": len(transfer_routes),
        "routes": all_routes,
        "database_write_skipped": True,
        "production_railway_tables_modified": False,
    }

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


APP_DIR = Path(__file__).resolve().parents[2]
DB_PATH = APP_DIR / "railyatra.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def rows_to_dicts(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    return [dict(row) for row in rows]


def find_direct_routes(
    source_station_code: str,
    destination_station_code: str,
    limit: int = 10,
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
                        "distance": row["distance"],
                        "stop_count": row["stop_count"],
                    }
                ],
                "total_stop_count": row["stop_count"],
                "total_distance": row["distance"],
                "warnings": [],
            }
        )

    return routes


def find_one_transfer_routes(
    source_station_code: str,
    destination_station_code: str,
    limit: int = 10,
) -> list[dict[str, Any]]:
    source = source_station_code.upper().strip()
    destination = destination_station_code.upper().strip()
    safe_limit = max(1, min(limit, 30))

    with get_connection() as conn:
        rows = conn.execute(
            """
            WITH first_leg AS (
                SELECT
                    s1.train_number AS first_train_number,
                    t1.train_name AS first_train_name,
                    t1.train_type AS first_train_type,
                    s1.station_code AS source_station_code,
                    s2.station_code AS transfer_station_code,
                    s1.stop_sequence AS source_sequence,
                    s2.stop_sequence AS transfer_arrival_sequence,
                    s1.departure AS first_departure,
                    s2.arrival AS first_arrival,
                    COALESCE(s2.distance, 0) - COALESCE(s1.distance, 0) AS first_distance,
                    s2.stop_sequence - s1.stop_sequence AS first_stop_count
                FROM staging_train_stops s1
                JOIN staging_train_stops s2
                    ON s1.train_number = s2.train_number
                   AND s2.stop_sequence > s1.stop_sequence
                LEFT JOIN staging_trains t1
                    ON t1.train_number = s1.train_number
                WHERE s1.station_code = ?
            ),
            second_leg AS (
                SELECT
                    s3.train_number AS second_train_number,
                    t2.train_name AS second_train_name,
                    t2.train_type AS second_train_type,
                    s3.station_code AS transfer_station_code,
                    s4.station_code AS destination_station_code,
                    s3.stop_sequence AS transfer_departure_sequence,
                    s4.stop_sequence AS destination_sequence,
                    s3.departure AS second_departure,
                    s4.arrival AS second_arrival,
                    COALESCE(s4.distance, 0) - COALESCE(s3.distance, 0) AS second_distance,
                    s4.stop_sequence - s3.stop_sequence AS second_stop_count
                FROM staging_train_stops s3
                JOIN staging_train_stops s4
                    ON s3.train_number = s4.train_number
                   AND s4.stop_sequence > s3.stop_sequence
                LEFT JOIN staging_trains t2
                    ON t2.train_number = s3.train_number
                WHERE s4.station_code = ?
            )
            SELECT
                first_leg.*,
                second_leg.second_train_number,
                second_leg.second_train_name,
                second_leg.second_train_type,
                second_leg.destination_station_code,
                second_leg.transfer_departure_sequence,
                second_leg.destination_sequence,
                second_leg.second_departure,
                second_leg.second_arrival,
                second_leg.second_distance,
                second_leg.second_stop_count,
                first_leg.first_stop_count + second_leg.second_stop_count AS total_stop_count,
                first_leg.first_distance + second_leg.second_distance AS total_distance
            FROM first_leg
            JOIN second_leg
                ON first_leg.transfer_station_code = second_leg.transfer_station_code
            WHERE first_leg.first_train_number != second_leg.second_train_number
              AND first_leg.transfer_station_code NOT IN (?, ?)
            ORDER BY total_stop_count ASC, total_distance ASC, first_leg.transfer_station_code
            LIMIT ?
            """,
            (source, destination, source, destination, safe_limit),
        ).fetchall()

    routes: list[dict[str, Any]] = []

    for row in rows_to_dicts(rows):
        warnings: list[str] = []

        if row["first_arrival"] in (None, "") or row["second_departure"] in (None, ""):
            warnings.append("transfer_time_unknown")

        route = {
            "route_type": "one_transfer",
            "source": source,
            "destination": destination,
            "transfer_station": row["transfer_station_code"],
            "legs": [
                {
                    "train_number": row["first_train_number"],
                    "train_name": row["first_train_name"],
                    "train_type": row["first_train_type"],
                    "from_station_code": row["source_station_code"],
                    "to_station_code": row["transfer_station_code"],
                    "from_sequence": row["source_sequence"],
                    "to_sequence": row["transfer_arrival_sequence"],
                    "departure": row["first_departure"],
                    "arrival": row["first_arrival"],
                    "distance": row["first_distance"],
                    "stop_count": row["first_stop_count"],
                },
                {
                    "train_number": row["second_train_number"],
                    "train_name": row["second_train_name"],
                    "train_type": row["second_train_type"],
                    "from_station_code": row["transfer_station_code"],
                    "to_station_code": row["destination_station_code"],
                    "from_sequence": row["transfer_departure_sequence"],
                    "to_sequence": row["destination_sequence"],
                    "departure": row["second_departure"],
                    "arrival": row["second_arrival"],
                    "distance": row["second_distance"],
                    "stop_count": row["second_stop_count"],
                },
            ],
            "total_stop_count": row["total_stop_count"],
            "total_distance": row["total_distance"],
            "warnings": warnings,
        }

        route["score"] = score_transfer_route(route)
        routes.append(route)

    return routes


def score_direct_route(row: dict[str, Any]) -> int:
    stop_count = int(row.get("stop_count") or 0)
    distance = int(row.get("distance") or 0)

    score = 1000
    score -= min(stop_count * 8, 250)

    if distance > 0:
        score -= min(distance // 25, 120)

    return max(score, 100)


def score_transfer_route(route: dict[str, Any]) -> int:
    stop_count = int(route.get("total_stop_count") or 0)
    distance = int(route.get("total_distance") or 0)

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
) -> dict[str, Any]:
    source = source_station_code.upper().strip()
    destination = destination_station_code.upper().strip()

    direct_routes = find_direct_routes(
        source_station_code=source,
        destination_station_code=destination,
        limit=direct_limit,
    )

    transfer_routes = find_one_transfer_routes(
        source_station_code=source,
        destination_station_code=destination,
        limit=transfer_limit,
    )

    all_routes = direct_routes + transfer_routes
    all_routes.sort(
        key=lambda route: (
            -int(route.get("score") or 0),
            int(route.get("total_stop_count") or 9999),
            route.get("route_type") != "direct",
        )
    )

    return {
        "mode": "staging_read_only",
        "engine": "phase_3_staging_route_engine",
        "source": source,
        "destination": destination,
        "count": len(all_routes),
        "direct_count": len(direct_routes),
        "one_transfer_count": len(transfer_routes),
        "routes": all_routes,
        "database_write_skipped": True,
        "production_railway_tables_modified": False,
    }

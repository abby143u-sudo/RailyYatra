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


def to_dicts(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    return [dict(row) for row in rows]


def get_staging_counts() -> dict[str, int]:
    with get_connection() as conn:
        return {
            "staging_stations": conn.execute(
                "SELECT COUNT(*) AS count FROM staging_stations"
            ).fetchone()["count"],
            "staging_trains": conn.execute(
                "SELECT COUNT(*) AS count FROM staging_trains"
            ).fetchone()["count"],
            "staging_train_stops": conn.execute(
                "SELECT COUNT(*) AS count FROM staging_train_stops"
            ).fetchone()["count"],
        }


def find_station_by_code(station_code: str) -> dict[str, Any] | None:
    code = station_code.upper().strip()

    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT station_code, station_name, state, latitude, longitude
            FROM staging_stations
            WHERE station_code = ?
            LIMIT 1
            """,
            (code,),
        ).fetchone()

    return dict(row) if row else None


def search_stations(query: str, limit: int = 10) -> list[dict[str, Any]]:
    value = query.upper().strip()
    like_value = f"%{value}%"

    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT station_code, station_name, state, latitude, longitude
            FROM staging_stations
            WHERE station_code LIKE ?
               OR UPPER(COALESCE(station_name, '')) LIKE ?
            ORDER BY
                CASE WHEN station_code = ? THEN 0 ELSE 1 END,
                station_code
            LIMIT ?
            """,
            (like_value, like_value, value, limit),
        ).fetchall()

    return to_dicts(rows)


def find_train_by_number(train_number: str) -> dict[str, Any] | None:
    number = train_number.strip()

    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT train_number, train_name, source_station_code,
                   destination_station_code, train_type
            FROM staging_trains
            WHERE train_number = ?
            LIMIT 1
            """,
            (number,),
        ).fetchone()

    return dict(row) if row else None


def get_train_stops(train_number: str, limit: int = 200) -> list[dict[str, Any]]:
    number = train_number.strip()

    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT train_number, station_code, stop_sequence,
                   arrival, departure, distance, day_offset
            FROM staging_train_stops
            WHERE train_number = ?
            ORDER BY stop_sequence, id
            LIMIT ?
            """,
            (number, limit),
        ).fetchall()

    return to_dicts(rows)


def find_direct_trains(
    source_station_code: str,
    destination_station_code: str,
    limit: int = 20,
) -> list[dict[str, Any]]:
    source = source_station_code.upper().strip()
    destination = destination_station_code.upper().strip()

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
                s2.stop_sequence - s1.stop_sequence AS stop_count
            FROM staging_train_stops s1
            JOIN staging_train_stops s2
                ON s1.train_number = s2.train_number
               AND s2.stop_sequence > s1.stop_sequence
            LEFT JOIN staging_trains t
                ON t.train_number = s1.train_number
            WHERE s1.station_code = ?
              AND s2.station_code = ?
            ORDER BY stop_count ASC, s1.train_number
            LIMIT ?
            """,
            (source, destination, limit),
        ).fetchall()

    return to_dicts(rows)


def get_next_stops_from_station(
    station_code: str,
    limit: int = 50,
) -> list[dict[str, Any]]:
    code = station_code.upper().strip()

    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT
                current_stop.train_number AS train_number,
                train.train_name AS train_name,
                current_stop.station_code AS from_station_code,
                next_stop.station_code AS to_station_code,
                current_stop.stop_sequence AS from_sequence,
                next_stop.stop_sequence AS to_sequence,
                current_stop.departure AS departure,
                next_stop.arrival AS arrival
            FROM staging_train_stops current_stop
            JOIN staging_train_stops next_stop
                ON current_stop.train_number = next_stop.train_number
               AND next_stop.stop_sequence = current_stop.stop_sequence + 1
            LEFT JOIN staging_trains train
                ON train.train_number = current_stop.train_number
            WHERE current_stop.station_code = ?
            ORDER BY current_stop.train_number, current_stop.stop_sequence
            LIMIT ?
            """,
            (code, limit),
        ).fetchall()

    return to_dicts(rows)


def get_graph_edge_preview(limit: int = 100) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT
                current_stop.train_number AS train_number,
                current_stop.station_code AS from_station_code,
                next_stop.station_code AS to_station_code,
                current_stop.stop_sequence AS from_sequence,
                next_stop.stop_sequence AS to_sequence,
                current_stop.departure AS departure,
                next_stop.arrival AS arrival
            FROM staging_train_stops current_stop
            JOIN staging_train_stops next_stop
                ON current_stop.train_number = next_stop.train_number
               AND next_stop.stop_sequence = current_stop.stop_sequence + 1
            ORDER BY current_stop.train_number, current_stop.stop_sequence
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return to_dicts(rows)


def get_station_pair_train_count(
    source_station_code: str,
    destination_station_code: str,
) -> int:
    source = source_station_code.upper().strip()
    destination = destination_station_code.upper().strip()

    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT COUNT(*) AS count
            FROM staging_train_stops s1
            JOIN staging_train_stops s2
                ON s1.train_number = s2.train_number
               AND s2.stop_sequence > s1.stop_sequence
            WHERE s1.station_code = ?
              AND s2.station_code = ?
            """,
            (source, destination),
        ).fetchone()

    return int(row["count"])

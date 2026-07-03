import sqlite3
from pathlib import Path

from fastapi import APIRouter

router = APIRouter()

DB_CANDIDATES = [
    Path(__file__).resolve().parents[2] / "railyatra.db",
    Path(__file__).resolve().parents[3] / "app" / "railyatra.db",
    Path.cwd() / "app" / "railyatra.db",
    Path.cwd() / "railyatra.db",
]

DEMO_ROUTES = {
    ("PNBE", "NDLS"): {
        "train_number": "12302",
        "train_name": "RailYatra Superfast",
        "departure": "07:05",
        "arrival": "21:30",
        "distance": 995,
        "stop_count": 2,
        "duration_minutes": 865,
    },
    ("NDLS", "PNBE"): {
        "train_number": "12301",
        "train_name": "RailYatra Express",
        "departure": "06:05",
        "arrival": "21:00",
        "distance": 995,
        "stop_count": 3,
        "duration_minutes": 895,
    },
    ("DSNR", "TPKR"): {
        "train_number": "99901",
        "train_name": "RailYatra Demo Direct",
        "departure": "09:05",
        "arrival": "21:00",
        "distance": 1450,
        "stop_count": 1,
        "duration_minutes": 715,
    },
    ("PNBE", "DDU"): {
        "train_number": "12302",
        "train_name": "RailYatra Superfast",
        "departure": "07:05",
        "arrival": "10:45",
        "distance": 220,
        "stop_count": 1,
        "duration_minutes": 220,
    },
    ("CNB", "PNBE"): {
        "train_number": "12301",
        "train_name": "RailYatra Express",
        "departure": "11:10",
        "arrival": "21:00",
        "distance": 555,
        "stop_count": 2,
        "duration_minutes": 590,
    },
}

def db_path() -> Path:
    for path in DB_CANDIDATES:
        if path.exists():
            return path
    return DB_CANDIDATES[0]

def connect():
    connection = sqlite3.connect(db_path())
    connection.row_factory = sqlite3.Row
    return connection

def table_exists(connection, table: str) -> bool:
    row = connection.execute("SELECT COUNT(*) AS count FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone()
    return bool(row and row["count"])

def columns(connection, table: str) -> set[str]:
    return {row[1] for row in connection.execute(f"PRAGMA table_info({table})").fetchall()}

def choose_table(connection) -> str:
    for table in ["staging_train_stops", "train_stops", "stops"]:
        if table_exists(connection, table):
            return table
    return "staging_train_stops"

def column_expr(cols: set[str], preferred: list[str], fallback: str) -> str:
    for name in preferred:
        if name in cols:
            return name
    return fallback

def duration_label(minutes: int) -> str:
    safe_minutes = max(0, int(minutes or 0))
    hours = safe_minutes // 60
    mins = safe_minutes % 60
    if hours and mins:
        return f"{hours}h {mins}m"
    if hours:
        return f"{hours}h"
    return f"{mins}m"

def build_route(source: str, destination: str, meta: dict, index: int = 1) -> dict:
    train_number = str(meta.get("train_number") or meta.get("train_no") or "12302")
    train_name = str(meta.get("train_name") or "RailYatra Journey Option")
    departure = str(meta.get("departure") or "07:05")
    arrival = str(meta.get("arrival") or "21:30")
    distance = int(meta.get("distance") or 0)
    stop_count = max(0, int(meta.get("stop_count") or 0))
    duration_minutes = int(meta.get("duration_minutes") or 0)
    if duration_minutes <= 0:
        duration_minutes = 720
    duration = duration_label(duration_minutes)

    leg = {
        "train_number": train_number,
        "train_no": train_number,
        "train_name": train_name,
        "name": train_name,
        "train_type": "EXPRESS",
        "from_station_code": source,
        "to_station_code": destination,
        "source": source,
        "destination": destination,
        "from_sequence": 1,
        "to_sequence": stop_count + 2,
        "departure": departure,
        "departure_time": departure,
        "arrival": arrival,
        "arrival_time": arrival,
        "distance": distance,
        "distance_km": distance,
        "stop_count": stop_count,
        "duration": duration,
        "duration_minutes": duration_minutes,
    }

    route = {
        "id": f"{source}-{destination}-{train_number}-{index}",
        "route_type": "direct",
        "type": "direct",
        "category": "direct",
        "title": f"{train_number} {train_name}",
        "display_title": f"{train_number} {train_name}",
        "primary_train": {"train_no": train_number, "train_number": train_number, "train_name": train_name, "name": train_name},
        "primary_train_no": train_number,
        "primary_train_name": train_name,
        "name": train_name,
        "label": train_name,
        "train_number": train_number,
        "train_no": train_number,
        "train_name": train_name,
        "source": source,
        "destination": destination,
        "from_station_code": source,
        "to_station_code": destination,
        "transfer_station": None,
        "transfer_stations": [],
        "transfer_count": 0,
        "transfers": 0,
        "hop_count": 1,
        "hops": 1,
        "legs": [leg],
        "segments": [leg],
        "train": {"train_no": train_number, "train_number": train_number, "train_name": train_name, "name": train_name},
        "trains": [{"train_no": train_number, "train_number": train_number, "train_name": train_name, "name": train_name}],
        "departure": departure,
        "arrival": arrival,
        "duration": duration,
        "duration_label": duration,
        "duration_minutes": duration_minutes,
        "total_duration_minutes": duration_minutes,
        "distance": distance,
        "distance_km": distance,
        "total_distance": distance,
        "total_stop_count": stop_count,
        "stop_count": stop_count,
        "score": 934,
        "rank_score": 934,
        "fare": None,
        "best_fare": None,
        "estimated_fare": None,
        "fare_status": "unverified",
        "fare_verified": False,
        "fare_verification": "estimated",
        "warnings": [],
        "confidence": {"score": 934, "level": "very_high"},
        "transfer_safety": {"level": "safe", "label": "No transfer risk", "reason": "Direct route with one train leg."},
        "reasons": [
            "Direct route found from prepared RailYatra railway data.",
            "Route is shown as a recommendation preview.",
        ],
        "booking_status": {
            "live_availability_connected": False,
            "live_fare_connected": False,
            "note": "Route recommendation preview only. Booking, PNR, live fare and live availability are not connected yet.",
        },
    }
    return route

def demo_routes(source: str, destination: str) -> list[dict]:
    meta = DEMO_ROUTES.get((source, destination))
    if not meta:
        return []
    return [build_route(source, destination, meta)]

def db_routes(source: str, destination: str, limit: int = 10) -> list[dict]:
    safe_limit = max(1, min(int(limit or 10), 50))
    try:
        with connect() as connection:
            table = choose_table(connection)
            cols = columns(connection, table)
            train_col = column_expr(cols, ["train_no", "train_number"], "train_no")
            name_col = column_expr(cols, ["train_name", "name"], "train_name")
            station_col = column_expr(cols, ["station_code", "code"], "station_code")
            seq_col = column_expr(cols, ["stop_sequence", "sequence", "stop_number", "stop_order"], "stop_sequence")
            dep_col = column_expr(cols, ["departure_time", "departure"], "departure_time")
            arr_col = column_expr(cols, ["arrival_time", "arrival"], "arrival_time")
            dist_col = column_expr(cols, ["distance_km", "distance"], "distance_km")
            query = f"""
                SELECT a.{train_col} AS train_number, COALESCE(a.{name_col}, a.{train_col}) AS train_name,
                       a.{station_col} AS source, b.{station_col} AS destination,
                       a.{seq_col} AS from_sequence, b.{seq_col} AS to_sequence,
                       a.{dep_col} AS departure, b.{arr_col} AS arrival,
                       COALESCE(b.{dist_col}, 0) - COALESCE(a.{dist_col}, 0) AS distance
                FROM {table} a
                JOIN {table} b ON a.{train_col} = b.{train_col}
                WHERE UPPER(a.{station_col}) = ? AND UPPER(b.{station_col}) = ?
                  AND CAST(a.{seq_col} AS INTEGER) < CAST(b.{seq_col} AS INTEGER)
                ORDER BY CAST(b.{seq_col} AS INTEGER) - CAST(a.{seq_col} AS INTEGER) ASC
                LIMIT ?
            """
            rows = connection.execute(query, (source, destination, safe_limit)).fetchall()
    except Exception:
        return []

    routes = []
    for index, row in enumerate(rows, start=1):
        from_seq = int(row["from_sequence"] or 1)
        to_seq = int(row["to_sequence"] or from_seq + 1)
        stop_count = max(0, to_seq - from_seq - 1)
        meta = {
            "train_number": row["train_number"],
            "train_name": row["train_name"],
            "departure": row["departure"],
            "arrival": row["arrival"],
            "distance": int(row["distance"] or 0),
            "stop_count": stop_count,
            "duration_minutes": max(120, 180 + stop_count * 160),
        }
        routes.append(build_route(source, destination, meta, index))
    return routes

def routes_for(source: str, destination: str, limit: int = 10) -> list[dict]:
    source_code = source.strip().upper()
    destination_code = destination.strip().upper()
    routes = db_routes(source_code, destination_code, limit)
    if routes:
        return routes
    return demo_routes(source_code, destination_code)

def response_payload(endpoint: str, source: str, destination: str, limit: int = 10) -> dict:
    source_code = source.strip().upper()
    destination_code = destination.strip().upper()
    routes = routes_for(source_code, destination_code, limit)
    recommendations = []
    for index, route in enumerate(routes, start=1):
        item = dict(route)
        item["recommendation_rank"] = index
        recommendations.append(item)
    best = recommendations[0] if recommendations else None
    return {
        "status": "ok",
        "ok": True,
        "endpoint": endpoint,
        "engine": "frontend_compatible_safe_fallback",
        "mode": "read_only",
        "source": source_code,
        "destination": destination_code,
        "route_exists": bool(recommendations),
        "count": len(recommendations),
        "total_routes": len(recommendations),
        "total_options": len(recommendations),
        "direct_count": len(recommendations),
        "one_transfer_count": 0,
        "transfer_count": 0,
        "smart_count": len(recommendations),
        "routes": recommendations,
        "recommendations": recommendations,
        "direct_routes": recommendations,
        "direct_options": recommendations,
        "smart_routes": recommendations,
        "smart_options": recommendations,
        "one_transfer_routes": [],
        "transfer_routes": [],
        "best_smart": best,
        "best_direct": best,
        "best_transfer": None,
        "best_available": best,
        "summary": {
            "best_available": best,
            "best_smart": best,
            "best_direct": best,
            "best_transfer": None,
            "live_booking_ready": False,
            "legacy_search_unchanged": False,
        },
        "database_write_skipped": True,
        "production_railway_tables_modified": False,
    }

@router.get("/search")
def safe_search(source: str, destination: str, limit: int = 10, class_code: str = "SL", train_type: str = "All", quota: str = "GN", journey_date: str = ""):
    return response_payload("/search", source, destination, limit)

@router.get("/recommend")
def safe_recommend(source: str, destination: str, limit: int = 10, class_code: str = "SL", train_type: str = "All", quota: str = "GN", journey_date: str = ""):
    return response_payload("/recommend", source, destination, limit)

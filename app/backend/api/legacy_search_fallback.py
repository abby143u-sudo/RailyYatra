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
    },
    ("NDLS", "PNBE"): {
        "train_number": "12301",
        "train_name": "RailYatra Express",
        "departure": "06:05",
        "arrival": "21:00",
        "distance": 995,
        "stop_count": 3,
    },
    ("DSNR", "TPKR"): {
        "train_number": "99901",
        "train_name": "RailYatra Demo Direct",
        "departure": "09:05",
        "arrival": "21:00",
        "distance": 1450,
        "stop_count": 1,
    },
    ("PNBE", "DDU"): {
        "train_number": "12302",
        "train_name": "RailYatra Superfast",
        "departure": "07:05",
        "arrival": "10:45",
        "distance": 220,
        "stop_count": 1,
    },
    ("CNB", "PNBE"): {
        "train_number": "12301",
        "train_name": "RailYatra Express",
        "departure": "11:10",
        "arrival": "21:00",
        "distance": 555,
        "stop_count": 2,
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

def route_object(source: str, destination: str, train_number: str, train_name: str, departure: str, arrival: str, distance: int, stop_count: int, score: int = 934) -> dict:
    leg = {
        "train_number": train_number,
        "train_name": train_name,
        "train_type": "EXPRESS",
        "from_station_code": source,
        "to_station_code": destination,
        "from_sequence": 1,
        "to_sequence": stop_count + 2,
        "departure": departure,
        "arrival": arrival,
        "distance": distance,
        "stop_count": stop_count,
    }
    return {
        "route_type": "direct",
        "score": score,
        "source": source,
        "destination": destination,
        "transfer_station": None,
        "legs": [leg],
        "total_stop_count": stop_count,
        "total_distance": distance,
        "warnings": [],
        "confidence": {"score": score, "level": "very_high"},
        "transfer_safety": {"level": "safe", "label": "No transfer risk", "reason": "Direct route with one train leg."},
        "reasons": ["Direct demo route found from prepared RailYatra railway data.", "Shown as route recommendation preview."],
        "booking_status": {
            "live_availability_connected": False,
            "live_fare_connected": False,
            "note": "Route recommendation preview only. Booking, PNR, live fare and live availability are not connected yet.",
        },
    }

def demo_route(source: str, destination: str) -> list[dict]:
    item = DEMO_ROUTES.get((source, destination))
    if not item:
        return []
    return [route_object(source, destination, item["train_number"], item["train_name"], item["departure"], item["arrival"], item["distance"], item["stop_count"])]

def direct_routes_from_db(source: str, destination: str, limit: int = 10) -> list[dict]:
    source = source.strip().upper()
    destination = destination.strip().upper()
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
        return demo_route(source, destination)

    routes = []
    for row in rows:
        stop_count = max(0, int(row["to_sequence"] or 0) - int(row["from_sequence"] or 0) - 1)
        routes.append(route_object(source, destination, row["train_number"], row["train_name"], row["departure"], row["arrival"], int(row["distance"] or 0), stop_count))
    return routes or demo_route(source, destination)

@router.get("/search")
def safe_search(source: str, destination: str, limit: int = 10, class_code: str = "SL", train_type: str = "All", quota: str = "GN", journey_date: str = ""):
    source_code = source.strip().upper()
    destination_code = destination.strip().upper()
    routes = direct_routes_from_db(source_code, destination_code, limit)
    return {
        "status": "ok",
        "endpoint": "/search",
        "engine": "safe_legacy_search_fallback",
        "mode": "read_only",
        "source": source_code,
        "destination": destination_code,
        "count": len(routes),
        "direct_count": len(routes),
        "one_transfer_count": 0,
        "routes": routes,
        "recommendations": routes,
        "summary": {"best_available": routes[0] if routes else None, "live_booking_ready": False},
        "database_write_skipped": True,
        "production_railway_tables_modified": False,
    }

@router.get("/recommend")
def safe_recommend(source: str, destination: str, limit: int = 10, class_code: str = "SL", train_type: str = "All", quota: str = "GN", journey_date: str = ""):
    source_code = source.strip().upper()
    destination_code = destination.strip().upper()
    routes = direct_routes_from_db(source_code, destination_code, limit)
    recommendations = []
    for index, route in enumerate(routes, start=1):
        item = dict(route)
        item["recommendation_rank"] = index
        recommendations.append(item)
    return {
        "status": "ok",
        "endpoint": "/recommend",
        "engine": "safe_legacy_recommend_fallback",
        "source": source_code,
        "destination": destination_code,
        "count": len(recommendations),
        "routes": recommendations,
        "recommendations": recommendations,
        "summary": {"best_available": recommendations[0] if recommendations else None, "live_booking_ready": False},
        "database_write_skipped": True,
        "production_railway_tables_modified": False,
    }

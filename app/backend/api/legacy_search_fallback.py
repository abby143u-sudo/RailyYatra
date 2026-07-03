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

def direct_routes(source: str, destination: str, limit: int = 10) -> list[dict]:
    source = source.strip().upper()
    destination = destination.strip().upper()
    safe_limit = max(1, min(int(limit or 10), 50))

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
            SELECT
                a.{train_col} AS train_number,
                COALESCE(a.{name_col}, a.{train_col}) AS train_name,
                a.{station_col} AS source,
                b.{station_col} AS destination,
                a.{seq_col} AS from_sequence,
                b.{seq_col} AS to_sequence,
                a.{dep_col} AS departure,
                b.{arr_col} AS arrival,
                COALESCE(b.{dist_col}, 0) - COALESCE(a.{dist_col}, 0) AS distance
            FROM {table} a
            JOIN {table} b ON a.{train_col} = b.{train_col}
            WHERE UPPER(a.{station_col}) = ?
              AND UPPER(b.{station_col}) = ?
              AND CAST(a.{seq_col} AS INTEGER) < CAST(b.{seq_col} AS INTEGER)
            ORDER BY CAST(b.{seq_col} AS INTEGER) - CAST(a.{seq_col} AS INTEGER) ASC
            LIMIT ?
        """
        rows = connection.execute(query, (source, destination, safe_limit)).fetchall()

    routes = []
    for row in rows:
        leg = {
            "train_number": row["train_number"],
            "train_name": row["train_name"],
            "train_type": "EXPRESS",
            "from_station_code": row["source"],
            "to_station_code": row["destination"],
            "from_sequence": row["from_sequence"],
            "to_sequence": row["to_sequence"],
            "departure": row["departure"],
            "arrival": row["arrival"],
            "distance": row["distance"],
            "stop_count": max(0, int(row["to_sequence"] or 0) - int(row["from_sequence"] or 0) - 1),
        }
        routes.append({
            "route_type": "direct",
            "score": 900,
            "source": source,
            "destination": destination,
            "transfer_station": None,
            "legs": [leg],
            "total_stop_count": leg["stop_count"],
            "total_distance": leg["distance"],
            "warnings": [],
        })
    return routes

@router.get("/search")
def safe_search(source: str, destination: str, limit: int = 10, class_code: str = "SL", train_type: str = "All", quota: str = "GN", journey_date: str = ""):
    routes = direct_routes(source, destination, limit)
    return {
        "status": "ok",
        "endpoint": "/search",
        "engine": "safe_legacy_search_fallback",
        "mode": "read_only",
        "source": source.strip().upper(),
        "destination": destination.strip().upper(),
        "count": len(routes),
        "direct_count": len(routes),
        "one_transfer_count": 0,
        "routes": routes,
        "database_write_skipped": True,
        "production_railway_tables_modified": False,
        "booking_status": {
            "live_availability_connected": False,
            "live_fare_connected": False,
            "note": "Route recommendation preview only. Booking, PNR, live fare and live availability are not connected yet.",
        },
    }

@router.get("/recommend")
def safe_recommend(source: str, destination: str, limit: int = 10, class_code: str = "SL", train_type: str = "All", quota: str = "GN", journey_date: str = ""):
    routes = direct_routes(source, destination, limit)
    recommendations = []
    for index, route in enumerate(routes, start=1):
        item = dict(route)
        item["recommendation_rank"] = index
        item["confidence"] = {"score": route.get("score", 900), "level": "high"}
        item["transfer_safety"] = {"level": "safe", "label": "No transfer risk", "reason": "Direct route with one train leg."}
        item["reasons"] = ["Direct route found from prepared railway data.", "Route is shown as preview recommendation."]
        recommendations.append(item)
    return {
        "status": "ok",
        "endpoint": "/recommend",
        "engine": "safe_legacy_recommend_fallback",
        "source": source.strip().upper(),
        "destination": destination.strip().upper(),
        "count": len(recommendations),
        "recommendations": recommendations,
        "summary": {"best_available": recommendations[0] if recommendations else None, "live_booking_ready": False},
        "database_write_skipped": True,
        "production_railway_tables_modified": False,
    }

import sqlite3
from pathlib import Path

from fastapi import APIRouter, Query

router = APIRouter()

DB_CANDIDATES = [
    Path(__file__).resolve().parents[2] / "railyatra.db",
    Path(__file__).resolve().parents[3] / "app" / "railyatra.db",
    Path.cwd() / "app" / "railyatra.db",
    Path.cwd() / "railyatra.db",
]

DEMO_STATIONS = [
    {"code": "PNBE", "name": "Patna Junction", "city": "Patna"},
    {"code": "NDLS", "name": "New Delhi", "city": "Delhi"},
    {"code": "DDU", "name": "Pt. Deen Dayal Upadhyaya", "city": "Mughalsarai"},
    {"code": "MGS", "name": "Mughalsarai legacy code", "city": "Mughalsarai"},
    {"code": "CNB", "name": "Kanpur Central", "city": "Kanpur"},
    {"code": "PRYJ", "name": "Prayagraj Junction", "city": "Prayagraj"},
    {"code": "BSB", "name": "Varanasi Junction", "city": "Varanasi"},
    {"code": "GAYA", "name": "Gaya Junction", "city": "Gaya"},
]

DEMO_ROUTES = [
    {"source": "PNBE", "destination": "NDLS", "label": "Patna to Delhi"},
    {"source": "NDLS", "destination": "PNBE", "label": "Delhi to Patna"},
    {"source": "PNBE", "destination": "DDU", "label": "Patna to DDU"},
    {"source": "CNB", "destination": "PNBE", "label": "Kanpur to Patna"},
    {"source": "DSNR", "destination": "TPKR", "label": "Delhi demo route"},
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

def count_table(connection, table: str) -> int:
    if not table_exists(connection, table):
        return 0
    try:
        return int(connection.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()["count"])
    except Exception:
        return 0

def table_columns(connection, table: str) -> list[str]:
    if not table_exists(connection, table):
        return []
    try:
        return [row[1] for row in connection.execute(f"PRAGMA table_info({table})").fetchall()]
    except Exception:
        return []

def choose_station_table(connection) -> str:
    for table in ["staging_stations", "stations"]:
        if table_exists(connection, table):
            return table
    return ""

def choose_column(columns: list[str], names: list[str], fallback: str) -> str:
    for name in names:
        if name in columns:
            return name
    return fallback

@router.get("/data-quality/health")
def data_quality_health():
    path = db_path()
    payload = {
        "ok": True,
        "database_path": str(path),
        "database_exists": path.exists(),
        "counts": {},
        "tables": {},
        "railway_data_ready": False,
        "station_autocomplete_ready": False,
        "route_demo_ready": True,
    }
    try:
        with connect() as connection:
            for table in ["staging_stations", "staging_trains", "staging_train_stops", "stations", "trains", "train_stops", "stops"]:
                columns = table_columns(connection, table)
                count = count_table(connection, table)
                payload["counts"][table] = count
                payload["tables"][table] = {
                    "exists": bool(columns),
                    "count": count,
                    "columns": columns[:40],
                    "has_stop_sequence": "stop_sequence" in columns,
                    "has_stop_order": "stop_order" in columns,
                }
            station_count = payload["counts"].get("staging_stations", 0) or payload["counts"].get("stations", 0)
            stop_count = payload["counts"].get("staging_train_stops", 0) or payload["counts"].get("train_stops", 0) or payload["counts"].get("stops", 0)
            train_count = payload["counts"].get("staging_trains", 0) or payload["counts"].get("trains", 0)
            payload["railway_data_ready"] = station_count > 0 and train_count > 0 and stop_count > 0
            payload["station_autocomplete_ready"] = station_count > 0
    except Exception as error:
        payload["ok"] = False
        payload["error"] = str(error)
    return payload

@router.get("/data-quality/stations")
def station_autocomplete(query: str = Query("", max_length=80), limit: int = 12):
    clean_query = (query or "").strip().upper()
    safe_limit = max(1, min(int(limit or 12), 30))
    results = []
    try:
        with connect() as connection:
            table = choose_station_table(connection)
            if table:
                cols = table_columns(connection, table)
                code_col = choose_column(cols, ["station_code", "code"], "station_code")
                name_col = choose_column(cols, ["station_name", "name"], code_col)
                city_col = choose_column(cols, ["city", "district", "state"], name_col)
                if clean_query:
                    rows = connection.execute(f"SELECT {code_col} AS code, {name_col} AS name, {city_col} AS city FROM {table} WHERE UPPER({code_col}) LIKE ? OR UPPER({name_col}) LIKE ? LIMIT ?", (f"%{clean_query}%", f"%{clean_query}%", safe_limit)).fetchall()
                else:
                    rows = connection.execute(f"SELECT {code_col} AS code, {name_col} AS name, {city_col} AS city FROM {table} LIMIT ?", (safe_limit,)).fetchall()
                results = [{"code": str(row["code"] or "").upper(), "name": str(row["name"] or ""), "city": str(row["city"] or "")} for row in rows]
    except Exception:
        results = []

    if not results:
        pool = DEMO_STATIONS
        if clean_query:
            pool = [item for item in DEMO_STATIONS if clean_query in item["code"].upper() or clean_query in item["name"].upper() or clean_query in item["city"].upper()]
        results = pool[:safe_limit]

    return {
        "ok": True,
        "query": clean_query,
        "count": len(results),
        "stations": results,
        "fallback_used": len(results) > 0 and all(item in DEMO_STATIONS for item in results),
    }

@router.get("/data-quality/demo-routes")
def demo_routes():
    return {
        "ok": True,
        "count": len(DEMO_ROUTES),
        "routes": DEMO_ROUTES,
        "note": "These are safe demo routes for public beta testing.",
    }

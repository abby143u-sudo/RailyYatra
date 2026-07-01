#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sqlite3
import shutil
from pathlib import Path
from typing import Any

APP_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = APP_ROOT / "railyatra.db"
RAW_DIR = APP_ROOT / "data" / "raw"
STATIONS_PATH = RAW_DIR / "stations.json"
TRAINS_PATH = RAW_DIR / "trains.json"
SCHEDULES_PATH = RAW_DIR / "schedules.json"

def norm_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value).lower())

def normalize_row(row: dict[str, Any]) -> dict[str, Any]:
    merged = dict(row)
    props = row.get("properties")
    if isinstance(props, dict):
        merged.update(props)
    geometry = row.get("geometry")
    if isinstance(geometry, dict):
        coords = geometry.get("coordinates")
        if isinstance(coords, list) and len(coords) >= 2:
            merged.setdefault("longitude", coords[0])
            merged.setdefault("latitude", coords[1])
    return merged

def add_parent_value(record: dict[str, Any], parent_key: str | None, kind: str) -> dict[str, Any]:
    copied = normalize_row(record)
    if parent_key:
        if kind == "stations" and not get_value(copied, ["stationcode", "code", "stncode"]):
            copied["station_code"] = parent_key
        if kind in ["trains", "schedules"] and not get_value(copied, ["trainnumber", "trainno", "number", "trainnum"]):
            copied["train_number"] = parent_key
    return copied

def get_value(row: dict[str, Any], aliases: list[str], default: Any = None) -> Any:
    normalized = {norm_key(key): value for key, value in row.items()}
    for alias in aliases:
        value = normalized.get(norm_key(alias))
        if value not in [None, ""]:
            return value
    return default

def flatten_records(data: Any, kind: str, parent_key: str | None = None) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                records.append(add_parent_value(item, parent_key, kind))
            elif isinstance(item, list):
                records.extend(flatten_records(item, kind, parent_key))
        return records
    if isinstance(data, dict):
        preferred_keys = [kind, "data", "items", "results", "records", "features", "stations", "trains", "schedules", "stops", "train_stops"]
        for key in preferred_keys:
            if key in data and isinstance(data[key], list):
                found = flatten_records(data[key], kind, parent_key)
                if found:
                    return found
        looks_like_record = False
        row = normalize_row(data)
        if kind == "stations" and get_value(row, ["stationcode", "code", "stncode", "station"]):
            looks_like_record = True
        if kind == "trains" and get_value(row, ["trainnumber", "trainno", "number", "trainnum"]):
            looks_like_record = True
        if kind == "schedules" and get_value(row, ["stationcode", "code", "stncode", "station"]):
            looks_like_record = True
        if looks_like_record:
            return [add_parent_value(data, parent_key, kind)]
        for key, value in data.items():
            if isinstance(value, dict):
                records.extend(flatten_records(value, kind, str(key)))
            elif isinstance(value, list):
                records.extend(flatten_records(value, kind, str(key)))
            elif kind == "stations" and value not in [None, ""]:
                records.append({"station_code": str(key), "station_name": str(value)})
        return records
    return records

def load_records(path: Path, kind: str) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing raw data file: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    records = flatten_records(data, kind)
    if not records:
        sample = str(data)[:500]
        raise ValueError(f"Unsupported JSON shape: {path}. Sample: {sample}")
    print(f"Loaded {len(records)} records from {path.name}")
    if records:
        print(f"Sample {kind} keys: {list(records[0].keys())[:20]}")
    return records

def text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value).strip()

def integer(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default

def floating(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None

def create_tables(conn: sqlite3.Connection) -> None:
    statements = [
        "DROP TABLE IF EXISTS staging_train_stops",
        "DROP TABLE IF EXISTS staging_trains",
        "DROP TABLE IF EXISTS staging_stations",
        "CREATE TABLE staging_stations (id INTEGER PRIMARY KEY AUTOINCREMENT, station_code TEXT UNIQUE NOT NULL, station_name TEXT, state TEXT, station_state TEXT, latitude REAL, longitude REAL)",
        "CREATE TABLE staging_trains (id INTEGER PRIMARY KEY AUTOINCREMENT, train_number TEXT UNIQUE NOT NULL, train_name TEXT, source_station_code TEXT, destination_station_code TEXT, source TEXT, destination TEXT, train_type TEXT, runs_on TEXT)",
        "CREATE TABLE staging_train_stops (id INTEGER PRIMARY KEY AUTOINCREMENT, train_number TEXT NOT NULL, station_code TEXT NOT NULL, station_name TEXT, sequence INTEGER NOT NULL, stop_sequence INTEGER NOT NULL, arrival TEXT, departure TEXT, arrival_time TEXT, departure_time TEXT, distance INTEGER, distance_from_source INTEGER, day_offset INTEGER DEFAULT 0)",
        "CREATE INDEX IF NOT EXISTS idx_staging_stations_code_name ON staging_stations(station_code, station_name)",
        "CREATE INDEX IF NOT EXISTS idx_staging_trains_number ON staging_trains(train_number)",
        "CREATE INDEX IF NOT EXISTS idx_staging_train_stops_station_train_sequence ON staging_train_stops(station_code, train_number, stop_sequence)",
        "CREATE INDEX IF NOT EXISTS idx_staging_train_stops_train_sequence_station ON staging_train_stops(train_number, stop_sequence, station_code)",
        "CREATE INDEX IF NOT EXISTS idx_staging_train_stops_station_sequence ON staging_train_stops(station_code, stop_sequence)",
        "CREATE INDEX IF NOT EXISTS idx_staging_train_stops_train_station_sequence ON staging_train_stops(train_number, station_code, stop_sequence)",
    ]
    for statement in statements:
        conn.execute(statement)

def import_stations(conn: sqlite3.Connection) -> int:
    rows = load_records(STATIONS_PATH, "stations")
    prepared = []
    skipped = 0
    for row in rows:
        code = text(get_value(row, ["station_code", "stationcode", "code", "station", "stn_code", "stncode"]))
        if not code:
            skipped += 1
            continue
        name = text(get_value(row, ["station_name", "stationname", "name", "stn_name", "stnname"], code), code)
        state = text(get_value(row, ["state", "station_state", "stationstate"], ""))
        latitude = floating(get_value(row, ["latitude", "lat"]))
        longitude = floating(get_value(row, ["longitude", "lng", "lon"]))
        prepared.append((code.upper(), name, state, state, latitude, longitude))
    print(f"Prepared stations: {len(prepared)} skipped: {skipped}")
    conn.executemany("INSERT OR REPLACE INTO staging_stations (station_code, station_name, state, station_state, latitude, longitude) VALUES (?, ?, ?, ?, ?, ?)", prepared)
    return len(prepared)

def import_trains(conn: sqlite3.Connection) -> int:
    rows = load_records(TRAINS_PATH, "trains")
    prepared = []
    skipped = 0
    for row in rows:
        number = text(get_value(row, ["train_number", "trainnumber", "train_no", "trainno", "number", "train_num", "trainnum"]))
        if not number:
            skipped += 1
            continue
        name = text(get_value(row, ["train_name", "trainname", "name"], f"Train {number}"), f"Train {number}")
        source = text(get_value(row, ["source_station_code", "sourcestationcode", "source", "from", "src"], ""))
        destination = text(get_value(row, ["destination_station_code", "destinationstationcode", "destination", "to", "dest"], ""))
        train_type = text(get_value(row, ["train_type", "traintype", "type"], ""))
        runs_raw = get_value(row, ["runs_on", "runson", "days", "run_days", "rundays"], "")
        runs_on = ",".join(str(item) for item in runs_raw) if isinstance(runs_raw, list) else text(runs_raw)
        prepared.append((number, name, source.upper(), destination.upper(), source.upper(), destination.upper(), train_type, runs_on))
    print(f"Prepared trains: {len(prepared)} skipped: {skipped}")
    conn.executemany("INSERT OR REPLACE INTO staging_trains (train_number, train_name, source_station_code, destination_station_code, source, destination, train_type, runs_on) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", prepared)
    return len(prepared)

def import_schedules(conn: sqlite3.Connection) -> int:
    rows = load_records(SCHEDULES_PATH, "schedules")
    prepared = []
    skipped = 0
    for index, row in enumerate(rows, start=1):
        train_number = text(get_value(row, ["train_number", "trainnumber", "train_no", "trainno", "number", "train_num", "trainnum"]))
        station_code = text(get_value(row, ["station_code", "stationcode", "station", "code", "stn_code", "stncode"]))
        if not train_number or not station_code:
            skipped += 1
            continue
        station_name = text(get_value(row, ["station_name", "stationname", "name", "stn_name", "stnname"], ""))
        sequence = integer(get_value(row, ["stop_sequence", "stopsequence", "sequence", "seq", "stop_number", "stopnumber"], index), index)
        arrival = text(get_value(row, ["arrival", "arrival_time", "arrivaltime", "arr"], ""))
        departure = text(get_value(row, ["departure", "departure_time", "departuretime", "dep"], ""))
        distance = integer(get_value(row, ["distance", "distance_from_source", "distancefromsource", "km"], 0), 0)
        day_offset = integer(get_value(row, ["day_offset", "dayoffset", "day"], 0), 0)
        prepared.append((train_number, station_code.upper(), station_name, sequence, sequence, arrival, departure, arrival, departure, distance, distance, day_offset))
    print(f"Prepared train stops: {len(prepared)} skipped: {skipped}")
    conn.executemany("INSERT INTO staging_train_stops (train_number, station_code, station_name, sequence, stop_sequence, arrival, departure, arrival_time, departure_time, distance, distance_from_source, day_offset) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", prepared)
    return len(prepared)


def create_compatibility_views(conn: sqlite3.Connection) -> None:
    conn.execute("CREATE VIEW IF NOT EXISTS stations AS SELECT id, station_code AS code, station_name AS name, station_code, station_name, state, station_state, latitude, longitude FROM staging_stations")
    conn.execute("CREATE VIEW IF NOT EXISTS trains AS SELECT id, train_number, train_name, source_station_code, destination_station_code, source, destination, train_type, runs_on FROM staging_trains")
    conn.execute("CREATE VIEW IF NOT EXISTS train_stops AS SELECT id, train_number, station_code, station_name, sequence, stop_sequence, arrival, departure, arrival_time, departure_time, distance, distance_from_source, day_offset FROM staging_train_stops")

def verify(conn: sqlite3.Connection) -> dict[str, int]:
    counts = {}
    for table in ["staging_stations", "staging_trains", "staging_train_stops"]:
        counts[table] = int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
    for table, count in counts.items():
        if count <= 0:
            raise RuntimeError(f"No rows imported into {table}")
    return counts

def main() -> int:
    print("RailYatra deploy database preparation")
    print(f"App root: {APP_ROOT}")
    print(f"Database: {DB_PATH}")
    print(f"Raw data: {RAW_DIR}")
    conn = sqlite3.connect(DB_PATH)
    try:
        create_tables(conn)
        station_count = import_stations(conn)
        train_count = import_trains(conn)
        stop_count = import_schedules(conn)
        conn.commit()
        create_compatibility_views(conn)
        counts = verify(conn)
        print(f"Stations imported: {station_count}")
        print(f"Trains imported: {train_count}")
        print(f"Train stops imported: {stop_count}")
        print(f"Verified counts: {counts}")
        alt_dir = APP_ROOT / "app"
        alt_dir.mkdir(exist_ok=True)
        alt_db_path = alt_dir / "railyatra.db"
        if alt_db_path.resolve() != DB_PATH.resolve():
            shutil.copy2(DB_PATH, alt_db_path)
            print(f"Runtime database copy created: {alt_db_path}")
        print("PASS: deploy database prepared")
        return 0
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    raise SystemExit(main())

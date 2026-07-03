#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sqlite3

DB_PATH = Path(__file__).resolve().parents[1] / "app" / "railyatra.db"

STATIONS = [
    ("NDLS", "New Delhi", "Delhi", "Delhi"),
    ("PNBE", "Patna Junction", "Patna", "Bihar"),
    ("CNB", "Kanpur Central", "Kanpur", "Uttar Pradesh"),
    ("PRYJ", "Prayagraj Junction", "Prayagraj", "Uttar Pradesh"),
    ("BSB", "Varanasi Junction", "Varanasi", "Uttar Pradesh"),
    ("DDU", "Pt. Deen Dayal Upadhyaya Junction", "Mughalsarai", "Uttar Pradesh"),
    ("MGS", "Mughalsarai Junction", "Mughalsarai", "Uttar Pradesh"),
    ("GAYA", "Gaya Junction", "Gaya", "Bihar"),
    ("DSNR", "Delhi Shahdara North Road", "Delhi", "Delhi"),
    ("TPKR", "Tikiapara", "Howrah", "West Bengal"),
]

TRAINS = [
    ("12301", "RailYatra Express", "NDLS", "PNBE", "Mon,Tue,Wed,Thu,Fri,Sat,Sun"),
    ("12302", "RailYatra Superfast", "PNBE", "NDLS", "Mon,Tue,Wed,Thu,Fri,Sat,Sun"),
    ("12303", "RailYatra Gaya Link", "PNBE", "NDLS", "Mon,Tue,Wed,Thu,Fri,Sat,Sun"),
    ("99901", "RailYatra Demo Direct", "DSNR", "TPKR", "Mon,Tue,Wed,Thu,Fri,Sat,Sun"),
    ("99902", "RailYatra Demo Transfer", "DSNR", "TPKR", "Mon,Tue,Wed,Thu,Fri,Sat,Sun"),
]

STOPS = [
    ("12301", "RailYatra Express", "NDLS", 1, "06:00", "06:05", 0, 0),
    ("12301", "RailYatra Express", "CNB", 2, "11:00", "11:10", 0, 440),
    ("12301", "RailYatra Express", "PRYJ", 3, "14:00", "14:10", 0, 635),
    ("12301", "RailYatra Express", "BSB", 4, "17:00", "17:10", 0, 760),
    ("12301", "RailYatra Express", "PNBE", 5, "21:00", "21:05", 0, 995),
    ("12302", "RailYatra Superfast", "PNBE", 1, "07:00", "07:05", 0, 0),
    ("12302", "RailYatra Superfast", "MGS", 2, "10:30", "10:40", 0, 215),
    ("12302", "RailYatra Superfast", "DDU", 3, "10:45", "10:55", 0, 220),
    ("12302", "RailYatra Superfast", "NDLS", 4, "21:30", "21:35", 0, 995),
    ("12303", "RailYatra Gaya Link", "PNBE", 1, "08:00", "08:05", 0, 0),
    ("12303", "RailYatra Gaya Link", "GAYA", 2, "10:00", "10:10", 0, 95),
    ("12303", "RailYatra Gaya Link", "DDU", 3, "14:30", "14:40", 0, 295),
    ("12303", "RailYatra Gaya Link", "NDLS", 4, "23:30", "23:35", 0, 995),
    ("99901", "RailYatra Demo Direct", "DSNR", 1, "09:00", "09:05", 0, 0),
    ("99901", "RailYatra Demo Direct", "TPKR", 2, "21:00", "21:05", 0, 1450),
    ("99902", "RailYatra Demo Transfer", "DSNR", 1, "10:00", "10:05", 0, 0),
    ("99902", "RailYatra Demo Transfer", "NDLS", 2, "10:30", "10:40", 0, 15),
    ("99902", "RailYatra Demo Transfer", "TPKR", 3, "22:30", "22:35", 0, 1465),
]

def station_name(code: str) -> str:
    for station_code, name, city, state in STATIONS:
        if station_code == code:
            return name
    return code

def ensure_columns(connection, table: str, columns: dict[str, str]) -> None:
    existing = {row[1] for row in connection.execute(f"PRAGMA table_info({table})").fetchall()}
    for name, definition in columns.items():
        if name not in existing:
            connection.execute(f"ALTER TABLE {table} ADD COLUMN {name} {definition}")

def prepare_stations(connection, table: str) -> None:
    connection.execute(f"CREATE TABLE IF NOT EXISTS {table} (station_code TEXT, station_name TEXT, code TEXT, name TEXT, city TEXT, state TEXT, latitude REAL, longitude REAL)")
    ensure_columns(connection, table, {"station_code": "TEXT", "station_name": "TEXT", "code": "TEXT", "name": "TEXT", "city": "TEXT", "state": "TEXT", "latitude": "REAL", "longitude": "REAL"})
    codes = [item[0] for item in STATIONS]
    placeholders = ",".join(["?"] * len(codes))
    try:
        connection.execute(f"DELETE FROM {table} WHERE station_code IN ({placeholders}) OR code IN ({placeholders})", codes + codes)
        connection.executemany(f"INSERT INTO {table} (station_code, station_name, code, name, city, state, latitude, longitude) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", [(code, name, code, name, city, state, None, None) for code, name, city, state in STATIONS])
    except Exception as error:
        print(f"WARNING: could not seed {table}: {error}")

def prepare_trains(connection, table: str) -> None:
    connection.execute(f"CREATE TABLE IF NOT EXISTS {table} (train_no TEXT, train_number TEXT, train_name TEXT, name TEXT, source TEXT, destination TEXT, runs_on TEXT, train_type TEXT)")
    ensure_columns(connection, table, {"train_no": "TEXT", "train_number": "TEXT", "train_name": "TEXT", "name": "TEXT", "source": "TEXT", "destination": "TEXT", "runs_on": "TEXT", "train_type": "TEXT"})
    train_numbers = [item[0] for item in TRAINS]
    placeholders = ",".join(["?"] * len(train_numbers))
    try:
        connection.execute(f"DELETE FROM {table} WHERE train_no IN ({placeholders}) OR train_number IN ({placeholders})", train_numbers + train_numbers)
        connection.executemany(f"INSERT INTO {table} (train_no, train_number, train_name, name, source, destination, runs_on, train_type) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", [(no, no, name, name, src, dst, runs, "EXPRESS") for no, name, src, dst, runs in TRAINS])
    except Exception as error:
        print(f"WARNING: could not seed {table}: {error}")

def prepare_stops(connection, table: str) -> None:
    connection.execute(f"CREATE TABLE IF NOT EXISTS {table} (train_no TEXT, train_number TEXT, train_name TEXT, station_code TEXT, station_name TEXT, code TEXT, name TEXT, stop_sequence INTEGER, sequence INTEGER, stop_number INTEGER, arrival_time TEXT, departure_time TEXT, arrival TEXT, departure TEXT, day_offset INTEGER, distance_km REAL, distance REAL)")
    ensure_columns(connection, table, {"train_no": "TEXT", "train_number": "TEXT", "train_name": "TEXT", "station_code": "TEXT", "station_name": "TEXT", "code": "TEXT", "name": "TEXT", "stop_sequence": "INTEGER", "sequence": "INTEGER", "stop_number": "INTEGER", "arrival_time": "TEXT", "departure_time": "TEXT", "arrival": "TEXT", "departure": "TEXT", "day_offset": "INTEGER", "distance_km": "REAL", "distance": "REAL"})
    train_numbers = sorted({item[0] for item in STOPS})
    placeholders = ",".join(["?"] * len(train_numbers))
    try:
        connection.execute(f"DELETE FROM {table} WHERE train_no IN ({placeholders}) OR train_number IN ({placeholders})", train_numbers + train_numbers)
        rows = []
        for train_no, train_name, station_code, sequence, arrival, departure, day_offset, distance in STOPS:
            name = station_name(station_code)
            rows.append((train_no, train_no, train_name, station_code, name, station_code, name, sequence, sequence, sequence, arrival, departure, arrival, departure, day_offset, distance, distance))
        connection.executemany(f"INSERT INTO {table} (train_no, train_number, train_name, station_code, station_name, code, name, stop_sequence, sequence, stop_number, arrival_time, departure_time, arrival, departure, day_offset, distance_km, distance) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", rows)
    except Exception as error:
        print(f"WARNING: could not seed {table}: {error}")

def prepare_fares(connection) -> None:
    connection.execute("CREATE TABLE IF NOT EXISTS fares (source TEXT, destination TEXT, train_no TEXT, class_code TEXT, fare INTEGER)")
    ensure_columns(connection, "fares", {"source": "TEXT", "destination": "TEXT", "train_no": "TEXT", "class_code": "TEXT", "fare": "INTEGER"})
    rows = [
        ("NDLS", "PNBE", "12301", "SL", 520),
        ("PNBE", "NDLS", "12302", "SL", 540),
        ("PNBE", "NDLS", "12303", "SL", 510),
        ("DSNR", "TPKR", "99901", "SL", 650),
        ("DSNR", "TPKR", "99902", "SL", 610),
    ]
    try:
        connection.execute("DELETE FROM fares WHERE train_no IN (\"12301\", \"12302\", \"12303\", \"99901\", \"99902\")")
        connection.executemany("INSERT INTO fares (source, destination, train_no, class_code, fare) VALUES (?, ?, ?, ?, ?)", rows)
    except Exception as error:
        print(f"WARNING: could not seed fares: {error}")

def prepare_database() -> Path:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as connection:
        prepare_stations(connection, "staging_stations")
        prepare_stations(connection, "stations")
        prepare_trains(connection, "staging_trains")
        prepare_trains(connection, "trains")
        prepare_stops(connection, "staging_train_stops")
        prepare_stops(connection, "train_stops")
        prepare_stops(connection, "stops")
        prepare_fares(connection)
        connection.commit()
    return DB_PATH

def main() -> int:
    path = prepare_database()
    print(f"RailYatra deploy database prepared: {path}")
    with sqlite3.connect(path) as connection:
        for table in ["staging_stations", "staging_trains", "staging_train_stops", "stations", "trains", "train_stops"]:
            count = connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            print(f"{table}: {count}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

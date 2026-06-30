CREATE TABLE IF NOT EXISTS staging_stations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ingestion_run_id INTEGER,
    station_code TEXT NOT NULL,
    station_name TEXT,
    state TEXT,
    latitude REAL,
    longitude REAL,
    source_file TEXT,
    source_row_number INTEGER,
    raw_json TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS staging_trains (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ingestion_run_id INTEGER,
    train_number TEXT NOT NULL,
    train_name TEXT,
    source_station_code TEXT,
    destination_station_code TEXT,
    train_type TEXT,
    source_file TEXT,
    source_row_number INTEGER,
    raw_json TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS staging_train_stops (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ingestion_run_id INTEGER,
    train_number TEXT NOT NULL,
    station_code TEXT NOT NULL,
    stop_sequence INTEGER NOT NULL,
    arrival TEXT,
    departure TEXT,
    distance INTEGER,
    day_offset INTEGER,
    source_file TEXT,
    source_row_number INTEGER,
    raw_json TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_staging_stations_code ON staging_stations (station_code);

CREATE INDEX IF NOT EXISTS idx_staging_trains_number ON staging_trains (train_number);

CREATE INDEX IF NOT EXISTS idx_staging_train_stops_train_number ON staging_train_stops (train_number);

CREATE INDEX IF NOT EXISTS idx_staging_train_stops_station_code ON staging_train_stops (station_code);

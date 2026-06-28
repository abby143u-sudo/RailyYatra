import sqlite3

DB_NAME = "railyatra.db"

def create_schema():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.executescript("""
    DROP TABLE IF EXISTS train_stops;
    DROP TABLE IF EXISTS stops;
    DROP TABLE IF EXISTS trains;
    DROP TABLE IF EXISTS stations;
    DROP TABLE IF EXISTS schedules;
    DROP TABLE IF EXISTS fares;
    DROP TABLE IF EXISTS delays;

    CREATE TABLE trains (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        train_no TEXT UNIQUE NOT NULL,
        train_name TEXT,
        train_type TEXT,
        source_station TEXT,
        destination_station TEXT
    );

    CREATE TABLE stations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        station_code TEXT UNIQUE NOT NULL,
        station_name TEXT,
        city TEXT,
        state TEXT,
        latitude REAL,
        longitude REAL
    );

    CREATE TABLE train_stops (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        train_no TEXT NOT NULL,
        station_code TEXT NOT NULL,
        stop_order INTEGER,
        arrival_time TEXT,
        departure_time TEXT,
        day INTEGER,
        distance_km REAL,
        FOREIGN KEY (train_no) REFERENCES trains(train_no),
        FOREIGN KEY (station_code) REFERENCES stations(station_code)
    );

    CREATE TABLE schedules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        train_no TEXT,
        run_day TEXT,
        FOREIGN KEY (train_no) REFERENCES trains(train_no)
    );

    CREATE TABLE fares (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        train_no TEXT,
        class_type TEXT,
        fare INTEGER,
        FOREIGN KEY (train_no) REFERENCES trains(train_no)
    );

    CREATE TABLE delays (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        train_no TEXT,
        avg_delay_minutes INTEGER,
        FOREIGN KEY (train_no) REFERENCES trains(train_no)
    );

    CREATE INDEX idx_train_stops_train_no ON train_stops(train_no);
    CREATE INDEX idx_train_stops_station_code ON train_stops(station_code);
    CREATE INDEX idx_trains_train_no ON trains(train_no);
    CREATE INDEX idx_stations_station_code ON stations(station_code);
    """)

    conn.commit()
    conn.close()
    print("RailYatra schema v3 created successfully.")

if __name__ == "__main__":
    create_schema()
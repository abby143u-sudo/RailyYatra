import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).resolve().parents[2] / "railyatra.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_official_fare_table():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS official_fares (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            train_no TEXT NOT NULL,
            source TEXT NOT NULL,
            destination TEXT NOT NULL,
            class_code TEXT NOT NULL DEFAULT 'SL',
            fare INTEGER NOT NULL,
            source_type TEXT DEFAULT 'sample',
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(train_no, source, destination, class_code)
        )
    """)

    conn.commit()
    conn.close()


def upsert_official_fare(train_no, source, destination, class_code, fare, source_type="sample"):
    ensure_official_fare_table()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO official_fares (
            train_no, source, destination, class_code, fare, source_type
        )
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(train_no, source, destination, class_code)
        DO UPDATE SET
            fare = excluded.fare,
            source_type = excluded.source_type,
            updated_at = CURRENT_TIMESTAMP
    """, (
        normalize(train_no),
        normalize(source),
        normalize(destination),
        normalize(class_code),
        int(fare),
        source_type,
    ))

    conn.commit()
    conn.close()


def get_official_fare(train_no, source, destination, class_code="SL"):
    ensure_official_fare_table()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT train_no, source, destination, class_code, fare, source_type, updated_at
        FROM official_fares
        WHERE train_no = ?
          AND source = ?
          AND destination = ?
          AND class_code = ?
        LIMIT 1
    """, (
        normalize(train_no),
        normalize(source),
        normalize(destination),
        normalize(class_code),
    ))

    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return dict(row)


def enrich_fare_with_table(item_type, data, fare, source, destination, class_code="SL"):
    fare = dict(fare or {})
    table_match = calculate_table_fare(
        item_type=item_type,
        data=data or {},
        source=source,
        destination=destination,
        class_code=class_code,
    )

    fare["class_code"] = class_code

    if not table_match:
        fare["fare_source"] = "estimate"
        return fare

    table_fare = table_match["table_fare"]
    saving_rate = get_saving_rate(item_type)
    saving = round_to_nearest_10(table_fare * saving_rate)

    fare["algorithm_estimated_fare"] = fare.get("estimated_fare")
    fare["estimated_fare"] = table_fare
    fare["split_saving_estimate"] = saving
    fare["estimated_after_split"] = max(table_fare - saving, 0)
    fare["confidence"] = "high"
    fare["fare_source"] = "fare_table"
    fare["fare_segments"] = table_match["segments"]
    fare["note"] = "Fare matched from local fare table. Verify with official booking source before purchase."

    return fare


def calculate_table_fare(item_type, data, source, destination, class_code):
    if item_type == "direct":
        train_no = data.get("train_no")
        row = get_official_fare(train_no, source, destination, class_code)

        if not row:
            return None

        return {
            "table_fare": int(row["fare"]),
            "segments": [row],
        }

    if item_type == "one_transfer":
        transfer = data.get("transfer_station")

        first = get_official_fare(
            data.get("first_train"),
            source,
            transfer,
            class_code,
        )

        second = get_official_fare(
            data.get("second_train"),
            transfer,
            destination,
            class_code,
        )

        if not first or not second:
            return None

        return {
            "table_fare": int(first["fare"]) + int(second["fare"]),
            "segments": [first, second],
        }

    if item_type == "multi_transfer":
        legs = data.get("train_legs", [])

        if not legs:
            return None

        segments = []
        total = 0

        for leg in legs:
            row = get_official_fare(
                leg.get("train_no"),
                leg.get("from"),
                leg.get("to"),
                class_code,
            )

            if not row:
                return None

            segments.append(row)
            total += int(row["fare"])

        return {
            "table_fare": total,
            "segments": segments,
        }

    return None



def get_saving_rate(item_type):
    if item_type == "direct":
        return 0.08

    if item_type == "one_transfer":
        return 0.12

    if item_type == "multi_transfer":
        return 0.14

    return 0.08


def normalize(value):
    return str(value or "").strip().upper()


def round_to_nearest_10(value):
    return int(round(float(value) / 10.0) * 10)

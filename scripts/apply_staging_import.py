#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = REPO_ROOT / "app" / "railyatra.db"
RAW_DIR = REPO_ROOT / "app" / "data" / "raw"

PLAN_SCRIPT = REPO_ROOT / "scripts" / "plan_staging_import.py"
PRE_IMPORT_GATE = REPO_ROOT / "scripts" / "pre_import_gate.sh"
BACKUP_SCRIPT = REPO_ROOT / "scripts" / "backup_database.py"

RAW_FILES = {
    "stations": RAW_DIR / "stations.json",
    "trains": RAW_DIR / "trains.json",
    "schedules": RAW_DIR / "schedules.json",
}

ALLOWED_STAGING_TABLES = [
    "staging_stations",
    "staging_trains",
    "staging_train_stops",
]

ALLOWED_METADATA_TABLES = [
    "ingestion_runs",
    "ingestion_source_files",
    "ingestion_issues",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_command(label: str, command: list[str]) -> int:
    print("")
    print("========================================")
    print(f"RUNNING: {label}")
    print("========================================")

    result = subprocess.run(command, cwd=REPO_ROOT, text=True)

    if result.returncode != 0:
        print(f"FAIL: {label}")
        return result.returncode

    print(f"PASS: {label}")
    return 0


def verify_required_files() -> int:
    required_files = [
        PLAN_SCRIPT,
        PRE_IMPORT_GATE,
        BACKUP_SCRIPT,
        DB_PATH,
        *RAW_FILES.values(),
    ]

    missing = [path for path in required_files if not path.exists()]

    if missing:
        print("FAIL: required file(s) missing")
        for path in missing:
            print(f"  missing: {path}")
        return 1

    return 0


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def first_value(record: dict[str, Any], keys: tuple[str, ...]) -> str:
    for key in keys:
        value = record.get(key)

        if value is not None and str(value).strip():
            return str(value).strip()

    return ""


def normalize_record(item: Any, role: str, parent_key: str | None = None) -> dict[str, Any]:
    if isinstance(item, dict):
        if "properties" in item and isinstance(item.get("properties"), dict):
            row = dict(item["properties"])

            geometry = item.get("geometry")
            if isinstance(geometry, dict):
                coordinates = geometry.get("coordinates")
                if isinstance(coordinates, list) and len(coordinates) >= 2:
                    row.setdefault("longitude", coordinates[0])
                    row.setdefault("latitude", coordinates[1])

            if parent_key is not None:
                row.setdefault("parent_key", parent_key)

            return row

        row = dict(item)

        if parent_key is not None:
            if role == "stations":
                row.setdefault("code", parent_key)
                row.setdefault("station_code", parent_key)
            elif role == "trains":
                row.setdefault("number", parent_key)
                row.setdefault("train_no", parent_key)
                row.setdefault("train_number", parent_key)
            elif role == "schedules":
                row.setdefault("train_number", parent_key)
                row.setdefault("train_no", parent_key)
            else:
                row.setdefault("parent_key", parent_key)

        return row

    if role == "stations":
        return {"code": parent_key, "station_code": parent_key, "name": item}

    if role == "trains":
        return {"number": parent_key, "train_no": parent_key, "train_number": parent_key, "name": item}

    return {"parent_key": parent_key, "value": item}


def records_from_json(data: Any, role: str) -> list[dict[str, Any]]:
    def records_from_value(value: Any, parent_key: str | None = None) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []

        if isinstance(value, list):
            for item in value:
                records.append(normalize_record(item, role, parent_key))
            return records

        if isinstance(value, dict):
            if "features" in value and isinstance(value.get("features"), list):
                return records_from_value(value["features"], parent_key)

            if "properties" in value and isinstance(value.get("properties"), dict):
                return [normalize_record(value, role, parent_key)]

            for key, child in value.items():
                if key in {"metadata", "meta", "info", "version", "source", "license", "type"}:
                    continue

                if isinstance(child, list):
                    records.extend(records_from_value(child, key))
                elif isinstance(child, dict):
                    if any(
                        field in child
                        for field in (
                            "name",
                            "station_name",
                            "train_name",
                            "code",
                            "station_code",
                            "number",
                            "train_no",
                            "train_number",
                            "properties",
                        )
                    ):
                        records.append(normalize_record(child, role, key))
                    else:
                        records.extend(records_from_value(child, key))
                else:
                    records.append(normalize_record(child, role, key))

            return records

        return [normalize_record(value, role, parent_key)]

    if isinstance(data, dict):
        for key in (
            "features",
            "data",
            "records",
            "items",
            "results",
            "stations",
            "station",
            "trains",
            "train",
            "schedules",
            "schedule",
            "stops",
            "train_stops",
        ):
            value = data.get(key)
            if isinstance(value, (list, dict)):
                records = records_from_value(value)
                return [record for record in records if isinstance(record, dict)]

    records = records_from_value(data)
    return [record for record in records if isinstance(record, dict)]


def station_code(record: dict[str, Any]) -> str:
    return first_value(record, ("station_code", "code", "stn_code", "stationCode", "station")).upper()


def station_name(record: dict[str, Any]) -> str:
    return first_value(record, ("station_name", "name", "stationName"))


def station_state(record: dict[str, Any]) -> str:
    return first_value(record, ("state", "state_name", "stateName"))


def float_or_none(value: Any) -> float | None:
    if value in (None, "", "NA"):
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def int_or_none(value: Any) -> int | None:
    if value in (None, "", "NA"):
        return None

    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def station_latitude(record: dict[str, Any]) -> float | None:
    return float_or_none(record.get("latitude", record.get("lat")))


def station_longitude(record: dict[str, Any]) -> float | None:
    return float_or_none(record.get("longitude", record.get("lon", record.get("lng"))))


def train_number(record: dict[str, Any]) -> str:
    return first_value(record, ("train_number", "train_no", "number", "trainNumber", "train"))


def train_name(record: dict[str, Any]) -> str:
    return first_value(record, ("train_name", "name", "trainName"))


def train_source(record: dict[str, Any]) -> str:
    return first_value(
        record,
        (
            "source_station_code",
            "source",
            "from",
            "from_station_code",
            "origin",
            "origin_station_code",
        ),
    ).upper()


def train_destination(record: dict[str, Any]) -> str:
    return first_value(
        record,
        (
            "destination_station_code",
            "destination",
            "to",
            "to_station_code",
            "dest",
            "destination_station",
        ),
    ).upper()


def train_type(record: dict[str, Any]) -> str:
    return first_value(record, ("train_type", "type", "category"))


def schedule_train_number(record: dict[str, Any]) -> str:
    return first_value(record, ("train_number", "train_no", "number", "trainNumber", "train"))


def schedule_station_code(record: dict[str, Any]) -> str:
    return first_value(record, ("station_code", "code", "station", "stationCode")).upper()


def schedule_sequence(record: dict[str, Any], fallback: int) -> int:
    value = first_value(record, ("stop_sequence", "sequence", "seq", "stop_number", "serial"))

    if value:
        parsed = int_or_none(value)
        if parsed is not None:
            return parsed

    return fallback


def schedule_arrival(record: dict[str, Any]) -> str:
    return first_value(record, ("arrival", "arrival_time", "arrivalTime"))


def schedule_departure(record: dict[str, Any]) -> str:
    return first_value(record, ("departure", "departure_time", "departureTime"))


def schedule_distance(record: dict[str, Any]) -> int | None:
    value = first_value(record, ("distance", "distance_km", "distanceKm"))
    return int_or_none(value)


def schedule_day_offset(record: dict[str, Any]) -> int | None:
    value = first_value(record, ("day_offset", "day", "dayOffset"))
    return int_or_none(value)


def raw_json(record: dict[str, Any]) -> str:
    return json.dumps(record, ensure_ascii=False, sort_keys=True)


def load_raw_records() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    stations = records_from_json(load_json(RAW_FILES["stations"]), "stations")
    trains = records_from_json(load_json(RAW_FILES["trains"]), "trains")
    schedules = records_from_json(load_json(RAW_FILES["schedules"]), "schedules")

    return stations, trains, schedules


def validate_blocking(
    stations: list[dict[str, Any]],
    trains: list[dict[str, Any]],
    schedules: list[dict[str, Any]],
) -> tuple[bool, list[str]]:
    station_codes = {station_code(record) for record in stations if station_code(record)}
    train_numbers = {train_number(record) for record in trains if train_number(record)}

    issues = []

    missing_station_codes = sum(1 for record in stations if not station_code(record))
    missing_train_numbers = sum(1 for record in trains if not train_number(record))
    missing_schedule_train_numbers = sum(1 for record in schedules if not schedule_train_number(record))
    missing_schedule_station_codes = sum(1 for record in schedules if not schedule_station_code(record))

    orphan_schedule_train_numbers = sum(
        1
        for record in schedules
        if schedule_train_number(record) and schedule_train_number(record) not in train_numbers
    )

    orphan_schedule_station_codes = sum(
        1
        for record in schedules
        if schedule_station_code(record) and schedule_station_code(record) not in station_codes
    )

    values = {
        "missing station codes": missing_station_codes,
        "missing train numbers": missing_train_numbers,
        "missing schedule train numbers": missing_schedule_train_numbers,
        "missing schedule station codes": missing_schedule_station_codes,
        "orphan schedule train numbers": orphan_schedule_train_numbers,
        "orphan schedule station codes": orphan_schedule_station_codes,
    }

    for label, count in values.items():
        if count:
            issues.append(f"{label}: {count}")

    return not issues, issues


def insert_ingestion_run(conn: sqlite3.Connection) -> int:
    columns = [row[1] for row in conn.execute("PRAGMA table_info(ingestion_runs)").fetchall()]
    values = {
        "started_at": utc_now(),
        "completed_at": utc_now(),
        "mode": "staging-apply",
        "run_type": "staging-apply",
        "status": "completed",
        "notes": "Staging-only railway data import. Production railway tables untouched.",
        "records_seen": 0,
        "records_accepted": 0,
        "records_rejected": 0,
    }

    writable = [column for column in columns if column in values]

    if not writable:
        return 0

    placeholders = ", ".join("?" for _ in writable)
    column_sql = ", ".join(writable)
    row_values = [values[column] for column in writable]

    cursor = conn.execute(
        f"INSERT INTO ingestion_runs ({column_sql}) VALUES ({placeholders})",
        row_values,
    )

    return int(cursor.lastrowid)


def table_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    return {row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}


def insert_row(conn: sqlite3.Connection, table: str, values: dict[str, Any]) -> None:
    columns = table_columns(conn, table)
    writable = [column for column in values if column in columns]

    if not writable:
        raise RuntimeError(f"No writable columns found for {table}")

    placeholders = ", ".join("?" for _ in writable)
    column_sql = ", ".join(writable)
    row_values = [values[column] for column in writable]

    conn.execute(
        f"INSERT INTO {table} ({column_sql}) VALUES ({placeholders})",
        row_values,
    )


def apply_staging_rows(
    conn: sqlite3.Connection,
    run_id: int,
    stations: list[dict[str, Any]],
    trains: list[dict[str, Any]],
    schedules: list[dict[str, Any]],
) -> None:
    conn.execute("DELETE FROM staging_train_stops")
    conn.execute("DELETE FROM staging_trains")
    conn.execute("DELETE FROM staging_stations")

    now = utc_now()

    for index, record in enumerate(stations, start=1):
        insert_row(
            conn,
            "staging_stations",
            {
                "ingestion_run_id": run_id,
                "station_code": station_code(record),
                "station_name": station_name(record),
                "state": station_state(record),
                "latitude": station_latitude(record),
                "longitude": station_longitude(record),
                "source_file": "stations.json",
                "source_row_number": index,
                "raw_json": raw_json(record),
                "created_at": now,
            },
        )

    for index, record in enumerate(trains, start=1):
        insert_row(
            conn,
            "staging_trains",
            {
                "ingestion_run_id": run_id,
                "train_number": train_number(record),
                "train_name": train_name(record),
                "source_station_code": train_source(record),
                "destination_station_code": train_destination(record),
                "train_type": train_type(record),
                "source_file": "trains.json",
                "source_row_number": index,
                "raw_json": raw_json(record),
                "created_at": now,
            },
        )

    train_stop_sequence: dict[str, int] = {}

    for index, record in enumerate(schedules, start=1):
        number = schedule_train_number(record)
        train_stop_sequence[number] = train_stop_sequence.get(number, 0) + 1

        insert_row(
            conn,
            "staging_train_stops",
            {
                "ingestion_run_id": run_id,
                "train_number": number,
                "station_code": schedule_station_code(record),
                "stop_sequence": schedule_sequence(record, train_stop_sequence[number]),
                "arrival": schedule_arrival(record),
                "departure": schedule_departure(record),
                "distance": schedule_distance(record),
                "day_offset": schedule_day_offset(record),
                "source_file": "schedules.json",
                "source_row_number": index,
                "raw_json": raw_json(record),
                "created_at": now,
            },
        )


def validate_staging_counts(
    conn: sqlite3.Connection,
    station_expected: int,
    train_expected: int,
    schedule_expected: int,
) -> tuple[bool, list[str]]:
    values = {
        "staging_stations": station_expected,
        "staging_trains": train_expected,
        "staging_train_stops": schedule_expected,
    }

    errors = []

    for table, expected in values.items():
        actual = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]

        if actual != expected:
            errors.append(f"{table} expected {expected}, got {actual}")

    return not errors, errors


def print_scope() -> None:
    print("Allowed staging tables:")
    for table in ALLOWED_STAGING_TABLES:
        print(f"  {table}")

    print("Allowed metadata tables:")
    for table in ALLOWED_METADATA_TABLES:
        print(f"  {table}")

    print("Forbidden:")
    print("  production railway tables")
    print("  fare tables")
    print("  graph/search result tables")


def dry_run() -> int:
    print("RailYatra staging apply")
    print("Mode: dry-run")
    print(f"Database: {DB_PATH}")
    print("Database opened: no")
    print("Database write skipped: yes")
    print("Railway production tables modified: no")

    file_check = verify_required_files()

    if file_check != 0:
        return file_check

    print_scope()

    planner_code = run_command(
        "Staging import planner dry-run",
        [sys.executable, str(PLAN_SCRIPT), "--dry-run"],
    )

    if planner_code != 0:
        return planner_code

    print("Apply mode status: enabled only with --apply --confirm-staging-write")
    print("PASS: staging apply dry-run completed")
    return 0


def apply(confirm: bool) -> int:
    print("RailYatra staging apply")
    print("Mode: apply")

    if not confirm:
        print("APPLY CONFIRMATION MISSING")
        print("Database opened: no")
        print("Database write skipped: yes")
        print("Railway production tables modified: no")
        print("Required command:")
        print("  python3 scripts/apply_staging_import.py --apply --confirm-staging-write")
        print("FAIL: apply requires explicit --confirm-staging-write")
        return 2

    file_check = verify_required_files()

    if file_check != 0:
        return file_check

    gate_code = run_command("Pre-import safety gate", [str(PRE_IMPORT_GATE)])

    if gate_code != 0:
        return gate_code

    backup_code = run_command("Database backup", [sys.executable, str(BACKUP_SCRIPT)])

    if backup_code != 0:
        return backup_code

    stations, trains, schedules = load_raw_records()
    ok, blocking_issues = validate_blocking(stations, trains, schedules)

    if not ok:
        print("FAIL: blocking validation failed before database write")
        for issue in blocking_issues:
            print(f"  {issue}")
        return 1

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("BEGIN")

        try:
            run_id = insert_ingestion_run(conn)
            apply_staging_rows(conn, run_id, stations, trains, schedules)

            counts_ok, count_errors = validate_staging_counts(
                conn,
                len(stations),
                len(trains),
                len(schedules),
            )

            if not counts_ok:
                for error in count_errors:
                    print(f"FAIL: {error}")
                conn.rollback()
                return 1

            conn.commit()

        except Exception as error:
            conn.rollback()
            print(f"FAIL: staging apply rolled back: {error}")
            return 1

    print("Database opened: yes")
    print("Database write completed: staging tables only")
    print("Railway production tables modified: no")
    print(f"Inserted staging_stations: {len(stations)}")
    print(f"Inserted staging_trains: {len(trains)}")
    print(f"Inserted staging_train_stops: {len(schedules)}")
    print("PASS: staging apply completed")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Safely apply raw railway data into staging tables only."
    )
    parser.add_argument("--dry-run", action="store_true", help="Plan staging apply without database writes.")
    parser.add_argument("--apply", action="store_true", help="Apply staging-only writes.")
    parser.add_argument("--confirm-staging-write", action="store_true", help="Required with --apply to confirm staging-only database write.")

    args = parser.parse_args()

    if args.dry_run and args.apply:
        print("FAIL: choose either --dry-run or --apply, not both")
        return 2

    if args.apply:
        return apply(args.confirm_staging_write)

    return dry_run()


if __name__ == "__main__":
    raise SystemExit(main())

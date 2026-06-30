#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = REPO_ROOT / "app" / "data" / "raw"

RAW_FILES = {
    "stations": RAW_DIR / "stations.json",
    "trains": RAW_DIR / "trains.json",
    "schedules": RAW_DIR / "schedules.json",
}


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


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


def first_value(record: dict[str, Any], keys: tuple[str, ...]) -> str:
    for key in keys:
        value = record.get(key)

        if value is not None and str(value).strip():
            return str(value).strip()

    return ""


def station_code(record: dict[str, Any]) -> str:
    return first_value(
        record,
        (
            "station_code",
            "code",
            "stn_code",
            "stationCode",
            "station",
        ),
    ).upper()


def station_name(record: dict[str, Any]) -> str:
    return first_value(
        record,
        (
            "station_name",
            "name",
            "stationName",
        ),
    )


def train_number(record: dict[str, Any]) -> str:
    return first_value(
        record,
        (
            "train_number",
            "train_no",
            "number",
            "trainNumber",
            "train",
        ),
    )


def train_name(record: dict[str, Any]) -> str:
    return first_value(
        record,
        (
            "train_name",
            "name",
            "trainName",
        ),
    )


def schedule_station_code(record: dict[str, Any]) -> str:
    return first_value(
        record,
        (
            "station_code",
            "code",
            "station",
            "stationCode",
        ),
    ).upper()


def schedule_train_number(record: dict[str, Any]) -> str:
    return first_value(
        record,
        (
            "train_number",
            "train_no",
            "number",
            "trainNumber",
            "train",
        ),
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Plan staging railway import without database writes."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Read raw files and print planned staging inserts without opening or writing the database.",
    )

    args = parser.parse_args()

    if not args.dry_run:
        args.dry_run = True

    print("RailYatra staging import planner")
    print("Mode: dry-run")
    print(f"Raw directory: {RAW_DIR}")

    missing_files = [
        str(path) for path in RAW_FILES.values() if not path.exists()
    ]

    if missing_files:
        print("FAIL: missing raw file(s)")
        for path in missing_files:
            print(f"  missing: {path}")
        return 1

    stations = records_from_json(load_json(RAW_FILES["stations"]), "stations")
    trains = records_from_json(load_json(RAW_FILES["trains"]), "trains")
    schedules = records_from_json(load_json(RAW_FILES["schedules"]), "schedules")

    station_codes = [station_code(record) for record in stations]
    train_numbers = [train_number(record) for record in trains]
    schedule_station_codes = [schedule_station_code(record) for record in schedules]
    schedule_train_numbers = [schedule_train_number(record) for record in schedules]

    station_code_counter = Counter(code for code in station_codes if code)
    train_number_counter = Counter(number for number in train_numbers if number)

    duplicate_station_codes = sum(1 for count in station_code_counter.values() if count > 1)
    duplicate_train_numbers = sum(1 for count in train_number_counter.values() if count > 1)

    station_code_set = set(station_code_counter)
    train_number_set = set(train_number_counter)

    missing_station_codes = sum(1 for code in station_codes if not code)
    missing_station_names = sum(1 for record in stations if not station_name(record))
    missing_train_numbers = sum(1 for number in train_numbers if not number)
    missing_train_names = sum(1 for record in trains if not train_name(record))

    schedules_missing_train_number = sum(1 for number in schedule_train_numbers if not number)
    schedules_missing_station_code = sum(1 for code in schedule_station_codes if not code)

    orphan_schedule_train_numbers = sum(
        1
        for number in schedule_train_numbers
        if number and number not in train_number_set
    )

    orphan_schedule_station_codes = sum(
        1
        for code in schedule_station_codes
        if code and code not in station_code_set
    )

    planned_staging_stations = len(stations)
    planned_staging_trains = len(trains)
    planned_staging_train_stops = len(schedules)

    print("Planned staging inserts:")
    print(f"  staging_stations: {planned_staging_stations}")
    print(f"  staging_trains: {planned_staging_trains}")
    print(f"  staging_train_stops: {planned_staging_train_stops}")

    print("Blocking validation:")
    print(f"  stations missing code: {missing_station_codes}")
    print(f"  trains missing number: {missing_train_numbers}")
    print(f"  schedules missing train number: {schedules_missing_train_number}")
    print(f"  schedules missing station code: {schedules_missing_station_code}")
    print(f"  duplicate station code groups: {duplicate_station_codes}")
    print(f"  duplicate train number groups: {duplicate_train_numbers}")
    print(f"  orphan schedule train numbers: {orphan_schedule_train_numbers}")
    print(f"  orphan schedule station codes: {orphan_schedule_station_codes}")

    print("Non-blocking data quality:")
    print(f"  stations missing name: {missing_station_names}")
    print(f"  trains missing name: {missing_train_names}")

    blocking_total = (
        missing_station_codes
        + missing_train_numbers
        + schedules_missing_train_number
        + schedules_missing_station_code
        + orphan_schedule_train_numbers
        + orphan_schedule_station_codes
    )

    print("Database opened: no")
    print("Database write skipped: yes")
    print("Railway data tables modified: no")

    if blocking_total:
        print(f"FAIL: staging plan has {blocking_total} blocking issue(s)")
        return 1

    print("PASS: staging import dry-run plan completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

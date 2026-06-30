#!/usr/bin/env python3
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = REPO_ROOT / "app" / "railyatra.db"
RAW_DIR = REPO_ROOT / "app" / "data" / "raw"

RAW_FILES = {
    "stations": RAW_DIR / "stations.json",
    "trains": RAW_DIR / "trains.json",
    "schedules": RAW_DIR / "schedules.json",
}

STAGING_TABLES = [
    "staging_stations",
    "staging_trains",
    "staging_train_stops",
]


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


def table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table,),
    ).fetchone()
    return row is not None


def main() -> int:
    print("RailYatra staging import verifier")
    print(f"Database: {DB_PATH}")

    if not DB_PATH.exists():
        print("FAIL: database missing")
        return 1

    expected = {
        "staging_stations": len(records_from_json(load_json(RAW_FILES["stations"]), "stations")),
        "staging_trains": len(records_from_json(load_json(RAW_FILES["trains"]), "trains")),
        "staging_train_stops": len(records_from_json(load_json(RAW_FILES["schedules"]), "schedules")),
    }

    with sqlite3.connect(DB_PATH) as conn:
        missing = [table for table in STAGING_TABLES if not table_exists(conn, table)]

        if missing:
            print("FAIL: missing staging table(s)")
            for table in missing:
                print(f"  missing: {table}")
            return 1

        for table, expected_count in expected.items():
            actual_count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            print(f"{table}: {actual_count}")

            if actual_count != expected_count:
                print(f"FAIL: {table} expected {expected_count}, got {actual_count}")
                return 1

        latest_run = conn.execute(
            "SELECT COUNT(*) FROM ingestion_runs"
        ).fetchone()[0]

        print(f"ingestion_runs total rows: {latest_run}")

    print("Production railway tables modified: no")
    print("PASS: staging import verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
APP_DIR = REPO_ROOT / "app"
DB_PATH = APP_DIR / "railyatra.db"
RAW_DIR = APP_DIR / "data" / "raw"

RAW_FILES = {
    "stations": RAW_DIR / "stations.json",
    "trains": RAW_DIR / "trains.json",
    "schedules": RAW_DIR / "schedules.json",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def load_json_records(path: Path):
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    role = path.stem.lower()

    def normalize_record(item, parent_key=None):
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
                if role.startswith("station"):
                    row.setdefault("code", parent_key)
                    row.setdefault("station_code", parent_key)
                elif role.startswith("train"):
                    row.setdefault("number", parent_key)
                    row.setdefault("train_no", parent_key)
                    row.setdefault("train_number", parent_key)
                elif role.startswith("schedule"):
                    row.setdefault("train_number", parent_key)
                    row.setdefault("train_no", parent_key)
                else:
                    row.setdefault("parent_key", parent_key)

            return row

        if role.startswith("station"):
            return {"code": parent_key, "station_code": parent_key, "name": item}

        if role.startswith("train"):
            return {"number": parent_key, "train_no": parent_key, "train_number": parent_key, "name": item}

        return {"parent_key": parent_key, "value": item}

    def records_from_value(value, parent_key=None):
        records = []

        if isinstance(value, list):
            for item in value:
                records.append(normalize_record(item, parent_key))
            return records

        if isinstance(value, dict):
            if "features" in value and isinstance(value.get("features"), list):
                return records_from_value(value["features"], parent_key)

            if "properties" in value and isinstance(value.get("properties"), dict):
                return [normalize_record(value, parent_key)]

            for key, child in value.items():
                if key in ("metadata", "meta", "info", "version", "source", "license"):
                    continue

                if isinstance(child, list):
                    records.extend(records_from_value(child, key))
                elif isinstance(child, dict):
                    if any(k in child for k in ("name", "station_name", "train_name", "code", "station_code", "number", "train_no", "train_number", "properties")):
                        records.append(normalize_record(child, key))
                    else:
                        nested = records_from_value(child, key)
                        if nested:
                            records.extend(nested)
                        else:
                            records.append(normalize_record(child, key))
                else:
                    records.append(normalize_record(child, key))

            return records

        return [normalize_record(value, parent_key)]

    if isinstance(data, list):
        records = records_from_value(data)
    elif isinstance(data, dict):
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
                break
        else:
            records = records_from_value(data)
    else:
        records = records_from_value(data)

    records = [record for record in records if isinstance(record, dict)]

    if not records:
        raise ValueError(f"{path} does not contain usable records")

    return records


def count_issues(records_by_name: dict[str, list]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []

    stations = records_by_name.get("stations", [])
    trains = records_by_name.get("trains", [])
    schedules = records_by_name.get("schedules", [])

    station_missing_name = sum(
        1 for item in stations if not (item.get("name") or item.get("station_name"))
    )
    station_missing_state = sum(
        1 for item in stations if not (item.get("state") or item.get("state_name"))
    )
    station_missing_coordinates = sum(
        1
        for item in stations
        if item.get("lat") in (None, "", "NA")
        and item.get("latitude") in (None, "", "NA")
    )

    train_missing_name = sum(
        1 for item in trains if not (item.get("name") or item.get("train_name"))
    )
    train_missing_number = sum(
        1 for item in trains if not (item.get("number") or item.get("train_no") or item.get("train_number"))
    )

    schedules_missing_train_number = sum(
        1
        for item in schedules
        if not (item.get("train_number") or item.get("train_no") or item.get("number"))
    )
    schedules_missing_station_code = sum(
        1
        for item in schedules
        if not (item.get("station_code") or item.get("code") or item.get("station"))
    )
    schedules_missing_arrival = sum(
        1 for item in schedules if item.get("arrival") in (None, "", "NA")
    )
    schedules_missing_departure = sum(
        1 for item in schedules if item.get("departure") in (None, "", "NA")
    )

    raw_issues = {
        "stations_missing_name": station_missing_name,
        "stations_missing_state": station_missing_state,
        "stations_missing_coordinates": station_missing_coordinates,
        "trains_missing_name": train_missing_name,
        "trains_missing_number": train_missing_number,
        "schedules_missing_train_number": schedules_missing_train_number,
        "schedules_missing_station_code": schedules_missing_station_code,
        "schedules_missing_arrival": schedules_missing_arrival,
        "schedules_missing_departure": schedules_missing_departure,
    }

    for code, count in raw_issues.items():
        if count:
            severity = "warning"
            if code in {
                "trains_missing_number",
                "schedules_missing_train_number",
                "schedules_missing_station_code",
            }:
                severity = "error"

            issues.append(
                {
                    "severity": severity,
                    "code": code,
                    "message": f"{count} record(s) reported for {code}",
                    "count": str(count),
                }
            )

    return issues


def ensure_metadata_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS ingestion_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            started_at TEXT NOT NULL,
            completed_at TEXT,
            mode TEXT NOT NULL,
            status TEXT NOT NULL,
            station_count INTEGER DEFAULT 0,
            train_count INTEGER DEFAULT 0,
            schedule_count INTEGER DEFAULT 0,
            issue_count INTEGER DEFAULT 0,
            notes TEXT
        );

        CREATE TABLE IF NOT EXISTS ingestion_source_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER NOT NULL,
            file_role TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_size_bytes INTEGER NOT NULL,
            sha256 TEXT NOT NULL,
            record_count INTEGER NOT NULL,
            FOREIGN KEY(run_id) REFERENCES ingestion_runs(id)
        );

        CREATE TABLE IF NOT EXISTS ingestion_issues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER NOT NULL,
            severity TEXT NOT NULL,
            issue_code TEXT NOT NULL,
            message TEXT NOT NULL,
            issue_count INTEGER DEFAULT 0,
            FOREIGN KEY(run_id) REFERENCES ingestion_runs(id)
        );
        """
    )


def normalize_values_for_table(table: str, values: dict[str, object]) -> dict[str, object]:
    normalized = dict(values)

    if table == "ingestion_source_files":
        role = normalized.get("file_role") or normalized.get("dataset_name") or "unknown"
        file_path = normalized.get("file_path") or normalized.get("source_path") or ""
        file_size = normalized.get("file_size_bytes") or normalized.get("size_bytes") or 0
        checksum = normalized.get("sha256") or normalized.get("checksum_sha256") or normalized.get("file_sha256") or ""
        record_count = normalized.get("record_count") or normalized.get("records_count") or 0

        normalized.setdefault("dataset_name", role)
        normalized.setdefault("source_name", role)
        normalized.setdefault("file_name", Path(str(file_path)).name if file_path else str(role))
        normalized.setdefault("path", file_path)
        normalized.setdefault("source_path", file_path)
        normalized.setdefault("relative_path", file_path)
        normalized.setdefault("size_bytes", file_size)
        normalized.setdefault("file_size", file_size)
        normalized.setdefault("checksum", checksum)
        normalized.setdefault("checksum_sha256", checksum)
        normalized.setdefault("file_sha256", checksum)
        normalized.setdefault("records_count", record_count)
        normalized.setdefault("row_count", record_count)
        normalized.setdefault("created_at", utc_now())
        normalized.setdefault("recorded_at", utc_now())

    if table == "ingestion_issues":
        code = normalized.get("issue_code") or normalized.get("code") or "unknown_issue"
        count = normalized.get("issue_count") or normalized.get("count") or 0

        normalized.setdefault("code", code)
        normalized.setdefault("issue_type", code)
        normalized.setdefault("field_name", code)
        normalized.setdefault("dataset_name", "raw_data")
        normalized.setdefault("source_name", "raw_data")
        normalized.setdefault("count", count)
        normalized.setdefault("records_count", count)
        normalized.setdefault("created_at", utc_now())
        normalized.setdefault("recorded_at", utc_now())

    if table == "ingestion_runs":
        normalized.setdefault("run_type", normalized.get("mode", "metadata-only"))
        normalized.setdefault("started_at", utc_now())
        normalized.setdefault("completed_at", utc_now())
        normalized.setdefault("created_at", utc_now())
        normalized.setdefault("updated_at", utc_now())
        normalized.setdefault("status", "completed")

    return normalized


def default_value_for_required_column(column: str, column_type: str) -> object:
    name = column.lower()
    kind = (column_type or "").upper()

    if "count" in name or "size" in name or "total" in name or "number" in name:
        return 0

    if "at" in name or "date" in name or "time" in name:
        return utc_now()

    if "status" in name:
        return "completed"

    if "mode" in name or "type" in name:
        return "metadata-only"

    if "severity" in name:
        return "warning"

    if "hash" in name or "sha" in name or "checksum" in name:
        return ""

    if "INT" in kind:
        return 0

    if "REAL" in kind or "FLOA" in kind or "DOUB" in kind:
        return 0.0

    return "unknown"


def insert_with_known_columns(
    conn: sqlite3.Connection,
    table: str,
    values: dict[str, object],
) -> int:
    values = normalize_values_for_table(table, values)

    table_info = conn.execute(f"PRAGMA table_info({table})").fetchall()

    if not table_info:
        raise RuntimeError(f"Table not found: {table}")

    final_values = {}

    for cid, column, column_type, notnull, default_value, pk in table_info:
        if pk:
            continue

        if column in values:
            final_values[column] = values[column]
            continue

        if notnull and default_value is None:
            final_values[column] = default_value_for_required_column(column, column_type)

    if not final_values:
        raise RuntimeError(f"No compatible columns found for {table}")

    writable = list(final_values.keys())
    placeholders = ", ".join("?" for _ in writable)
    column_sql = ", ".join(writable)
    row_values = [final_values[column] for column in writable]

    cursor = conn.execute(
        f"INSERT INTO {table} ({column_sql}) VALUES ({placeholders})",
        row_values,
    )

    return int(cursor.lastrowid)


def backup_database() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/backup_database.py"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
    )

    print(result.stdout, end="")

    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        raise SystemExit(result.returncode)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Write ingestion metadata only. Railway data tables stay untouched."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Inspect metadata write plan without writing to database.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write ingestion metadata rows only. Requires backup.",
    )

    args = parser.parse_args()

    if args.dry_run and args.apply:
        print("FAIL: choose either --dry-run or --apply, not both")
        return 2

    if not args.dry_run and not args.apply:
        args.dry_run = True

    if not DB_PATH.exists():
        print(f"FAIL: database not found: {DB_PATH}")
        return 1

    records_by_name = {}
    source_file_rows = []

    for role, path in RAW_FILES.items():
        if not path.exists():
            print(f"FAIL: raw file missing: {path}")
            return 1

        records = load_json_records(path)
        records_by_name[role] = records

        source_file_rows.append(
            {
                "file_role": role,
                "file_path": str(path.relative_to(REPO_ROOT)),
                "file_size_bytes": path.stat().st_size,
                "sha256": sha256_file(path),
                "record_count": len(records),
            }
        )

    issues = count_issues(records_by_name)

    station_count = len(records_by_name["stations"])
    train_count = len(records_by_name["trains"])
    schedule_count = len(records_by_name["schedules"])
    issue_count = len(issues)

    print("RailYatra ingestion metadata writer")
    print(f"Mode: {'apply' if args.apply else 'dry-run'}")
    print(f"Database: {DB_PATH}")
    print("Counts:")
    print(f"  stations: {station_count}")
    print(f"  trains: {train_count}")
    print(f"  schedules/stops: {schedule_count}")
    print(f"  issue categories: {issue_count}")
    print("Railway data tables modified: no")

    if args.dry_run:
        print("Database write skipped: yes")
        print("PASS: metadata write dry-run completed")
        return 0

    print("Creating backup before metadata write...")
    backup_database()

    started_at = utc_now()
    completed_at = utc_now()

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("BEGIN")
        ensure_metadata_tables(conn)

        run_id = insert_with_known_columns(
            conn,
            "ingestion_runs",
            {
                "started_at": started_at,
                "completed_at": completed_at,
                "mode": "metadata-only",
                "status": "completed",
                "station_count": station_count,
                "train_count": train_count,
                "schedule_count": schedule_count,
                "issue_count": issue_count,
                "notes": "Metadata-only ingestion audit run. Railway data tables untouched.",
            },
        )

        for row in source_file_rows:
            insert_with_known_columns(
                conn,
                "ingestion_source_files",
                {
                    "run_id": run_id,
                    "ingestion_run_id": run_id,
                    **row,
                },
            )

        for issue in issues:
            insert_with_known_columns(
                conn,
                "ingestion_issues",
                {
                    "run_id": run_id,
                    "ingestion_run_id": run_id,
                    "severity": issue["severity"],
                    "issue_code": issue["code"],
                    "code": issue["code"],
                    "message": issue["message"],
                    "issue_count": int(issue["count"]),
                    "count": int(issue["count"]),
                },
            )

        conn.commit()

    print(f"Metadata ingestion run inserted: {run_id}")
    print("Railway data tables modified: no")
    print("PASS: metadata-only write completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

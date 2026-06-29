from __future__ import annotations

import json
from pathlib import Path
from typing import Any


APP_DIR = Path(__file__).resolve().parents[2]
DEFAULT_RAW_DIR = APP_DIR / "data" / "raw"


class IngestionInspectionError(RuntimeError):
    pass


def inspect_raw_railway_data(raw_dir: str | Path | None = None) -> dict[str, Any]:
    source_dir = Path(raw_dir).expanduser().resolve() if raw_dir else DEFAULT_RAW_DIR

    stations = _load_items(source_dir / "stations.json", "stations")
    station_issues = _inspect_stations(stations)
    station_count = len(stations)
    del stations

    trains = _load_items(source_dir / "trains.json", "trains")
    train_issues = _inspect_trains(trains)
    train_count = len(trains)
    del trains

    schedules = _load_items(source_dir / "schedules.json", "schedules")
    schedule_issues = _inspect_schedules(schedules)
    schedule_count = len(schedules)
    del schedules

    counts = {
        "stations": station_count,
        "trains": train_count,
        "schedules_or_stops": schedule_count,
    }

    empty_files = [name for name, count in counts.items() if count == 0]
    if empty_files:
        raise IngestionInspectionError(
            f"Required raw datasets contain no records: {', '.join(empty_files)}"
        )

    return {
        "mode": "dry-run",
        "raw_dir": str(source_dir),
        "counts": counts,
        "issues": {
            **station_issues,
            **train_issues,
            **schedule_issues,
        },
    }


def format_inspection_report(report: dict[str, Any]) -> str:
    counts = report["counts"]
    issues = report["issues"]

    lines = [
        "RailYatra railway data inspection (dry-run)",
        f"Raw directory: {report['raw_dir']}",
        "Counts:",
        f"  stations: {counts['stations']}",
        f"  trains: {counts['trains']}",
        f"  schedules/stops: {counts['schedules_or_stops']}",
        "Issues:",
    ]

    for name, count in issues.items():
        lines.append(f"  {name}: {count}")

    return "\n".join(lines)


def _load_items(path: Path, dataset_name: str) -> list[Any]:
    if not path.is_file():
        raise IngestionInspectionError(f"Missing required raw file: {path}")

    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError as exc:
        raise IngestionInspectionError(
            f"Invalid JSON in {path}: line {exc.lineno}, column {exc.colno}"
        ) from exc
    except OSError as exc:
        raise IngestionInspectionError(f"Could not read {path}: {exc}") from exc

    if isinstance(data, list):
        return data

    if isinstance(data, dict) and isinstance(data.get("features"), list):
        return data["features"]

    raise IngestionInspectionError(
        f"Unsupported {dataset_name} JSON structure in {path}; expected an array "
        "or a GeoJSON object containing a features array"
    )


def _inspect_stations(items: list[Any]) -> dict[str, int]:
    issues = {
        "stations_missing_code": 0,
        "stations_missing_name": 0,
        "stations_missing_state": 0,
        "stations_missing_coordinates": 0,
    }

    for item in items:
        properties = _properties(item)

        if _is_blank(properties.get("code") or properties.get("station_code")):
            issues["stations_missing_code"] += 1
        if _is_blank(properties.get("name") or properties.get("station_name")):
            issues["stations_missing_name"] += 1
        if _is_blank(properties.get("state")):
            issues["stations_missing_state"] += 1
        if not _has_coordinates(item):
            issues["stations_missing_coordinates"] += 1

    return issues


def _inspect_trains(items: list[Any]) -> dict[str, int]:
    issues = {
        "trains_missing_number": 0,
        "trains_missing_name": 0,
        "trains_missing_source": 0,
        "trains_missing_destination": 0,
    }

    for item in items:
        properties = _properties(item)

        if _is_blank(
            properties.get("number")
            or properties.get("train_number")
            or properties.get("train_no")
        ):
            issues["trains_missing_number"] += 1
        if _is_blank(properties.get("name") or properties.get("train_name")):
            issues["trains_missing_name"] += 1
        if _is_blank(
            properties.get("from_station_code")
            or properties.get("source_station")
            or properties.get("source")
        ):
            issues["trains_missing_source"] += 1
        if _is_blank(
            properties.get("to_station_code")
            or properties.get("destination_station")
            or properties.get("destination")
        ):
            issues["trains_missing_destination"] += 1

    return issues


def _inspect_schedules(items: list[Any]) -> dict[str, int]:
    issues = {
        "schedules_missing_train_number": 0,
        "schedules_missing_station_code": 0,
        "schedules_missing_arrival": 0,
        "schedules_missing_departure": 0,
    }

    for item in items:
        properties = _properties(item)

        if _is_blank(
            properties.get("train_number")
            or properties.get("train_no")
            or properties.get("number")
        ):
            issues["schedules_missing_train_number"] += 1
        if _is_blank(properties.get("station_code") or properties.get("code")):
            issues["schedules_missing_station_code"] += 1
        if _is_blank(properties.get("arrival")):
            issues["schedules_missing_arrival"] += 1
        if _is_blank(properties.get("departure")):
            issues["schedules_missing_departure"] += 1

    return issues


def _properties(item: Any) -> dict[str, Any]:
    if not isinstance(item, dict):
        return {}

    properties = item.get("properties")
    return properties if isinstance(properties, dict) else item


def _has_coordinates(item: Any) -> bool:
    if not isinstance(item, dict):
        return False

    geometry = item.get("geometry")
    if not isinstance(geometry, dict):
        return False

    coordinates = geometry.get("coordinates")
    if not isinstance(coordinates, list) or len(coordinates) < 2:
        return False

    longitude, latitude = coordinates[:2]
    return isinstance(longitude, (int, float)) and isinstance(latitude, (int, float))


def _is_blank(value: Any) -> bool:
    return value is None or str(value).strip().lower() in {"", "none", "null"}

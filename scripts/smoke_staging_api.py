#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

from fastapi.testclient import TestClient


REPO_ROOT = Path(__file__).resolve().parents[1]
APP_DIR = REPO_ROOT / "app"
sys.path.insert(0, str(APP_DIR))


def main() -> int:
    from backend.api.main import app
    from backend.staging.queries import get_graph_edge_preview

    print("RailYatra staging API smoke test")
    print("Mode: read-only")

    client = TestClient(app)

    health_response = client.get("/staging/health")
    print(f"GET /staging/health -> {health_response.status_code}")

    if health_response.status_code != 200:
        print(health_response.text)
        print("FAIL: /staging/health did not return 200")
        return 1

    health = health_response.json()
    print(f"staging status: {health.get('status')}")
    print(f"staging counts: {health.get('counts')}")

    if health.get("database_write_skipped") is not True:
        print("FAIL: /staging/health did not report database_write_skipped true")
        return 1

    if health.get("production_railway_tables_modified") is not False:
        print("FAIL: /staging/health did not report production tables protected")
        return 1

    stations_response = client.get("/staging/stations", params={"q": "PATNA", "limit": 5})
    print(f"GET /staging/stations?q=PATNA -> {stations_response.status_code}")

    if stations_response.status_code != 200:
        print(stations_response.text)
        print("FAIL: /staging/stations did not return 200")
        return 1

    stations = stations_response.json()
    print(f"station result count: {stations.get('count')}")

    if stations.get("count", 0) < 1:
        print("FAIL: /staging/stations returned no PATNA results")
        return 1

    if stations.get("database_write_skipped") is not True:
        print("FAIL: /staging/stations did not report database_write_skipped true")
        return 1

    edges = get_graph_edge_preview(limit=1)

    if not edges:
        print("FAIL: no staging graph edge sample available")
        return 1

    source = edges[0]["from_station_code"]
    destination = edges[0]["to_station_code"]
    train_number = str(edges[0]["train_number"])

    direct_response = client.get(
        "/staging/direct",
        params={
            "source": source,
            "destination": destination,
            "limit": 5,
        },
    )

    print(f"GET /staging/direct?source={source}&destination={destination} -> {direct_response.status_code}")

    if direct_response.status_code != 200:
        print(direct_response.text)
        print("FAIL: /staging/direct did not return 200")
        return 1

    direct = direct_response.json()
    print(f"direct source: {direct.get('source')}")
    print(f"direct destination: {direct.get('destination')}")
    print(f"direct count: {direct.get('count')}")

    if direct.get("count", 0) < 1:
        print("FAIL: /staging/direct returned no routes for sample edge")
        return 1

    if direct.get("database_write_skipped") is not True:
        print("FAIL: /staging/direct did not report database_write_skipped true")
        return 1

    train_stops_response = client.get(
        f"/staging/trains/{train_number}/stops",
        params={"limit": 20},
    )

    print(f"GET /staging/trains/{train_number}/stops -> {train_stops_response.status_code}")

    if train_stops_response.status_code != 200:
        print(train_stops_response.text)
        print("FAIL: /staging/trains/{train_number}/stops did not return 200")
        return 1

    train_stops = train_stops_response.json()
    print(f"train found: {train_stops.get('train_found')}")
    print(f"train stop count: {train_stops.get('count')}")

    if train_stops.get("train_found") is not True:
        print("FAIL: train should be found in staging_trains")
        return 1

    if train_stops.get("count", 0) < 2:
        print("FAIL: train stops should return at least 2 rows")
        return 1

    if train_stops.get("database_write_skipped") is not True:
        print("FAIL: train stops endpoint did not report database_write_skipped true")
        return 1

    if train_stops.get("production_railway_tables_modified") is not False:
        print("FAIL: train stops endpoint did not report production tables protected")
        return 1

    print("Database write skipped: yes")
    print("Production railway tables modified: no")
    print("PASS: staging API smoke test completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

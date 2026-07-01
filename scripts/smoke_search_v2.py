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

    print("RailYatra search-v2 smoke test")
    print("Mode: read-only")

    client = TestClient(app)
    edges = get_graph_edge_preview(limit=1)

    if not edges:
        print("FAIL: no staging graph edge available")
        return 1

    source = str(edges[0]["from_station_code"])
    destination = str(edges[0]["to_station_code"])

    response = client.get(
        "/search-v2",
        params={
            "source": source,
            "destination": destination,
            "direct_limit": 5,
            "transfer_limit": 1,
        },
    )

    print(f"GET /search-v2?source={source}&destination={destination} -> {response.status_code}")

    if response.status_code != 200:
        print(response.text)
        print("FAIL: /search-v2 did not return 200")
        return 1

    payload = response.json()

    print(f"status: {payload.get('status')}")
    print(f"engine: {payload.get('engine')}")
    print(f"count: {payload.get('count')}")
    print(f"direct_count: {payload.get('direct_count')}")
    print(f"one_transfer_count: {payload.get('one_transfer_count')}")

    if payload.get("status") != "ok":
        print("FAIL: /search-v2 status should be ok")
        return 1

    if payload.get("endpoint") != "/search-v2":
        print("FAIL: /search-v2 endpoint marker missing")
        return 1

    if payload.get("count", 0) < 1:
        print("FAIL: /search-v2 returned no routes for known staging edge")
        return 1

    if payload.get("direct_count", 0) < 1:
        print("FAIL: /search-v2 returned no direct routes for known staging edge")
        return 1

    if not payload.get("routes"):
        print("FAIL: /search-v2 routes missing")
        return 1

    first_route = payload["routes"][0]

    if "legs" not in first_route or not first_route["legs"]:
        print("FAIL: first /search-v2 route missing legs")
        return 1

    if payload.get("database_write_skipped") is not True:
        print("FAIL: /search-v2 did not report database_write_skipped true")
        return 1

    if payload.get("production_railway_tables_modified") is not False:
        print("FAIL: /search-v2 did not report production table protection")
        return 1

    legacy_response = client.get(
        "/search",
        params={
            "source": source,
            "destination": destination,
        },
    )

    print(f"GET /search legacy endpoint -> {legacy_response.status_code}")

    if legacy_response.status_code != 200:
        print("FAIL: legacy /search should remain available")
        return 1

    print("Database write skipped: yes")
    print("Production railway tables modified: no")
    print("Legacy /search unchanged: yes")
    print("PASS: search-v2 smoke test completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

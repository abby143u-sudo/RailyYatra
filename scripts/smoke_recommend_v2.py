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

    print("RailYatra recommend-v2 smoke test")
    print("Mode: read-only")

    client = TestClient(app)
    edges = get_graph_edge_preview(limit=1)

    if not edges:
        print("FAIL: no staging graph edge available")
        return 1

    source = str(edges[0]["from_station_code"])
    destination = str(edges[0]["to_station_code"])

    response = client.get(
        "/recommend-v2",
        params={
            "source": source,
            "destination": destination,
            "direct_limit": 5,
            "transfer_limit": 1,
        },
    )

    print(f"GET /recommend-v2?source={source}&destination={destination} -> {response.status_code}")

    if response.status_code != 200:
        print(response.text)
        print("FAIL: /recommend-v2 did not return 200")
        return 1

    payload = response.json()

    print(f"status: {payload.get('status')}")
    print(f"engine: {payload.get('engine')}")
    print(f"count: {payload.get('count')}")
    print(f"direct_count: {payload.get('direct_count')}")
    print(f"one_transfer_count: {payload.get('one_transfer_count')}")

    if payload.get("status") != "ok":
        print("FAIL: /recommend-v2 status should be ok")
        return 1

    if payload.get("endpoint") != "/recommend-v2":
        print("FAIL: /recommend-v2 endpoint marker missing")
        return 1

    recommendations = payload.get("recommendations") or []

    if not recommendations:
        print("FAIL: /recommend-v2 returned no recommendations")
        return 1

    first = recommendations[0]

    required_first_route_fields = [
        "recommendation_rank",
        "confidence",
        "transfer_safety",
        "reasons",
        "booking_status",
        "legs",
    ]

    for field in required_first_route_fields:
        print(f"top recommendation field {field}: {'yes' if field in first else 'missing'}")
        if field not in first:
            print(f"FAIL: top recommendation missing {field}")
            return 1

    if first["recommendation_rank"] != 1:
        print("FAIL: first recommendation rank should be 1")
        return 1

    if not first.get("legs"):
        print("FAIL: first recommendation missing legs")
        return 1

    if not first.get("reasons"):
        print("FAIL: first recommendation missing reasons")
        return 1

    if first.get("booking_status", {}).get("live_availability_connected") is not False:
        print("FAIL: booking status should say live availability is not connected yet")
        return 1

    if payload.get("summary", {}).get("legacy_search_unchanged") is not True:
        print("FAIL: summary should mark legacy search unchanged")
        return 1

    if payload.get("database_write_skipped") is not True:
        print("FAIL: /recommend-v2 did not report database_write_skipped true")
        return 1

    if payload.get("production_railway_tables_modified") is not False:
        print("FAIL: /recommend-v2 did not report production table protection")
        return 1

    legacy_response = client.get(
        "/search",
        params={
            "source": source,
            "destination": destination,
        },
    )

    search_v2_response = client.get(
        "/search-v2",
        params={
            "source": source,
            "destination": destination,
            "direct_limit": 5,
            "transfer_limit": 1,
        },
    )

    print(f"GET /search legacy endpoint -> {legacy_response.status_code}")
    print(f"GET /search-v2 endpoint -> {search_v2_response.status_code}")

    if legacy_response.status_code != 200:
        print("FAIL: legacy /search should remain available")
        return 1

    if search_v2_response.status_code != 200:
        print("FAIL: /search-v2 should remain available")
        return 1

    print("Database write skipped: yes")
    print("Production railway tables modified: no")
    print("Legacy /search unchanged: yes")
    print("Search-v2 still available: yes")
    print("PASS: recommend-v2 smoke test completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
APP_DIR = REPO_ROOT / "app"
sys.path.insert(0, str(APP_DIR))


def main() -> int:
    from backend.staging.queries import get_graph_edge_preview
    from backend.staging.route_engine import search_staging_routes

    print("RailYatra staging route engine smoke test")
    print("Mode: read-only")

    edges = get_graph_edge_preview(limit=1)

    if not edges:
        print("FAIL: no staging edge available")
        return 1

    source = str(edges[0]["from_station_code"])
    destination = str(edges[0]["to_station_code"])

    result = search_staging_routes(
        source_station_code=source,
        destination_station_code=destination,
        direct_limit=5,
        transfer_limit=1,
    )

    print(f"source: {result['source']}")
    print(f"destination: {result['destination']}")
    print(f"total routes: {result['count']}")
    print(f"direct routes: {result['direct_count']}")
    print(f"one-transfer routes: {result['one_transfer_count']}")

    if result["count"] < 1:
        print("FAIL: route engine returned no routes for known staging edge")
        return 1

    if result["direct_count"] < 1:
        print("FAIL: route engine returned no direct route for known staging edge")
        return 1

    first_route = result["routes"][0]
    print(f"top route type: {first_route.get('route_type')}")
    print(f"top route score: {first_route.get('score')}")
    print(f"top route legs: {len(first_route.get('legs', []))}")

    if "score" not in first_route:
        print("FAIL: top route missing score")
        return 1

    if not first_route.get("legs"):
        print("FAIL: top route missing legs")
        return 1

    if result.get("database_write_skipped") is not True:
        print("FAIL: route engine did not report database_write_skipped true")
        return 1

    if result.get("production_railway_tables_modified") is not False:
        print("FAIL: route engine did not report production table protection")
        return 1

    print("Database write skipped: yes")
    print("Production railway tables modified: no")
    print("PASS: staging route engine smoke test completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

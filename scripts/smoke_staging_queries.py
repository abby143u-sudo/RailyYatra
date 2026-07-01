#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
APP_DIR = REPO_ROOT / "app"
sys.path.insert(0, str(APP_DIR))


def main() -> int:
    from backend.staging.queries import (
        find_direct_trains,
        find_station_by_code,
        find_train_by_number,
        get_graph_edge_preview,
        get_next_stops_from_station,
        get_staging_counts,
        get_station_pair_train_count,
        get_train_stops,
        search_stations,
    )

    print("RailYatra staging query helper smoke test")
    print("Mode: read-only")

    counts = get_staging_counts()
    print("Staging counts:")
    for key, value in counts.items():
        print(f"  {key}: {value}")

    if counts.get("staging_stations", 0) < 8000:
        print("FAIL: staging_stations count too low")
        return 1

    if counts.get("staging_trains", 0) < 5000:
        print("FAIL: staging_trains count too low")
        return 1

    if counts.get("staging_train_stops", 0) < 400000:
        print("FAIL: staging_train_stops count too low")
        return 1

    station = find_station_by_code("NDLS")
    print(f"NDLS station found: {'yes' if station else 'no'}")

    station_results = search_stations("PATNA", limit=5)
    print(f"PATNA station search result count: {len(station_results)}")

    edges = get_graph_edge_preview(limit=10)
    print(f"Graph edge preview count: {len(edges)}")

    if not edges:
        print("FAIL: graph edge preview returned no rows")
        return 1

    sample_train_number = str(edges[0]["train_number"])
    sample_from = str(edges[0]["from_station_code"])
    sample_to = str(edges[0]["to_station_code"])

    train = find_train_by_number(sample_train_number)
    print(f"Sample train found: {'yes' if train else 'no'}")
    print(f"Sample train number: {sample_train_number}")

    stops = get_train_stops(sample_train_number, limit=20)
    print(f"Sample train stops returned: {len(stops)}")

    if not stops:
        print("FAIL: sample train stops returned no rows")
        return 1

    next_stops = get_next_stops_from_station(sample_from, limit=10)
    print(f"Next stops from {sample_from}: {len(next_stops)}")

    pair_count = get_station_pair_train_count(sample_from, sample_to)
    print(f"Sample station pair train count {sample_from}->{sample_to}: {pair_count}")

    if pair_count < 1:
        print("FAIL: sample station pair train count should be at least 1")
        return 1

    direct_sample = find_direct_trains(sample_from, sample_to, limit=5)
    print(f"Direct train sample count {sample_from}->{sample_to}: {len(direct_sample)}")

    if not direct_sample:
        print("FAIL: direct train sample should return at least 1 row")
        return 1

    print("Database write skipped: yes")
    print("Production railway tables modified: no")
    print("PASS: staging query helper smoke test completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

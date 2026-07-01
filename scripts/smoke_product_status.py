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

    print("RailYatra product status smoke test")
    print("Mode: read-only")

    client = TestClient(app)
    response = client.get("/product/status")

    print(f"GET /product/status -> {response.status_code}")

    if response.status_code != 200:
        print(response.text)
        print("FAIL: /product/status did not return 200")
        return 1

    payload = response.json()

    required_top_level = [
        "status",
        "product_name",
        "phase",
        "current_mode",
        "available_engines",
        "data_layer",
        "live_integrations",
        "public_beta_flags",
        "safety",
        "next_steps",
    ]

    for key in required_top_level:
        print(f"top-level field {key}: {'yes' if key in payload else 'missing'}")
        if key not in payload:
            print(f"FAIL: missing {key}")
            return 1

    if payload.get("product_name") != "RailYatra":
        print("FAIL: product_name should be RailYatra")
        return 1

    if payload.get("phase") != "phase_5_public_beta_readiness":
        print("FAIL: phase marker incorrect")
        return 1

    engines = payload.get("available_engines", {})

    for key in ["legacy_search", "search_v2", "recommend_v2", "staging_api"]:
        print(f"engine {key}: {'yes' if key in engines else 'missing'}")
        if key not in engines:
            print(f"FAIL: missing engine {key}")
            return 1

    live = payload.get("live_integrations", {})

    for key in ["live_fare", "live_availability", "pnr", "booking", "payment", "cancellation"]:
        if live.get(key) is not False:
            print(f"FAIL: live integration {key} should be false")
            return 1

    flags = payload.get("public_beta_flags", {})

    if flags.get("can_demo_real_routes") is not True:
        print("FAIL: can_demo_real_routes should be true")
        return 1

    if flags.get("can_claim_live_booking") is not False:
        print("FAIL: can_claim_live_booking should be false")
        return 1

    safety = payload.get("safety", {})

    if safety.get("legacy_search_unchanged") is not True:
        print("FAIL: legacy_search_unchanged should be true")
        return 1

    if safety.get("database_write_skipped") is not True:
        print("FAIL: database_write_skipped should be true")
        return 1

    if safety.get("production_railway_tables_modified") is not False:
        print("FAIL: production_railway_tables_modified should be false")
        return 1

    legacy_response = client.get("/search", params={"source": "LTT", "destination": "VVH"})
    search_v2_response = client.get("/search-v2", params={"source": "LTT", "destination": "VVH", "direct_limit": 3, "transfer_limit": 1})
    recommend_v2_response = client.get("/recommend-v2", params={"source": "LTT", "destination": "VVH", "direct_limit": 3, "transfer_limit": 1})

    print(f"GET /search -> {legacy_response.status_code}")
    print(f"GET /search-v2 -> {search_v2_response.status_code}")
    print(f"GET /recommend-v2 -> {recommend_v2_response.status_code}")

    if legacy_response.status_code != 200:
        print("FAIL: legacy /search should remain available")
        return 1

    if search_v2_response.status_code != 200:
        print("FAIL: /search-v2 should remain available")
        return 1

    if recommend_v2_response.status_code != 200:
        print("FAIL: /recommend-v2 should remain available")
        return 1

    print("Database write skipped: yes")
    print("Production railway tables modified: no")
    print("Legacy /search unchanged: yes")
    print("Live booking claim blocked: yes")
    print("PASS: product status smoke test completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

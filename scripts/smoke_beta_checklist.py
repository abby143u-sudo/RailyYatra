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

    print("RailYatra beta checklist smoke test")
    print("Mode: read-only")

    client = TestClient(app)
    response = client.get("/product/beta-checklist")

    print(f"GET /product/beta-checklist -> {response.status_code}")

    if response.status_code != 200:
        print(response.text)
        print("FAIL: /product/beta-checklist did not return 200")
        return 1

    payload = response.json()

    required_fields = [
        "status",
        "phase",
        "ready_count",
        "blocked_count",
        "ready_items",
        "blocked_items",
        "next_actions",
        "public_beta_decision",
        "safety",
    ]

    for field in required_fields:
        print(f"field {field}: {'yes' if field in payload else 'missing'}")
        if field not in payload:
            print(f"FAIL: missing field {field}")
            return 1

    if payload.get("phase") != "phase_5_public_beta_readiness":
        print("FAIL: incorrect phase marker")
        return 1

    if payload.get("ready_count", 0) < 5:
        print("FAIL: expected at least 5 ready items")
        return 1

    if payload.get("blocked_count", 0) < 4:
        print("FAIL: expected at least 4 blocked/pending items")
        return 1

    decision = payload.get("public_beta_decision", {})

    if decision.get("can_show_demo_to_users") is not True:
        print("FAIL: can_show_demo_to_users should be true")
        return 1

    if decision.get("can_call_it_live_booking_product") is not False:
        print("FAIL: can_call_it_live_booking_product should be false")
        return 1

    if decision.get("can_take_ticket_payments") is not False:
        print("FAIL: can_take_ticket_payments should be false")
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

    if safety.get("live_booking_claim_blocked") is not True:
        print("FAIL: live_booking_claim_blocked should be true")
        return 1

    product_status_response = client.get("/product/status")
    recommend_response = client.get(
        "/recommend-v2",
        params={
            "source": "LTT",
            "destination": "VVH",
            "direct_limit": 3,
            "transfer_limit": 1,
        },
    )

    print(f"GET /product/status -> {product_status_response.status_code}")
    print(f"GET /recommend-v2 -> {recommend_response.status_code}")

    if product_status_response.status_code != 200:
        print("FAIL: /product/status should remain available")
        return 1

    if recommend_response.status_code != 200:
        print("FAIL: /recommend-v2 should remain available")
        return 1

    print("Demo allowed: yes")
    print("Live booking claim blocked: yes")
    print("Database write skipped: yes")
    print("Production railway tables modified: no")
    print("PASS: beta checklist smoke test completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

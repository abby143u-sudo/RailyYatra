#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

from fastapi.testclient import TestClient


REPO_ROOT = Path(__file__).resolve().parents[1]
APP_DIR = REPO_ROOT / "app"
ENV_EXAMPLE = REPO_ROOT / ".env.example"
DEPLOYMENT_NOTES = REPO_ROOT / "docs" / "DEPLOYMENT_NOTES.md"
sys.path.insert(0, str(APP_DIR))


def main() -> int:
    from backend.api.main import app

    print("RailYatra deployment config smoke test")
    print("Mode: read-only")

    if not ENV_EXAMPLE.exists():
        print("FAIL: .env.example missing")
        return 1

    if not DEPLOYMENT_NOTES.exists():
        print("FAIL: docs/DEPLOYMENT_NOTES.md missing")
        return 1

    env_text = ENV_EXAMPLE.read_text(encoding="utf-8")
    notes_text = DEPLOYMENT_NOTES.read_text(encoding="utf-8")

    required_env_phrases = [
        "RAILYATRA_ALLOWED_ORIGINS",
        "RAILYATRA_LIVE_BOOKING_ENABLED=false",
        "RAILYATRA_LIVE_FARE_ENABLED=false",
        "RAILYATRA_LIVE_AVAILABILITY_ENABLED=false",
        "RAILYATRA_PNR_ENABLED=false",
        "RAILYATRA_PAYMENT_ENABLED=false",
        "VITE_RAILYATRA_API_BASE=http://127.0.0.1:8000",
    ]

    required_notes_phrases = [
        "Real railway route recommendation preview",
        "scripts/check_all.sh",
        "scripts/pre_import_gate.sh",
        "Do not claim",
        "live seat availability",
        "payment-enabled ticketing",
    ]

    for phrase in required_env_phrases:
        print(f".env.example phrase {phrase}: {'yes' if phrase in env_text else 'missing'}")
        if phrase not in env_text:
            print(f"FAIL: missing env phrase {phrase}")
            return 1

    for phrase in required_notes_phrases:
        print(f"deployment note phrase {phrase}: {'yes' if phrase in notes_text else 'missing'}")
        if phrase not in notes_text:
            print(f"FAIL: missing deployment note phrase {phrase}")
            return 1

    client = TestClient(app)
    response = client.get("/product/deployment-status")

    print(f"GET /product/deployment-status -> {response.status_code}")

    if response.status_code != 200:
        print(response.text)
        print("FAIL: /product/deployment-status did not return 200")
        return 1

    payload = response.json()

    if payload.get("phase") != "phase_6_deployment_preparation":
        print("FAIL: incorrect phase marker")
        return 1

    flags = payload.get("live_feature_flags", {})

    for key in [
        "live_booking_enabled",
        "live_fare_enabled",
        "live_availability_enabled",
        "pnr_enabled",
        "payment_enabled",
    ]:
        print(f"feature flag {key}: {flags.get(key)}")
        if flags.get(key) is not False:
            print(f"FAIL: {key} should be false")
            return 1

    readiness = payload.get("deployment_readiness", {})

    if readiness.get("cors_configured") is not True:
        print("FAIL: cors_configured should be true")
        return 1

    if readiness.get("live_booking_claim_blocked") is not True:
        print("FAIL: live_booking_claim_blocked should be true")
        return 1

    safety = payload.get("safety", {})

    if safety.get("database_write_skipped") is not True:
        print("FAIL: database_write_skipped should be true")
        return 1

    if safety.get("production_railway_tables_modified") is not False:
        print("FAIL: production_railway_tables_modified should be false")
        return 1

    print("Deployment env template present: yes")
    print("CORS configured: yes")
    print("Live booking disabled: yes")
    print("Database write skipped: yes")
    print("Production railway tables modified: no")
    print("PASS: deployment config smoke test completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

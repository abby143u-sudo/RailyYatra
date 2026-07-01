#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

BACKEND_URL = os.getenv("RAILYATRA_DEPLOYED_BACKEND_URL", "").strip().rstrip("/")
FRONTEND_URL = os.getenv("RAILYATRA_DEPLOYED_FRONTEND_URL", "").strip().rstrip("/")

def fetch_url(url: str, timeout: int = 25):
    request = urllib.request.Request(url, headers={"User-Agent": "RailYatraDeploymentSmoke/1.0"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = response.read().decode("utf-8", errors="replace")
        return response.status, body

def fetch_json(url: str):
    status, body = fetch_url(url)
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        print(f"FAIL: URL did not return JSON: {url}")
        print(body[:500])
        return status, None
    return status, payload

def check_backend_endpoint(path: str, expected_phrases: list[str] | None = None):
    url = BACKEND_URL + path
    print(f"Checking backend: {url}")
    status, body = fetch_url(url)
    print(f"  status: {status}")
    if status < 200 or status >= 300:
        print(f"FAIL: backend endpoint returned non-2xx: {path}")
        return False
    if expected_phrases:
        for phrase in expected_phrases:
            found = "yes" if phrase in body else "missing"
            print(f"  phrase {phrase}: {found}")
            if phrase not in body:
                print(f"FAIL: backend endpoint missing phrase {phrase}: {path}")
                return False
    return True

def main() -> int:
    print("RailYatra deployed public demo smoke test")
    print("Mode: deployed URL check")

    if not BACKEND_URL or not FRONTEND_URL:
        print("SKIP: deployed URLs are not set.")
        print("Set both variables after deployment:")
        print("  RAILYATRA_DEPLOYED_BACKEND_URL=https://your-render-backend-url.onrender.com")
        print("  RAILYATRA_DEPLOYED_FRONTEND_URL=https://your-vercel-frontend-url.vercel.app")
        print("PASS: deployed smoke skipped safely for local development")
        return 0

    checks = []
    checks.append(check_backend_endpoint("/", ["RailYatra"]))
    checks.append(check_backend_endpoint("/health"))

    status_url = BACKEND_URL + "/product/status"
    print(f"Checking backend JSON: {status_url}")
    status_code, status_payload = fetch_json(status_url)
    checks.append(status_code >= 200 and status_code < 300 and status_payload is not None)
    if status_payload:
        live = status_payload.get("live_integrations", {})
        safety = status_payload.get("safety", {})
        print(f"  product_name: {status_payload.get('product_name')}")
        print(f"  live booking: {live.get('booking')}")
        print(f"  payment: {live.get('payment')}")
        if live.get("booking") is not False:
            print("FAIL: deployed product status should keep booking false")
            checks.append(False)
        if live.get("payment") is not False:
            print("FAIL: deployed product status should keep payment false")
            checks.append(False)
        if safety.get("production_railway_tables_modified") is not False:
            print("FAIL: production railway table safety flag should be false")
            checks.append(False)

    checklist_url = BACKEND_URL + "/product/beta-checklist"
    print(f"Checking backend JSON: {checklist_url}")
    checklist_status, checklist_payload = fetch_json(checklist_url)
    checks.append(checklist_status >= 200 and checklist_status < 300 and checklist_payload is not None)
    if checklist_payload:
        decision = checklist_payload.get("public_beta_decision", {})
        print(f"  recommended_label: {decision.get('recommended_label')}")
        if decision.get("can_call_it_live_booking_product") is not False:
            print("FAIL: deployed checklist should block live booking claim")
            checks.append(False)
        if decision.get("can_take_ticket_payments") is not False:
            print("FAIL: deployed checklist should block ticket payments")
            checks.append(False)

    deploy_status_url = BACKEND_URL + "/product/deployment-status"
    print(f"Checking backend JSON: {deploy_status_url}")
    deployment_status, deployment_payload = fetch_json(deploy_status_url)
    checks.append(deployment_status >= 200 and deployment_status < 300 and deployment_payload is not None)
    if deployment_payload:
        flags = deployment_payload.get("live_feature_flags", {})
        for key in ["live_booking_enabled", "live_fare_enabled", "live_availability_enabled", "pnr_enabled", "payment_enabled"]:
            print(f"  {key}: {flags.get(key)}")
            if flags.get(key) is not False:
                print(f"FAIL: deployed flag should be false: {key}")
                checks.append(False)

    params = urllib.parse.urlencode({"source": "LTT", "destination": "VVH", "direct_limit": "3", "transfer_limit": "1"})
    recommend_url = BACKEND_URL + "/recommend-v2?" + params
    print(f"Checking backend JSON: {recommend_url}")
    recommend_status, recommend_payload = fetch_json(recommend_url)
    checks.append(recommend_status >= 200 and recommend_status < 300 and recommend_payload is not None)
    if recommend_payload:
        print(f"  recommendation count: {recommend_payload.get('count')}")
        if recommend_payload.get("database_write_skipped") is not True:
            print("FAIL: recommend-v2 should report database_write_skipped true")
            checks.append(False)

    print(f"Checking frontend: {FRONTEND_URL}")
    frontend_status, frontend_body = fetch_url(FRONTEND_URL)
    print(f"  status: {frontend_status}")
    checks.append(frontend_status >= 200 and frontend_status < 300)

    required_frontend_phrases = ["RailYatra"]
    for phrase in required_frontend_phrases:
        found = "yes" if phrase in frontend_body else "missing"
        print(f"  frontend phrase {phrase}: {found}")
        if phrase not in frontend_body:
            print(f"FAIL: frontend missing phrase {phrase}")
            checks.append(False)

    if not all(checks):
        print("FAIL: deployed public demo smoke test failed")
        return 1

    print("Backend deployed: yes")
    print("Frontend deployed: yes")
    print("Live booking blocked: yes")
    print("Payment blocked: yes")
    print("Production railway tables modified: no")
    print("PASS: deployed public demo smoke test completed")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except urllib.error.URLError as error:
        print(f"FAIL: network/deployed URL check failed: {error}")
        raise SystemExit(1)

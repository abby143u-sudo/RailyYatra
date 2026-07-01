#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import time
import urllib.request
import urllib.error

BACKEND_URL = os.environ.get("RAILYATRA_DEPLOYED_BACKEND_URL", "").rstrip("/")
FRONTEND_URL = os.environ.get("RAILYATRA_DEPLOYED_FRONTEND_URL", "").rstrip("/")

def fetch_url(url: str, timeout: int = 30, retries: int = 3):
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "RailYatraSmoke/1.0"})
            with urllib.request.urlopen(request, timeout=timeout) as response:
                body = response.read().decode("utf-8", errors="replace")
                return response.status, body
        except Exception as error:
            last_error = error
            print(f"  attempt {attempt} failed: {error}")
            time.sleep(2)

    try:
        completed = subprocess.run(
            ["curl", "-L", "-fsS", "--max-time", str(timeout), url],
            check=True,
            capture_output=True,
            text=True,
        )
        return 200, completed.stdout
    except Exception as curl_error:
        return 0, f"FETCH_FAILED: urllib={last_error}; curl={curl_error}"

def fetch_json(url: str):
    status, body = fetch_url(url)
    if status != 200:
        return status, None, body
    try:
        return status, json.loads(body), body
    except json.JSONDecodeError:
        return status, None, body

def check(condition: bool, label: str) -> bool:
    print(f"  {label}: {'yes' if condition else 'no'}")
    return condition

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

    failures = []

    print(f"Checking backend: {BACKEND_URL}/")
    status, body = fetch_url(f"{BACKEND_URL}/")
    print(f"  status: {status}")
    if status != 200:
        failures.append("backend home not 200")
    if not check("RailYatra" in body, "phrase RailYatra"):
        failures.append("backend home missing RailYatra")

    print(f"Checking backend: {BACKEND_URL}/health")
    status, body = fetch_url(f"{BACKEND_URL}/health")
    print(f"  status: {status}")
    if status != 200:
        failures.append("backend health not 200")

    print(f"Checking backend JSON: {BACKEND_URL}/product/status")
    status, payload, body = fetch_json(f"{BACKEND_URL}/product/status")
    if status != 200 or not isinstance(payload, dict):
        failures.append("product status invalid")
    else:
        print(f"  product_name: {payload.get('product_name')}")
        print(f"  live booking: {payload.get('live_integrations', {}).get('booking')}")
        print(f"  payment: {payload.get('live_integrations', {}).get('payment')}")
        if payload.get("product_name") != "RailYatra":
            failures.append("product name mismatch")
        if payload.get("live_integrations", {}).get("booking") is not False:
            failures.append("booking flag not false")
        if payload.get("live_integrations", {}).get("payment") is not False:
            failures.append("payment flag not false")

    print(f"Checking backend JSON: {BACKEND_URL}/product/beta-checklist")
    status, payload, body = fetch_json(f"{BACKEND_URL}/product/beta-checklist")
    if status != 200 or not isinstance(payload, dict):
        failures.append("beta checklist invalid")
    else:
        label = payload.get("public_beta_decision", {}).get("recommended_label")
        print(f"  recommended_label: {label}")
        if label != "Real railway route recommendation preview":
            failures.append("recommended label mismatch")

    print(f"Checking backend JSON: {BACKEND_URL}/product/deployment-status")
    status, payload, body = fetch_json(f"{BACKEND_URL}/product/deployment-status")
    if status != 200 or not isinstance(payload, dict):
        failures.append("deployment status invalid")
    else:
        flags = payload.get("live_feature_flags", {})
        for key in ["live_booking_enabled", "live_fare_enabled", "live_availability_enabled", "pnr_enabled", "payment_enabled"]:
            print(f"  {key}: {flags.get(key)}")
            if flags.get(key) is not False:
                failures.append(f"{key} not false")

    route = f"{BACKEND_URL}/recommend-v2?source=LTT&destination=VVH&direct_limit=3&transfer_limit=1"
    print(f"Checking backend JSON: {route}")
    status, payload, body = fetch_json(route)
    if status != 200 or not isinstance(payload, dict):
        failures.append("recommend-v2 invalid")
    else:
        count = payload.get("count", 0)
        print(f"  recommendation count: {count}")
        if count <= 0:
            failures.append("recommendation count empty")

    print(f"Checking frontend: {FRONTEND_URL}")
    status, body = fetch_url(FRONTEND_URL, timeout=45, retries=3)
    print(f"  status: {status}")
    if status != 200:
        failures.append("frontend not 200")
    if not check("RailYatra" in body, "frontend phrase RailYatra"):
        failures.append("frontend missing phrase RailYatra")
    if not check("127.0.0.1:8000/health" not in body, "frontend does not hardcode localhost health"):
        failures.append("frontend hardcodes localhost health")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        print("FAIL: deployed public demo smoke test failed")
        return 1

    print("PASS: deployed public demo smoke test completed")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

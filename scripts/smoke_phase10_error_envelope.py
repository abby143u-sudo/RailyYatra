#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

BACKEND_URL = os.environ.get("RAILYATRA_BACKEND_URL", "https://railyyatra-backend.onrender.com").rstrip("/")

def post_json_expect_error(path: str, payload: dict):
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        f"{BACKEND_URL}{path}",
        data=data,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "User-Agent": "RailYatraErrorEnvelopeSmoke/1.0",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            body = response.read().decode("utf-8", errors="replace")
            return response.status, json.loads(body)
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        return error.code, json.loads(body)

def get_json_expect_error(path: str):
    request = urllib.request.Request(f"{BACKEND_URL}{path}", headers={"User-Agent": "RailYatraErrorEnvelopeSmoke/1.0"})

    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            body = response.read().decode("utf-8", errors="replace")
            return response.status, json.loads(body)
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        return error.code, json.loads(body)

def check_envelope(label: str, status: int, payload: dict, expected_status: int) -> bool:
    print(f"{label}: status {status}")
    if status != expected_status:
        print(f"FAIL: expected status {expected_status}")
        return False

    if payload.get("ok") is not False:
        print("FAIL: ok=false missing")
        return False

    error = payload.get("error")
    if not isinstance(error, dict):
        print("FAIL: error object missing")
        return False

    required = ["code", "message", "status_code", "path", "timestamp"]
    missing = [key for key in required if key not in error]
    if missing:
        print(f"FAIL: missing keys {missing}")
        return False

    print(f"PASS: {label} envelope code={error.get('code')}")
    return True

def main() -> int:
    print("RailYatra Phase 10 error envelope smoke test")
    print(f"Backend: {BACKEND_URL}")

    failures = 0

    status, payload = post_json_expect_error("/feedback", {"type": "general", "message": ""})
    if not check_envelope("feedback validation error", status, payload, 422):
        failures += 1

    status, payload = get_json_expect_error("/route-that-does-not-exist")
    if not check_envelope("not found error", status, payload, 404):
        failures += 1

    if failures:
        print("FAIL: error envelope smoke test failed")
        return 1

    print("PASS: error envelope smoke test completed")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

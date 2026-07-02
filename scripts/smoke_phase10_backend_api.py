#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone

BACKEND_URL = os.environ.get("RAILYATRA_BACKEND_URL", "https://railyyatra-backend.onrender.com").rstrip("/")

def request_json(path: str, method: str = "GET", payload: dict | None = None):
    url = f"{BACKEND_URL}{path}"
    data = None
    headers = {"User-Agent": "RailYatraPhase10Smoke/1.0"}

    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(url, data=data, method=method, headers=headers)

    with urllib.request.urlopen(request, timeout=45) as response:
        body = response.read().decode("utf-8", errors="replace")
        return response.status, json.loads(body)

def main() -> int:
    print("RailYatra Phase 10 backend API smoke test")
    print(f"Backend: {BACKEND_URL}")

    failures: list[str] = []

    checks = [
        ("/health", "GET", None, "backend health"),
        ("/feedback/health", "GET", None, "feedback health"),
        ("/analytics/health", "GET", None, "analytics health"),
    ]

    for path, method, payload, label in checks:
        try:
            status, data = request_json(path, method, payload)
            print(f"{label}: status {status}")
            if status != 200:
                failures.append(f"{label} not 200")
        except Exception as error:
            print(f"{label}: FAILED {error}")
            failures.append(f"{label} failed")

    feedback_payload = {
        "type": "general",
        "message": "Phase 10 smoke test feedback",
        "page": "phase10-smoke-test",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    try:
        status, data = request_json("/feedback", "POST", feedback_payload)
        print(f"feedback post: status {status}, ok={data.get('ok')}")
        if status != 200 or data.get("ok") is not True:
            failures.append("feedback post failed")
    except Exception as error:
        print(f"feedback post: FAILED {error}")
        failures.append("feedback post failed")

    analytics_payload = {
        "type": "page_view",
        "details": {"source": "phase10_smoke_test"},
        "page": "phase10-smoke-test",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    try:
        status, data = request_json("/analytics/event", "POST", analytics_payload)
        print(f"analytics post: status {status}, ok={data.get('ok')}")
        if status != 200 or data.get("ok") is not True:
            failures.append("analytics post failed")
    except Exception as error:
        print(f"analytics post: FAILED {error}")
        failures.append("analytics post failed")

    try:
        status, data = request_json("/feedback?limit=5")
        print(f"feedback list: status {status}, count={data.get('count')}")
        if status != 200 or data.get("ok") is not True:
            failures.append("feedback list failed")
    except Exception as error:
        print(f"feedback list: FAILED {error}")
        failures.append("feedback list failed")

    try:
        status, data = request_json("/analytics/events?limit=5")
        print(f"analytics list: status {status}, count={data.get('count')}")
        if status != 200 or data.get("ok") is not True:
            failures.append("analytics list failed")
    except Exception as error:
        print(f"analytics list: FAILED {error}")
        failures.append("analytics list failed")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        print("FAIL: Phase 10 backend API smoke test failed")
        return 1

    print("PASS: Phase 10 backend API smoke test completed")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

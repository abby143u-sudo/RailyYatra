#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import urllib.request

BACKEND_URL = os.environ.get("RAILYATRA_BACKEND_URL", "https://railyyatra-backend.onrender.com").rstrip("/")

def get_json(path: str):
    request = urllib.request.Request(f"{BACKEND_URL}{path}", headers={"User-Agent": "RailYatraAdminSmoke/1.0"})
    with urllib.request.urlopen(request, timeout=45) as response:
        return response.status, json.loads(response.read().decode("utf-8", errors="replace"))

def main() -> int:
    print("RailYatra Phase 10 admin API smoke test")
    print(f"Backend: {BACKEND_URL}")

    failures = []
    checks = [
        ("/admin/health", "admin health"),
        ("/admin/feedback-summary", "feedback summary"),
        ("/admin/analytics-summary", "analytics summary"),
        ("/admin/demo-summary", "demo summary"),
    ]

    for path, label in checks:
        try:
            status, data = get_json(path)
            print(f"{label}: status {status}, ok={data.get('ok')}")
            if status != 200 or data.get("ok") is not True:
                failures.append(label)
        except Exception as error:
            print(f"{label}: FAILED {error}")
            failures.append(label)

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        print("FAIL: admin API smoke test failed")
        return 1

    print("PASS: admin API smoke test completed")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

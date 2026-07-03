#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

BACKEND_URL = os.environ.get("RAILYATRA_BACKEND_URL", "https://railyyatra-backend.onrender.com").rstrip("/")
EXPECTED_MODE = os.environ.get("RAILYATRA_EXPECTED_DB_MODE", "postgresql").strip()

def get_json(path: str):
    request = urllib.request.Request(BACKEND_URL + path, headers={"User-Agent": "RailYatraPhase12PostgresReadiness/1.0"})
    with urllib.request.urlopen(request, timeout=45) as response:
        return response.status, json.loads(response.read().decode("utf-8", errors="replace"))

def main() -> int:
    print("RailYatra Phase 12 deployed PostgreSQL readiness check")
    print("Backend: " + BACKEND_URL)
    failures = []
    checks = ["/admin/database-status", "/feedback/health", "/analytics/health"]
    for path in checks:
        try:
            status, data = get_json(path)
            detected = data.get("mode") or data.get("storage")
            configured = data.get("database_url_configured")
            print(path + ": status=" + str(status) + ", mode=" + str(detected) + ", configured=" + str(configured))
            if status != 200 or data.get("ok") is not True:
                failures.append(path + " failed")
            if detected != EXPECTED_MODE:
                failures.append(path + " expected " + EXPECTED_MODE + " got " + str(detected))
            if EXPECTED_MODE == "postgresql" and configured is not True:
                failures.append(path + " DATABASE_URL not configured")
        except Exception as error:
            print(path + ": FAILED " + str(error))
            failures.append(path + " request failed")
    if failures:
        for failure in failures:
            print("FAIL: " + failure)
        print("FAIL: deployed PostgreSQL readiness check failed")
        return 1
    print("PASS: deployed PostgreSQL readiness check completed")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

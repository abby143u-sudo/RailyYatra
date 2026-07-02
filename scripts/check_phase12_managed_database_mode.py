#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import urllib.request

BACKEND_URL = os.environ.get("RAILYATRA_BACKEND_URL", "https://railyyatra-backend.onrender.com").rstrip("/")
EXPECTED_MODE = os.environ.get("RAILYATRA_EXPECTED_DB_MODE", "").strip()

def get_json(path: str):
    request = urllib.request.Request(BACKEND_URL + path, headers={"User-Agent": "RailYatraPhase12DbMode/1.0"})
    with urllib.request.urlopen(request, timeout=45) as response:
        return response.status, json.loads(response.read().decode("utf-8", errors="replace"))

def main() -> int:
    print("RailYatra Phase 12 managed database mode check")
    print("Backend: " + BACKEND_URL)
    failures = []

    for path in ["/admin/database-status", "/feedback/health", "/analytics/health"]:
        status, data = get_json(path)
        print(path + ": status=" + str(status) + ", mode=" + str(data.get("mode") or data.get("storage")) + ", configured=" + str(data.get("database_url_configured")))
        if status != 200 or data.get("ok") is not True:
            failures.append(path + " failed")
        detected_mode = data.get("mode") or data.get("storage")
        if EXPECTED_MODE and detected_mode != EXPECTED_MODE:
            failures.append(path + " expected " + EXPECTED_MODE + " got " + str(detected_mode))

    if failures:
        for failure in failures:
            print("FAIL: " + failure)
        print("FAIL: Phase 12 database mode check failed")
        return 1

    print("PASS: Phase 12 database mode check completed")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

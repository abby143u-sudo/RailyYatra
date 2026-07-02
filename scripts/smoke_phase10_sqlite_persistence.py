#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import time
import urllib.request
from datetime import datetime, timezone

BACKEND_URL = os.environ.get("RAILYATRA_BACKEND_URL", "https://railyyatra-backend.onrender.com").rstrip("/")

def request_json(path: str, method: str = "GET", payload: dict | None = None):
    data = None
    headers = {"User-Agent": "RailYatraSqliteSmoke/1.0"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(BACKEND_URL + path, data=data, method=method, headers=headers)
    with urllib.request.urlopen(request, timeout=45) as response:
        return response.status, json.loads(response.read().decode("utf-8", errors="replace"))

def main() -> int:
    print("RailYatra Phase 10 SQLite persistence smoke test")
    print("Backend: " + BACKEND_URL)
    marker = "sqlite-smoke-" + str(int(time.time()))
    failures = []
    status, data = request_json("/feedback/health")
    print("feedback health: status " + str(status) + ", storage=" + str(data.get("storage")))
    if status != 200 or data.get("storage") != "sqlite":
        failures.append("feedback sqlite health failed")
    status, data = request_json("/analytics/health")
    print("analytics health: status " + str(status) + ", storage=" + str(data.get("storage")))
    if status != 200 or data.get("storage") != "sqlite":
        failures.append("analytics sqlite health failed")
    status, data = request_json("/feedback", "POST", {"type": "general", "message": "Phase 10 SQLite persistence smoke " + marker, "page": "sqlite-smoke-test", "created_at": datetime.now(timezone.utc).isoformat()})
    print("feedback post: status " + str(status) + ", ok=" + str(data.get("ok")))
    if status != 200 or data.get("ok") is not True:
        failures.append("feedback post failed")
    status, data = request_json("/analytics/event", "POST", {"type": "page_view", "details": {"marker": marker, "source": "sqlite_smoke_test"}, "page": "sqlite-smoke-test", "created_at": datetime.now(timezone.utc).isoformat()})
    print("analytics post: status " + str(status) + ", ok=" + str(data.get("ok")))
    if status != 200 or data.get("ok") is not True:
        failures.append("analytics post failed")
    status, data = request_json("/feedback?limit=20")
    feedback_found = any(marker in str(item.get("message", "")) for item in data.get("feedback", []))
    print("feedback list marker found: " + str(feedback_found))
    if not feedback_found:
        failures.append("feedback marker not found")
    status, data = request_json("/analytics/events?limit=20")
    analytics_found = any(marker in str(item.get("details", {})) for item in data.get("events", []))
    print("analytics list marker found: " + str(analytics_found))
    if not analytics_found:
        failures.append("analytics marker not found")
    if failures:
        for failure in failures:
            print("FAIL: " + failure)
        print("FAIL: SQLite persistence smoke test failed")
        return 1
    print("PASS: SQLite persistence smoke test completed")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

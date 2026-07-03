#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

BACKEND_URL = os.environ.get("RAILYATRA_BACKEND_URL", "https://railyyatra-backend.onrender.com").rstrip("/")
ADMIN_TOKEN = os.environ.get("RAILYATRA_ADMIN_TOKEN", "").strip()

def get_json(path: str):
    headers = {"User-Agent": "RailYatraPhase13AdminAudit/1.0"}
    if ADMIN_TOKEN:
        headers["X-RailYatra-Admin-Token"] = ADMIN_TOKEN
    request = urllib.request.Request(BACKEND_URL + path, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            return response.status, json.loads(response.read().decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        try:
            data = json.loads(body)
        except Exception:
            data = {"raw": body}
        print("HTTP ERROR", error.code, path)
        print(json.dumps(data, indent=2)[:2000])
        return error.code, data

def main() -> int:
    print("RailYatra Phase 13 admin auth and audit smoke")
    print("Backend: " + BACKEND_URL)
    failures = []

    for path in ["/admin/auth-status", "/admin/audit-logs?limit=20"]:
        status, data = get_json(path)
        print(path + ": status=" + str(status) + ", ok=" + str(data.get("ok")))
        print(json.dumps(data, indent=2)[:1200])
        if status != 200 or data.get("ok") is not True:
            failures.append(path + " failed")

    status, data = get_json("/admin/audit-logs?limit=20")
    if status != 200 or data.get("count", 0) < 1:
        failures.append("audit log count did not increase")

    if failures:
        for failure in failures:
            print("FAIL: " + failure)
        print("FAIL: Phase 13 admin auth audit smoke failed")
        return 1

    print("PASS: Phase 13 admin auth and audit smoke completed")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

BACKEND_URL = os.environ.get("RAILYATRA_BACKEND_URL", "https://railyyatra-backend.onrender.com").rstrip("/")
ADMIN_TOKEN = os.environ.get("RAILYATRA_ADMIN_TOKEN", "").strip()

def get_json(path: str, token: str = ""):
    headers = {"User-Agent": "RailYatraSecuritySmoke/1.0"}
    if token:
        headers["X-RailYatra-Admin-Token"] = token
    request = urllib.request.Request(BACKEND_URL + path, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            return response.status, json.loads(response.read().decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read().decode("utf-8", errors="replace"))

def main() -> int:
    print("RailYatra Phase 10 security middleware smoke test")
    print("Backend: " + BACKEND_URL)
    failures = []

    status, payload = get_json("/health")
    print("health: status " + str(status))
    if status != 200:
        failures.append("health failed")

    status, payload = get_json("/admin/health")
    print("admin health without token: status " + str(status))

    if ADMIN_TOKEN:
        if status != 401 or payload.get("ok") is not False:
            failures.append("admin protection without token failed")
        status, payload = get_json("/admin/health", ADMIN_TOKEN)
        print("admin health with token: status " + str(status) + ", ok=" + str(payload.get("ok")))
        if status != 200 or payload.get("ok") is not True:
            failures.append("admin protection with token failed")
    else:
        if status != 200:
            failures.append("admin optional mode failed")

    if failures:
        for failure in failures:
            print("FAIL: " + failure)
        print("FAIL: security middleware smoke test failed")
        return 1

    print("PASS: security middleware smoke test completed")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

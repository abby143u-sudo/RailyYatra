#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import urllib.request

BACKEND_URL = os.environ.get("RAILYATRA_BACKEND_URL", "https://railyyatra-backend.onrender.com").rstrip("/")
ADMIN_TOKEN = os.environ.get("RAILYATRA_ADMIN_TOKEN", "").strip()

def main() -> int:
    headers = {"User-Agent": "RailYatraDatabaseStatusCheck/1.0"}
    if ADMIN_TOKEN:
        headers["X-RailYatra-Admin-Token"] = ADMIN_TOKEN
    request = urllib.request.Request(BACKEND_URL + "/admin/database-status", headers=headers)
    with urllib.request.urlopen(request, timeout=45) as response:
        data = json.loads(response.read().decode("utf-8", errors="replace"))
    print(json.dumps(data, indent=2))
    if data.get("ok") is not True:
        print("FAIL: database status endpoint did not return ok=true")
        return 1
    print("PASS: database status endpoint works")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

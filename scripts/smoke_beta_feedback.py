#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
import tempfile
import uuid
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_DIR = PROJECT_ROOT / "app"

sys.path.insert(0, str(APP_DIR))

# Force an isolated SQLite database for this test.
os.environ.pop("DATABASE_URL", None)
os.environ.pop("RAILYATRA_DEMO_DATABASE_URL", None)
os.environ.pop("RAILYATRA_FEEDBACK_DATABASE_URL", None)

ADMIN_TOKEN = "feedback-smoke-test-token"
os.environ["RAILYATRA_ADMIN_TOKEN"] = ADMIN_TOKEN


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def main() -> int:
    with tempfile.TemporaryDirectory(
        prefix="railyatra-feedback-smoke-"
    ) as temp_dir:
        import backend.api.beta_feedback_store as store

        store.SQLITE_DB_PATH = (
            Path(temp_dir) / "feedback-smoke.db"
        )

        from fastapi.testclient import TestClient
        from backend.api.main import app

        client = TestClient(app)

        admin_headers = {
            "X-RailYatra-Admin-Token": ADMIN_TOKEN,
        }

        marker = (
            "RailYatra feedback smoke "
            + uuid.uuid4().hex
        )

        print("RailYatra beta feedback smoke test")
        print("Mode: isolated SQLite")

        # Health
        response = client.get("/beta/feedback/health")

        print(
            "GET /beta/feedback/health ->",
            response.status_code,
        )

        if response.status_code != 200:
            fail("feedback health endpoint failed")

        health = response.json()

        if health.get("storage_mode") != "sqlite":
            fail("isolated smoke test is not using SQLite")

        # Create
        response = client.post(
            "/beta/feedback",
            json={
                "message": marker,
                "page": "feedback-smoke-test",
                "severity": "normal",
                "name": "Smoke Test",
            },
        )

        print(
            "POST /beta/feedback ->",
            response.status_code,
        )

        if response.status_code != 200:
            fail(f"feedback creation failed: {response.text}")

        feedback_id = response.json().get("feedback_id")

        if not feedback_id:
            fail("feedback_id missing from create response")

        print("Created feedback id:", feedback_id)

        # Paginated admin list
        response = client.get(
            "/admin/beta-feedback",
            params={
                "page": 1,
                "page_size": 1,
            },
            headers=admin_headers,
        )

        print(
            "GET /admin/beta-feedback ->",
            response.status_code,
        )

        if response.status_code != 200:
            fail(f"admin feedback list failed: {response.text}")

        listing = response.json()

        required_pagination_fields = [
            "total",
            "page",
            "page_size",
            "total_pages",
            "has_previous",
            "has_next",
            "feedback",
        ]

        for field in required_pagination_fields:
            if field not in listing:
                fail(f"pagination field missing: {field}")

        # Summary
        response = client.get(
            "/admin/beta-feedback/summary",
            headers=admin_headers,
        )

        print(
            "GET /admin/beta-feedback/summary ->",
            response.status_code,
        )

        if response.status_code != 200:
            fail(f"feedback summary failed: {response.text}")

        summary = response.json().get("counts", {})

        if summary.get("total", 0) < 1:
            fail("summary total did not include test feedback")

        if summary.get("new", 0) < 1:
            fail("summary new count did not include test feedback")

        # Global search + status filter
        response = client.get(
            "/admin/beta-feedback",
            params={
                "page": 1,
                "page_size": 25,
                "status": "new",
                "q": marker,
            },
            headers=admin_headers,
        )

        print(
            "GET filtered /admin/beta-feedback ->",
            response.status_code,
        )

        if response.status_code != 200:
            fail(f"filtered feedback search failed: {response.text}")

        filtered = response.json()

        if filtered.get("total") != 1:
            fail(
                "global search did not return exactly "
                "the created feedback"
            )

        # Update status
        response = client.patch(
            f"/admin/beta-feedback/{feedback_id}/status",
            headers=admin_headers,
            json={"status": "reviewed"},
        )

        print(
            "PATCH feedback status ->",
            response.status_code,
        )

        if response.status_code != 200:
            fail(f"status update failed: {response.text}")

        if response.json().get("status") != "reviewed":
            fail("feedback status was not updated to reviewed")

        # Verify reviewed filter
        response = client.get(
            "/admin/beta-feedback",
            params={
                "status": "reviewed",
                "q": marker,
            },
            headers=admin_headers,
        )

        if response.status_code != 200:
            fail("reviewed feedback verification failed")

        reviewed_items = response.json().get("feedback", [])

        if len(reviewed_items) != 1:
            fail("reviewed feedback was not found")

        # Delete
        response = client.delete(
            f"/admin/beta-feedback/{feedback_id}",
            headers=admin_headers,
        )

        print(
            "DELETE feedback ->",
            response.status_code,
        )

        if response.status_code != 200:
            fail(f"feedback deletion failed: {response.text}")

        # Confirm deletion
        response = client.get(
            "/admin/beta-feedback",
            params={"q": marker},
            headers=admin_headers,
        )

        if response.status_code != 200:
            fail("post-delete verification request failed")

        if response.json().get("total") != 0:
            fail("deleted feedback is still present")

        print("PASS: feedback health")
        print("PASS: feedback creation")
        print("PASS: pagination")
        print("PASS: admin summary")
        print("PASS: global search and filtering")
        print("PASS: status update")
        print("PASS: deletion")
        print("PASS: beta feedback smoke test completed")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

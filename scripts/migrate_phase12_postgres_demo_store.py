#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from urllib.parse import urlparse

def database_url() -> str:
    return (os.environ.get("DATABASE_URL") or os.environ.get("RAILYATRA_DEMO_DATABASE_URL") or "").strip()

def mask_url(value: str) -> str:
    if not value:
        return ""
    parsed = urlparse(value)
    if not parsed.scheme:
        return "configured"
    host = parsed.hostname or "unknown-host"
    port = f":{parsed.port}" if parsed.port else ""
    database = parsed.path.lstrip("/") or "unknown-db"
    return f"{parsed.scheme}://***:***@{host}{port}/{database}"

def connect(url: str):
    import psycopg2
    return psycopg2.connect(url)

def migrate(url: str) -> None:
    with connect(url) as db:
        with db.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS feedback (
                    id BIGSERIAL PRIMARY KEY,
                    type TEXT NOT NULL,
                    message TEXT NOT NULL,
                    page TEXT,
                    client_created_at TEXT,
                    server_created_at TEXT NOT NULL,
                    source TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_feedback_server_created_at
                ON feedback (server_created_at DESC)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_feedback_type
                ON feedback (type)
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analytics_events (
                    id BIGSERIAL PRIMARY KEY,
                    type TEXT NOT NULL,
                    details_json TEXT NOT NULL,
                    page TEXT,
                    client_created_at TEXT,
                    server_created_at TEXT NOT NULL,
                    source TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_analytics_server_created_at
                ON analytics_events (server_created_at DESC)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_analytics_type
                ON analytics_events (type)
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS admin_audit_logs (
                    id BIGSERIAL PRIMARY KEY,
                    admin_id TEXT,
                    action TEXT NOT NULL,
                    endpoint TEXT,
                    ip TEXT,
                    created_at TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_admin_audit_created_at
                ON admin_audit_logs (created_at DESC)
            """)
        db.commit()

def verify(url: str) -> dict:
    result = {
        "ok": True,
        "tables": {},
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }
    with connect(url) as db:
        with db.cursor() as cursor:
            for table in ["feedback", "analytics_events", "admin_audit_logs"]:
                cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_name = %s", (table,))
                exists = cursor.fetchone()[0] == 1
                result["tables"][table] = {"exists": exists}
                if not exists:
                    result["ok"] = False
            cursor.execute("SELECT COUNT(*) FROM feedback")
            result["tables"]["feedback"]["row_count"] = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM analytics_events")
            result["tables"]["analytics_events"]["row_count"] = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM admin_audit_logs")
            result["tables"]["admin_audit_logs"]["row_count"] = cursor.fetchone()[0]
    return result

def main() -> int:
    url = database_url()
    print("RailYatra Phase 12 PostgreSQL migration")
    if not url:
        print("DATABASE_URL/RAILYATRA_DEMO_DATABASE_URL not configured.")
        print("SKIP: SQLite fallback mode remains active.")
        return 0
    if not url.startswith(("postgres://", "postgresql://")):
        print("FAIL: configured database URL is not PostgreSQL")
        print(mask_url(url))
        return 1
    print("Database: " + mask_url(url))
    migrate(url)
    result = verify(url)
    print(json.dumps(result, indent=2))
    if not result.get("ok"):
        print("FAIL: PostgreSQL migration verification failed")
        return 1
    print("PASS: PostgreSQL migration completed")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

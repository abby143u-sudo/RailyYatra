import json
import os
import sqlite3
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

DEMO_DB = Path(__file__).resolve().parents[2] / "data" / "demo_events.db"

def configured_database_url() -> str:
    return (os.environ.get("DATABASE_URL") or os.environ.get("RAILYATRA_DEMO_DATABASE_URL") or "").strip()

def postgres_enabled() -> bool:
    value = configured_database_url()
    return value.startswith("postgres://") or value.startswith("postgresql://")

def mask_database_url(value: str) -> str:
    if not value:
        return ""
    parsed = urlparse(value)
    if not parsed.scheme:
        return "configured"
    host = parsed.hostname or "unknown-host"
    port = f":{parsed.port}" if parsed.port else ""
    database = parsed.path.lstrip("/") or "unknown-db"
    return f"{parsed.scheme}://***:***@{host}{port}/{database}"

def get_store_status() -> dict[str, Any]:
    database_url = configured_database_url()
    mode = "postgresql" if postgres_enabled() else "sqlite"
    return {
        "ok": True,
        "mode": mode,
        "database_url_configured": bool(database_url),
        "masked_database_url": mask_database_url(database_url),
        "sqlite_path": str(DEMO_DB),
        "runtime_store": "managed_postgresql" if mode == "postgresql" else "runtime_sqlite",
    }

def sqlite_connect():
    DEMO_DB.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DEMO_DB)
    connection.row_factory = sqlite3.Row
    return connection

def postgres_connect():
    import psycopg2
    return psycopg2.connect(configured_database_url())

def init_sqlite_store() -> None:
    with sqlite_connect() as db:
        db.execute("CREATE TABLE IF NOT EXISTS feedback (id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT NOT NULL, message TEXT NOT NULL, page TEXT, client_created_at TEXT, server_created_at TEXT NOT NULL, source TEXT NOT NULL, payload_json TEXT NOT NULL)")
        db.execute("CREATE TABLE IF NOT EXISTS analytics_events (id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT NOT NULL, details_json TEXT NOT NULL, page TEXT, client_created_at TEXT, server_created_at TEXT NOT NULL, source TEXT NOT NULL, payload_json TEXT NOT NULL)")
        db.commit()

def init_postgres_store() -> None:
    with postgres_connect() as db:
        with db.cursor() as cursor:
            cursor.execute("CREATE TABLE IF NOT EXISTS feedback (id BIGSERIAL PRIMARY KEY, type TEXT NOT NULL, message TEXT NOT NULL, page TEXT, client_created_at TEXT, server_created_at TEXT NOT NULL, source TEXT NOT NULL, payload_json TEXT NOT NULL)")
            cursor.execute("CREATE TABLE IF NOT EXISTS analytics_events (id BIGSERIAL PRIMARY KEY, type TEXT NOT NULL, details_json TEXT NOT NULL, page TEXT, client_created_at TEXT, server_created_at TEXT NOT NULL, source TEXT NOT NULL, payload_json TEXT NOT NULL)")
        db.commit()

def init_demo_store() -> None:
    if postgres_enabled():
        init_postgres_store()
    else:
        init_sqlite_store()

def save_feedback_entry_sqlite(entry: dict[str, Any]) -> dict[str, Any]:
    init_sqlite_store()
    payload_json = json.dumps(entry, ensure_ascii=False, default=str)
    with sqlite_connect() as db:
        cursor = db.execute("INSERT INTO feedback (type, message, page, client_created_at, server_created_at, source, payload_json) VALUES (?, ?, ?, ?, ?, ?, ?)", (str(entry.get("type") or "general"), str(entry.get("message") or ""), str(entry.get("page") or ""), entry.get("client_created_at"), str(entry.get("server_created_at") or ""), str(entry.get("source") or "public_demo"), payload_json))
        db.commit()
        saved = dict(entry)
        saved["id"] = cursor.lastrowid
        return saved

def save_feedback_entry_postgres(entry: dict[str, Any]) -> dict[str, Any]:
    init_postgres_store()
    payload_json = json.dumps(entry, ensure_ascii=False, default=str)
    with postgres_connect() as db:
        with db.cursor() as cursor:
            cursor.execute("INSERT INTO feedback (type, message, page, client_created_at, server_created_at, source, payload_json) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id", (str(entry.get("type") or "general"), str(entry.get("message") or ""), str(entry.get("page") or ""), entry.get("client_created_at"), str(entry.get("server_created_at") or ""), str(entry.get("source") or "public_demo"), payload_json))
            new_id = cursor.fetchone()[0]
        db.commit()
    saved = dict(entry)
    saved["id"] = new_id
    return saved

def save_feedback_entry(entry: dict[str, Any]) -> dict[str, Any]:
    if postgres_enabled():
        return save_feedback_entry_postgres(entry)
    return save_feedback_entry_sqlite(entry)

def read_feedback_entries_sqlite(limit: int = 20) -> list[dict[str, Any]]:
    init_sqlite_store()
    safe_limit = max(1, min(int(limit or 20), 200))
    with sqlite_connect() as db:
        rows = db.execute("SELECT * FROM feedback ORDER BY id DESC LIMIT ?", (safe_limit,)).fetchall()
    entries = []
    for row in rows:
        try:
            item = json.loads(row["payload_json"])
        except Exception:
            item = {}
        if not isinstance(item, dict):
            item = {}
        item["id"] = row["id"]
        entries.append(item)
    return entries

def read_feedback_entries_postgres(limit: int = 20) -> list[dict[str, Any]]:
    init_postgres_store()
    safe_limit = max(1, min(int(limit or 20), 200))
    with postgres_connect() as db:
        with db.cursor() as cursor:
            cursor.execute("SELECT id, payload_json FROM feedback ORDER BY id DESC LIMIT %s", (safe_limit,))
            rows = cursor.fetchall()
    entries = []
    for row_id, payload_json in rows:
        try:
            item = json.loads(payload_json)
        except Exception:
            item = {}
        if not isinstance(item, dict):
            item = {}
        item["id"] = row_id
        entries.append(item)
    return entries

def read_feedback_entries(limit: int = 20) -> list[dict[str, Any]]:
    if postgres_enabled():
        return read_feedback_entries_postgres(limit)
    return read_feedback_entries_sqlite(limit)

def save_analytics_entry_sqlite(entry: dict[str, Any]) -> dict[str, Any]:
    init_sqlite_store()
    payload_json = json.dumps(entry, ensure_ascii=False, default=str)
    details_json = json.dumps(entry.get("details") or {}, ensure_ascii=False, default=str)
    with sqlite_connect() as db:
        cursor = db.execute("INSERT INTO analytics_events (type, details_json, page, client_created_at, server_created_at, source, payload_json) VALUES (?, ?, ?, ?, ?, ?, ?)", (str(entry.get("type") or "custom_event"), details_json, str(entry.get("page") or ""), entry.get("client_created_at"), str(entry.get("server_created_at") or ""), str(entry.get("source") or "public_demo"), payload_json))
        db.commit()
        saved = dict(entry)
        saved["id"] = cursor.lastrowid
        return saved

def save_analytics_entry_postgres(entry: dict[str, Any]) -> dict[str, Any]:
    init_postgres_store()
    payload_json = json.dumps(entry, ensure_ascii=False, default=str)
    details_json = json.dumps(entry.get("details") or {}, ensure_ascii=False, default=str)
    with postgres_connect() as db:
        with db.cursor() as cursor:
            cursor.execute("INSERT INTO analytics_events (type, details_json, page, client_created_at, server_created_at, source, payload_json) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id", (str(entry.get("type") or "custom_event"), details_json, str(entry.get("page") or ""), entry.get("client_created_at"), str(entry.get("server_created_at") or ""), str(entry.get("source") or "public_demo"), payload_json))
            new_id = cursor.fetchone()[0]
        db.commit()
    saved = dict(entry)
    saved["id"] = new_id
    return saved

def save_analytics_entry(entry: dict[str, Any]) -> dict[str, Any]:
    if postgres_enabled():
        return save_analytics_entry_postgres(entry)
    return save_analytics_entry_sqlite(entry)

def read_analytics_entries_sqlite(limit: int = 50) -> list[dict[str, Any]]:
    init_sqlite_store()
    safe_limit = max(1, min(int(limit or 50), 500))
    with sqlite_connect() as db:
        rows = db.execute("SELECT * FROM analytics_events ORDER BY id DESC LIMIT ?", (safe_limit,)).fetchall()
    entries = []
    for row in rows:
        try:
            item = json.loads(row["payload_json"])
        except Exception:
            item = {}
        if not isinstance(item, dict):
            item = {}
        item["id"] = row["id"]
        entries.append(item)
    return entries

def read_analytics_entries_postgres(limit: int = 50) -> list[dict[str, Any]]:
    init_postgres_store()
    safe_limit = max(1, min(int(limit or 50), 500))
    with postgres_connect() as db:
        with db.cursor() as cursor:
            cursor.execute("SELECT id, payload_json FROM analytics_events ORDER BY id DESC LIMIT %s", (safe_limit,))
            rows = cursor.fetchall()
    entries = []
    for row_id, payload_json in rows:
        try:
            item = json.loads(payload_json)
        except Exception:
            item = {}
        if not isinstance(item, dict):
            item = {}
        item["id"] = row_id
        entries.append(item)
    return entries

def read_analytics_entries(limit: int = 50) -> list[dict[str, Any]]:
    if postgres_enabled():
        return read_analytics_entries_postgres(limit)
    return read_analytics_entries_sqlite(limit)

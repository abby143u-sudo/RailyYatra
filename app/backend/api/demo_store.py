import json
import sqlite3
from pathlib import Path
from typing import Any

DEMO_DB = Path(__file__).resolve().parents[2] / "data" / "demo_events.db"

def connect():
    DEMO_DB.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DEMO_DB)
    connection.row_factory = sqlite3.Row
    return connection

def init_demo_store() -> None:
    with connect() as db:
        db.execute("CREATE TABLE IF NOT EXISTS feedback (id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT NOT NULL, message TEXT NOT NULL, page TEXT, client_created_at TEXT, server_created_at TEXT NOT NULL, source TEXT NOT NULL, payload_json TEXT NOT NULL)")
        db.execute("CREATE TABLE IF NOT EXISTS analytics_events (id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT NOT NULL, details_json TEXT NOT NULL, page TEXT, client_created_at TEXT, server_created_at TEXT NOT NULL, source TEXT NOT NULL, payload_json TEXT NOT NULL)")
        db.commit()

def save_feedback_entry(entry: dict[str, Any]) -> dict[str, Any]:
    init_demo_store()
    payload_json = json.dumps(entry, ensure_ascii=False, default=str)
    with connect() as db:
        cursor = db.execute("INSERT INTO feedback (type, message, page, client_created_at, server_created_at, source, payload_json) VALUES (?, ?, ?, ?, ?, ?, ?)", (str(entry.get("type") or "general"), str(entry.get("message") or ""), str(entry.get("page") or ""), entry.get("client_created_at"), str(entry.get("server_created_at") or ""), str(entry.get("source") or "public_demo"), payload_json))
        db.commit()
        saved = dict(entry)
        saved["id"] = cursor.lastrowid
        return saved

def read_feedback_entries(limit: int = 20) -> list[dict[str, Any]]:
    init_demo_store()
    safe_limit = max(1, min(int(limit or 20), 200))
    with connect() as db:
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

def save_analytics_entry(entry: dict[str, Any]) -> dict[str, Any]:
    init_demo_store()
    payload_json = json.dumps(entry, ensure_ascii=False, default=str)
    details_json = json.dumps(entry.get("details") or {}, ensure_ascii=False, default=str)
    with connect() as db:
        cursor = db.execute("INSERT INTO analytics_events (type, details_json, page, client_created_at, server_created_at, source, payload_json) VALUES (?, ?, ?, ?, ?, ?, ?)", (str(entry.get("type") or "custom_event"), details_json, str(entry.get("page") or ""), entry.get("client_created_at"), str(entry.get("server_created_at") or ""), str(entry.get("source") or "public_demo"), payload_json))
        db.commit()
        saved = dict(entry)
        saved["id"] = cursor.lastrowid
        return saved

def read_analytics_entries(limit: int = 50) -> list[dict[str, Any]]:
    init_demo_store()
    safe_limit = max(1, min(int(limit or 50), 500))
    with connect() as db:
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

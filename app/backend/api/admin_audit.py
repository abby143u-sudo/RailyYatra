import json
from datetime import datetime, timezone
from typing import Any

from fastapi import Request

from backend.api.demo_store import postgres_connect, postgres_enabled, sqlite_connect

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()

def request_ip(request: Request | None) -> str:
    if request is None or request.client is None:
        return ""
    return request.client.host or ""

def ensure_sqlite_audit_store() -> None:
    with sqlite_connect() as db:
        db.execute("CREATE TABLE IF NOT EXISTS admin_audit_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, admin_id TEXT, action TEXT NOT NULL, endpoint TEXT, ip TEXT, created_at TEXT NOT NULL, payload_json TEXT NOT NULL)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_admin_audit_created_at ON admin_audit_logs (created_at DESC)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_admin_audit_action ON admin_audit_logs (action)")
        db.commit()

def ensure_postgres_audit_store() -> None:
    with postgres_connect() as db:
        with db.cursor() as cursor:
            cursor.execute("CREATE TABLE IF NOT EXISTS admin_audit_logs (id BIGSERIAL PRIMARY KEY, admin_id TEXT, action TEXT NOT NULL, endpoint TEXT, ip TEXT, created_at TEXT NOT NULL, payload_json TEXT NOT NULL)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_admin_audit_created_at ON admin_audit_logs (created_at DESC)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_admin_audit_action ON admin_audit_logs (action)")
        db.commit()

def active_audit_store() -> str:
    if postgres_enabled():
        try:
            ensure_postgres_audit_store()
            return "postgresql"
        except Exception:
            ensure_sqlite_audit_store()
            return "sqlite_fallback"
    ensure_sqlite_audit_store()
    return "sqlite"

def insert_sqlite(entry: dict[str, Any], payload_json: str) -> dict[str, Any]:
    ensure_sqlite_audit_store()
    with sqlite_connect() as db:
        cursor = db.execute("INSERT INTO admin_audit_logs (admin_id, action, endpoint, ip, created_at, payload_json) VALUES (?, ?, ?, ?, ?, ?)", (entry["admin_id"], entry["action"], entry["endpoint"], entry["ip"], entry["created_at"], payload_json))
        db.commit()
        entry["id"] = cursor.lastrowid
    return entry

def insert_postgres(entry: dict[str, Any], payload_json: str) -> dict[str, Any]:
    ensure_postgres_audit_store()
    with postgres_connect() as db:
        with db.cursor() as cursor:
            cursor.execute("INSERT INTO admin_audit_logs (admin_id, action, endpoint, ip, created_at, payload_json) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id", (entry["admin_id"], entry["action"], entry["endpoint"], entry["ip"], entry["created_at"], payload_json))
            entry["id"] = cursor.fetchone()[0]
        db.commit()
    return entry

def save_admin_audit_log(action: str, endpoint: str, request: Request | None = None, admin_id: str = "", payload: dict[str, Any] | None = None) -> dict[str, Any]:
    entry = {
        "admin_id": admin_id or "unknown_admin",
        "action": action,
        "endpoint": endpoint,
        "ip": request_ip(request),
        "created_at": utc_now(),
        "payload": payload or {},
    }
    payload_json = json.dumps(entry, ensure_ascii=False, default=str)
    store = active_audit_store()
    entry["store"] = store

    try:
        if store == "postgresql":
            saved = insert_postgres(entry, payload_json)
        else:
            saved = insert_sqlite(entry, payload_json)
        return {"ok": True, "audit": saved}
    except Exception as error:
        try:
            entry["store"] = "sqlite_error_fallback"
            entry["fallback_reason"] = str(error)
            fallback_json = json.dumps(entry, ensure_ascii=False, default=str)
            saved = insert_sqlite(entry, fallback_json)
            return {"ok": True, "audit": saved, "fallback_reason": str(error)}
        except Exception as fallback_error:
            return {"ok": False, "error": str(fallback_error), "original_error": str(error), "audit": entry}

def read_sqlite_logs(limit: int) -> list[dict[str, Any]]:
    ensure_sqlite_audit_store()
    with sqlite_connect() as db:
        rows = db.execute("SELECT id, payload_json FROM admin_audit_logs ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return rows_to_logs(rows)

def read_postgres_logs(limit: int) -> list[dict[str, Any]]:
    ensure_postgres_audit_store()
    with postgres_connect() as db:
        with db.cursor() as cursor:
            cursor.execute("SELECT id, payload_json FROM admin_audit_logs ORDER BY id DESC LIMIT %s", (limit,))
            rows = cursor.fetchall()
    return rows_to_logs(rows)

def rows_to_logs(rows) -> list[dict[str, Any]]:
    logs = []
    for row in rows:
        row_id = row[0]
        payload_json = row[1]
        try:
            item = json.loads(payload_json)
        except Exception:
            item = {}
        if not isinstance(item, dict):
            item = {}
        item["id"] = row_id
        logs.append(item)
    return logs

def read_admin_audit_logs(limit: int = 50) -> list[dict[str, Any]]:
    safe_limit = max(1, min(int(limit or 50), 200))
    store = active_audit_store()
    try:
        if store == "postgresql":
            return read_postgres_logs(safe_limit)
        return read_sqlite_logs(safe_limit)
    except Exception:
        return read_sqlite_logs(safe_limit)

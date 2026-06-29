import sqlite3
from pathlib import Path

DB_NAME = "railyatra.db"


def get_database_path():
    return Path(__file__).resolve().parents[2] / DB_NAME


def get_connection():
    conn = sqlite3.connect(get_database_path())
    conn.row_factory = sqlite3.Row
    return conn


def fetch_all(query, params=()):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def fetch_one(query, params=()):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

# metrics.py
import sqlite3
import os
import threading
from datetime import datetime

DB_DIR = "metrics"
DB_PATH = os.path.join(DB_DIR, "metrics.db")

# Ensure the metrics/ folder exists
os.makedirs(DB_DIR, exist_ok=True)

# We’ll use a simple threading.Lock to serialize writes
_lock = threading.Lock()

def _get_connection():
    """
    Return a sqlite3.Connection (create table if it doesn’t exist).
    """
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def initialize_db():
    """
    Create the table if it does not exist.
    """
    conn = _get_connection()
    with conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS invocations (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp   TEXT NOT NULL,
                latency_ms  REAL NOT NULL,
                success     INTEGER NOT NULL
            )
            """
        )
    conn.close()

def record_invocation(latency_ms: float, success: bool):
    """
    Insert a new row into invocations with the current timestamp.
    """
    initialize_db()
    ts = datetime.utcnow().isoformat(sep=" ", timespec="seconds")
    success_flag = 1 if success else 0
    with _lock:
        conn = _get_connection()
        with conn:
            conn.execute(
                "INSERT INTO invocations (timestamp, latency_ms, success) VALUES (?, ?, ?)",
                (ts, latency_ms, success_flag),
            )
        conn.close()

def fetch_all_invocations():
    """
    Returns a list of dicts, one per row, ordered by id ascending.
    """
    initialize_db()
    conn = _get_connection()
    cursor = conn.execute("SELECT * FROM invocations ORDER BY id ASC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

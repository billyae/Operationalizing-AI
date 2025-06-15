import sqlite3
import logging
from datetime import datetime

DB_FILE = 'audit_logs.db'

# ─── Logger Configuration ──────────────────────────────────────────────────────
logger = logging.getLogger("audit_logger")
logger.setLevel(logging.INFO)
if not logger.handlers:
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s %(levelname)-8s %(message)s",
                            datefmt="%Y-%m-%d %H:%M:%S")
    console.setFormatter(fmt)
    logger.addHandler(console)


def init_db() -> None:
    """
    Initialize or migrate the audit_logs table:
      1. Create it if it doesn't exist.
      2. Add `latency_ms` and `success` columns if they're missing.
    """
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    # Create the base table (legacy columns only)
    cur.execute('''
        CREATE TABLE IF NOT EXISTS audit_logs (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT    NOT NULL,
            user_id   TEXT    NOT NULL,
            prompt    TEXT    NOT NULL,
            response  TEXT    NOT NULL
        )
    ''')

    # Inspect existing columns
    cur.execute("PRAGMA table_info(audit_logs)")
    cols = {row[1] for row in cur.fetchall()}

    # Add missing columns
    if 'latency_ms' not in cols:
        cur.execute("ALTER TABLE audit_logs ADD COLUMN latency_ms REAL NOT NULL DEFAULT 0")
    if 'success' not in cols:
        cur.execute("ALTER TABLE audit_logs ADD COLUMN success   INTEGER NOT NULL DEFAULT 1")

    conn.commit()
    conn.close()


def record_log(
    user_id: str,
    prompt: str,
    response: str,
    latency_ms: float,
    success: bool
) -> None:
    """
    Store an audit entry and also print it to the console.

    :param user_id:    Identifier for the requester.
    :param prompt:     The user's last message.
    :param response:   The model's reply or error text.
    :param latency_ms: Elapsed time in milliseconds.
    :param success:    True on success, False on failure.
    """
    timestamp = datetime.utcnow().isoformat()
    success_flag = 1 if success else 0

    # 1) Persist to SQLite
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute('''
            INSERT INTO audit_logs (
                timestamp, user_id, prompt, response, latency_ms, success
            ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (timestamp, user_id, prompt, response, latency_ms, success_flag))
        conn.commit()

    # 2) Print to console
    logger.info(
        f"[Audit] user={user_id!r} prompt={prompt!r} "
        f"latency={latency_ms:.1f}ms success={bool(success_flag)}"
    )

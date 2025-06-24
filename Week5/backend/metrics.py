import sqlite3
import os
import threading
from datetime import datetime

# Constants defining the metrics directory and database path
DB_DIR = "metrics"
DB_PATH = os.path.join(DB_DIR, "metrics.db")

# A threading lock to serialize database writes
_lock = threading.Lock()

def create_db_directory(db_dir: str = DB_DIR) -> None:
    """
    Ensure that the specified metrics directory exists. If it does not, create it.

    Args:
        db_dir (str): Path to the directory for storing the SQLite database.
    """
    try:
        os.makedirs(db_dir, exist_ok=True)
    except Exception as e:
        raise RuntimeError(f"Failed to create metrics directory '{db_dir}': {e}")


def _get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    """
    Create and return a new SQLite connection. Sets row_factory to allow
    dict-like row access.

    Args:
        db_path (str): Path to the SQLite database file.

    Returns:
        sqlite3.Connection: A new connection to the SQLite database.
    """
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_db() -> None:
    """
    Initialize the database by:
      1. Ensuring the metrics directory exists.
      2. Creating the 'invocations' table if it does not exist.

    This function should be called before any read/write operations.
    """
    # Ensure the metrics directory and database file can be created
    create_db_directory()

    # Create the table if it doesn't already exist
    conn = _get_connection()
    try:
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
    except Exception as e:
        raise RuntimeError(f"Failed to initialize database table: {e}")
    finally:
        conn.close()


def record_invocation(latency_ms: float, success: bool) -> None:
    """
    Record a single invocation entry into the 'invocations' table.

    Args:
        latency_ms (float): The latency of the invocation in milliseconds.
        success (bool): Whether the invocation succeeded (True) or failed (False).

    Raises:
        RuntimeError: If any database write operation fails.
    """
    # Ensure the database and table exist before inserting
    initialize_db()

    # Format current UTC timestamp (e.g., "2025-06-05 12:34:56")
    timestamp = datetime.utcnow().isoformat(sep=" ", timespec="seconds")
    success_flag = 1 if success else 0

    # Acquire lock to serialize writes across threads
    with _lock:
        conn = _get_connection()
        try:
            with conn:
                conn.execute(
                    """
                    INSERT INTO invocations (timestamp, latency_ms, success)
                    VALUES (?, ?, ?)
                    """,
                    (timestamp, latency_ms, success_flag),
                )
        except Exception as e:
            raise RuntimeError(f"Failed to record invocation: {e}")
        finally:
            conn.close()


def fetch_all_invocations() -> list[dict]:
    """
    Retrieve all invocation records from the database, ordered by ID ascending.

    Returns:
        List[dict]: A list of dictionaries, where each dictionary represents a row
                    from the 'invocations' table with keys: 'id', 'timestamp',
                    'latency_ms', and 'success'.

    Raises:
        RuntimeError: If any database read operation fails.
    """
    # Ensure the database and table exist before querying
    initialize_db()

    conn = _get_connection()
    try:
        cursor = conn.execute("SELECT * FROM invocations ORDER BY id ASC")
        rows = cursor.fetchall()
        # Convert sqlite3.Row objects into plain dictionaries
        return [dict(row) for row in rows]
    except Exception as e:
        raise RuntimeError(f"Failed to fetch invocation records: {e}")
    finally:
        conn.close()
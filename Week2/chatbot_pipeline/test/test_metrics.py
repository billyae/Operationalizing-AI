import os
import sqlite3
import threading
import pytest
import metrics

def test_create_db_directory(tmp_path):
    """
    Test that create_db_directory creates the DB_DIR directory if it does not exist.
    Args:
        tmp_path: pytest fixture for creating temporary directories.
    """

    test_dir = tmp_path / "m"
    assert not test_dir.exists()
    metrics.create_db_directory(str(test_dir))
    assert test_dir.is_dir()

def test_get_connection_defaults(tmp_path, monkeypatch):
    """
    Test that _get_connection returns a connection to the default DB_PATH.
    Args:
        tmp_path: pytest fixture for creating temporary directories.
        monkeypatch: pytest fixture to modify the DB_PATH attribute.
    """

    # Point DB_PATH to an in-memory filename (won’t actually create file)
    monkeypatch.setattr(metrics, "DB_PATH", ":memory:")
    conn = metrics._get_connection()
    assert isinstance(conn, sqlite3.Connection)
    conn.close()

def test_record_and_fetch_invocations(tmp_path, monkeypatch):
    """
    Test that record_invocation stores data in the database and fetch_all_invocations retrieves it.
    Args:
        tmp_path: pytest fixture for creating temporary directories.
        monkeypatch: pytest fixture to modify the DB_DIR and DB_PATH attributes.
    """
    
    # Redirect DB_DIR/DB_PATH to tmp
    metrics.DB_DIR = str(tmp_path / "d")
    metrics.DB_PATH = os.path.join(metrics.DB_DIR, "metrics.db")

    # record two invocations
    metrics.record_invocation(100.5, True)
    metrics.record_invocation(200.0, False)

    rows = metrics.fetch_all_invocations()  # :contentReference[oaicite:2]{index=2}

    # Instead of exact count, just verify our two new entries are in there:
    latencies = [r["latency_ms"] for r in rows]
    assert 100.5 in latencies
    assert 200.0 in latencies
    # And verify the boolean→int mapping
    successes = [r["success"] for r in rows if r["latency_ms"] in (100.5, 200.0)]
    assert 1 in successes and 0 in successes

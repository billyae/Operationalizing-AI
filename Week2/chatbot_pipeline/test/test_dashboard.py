import os
import sqlite3
import pandas as pd
import builtins
import pytest

# import the dashboard module from the monitoring folder
from monitoring import dashboard

def test_load_metrics_no_db(tmp_path, monkeypatch):
    """
    Test that load_metrics returns an empty DataFrame with the correct columns
    when the database file does not exist.
    Args:
        tmp_path: pytest fixture for creating temporary directories/files.
        monkeypatch: pytest fixture to modify the DB_PATH attribute.
    """

    # point DB_PATH at a non‐existent file
    fake_db = tmp_path / "no_such.db"
    monkeypatch.setattr(dashboard, "DB_PATH", str(fake_db))
    if fake_db.exists():
        fake_db.unlink()

    df = dashboard.load_metrics()
    # should get an empty DataFrame with the correct columns
    assert isinstance(df, pd.DataFrame)
    assert df.empty
    assert list(df.columns) == ["id", "timestamp", "latency_ms", "success"]


def test_load_metrics_with_data(tmp_path, monkeypatch):
    """
    Test that load_metrics reads the database and returns a DataFrame with the correct data.
    Args:
        tmp_path: pytest fixture for creating temporary directories/files.
        monkeypatch: pytest fixture to modify the DB_PATH attribute.
    """

    # create a real SQLite file with one row in invocations
    fake_db = tmp_path / "metrics.db"
    conn = sqlite3.connect(str(fake_db))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS invocations (
            id INTEGER PRIMARY KEY,
            timestamp TEXT,
            latency_ms REAL,
            success INTEGER
        )
    """)
    conn.execute("""
        INSERT INTO invocations (timestamp, latency_ms, success)
        VALUES ('2025-06-06 10:00:00', 1.23, 1)
    """)
    conn.commit()
    conn.close()

    monkeypatch.setattr(dashboard, "DB_PATH", str(fake_db))
    df = dashboard.load_metrics()

    assert len(df) == 1
    # pandas will parse timestamp automatically
    assert df.loc[0, "latency_ms"] == 1.23
    assert df.loc[0, "success"] == 1


def test_tail_log_no_file(monkeypatch):
    """
    Test that tail_log returns a message indicating no log file found
    when the log file does not exist.
    Args:
        monkeypatch: pytest fixture to modify the os.path.exists function.
    """

    # force the log‐file check to always say “not there”
    monkeypatch.setattr(dashboard.os.path, "exists", lambda p: False)

    out = dashboard.tail_log(5)
    assert out == ["(no log file found)"]


def test_tail_log_with_file(tmp_path, monkeypatch):
    """
    Test that tail_log reads the last n lines from the log file.
    Args:
        tmp_path: pytest fixture for creating temporary directories/files.
        monkeypatch: pytest fixture to modify the os.path.exists and open functions.
    """
    
    # write a fake log file
    fake_log = tmp_path / "bedrock_chatbot.log"
    lines = [f"entry{i}\n" for i in range(1, 7)]
    fake_log.write_text("".join(lines))

    # pretend the real log exists
    monkeypatch.setattr(dashboard.os.path, "exists", lambda p: True)

    # hijack any open() call so it always opens our fake_log
    real_open = builtins.open
    def fake_open(path, mode="r", encoding=None):
        return real_open(str(fake_log), mode, encoding=encoding)
    monkeypatch.setattr(builtins, "open", fake_open)

    # should get the last 3 lines
    out = dashboard.tail_log(3)
    assert out == lines[-3:]

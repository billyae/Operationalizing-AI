import sqlite3
import common.logger as logger_module
from common.logger import init_db, record_log, DB_FILE

def test_init_db_and_record(tmp_path, monkeypatch):
    # Redirect DB_FILE to a temp path
    fake_db = tmp_path / "audit_logs.db"
    monkeypatch.setattr(logger_module, 'DB_FILE', str(fake_db))

    # Initialize and log one entry
    init_db()
    record_log('u1', 'p1', 'r1', 12.3, True)

    # Verify insertion
    conn = sqlite3.connect(fake_db)
    cur = conn.cursor()
    cur.execute("SELECT user_id, prompt, response, latency_ms, success FROM audit_logs")
    row = cur.fetchone()
    conn.close()

    assert row[0] == 'u1'
    assert row[1] == 'p1'
    assert row[2] == 'r1'
    assert isinstance(row[3], float)
    assert row[4] == 1

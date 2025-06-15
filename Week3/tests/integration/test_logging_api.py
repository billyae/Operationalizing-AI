import sys
import sqlite3 as _sqlite
import pytest
from fastapi.testclient import TestClient

import common.logger as logger_module
sys.modules['common.logger'] = logger_module
import backend.logging_api as logging_api

DB = logger_module.DB_FILE

@pytest.fixture(autouse=True)
def clean_db(tmp_path, monkeypatch):
    """
    Fixture to clean up the database before each test.
    Parameters:
        tmp_path: pytest fixture for temporary directory
        monkeypatch: pytest fixture to patch methods
    """
    # Redirect DB_FILE and re-init the logging_api app
    fake_db = tmp_path / "audit_logs.db"
    monkeypatch.setattr(logger_module, 'DB_FILE', str(fake_db))
    import importlib
    importlib.reload(logging_api)
    yield

def test_create_and_list_log():
    """
    Test creating a log entry and listing logs.
    This test checks that a log entry can be created successfully
    and that it can be retrieved with the correct fields.
    """
    client = TestClient(logging_api.app)
    entry = {
        'user_id':'u','prompt':'p',
        'response':'r','latency_ms':10.5,'success':True
    }
    # POST /log
    r1 = client.post("/log", json=entry)
    assert r1.status_code == 201
    assert r1.json() == {'status':'success'}

    # GET /logs
    r2 = client.get("/logs?limit=1")
    assert r2.status_code == 200
    data = r2.json()
    assert len(data) == 1
    got = data[0]
    assert got['user_id']=='u'
    assert got['prompt']=='p'
    assert got['response']=='r'
    assert got['latency_ms']==10.5
    assert got['success']==True

def test_list_logs_db_error(monkeypatch):
    """
    Test that listing logs returns 500 when there is a database error.
    Parameters:
        monkeypatch: pytest fixture to patch methods
    """
    
    # Patch the sqlite connect method to raise an error
    monkeypatch.setattr(_sqlite, 'connect',
                        lambda *a, **k: (_ for _ in ()).throw(_sqlite.Error("err")))
    client = TestClient(logging_api.app)
    r = client.get("/logs")
    assert r.status_code == 500
    assert 'DB error' in r.json()['detail']

import sqlite3
from typing import List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from common.logger import init_db, record_log, DB_FILE

app = FastAPI(title="Audit Logging Service")

# Ensure the DB and table exist when the service starts
init_db()

class LogEntry(BaseModel):
    user_id: str
    prompt: str
    response: str
    latency_ms: float
    success: bool

@app.post("/log", status_code=201)
def create_log(entry: LogEntry):
    """
    Receive an audit log entry (with performance metrics) and store it.
    """
    record_log(
        user_id=entry.user_id,
        prompt=entry.prompt,
        response=entry.response,
        latency_ms=entry.latency_ms,
        success=entry.success
    )
    return {"status": "success"}

@app.get("/logs", response_model=List[LogEntry])
def list_logs(limit: int = 100):
    """
    Retrieve the most recent audit log entries.

    :param limit: Maximum number of entries to return (default: 100).
    """
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT user_id, prompt, response, latency_ms, success
                FROM audit_logs
                ORDER BY id DESC
                LIMIT ?
            ''', (limit,))
            rows = cursor.fetchall()
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"DB error: {e}")

    return [
        LogEntry(
            user_id=row[0],
            prompt=row[1],
            response=row[2],
            latency_ms=row[3],
            success=bool(row[4])
        )
        for row in rows
    ]

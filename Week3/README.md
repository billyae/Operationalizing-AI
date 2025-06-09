# Enterprise Bedrock Chatbot

A lightweight chat service powered by Amazon Bedrock, with end-to-end audit logging (including performance metrics) persisted to SQLite and streamed to console, plus a Streamlit frontend.

---

## Table of Contents

1. [Features](#features)  
2. [Architecture](#architecture)  
3. [Prerequisites](#prerequisites)  
4. [Installation](#installation)  
5. [Running the Services](#running-the-services)  
6. [API Reference](#api-reference)  
7. [Streamlit Frontend](#streamlit-frontend)  
8. [Audit Logs](#audit-logs)  
9. [Deployment](#deployment)  
10. [License](#license)  

---

## Features

- **Chat API** – FastAPI-based endpoint that authenticates AWS credentials, invokes a Bedrock chat model, measures latency, and returns the assistant’s reply.  
- **Audit Logging API** – FastAPI-based service that stores each interaction (user ID, prompt, response, latency, success flag) into SQLite.  
- **Console Logging** – Each audit entry is also emitted to console via Python’s `logging` module.  
- **Streamlit Frontend** – Simple UI for entering AWS keys, sending chat messages, and viewing replies in context.  

---

## Architecture

```text
┌─────────────────┐      ┌─────────────────────┐      ┌─────────────────┐
│ Streamlit UI    │  →   │ Chat API (FastAPI)  │  →   │ Bedrock Client  │
│ (app.py)        │      │ (/chat)             │      │ (invoke model)  │
└─────────────────┘      └─────────────────────┘      └─────────────────┘
       │                        │
       ↓                        ↓
┌─────────────────┐      ┌─────────────────────┐
│ Logging API     │◀─────┤ Chat API sends log  │
│ (/log, /logs)   │      └─────────────────────┘
└─────────────────┘
       │
       ↓
┌─────────────────┐
│ SQLite DB       │
│ (audit_logs.db) │
└─────────────────┘
```
- common/logger.py

    - init_db() migrates/creates the audit_logs table.

    - record_log() persists and prints each entry.

- logging_api.py

    -  /log to ingest audit entries.
    -  /logs to retrieve recent entries.

- chat_api.py
    - /chat endpoint handles chat flow and posts audit logs.

- app.py
    - Streamlit UI wiring chat to /chat.

## Prerequisites

- Python ≥ 3.10

- pip

- SQLite3 (bundled on most systems)

- AWS IAM keys with bedrock:InvokeModel permission

- Network access to AWS Bedrock

## Installation

```bash
git clone <your-repo-url>
cd <your-repo-dir>
python -m venv venv
source venv/bin/activate     # Windows: venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Running the Services

Open three terminals (or use tmux/docker-compose):  

### 1.Audit Logging API

``` uvicorn logging_api:app --host 0.0.0.0 --port 8001 --reload ```

### 2. Chat API

``` uvicorn chat_api:app --host 0.0.0.0 --port 8000 --reload ```

### 3. Streamlit Frontend

```streamlit run app.py --server.port 8501```

## API Reference

### Chat API

- POST /chat    

```json
// Request Body
{
  "user_id":     "alice",
  "access_key":  "AKIA…",
  "secret_key":  "…",
  "region":      "us-east-1",
  "messages": [
    {"role":"system","content":"Authenticate"},
    {"role":"user","content":"Hello"}
  ]
}
```

- Response
    
``` { "response": "Hi there, how can I help?" }```

### Logging API

- POST /log   

```json
{
  "user_id":    "alice",
  "prompt":     "Hello",
  "response":   "Hi there!",
  "latency_ms": 123.4,
  "success":    true
}
```

- GET /logs?limit=50
Returns the most recent 50 entries.

## Streamlit Frontend

- Enter your AWS keys in the sidebar.

- Type messages in the chat input.

- Replies display chronologically.

## Audit Logs

- Stored in audit_logs.db (SQLite).

- Table schema (automatically migrated by init_db()):

    ```id | timestamp | user_id | prompt | response | latency_ms | success```

- onsole logs appear at INFO level:

    ```YYYY-MM-DD HH:MM:SS [Audit] user='alice' prompt='Hello' latency=123.4ms success=True```

## Deployment

See deployment_guide.md for Docker-Compose, environment setup, and service orchestration.    

## License

This project is licensed under the MIT License.


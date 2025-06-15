# Deployment Guide

This document walks through deploying the Audit-Logging & Chat system.

## 1. Prerequisites

- **Python** ≥3.10  
- **pip** (or an alternative package manager)  
- **SQLite3** (bundled with most OSes)  
- **AWS Credentials** with permission to invoke Bedrock models  
- **Network**: outbound HTTPS access to AWS Bedrock endpoints

## 2. Repository Setup

```bash
git clone <your-repo-url>
cd <your-repo-dir>
python -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 3. Database Initialization

The logging service auto-migrates on start (via common/logger.init_db()).    
To force a fresh schema (and wipe old logs), delete the file:   

```rm audit_logs.db    # or del audit_logs.db on Windows```

## 4. Running Services

### Audit Logging API

```uvicorn logging_api:app --host 0.0.0.0 --port 8001 --reload```

### Chat API

```uvicorn chat_api:app --host 0.0.0.0 --port 8000 --reload```

### Streamlit Frontend

```streamlit run app.py --server.port 8501```

## 5. Run the Test with Coverage Report

```python -m pytest tests --disable-warnings --cov=./ --cov-report=term-missing ```



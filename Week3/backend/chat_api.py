import os
import time
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any, Dict
from common.auth import authenticate_aws
from common.bedrock_client import invoke_chat_model

app = FastAPI(title="Chat Service")

MODEL_ID      = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0")
DEFAULT_REGION= os.getenv("AWS_REGION", "us-east-1")
LOGGING_URL   = os.getenv("LOGGING_SERVICE_URL", "http://localhost:8001/log")

class ChatRequest(BaseModel):
    user_id: str
    access_key: str
    secret_key: str
    region: str = DEFAULT_REGION
    messages: list

def send_audit_log(entry: Dict[str, Any]) -> None:
    """
    Best-effort send of audit log entry (with performance metrics) to logging service.
    """
    try:
        resp = requests.post(LOGGING_URL, json=entry, timeout=2)
        resp.raise_for_status()
    except requests.RequestException:
        # Silently ignore logging failures
        pass

@app.post("/chat")
def chat(request: ChatRequest) -> Dict[str, str]:
    """
    1) Authenticate AWS credentials
    2) Invoke the Bedrock chat model (measure latency)
    3) Send audit log (user_id, prompt, response, latency_ms, success)
    4) Return the assistant's response or error
    """
    # Validate credentials
    if not authenticate_aws(request.access_key, request.secret_key, request.region):
        raise HTTPException(status_code=401, detail="Invalid AWS credentials")

    # Invoke model and measure performance
    start = time.perf_counter()
    try:
        reply = invoke_chat_model(
            request.access_key,
            request.secret_key,
            request.region,
            MODEL_ID,
            request.messages
        )
        success = True
    except Exception as e:
        reply = str(e)
        success = False
    latency_ms = (time.perf_counter() - start) * 1000

    # Audit logging
    last_prompt = request.messages[-1].get("content", "")
    log_entry = {
        "user_id":    request.user_id,
        "prompt":     last_prompt,
        "response":   reply,
        "latency_ms": latency_ms,
        "success":    success
    }
    send_audit_log(log_entry)

    # Return or error
    if not success:
        raise HTTPException(status_code=500, detail=reply)

    return {"response": reply}

# invoke_bedrock_handler.py

import os
import json
import time
import boto3

bedrock = boto3.client("bedrock-runtime")  # Bedrock client

MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-sonnet")  # or whichever

def lambda_handler(event, context):
    """
    event = {
       "bedrock_input": {"prompt": "..."},
       "meta": {"original_key": "raw/some_input.json"}
    }
    """
    bedrock_input = event["bedrock_input"]
    meta = event["meta"]
    
    start_time = time.time()
    try:
        response = bedrock.invoke_model(
            modelId=MODEL_ID,
            body=json.dumps({
                "inputText": bedrock_input["prompt"]
                # Include other parameters your model expects
            }).encode("utf‑8"),
            contentType="application/json",
            accept="application/json"
        )
        latency_ms = int((time.time() - start_time) * 1000)
        response_body = json.loads(response["body"].read().decode("utf‑8"))
        
        return {
            "bedrock_response": response_body,
            "latency_ms": latency_ms,
            "meta": meta
        }
    except Exception as e:
        # In Step Functions, you can catch this exception and trigger retry or failure path
        raise RuntimeError(f"Bedrock invocation failed: {str(e)}")

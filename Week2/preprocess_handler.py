# preprocess_handler.py

import json
import boto3
import os

s3 = boto3.client("s3")

def lambda_handler(event, context):
    """
    event = {
      "bucket": "my‑ai‑pipeline‑bucket",
      "key": "raw/some_input.json"
    }
    """
    bucket = event["bucket"]
    key = event["key"]
    
    # 1. Fetch raw data
    obj = s3.get_object(Bucket=bucket, Key=key)
    raw_body = obj["Body"].read().decode("utf‑8")
    payload = json.loads(raw_body)
    
    # 2. Normalize / Clean / Tokenize
    # (For example, ensure a "prompt" field exists)
    text = payload.get("text", "")
    cleaned_text = text.strip()  # basic example
    bedrock_payload = {
        "prompt": f"Please analyze: {cleaned_text}"
    }
    
    # 3. Return the payload for the next Step Functions state
    return {
        "bedrock_input": bedrock_payload,
        "meta": {"original_key": key}
    }
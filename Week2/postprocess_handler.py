# postprocess_handler.py

import json
import boto3
import os

s3 = boto3.client("s3")

OUTPUT_BUCKET = os.getenv("OUTPUT_BUCKET", "my‑ai‑pipeline‑bucket")
OUTPUT_PREFIX = "processed/"

def lambda_handler(event, context):
    """
    event = {
      "bedrock_response": {"completion": "..."},
      "latency_ms": 123,
      "meta": {"original_key": "raw/some_input.json"}
    }
    """
    bedrock_response = event["bedrock_response"]
    latency = event["latency_ms"]
    meta = event["meta"]
    
    # Extract model’s answer
    answer = bedrock_response.get("completion", "")
    result_payload = {
        "answer": answer,
        "latency_ms": latency,
        "source": meta["original_key"]
    }
    
    # Derive output key
    original_key = meta["original_key"]  # e.g. "raw/some_input.json"
    filename = os.path.basename(original_key)
    output_key = OUTPUT_PREFIX + filename.replace("raw/", "").replace(".json", "_result.json")
    
    # Store result
    s3.put_object(
        Bucket=OUTPUT_BUCKET,
        Key=output_key,
        Body=json.dumps(result_payload).encode("utf‑8"),
        ContentType="application/json"
    )
    
    return {
        "status": "SUCCESS",
        "output_key": output_key,
        "meta": meta
    }

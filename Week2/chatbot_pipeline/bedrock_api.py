import os
import logging
import json

from dotenv import load_dotenv
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

# ──────────────────────────────────────────────────────────────────────────────
# 1) Load environment variables from .env
# ──────────────────────────────────────────────────────────────────────────────
load_dotenv()  # Reads .env in the same folder

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_SESSION_TOKEN = os.getenv("AWS_SESSION_TOKEN")  # if you use temporary STS tokens
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
    raise RuntimeError(
        "Missing AWS credentials. "
        "Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in your .env file."
    )

# ──────────────────────────────────────────────────────────────────────────────
# 2) Configure logging
# ──────────────────────────────────────────────────────────────────────────────
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# 3) Create a Bedrock Runtime client with custom timeouts (disable boto3 retries)
# ──────────────────────────────────────────────────────────────────────────────
BOTTLENECK_CONFIG = Config(
    retries={"max_attempts": 1},  # Turn off boto3 automatic retries
    read_timeout=60,
    connect_timeout=5,
)

client = boto3.client(
    "bedrock-runtime",
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    aws_session_token=AWS_SESSION_TOKEN,
    config=BOTTLENECK_CONFIG,
)

# ──────────────────────────────────────────────────────────────────────────────
# 4) query_bedrock(...) with Tenacity retry and proper JSON→bytes conversion
# ──────────────────────────────────────────────────────────────────────────────


def format_for_claude(raw_input: str) -> str:
    # Always prefix with “Human:” and suffix with “\nAssistant:”
    # so that Claude knows where the user stops and the assistant should begin.
    return f"Human: {raw_input}\nAssistant:"

@retry(
    reraise=True,
    retry=retry_if_exception_type(ClientError),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
)
def query_bedrock(prompt: str) -> str:
    """
    Send `prompt` to Amazon Bedrock and return the generated completion.
    Retries up to 3 times (on ClientError) with exponential backoff.
    """
    # 1) Build a Python dict, then JSON-serialize + encode to bytes:
    payload_dict = {
        # NOTE: wrap the user’s text using the “Human:” / “Assistant:” pattern:
        "prompt": format_for_claude(prompt),
        "max_tokens_to_sample": 512,
        "temperature": 0.7,
    }
    payload_json = json.dumps(payload_dict)
    payload_bytes = payload_json.encode("utf-8")

    try:
        response = client.invoke_model(
            modelId="anthropic.claude-3-sonnet-20240229-v1:0",       # ← Change to your chosen Bedrock model
            body=payload_bytes,
            contentType="application/json",
            accept="application/json",
        )
    except ClientError as e:
        logger.warning(f"Bedrock ClientError (will retry): {e}")
        raise  # Tenacity sees this and retries up to 3 total attempts

    # 2) Parse the JSON body from the response (response["body"] is a StreamingBody)
    raw_body = response["body"].read().decode("utf-8")
    try:
        parsed = json.loads(raw_body)
    except json.JSONDecodeError:
        logger.error(f"Failed to parse JSON from Bedrock response: {raw_body}")
        raise RuntimeError("Invalid JSON response from Bedrock")

    if "completion" not in parsed:
        logger.error(f"Bedrock response missing 'completion' key: {parsed}")
        raise RuntimeError("Bedrock returned no 'completion' field")

    return parsed["completion"]

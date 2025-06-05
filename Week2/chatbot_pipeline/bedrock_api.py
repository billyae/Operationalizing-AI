import os
import json
import logging

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

# Configure a shared Botocore Config to limit automatic retries and set timeouts
BOTTLENECK_CONFIG = Config(
    retries={"max_attempts": 1},  # Disable boto3’s own retry logic
    read_timeout=60,
    connect_timeout=5,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def build_anthropic_payload(full_history: list[dict[str,str]]) -> list[dict[str,str]]:
    """
    Ensure that the first element we pass to Bedrock is always a user turn.
    If the history begins with an assistant turn, drop it here.
    """
    if not full_history:
        return full_history

    # If first turn is assistant, drop it so Bedrock sees a user first.
    if full_history[0]["role"] == "assistant":
        return full_history[1:]
    return full_history


def get_bedrock_client() -> boto3.client:
    """
    Create and return a new boto3 Bedrock Runtime client using AWS credentials
    pulled from environment variables. Raises RuntimeError if credentials are missing.

    Environment variables expected:
      - AWS_ACCESS_KEY_ID
      - AWS_SECRET_ACCESS_KEY
      - AWS_SESSION_TOKEN (optional)
      - AWS_REGION (optional; defaults to 'us-east-1')
    """
    aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    aws_session_token = os.getenv("AWS_SESSION_TOKEN")  # Optional
    aws_region = os.getenv("AWS_REGION", "us-east-1")

    if not aws_access_key_id or not aws_secret_access_key:
        raise RuntimeError(
            "Missing AWS credentials. "
            "Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY "
            "before calling query_bedrock()."
        )

    # Instantiate a fresh Bedrock client with the current environment’s credentials
    return boto3.client(
        "bedrock-runtime",
        region_name=aws_region,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        aws_session_token=aws_session_token,
        config=BOTTLENECK_CONFIG,
    )


@retry(
    reraise=True,
    retry=retry_if_exception_type(ClientError),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
)
def query_bedrock(messages: list[dict[str, str]]) -> str:
    """
    Send a sequence of chat messages to Amazon Bedrock (Claude model) and return
    the model’s assistant reply as a string. Retries up to 3 times on ClientError.

    Args:
        messages: A list of dictionaries, each with keys:
                  - "role": either "user" or "assistant"
                  - "content": the text string for that turn

    Returns:
        The assistant-generated reply (string).

    Raises:
        RuntimeError: If the Bedrock response cannot be parsed or contains no completion.
        ClientError: Propagated from the boto3 client if the invoke_model call fails.
    """
    client = get_bedrock_client()

    # Construct the JSON payload in Anthropic chat format
    payload = {
        "anthropic_version": "bedrock-2023-05-31",
        "messages": build_anthropic_payload(messages),
        "max_tokens": 512,
        "temperature": 0.7,
    }
    body_bytes = json.dumps(payload).encode("utf-8")

    try:
        response = client.invoke_model(
            modelId="anthropic.claude-3-sonnet-20240229-v1:0",  # Change modelId if needed
            body=body_bytes,
            contentType="application/json",
            accept="application/json",
        )
    except ClientError as e:
        # Let Tenacity retry on ClientError
        logger.warning(f"Bedrock ClientError (will retry): {e}")
        raise

    raw_body = response["body"].read().decode("utf-8")
    try:
        parsed = json.loads(raw_body)
    except json.JSONDecodeError:
        logger.error(f"Unable to parse JSON from Bedrock response: {raw_body}")
        raise RuntimeError("Invalid JSON response from Bedrock.")

    # Legacy top-level "completion" key
    if "completion" in parsed:
        return parsed["completion"]

    # Anthropic chat-style "content" array
    if "content" in parsed and isinstance(parsed["content"], list):
        text_chunks = [
            chunk["text"]
            for chunk in parsed["content"]
            if chunk.get("type") == "text" and "text" in chunk
        ]
        reply = "".join(text_chunks)
        if reply:
            return reply
        else:
            logger.error(f"Bedrock 'content' field empty: {parsed['content']}")
            raise RuntimeError("Bedrock returned no usable 'content' text.")

    # Fallback "choices" array (alternate schema)
    if "choices" in parsed and parsed["choices"]:
        first_choice = parsed["choices"][0]
        message_obj = first_choice.get("message", {})
        content = message_obj.get("content")
        if content is not None:
            return content

    # If none of the expected keys were found, report an error
    logger.error(f"Bedrock response did not include a valid completion: {parsed}")
    raise RuntimeError("Bedrock returned no usable completion.")

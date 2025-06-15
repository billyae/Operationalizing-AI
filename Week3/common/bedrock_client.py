import json
import boto3
from botocore.exceptions import ClientError
from botocore.config import Config

# ─── Default parameters for Anthropic models ───────────────────────────────────
_ANTHROPIC_VERSION    = "2023-05-31"
_MAX_TOKENS           = 512
_TEMPERATURE          = 0.7
_RETRIES              = {"max_attempts": 1}
_READ_TIMEOUT         = 60
_CONNECT_TIMEOUT      = 5


def invoke_chat_model(
    access_key: str,
    secret_key: str,
    region: str,
    model_id: str,
    messages: list,
    anthropic_version: str = _ANTHROPIC_VERSION,
    max_tokens_to_sample: int = _MAX_TOKENS,
    temperature: float = _TEMPERATURE
) -> str:
    """
    Invoke an Anthropic chat model on Amazon Bedrock and return its reply.

    :param access_key:           AWS Access Key ID
    :param secret_key:           AWS Secret Access Key
    :param region:               AWS Region (e.g. "us-east-1")
    :param model_id:             Bedrock model identifier (e.g. "anthropic.claude-3")
    :param messages:             List of dicts [{"role":"system|user|assistant", "content":...}, ...]
    :param anthropic_version:    Anthropic API version (will be prefixed with "bedrock-")
    :param max_tokens_to_sample: Maximum tokens to generate
    :param temperature:          Sampling temperature
    :returns:                    The assistant’s reply string
    :raises RuntimeError:        On invocation failure or unrecognized response shape
    """

    # Separate system prompt and prepare message list
    system_prompt = None
    chat_messages = []
    for m in messages:
        role = m.get("role")
        content = m.get("content")
        if role == "system":
            system_prompt = content
        else:
            chat_messages.append({"role": role, "content": content})

    # Ensure the first message is from the user by dropping any leading non-user turns
    while chat_messages and chat_messages[0].get("role") != "user":
        chat_messages.pop(0)

    if not chat_messages or chat_messages[0].get("role") != "user":
        raise RuntimeError("No user message found in the conversation to send to Anthropic Claude.")

    # Build the native Bedrock request body
    ver = anthropic_version
    if not ver.startswith("bedrock-"):
        ver = f"bedrock-{ver}"

    body = {
        "anthropic_version": ver,
        "max_tokens":        max_tokens_to_sample,
        "temperature":       temperature,
        "messages":          chat_messages,
    }
    if system_prompt is not None:
        body["system"] = system_prompt

    body_bytes = json.dumps(body).encode("utf-8")

    # Create Bedrock Runtime client
    try:
        client = boto3.client(
            "bedrock-runtime",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
            config=Config(
                retries=_RETRIES,
                read_timeout=_READ_TIMEOUT,
                connect_timeout=_CONNECT_TIMEOUT
            )
        )
    except ClientError as e:
        raise RuntimeError(f"Anthropic invocation failed: {e}")

    try:
        # Invoke the model
        resp = client.invoke_model(
            modelId=model_id,
            contentType="application/json",
            accept="application/json",
            body=body_bytes
        )

        # Read and parse the response
        raw = resp["body"].read().decode("utf-8")
        data = json.loads(raw)

        # Legacy completions API
        if "completions" in data:
            return data["completions"][0]["completion"]
        if "completion" in data:
            return data["completion"]

        # Messages API → top-level "content" blocks
        if "content" in data and isinstance(data["content"], list):
            return "".join(
                block.get("text", "")
                for block in data["content"]
                if block.get("type") == "text"
            )

        # Alternative: top-level "messages" list
        if "messages" in data and isinstance(data["messages"], list):
            for msg in data["messages"]:
                if msg.get("role") == "assistant":
                    c = msg.get("content")
                    if isinstance(c, list):
                        return "".join(
                            block.get("text", "")
                            for block in c
                            if block.get("type") == "text"
                        )
                    elif isinstance(c, str):
                        return c
            first = data["messages"][0].get("content")
            return first if isinstance(first, str) else ""

        raise RuntimeError(f"Unrecognized Anthropic response shape: {data}")

    except ClientError as e:
        raise RuntimeError(f"Anthropic invocation failed: {e}")

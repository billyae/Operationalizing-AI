import os
import json
import pytest
import boto3
import bedrock_api

class FakeBody:
    """
    Stub for the HTTP response body returned by boto3.invoke_model.
    Holds raw bytes and returns them when `.read()` is called.
    """
    def __init__(self, data):
        self._data = data

    def read(self):
        return self._data


class FakeClient:
    """
    Stub for a boto3 client. 
    Always returns a FakeBody wrapping the provided raw bytes.
    """
    def __init__(self, raw):
        self.raw = raw

    def invoke_model(self, **kwargs):
        # Simulate the structure {"body": <file-like>}
        return {"body": FakeBody(self.raw)}


def make_fake(monkeypatch, raw_bytes):
    """
    Helper to:
      1) Ensure AWS credentials are present in the env
      2) Monkeypatch boto3.client(...) → FakeClient(raw_bytes)
    """
    # Set up valid credentials in environment
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "AK")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "SK")
    # Remove any session token so it’s optional
    monkeypatch.delenv("AWS_SESSION_TOKEN", raising=False)

    def fake_client(service, **kw):
        # Ignore service name / kwargs, always return our stub
        return FakeClient(raw_bytes)

    # Patch boto3.client globally within the test
    monkeypatch.setattr(boto3, "client", fake_client)


def test_missing_credentials(monkeypatch):
    """
    If AWS_ACCESS_KEY_ID or AWS_SECRET_ACCESS_KEY are not set,
    query_bedrock should raise a RuntimeError.
    """
    monkeypatch.delenv("AWS_ACCESS_KEY_ID", raising=False)
    monkeypatch.delenv("AWS_SECRET_ACCESS_KEY", raising=False)

    with pytest.raises(RuntimeError):
        bedrock_api.query_bedrock([{"role": "user", "content": "x"}])


def test_query_bedrock_completion_key(monkeypatch):
    """
    When the response JSON has a top-level "completion" field,
    its value should be returned directly.
    """
    # Simulate {"completion": "hey"}
    raw = json.dumps({"completion": "hey"}).encode()
    make_fake(monkeypatch, raw)

    result = bedrock_api.query_bedrock([{"role": "user", "content": "x"}])
    assert result == "hey"


def test_query_bedrock_content_chunks(monkeypatch):
    """
    When the response JSON has a "content" array of text chunks,
    they should be concatenated in order.
    """
    payload = {
        "content": [
            {"type": "text", "text": "a"},
            {"type": "text", "text": "b"},
        ]
    }
    raw = json.dumps(payload).encode()
    make_fake(monkeypatch, raw)

    result = bedrock_api.query_bedrock([{"role": "user", "content": "x"}])
    assert result == "ab"


def test_query_bedrock_choices_fallback(monkeypatch):
    """
    If neither "completion" nor "content" is present,
    fallback to reading from payload["choices"][0]["message"]["content"].
    """
    payload = {"choices": [{"message": {"content": "z"}}]}
    raw = json.dumps(payload).encode()
    make_fake(monkeypatch, raw)

    result = bedrock_api.query_bedrock([{"role": "user", "content": "x"}])
    assert result == "z"


def test_invalid_json(monkeypatch):
    """
    If the service returns invalid JSON, query_bedrock should
    raise a RuntimeError rather than crash.
    """
    make_fake(monkeypatch, b"not-json")

    with pytest.raises(RuntimeError):
        bedrock_api.query_bedrock([{"role": "user", "content": "x"}])


def test_no_expected_field(monkeypatch):
    """
    If the JSON is valid but contains none of the expected keys
    ("completion", "content", "choices"), we should also get a RuntimeError.
    """
    make_fake(monkeypatch, json.dumps({}).encode())

    with pytest.raises(RuntimeError):
        bedrock_api.query_bedrock([{"role": "user", "content": "x"}])
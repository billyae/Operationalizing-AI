import pytest
import common.auth as auth
from botocore.exceptions import ClientError

def test_authenticate_aws_success(monkeypatch):
    # Simulate boto3.client not raising
    class DummyClient: pass
    monkeypatch.setattr(auth.boto3, 'client', lambda *a, **k: DummyClient())
    assert auth.authenticate_aws('a', 'b', 'c') is True

def test_authenticate_aws_failure(monkeypatch):
    # Simulate boto3.client raising ClientError
    def fake_client(*a, **k):
        raise ClientError({'Error': {}}, 'op')
    monkeypatch.setattr(auth.boto3, 'client', fake_client)
    assert auth.authenticate_aws('a', 'b') is False

import pytest
from fastapi.testclient import TestClient
import backend.chat_api as chat_api

@pytest.fixture(autouse=True)
def no_external(monkeypatch):
    """
    Patch out external requests to avoid network calls during tests.
    Parameters:
        monkeypatch: pytest fixture to patch methods
    
    """

    # Patch the requests.post method to return a mock response
    monkeypatch.setattr(chat_api.requests, 'post',
                        lambda *a, **k: type('R',(),{'raise_for_status':lambda self: None})())
    yield

def test_chat_unauthorized(monkeypatch):
    """
    Test that chat endpoint returns 401 when AWS credentials are invalid.
    Parameters:
        monkeypatch: pytest fixture to patch methods
    """

    # Patch the authenticate_aws method to return False
    monkeypatch.setattr(chat_api,    'authenticate_aws', lambda *a,**k: False)
    client = TestClient(chat_api.app)
    r = client.post("/chat", json={
        'user_id':'u','access_key':'a','secret_key':'s',
        'region':'r','messages':[{'role':'user','content':'hi'}]
    })
    assert r.status_code == 401
    assert r.json()['detail']=='Invalid AWS credentials'

def test_chat_invocation_failure(monkeypatch):
    """
    Test that chat endpoint returns 500 when invoking the chat model fails.
    Parameters:
        monkeypatch: pytest fixture to patch methods
    """

    # Patch the authenticate_aws method to return True and invoke_chat_model to raise an exception
    monkeypatch.setattr(chat_api, 'authenticate_aws', lambda *a: True)
    monkeypatch.setattr(chat_api,    'invoke_chat_model',
                        lambda *a, **k: (_ for _ in ()).throw(Exception("fail")))

    client = TestClient(chat_api.app)
    r = client.post("/chat", json={
        'user_id':'u','access_key':'a','secret_key':'s',
        'region':'r','messages':[{'role':'user','content':'hi'}]
    })
    assert r.status_code == 500
    assert 'fail' in r.json()['detail']

def test_chat_success(monkeypatch):
    """
    Test that chat endpoint returns 200 and a valid response when everything works.
    Parameters:
        monkeypatch: pytest fixture to patch methods
    """

    # Patch the authenticate_aws method to return True and invoke_chat_model to return a mock response
    monkeypatch.setattr(chat_api, 'authenticate_aws', lambda *a: True)
    monkeypatch.setattr(chat_api, 'invoke_chat_model', lambda *a, **k: "reply")
    client = TestClient(chat_api.app)
    r = client.post("/chat", json={
        'user_id':'u','access_key':'a','secret_key':'s',
        'region':'r','messages':[{'role':'user','content':'hi'}]
    })
    assert r.status_code == 200
    assert r.json() == {'response':'reply'}""

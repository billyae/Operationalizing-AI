import pytest
import json
from botocore.exceptions import ClientError
import common.bedrock_client as bedrock_client

class DummyBody:
    def __init__(self, data): self._data = data
    def read(self): return json.dumps(self._data).encode('utf-8')

class DummyClient:
    def __init__(self, resp): self.resp = resp
    def invoke_model(self, **_): return {'body': DummyBody(self.resp)}

@pytest.fixture(autouse=True)
def patch_boto(monkeypatch):
    # Patch boto3.client to return DummyClient using monkeypatch._response
    monkeypatch.setattr(bedrock_client.boto3, 'client',
                        lambda *a, **k: DummyClient(monkeypatch._response))
    return monkeypatch

def test_invoke_with_completion(monkeypatch):
    monkeypatch._response = {'completion': 'hello'}
    assert bedrock_client.invoke_chat_model('a','b','r','m',
        [{'role':'user','content':'hi'}]) == 'hello'

def test_invoke_with_completions(monkeypatch):
    monkeypatch._response = {'completions': [{'completion':'world'}]}
    assert bedrock_client.invoke_chat_model('a','b','r','m',
        [{'role':'user','content':'hi'}]) == 'world'

def test_invoke_with_content_list(monkeypatch):
    monkeypatch._response = {'content': [
        {'type':'text','text':'foo'},
        {'type':'text','text':'bar'}
    ]}
    assert bedrock_client.invoke_chat_model('a','b','r','m',
        [{'role':'user','content':'hi'}]) == 'foobar'

def test_invoke_with_messages_list(monkeypatch):
    monkeypatch._response = {'messages':[{'role':'assistant','content':'resp'}]}
    assert bedrock_client.invoke_chat_model('a','b','r','m',
        [{'role':'user','content':'hi'}]) == 'resp'

def test_invoke_no_user_message(monkeypatch):
    with pytest.raises(RuntimeError):
        bedrock_client.invoke_chat_model('a','b','r','m',
            [{'role':'assistant','content':'x'}])

def test_invoke_unrecognized_shape(monkeypatch):
    monkeypatch._response = {'unknown':'x'}
    with pytest.raises(RuntimeError) as e:
        bedrock_client.invoke_chat_model('a','b','r','m',
            [{'role':'user','content':'hi'}])
    assert 'Unrecognized Anthropic response shape' in str(e.value)

def test_invoke_client_error(monkeypatch):
    # Patch client.invoke_model to throw ClientError
    monkeypatch.setattr(bedrock_client.boto3, 'client',
                        lambda *a, **k: (_ for _ in ()).throw(ClientError({}, 'op')))
    with pytest.raises(RuntimeError) as e:
        bedrock_client.invoke_chat_model('a','b','r','m',
            [{'role':'user','content':'hi'}])
    assert 'Anthropic invocation failed' in str(e.value)

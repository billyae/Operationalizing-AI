import math
import pytest
from fastapi.testclient import TestClient

def test_embed_text_success(text_client: TestClient):
    """
    Posting JSON {"text": "..."} returns a normalized embedding.
    """
    response = text_client.post(
        "/embed_text/",
        json={"text": "hello world"},
    )
    assert response.status_code == 200, response.text

    data = response.json()
    assert "embedding" in data
    emb = data["embedding"]
    assert isinstance(emb, list)
    # CLIP base text embedding is 512 dims
    assert len(emb) == 512

    # Check L2–norm ~ 1
    norm = math.sqrt(sum(x * x for x in emb))
    assert pytest.approx(norm, rel=1e-3) == 1.0

@pytest.mark.parametrize("payload", [
    {},                 # missing key
    {"text": 123},      # wrong type
])
def test_embed_text_bad_request(text_client: TestClient, payload):
    """
    Invalid JSON or wrong types should yield a 422 Unprocessable Entity.
    """
    response = text_client.post("/embed_text/", json=payload)
    assert response.status_code == 422

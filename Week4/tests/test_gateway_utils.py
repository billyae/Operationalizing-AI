# tests/test_gateway_utils.py

import io
import pytest
import numpy as np
import httpx
from fastapi import HTTPException

from app.gateway import (
    fetch_image_embedding,
    fetch_text_embedding,
    cosine_similarity,
    IMAGE_SVC,
    TEXT_SVC,
)

class DummyUpload:
    """
    Minimal stand-in for FastAPI's UploadFile:
    only supports `.filename`, `.content_type`, and async `.read()`.
    """
    def __init__(self, data: bytes = b"abc"):
        self.filename = "file.png"
        self.content_type = "image/png"
        self._data = data

    async def read(self) -> bytes:
        return self._data

class DummyResponse:
    """
    Dummy for httpx.Response-like object with status_code and json().
    """
    def __init__(self, status_code: int, payload: dict):
        self.status_code = status_code
        self._payload = payload

    def json(self) -> dict:
        return self._payload

# -------------------------------------------------------------------
# Tests for fetch_image_embedding
# -------------------------------------------------------------------

@pytest.mark.asyncio
async def test_fetch_image_embedding_success(monkeypatch):
    """
    When the image service returns 200 + a JSON 'embedding' list,
    fetch_image_embedding should return a NumPy array of that list.
    """
    dummy_file = DummyUpload(b"\x89PNG...")

    expected = [0.1, 0.2, 0.3]
    async def fake_post(self, url, **kwargs):
        # Assert correct target URL
        assert url == f"{IMAGE_SVC}/embed/"
        return DummyResponse(200, {"embedding": expected})

    # Patch AsyncClient.post
    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

    arr = await fetch_image_embedding(dummy_file)
    assert isinstance(arr, np.ndarray)
    assert arr.tolist() == expected

@pytest.mark.asyncio
async def test_fetch_image_embedding_http_error(monkeypatch):
    """
    If the image service returns non-200, fetch_image_embedding must
    raise an HTTPException(502).
    """
    dummy_file = DummyUpload()

    async def fake_post(self, url, **kwargs):
        return DummyResponse(500, {})

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

    with pytest.raises(HTTPException) as exc_info:
        await fetch_image_embedding(dummy_file)
    assert exc_info.value.status_code == 502

# -------------------------------------------------------------------
# Tests for fetch_text_embedding
# -------------------------------------------------------------------

@pytest.mark.asyncio
async def test_fetch_text_embedding_success(monkeypatch):
    """
    When the text service returns 200 + a JSON 'embedding' list,
    fetch_text_embedding should return a NumPy array of that list.
    """
    expected = [0.4, 0.5, 0.6]
    async def fake_post(self, url, **kwargs):
        assert url == f"{TEXT_SVC}/embed_text/"
        return DummyResponse(200, {"embedding": expected})

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

    arr = await fetch_text_embedding("hello")
    assert isinstance(arr, np.ndarray)
    assert arr.tolist() == expected

@pytest.mark.asyncio
async def test_fetch_text_embedding_http_error(monkeypatch):
    """
    If the text service returns non-200, fetch_text_embedding must
    raise an HTTPException(502).
    """
    async def fake_post(self, url, **kwargs):
        return DummyResponse(404, {})

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

    with pytest.raises(HTTPException) as exc_info:
        await fetch_text_embedding("hello")
    assert exc_info.value.status_code == 502

# -------------------------------------------------------------------
# Tests for cosine_similarity
# -------------------------------------------------------------------

def test_cosine_similarity_same_and_orthogonal():
    """
    Verify that identical vectors give 1.0 and orthogonal vectors give 0.0.
    """
    a = np.array([1.0, 2.0, 3.0])
    assert pytest.approx(cosine_similarity(a, a), abs=1e-6) == 1.0

    b = np.array([-2.0, 1.0, 0.0])
    # Dot product a·b = 1*(-2)+2*1+3*0 = 0 → similarity 0
    assert pytest.approx(cosine_similarity(a, b), abs=1e-6) == 0.0

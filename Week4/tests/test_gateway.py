# tests/test_gateway.py
import io
import pytest
import numpy as np
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.gateway import cosine_similarity

# -------------------------------------------------------------------
# Helpers & Fixtures
# -------------------------------------------------------------------

@pytest.fixture
def dummy_file() -> tuple[str, bytes, str]:
    """
    Returns a minimal PNG‐like file tuple for the gateway POST.
    """
    # Only the bytes length matters for our stub
    return ("dummy.png", b"\x89PNG\r\n\x1a\n...", "image/png")


# We reuse the existing gateway_client fixture from conftest.py,
# which by default patches both fetch_* to return np.ones(512).

# -------------------------------------------------------------------
# Utility Function Tests
# -------------------------------------------------------------------

def test_cosine_similarity_orthogonal():
    """
    Two orthogonal vectors should have similarity 0.
    """
    a = np.array([1.0, 0.0, 0.0])
    b = np.array([0.0, 1.0, 0.0])
    assert cosine_similarity(a, b) == pytest.approx(0.0, abs=1e-6)

def test_cosine_similarity_same_vector():
    """
    A vector with itself must yield 1.0.
    """
    v = np.array([2.0, -3.0, 1.0])
    assert cosine_similarity(v, v) == pytest.approx(1.0, abs=1e-6)

# -------------------------------------------------------------------
# Gateway Endpoint Tests
# -------------------------------------------------------------------

def test_compare_image_service_error(
    monkeypatch,
    gateway_client: TestClient,
    dummy_file
):
    """
    If fetch_image_embedding raises a 502 HTTPException,
    compare() should return status 502.
    """
    async def broken_image(file):
        raise HTTPException(status_code=502, detail="Image service error")

    # Override only the image fetcher
    monkeypatch.setattr(
        "app.gateway.fetch_image_embedding",
        broken_image
    )

    resp = gateway_client.post(
        "/compare/",
        files={"file": dummy_file},
        data={"text": "anything"}
    )
    assert resp.status_code == 502
    assert resp.json()["detail"] == "Image service error"

def test_compare_text_service_error(
    monkeypatch,
    gateway_client: TestClient,
    dummy_file
):
    """
    If fetch_text_embedding raises a 502 HTTPException,
    compare() should return status 502.
    """
    # stub image fetch to succeed with a small vector
    async def good_image(file):
        return np.ones(3, dtype=float)

    # stub text fetch to fail
    async def broken_text(text):
        raise HTTPException(status_code=502, detail="Text service error")

    monkeypatch.setattr(
        "app.gateway.fetch_image_embedding",
        good_image
    )
    monkeypatch.setattr(
        "app.gateway.fetch_text_embedding",
        broken_text
    )

    resp = gateway_client.post(
        "/compare/",
        files={"file": dummy_file},
        data={"text": "anything"}
    )
    assert resp.status_code == 502
    assert resp.json()["detail"] == "Text service error"

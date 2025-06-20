import pytest
import numpy as np
from fastapi.testclient import TestClient

from app.image_service import app as image_app
from app.text_service import app as text_app
from app.gateway import app as gateway_app

@pytest.fixture
def image_client() -> TestClient:
    """
    TestClient for the image_service FastAPI app.
    """
    return TestClient(image_app)

@pytest.fixture
def text_client() -> TestClient:
    """
    TestClient for the text_service FastAPI app.
    """
    return TestClient(text_app)

@pytest.fixture
def gateway_client(monkeypatch) -> TestClient:
    """
    TestClient for the gateway FastAPI app, with the external
    embedding‐fetch functions patched to return dummy vectors.
    """
    async def fake_img(file) -> np.ndarray:
        # Always return a 512‐dim vector of ones
        return np.ones(512, dtype=float)

    async def fake_txt(text: str) -> np.ndarray:
        # Always return a 512‐dim vector of ones
        return np.ones(512, dtype=float)

    # Patch out the real network calls
    monkeypatch.setattr(
        "app.gateway.fetch_image_embedding",
        fake_img,
    )
    monkeypatch.setattr(
        "app.gateway.fetch_text_embedding",
        fake_txt,
    )

    return TestClient(gateway_app)

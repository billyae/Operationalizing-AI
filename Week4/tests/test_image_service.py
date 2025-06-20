import io
from PIL import Image
import pytest
from fastapi.testclient import TestClient

def make_png_bytes(color: str = "blue", size: tuple[int, int] = (32, 32)) -> bytes:
    """
    Helper: create an in‐memory PNG of a solid‐color square.
    """
    buf = io.BytesIO()
    Image.new("RGB", size, color=color).save(buf, format="PNG")
    return buf.getvalue()

def test_embed_image_success(image_client: TestClient):
    """
    Uploading a valid PNG should return a 200 and a normalized embedding list.
    """
    img_bytes = make_png_bytes()
    response = image_client.post(
        "/embed/",
        files={"file": ("blue.png", img_bytes, "image/png")},
    )
    assert response.status_code == 200, response.text

    data = response.json()
    assert "embedding" in data, "Response JSON must contain 'embedding' key"
    emb = data["embedding"]
    assert isinstance(emb, list), "Embedding must be a list of floats"
    # Check length matches CLIP‐base (512 dims for text, 512 for image by default)
    assert len(emb) in (512, 768), f"Unexpected embedding size: {len(emb)}"

    # Validate the vector is L2‐normalized
    norm = sum(x * x for x in emb) ** 0.5
    assert pytest.approx(norm, rel=1e-3) == 1.0

def test_embed_image_invalid(image_client: TestClient):
    """
    Sending non‐image bytes should return a 400 error.
    """
    response = image_client.post(
        "/embed/",
        files={"file": ("bad.txt", b"not an image", "text/plain")},
    )
    assert response.status_code == 400

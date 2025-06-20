from fastapi import FastAPI, File, UploadFile, Form, HTTPException
import httpx
import numpy as np
from app.monitoring import setup_metrics

app = FastAPI(title="API Gateway")

# wire up metrics under service name "gateway"
setup_metrics(app, service_name="gateway")

IMAGE_SVC = "http://127.0.0.1:8001"
TEXT_SVC  = "http://127.0.0.1:8002"

async def fetch_image_embedding(file: UploadFile) -> np.ndarray:
    """
    Uploads the file bytes to the image_service and returns
    its embedding as a NumPy array.
    """
    content = await file.read()
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{IMAGE_SVC}/embed/",
            files={"file": (file.filename, content, file.content_type)},
        )
    if resp.status_code != 200:
        raise HTTPException(502, detail="Image service error")
    return np.array(resp.json()["embedding"], dtype=float)

async def fetch_text_embedding(text: str) -> np.ndarray:
    """
    Sends the text to the text_service and returns
    its embedding as a NumPy array.
    """
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{TEXT_SVC}/embed_text/",
            json={"text": text},
        )
    if resp.status_code != 200:
        raise HTTPException(502, detail="Text service error")
    return np.array(resp.json()["embedding"], dtype=float)

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """
    Compute and return cosine similarity between two vectors.
    """
    return float((a @ b) / (np.linalg.norm(a) * np.linalg.norm(b)))

@app.post("/compare/")
async def compare(file: UploadFile = File(...), text: str = Form(...)) -> dict:
    """
    Endpoint: accepts an image file and a text form field,
    returns {"similarity": <cosine_similarity>}.
    """
    emb_img  = await fetch_image_embedding(file)
    emb_text = await fetch_text_embedding(text)
    sim = cosine_similarity(emb_img, emb_text)
    return {"similarity": sim}

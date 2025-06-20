from fastapi import FastAPI
from pydantic import BaseModel, StrictStr
from transformers import CLIPProcessor, CLIPModel
from app.monitoring import setup_metrics
import torch

app = FastAPI(title="Text Service")

# wire up metrics under service name "text_service"
setup_metrics(app, service_name="text_service")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").eval()

class TextIn(BaseModel):
    text: StrictStr

def extract_text_embedding(text: str) -> list[float]:
    """
    Tokenize and encode text via CLIP, normalize, and return list.
    """
    inputs = processor(text=text, return_tensors="pt", padding=True)
    with torch.no_grad():
        feats = model.get_text_features(**inputs)
    feats = feats / feats.norm(p=2, dim=-1, keepdim=True)
    return feats[0].tolist()

@app.post("/embed_text/")
def embed_text(payload: TextIn) -> dict:
    """
    Endpoint: accepts JSON {"text": "..."},
    returns {"embedding": [...]}.
    """
    embedding = extract_text_embedding(payload.text)
    return {"embedding": embedding}

import io
from fastapi import FastAPI, UploadFile, File, HTTPException
from PIL import Image, UnidentifiedImageError
from transformers import CLIPImageProcessor, CLIPModel
from app.monitoring import setup_metrics
import torch

app = FastAPI(title="Image Service")

# wire up metrics under service name "image_service"
setup_metrics(app, service_name="image_service")
# Choose device and load model once at startup
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
processor = CLIPImageProcessor.from_pretrained("openai/clip-vit-base-patch32")
model = (
    CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
    .to(device)
    .eval()
)

def read_image(data: bytes) -> Image.Image:
    """
    Decode raw bytes into a PIL RGB image.
    Raises HTTPException(400) if the bytes are not a valid image.
    """
    try:
        return Image.open(io.BytesIO(data)).convert("RGB")
    except (UnidentifiedImageError, OSError):
        raise HTTPException(status_code=400, detail="Invalid image file.")

def preprocess_image(img: Image.Image) -> torch.Tensor:
    """
    Apply the CLIPImageProcessor to create a batched tensor.
    Returns pixel_values on the correct device.
    """
    batch = processor([img], return_tensors="pt", padding=True)
    return batch["pixel_values"].to(device)

def extract_image_embedding(pixel_values: torch.Tensor) -> list[float]:
    """
    Run the CLIP model to get a normalized image embedding.
    Returns a plain Python list.
    """
    with torch.no_grad():
        feats = model.get_image_features(pixel_values=pixel_values)
        feats = feats / feats.norm(dim=-1, keepdim=True)
    return feats[0].cpu().tolist()

@app.post("/embed/")
async def embed_image(file: UploadFile = File(...)) -> dict:
    """
    Endpoint: accepts multipart/form-data image upload,
    returns {"embedding": [...]}.
    """
    raw = await file.read()
    img = read_image(raw)
    pixel_values = preprocess_image(img)
    embedding = extract_image_embedding(pixel_values)
    return {"embedding": embedding}

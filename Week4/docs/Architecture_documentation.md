# Architecture Documentation
## Overview

The system follows a micro-services pattern, composed of three FastAPI applications:  
- API Gateway
    - Exposes /compare/ endpoint.
    - Forwards image uploads to the Image Service and text payloads to the Text Service.
    - Computes cosine similarity of the two returned embeddings.
    - Aggregates metrics under gateway service name.

- Image Service

    - Exposes /embed/ endpoint
    - Reads, preprocesses, and embeds images via a CLIP model
    - Returns an L2-normalized vector
    - Aggregates metrics under image_service 

- Text Service

    - Exposes /embed_text/ endpoint
    - Tokenizes and embeds text via a CLIP model
    - Returns an L2-normalized vector
    - Aggregates metrics under text_service 

All services integrate the same Prometheus middleware (request count & latency) and expose /metrics.

## Component Breakdown

| Component             | Language/Framework          | Key Responsibilities                                                                                                             |
| --------------------- | --------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| **gateway.py**        | Python / FastAPI            | - Receive multipart image + form text<br>- Call `fetch_image_embedding` & `fetch_text_embedding`<br>- Compute cosine similarity  |
| **image\_service.py** | Python / FastAPI            | - Validate & decode images<br>- Preprocess via `CLIPImageProcessor`<br>- Model inference & normalization                         |
| **text\_service.py**  | Python / FastAPI            | - Validate text payload via Pydantic<br>- Preprocess via `CLIPProcessor`<br>- Model inference & normalization                    |
| **monitoring.py**     | Python                      | - Prometheus `Counter` & `Histogram` middleware<br>- `/metrics` endpoint                                                         |
| **tests/**            | pytest + httpx + TestClient | - Unit & integration tests for utils, gateway, image & text endpoints                                                            |
| **requirements.txt**  | —                           | Python dependency pinning                                                                                                        |
| **pytest.ini**        | —                           | Test discovery & coverage config                                                                                                 |

## Data Flow

Client → API Gateway (POST /compare/)

API Gateway → Image Service (POST /embed/)

Image Service → API Gateway (returns 512-dim image embedding)

API Gateway → Text Service (POST /embed_text/)

Text Service → API Gateway (returns 512-dim text embedding)

API Gateway → Client (returns {"similarity": <float>})

## Metrics Collection

- Prometheus scrapes /metrics from:
    - Image Service
    - Text Service
    - API Gateway
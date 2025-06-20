# Multimodal AI Service

A lightweight, micro‑service based system for computing similarity between images and text via a shared CLIP backbone. It consists of:

- **API Gateway** (gateway.py): Accepts image + text, forwards to embedding services, computes cosine similarity.

- **Image Service** (image_service.py): Embeds images (/embed/).

- **Text Service** (text_service.py): Embeds text (/embed_text/).

- **Monitoring** (monitoring.py): Exposes Prometheus metrics (/metrics).

Tests are provided under tests/, with coverage configured via pytest.ini. A sample Prometheus scrape config lives in prometheus/prometheus.yml.

## Architecture

1. Client calls POST /compare/ on the API Gateway

2. Gateway fans out to:

   - Image Service: POST /embed/ → 512‑dim image embedding

   - Text Service:  POST /embed_text/ → 512‑dim text - embedding

3. Gateway computes cosine similarity and returns:

    ```json
    { "similarity": <float> }
    ```

4. All three services expose /metrics for Prometheus scraping.

## Prerequisites

- Python 3.9+
- (Optional, for GPU) CUDA 11+ with compatible PyTorch
- git, curl, etc.

## Installation

```bash
git clone <repo-url>
cd <repo-dir>
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Running Locally

Start each service in its own terminal:

```bash
uvicorn app.image_service:app --host 0.0.0.0 --port 8001 --workers 2
uvicorn app.text_service:app  --host 0.0.0.0 --port 8002 --workers 2
uvicorn app.gateway:app       --host 0.0.0.0 --port 8000 --workers 2
```

- Gateway:  http://localhost:8000/compare/
- Image:    http://localhost:8001/embed/
- Text:     http://localhost:8002/embed_text/
- Metrics:  http://\<host>:\<port>/metrics

Example compare call:

```bash
curl -X POST \
  -F "image=@/path/to/cat.jpg" \
  -F "text=“a cute cat”" \
  http://localhost:8000/compare/
```
## Testing & Coverage

```bash
pytest
```

## Deployment

Write a Dockerfile: 
```Dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.image_service:app", "--host", "0.0.0.0", "--port", "8001"]
```
docker-compose.yml:
```yaml
version: "3.8"
services:
  image_service:
    build: .
    container_name: image_svc
    ports: ["8001:8001"]
  text_service:
    build: .
    container_name: text_svc
    ports: ["8002:8002"]
  gateway:
    build: .
    container_name: gateway
    ports: ["8000:8000"]
    environment:
      IMAGE_SVC: "http://image_svc:8001"
      TEXT_SVC:  "http://text_svc:8002"
```

Build images:
```bash
docker build -t multimodal-image -f Dockerfile.image .
docker build -t multimodal-text  -f Dockerfile.text  .
docker build -t multimodal-gateway -f Dockerfile.gateway .
```
Or use docker-compose.yml:
```bash
docker-compose up --build
```

##  Kubernetes
- Define Deployments for each service, exposing /metrics and HTTP ports.
- Use a Service + Ingress to route /compare/ to the gateway.
- Scrape metrics in Prometheus via prometheus.yml.

## Monitoring & Alerting

- Point your prometheus.yml at each /metrics endpoint

- Define alerts on:
    - High request latency
    - Error rate spikes (http_requests_total{http_status=~"5.."} > threshold)

- Visualize in Grafana (dashboards for latency histograms and QPS)



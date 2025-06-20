# Deployment Guide

## Prerequisites

- OS: Linux (Ubuntu/Debian) or container
- Python: 3.9+
- CUDA toolkit (if GPU)
- Prometheus server for metrics scraping
- Ports:
    - Gateway: 8000
    - Image Service: 8001
    - Text Service: 8002

Install deps:

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt  # :contentReference[oaicite:10]{index=10}
```

## Running Locally

Start each service in its own terminal:

```bash
uvicorn app.image_service:app --host 0.0.0.0 --port 8001 --workers 2
uvicorn app.text_service:app  --host 0.0.0.0 --port 8002 --workers 2
uvicorn app.gateway:app       --host 0.0.0.0 --port 8000 --workers 2
```

Probe metrics at:

- http://localhost:8001/metrics
- http://localhost:8002/metrics
- http://localhost:8000/metrics

## Docker & Docker-Compose

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
## Kubernetes Deployment

- Deployments for each service with 2–3 replicas
- Services exposing ClusterIP on respective ports
- Ingress routing /compare/ to gateway
- HorizontalPodAutoscaler based on CPU/GPU utilization
- ConfigMap for Prometheus scrape targets

## Monitoring & Alerting

- Point your prometheus.yml at each /metrics endpoint

- Define alerts on:
    - High request latency
    - Error rate spikes (http_requests_total{http_status=~"5.."} > threshold)

- Visualize in Grafana (dashboards for latency histograms and QPS)


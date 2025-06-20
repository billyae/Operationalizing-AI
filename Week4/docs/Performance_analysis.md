# Performance Analysis
##  Benchmarking Setup
- Hardware: GPU (e.g., NVIDIA T4) vs. CPU fallback
- Batch size: Single-item processing
- Metric tools: Prometheus metrics (http_request_latency_seconds), custom timing

## Latency Breakdown

| Service           | Median Latency (GPU) | Median Latency (CPU) | Notes                                   |
| ----------------- | -------------------- | -------------------- | --------------------------------------- |
| **Image Service** | \~30–50 ms           | \~150–250 ms         | CLIP forward + preprocessing            |
| **Text Service**  | \~20–40 ms           | \~80–120 ms          | Tokenization + forward pass             |
| **API Gateway**   | \~5–10 ms            | \~5–10 ms            | Pure Python compute + HTTP calls (\~2×) |
| **End-to-End**    | \~60–100 ms          | \~300–400 ms         | Two downstream calls + similarity calc  |

## Throughput & Concurrency

- Uvicorn workers: 2–4 per service recommended
- Max concurrent requests limited by model inference time and GPU memory
- HTTP connection reuse: consider a long-lived httpx.AsyncClient instead of instantiating per call to improve gateway throughput.

## Bottlenecks & Profiling

- Model load time on cold start
- Single-threaded Python within FastAPI worker
- I/O overhead reading images/text and serializing JSON
- Network round trips between gateway ↔ services

Profiling tools:
- PyTorch profiler for inference
- py-spy or scalene for CPU hotspots
- Prometheus + Grafana dashboards for live metrics

## Optimization Strategies

- Batch inference via queue and grouped calls
- FP16 or ONNX conversion for faster CPU inference
- Caching frequent embeddings (e.g., identical text queries)
- Horizontal scaling behind a load-balancer
- Asynchronous HTTP clients reused per process


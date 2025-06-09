# Performance Analysis

This document outlines key metrics, observed bottlenecks, and tuning recommendations.

## 1. Latency Metrics

| Metric        | Description                                    |
| ------------- | ---------------------------------------------- |
| **p50**       | Median round-trip to Bedrock + logging (ms)    |
| **p95**       | 95th-percentile latency                         |
| **Max**       | Worst-case observed latency                     |

> **Data source:** `latency_ms` column in `audit_logs.db`

## 2. Bottleneck Breakdown

1. **Model Invocation**  
   - Dominant cost (~90% of total).  
   - Dependent on AWS Bedrock throughput and network.

2. **Audit Logging**  
   - SQLite write & console I/O (~5–10 ms).  
   - Consider batching or asynchronous writes for high QPS.

3. **Frontend Overhead**  
   - Streamlit rerenders ~100–200 ms on each user action.

## 3. Load Testing

- Use tools like **Locust** or **hey**:
  ```bash
  hey -n 1000 -c 50 http://localhost:8000/chat

## 4.Scaling Recommendations

- Model Parallelism: Increase Bedrock provisioned throughput or use multiple profiles.

- Horizontal Scaling:

    - Deploy multiple FastAPI workers (e.g. --workers 4 with Uvicorn/Gunicorn).

    - Route via a load balancer.

- Logging Backend:

    - Migrate from SQLite → PostgreSQL or another server-grade DB for high write volume.

    - Use a message queue (e.g. RabbitMQ/Kafka) for non-blocking audit writes.

## 5. Caching

- Prompt Caching: For repeated/system‐level prompts, cache replies in Redis.

- HTTP Keep-Alive: Reuse connections to Logging API to reduce TCP overhead.
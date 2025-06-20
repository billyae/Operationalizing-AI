# app/monitoring.py
import time
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Request, Response

# Labels: service name, endpoint path, HTTP status
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["service", "endpoint", "http_status"],
)
REQUEST_LATENCY = Histogram(
    "http_request_latency_seconds",
    "Latency of HTTP requests in seconds",
    ["service", "endpoint"],
)

def setup_metrics(app, service_name: str):
    """
    Add Prometheus middleware and /metrics endpoint to the FastAPI app.
    """
    @app.middleware("http")
    async def metrics_middleware(request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        elapsed = time.time() - start

        endpoint = request.url.path
        status = response.status_code

        # Record metrics
        REQUEST_LATENCY.labels(service_name, endpoint).observe(elapsed)
        REQUEST_COUNT.labels(service_name, endpoint, status).inc()

        return response

    @app.get("/metrics")
    def metrics():
        """
        Expose Prometheus metrics.
        """
        data = generate_latest()
        return Response(data, media_type=CONTENT_TYPE_LATEST)

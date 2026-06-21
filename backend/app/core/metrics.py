"""Lightweight Prometheus metrics middleware (no fragile route introspection)."""

from __future__ import annotations

import time

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

REQUESTS = Counter(
    "http_requests_total", "Total HTTP requests", ["method", "path", "status"]
)
LATENCY = Histogram(
    "http_request_duration_seconds", "Request latency", ["method", "path"]
)


class PrometheusMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        # use the route template, not the raw path, to keep cardinality low
        route = request.scope.get("route")
        path = getattr(route, "path", request.url.path)
        try:
            response = await call_next(request)
            status = response.status_code
        except Exception:
            REQUESTS.labels(request.method, path, 500).inc()
            raise
        LATENCY.labels(request.method, path).observe(time.perf_counter() - start)
        REQUESTS.labels(request.method, path, status).inc()
        return response


def metrics_endpoint() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

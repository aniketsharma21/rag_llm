"""Observability middleware for request tracing and Prometheus metrics."""
from __future__ import annotations

from time import perf_counter
from typing import Callable
from uuid import uuid4

from fastapi import FastAPI, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response as StarletteResponse

from src.logging_config import (
    clear_request_context,
    get_logger,
    request_log_entry,
    set_request_context,
)


REQUEST_COUNTER = Counter(
    "rag_http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)
REQUEST_LATENCY = Histogram(
    "rag_http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "path"],
)
REQUEST_IN_PROGRESS = Gauge(
    "rag_http_requests_in_progress",
    "Number of HTTP requests currently being processed",
)


def _resolve_route_path(request: Request) -> str:
    route = request.scope.get("route")
    if route and getattr(route, "path", None):
        return route.path  # type: ignore[attr-defined]
    return request.url.path


class RequestMetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], StarletteResponse],
    ) -> StarletteResponse:
        REQUEST_IN_PROGRESS.inc()
        start_time = perf_counter()
        status_code = 500
        response: StarletteResponse | None = None
        request_id = request.headers.get("x-request-id") or str(uuid4())
        client_ip = request.client.host if request.client else None
        route_path = _resolve_route_path(request)
        set_request_context(
            request_id=request_id,
            client_ip=client_ip,
            user_agent=request.headers.get("user-agent"),
        )
        logger = get_logger("request")
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            duration = perf_counter() - start_time
            REQUEST_COUNTER.labels(request.method, route_path, str(status_code)).inc()
            REQUEST_LATENCY.labels(request.method, route_path).observe(duration)
            REQUEST_IN_PROGRESS.dec()
            logger.info(
                request_log_entry(
                    method=request.method,
                    path=route_path,
                    status_code=status_code,
                    duration_seconds=duration,
                    request_id=request_id,
                    client_ip=client_ip,
                )
            )
            clear_request_context()


def setup_observability(app: FastAPI) -> None:
    """Configure observability middleware and metrics endpoint."""

    if getattr(app.state, "observability_configured", False):
        return

    app.add_middleware(RequestMetricsMiddleware)

    async def metrics() -> Response:  # pragma: no cover - simple wrapper
        data = generate_latest()
        return Response(content=data, media_type=CONTENT_TYPE_LATEST)

    app.add_api_route("/metrics", metrics, include_in_schema=False)
    app.state.metrics_route_registered = True
    app.state.observability_configured = True

"""Observability middleware for request tracing and Prometheus metrics.

This module provides middleware and utilities for monitoring and observability in the RAG LLM application.
It includes request tracking, metrics collection, and error monitoring using Prometheus metrics
and structured logging.
"""
from __future__ import annotations

from time import perf_counter
from typing import Callable, Dict
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

RAG_RETRIEVAL_LATENCY = Histogram(
    "rag_retrieval_duration_seconds",
    "Time spent retrieving documents for RAG queries",
    ["mode"],
)

RAG_RETRIEVED_DOCUMENTS = Histogram(
    "rag_retrieved_documents_count",
    "Number of documents returned from retrieval",
    ["mode"],
)

RAG_GENERATION_LATENCY = Histogram(
    "rag_generation_duration_seconds",
    "Time spent generating responses with the LLM",
    ["provider", "model"],
)

RAG_TOKEN_USAGE = Counter(
    "rag_generation_tokens_total",
    "Token usage reported by the LLM provider",
    ["provider", "model", "token_type"],
)

RAG_ERRORS = Counter(
    "rag_pipeline_errors_total",
    "Count of errors emitted during the RAG pipeline",
    ["component", "exception_type"],
)


def _resolve_route_path(request: Request) -> str:
    """Extract the route path from a request object.

    Args:
        request: The incoming HTTP request.

    Returns:
        str: The resolved route path or URL path if route is not available.
    """
    route = request.scope.get("route")
    if route and getattr(route, "path", None):
        return route.path  # type: ignore[attr-defined]
    return request.url.path


class RequestMetricsMiddleware(BaseHTTPMiddleware):
    """Middleware for collecting HTTP request metrics and logging.

    This middleware tracks:
    - Request count by method, path, and status code
    - Request latency
    - In-progress request count
    - Request context for structured logging
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], StarletteResponse],
    ) -> StarletteResponse:
        """Process an incoming HTTP request and collect metrics.

        Args:
            request: The incoming HTTP request.
            call_next: Callable to proceed with request processing.

        Returns:
            StarletteResponse: The HTTP response.
        
        Note:
            Automatically captures and logs request details including duration,
            status code, and request context.
        """
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
    """Configure observability middleware and metrics endpoint.
    
    This function:
    - Adds the RequestMetricsMiddleware to the FastAPI app
    - Sets up a /metrics endpoint for Prometheus scraping
    - Ensures idempotent setup with state tracking
    
    Args:
        app: The FastAPI application instance to configure.
        
    Note:
        Safe to call multiple times; will only configure once per app instance.
    """

    if getattr(app.state, "observability_configured", False):
        return

    app.add_middleware(RequestMetricsMiddleware)

    async def metrics() -> Response:  # pragma: no cover - simple wrapper
        data = generate_latest()
        return Response(content=data, media_type=CONTENT_TYPE_LATEST)

    app.add_api_route("/metrics", metrics, include_in_schema=False)
    app.state.metrics_route_registered = True
    app.state.observability_configured = True


def observe_rag_retrieval(*, duration_seconds: float, document_count: int, mode: str) -> None:
    """Record retrieval metrics for observability dashboards.
    
    Tracks the performance of document retrieval operations in the RAG pipeline.
    
    Args:
        duration_seconds: Time taken for the retrieval operation in seconds.
        document_count: Number of documents retrieved.
        mode: The retrieval mode used (e.g., 'semantic', 'keyword', 'hybrid').
        
    Note:
        Metrics are collected under the following names:
        - rag_retrieval_duration_seconds: Histogram of retrieval times by mode
        - rag_retrieved_documents_count: Histogram of document counts by mode
    """

    sanitized_mode = mode or "unknown"
    try:
        RAG_RETRIEVAL_LATENCY.labels(sanitized_mode).observe(max(duration_seconds, 0.0))
        RAG_RETRIEVED_DOCUMENTS.labels(sanitized_mode).observe(max(document_count, 0))
    except Exception:  # pragma: no cover - metrics should not break business logic
        return


def observe_rag_generation(
    *,
    provider: str,
    model: str,
    duration_seconds: float,
    token_usage: Dict[str, int] | None = None,
) -> None:
    """Record LLM generation metrics including latency and token usage.
    
    Tracks the performance and resource usage of LLM generation operations.
    
    Args:
        provider: The LLM provider (e.g., 'openai', 'huggingface').
        model: The specific model name/identifier.
        duration_seconds: Time taken for generation in seconds.
        token_usage: Optional dictionary of token counts by token type.
            Common keys include 'prompt_tokens', 'completion_tokens', 'total_tokens'.
            
    Note:
        Metrics are collected under the following names:
        - rag_generation_duration_seconds: Histogram of generation times by provider and model
        - rag_generation_tokens_total: Counter of token usage by type, provider, and model
    """

    sanitized_provider = (provider or "unknown").lower()
    sanitized_model = model or "unknown"
    try:
        RAG_GENERATION_LATENCY.labels(sanitized_provider, sanitized_model).observe(max(duration_seconds, 0.0))
        if token_usage:
            for token_type, count in token_usage.items():
                if count is None:
                    continue
                RAG_TOKEN_USAGE.labels(sanitized_provider, sanitized_model, token_type).inc(max(int(count), 0))
    except Exception:  # pragma: no cover - defensive metric handling
        return


def increment_rag_error(*, component: str, exception_type: str) -> None:
    """Increment error counter for a RAG component.
    
    Tracks error occurrences in the RAG pipeline by component and exception type.
    
    Args:
        component: The component where the error occurred (e.g., 'retrieval', 'generation').
        exception_type: The type/class of the exception that was raised.
        
    Note:
        Metrics are collected under 'rag_pipeline_errors_total' counter with
        'component' and 'exception_type' labels.
    """

    sanitized_component = component or "unknown"
    sanitized_exception = exception_type or "UnknownException"
    try:
        RAG_ERRORS.labels(sanitized_component, sanitized_exception).inc()
    except Exception:  # pragma: no cover - ensure metrics never raise
        return

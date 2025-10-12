"""Observability middleware for request tracing and Prometheus metrics.

This module provides middleware and utilities for monitoring and observability in the RAG LLM application.
It includes request tracking, metrics collection, and error monitoring using Prometheus metrics
and structured logging.
"""
from __future__ import annotations

from time import perf_counter
from typing import Awaitable, Callable, Dict
from uuid import uuid4
import logging

from fastapi import FastAPI, HTTPException, Response
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
        The resolved route path or URL path if route is not available.

    Example:
        >>> request = Request(scope={"type": "http", "path": "/test"})
        >>> _resolve_route_path(request)
        '/test'
    """
    try:
        route = request.scope.get("route")
        if route and hasattr(route, "path") and route.path:  # type: ignore[attr-defined]
            return str(route.path)  # type: ignore[attr-defined]
        return str(request.url.path)
    except Exception as e:
        logger = logging.getLogger("observability")
        logger.warning("Failed to resolve route path: %s", str(e), exc_info=True)
        return "unknown"


class RequestMetricsMiddleware(BaseHTTPMiddleware):
    """Middleware for collecting HTTP request metrics and logging.

    This middleware tracks:
    - Request count by method, path, and status code
    - Request and response sizes
    - Request latency with percentiles
    - In-progress request count
    - Request context for structured logging
    - Error tracking and logging
    
    Attributes:
        logger: Logger instance for request logging
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.logger = get_logger("request")

    async def _get_request_size(self, request: Request) -> int:
        """Calculate the size of the request body in bytes."""
        try:
            body = await request.body()
            return len(body) if body else 0
        except Exception as e:
            self.logger.warning("Failed to get request size: %s", str(e))
            return 0

    async def _get_response_size(self, response: StarletteResponse) -> int:
        """Calculate the size of the response body in bytes."""
        if hasattr(response, 'body'):
            return len(response.body) if response.body else 0
        return 0

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[StarletteResponse]],
    ) -> StarletteResponse:
        """Process an incoming HTTP request and collect metrics.

        Args:
            request: The incoming HTTP request.
            call_next: Callable to proceed with request processing.

        Returns:
            The HTTP response.

        Note:
            Automatically captures and logs request details including duration,
            status code, request/response sizes, and request context.
        """
        REQUEST_IN_PROGRESS.inc()
        start_time = perf_counter()
        status_code = 500
        request_id = request.headers.get("x-request-id") or str(uuid4())
        client_ip = request.client.host if request.client else None
        route_path = _resolve_route_path(request)
        
        try:
            # Set up request context
            set_request_context(
                request_id=request_id,
                client_ip=client_ip,
                user_agent=request.headers.get("user-agent"),
            )
            
            # Process the request
            response = await call_next(request)
            status_code = response.status_code
            
            # Log successful request
            self._log_request(
                request=request,
                route_path=route_path,
                status_code=status_code,
                start_time=start_time,
                request_id=request_id,
                client_ip=client_ip,
            )
            
            return response
            
        except HTTPException as http_exc:
            status_code = http_exc.status_code
            self.logger.error(
                "HTTP error processing request",
                exc_info=True,
                extra={
                    "status_code": status_code,
                    "path": route_path,
                    "method": request.method,
                    "request_id": request_id,
                },
            )
            raise
            
        except Exception as exc:
            status_code = 500
            self.logger.critical(
                "Unexpected error processing request",
                exc_info=True,
                extra={
                    "status_code": status_code,
                    "path": route_path,
                    "method": request.method,
                    "request_id": request_id,
                },
            )
            raise
            
        finally:
            try:
                # Update metrics
                duration = perf_counter() - start_time
                REQUEST_COUNTER.labels(
                    method=request.method,
                    path=route_path,
                    status=str(status_code)
                ).inc()
                
                REQUEST_LATENCY.labels(
                    method=request.method,
                    path=route_path
                ).observe(duration)
                
                # Log slow requests
                if duration > 5.0:  # 5 seconds threshold
                    self.logger.warning(
                        "Slow request detected",
                        extra={
                            "duration_seconds": duration,
                            "path": route_path,
                            "method": request.method,
                            "status_code": status_code,
                            "request_id": request_id,
                        },
                    )
                    
            except Exception as metrics_error:
                self.logger.error(
                    "Failed to record metrics",
                    exc_info=metrics_error,
                    extra={"request_id": request_id},
                )
                
            finally:
                REQUEST_IN_PROGRESS.dec()
                clear_request_context()
    
    def _log_request(
        self,
        request: Request,
        route_path: str,
        status_code: int,
        start_time: float,
        request_id: str,
        client_ip: str | None,
    ) -> None:
        """Log request details in a structured format."""
        duration = perf_counter() - start_time
        log_data = {
            "method": request.method,
            "path": route_path,
            "status_code": status_code,
            "duration_seconds": duration,
            "request_id": request_id,
            "client_ip": client_ip,
            "user_agent": request.headers.get("user-agent"),
            "query_params": dict(request.query_params) if request.query_params else None,
        }
        
        if status_code >= 400:
            self.logger.warning("Request completed with error", **log_data)
        else:
            self.logger.info("Request completed successfully", **log_data)


def setup_observability(app: FastAPI) -> None:
    """Configure observability middleware and endpoints.

    This function:
    - Adds the RequestMetricsMiddleware to the FastAPI app
    - Sets up a /metrics endpoint for Prometheus scraping
    - Adds a /health endpoint for health checks
    - Ensures idempotent setup with state tracking

    Args:
        app: The FastAPI application instance to configure.

    Note:
        Safe to call multiple times; will only configure once per app instance.
    """
    if getattr(app.state, "observability_configured", False):
        return

    # Add metrics middleware
    app.add_middleware(RequestMetricsMiddleware)
    logger = get_logger("observability")

    @app.get("/health", include_in_schema=False)
    async def health_check() -> dict[str, str]:
        """Health check endpoint for load balancers and monitoring.

        Returns:
            A JSON response with status "ok" if the service is healthy.
        """
        try:
            # Add any additional health checks here
            return {"status": "ok"}
        except Exception as e:
            logger.error("Health check failed", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail={"status": "error", "error": str(e)},
            )

    @app.get("/metrics", include_in_schema=False)
    async def metrics() -> Response:
        """Expose Prometheus metrics.

        Returns:
            Response: The Prometheus metrics in text format.
        """
        try:
            data = generate_latest()
            return Response(content=data, media_type=CONTENT_TYPE_LATEST)
        except Exception as e:
            logger.error("Failed to generate metrics", exc_info=True)
            return Response(
                content=str(e), status_code=500, media_type="text/plain"
            )

    # Mark as configured
    app.state.observability_configured = True  # type: ignore[attr-defined]
    logger.info("Observability middleware and endpoints configured")


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
                try:
                    if count is None:
                        continue
                    RAG_TOKEN_USAGE.labels(sanitized_provider, sanitized_model, token_type).inc(max(int(count), 0))
                except Exception:  # Defensive handling for individual token updates
                    continue
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

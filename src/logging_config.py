"""Enhanced logging configuration with structured logging support.

This module provides a comprehensive logging configuration for the RAG LLM application,
featuring structured logging with JSON format in production and human-readable output
in development. It includes utilities for request tracing, error logging, and performance
monitoring.

Key Features:
- JSON-formatted logs in production, human-readable in development
- Request context tracking
- Performance monitoring
- Error handling with rich context
- Structured logging with structlog
"""

import os
import sys
import logging
import structlog
from structlog.contextvars import bind_contextvars, clear_contextvars
from pythonjsonlogger.json import JsonFormatter
from typing import Any, Dict


def setup_logging(log_level: str = None, json_logs: bool = None) -> None:
    """
    Configure structured logging for the application.
    
    Args:
        log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_logs: Whether to use JSON format (default: True in production)
    """
    # Determine log level
    if log_level is None:
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    
    # Determine if we should use JSON logs (default: False for development)
    if json_logs is None:
        json_logs = os.getenv("ENVIRONMENT", "production") == "production"
    
    # Configure standard logging
    logging.basicConfig(
        level=getattr(logging, log_level),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s" if not json_logs else None,
        stream=sys.stdout,
        force=True
    )
    
    # Configure structlog processors
    if json_logs:
        processors = [
            structlog.stdlib.filter_by_level,
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ]
    else:
        # Use simple console logging for development
        processors = [
            structlog.stdlib.filter_by_level,
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.KeyValueRenderer(key_order=['timestamp', 'level', 'logger'])
        ]
    
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Set up JSON formatter for standard logging if needed
    if json_logs:
        root_logger = logging.getLogger()
        if root_logger.handlers:
            handler = root_logger.handlers[0]
            formatter = JsonFormatter(
                '%(asctime)s %(name)s %(levelname)s %(message)s'
            )
            handler.setFormatter(formatter)


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)


def log_function_call(func_name: str, **kwargs) -> Dict[str, Any]:
    """
    Helper to create consistent function call log entries.
    
    Args:
        func_name: Name of the function being called
        **kwargs: Additional context to log
        
    Returns:
        Log context dictionary
    """
    return {
        "event": "function_call",
        "function": func_name,
        **kwargs
    }


def log_error(error: Exception, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Helper to create consistent error log entries.
    
    Args:
        error: Exception that occurred
        context: Additional context about the error
        
    Returns:
        Log context dictionary
    """
    return {
        "event": "error",
        "error_type": type(error).__name__,
        "error_message": str(error),
        "context": context or {}
    }


def log_performance(operation: str, duration: float, **kwargs) -> Dict[str, Any]:
    """
    Helper to create consistent performance log entries.
    
    Args:
        operation: Name of the operation
        duration: Time taken in seconds
        **kwargs: Additional metrics
        
    Returns:
        Log context dictionary
    """
    return {
        "event": "performance",
        "operation": operation,
        "duration_seconds": duration,
        **kwargs
    }


def set_request_context(request_id: str = None, client_ip: str = None, user_agent: str = None) -> None:
    """Bind request-level context variables for structured logging.
    
    This function adds request-specific information to the logging context, which will be
    included in all subsequent log entries until cleared.
    
    Args:
        request_id: Unique identifier for the request
        client_ip: IP address of the client making the request
        user_agent: User-Agent header from the HTTP request
        
    Example:
        >>> set_request_context(
        ...     request_id="req-123",
        ...     client_ip="192.168.1.1",
        ...     user_agent="Mozilla/5.0"
        ... )
    """
    context = {}
    if request_id:
        context["request_id"] = request_id
    if client_ip:
        context["client_ip"] = client_ip
    if user_agent:
        context["user_agent"] = user_agent
    if context:
        bind_contextvars(**context)


def clear_request_context() -> None:
    """Clear any bound request context variables.
    
    This should typically be called at the end of a request to prevent context
    leakage between requests.
    
    Example:
        >>> clear_request_context()  # Clears all bound context variables
    """
    clear_contextvars()


def request_log_entry(
    *,
    method: str,
    path: str,
    status_code: int,
    duration_seconds: float,
    request_id: str | None = None,
    client_ip: str | None = None,
) -> Dict[str, Any]:
    """Create a structured log entry for HTTP request tracing.
    
    This function generates a standardized log entry for HTTP requests that includes
    timing, status, and request identification information.
    
    Args:
        method: HTTP method (GET, POST, etc.)
        path: Request path
        status_code: HTTP status code
        duration_seconds: Request processing time in seconds
        request_id: Optional unique request identifier
        client_ip: Optional client IP address
        
    Returns:
        A dictionary containing the structured log data with the following keys:
        - event: Always "http_request"
        - method: HTTP method
        - path: Request path
        - status_code: HTTP status code
        - duration_seconds: Request duration in seconds (rounded to 6 decimal places)
        - request_id: The request ID if provided
        - client_ip: The client IP if provided
        
    Example:
        >>> log_entry = request_log_entry(
        ...     method="GET",
        ...     path="/api/data",
        ...     status_code=200,
        ...     duration_seconds=0.1234567,
        ...     request_id="req-123"
        ... )
    """
    payload: Dict[str, Any] = {
        "event": "http_request",
        "method": method,
        "path": path,
        "status_code": status_code,
        "duration_seconds": round(duration_seconds, 6),
    }
    if request_id:
        payload["request_id"] = request_id
    if client_ip:
        payload["client_ip"] = client_ip
    return payload


# Initialize logging when module is imported
setup_logging()

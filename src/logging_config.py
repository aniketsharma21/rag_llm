"""
logging_config.py

Enhanced logging configuration with structured logging support.
Provides JSON logging for production and human-readable logs for development.
"""

import os
import sys
import logging
import structlog
from structlog.contextvars import bind_contextvars, clear_contextvars
from pythonjsonlogger import jsonlogger
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
            formatter = jsonlogger.JsonFormatter(
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
    """Bind request-level context variables for structured logging."""
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
    """Clear any bound request context variables."""
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
    """Structured payload for request trace logs."""
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

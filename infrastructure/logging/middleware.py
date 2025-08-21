"""Logging middleware for API requests and responses."""

import time
import uuid
import logging
from typing import Callable
from fastapi import Request, Response
from fastapi.routing import Match
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log API requests and responses."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request ID
        request_id = str(uuid.uuid4())
        start_time = time.time()
        
        # Add request ID to request state
        request.state.request_id = request_id
        
        # Log request
        await self._log_request(request, request_id)
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Log response
        await self._log_response(request, response, request_id, duration)
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response
    
    async def _log_request(self, request: Request, request_id: str):
        """Log incoming request details."""
        # Get client IP
        client_ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "unknown")
        
        # Get user agent
        user_agent = request.headers.get("User-Agent", "unknown")
        
        # Skip logging for health checks and docs
        if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json"]:
            return
        
        logger.info(
            "API request received",
            extra={
                "request_id": request_id,
                "method": request.method,
                "url": str(request.url),
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "client_ip": client_ip,
                "user_agent": user_agent,
                "content_type": request.headers.get("Content-Type"),
                "content_length": request.headers.get("Content-Length"),
                "event_type": "request_start"
            }
        )
    
    async def _log_response(self, request: Request, response: Response, request_id: str, duration: float):
        """Log response details."""
        # Skip logging for health checks and docs
        if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json"]:
            return
        
        # Determine log level based on status code
        if response.status_code >= 500:
            log_level = logging.ERROR
        elif response.status_code >= 400:
            log_level = logging.WARNING
        else:
            log_level = logging.INFO
        
        logger.log(
            log_level,
            "API request completed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_seconds": round(duration, 4),
                "response_size": response.headers.get("Content-Length"),
                "event_type": "request_end"
            }
        )
        
        # Log slow requests
        if duration > 2.0:  # 2 seconds threshold
            logger.warning(
                "Slow API request detected",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "duration_seconds": round(duration, 4),
                    "event_type": "slow_request"
                }
            )


class ErrorLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log unhandled errors."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            # Get request ID if available
            request_id = getattr(request.state, 'request_id', 'unknown')
            
            logger.error(
                "Unhandled error in API request",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                    "event_type": "unhandled_error"
                },
                exc_info=True
            )
            
            # Re-raise the exception to let FastAPI handle it
            raise exc


def get_request_id_filter():
    """Get a filter that adds request ID to log records."""
    class RequestIDFilter(logging.Filter):
        def filter(self, record):
            # Try to get request ID from context
            # This would need to be set by the middleware
            record.request_id = getattr(record, 'request_id', None)
            return True
    
    return RequestIDFilter()
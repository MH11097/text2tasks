from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import redis
from typing import Optional
import os

from .config import settings
from .logging_config import get_logger

logger = get_logger(__name__)

# Redis connection for rate limiting (optional)
redis_client: Optional[redis.Redis] = None

try:
    # Try to connect to Redis if available
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    redis_client = redis.from_url(redis_url, decode_responses=True, socket_timeout=5)
    # Test connection
    redis_client.ping()
    logger.info("Connected to Redis for rate limiting")
except Exception as e:
    logger.warning(f"Redis not available, using in-memory rate limiting: {e}")
    redis_client = None

def get_api_key_identifier(request: Request) -> str:
    """Extract identifier for rate limiting - prefer API key, fallback to IP"""
    # Check for API key in headers
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return f"api_key:{api_key}"
    
    # Fallback to IP address
    return f"ip:{get_remote_address(request)}"

# Configure limiter
if redis_client:
    # Use Redis backend
    limiter = Limiter(
        key_func=get_api_key_identifier,
        storage_uri=os.getenv("REDIS_URL", "redis://localhost:6379")
    )
else:
    # Use in-memory backend (not recommended for production)
    limiter = Limiter(
        key_func=get_api_key_identifier,
        default_limits=["1000/hour"]
    )

def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Custom rate limit exceeded handler with structured logging"""
    identifier = get_api_key_identifier(request)
    
    logger.warning(
        "Rate limit exceeded",
        extra={
            "identifier": identifier,
            "path": request.url.path,
            "method": request.method,
            "limit": str(exc.detail)
        }
    )
    
    response = JSONResponse(
        status_code=429,
        content={
            "error": "Rate limit exceeded",
            "detail": f"Rate limit exceeded: {exc.detail}",
            "retry_after": getattr(exc, 'retry_after', None)
        }
    )
    
    # Add rate limiting headers
    response.headers["X-RateLimit-Limit"] = str(exc.detail)
    response.headers["X-RateLimit-Remaining"] = "0"
    if hasattr(exc, 'retry_after'):
        response.headers["Retry-After"] = str(exc.retry_after)
    
    return response

# Rate limiting decorators for different endpoints
def write_endpoint_limit():
    """Rate limit for write endpoints (ingest, task updates)"""
    return limiter.limit("100/minute")

def read_endpoint_limit():
    """Rate limit for read endpoints"""
    return limiter.limit("500/minute")

def health_endpoint_limit():
    """Rate limit for health checks (more permissive)"""
    return limiter.limit("1000/minute")
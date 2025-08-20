from fastapi import Request, Response, HTTPException, Header
from fastapi.security import HTTPBearer
from starlette.middleware.base import BaseHTTPMiddleware
import re
from typing import Optional
import html

from .config import settings
from .logging_config import get_logger

logger = get_logger(__name__)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # Content Security Policy
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        response.headers["Content-Security-Policy"] = csp
        
        # HTTPS enforcement (when not in debug mode)
        if not settings.debug:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response

class InputValidationError(Exception):
    """Custom exception for input validation errors"""
    pass

def validate_text_input(text: str, max_length: int = 50000, field_name: str = "text") -> str:
    """
    Validate and sanitize text input
    
    Args:
        text: Input text to validate
        max_length: Maximum allowed length
        field_name: Name of the field for error messages
    
    Returns:
        Sanitized text
        
    Raises:
        InputValidationError: If validation fails
    """
    if not isinstance(text, str):
        raise InputValidationError(f"{field_name} must be a string")
    
    # Check length
    if len(text) > max_length:
        raise InputValidationError(f"{field_name} exceeds maximum length of {max_length} characters")
    
    # Check for null bytes
    if '\x00' in text:
        raise InputValidationError(f"{field_name} contains null bytes")
    
    # Basic XSS prevention - escape HTML
    sanitized_text = html.escape(text)
    
    # Check for potentially malicious patterns
    suspicious_patterns = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'vbscript:',
        r'onload\s*=',
        r'onerror\s*=',
        r'onclick\s*=',
    ]
    
    for pattern in suspicious_patterns:
        if re.search(pattern, text, re.IGNORECASE | re.DOTALL):
            logger.warning(f"Suspicious pattern detected in {field_name}", extra={
                "pattern": pattern,
                "text_preview": text[:100]
            })
            # Don't block, but log for monitoring
    
    return sanitized_text

def validate_source_input(source: str) -> str:
    """Validate source field input"""
    if not isinstance(source, str):
        raise InputValidationError("source must be a string")
    
    # Whitelist allowed sources
    allowed_sources = ["email", "meeting", "note", "other", "document", "chat"]
    
    if source not in allowed_sources:
        raise InputValidationError(f"source must be one of: {', '.join(allowed_sources)}")
    
    return source

def validate_task_status(status: str) -> str:
    """Validate task status input"""
    if not isinstance(status, str):
        raise InputValidationError("status must be a string")
    
    # Whitelist allowed statuses
    allowed_statuses = ["new", "in_progress", "blocked", "done"]
    
    if status not in allowed_statuses:
        raise InputValidationError(f"status must be one of: {', '.join(allowed_statuses)}")
    
    return status

def validate_owner_input(owner: Optional[str]) -> Optional[str]:
    """Validate owner field input"""
    if owner is None:
        return None
    
    if not isinstance(owner, str):
        raise InputValidationError("owner must be a string")
    
    # Check length
    if len(owner) > 100:
        raise InputValidationError("owner exceeds maximum length of 100 characters")
    
    # Basic sanitization
    owner = owner.strip()
    
    # Check for potentially malicious patterns
    if re.search(r'[<>"\']', owner):
        raise InputValidationError("owner contains invalid characters")
    
    return html.escape(owner)

def validate_date_input(date_str: Optional[str]) -> Optional[str]:
    """Validate date input (YYYY-MM-DD format)"""
    if date_str is None:
        return None
    
    if not isinstance(date_str, str):
        raise InputValidationError("date must be a string")
    
    # Validate YYYY-MM-DD format
    date_pattern = r'^\d{4}-\d{2}-\d{2}$'
    if not re.match(date_pattern, date_str):
        raise InputValidationError("date must be in YYYY-MM-DD format")
    
    # Additional validation could include checking if date is valid
    try:
        year, month, day = map(int, date_str.split('-'))
        if not (1 <= month <= 12):
            raise InputValidationError("Invalid month in date")
        if not (1 <= day <= 31):
            raise InputValidationError("Invalid day in date")
        if year < 2020 or year > 2030:
            raise InputValidationError("Year must be between 2020 and 2030")
    except ValueError:
        raise InputValidationError("Invalid date format")
    
    return date_str

def validate_question_input(question: str) -> str:
    """Validate question input for Q&A"""
    if not isinstance(question, str):
        raise InputValidationError("question must be a string")
    
    # Check length
    if len(question) > 1000:
        raise InputValidationError("question exceeds maximum length of 1000 characters")
    
    if len(question.strip()) < 3:
        raise InputValidationError("question must be at least 3 characters long")
    
    # Sanitize
    question = html.escape(question.strip())
    
    return question

def validate_api_key_header(api_key: Optional[str]) -> str:
    """Validate API key from header"""
    if not api_key:
        raise HTTPException(status_code=401, detail="Missing API key")
    
    if not isinstance(api_key, str):
        raise HTTPException(status_code=401, detail="Invalid API key format")
    
    # Basic format validation
    if len(api_key) < 10:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    # Check for suspicious patterns
    if re.search(r'[<>"\'\x00-\x1f]', api_key):
        logger.warning("Suspicious API key format detected", extra={
            "key_preview": api_key[:10] + "..." if len(api_key) > 10 else api_key
        })
        raise HTTPException(status_code=401, detail="Invalid API key format")
    
    return api_key

def validate_request_size(request: Request, max_size: int = 1024 * 1024):  # 1MB default
    """Validate request content length"""
    content_length = request.headers.get("content-length")
    
    if content_length:
        try:
            size = int(content_length)
            if size > max_size:
                raise HTTPException(
                    status_code=413,
                    detail=f"Request too large. Maximum size: {max_size} bytes"
                )
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid content-length header")

class RequestSizeMiddleware(BaseHTTPMiddleware):
    """Middleware to validate request size"""
    
    def __init__(self, app, max_size: int = 1024 * 1024):  # 1MB default
        super().__init__(app)
        self.max_size = max_size
    
    async def dispatch(self, request: Request, call_next):
        # Skip size check for GET requests
        if request.method in ["GET", "HEAD", "OPTIONS"]:
            return await call_next(request)
        
        validate_request_size(request, self.max_size)
        return await call_next(request)

async def verify_api_key(x_api_key: Optional[str] = Header(None)):
    """Verify API key from header"""
    validated_key = validate_api_key_header(x_api_key)
    
    if validated_key != settings.api_key:
        logger.warning("Invalid API key attempted", extra={"key_preview": validated_key[:10] + "..." if len(validated_key) > 10 else validated_key})
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return validated_key
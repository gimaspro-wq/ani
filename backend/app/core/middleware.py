"""Middleware for trace ID propagation and security headers."""
import logging
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import settings
from app.core.logging_config import set_trace_id, get_trace_id

logger = logging.getLogger(__name__)


class TraceIDMiddleware(BaseHTTPMiddleware):
    """Add trace ID to request context and response headers."""
    
    async def dispatch(self, request: Request, call_next):
        """Process request with trace ID."""
        # Generate or extract trace ID
        trace_id = request.headers.get("X-Trace-ID", str(uuid4()))
        set_trace_id(trace_id)
        
        # Process request
        response: Response = await call_next(request)
        
        # Add trace ID to response headers
        response.headers["X-Trace-ID"] = get_trace_id()
        
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""
    
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        
        # Only add HSTS header when using HTTPS (production with COOKIE_SECURE=true)
        if settings.COOKIE_SECURE:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )
        
        return response

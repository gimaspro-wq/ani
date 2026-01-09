"""Custom exceptions and error codes."""
from typing import Any


class AppError(Exception):
    """Base application error."""
    
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 500,
        details: dict[str, Any] | None = None
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


# Alias for clarity at the application layer
ApplicationError = AppError


class ValidationError(AppError):
    """Validation error."""
    
    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(
            code="VALIDATION_ERROR",
            message=message,
            status_code=400,
            details=details
        )


class AuthenticationError(AppError):
    """Authentication error."""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            code="AUTHENTICATION_ERROR",
            message=message,
            status_code=401
        )


class AuthorizationError(AppError):
    """Authorization error."""
    
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(
            code="AUTHORIZATION_ERROR",
            message=message,
            status_code=403
        )


class NotFoundError(AppError):
    """Resource not found error."""
    
    def __init__(self, message: str = "Resource not found"):
        super().__init__(
            code="NOT_FOUND",
            message=message,
            status_code=404
        )


class ConflictError(AppError):
    """Conflict error."""
    
    def __init__(self, message: str = "Resource conflict", status_code: int = 409):
        super().__init__(
            code="CONFLICT",
            message=message,
            status_code=status_code
        )


class RateLimitError(AppError):
    """Rate limit exceeded error."""
    
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(
            code="RATE_LIMIT_EXCEEDED",
            message=message,
            status_code=429
        )


class InternalError(AppError):
    """Internal server error."""
    
    def __init__(self, message: str = "Internal server error"):
        super().__init__(
            code="INTERNAL_ERROR",
            message=message,
            status_code=500
        )

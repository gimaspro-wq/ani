"""Global exception handling middleware."""
import logging
from typing import Any

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.errors import AppError
from app.core.logging_config import get_trace_id

logger = logging.getLogger(__name__)


class ErrorResponse:
    """Standardized error response."""
    
    def __init__(self, code: str, message: str, trace_id: str):
        self.error = {
            "code": code,
            "message": message,
            "trace_id": trace_id
        }
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {"error": self.error}


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Handle custom application errors."""
    trace_id = get_trace_id()
    
    logger.warning(
        f"Application error: {exc.code} - {exc.message}",
        extra={"extra_fields": {"trace_id": trace_id, "details": exc.details}}
    )
    
    error_response = ErrorResponse(
        code=exc.code,
        message=exc.message,
        trace_id=trace_id
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.to_dict()
    )


async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors."""
    trace_id = get_trace_id()
    
    logger.warning(
        "Validation error",
        extra={"extra_fields": {"trace_id": trace_id, "errors": exc.errors()}}
    )
    
    error_response = ErrorResponse(
        code="VALIDATION_ERROR",
        message="Invalid request data",
        trace_id=trace_id
    )
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=error_response.to_dict()
    )


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Handle Starlette HTTP exceptions."""
    trace_id = get_trace_id()
    
    logger.warning(
        f"HTTP exception: {exc.status_code} - {exc.detail}",
        extra={"extra_fields": {"trace_id": trace_id}}
    )
    
    error_response = ErrorResponse(
        code="HTTP_ERROR",
        message=str(exc.detail),
        trace_id=trace_id
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.to_dict()
    )


async def unhandled_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Handle all unhandled exceptions."""
    trace_id = get_trace_id()
    
    logger.exception(
        "Unhandled exception",
        extra={"extra_fields": {"trace_id": trace_id}},
        exc_info=exc
    )
    
    error_response = ErrorResponse(
        code="INTERNAL_ERROR",
        message="An unexpected error occurred",
        trace_id=trace_id
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.to_dict()
    )

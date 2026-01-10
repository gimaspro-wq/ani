"""Structured JSON logging configuration."""
import logging
import json
import sys
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

# Context variable to store trace_id across async calls
trace_id_var: ContextVar[str] = ContextVar("trace_id", default="")
_service_name = "app"
_include_stack_traces = False


def get_trace_id() -> str:
    """Get current trace_id from context."""
    return trace_id_var.get() or str(uuid4())


def set_trace_id(trace_id: str) -> None:
    """Set trace_id in context."""
    trace_id_var.set(trace_id)


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "trace_id": get_trace_id(),
            "request_id": get_trace_id(),
            "service": _service_name,
        }
        
        # Add exception info if present
        if record.exc_info and _include_stack_traces:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)
        
        return json.dumps(log_data)


def setup_logging(debug: bool = False, service_name: str | None = None) -> None:
    """Configure structured JSON logging."""
    global _service_name, _include_stack_traces

    level = logging.DEBUG if debug else logging.INFO
    _service_name = service_name or _service_name
    _include_stack_traces = bool(debug)
    
    # Create handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers = [handler]
    
    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

"""OpenTelemetry tracing configuration."""
import logging
from typing import Optional

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from app.core.config import settings

logger = logging.getLogger(__name__)


def setup_tracing(app) -> Optional[TracerProvider]:
    """
    Setup OpenTelemetry tracing if enabled.
    
    Args:
        app: FastAPI application instance
        
    Returns:
        TracerProvider if tracing is enabled, None otherwise
    """
    if not settings.TRACING_ENABLED:
        logger.info("OpenTelemetry tracing is disabled")
        return None
    
    if not settings.OTEL_EXPORTER_OTLP_ENDPOINT:
        logger.warning(
            "TRACING_ENABLED is true but OTEL_EXPORTER_OTLP_ENDPOINT is not set. "
            "Tracing will be disabled."
        )
        return None
    
    try:
        # Create resource
        resource = Resource(attributes={
            SERVICE_NAME: settings.OTEL_SERVICE_NAME
        })
        
        # Create tracer provider
        provider = TracerProvider(resource=resource)
        
        # Create OTLP exporter
        otlp_exporter = OTLPSpanExporter(
            endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT,
            insecure=True  # Use insecure for local dev, should be secure in prod
        )
        
        # Add span processor
        provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
        
        # Set as global tracer provider
        trace.set_tracer_provider(provider)
        
        # Instrument FastAPI
        FastAPIInstrumentor.instrument_app(app)
        
        logger.info(
            f"OpenTelemetry tracing enabled. "
            f"Service: {settings.OTEL_SERVICE_NAME}, "
            f"Endpoint: {settings.OTEL_EXPORTER_OTLP_ENDPOINT}"
        )
        
        return provider
        
    except Exception as e:
        logger.error(f"Failed to setup OpenTelemetry tracing: {e}")
        return None

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from prometheus_fastapi_instrumentator import Instrumentator

from app.api.v1 import auth, users, library, anime, internal, admin
from app.core.config import settings
from app.core.errors import AppError
from app.core.exception_handlers import (
    app_error_handler,
    http_exception_handler,
    unhandled_exception_handler,
    validation_error_handler,
)
from app.core.logging_config import setup_logging
from app.core.middleware import AccessLogMiddleware, SecurityHeadersMiddleware, TraceIDMiddleware
from app.core.rate_limiting import limiter, RateLimitMiddleware
from app.core.tracing import setup_tracing
from app.infrastructure.adapters.redis_client import redis_client
from app.db.database import engine






# Setup logging
setup_logging(debug=settings.DEBUG)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown."""
    
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.VERSION} (env={settings.ENV})")
    
    # Connect to Redis (skip in test mode if Redis is not available)
    try:
        await redis_client.connect()
        logger.info("Redis connected successfully")
    except Exception as e:
        logger.warning(f"Failed to connect to Redis: {e}")
        if settings.ENV == "production":
            logger.error("Redis connection is required in production")
            raise
        # In dev/test, continue without Redis
        logger.info("Continuing without Redis connection")
    
    # Validate migrations in production
    if settings.ENV == "production":
        from app.core.migration_validator import validate_migrations
        try:
            if not validate_migrations(settings.DATABASE_URL):
                raise RuntimeError(
                    "Database migrations are not up to date. "
                    "Run 'alembic upgrade head' before starting the application."
                )
        except Exception as e:
            logger.error(f"Migration validation failed: {e}")
            raise
    else:
        logger.info("Database migrations must be run separately from application startup.")
    
    logger.info("Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("Application shutdown initiated")
    
    # Disconnect Redis
    try:
        await redis_client.disconnect()
    except Exception:
        pass  # Ignore shutdown errors
    
    try:
        await engine.dispose()
    except Exception:
        pass  # Ignore shutdown errors
    
    logger.info("Application shutdown complete")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    debug=settings.DEBUG,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# Add exception handlers
app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

# Add middlewares (order matters - they are applied in reverse)
# 1. Security headers (outermost)
app.add_middleware(SecurityHeadersMiddleware)

# 2. Trace ID
app.add_middleware(TraceIDMiddleware)

# 3. Rate limiting
if settings.RATE_LIMIT_ENABLED:
    app.add_middleware(RateLimitMiddleware)
    app.state.limiter = limiter

# 4. Access logging
app.add_middleware(AccessLogMiddleware)

# 5. CORS (innermost, closest to routes)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
    expose_headers=["Content-Type", "X-Trace-ID"],
    max_age=600,
)

# Setup Prometheus metrics
if settings.METRICS_ENABLED:
    instrumentator = Instrumentator()
    instrumentator.instrument(app).expose(app, endpoint="/metrics")
    logger.info("Prometheus metrics enabled at /metrics")

# Setup OpenTelemetry tracing
if settings.TRACING_ENABLED:
    setup_tracing(app)

# Include routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(library.router, prefix="/api/v1")
app.include_router(anime.router, prefix="/api/v1")
app.include_router(internal.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": f"Welcome to {settings.APP_NAME}"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "version": settings.VERSION}

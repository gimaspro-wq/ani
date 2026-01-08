# Anirohi Backend - Production-Ready API

## Overview

Production-ready FastAPI backend with:
- Clean Architecture patterns
- RBAC (Role-Based Access Control)
- Rate limiting
- Redis caching
- Prometheus metrics
- OpenTelemetry tracing
- Structured JSON logging
- Secure by default

## Architecture

The backend follows **Clean Architecture Light** principles:

```
app/
├── api/                    # HTTP layer (FastAPI routers)
├── application/            # Business logic (use cases)
│   ├── use_cases/         # Application services
│   └── dtos/              # Data transfer objects
├── domain/                # Business rules
│   ├── entities/          # Domain models
│   └── interfaces/        # Repository interfaces
├── infrastructure/        # External adapters
│   ├── adapters/          # Service implementations
│   └── repositories/      # Data access implementations
├── core/                  # Cross-cutting concerns
│   ├── config.py          # Configuration
│   ├── errors.py          # Custom exceptions
│   ├── logging_config.py  # Structured logging
│   ├── middleware.py      # Security headers, trace ID
│   ├── rate_limiting.py   # Rate limiting
│   ├── rbac.py            # Permission checking
│   └── container.py       # Dependency injection
├── db/                    # Database
│   ├── models.py          # ORM models
│   └── database.py        # Database connection
└── main.py                # Application entry point
```

### Dependency Flow

```
api → application → domain ← infrastructure
                      ↓
                    core
```

- **api**: HTTP endpoints, request/response handling
- **application**: Use cases, business logic orchestration
- **domain**: Interfaces, business rules
- **infrastructure**: Database, Redis, security implementations
- **core**: Configuration, errors, logging, middleware

## Environment Variables

All environment variables must be configured before running. See `.env.example` for reference.

### Required Variables

```bash
# Database (REQUIRED)
DATABASE_URL=postgresql+asyncpg://user:password@host:port/database

# Security (REQUIRED, NO DEFAULTS)
SECRET_KEY=<generate-with-openssl-rand-hex-32>
```

### Optional Variables

```bash
# Application
APP_NAME=Anirohi API
VERSION=1.0.0
DEBUG=false
ENV=production  # dev, production, test

# Security
ALGORITHM=HS256
JWT_ACCESS_TTL_MINUTES=15
REFRESH_TTL_DAYS=30
COOKIE_SECURE=true  # Must be true in production with HTTPS

# CORS
ALLOWED_ORIGINS=https://yourdomain.com

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_MAX_CONNECTIONS=10

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60

# Observability
METRICS_ENABLED=true
TRACING_ENABLED=false
OTEL_SERVICE_NAME=anirohi-api
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
```

## Security Features

### 1. Strict Configuration Validation

- **Fail-fast on startup** if required env vars are missing
- **No default secrets** - must provide SECRET_KEY
- **Production validation** - enforces strong secrets in production mode

### 2. Refresh Token Security

- **Hashed storage** - tokens are hashed before storage
- **Token rotation** - new token issued on refresh, old token revoked
- **Reuse detection** - revoked tokens can't be reused
- **Expiration** - configurable TTL (default: 30 days)

### 3. RBAC (Role-Based Access Control)

Default roles:
- **user**: Standard user (library access)
- **admin**: Full administrative access

Default permissions:
- `library:read` - Read user library
- `library:write` - Modify user library
- `library:delete` - Delete library items
- `user:read` - Read user information
- `user:write` - Modify user information
- `admin:access` - Full administrative access

Usage in endpoints:
```python
from app.core.rbac import require_permission

@router.get("/admin/users")
@require_permission("admin:access")
async def list_users(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    ...
```

### 4. Rate Limiting

- **Per-IP limiting** using slowapi + Redis
- **Default**: 60 requests per minute
- **Configurable** via `RATE_LIMIT_PER_MINUTE`
- **X-Forwarded-For support** for proxied requests

### 5. Security Headers

Automatically applied to all responses:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Content-Security-Policy: default-src 'self'; ...`
- `Strict-Transport-Security` (when COOKIE_SECURE=true)

### 6. Error Handling

All errors return standardized format:
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message",
    "trace_id": "uuid"
  }
}
```

- **Never exposes stack traces** to clients
- **Trace ID propagation** for request tracking
- **Structured logging** of all errors

## Observability

### Structured Logging

All logs are output as JSON:
```json
{
  "timestamp": "2026-01-08T16:00:00.000Z",
  "level": "INFO",
  "logger": "app.main",
  "message": "Application startup complete",
  "trace_id": "uuid"
}
```

### Prometheus Metrics

Metrics endpoint: `/metrics`

Automatically tracked:
- Request count
- Request duration
- Request size
- Response size
- Active requests
- HTTP status codes

### OpenTelemetry Tracing (Optional)

Enable with `TRACING_ENABLED=true` and `OTEL_EXPORTER_OTLP_ENDPOINT`.

Traces:
- HTTP requests
- Database queries
- External API calls

### Trace ID Propagation

Every request gets a unique `trace_id`:
- Generated automatically or extracted from `X-Trace-ID` header
- Included in all logs
- Returned in `X-Trace-ID` response header
- Propagated through async context

## Development

### Setup

```bash
# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Configure environment
cp .env.example .env
# Edit .env and set required variables

# Run database migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py -v
```

### Database Migrations

```bash
# Create new migration
alembic revision -m "description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# Show current revision
alembic current

# Show migration history
alembic history
```

## Deployment

### Docker

```bash
# Build image
docker build -t anirohi-backend:latest ./backend

# Run with docker-compose
docker compose up -d

# View logs
docker compose logs -f backend
```

### Production Checklist

- [ ] Set `ENV=production`
- [ ] Set `DEBUG=false`
- [ ] Generate strong `SECRET_KEY` (min 32 chars)
- [ ] Set `COOKIE_SECURE=true`
- [ ] Configure `ALLOWED_ORIGINS` (no wildcards)
- [ ] Set up HTTPS/TLS
- [ ] Configure PostgreSQL connection pooling
- [ ] Set up Redis for rate limiting and caching
- [ ] Configure log aggregation (e.g., ELK, Loki)
- [ ] Set up metrics monitoring (Prometheus + Grafana)
- [ ] Enable health checks in orchestrator
- [ ] Set resource limits (CPU, memory)
- [ ] Configure backup strategy for database
- [ ] Set up alerting for errors and metrics
- [ ] Review and update CORS origins
- [ ] Validate rate limits for production load

### Health Checks

- **Liveness**: `GET /health`
- **Readiness**: `GET /health` (checks DB connection in future)
- **Metrics**: `GET /metrics` (Prometheus format)

### Docker Healthcheck

Dockerfile includes built-in healthcheck:
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').read()" || exit 1
```

## API Documentation

When `DEBUG=true`, interactive API docs are available:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

In production (`DEBUG=false`), docs are disabled for security.

## Monitoring & Alerting

### Key Metrics to Monitor

1. **Application Health**
   - HTTP 5xx error rate
   - Request latency (p50, p95, p99)
   - Active database connections
   - Redis connection status

2. **Business Metrics**
   - Registration rate
   - Login success/failure rate
   - API endpoint usage
   - Library operations

3. **Infrastructure**
   - CPU usage
   - Memory usage
   - Disk I/O
   - Network I/O

### Recommended Alerts

- HTTP 5xx rate > 1%
- p95 latency > 500ms
- Error log rate > 10/min
- Database connection pool exhaustion
- Redis connection failures

## Troubleshooting

### Common Issues

**Issue**: Application won't start - "Configuration validation failed"
- **Fix**: Ensure all required env vars are set (DATABASE_URL, SECRET_KEY)

**Issue**: Database connection errors
- **Fix**: Check DATABASE_URL format, ensure PostgreSQL is running

**Issue**: Redis connection errors in development
- **Fix**: Redis is optional in dev/test mode, app will continue without it

**Issue**: Rate limiting not working
- **Fix**: Ensure Redis is connected and `RATE_LIMIT_ENABLED=true`

**Issue**: Metrics endpoint returns 404
- **Fix**: Set `METRICS_ENABLED=true`

### Debug Mode

Enable detailed logging:
```bash
DEBUG=true
ENV=dev
```

This will:
- Show SQL queries
- Enable API documentation
- Log at DEBUG level
- Disable some security headers

**Never use in production!**

## Contributing

1. Follow Clean Architecture patterns
2. Add tests for new features
3. Update documentation
4. Ensure all tests pass
5. Run linters before committing

## License

[Your License Here]

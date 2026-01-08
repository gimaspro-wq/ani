# Backend Setup Guide

Complete guide for setting up the FastAPI authentication backend.

## Prerequisites

- Python 3.11 or higher
- PostgreSQL 16+ (or Docker to run postgres via docker-compose)
- OpenSSL (for generating secure keys)

## Quick Start (Docker)

The easiest way to get started is with Docker Compose:

```bash
# From repository root
docker-compose up -d

# Backend will be available at http://localhost:8000
# API docs at http://localhost:8000/docs
```

This will:
1. Start PostgreSQL database
2. Run Alembic migrations automatically
3. Start the FastAPI backend

## Manual Setup

### 1. Install Python Dependencies

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install dev dependencies (for tests)
pip install -r requirements-dev.txt
```

### 2. Configure Environment Variables

Copy the example environment file:

```bash
cp .env.example .env
```

**IMPORTANT**: Edit `.env` and set these values:

#### Required Settings

```bash
# Generate a secure SECRET_KEY (CRITICAL!)
SECRET_KEY=$(openssl rand -hex 32)

# Database connection string
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/ani_db
```

#### Optional Settings (with defaults)

```bash
# App settings
APP_NAME=Anirohi API
VERSION=1.0.0
DEBUG=true              # Set to false in production
ENV=dev                 # Set to "production" in production

# JWT/Auth settings
JWT_ACCESS_TTL_MINUTES=15    # Access token lifetime (15 minutes recommended)
REFRESH_TTL_DAYS=30          # Refresh token lifetime (30 days)
COOKIE_SECURE=false          # MUST be true in production with HTTPS

# CORS (comma-separated)
ALLOWED_ORIGINS=http://localhost:3000
```

### 3. Setup Database

#### Option A: Using Docker

```bash
# Start only PostgreSQL
docker-compose up -d postgres

# Connection string will be:
# postgresql+asyncpg://ani_user:ani_password@localhost:5432/ani_db
```

#### Option B: Local PostgreSQL

```bash
# Create database
psql -U postgres
CREATE DATABASE ani_db;
CREATE USER ani_user WITH PASSWORD 'ani_password';
GRANT ALL PRIVILEGES ON DATABASE ani_db TO ani_user;
\q

# Update DATABASE_URL in .env
DATABASE_URL=postgresql+asyncpg://ani_user:ani_password@localhost:5432/ani_db
```

### 4. Run Database Migrations

```bash
# Apply migrations
alembic upgrade head

# To create a new migration (after model changes):
alembic revision --autogenerate -m "description"
```

### 5. Start the Backend

```bash
# Development mode (with auto-reload)
uvicorn app.main:app --reload --port 8000

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Backend will be available at:
- **API**: http://localhost:8000
- **Interactive docs**: http://localhost:8000/docs (dev only)
- **Alternative docs**: http://localhost:8000/redoc (dev only)
- **Health check**: http://localhost:8000/health

## Running Tests

```bash
cd backend

# Install test dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=app --cov-report=html
```

## Production Deployment Checklist

Before deploying to production, ensure:

### Security
- [ ] `SECRET_KEY` is set to a strong random value (min 32 characters)
- [ ] `SECRET_KEY` is different from any defaults or examples
- [ ] `COOKIE_SECURE=true` (requires HTTPS)
- [ ] `DEBUG=false`
- [ ] `ENV=production`
- [ ] Database credentials are not default values
- [ ] CORS `ALLOWED_ORIGINS` contains only your production domains (no wildcards)

### Database
- [ ] PostgreSQL is properly configured and secured
- [ ] Database backups are configured
- [ ] Migrations have been tested in staging
- [ ] Connection pooling is configured if needed

### Infrastructure
- [ ] Application is behind HTTPS (TLS certificate)
- [ ] Rate limiting is enabled (use nginx, cloudflare, or similar)
- [ ] Firewall rules are properly configured
- [ ] Health checks are configured
- [ ] Logging is configured and monitored

### Testing
- [ ] All tests pass (`pytest`)
- [ ] Manual testing of auth flows completed
- [ ] Load testing performed if expecting high traffic

## Environment Variables Reference

### Required in Production

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | JWT signing key (min 32 chars) | Generate with `openssl rand -hex 32` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://user:pass@host:5432/db` |

### Optional (with defaults)

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_NAME` | Anirohi API | Application name |
| `VERSION` | 1.0.0 | API version |
| `DEBUG` | false | Enable debug mode |
| `ENV` | dev | Environment (dev/production) |
| `ALGORITHM` | HS256 | JWT algorithm |
| `JWT_ACCESS_TTL_MINUTES` | 15 | Access token lifetime (minutes) |
| `REFRESH_TTL_DAYS` | 30 | Refresh token lifetime (days) |
| `COOKIE_SECURE` | false | Enable secure cookies (HTTPS required) |
| `ALLOWED_ORIGINS` | http://localhost:3000 | CORS allowed origins (comma-separated) |

## Troubleshooting

### SECRET_KEY validation error

**Error**: `ValueError: SECRET_KEY must be set`

**Solution**: Set `SECRET_KEY` in your `.env` file:
```bash
openssl rand -hex 32 > /tmp/secret.txt
# Copy the value from /tmp/secret.txt to your .env file
```

### SECRET_KEY too short in production

**Error**: `ValueError: SECRET_KEY must be at least 32 characters in production`

**Solution**: Generate a longer key:
```bash
openssl rand -hex 32  # Generates 64 character hex string
```

### Database connection failed

**Error**: `sqlalchemy.exc.OperationalError`

**Solutions**:
1. Verify PostgreSQL is running: `docker-compose ps` or `pg_isready`
2. Check DATABASE_URL format: `postgresql+asyncpg://user:pass@host:port/db`
3. Ensure database exists: `psql -U postgres -l`
4. Check credentials are correct

### Alembic migration errors

**Error**: `Target database is not up to date`

**Solution**:
```bash
# Check migration status
alembic current

# Apply missing migrations
alembic upgrade head
```

### CORS errors in browser

**Error**: `Access-Control-Allow-Origin header is missing`

**Solutions**:
1. Add frontend URL to `ALLOWED_ORIGINS` in `.env`
2. Ensure no trailing slashes in origins
3. Check the exact URL (including port) matches
4. Verify `allow_credentials=True` in CORS config

### Cookies not working

**Problems**:
- Refresh token not sent by browser
- Cookie not set after login/register

**Solutions**:
1. Frontend and backend must be on same domain OR:
2. Backend must include frontend domain in `ALLOWED_ORIGINS`
3. Requests must include `credentials: 'include'` (fetch API)
4. In dev with http://, `COOKIE_SECURE` must be `false`
5. Check browser console for SameSite warnings

## Development Tips

### Hot Reload

Use `--reload` flag for automatic reloading during development:
```bash
uvicorn app.main:app --reload
```

### Database Inspection

```bash
# Connect to database
docker-compose exec postgres psql -U ani_user -d ani_db

# List tables
\dt

# Inspect users table
\d users

# Query data
SELECT * FROM users;
```

### Test Endpoints Manually

Use the interactive docs at http://localhost:8000/docs or curl:

```bash
# Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpass123"}' \
  -c cookies.txt

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpass123"}' \
  -c cookies.txt

# Get current user (with Bearer token from login response)
curl http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer <access_token>"

# Refresh token (uses cookie)
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -b cookies.txt \
  -c cookies.txt

# Logout
curl -X POST http://localhost:8000/api/v1/auth/logout \
  -b cookies.txt
```

## Additional Resources

- [Architecture Documentation](./architecture.md)
- [Authentication Flow Details](./auth.md)
- [API Plan & Roadmap](./api-plan.md)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Async Documentation](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)

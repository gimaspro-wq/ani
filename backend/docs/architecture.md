# Backend Architecture

## Overview

The Anirohi backend is a FastAPI application that provides authentication and user management APIs. It follows a clean architecture pattern with clear separation of concerns.

## Technology Stack

- **Framework**: FastAPI 0.115.6
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: JWT (access tokens) + httpOnly cookies (refresh tokens)
- **Password Hashing**: bcrypt via passlib
- **Validation**: Pydantic v2
- **Testing**: pytest with httpx

## Directory Structure

```
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── auth.py          # Auth endpoints (register, login, refresh, logout)
│   │       └── users.py         # User endpoints (/users/me)
│   ├── core/
│   │   ├── config.py            # Settings and configuration
│   │   ├── security.py          # Password hashing, JWT utilities
│   │   └── dependencies.py      # FastAPI dependencies (auth)
│   ├── db/
│   │   ├── database.py          # SQLAlchemy engine and session
│   │   └── models.py            # Database models (User, RefreshToken)
│   ├── schemas/
│   │   └── auth.py              # Pydantic schemas for request/response
│   ├── services/
│   │   └── auth.py              # Business logic for authentication
│   └── main.py                  # FastAPI application entry point
├── docs/                        # Documentation
├── tests/                       # Test suite
├── requirements.txt             # Python dependencies
├── requirements-dev.txt         # Dev dependencies (pytest, etc.)
├── Dockerfile                   # Docker image definition
└── .env.example                 # Example environment variables
```

## Architectural Layers

### 1. API Layer (`app/api/`)

Handles HTTP requests and responses. Uses FastAPI's dependency injection for:
- Database sessions
- Authentication
- Request validation

**Responsibilities:**
- Parse and validate request data
- Call service layer
- Format responses
- Set/clear cookies

### 2. Service Layer (`app/services/`)

Contains business logic and orchestrates database operations.

**Responsibilities:**
- User registration and authentication
- Token creation and validation
- Token rotation and revocation
- Business rules enforcement

### 3. Data Access Layer (`app/db/`)

Manages database models and sessions.

**Models:**
- `User`: User accounts with email and hashed password
- `RefreshToken`: Refresh tokens with expiration and revocation support

### 4. Core Layer (`app/core/`)

Shared utilities and configuration.

**Components:**
- `config.py`: Environment-based settings
- `security.py`: Cryptographic functions (hashing, JWT)
- `dependencies.py`: FastAPI dependency functions

### 5. Schema Layer (`app/schemas/`)

Pydantic models for API contracts (request/response validation).

## Design Decisions

### Why FastAPI?

- Modern Python framework with automatic OpenAPI docs
- Native async support
- Type hints and validation with Pydantic
- Fast performance (comparable to Node.js)
- Great developer experience

### Why SQLAlchemy?

- Industry-standard Python ORM
- Type-safe database access
- Migration support via Alembic
- Works well with PostgreSQL

### Why PostgreSQL?

- Robust, production-ready relational database
- ACID compliance
- JSON support for future extensibility
- Wide ecosystem and hosting options

### Token Storage Strategy

**Refresh Tokens:**
- Stored hashed in database (not plain text)
- Enables token rotation
- Allows remote revocation
- Supports per-user logout

**Access Tokens:**
- Stateless JWT
- Short TTL (30 minutes)
- Not stored in database
- Verified via signature

### Password Security

- Bcrypt hashing (industry standard)
- Automatic salt generation
- Configurable work factor
- Resistant to rainbow table attacks

## Configuration

All configuration is loaded from environment variables via `pydantic-settings`:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | PostgreSQL connection string | Database connection |
| `SECRET_KEY` | (required) | JWT signing key |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 30 | Access token TTL |
| `REFRESH_TOKEN_EXPIRE_DAYS` | 30 | Refresh token TTL |
| `ALLOWED_ORIGINS` | `http://localhost:3000` | CORS allowed origins |

## CORS Configuration

CORS is configured via FastAPI middleware:
- Allows credentials (cookies)
- Configured origins from environment
- All methods and headers allowed for configured origins

## Database Schema

### Users Table

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR UNIQUE NOT NULL,
    hashed_password VARCHAR NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL
);
```

### Refresh Tokens Table

```sql
CREATE TABLE refresh_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) NOT NULL,
    token_hash VARCHAR UNIQUE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    revoked BOOLEAN DEFAULT FALSE NOT NULL
);
```

## Error Handling

FastAPI automatically handles:
- Validation errors (422 Unprocessable Entity)
- Not found (404)
- Server errors (500)

Custom exceptions:
- `HTTPException` for business logic errors (401, 403, 400)

## Testing Strategy

Tests use:
- In-memory SQLite database (fast, isolated)
- FastAPI TestClient
- Pytest fixtures for setup/teardown
- Dependency overrides for database injection

## Future Considerations

**Not Implemented (By Design):**
- OTP/2FA authentication
- Social login (OAuth)
- Email verification
- Password reset
- User profiles beyond email
- Field include/exclude in responses
- Rate limiting
- Ads modules

**Could Be Added Later:**
- Redis for token blacklisting
- Email service integration
- User roles and permissions
- API rate limiting
- Logging and monitoring
- Health checks with database ping

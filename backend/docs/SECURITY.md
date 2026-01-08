# Security Implementation Details

This document provides detailed information about the security measures implemented in the backend.

## Table of Contents

1. [Authentication Security](#authentication-security)
2. [Cookie Security](#cookie-security)
3. [JWT Implementation](#jwt-implementation)
4. [CORS Configuration](#cors-configuration)
5. [Security Headers](#security-headers)
6. [Production Requirements](#production-requirements)
7. [Security Audit Verification](#security-audit-verification)

## Authentication Security

### Password Hashing

- **Algorithm**: bcrypt via passlib
- **Implementation**: `backend/app/core/security.py`
- **Rounds**: Default bcrypt cost factor (12)
- **Verification**: Constant-time comparison via passlib

```python
# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
```

### Refresh Token Storage

- **Storage**: Only bcrypt hash stored in database
- **Token Generation**: 32-byte URL-safe random token via `secrets.token_urlsafe(32)`
- **Plaintext**: Never stored, only returned once to client
- **Rotation**: Old token revoked before new token created
- **Expiration**: Configurable via `REFRESH_TTL_DAYS` (default 30 days)

**Database Schema:**
```python
class RefreshToken(Base):
    token_hash = Column(String, unique=True, index=True, nullable=False)  # bcrypt hash only
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked = Column(Boolean, default=False, nullable=False)
```

**Implementation:** `backend/app/services/auth.py:95-96`
```python
token = secrets.token_urlsafe(32)  # Generated once
token_hash = get_password_hash(token)  # Only hash stored
```

### Token Rotation Flow

1. Client sends refresh request with refresh token cookie
2. Backend verifies token hash against database
3. Backend revokes old refresh token (sets `revoked=True`)
4. Backend generates new refresh token
5. Backend stores new token hash in database
6. Backend sends new access token + sets new refresh cookie

**Implementation:** `backend/app/api/v1/auth.py:112-120`

### User Account Security

- **Active Flag**: Users can be disabled via `is_active` field
- **Timestamps**: `created_at` and `updated_at` tracked
- **Email Uniqueness**: Enforced at database level
- **Credential Validation**: Timing-attack resistant via bcrypt

## Cookie Security

### Cookie Configuration

All authentication cookies use consistent security flags:

```python
response.set_cookie(
    key=REFRESH_COOKIE_NAME,  # Centralized constant
    value=refresh_token,
    httponly=True,           # Prevents JavaScript access (XSS protection)
    secure=settings.COOKIE_SECURE,  # HTTPS only in production
    samesite="lax",          # CSRF protection
    path="/",                # Available to all endpoints
    max_age=settings.REFRESH_TTL_DAYS * 24 * 60 * 60,  # 30 days
)
```

**Cookie Name:** Centralized as `REFRESH_COOKIE_NAME` constant in `backend/app/core/config.py`

### Cookie Flags Explained

| Flag | Value | Purpose |
|------|-------|---------|
| `httponly` | `True` | Prevents client-side JavaScript from accessing cookie (XSS mitigation) |
| `secure` | From `COOKIE_SECURE` env | Ensures cookie only sent over HTTPS in production |
| `samesite` | `lax` | Prevents cross-site request forgery (CSRF) while allowing normal navigation |
| `path` | `/` | Cookie available to all API endpoints |
| `max_age` | 30 days (2,592,000 seconds) | Cookie expires after REFRESH_TTL_DAYS |

### Cookie Deletion on Logout

Explicit deletion with matching flags:

```python
response.delete_cookie(key=REFRESH_COOKIE_NAME, path="/", samesite="lax")
```

**Verification:** `backend/app/api/v1/auth.py:149`

## JWT Implementation

### JWT Configuration

- **Algorithm**: HS256 (HMAC with SHA-256)
- **Signing Key**: From `SECRET_KEY` environment variable (required, min 32 chars in production)
- **Token Type**: Embedded in payload (`"type": "access"`)
- **Expiration**: 15 minutes (configurable via `JWT_ACCESS_TTL_MINUTES`)

### JWT Payload Structure

```json
{
  "sub": "123",              // User ID (as string for JWT spec)
  "exp": 1234567890,         // Expiration timestamp
  "type": "access"           // Token type verification
}
```

### JWT Security Measures

1. **Algorithm Fixed**: Hardcoded to HS256, no dynamic algorithm selection
2. **Type Verification**: Payload includes `type` field checked on decode
3. **Expiration**: Always included and checked
4. **User ID Conversion**: Sub field converted to int after decode for type safety
5. **No Sensitive Data**: Only user ID stored, no passwords or PII

**Implementation:** `backend/app/core/security.py:23-56`

### SECRET_KEY Requirements

The SECRET_KEY is validated on startup:

```python
@field_validator("SECRET_KEY")
def validate_secret_key(cls, v: str, info) -> str:
    if not v:
        raise ValueError("SECRET_KEY must be set")
    
    # Production validation
    if env == "production" and len(v) < 32:
        raise ValueError("SECRET_KEY must be at least 32 characters in production")
    
    # Weak key detection
    weak_keys = ["your-secret-key", "change-this", "changeme", "secret", "default"]
    if any(weak in v.lower() for weak in weak_keys):
        if env == "production":
            raise ValueError("SECRET_KEY appears to be a default/weak value")
```

**Generate secure key:**
```bash
openssl rand -hex 32
```

**Verification:** `backend/app/core/config.py:36-65`

## CORS Configuration

### Strict CORS Policy

No wildcards allowed - all values explicitly configured:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,  # From ALLOWED_ORIGINS env
    allow_credentials=True,                       # Required for cookies
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],  # Explicit only
    allow_headers=["Content-Type", "Authorization"],  # Explicit only
    expose_headers=["Content-Type"],
    max_age=600,  # Cache preflight for 10 minutes
)
```

**Verification:** `backend/app/main.py:46-53`

### CORS Configuration Rules

- **Origins**: Comma-separated list in `ALLOWED_ORIGINS` env variable (e.g., `http://localhost:3000,https://example.com`)
- **No Wildcards**: `allow_origins=["*"]` is never used
- **Credentials Required**: `allow_credentials=True` enables cookie support
- **Methods**: Only HTTP methods actually used by API
- **Headers**: Only headers necessary for authentication and content type

### Development vs Production

**Development:**
```bash
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001
```

**Production:**
```bash
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

## Security Headers

### Security Headers Middleware

All responses include security headers:

```python
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Conditional HSTS (HTTPS only)
        if settings.COOKIE_SECURE:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response
```

**Verification:** `backend/app/main.py:12-26`

### Headers Explained

| Header | Value | Purpose |
|--------|-------|---------|
| `X-Content-Type-Options` | `nosniff` | Prevents MIME type sniffing |
| `X-Frame-Options` | `DENY` | Prevents clickjacking attacks |
| `X-XSS-Protection` | `1; mode=block` | Enables browser XSS filter |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Limits referrer information leakage |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` | Enforces HTTPS (production only) |

### HSTS (HTTP Strict Transport Security)

- **Enabled**: Only when `COOKIE_SECURE=true` (production with HTTPS)
- **Max Age**: 1 year (31536000 seconds)
- **Include Subdomains**: Yes
- **Preload**: Not included (can be added manually if needed)

## Production Requirements

### Critical Environment Variables

These MUST be properly configured for production:

```bash
# REQUIRED - Generate with: openssl rand -hex 32
SECRET_KEY=your-64-character-hex-string-from-openssl

# REQUIRED - Enable HTTPS-only cookies
COOKIE_SECURE=true

# REQUIRED - Production environment
ENV=production

# REQUIRED - Disable debug mode
DEBUG=false

# REQUIRED - Production database with strong credentials
DATABASE_URL=postgresql+asyncpg://secure_user:strong_password@db.example.com:5432/ani_production

# REQUIRED - Only your production domains
ALLOWED_ORIGINS=https://example.com,https://www.example.com
```

### Production Checklist

Before deploying to production:

#### Security
- [ ] SECRET_KEY is strong (64+ characters from `openssl rand -hex 32`)
- [ ] SECRET_KEY is unique and never committed to version control
- [ ] COOKIE_SECURE is set to `true`
- [ ] ENV is set to `production`
- [ ] DEBUG is set to `false`
- [ ] Database credentials are strong and unique
- [ ] ALLOWED_ORIGINS contains only production domains
- [ ] All default credentials changed

#### Infrastructure
- [ ] HTTPS/TLS is configured and working
- [ ] SSL certificates are valid and auto-renewing
- [ ] Rate limiting is enabled (nginx/cloudflare/etc)
- [ ] Firewall rules are configured
- [ ] Health checks are configured and monitored
- [ ] Logging is configured (application and access logs)
- [ ] Monitoring and alerting is set up
- [ ] Backup strategy is in place

#### Application
- [ ] All tests pass (`pytest -q`)
- [ ] Database migrations tested in staging
- [ ] API documentation is accessible to authorized users only
- [ ] Error messages don't leak sensitive information
- [ ] Dependency versions are up to date and secure

#### Testing
- [ ] Manual testing of all auth flows completed
- [ ] Security testing performed (penetration testing recommended)
- [ ] Load testing performed if expecting high traffic
- [ ] Disaster recovery tested

## Security Audit Verification

### Audit Completed: 2026-01-08

All security requirements verified and implemented:

#### Authentication
✅ Password hashing with bcrypt  
✅ Refresh token hash-only storage  
✅ Token rotation on refresh  
✅ No plaintext token storage  
✅ User account active flag  

#### Cookies
✅ HttpOnly flag prevents XSS  
✅ Secure flag for HTTPS (production)  
✅ SameSite=lax for CSRF protection  
✅ Consistent flags across endpoints  
✅ Centralized cookie name constant  
✅ Proper cookie deletion on logout  

#### JWT
✅ Algorithm fixed (HS256)  
✅ SECRET_KEY validation (required, min 32 chars)  
✅ Weak key detection  
✅ Token type verification  
✅ Expiration enforcement  
✅ No sensitive data in payload  

#### CORS
✅ No wildcard origins  
✅ Explicit methods only  
✅ Explicit headers only  
✅ Credentials enabled  
✅ Environment-based origins  

#### Headers
✅ X-Content-Type-Options: nosniff  
✅ X-Frame-Options: DENY  
✅ X-XSS-Protection enabled  
✅ Referrer-Policy configured  
✅ HSTS conditional on HTTPS  

#### Testing
✅ 10/10 tests passing  
✅ Test secret key clearly marked  
✅ Async test fixtures working  
✅ All auth flows covered  

### Security Audit Commits

- **dd67e7d**: Security audit - SECRET_KEY enforcement, cookie constants, CORS hardening, security headers
- **93f5cbe**: Code review fixes - conditional HSTS, clearer test secret

### Audit Files Modified

1. `backend/app/core/config.py` - SECRET_KEY validation, cookie constant
2. `backend/app/api/v1/auth.py` - Cookie constant usage
3. `backend/app/main.py` - CORS hardening, security headers, conditional HSTS
4. `backend/tests/conftest.py` - Test secret key clarification
5. `docker-compose.yml` - SECRET_KEY in environment
6. `README.md` - Documentation updates
7. `backend/.env.example` - Enhanced documentation
8. `backend/docs/setup.md` - Comprehensive setup guide

## Reporting Security Issues

If you discover a security vulnerability, please report it responsibly:

1. **DO NOT** open a public GitHub issue
2. Email security concerns to the maintainers (see repository for contact info)
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

We will respond within 48 hours and provide updates on the resolution.

## Additional Resources

- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [FastAPI Security Best Practices](https://fastapi.tiangolo.com/tutorial/security/)
- [JWT Best Current Practices](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-jwt-bcp)

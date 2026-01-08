# API Plan and MVP Scope

## MVP Implementation Status

This document describes the MVP (Minimum Viable Product) authentication API that has been implemented, along with planned features that are explicitly **NOT** included in this initial version.

## Implemented Endpoints (v1)

### Authentication Endpoints

#### POST `/api/v1/auth/register`

Register a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response:** `201 Created`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Cookies Set:**
- `refresh_token` (httpOnly, secure, 30 days)

**Errors:**
- `400 Bad Request` - Email already registered
- `422 Unprocessable Entity` - Invalid email format or password too short

---

#### POST `/api/v1/auth/login`

Login with email and password.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Cookies Set:**
- `refresh_token` (httpOnly, secure, 30 days)

**Errors:**
- `401 Unauthorized` - Incorrect email or password
- `403 Forbidden` - User account disabled

---

#### POST `/api/v1/auth/refresh`

Refresh access token using refresh token from cookie.

**Request:**
- Requires `refresh_token` cookie

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Cookies Set:**
- `refresh_token` (new token, httpOnly, secure, 30 days)

**Note:** Implements token rotation - old refresh token is revoked.

**Errors:**
- `401 Unauthorized` - Missing, invalid, or expired refresh token

---

#### POST `/api/v1/auth/logout`

Logout and revoke refresh token.

**Request:**
- Optional `refresh_token` cookie

**Response:** `200 OK`
```json
{
  "message": "Logged out successfully"
}
```

**Cookies Cleared:**
- `refresh_token`

---

### User Endpoints

#### GET `/api/v1/users/me`

Get current authenticated user information.

**Request Headers:**
```
Authorization: Bearer <access_token>
```

**Response:** `200 OK`
```json
{
  "id": 1,
  "email": "user@example.com",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z"
}
```

**Errors:**
- `401 Unauthorized` - Invalid or expired access token
- `403 Forbidden` - Missing authorization header

---

## Authentication Flow Examples

### Complete Registration Flow

```
1. POST /api/v1/auth/register
   → Returns: access_token + refresh_token cookie

2. GET /api/v1/users/me (with access_token)
   → Returns: user information
```

### Complete Login Flow

```
1. POST /api/v1/auth/login
   → Returns: access_token + refresh_token cookie

2. GET /api/v1/users/me (with access_token)
   → Returns: user information
```

### Token Refresh Flow

```
1. POST /api/v1/auth/refresh (with refresh_token cookie)
   → Returns: new access_token + new refresh_token cookie

2. Use new access_token for authenticated requests
```

### Logout Flow

```
1. POST /api/v1/auth/logout (with refresh_token cookie)
   → Revokes refresh token
   → Clears cookie

2. Future /api/v1/auth/refresh calls will fail
```

---

## NOT Implemented (By Design)

The following features were considered in planning but are explicitly **NOT** implemented in the MVP. This is intentional to keep the initial version simple and production-ready.

### Authentication Features NOT Included

#### ❌ OTP (One-Time Password)

**Why not:**
- Adds complexity (SMS/email delivery)
- Requires additional infrastructure
- Out of scope for MVP

**If needed later:**
- Add `otp_secret` field to User model
- Add `/auth/otp/enable` and `/auth/otp/verify` endpoints
- Integrate TOTP library (pyotp)

---

#### ❌ Social Login (OAuth)

**Why not:**
- Requires OAuth provider setup
- Adds complexity for MVP
- Can be added as extension

**If needed later:**
- Add OAuth client configuration
- Add `/auth/oauth/{provider}` endpoints
- Add social account linking table

---

#### ❌ Device/Session Management

**Why not:**
- Increases complexity
- Refresh token rotation provides basic security
- Not critical for MVP

**If needed later:**
- Add `sessions` table with device fingerprinting
- Add `/auth/sessions` endpoint to list active sessions
- Add ability to revoke specific sessions

---

#### ❌ Geographic/IP Tracking

**Why not:**
- Privacy concerns
- Adds database overhead
- Not essential for MVP

**If needed later:**
- Add IP address logging
- Add GeoIP lookup
- Add suspicious login detection

---

#### ❌ Email Verification

**Why not:**
- Requires email sending infrastructure
- Adds registration friction
- Out of scope for MVP

**If needed later:**
- Add `email_verified` field to User model
- Add verification token system
- Add email sending service integration

---

#### ❌ Password Reset

**Why not:**
- Requires email sending
- Adds complexity
- Can be added as enhancement

**If needed later:**
- Add password reset token system
- Add `/auth/forgot-password` endpoint
- Add `/auth/reset-password` endpoint

---

### API Features NOT Included

#### ❌ Field Include/Exclude

**Why not:**
- Premature optimization
- Current responses are already minimal
- Adds API complexity

**If needed later:**
- Add query parameters like `?fields=id,email`
- Implement field filtering in serialization

---

#### ❌ Pagination

**Why not:**
- No list endpoints in MVP (only `/users/me`)
- Will be needed when adding user listing

**If needed later:**
- Add pagination parameters (`?page=1&per_page=20`)
- Add pagination response wrapper

---

#### ❌ Search/Filtering

**Why not:**
- No collection endpoints yet
- Out of scope for auth MVP

**If needed later:**
- Add query parameters for filtering
- Add search functionality

---

#### ❌ Rate Limiting

**Why not:**
- Can be handled at infrastructure level (nginx, Cloudflare)
- Not critical for initial deployment
- Adds complexity

**If needed later:**
- Add Redis-based rate limiting
- Add per-endpoint rate limits
- Add rate limit headers

---

#### ❌ API Versioning in URL

**Status:** Partially implemented
- URLs include `/api/v1/` prefix
- No version negotiation or deprecated version support

**If needed later:**
- Add version header support
- Add deprecation warnings
- Maintain multiple API versions

---

### Business Features NOT Included

#### ❌ Ads Module

**Why not:**
- Backend is authentication-focused
- Ad serving is typically frontend concern
- Out of scope

**Includes (NOT implemented):**
- VAST video ads
- Banner ads
- Promotional content API
- Ad tracking endpoints

---

#### ❌ User Profiles

**Why not:**
- MVP only needs authentication
- Profile data can be added later
- Keeps user model minimal

**If needed later:**
- Add `profiles` table
- Add endpoints for profile CRUD
- Add avatar upload

---

#### ❌ User Preferences/Settings

**Why not:**
- Frontend can store preferences locally
- No server-side preferences needed for MVP
- Keeps backend simple

**If needed later:**
- Add `user_settings` table
- Add settings API endpoints

---

#### ❌ Content/Anime Data

**Why not:**
- Separate concern from authentication
- Existing Next.js `/rpc` endpoints handle this
- Out of scope for auth backend

**Note:** The existing oRPC anime data endpoints remain unchanged and functional.

---

## Future API Extensions

While not in MVP, these are potential extensions that could be added:

### Phase 2: Enhanced Security
- Rate limiting
- IP-based restrictions
- Suspicious activity detection
- Email verification
- Password reset

### Phase 3: User Management
- User profiles
- User preferences
- Avatar uploads
- Account deletion

### Phase 4: Advanced Auth
- OAuth providers (Google, GitHub, etc.)
- Two-factor authentication (TOTP)
- WebAuthn/Passkeys
- Session management

### Phase 5: Admin Features
- User administration
- Role-based access control (RBAC)
- Audit logs
- Analytics

---

## API Standards

The implemented API follows these standards:

### HTTP Status Codes

| Code | Usage |
|------|-------|
| `200 OK` | Successful request |
| `201 Created` | Resource created (registration) |
| `400 Bad Request` | Client error (duplicate email) |
| `401 Unauthorized` | Authentication failed |
| `403 Forbidden` | Authorization failed |
| `422 Unprocessable Entity` | Validation error |
| `500 Internal Server Error` | Server error |

### Response Format

All responses are JSON:

**Success:**
```json
{
  "field1": "value1",
  "field2": "value2"
}
```

**Error:**
```json
{
  "detail": "Error message"
}
```

### Authentication

- Access tokens use Bearer scheme: `Authorization: Bearer <token>`
- Refresh tokens use httpOnly cookies
- Cookies include CORS credentials

### CORS

- Configured via `ALLOWED_ORIGINS` environment variable
- Credentials allowed for configured origins
- All HTTP methods allowed

---

## Documentation

Additional documentation:

- **Architecture:** See `backend/docs/architecture.md`
- **Auth Flows:** See `backend/docs/auth.md`
- **OpenAPI:** Available at `http://localhost:8000/docs` when running

---

## Testing

Comprehensive test suite covers:

✅ Registration → Get user info  
✅ Login → Get user info  
✅ Refresh → Get user info  
✅ Logout → Refresh fails  
✅ Duplicate email registration  
✅ Invalid credentials  
✅ Missing/invalid tokens  

Run tests:
```bash
cd backend
pip install -r requirements-dev.txt
pytest
```

---

## Summary

**What's included:**
- ✅ User registration (email + password)
- ✅ User login
- ✅ JWT access tokens (30min TTL)
- ✅ Refresh tokens in httpOnly cookies (30 day TTL)
- ✅ Token rotation on refresh
- ✅ Logout with token revocation
- ✅ Get current user endpoint
- ✅ Password hashing (bcrypt)
- ✅ CORS support
- ✅ Comprehensive tests

**What's NOT included:**
- ❌ OTP/2FA
- ❌ Social login
- ❌ Email verification
- ❌ Password reset
- ❌ Device/session management
- ❌ Geographic tracking
- ❌ Field include/exclude
- ❌ Rate limiting (use infrastructure)
- ❌ Ads modules
- ❌ User profiles
- ❌ Anime/content data (use existing `/rpc`)

This MVP provides a solid, production-ready authentication foundation that can be extended as needed.

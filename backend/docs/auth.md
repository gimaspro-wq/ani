# Authentication System

## Overview

The authentication system uses a dual-token approach:
1. **Access Token** (JWT) - Short-lived, sent in response body
2. **Refresh Token** - Long-lived, stored in httpOnly cookie

## Authentication Flow

### Registration Flow

```
┌─────────┐                                          ┌─────────┐
│ Client  │                                          │ Backend │
└────┬────┘                                          └────┬────┘
     │                                                    │
     │ POST /api/v1/auth/register                        │
     │ { email, password }                               │
     ├──────────────────────────────────────────────────>│
     │                                                    │
     │                          Create user in DB        │
     │                          Hash password (bcrypt)   │
     │                          Generate access token    │
     │                          Generate refresh token   │
     │                          Store refresh token hash │
     │                                                    │
     │ 201 Created                                       │
     │ { access_token, token_type }                      │
     │ Set-Cookie: refresh_token=...; HttpOnly           │
     │<──────────────────────────────────────────────────┤
     │                                                    │
```

### Login Flow

```
┌─────────┐                                          ┌─────────┐
│ Client  │                                          │ Backend │
└────┬────┘                                          └────┬────┘
     │                                                    │
     │ POST /api/v1/auth/login                           │
     │ { email, password }                               │
     ├──────────────────────────────────────────────────>│
     │                                                    │
     │                          Verify credentials       │
     │                          Generate access token    │
     │                          Generate refresh token   │
     │                          Store refresh token hash │
     │                                                    │
     │ 200 OK                                            │
     │ { access_token, token_type }                      │
     │ Set-Cookie: refresh_token=...; HttpOnly           │
     │<──────────────────────────────────────────────────┤
     │                                                    │
```

### Authenticated Request Flow

```
┌─────────┐                                          ┌─────────┐
│ Client  │                                          │ Backend │
└────┬────┘                                          └────┬────┘
     │                                                    │
     │ GET /api/v1/users/me                              │
     │ Authorization: Bearer <access_token>              │
     ├──────────────────────────────────────────────────>│
     │                                                    │
     │                          Verify JWT signature     │
     │                          Check expiration         │
     │                          Extract user_id          │
     │                          Load user from DB        │
     │                                                    │
     │ 200 OK                                            │
     │ { id, email, is_active, created_at }              │
     │<──────────────────────────────────────────────────┤
     │                                                    │
```

### Refresh Token Flow (Token Rotation)

```
┌─────────┐                                          ┌─────────┐
│ Client  │                                          │ Backend │
└────┬────┘                                          └────┬────┘
     │                                                    │
     │ POST /api/v1/auth/refresh                         │
     │ Cookie: refresh_token=<old_token>                 │
     ├──────────────────────────────────────────────────>│
     │                                                    │
     │                          Verify refresh token     │
     │                          Check if not revoked     │
     │                          Check expiration         │
     │                          Revoke old token         │
     │                          Generate new tokens      │
     │                          Store new refresh hash   │
     │                                                    │
     │ 200 OK                                            │
     │ { access_token, token_type }                      │
     │ Set-Cookie: refresh_token=<new_token>; HttpOnly   │
     │<──────────────────────────────────────────────────┤
     │                                                    │
```

### Logout Flow

```
┌─────────┐                                          ┌─────────┐
│ Client  │                                          │ Backend │
└────┬────┘                                          └────┬────┘
     │                                                    │
     │ POST /api/v1/auth/logout                          │
     │ Cookie: refresh_token=<token>                     │
     ├──────────────────────────────────────────────────>│
     │                                                    │
     │                          Revoke refresh token     │
     │                          in database              │
     │                                                    │
     │ 200 OK                                            │
     │ { message: "Logged out successfully" }            │
     │ Set-Cookie: refresh_token=; Max-Age=0             │
     │<──────────────────────────────────────────────────┤
     │                                                    │
```

## Token Details

### Access Token (JWT)

**Format:** JSON Web Token (JWT)

**Contents:**
```json
{
  "sub": 123,              // User ID
  "exp": 1234567890,       // Expiration timestamp
  "type": "access"         // Token type
}
```

**Properties:**
- **TTL**: 30 minutes (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`)
- **Algorithm**: HS256 (HMAC with SHA-256)
- **Signed with**: `SECRET_KEY` from environment
- **Storage**: Client-side (localStorage, memory, or state management)
- **Transmission**: `Authorization: Bearer <token>` header

**Security:**
- Short-lived to limit exposure window
- Stateless (no database lookup needed)
- Cannot be revoked before expiration

### Refresh Token

**Format:** Random secure string (32 bytes, URL-safe base64)

**Properties:**
- **TTL**: 30 days (configurable via `REFRESH_TOKEN_EXPIRE_DAYS`)
- **Storage**: 
  - Client: httpOnly cookie (protected from JavaScript access)
  - Server: Hashed in database (not plain text)
- **Transmission**: Automatic via cookie (no manual handling)

**Security:**
- Stored hashed in database (like passwords)
- httpOnly cookie prevents XSS attacks
- SameSite=lax prevents CSRF in most cases
- Secure flag (HTTPS only) in production
- Can be revoked remotely
- Token rotation on each refresh

**Cookie Attributes:**
```
Set-Cookie: refresh_token=<token>; 
            HttpOnly; 
            Secure; 
            SameSite=Lax; 
            Max-Age=2592000;
            Path=/
```

## Token Rotation

When refreshing tokens:
1. Client sends old refresh token via cookie
2. Server validates token
3. Server **revokes** old refresh token in database
4. Server generates **new** access token
5. Server generates **new** refresh token
6. Server stores new refresh token hash
7. Server returns new access token + sets new refresh cookie

**Benefits:**
- Limits replay attack window
- Detects token theft (old token won't work twice)
- Allows forced re-authentication if suspicious activity detected

## Security Considerations

### Password Security

- Passwords hashed with bcrypt
- Salt automatically generated per password
- Configurable work factor (default: 12 rounds)
- Plain passwords never stored or logged

### Token Security

**Access Token:**
- ✅ Short TTL minimizes risk
- ✅ Stateless for performance
- ❌ Cannot be revoked before expiration
- ❌ Exposed to JavaScript (if stored in localStorage)

**Refresh Token:**
- ✅ httpOnly cookie prevents XSS
- ✅ Can be revoked in database
- ✅ Hashed storage prevents plaintext leaks
- ✅ Token rotation limits replay attacks
- ❌ Longer TTL increases risk window

### CORS Configuration

For cookie-based authentication to work:
- Frontend origin must be in `ALLOWED_ORIGINS`
- CORS middleware configured with `allow_credentials=True`
- Frontend requests must use `credentials: 'include'`

### HTTPS Requirement

In production:
- `Secure` cookie flag must be enabled
- All traffic over HTTPS
- Prevents man-in-the-middle attacks

## Token Expiration & Renewal Strategy

### Normal Flow

```
Time: 0min        Access Token Valid (30min TTL)
      │────────────────────────────────────────> requests work
Time: 28min       Access Token about to expire
      │           Frontend detects expiration coming
      │           Calls /auth/refresh proactively
      │────────────────────────────────────────> new access token
Time: 29min       New Access Token Valid
      │────────────────────────────────────────> requests work
```

### Refresh Token Expiration

```
Time: 0 days      Refresh Token Valid (30 days TTL)
      │────────────────────────────────────────> refreshes work
Time: 29 days     Refresh Token about to expire
      │           No automatic renewal
Time: 30 days     Refresh Token Expired
      │           User must log in again
```

## Client Implementation Notes

### Storing Tokens

**Access Token:**
- Can be stored in memory (most secure but lost on refresh)
- Can be stored in localStorage (persists but XSS vulnerable)
- Can be stored in secure state management (React context, etc.)

**Refresh Token:**
- Automatically handled by browser via cookie
- No manual storage needed
- No JavaScript access (httpOnly)

### Making Authenticated Requests

```typescript
// Example fetch with access token and credentials
fetch('http://localhost:8000/api/v1/users/me', {
  method: 'GET',
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json',
  },
  credentials: 'include',  // Important: includes cookies
})
```

### Handling Token Expiration

```typescript
// Pseudo-code for token refresh
async function makeAuthenticatedRequest(url, options) {
  let response = await fetch(url, {
    ...options,
    headers: {
      ...options.headers,
      'Authorization': `Bearer ${getAccessToken()}`,
    },
    credentials: 'include',
  });
  
  // If 401, try to refresh
  if (response.status === 401) {
    const refreshResponse = await fetch('/api/v1/auth/refresh', {
      method: 'POST',
      credentials: 'include',
    });
    
    if (refreshResponse.ok) {
      const { access_token } = await refreshResponse.json();
      setAccessToken(access_token);
      
      // Retry original request
      response = await fetch(url, {
        ...options,
        headers: {
          ...options.headers,
          'Authorization': `Bearer ${access_token}`,
        },
        credentials: 'include',
      });
    } else {
      // Refresh failed, redirect to login
      redirectToLogin();
    }
  }
  
  return response;
}
```

## API Endpoints Summary

| Endpoint | Method | Auth Required | Description |
|----------|--------|---------------|-------------|
| `/api/v1/auth/register` | POST | No | Register new user |
| `/api/v1/auth/login` | POST | No | Login with credentials |
| `/api/v1/auth/refresh` | POST | Refresh cookie | Get new access token |
| `/api/v1/auth/logout` | POST | No (optional) | Revoke refresh token |
| `/api/v1/users/me` | GET | Yes (Bearer) | Get current user info |

## Testing Authentication

See `backend/tests/test_auth.py` for comprehensive test suite covering:
- Registration flow
- Login flow
- Token refresh
- Logout and token revocation
- Invalid credentials handling
- Missing token handling

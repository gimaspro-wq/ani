# Reference from v1.json Example

This document serves as a reference for the original v1.json API plan that was considered during the design phase. The v1.json file itself is **not** committed to the repository as per project requirements.

## Background

During the planning phase, a comprehensive v1.json file was used as a reference to outline the full scope of possible API endpoints and features. However, for the MVP (Minimum Viable Product), only a core subset of authentication endpoints has been implemented.

## Implemented MVP Endpoints

The following endpoints from the original v1 plan have been **implemented** in the current MVP:

### Authentication Endpoints

- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Refresh access token (with token rotation)
- `POST /api/v1/auth/logout` - User logout
- `GET /api/v1/users/me` - Get current user information

## Explicitly Excluded from MVP

The following features were considered in the v1 plan but are **intentionally not implemented** in the MVP:

### Authentication Extensions (Not Implemented)
- OTP/2FA authentication
- Social login (OAuth providers: Google, GitHub, etc.)
- Email verification flows
- Password reset flows
- Device/session management
- Geographic/IP tracking
- Multi-device login tracking
- Suspicious activity detection

### API Features (Not Implemented)
- Field include/exclude in responses
- Pagination for list endpoints
- Advanced search/filtering
- Rate limiting (should be handled at infrastructure level)
- API versioning negotiation
- Webhook support

### Business Features (Not Implemented)
- Ads modules (VAST video ads, banner ads, promotional content)
- User profile management beyond email
- User preferences/settings API
- Avatar upload
- Content/anime data management (separate concern, handled by existing `/rpc` endpoints)

### Admin Features (Not Implemented)
- User administration
- Role-based access control (RBAC)
- Audit logs
- Analytics endpoints
- Content moderation

## Future Considerations

If the v1 plan is needed for future development phases, the key principles to follow are:

### Phase 2: Enhanced Security
- Implement rate limiting per endpoint
- Add IP-based restrictions
- Implement suspicious activity detection
- Add email verification workflow
- Add password reset workflow

### Phase 3: User Management
- Extend user profiles with additional fields
- Add user preferences API
- Implement avatar upload
- Add account deletion workflow

### Phase 4: Advanced Authentication
- Implement OAuth providers (Google, GitHub, etc.)
- Add Two-factor authentication (TOTP)
- Implement WebAuthn/Passkeys support
- Add comprehensive session management

### Phase 5: Admin & Analytics
- Add user administration panel API
- Implement RBAC system
- Add audit log tracking
- Implement analytics endpoints
- Add content moderation features

## Current MVP Scope

The current implementation focuses on:

1. **Core Authentication**: Register, login, logout with JWT tokens
2. **Token Management**: Access tokens (15 min TTL) + refresh tokens (30 day TTL)
3. **Security**: httpOnly cookies, bcrypt password hashing, token rotation
4. **Database**: PostgreSQL with async SQLAlchemy + asyncpg
5. **Migrations**: Alembic for database schema management
6. **Testing**: Comprehensive test suite (10 tests covering all auth flows)
7. **Documentation**: Complete API documentation in Markdown

## Why This Approach?

By implementing only the core MVP features and documenting the full v1 plan separately:

- ✅ Faster time to market
- ✅ Simpler codebase to maintain
- ✅ Easier to test and debug
- ✅ Clear path for future enhancements
- ✅ Avoid feature creep
- ✅ Focus on production-ready essentials

## API Design Principles

The implemented endpoints follow these principles from the original v1 plan:

1. **RESTful Design**: Standard HTTP methods and status codes
2. **JSON Responses**: All endpoints return JSON
3. **Token-Based Auth**: JWT for access, secure cookies for refresh
4. **CORS Support**: Configurable allowed origins
5. **Async Operations**: Fully async with asyncpg
6. **Type Safety**: Pydantic validation for all inputs/outputs
7. **Security First**: bcrypt hashing, token rotation, httpOnly cookies

## Migration Path

To implement additional features from the v1 plan:

1. Review this document and identify the feature
2. Design the database schema changes (if any)
3. Create Alembic migration
4. Implement service layer logic
5. Add API endpoints
6. Write tests
7. Update documentation

## See Also

- [Architecture](./architecture.md) - Backend structure and design decisions
- [Authentication](./auth.md) - Current auth implementation details
- [API Plan](./api-plan.md) - MVP scope and excluded features

# v1 API Plan Reference

This document provides context about the original v1.json planning file and explains why it's not included in the repository.

---

## Background

During the design phase, a comprehensive `v1.json` file was created to outline the complete API specification including all possible endpoints, request/response schemas, and future features. However, this file is **intentionally not committed** to the repository for the following reasons:

1. **Maintenance burden**: Large JSON files are hard to maintain and review
2. **Focus on MVP**: We want to avoid feature creep and focus on production-ready essentials
3. **Documentation clarity**: Markdown documentation is more readable and maintainable
4. **Flexibility**: Allows us to evolve the API design without being locked into a rigid schema

---

## What Replaced v1.json

Instead of a monolithic JSON file, we now have structured documentation:

### 1. API Plan (`api-plan.md`)
- **MVP Endpoints**: What's currently implemented
- **Planned Domains**: Future API structure organized by domain
- **Design Principles**: Pagination, authentication, versioning
- **Implementation Phases**: Roadmap for future development

### 2. Architecture (`architecture.md`)
- Backend structure and organization
- Technology stack decisions
- Database schema design
- Code organization principles

### 3. Authentication (`auth.md`)
- Current auth implementation details
- Token flows and lifecycle
- Security considerations
- Cookie and CORS configuration

---

## MVP vs Full v1 Plan

### Implemented in MVP ✅

The current implementation includes only the core authentication endpoints:

- `POST /api/v1/auth/register` - User registration with email/password
- `POST /api/v1/auth/login` - User authentication
- `POST /api/v1/auth/refresh` - Token refresh with rotation
- `POST /api/v1/auth/logout` - User logout and token revocation
- `GET /api/v1/users/me` - Get current user information
- `GET /` - Health check endpoint

### Planned for Future (from v1)

The v1 plan outlined 13 major API domains that are **not yet implemented**:

1. **System & Health** - Advanced health checks, version info, status monitoring
2. **User Management** - Profile updates, password changes, avatar uploads, settings
3. **Catalog & Titles** - Anime search, filtering, trending, seasonal lists
4. **Releases & Episodes** - Release management, episode listings, relationships
5. **Streaming** - Video sources, streams, subtitles
6. **Progress & History** - Watch history, progress tracking, completion status
7. **Collections & Lists** - User lists (watching, completed, plan-to-watch)
8. **Ratings & Reviews** - User ratings and reviews for titles
9. **Notifications** - User notification system for updates and events
10. **Social Features** - Following, followers, activity feeds
11. **Comments & Discussions** - Comments on titles and episodes
12. **Search** - Global search across all content types
13. **Admin** - Administrative endpoints for moderation and management

See `api-plan.md` for detailed endpoint outlines for each domain.

---

## Explicitly Excluded Features

The following features from the v1 plan are **NOT** being implemented:

### Security Features (Not Implemented)
- ❌ OTP/2FA authentication
- ❌ Social login (OAuth providers)
- ❌ Email verification
- ❌ Password reset flows
- ❌ Device/session management
- ❌ Geographic/IP tracking
- ❌ Suspicious activity detection

**Rationale**: These add significant complexity and infrastructure requirements. They can be added incrementally in future phases if needed.

### API Features (Not Implemented)
- ❌ Field include/exclude in responses
- ❌ Advanced search/filtering (in MVP)
- ❌ Webhook support
- ❌ API versioning negotiation
- ❌ GraphQL interface

**Rationale**: These are premature optimizations. The MVP uses simple, well-defined REST endpoints with full responses.

### Business Features (Not Implemented)
- ❌ Ads modules (VAST video ads, banner ads, promotional content)
- ❌ Extended user profiles
- ❌ Avatar uploads (in MVP)
- ❌ Content moderation tools

**Rationale**: 
- **Ads**: Out of scope - backend is authentication-focused
- **Profiles/Avatars**: Can be added in Phase 3 when needed
- **Moderation**: Admin features are Phase 5

### Admin Features (Not Implemented in MVP)
- ❌ User administration panel
- ❌ Role-based access control (RBAC)
- ❌ Audit logs
- ❌ Analytics endpoints
- ❌ Content moderation

**Rationale**: Admin features are Phase 5. MVP focuses on core user-facing functionality.

---

## Integration with Existing System

### What Stays Unchanged

The backend MVP coexists with the existing Next.js frontend without disrupting current functionality:

- ✅ **Frontend**: Next.js app in `frontend/` directory (moved from root)
- ✅ **Anime Data**: Existing `/rpc` endpoints (oRPC + aniwatch scraper)
- ✅ **Video Proxy**: Existing `/api/proxy` route
- ✅ **Player**: Existing video player implementation

### Future Migration Path

When implementing the full v1 plan:

1. **Phase 2** will add catalog endpoints that can gradually replace `/rpc` scraping
2. **Phase 5** will integrate video streaming with the existing `/api/proxy`
3. Frontend will be updated to consume new backend APIs incrementally

---

## Development Phases

### Phase 1: Authentication MVP (✅ Completed)
**Timeline**: Initial release  
**Scope**: Core authentication only
- User registration and login
- JWT access tokens (15 min TTL)
- Refresh tokens with rotation (30 day TTL)
- httpOnly cookies for refresh tokens
- Basic user endpoint (`/users/me`)

**Status**: ✅ Fully implemented and tested

### Phase 2: Core Content Features (Planned)
**Estimated Timeline**: 2-3 months after MVP  
**Scope**: Content browsing and tracking
- Catalog browsing and search
- Episode metadata
- User progress tracking
- Basic lists (watching, completed, plan-to-watch)

**Prerequisites**: 
- Content database design
- Migration from scraping to database
- Alembic migrations for new tables

### Phase 3: Social Features (Planned)
**Estimated Timeline**: 4-6 months after MVP  
**Scope**: Community features
- User ratings and reviews
- Extended user profiles
- Following/followers system
- Comments and discussions

**Prerequisites**:
- Phase 2 completion
- Moderation strategy
- Notification system design

### Phase 4: Advanced Features (Planned)
**Estimated Timeline**: 7-9 months after MVP  
**Scope**: Enhanced functionality
- Real-time notifications
- Recommendation engine
- Advanced search with filters
- Social activity feeds

**Prerequisites**:
- Phase 3 completion
- WebSocket infrastructure
- Caching strategy (Redis)

### Phase 5: Admin & Analytics (Planned)
**Estimated Timeline**: 10-12 months after MVP  
**Scope**: Administrative capabilities
- Admin panel API
- User management and moderation
- Content moderation tools
- Analytics and reporting
- RBAC implementation

**Prerequisites**:
- All previous phases
- Admin role system
- Audit logging infrastructure

---

## API Evolution Strategy

### Versioning

Current approach:
- API version in URL: `/api/v1/`
- All endpoints under `/api/v1/` prefix
- No version negotiation in MVP

Future approach (when v2 is needed):
- New endpoints at `/api/v2/`
- Maintain `/api/v1/` for backwards compatibility
- Add deprecation warnings to old versions
- Document migration path

### Breaking Changes

How to introduce breaking changes:
1. Create new endpoint version
2. Mark old endpoint as deprecated
3. Provide migration timeline (e.g., 6 months)
4. Support both versions during transition
5. Remove old version after grace period

### Non-Breaking Additions

These can be added to existing version:
- New optional query parameters
- New optional fields in request bodies
- New fields in responses (clients should ignore unknown fields)
- New endpoints

---

## Implementation Guidelines

When implementing features from the v1 plan:

### Step 1: Design
- Review domain outline in `api-plan.md`
- Define detailed endpoint specifications
- Design database schema changes
- Document request/response formats

### Step 2: Database
- Create Alembic migration for new tables
- Update SQLAlchemy models
- Add relationships and constraints

### Step 3: Backend Implementation
- Implement service layer logic
- Add API endpoint routers
- Add Pydantic schemas for validation
- Implement proper error handling

### Step 4: Testing
- Write unit tests for service layer
- Write integration tests for endpoints
- Test edge cases and error conditions
- Update test coverage targets

### Step 5: Documentation
- Update `api-plan.md` to mark as implemented
- Document new endpoints with examples
- Update OpenAPI schema
- Add to authentication/architecture docs if relevant

### Step 6: Frontend Integration
- Update frontend to consume new endpoints
- Add error handling
- Update UI components
- Test end-to-end flows

---

## Why Not Commit v1.json?

### Problems with Large JSON Specs

1. **Difficult to review**: Large JSON files are hard to review in pull requests
2. **Merge conflicts**: JSON files often have merge conflicts that are hard to resolve
3. **Not human-friendly**: JSON is not as readable as Markdown for documentation
4. **Premature detail**: Specifying all request/response schemas upfront leads to wasted effort
5. **Maintenance burden**: Keeping a large spec in sync with code is difficult
6. **Version control**: Binary-like JSON diffs are not easy to understand

### Benefits of Markdown Documentation

1. **Readable**: Easy to read and understand
2. **Reviewable**: Easy to review in pull requests
3. **Maintainable**: Easy to update as the API evolves
4. **Flexible**: Can add notes, rationale, and context
5. **Searchable**: Easy to search and reference
6. **Version controlled**: Text diffs are meaningful

### When to Use OpenAPI/Swagger

We use OpenAPI (Swagger) for:
- **Interactive documentation**: `/docs` endpoint with Swagger UI
- **Code generation**: If needed for client SDKs
- **API testing**: Via Swagger UI
- **Contract testing**: Between frontend and backend

OpenAPI spec is **auto-generated** from FastAPI code, not maintained manually.

---

## Summary

**What we have now:**
- ✅ Clean, maintainable Markdown documentation
- ✅ Clear MVP scope (authentication only)
- ✅ Structured plan for future expansion
- ✅ No JSON dumps or unused specifications
- ✅ Focus on implemented features

**What we don't have:**
- ❌ No v1.json file in repository
- ❌ No large JSON specifications
- ❌ No premature API design
- ❌ No feature creep

**Why this is better:**
- Easier to maintain and review
- Clear focus on MVP
- Flexibility to evolve
- Production-ready essentials only
- Comprehensive but readable documentation

---

## See Also

- [`api-plan.md`](./api-plan.md) - Complete API structure and planned domains
- [`architecture.md`](./architecture.md) - Backend architecture and design
- [`auth.md`](./auth.md) - Authentication implementation details

For interactive API documentation, run the backend and visit `http://localhost:8000/docs`.

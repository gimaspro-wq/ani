# API Plan: MVP and Future Expansion

This document outlines the implemented MVP authentication API and the planned structure for future expansion. It serves as a replacement for v1.json (which is not committed to the repository).

---

## MVP: Implemented Endpoints

### Authentication & Users (Implemented)

#### POST `/api/v1/auth/register`
Register a new user with email and password. Returns access token in JSON and sets refresh token in httpOnly cookie.

#### POST `/api/v1/auth/login`
Authenticate user with email and password. Returns access token in JSON and sets refresh token in httpOnly cookie.

#### POST `/api/v1/auth/refresh`
Exchange refresh token (from cookie) for a new access token. Implements token rotation - old refresh token is revoked.

#### POST `/api/v1/auth/logout`
Revoke refresh token and clear cookie. User must re-authenticate to get new tokens.

#### GET `/api/v1/users/me`
Get current authenticated user information. Requires Bearer access token.

#### GET `/` (root)
Health check endpoint returning API status and version.

---

## Planned: Future API Domains

### 1. System & Health

#### GET `/api/v1/health`
Detailed health check including database connectivity, cache status, etc.

#### GET `/api/v1/version`
API version information and build details.

#### GET `/api/v1/status`
System status and service availability.

---

### 2. Accounts & User Management

#### GET `/api/v1/users/{id}`
Get public user profile by ID (if public profiles are implemented).

#### PATCH `/api/v1/users/me`
Update current user profile (name, bio, avatar URL, etc.).

#### POST `/api/v1/users/me/change-password`
Change password for authenticated user. Requires current password verification.

#### DELETE `/api/v1/users/me`
Soft delete user account. May require password confirmation.

#### GET `/api/v1/users/me/settings`
Get user preferences and settings.

#### PATCH `/api/v1/users/me/settings`
Update user preferences (theme, language, notifications, etc.).

#### POST `/api/v1/users/me/avatar`
Upload user avatar image. Multipart form data.

---

### 3. Catalog & Titles

Anime/content catalog search and discovery.

#### GET `/api/v1/catalog/titles`
List and search anime titles. Query parameters:
- `q` - search query
- `genre` - filter by genre
- `year` - filter by year
- `status` - ongoing, completed, upcoming
- `type` - TV, movie, OVA, special
- `page`, `per_page` - pagination

#### GET `/api/v1/catalog/titles/{id}`
Get detailed information about a specific title including synopsis, ratings, staff, etc.

#### GET `/api/v1/catalog/genres`
Get list of all available genres with counts.

#### GET `/api/v1/catalog/tags`
Get list of all content tags/themes.

#### GET `/api/v1/catalog/studios`
Get list of animation studios.

#### GET `/api/v1/catalog/trending`
Get currently trending titles.

#### GET `/api/v1/catalog/popular`
Get popular titles (by views, ratings, etc.).

#### GET `/api/v1/catalog/seasonal`
Get titles for current anime season.

---

### 4. Releases & Episodes

#### GET `/api/v1/releases`
List anime releases with filtering and sorting.

#### GET `/api/v1/releases/{id}`
Get detailed release information including episode count, air dates, etc.

#### GET `/api/v1/releases/{id}/episodes`
List all episodes for a release. Supports pagination.

#### GET `/api/v1/releases/{id}/related`
Get related titles (sequels, prequels, spin-offs, same franchise).

#### GET `/api/v1/releases/{id}/recommendations`
Get recommended similar titles based on this release.

---

### 5. Episodes & Streaming

#### GET `/api/v1/episodes/{id}`
Get episode metadata including title, synopsis, air date, duration.

#### GET `/api/v1/episodes/{id}/streams`
Get available video streams with different qualities and translations.

#### GET `/api/v1/episodes/{id}/sources`
Get video source URLs (may require authentication for some sources).

#### GET `/api/v1/episodes/{id}/subtitles`
Get available subtitle tracks for episode.

---

### 6. User Progress & History

Track user viewing progress and history.

#### GET `/api/v1/progress/watching`
Get list of titles user is currently watching.

#### GET `/api/v1/progress/completed`
Get list of completed titles.

#### GET `/api/v1/progress/{title_id}`
Get user's progress for specific title (episodes watched, last position, etc.).

#### POST `/api/v1/progress/{title_id}/episodes/{episode_id}`
Update viewing progress for an episode. Records timestamp, completion status.

#### DELETE `/api/v1/progress/{title_id}`
Remove title from user's progress/history.

#### GET `/api/v1/history`
Get user's viewing history with timestamps.

---

### 7. Collections & Lists

User-created lists and collections.

#### GET `/api/v1/lists`
Get all lists for authenticated user (watching, plan-to-watch, completed, dropped, etc.).

#### POST `/api/v1/lists`
Create a new custom list.

#### GET `/api/v1/lists/{id}`
Get specific list with all titles.

#### PATCH `/api/v1/lists/{id}`
Update list metadata (name, description, privacy).

#### DELETE `/api/v1/lists/{id}`
Delete a list.

#### POST `/api/v1/lists/{id}/titles/{title_id}`
Add title to list.

#### DELETE `/api/v1/lists/{id}/titles/{title_id}`
Remove title from list.

---

### 8. Ratings & Reviews

#### GET `/api/v1/titles/{id}/ratings`
Get rating statistics for a title.

#### POST `/api/v1/titles/{id}/ratings`
Submit user rating for a title (1-10 scale).

#### GET `/api/v1/titles/{id}/reviews`
Get user reviews for a title with pagination.

#### POST `/api/v1/titles/{id}/reviews`
Submit a review for a title.

#### GET `/api/v1/reviews/{id}`
Get specific review.

#### PATCH `/api/v1/reviews/{id}`
Update user's own review.

#### DELETE `/api/v1/reviews/{id}`
Delete user's own review.

#### POST `/api/v1/reviews/{id}/helpful`
Mark review as helpful.

---

### 9. Notifications

User notifications system.

#### GET `/api/v1/notifications`
Get user notifications (new episodes, replies, system messages).

#### GET `/api/v1/notifications/unread`
Get count of unread notifications.

#### PATCH `/api/v1/notifications/{id}/read`
Mark notification as read.

#### PATCH `/api/v1/notifications/read-all`
Mark all notifications as read.

#### DELETE `/api/v1/notifications/{id}`
Delete notification.

---

### 10. Social Features

#### GET `/api/v1/users/{id}/following`
Get list of users this user follows.

#### GET `/api/v1/users/{id}/followers`
Get list of users following this user.

#### POST `/api/v1/users/{id}/follow`
Follow a user.

#### DELETE `/api/v1/users/{id}/follow`
Unfollow a user.

#### GET `/api/v1/feed`
Get activity feed from followed users.

---

### 11. Comments & Discussions

#### GET `/api/v1/titles/{id}/comments`
Get comments for a title.

#### POST `/api/v1/titles/{id}/comments`
Post a comment on a title.

#### GET `/api/v1/episodes/{id}/comments`
Get comments for an episode.

#### POST `/api/v1/episodes/{id}/comments`
Post a comment on an episode.

#### PATCH `/api/v1/comments/{id}`
Edit own comment.

#### DELETE `/api/v1/comments/{id}`
Delete own comment.

#### POST `/api/v1/comments/{id}/replies`
Reply to a comment.

---

### 12. Search

Unified search across all content types.

#### GET `/api/v1/search`
Global search. Query parameters:
- `q` - search query
- `type` - titles, users, reviews, comments
- `page`, `per_page` - pagination

#### GET `/api/v1/search/suggestions`
Get search suggestions/autocomplete.

---

### 13. Admin (Future)

Administrative endpoints for content and user management.

#### GET `/api/v1/admin/users`
List all users with filtering and sorting.

#### PATCH `/api/v1/admin/users/{id}`
Update user (ban, verify, change role).

#### GET `/api/v1/admin/reports`
Get content reports (spam, inappropriate content).

#### PATCH `/api/v1/admin/reports/{id}`
Resolve or dismiss a report.

#### GET `/api/v1/admin/analytics`
Get system analytics and statistics.

#### GET `/api/v1/admin/audit-logs`
Get audit log of admin actions.

---

## API Design Principles

### Request/Response Format
- All endpoints accept and return JSON
- Use standard HTTP methods (GET, POST, PATCH, DELETE)
- Use standard HTTP status codes (200, 201, 400, 401, 404, 500)

### Authentication
- Public endpoints: no authentication required
- Protected endpoints: require Bearer access token
- Admin endpoints: require admin role

### Pagination
Standard pagination for list endpoints:
```
?page=1&per_page=20
```

Response includes pagination metadata:
```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 100,
    "total_pages": 5
  }
}
```

### Filtering & Sorting
Query parameters for filtering:
```
?genre=action&year=2024&status=ongoing
```

Sorting:
```
?sort_by=rating&sort_order=desc
```

### Rate Limiting
- Implemented at infrastructure level (nginx/Cloudflare)
- Per-user limits for authenticated endpoints
- Stricter limits for unauthenticated requests

### Versioning
- API version in URL: `/api/v1/`
- Version in response headers
- Deprecation warnings for old versions

---

## Implementation Phases

### Phase 1: MVP (Completed) ✅
- User authentication (register, login, logout)
- Token management (access + refresh)
- Get current user info

### Phase 2: Core Features (Planned)
- Catalog browsing and search
- Episode streaming
- User progress tracking
- Basic lists (watching, completed)

### Phase 3: Social Features (Planned)
- Ratings and reviews
- User profiles
- Following/followers
- Comments and discussions

### Phase 4: Advanced Features (Planned)
- Notifications
- Recommendations engine
- Advanced search
- Social feed

### Phase 5: Admin & Analytics (Planned)
- Admin panel API
- User management
- Content moderation
- Analytics and reporting

---

## Notes

### Current Integration
- **Frontend**: Next.js app in `frontend/` directory
- **Anime Data**: Existing `/rpc` (oRPC + aniwatch scraper) - NOT changed
- **Video Proxy**: Existing `/api/proxy` - NOT changed
- **Player**: Existing player - NOT changed

### Future Integration Points
- Backend catalog API will eventually replace `/rpc` scraping
- Video streaming will integrate with `/api/proxy`
- Player will consume backend APIs for metadata

### Excluded Features
The following are **NOT** planned for implementation:
- ❌ Ads modules (VAST, banners, promotions)
- ❌ OTP/2FA authentication (out of scope for MVP)
- ❌ Social login (OAuth) - may add later
- ❌ Email verification - may add later
- ❌ Password reset - may add later
- ❌ Device/session management - may add later
- ❌ Geographic/IP tracking
- ❌ Field include/exclude in responses

---

## Documentation

For more details, see:
- [Architecture](./architecture.md) - Backend structure
- [Authentication](./auth.md) - Auth implementation details  
- [v1 Reference](./reference-from-v1-example.md) - Original v1 plan context

Interactive API documentation available at `http://localhost:8000/docs` when running the backend.

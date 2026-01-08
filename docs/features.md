# Features Documentation

This document describes the new features implemented in Anirohi.

## Overview

Anirohi now includes server-synced library management, watch progress tracking, and watch history - bringing the app closer to feature parity with services like aniliberty.top and Anixtar.

## Features

### 1. User Library

Manage your anime collection with server-synced library items.

**Statuses:**
- **Watching**: Currently watching this anime
- **Planned**: Planning to watch this anime
- **Completed**: Finished watching this anime
- **Dropped**: Stopped watching this anime

**Favorites:**
- Mark anime as favorites for quick access
- Filter library by favorites only

**API Endpoints:**
- `GET /api/v1/me/library` - Get user's library items (supports filtering by status and favorites)
- `PUT /api/v1/me/library/{title_id}` - Add or update a library item
- `DELETE /api/v1/me/library/{title_id}` - Remove a library item

**Usage Example:**
```bash
# Get all library items
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/api/v1/me/library

# Add anime to library as watching
curl -X PUT -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "watching", "is_favorite": true}' \
  http://localhost:8000/api/v1/me/library/anime-123

# Filter by status
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/me/library?status=watching

# Get only favorites
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/me/library?favorites=true
```

### 2. Watch Progress

Track your episode watch progress across devices.

**Features:**
- Automatic progress sync when logged in
- Falls back to local storage when logged out
- Resume watching from where you left off
- Progress indicators on episode lists

**API Endpoints:**
- `GET /api/v1/me/progress` - Get user's watch progress (optionally filter by title_id)
- `PUT /api/v1/me/progress/{episode_id}` - Update episode watch progress

**Usage Example:**
```bash
# Get all progress
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/api/v1/me/progress

# Get progress for specific title
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/me/progress?title_id=anime-123

# Update progress
curl -X PUT -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title_id": "anime-123", "position_seconds": 120.5, "duration_seconds": 1440.0}' \
  http://localhost:8000/api/v1/me/progress/episode-1
```

### 3. Watch History

View your complete watch history.

**Features:**
- Automatic history tracking
- Sort by most recent watches
- Configurable limit

**API Endpoints:**
- `GET /api/v1/me/history` - Get user's watch history (default limit: 50, max: 100)

**Usage Example:**
```bash
# Get recent history
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/api/v1/me/history

# Get last 20 items
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/me/history?limit=20
```

### 4. Multi-Provider Support

All features support multiple data providers for future expansion.

**Providers:**
- `rpc` (default): Current aniwatch-based data source
- Future providers: aniliberty, anixtar, etc.

**Usage:**
All endpoints accept an optional `provider` query parameter (defaults to `rpc`):

```bash
# Use default rpc provider
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/me/library?provider=rpc

# Future: Use alternative provider
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/me/library?provider=aniliberty
```

## Frontend Integration

### Authentication

The frontend uses localStorage to store the JWT access token and httpOnly cookies for refresh tokens.

**Login Flow:**
1. User logs in via `/api/v1/auth/login`
2. Access token stored in localStorage
3. Refresh token stored in httpOnly cookie
4. Access token included in `Authorization` header for authenticated requests

### Local Storage Fallback

When users are not logged in, data is stored locally:

- **Watch Progress**: Stored in localStorage using `use-watch-progress` hook
- **Saved Series**: Stored in localStorage using `use-saved-series` hook

### Login Merge Strategy

When a user logs in with existing local data:

1. Local progress/library items are read
2. Merged with server data (server wins on conflict by `updated_at`)
3. User sees combined data immediately
4. Background sync pushes local changes to server

### Frontend Hooks

**Library Management:**
```typescript
import { useLibrary, useIsInLibrary } from '@/hooks/use-library';

// Get all library items
const { items, isLoading, updateItem, deleteItem } = useLibrary();

// Check if a title is in library
const { isInLibrary, status, isFavorite } = useIsInLibrary('anime-123');

// Add to library
updateItem({ titleId: 'anime-123', status: 'watching', isFavorite: true });
```

**Progress Tracking:**
```typescript
import { useServerProgress } from '@/hooks/use-server-progress';

// Get progress with automatic local fallback
const { saveProgress, getProgress, isSyncing } = useServerProgress();

// Save progress (syncs to server if authenticated, otherwise local only)
saveProgress('anime-123', 1, 120.5, 1440.0, {
  poster: '/image.jpg',
  name: 'Anime Title'
});

// Get progress
const progress = getProgress('anime-123', 1);
```

**History:**
```typescript
import { useHistory } from '@/hooks/use-server-progress';

const { items, isLoading } = useHistory({ limit: 50 });
```

## Database Schema

### user_library_items

Stores user library items with status and favorites.

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| user_id | Integer | Foreign key to users |
| provider | String | Data provider (default: 'rpc') |
| title_id | String | Title identifier |
| status | Enum | Library status (watching/planned/completed/dropped) |
| is_favorite | Boolean | Favorite flag |
| created_at | DateTime | Creation timestamp |
| updated_at | DateTime | Last update timestamp |

**Indexes:**
- `user_id`, `provider`, `title_id` (composite unique)
- `updated_at` (for sorting)

### user_progress

Stores episode watch progress.

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| user_id | Integer | Foreign key to users |
| provider | String | Data provider (default: 'rpc') |
| title_id | String | Title identifier |
| episode_id | String | Episode identifier |
| position_seconds | Float | Current playback position |
| duration_seconds | Float | Total episode duration |
| updated_at | DateTime | Last update timestamp |

**Indexes:**
- `user_id`, `provider`, `episode_id` (composite unique)
- `updated_at` (for sorting)

### user_history

Stores watch history.

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| user_id | Integer | Foreign key to users |
| provider | String | Data provider (default: 'rpc') |
| title_id | String | Title identifier |
| episode_id | String | Episode identifier |
| position_seconds | Float | Position when added to history (nullable) |
| watched_at | DateTime | Watch timestamp |

**Indexes:**
- `user_id`, `provider` (composite)
- `watched_at` (for sorting)

## Running Migrations

After pulling this PR, run the database migrations:

```bash
cd backend

# If using Docker:
docker compose exec backend alembic upgrade head

# If running locally:
source venv/bin/activate
alembic upgrade head
```

## Environment Variables

No new environment variables are required. The existing configuration works for these features.

### Optional Backend Configuration

If you want to customize the backend URL for the frontend:

```bash
# frontend/.env.local
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

## Performance Considerations

### Caching Strategy

TanStack Query is configured with:
- **Library**: 5 minute stale time, 30 minute garbage collection
- **Progress**: 2 minute stale time, 10 minute garbage collection  
- **History**: 5 minute stale time, 30 minute garbage collection

### Database Indexes

All tables have appropriate indexes for:
- Foreign keys (`user_id`)
- Filter fields (`provider`, `title_id`, `episode_id`)
- Sort fields (`updated_at`, `watched_at`)
- Unique constraints to prevent duplicates

### Resource Usage

Designed for 4 vCPU / 8GB RAM minimum:
- No heavy background processing
- Simple CRUD operations
- Indexed queries for fast lookups
- Client-side caching reduces server load

## Future Enhancements

Features planned for future releases:

1. **Client-Side Search Index**: MiniSearch/FlexSearch with IndexedDB persistence
2. **Advanced Search Page**: Filters for genres, year, season, status, type, studio, rating
3. **Enhanced Command Palette**: Better keyboard navigation, quick actions
4. **Rich Title Pages**: Seasons grouping, similar titles, trailers
5. **Continue Watching**: Server-synced "continue watching" section

## Testing

Run backend tests:

```bash
cd backend
source venv/bin/activate
pytest -v
```

The test suite includes comprehensive tests for:
- Library CRUD operations
- Progress tracking
- History tracking
- Multi-provider support
- Authentication requirements
- Data isolation

## Security

- All endpoints require authentication (JWT Bearer token)
- Data is isolated by user_id
- SQL injection prevention via SQLAlchemy ORM
- Input validation via Pydantic schemas
- No sensitive data exposure in responses

## Troubleshooting

### "401 Unauthorized" errors

Make sure you're including the access token in requests:

```bash
curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  http://localhost:8000/api/v1/me/library
```

### Progress not syncing

1. Check that you're logged in
2. Verify backend URL is correct
3. Check browser console for errors
4. Ensure backend is running

### Library items not showing

1. Verify authentication token is valid
2. Check provider parameter matches
3. Try refreshing the token
4. Check API response in network tab

## License

This project is open source and available under the MIT License.

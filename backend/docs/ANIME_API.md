# Anime Backend API Documentation

This document provides complete API documentation for the anime backend implementation, including example requests and responses for both internal and public APIs.

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Internal API](#internal-api)
4. [Public API](#public-api)
5. [Database Schema](#database-schema)
6. [Environment Variables](#environment-variables)
7. [Deployment](#deployment)

## Overview

The anime backend provides two distinct APIs:

- **Internal API** (`/api/v1/internal/*`): For parser/scraper access only, protected by internal token
- **Public API** (`/api/v1/anime*`): For frontend/client access, no authentication required

### Key Features

- **Upsert logic**: Repeated imports update existing data without creating duplicates
- **Active status preservation**: Manual deactivation (is_active=false) is not overridden by imports
- **Multi-source support**: Supports multiple data sources with unique source_name + source_id combinations
- **Video source prioritization**: Multiple video sources per episode, sorted by priority
- **Slug generation**: Automatic URL-friendly slug generation from titles

## Authentication

### Internal API Token

All internal API endpoints require authentication via the `X-Internal-Token` header.

**Header:**
```
X-Internal-Token: your-internal-token-here
```

**Configuration:**
Set the `INTERNAL_TOKEN` environment variable (minimum 32 characters in production).

```bash
# Generate a secure token
openssl rand -hex 32

# Set in .env
INTERNAL_TOKEN=your-generated-token-here
```

## Internal API

### POST /api/v1/internal/import/anime

Import or update anime metadata.

**Authentication:** Required (X-Internal-Token header)

**Request Body:**
```json
{
  "source_name": "example_source",
  "source_id": "12345",
  "title": "Naruto",
  "alternative_titles": ["ナルト", "Naruto Shippuden"],
  "description": "A young ninja's quest to become the strongest ninja and leader of his village.",
  "year": 2002,
  "status": "completed",
  "poster": "https://example.com/posters/naruto.jpg",
  "genres": ["Action", "Adventure", "Fantasy"]
}
```

**Required Fields:**
- `source_name` (string): Identifier for the data source
- `source_id` (string): Unique ID within the source
- `title` (string): Anime title

**Optional Fields:**
- `alternative_titles` (array of strings): Alternative titles
- `description` (string): Anime description
- `year` (integer): Release year (1900-2100)
- `status` (string): One of "ongoing", "completed", "upcoming"
- `poster` (string): Poster image URL
- `genres` (array of strings): List of genres

**Success Response (200 OK):**
```json
{
  "success": true,
  "message": "Anime imported successfully: Naruto"
}
```

**Error Responses:**

403 Forbidden (Invalid token):
```json
{
  "detail": "Invalid internal token"
}
```

422 Unprocessable Entity (Validation error):
```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "source_id"],
      "msg": "Field required"
    }
  ]
}
```

**Behavior:**
- Creates new anime if (source_name, source_id) combination doesn't exist
- Updates existing anime if it already exists
- Does NOT modify `is_active` if it was manually set to false
- Automatically generates URL-friendly slug from title
- Handles slug conflicts by appending numbers (e.g., "naruto-1", "naruto-2")

**Example with cURL:**
```bash
curl -X POST http://localhost:8000/api/v1/internal/import/anime \
  -H "Content-Type: application/json" \
  -H "X-Internal-Token: your-token-here" \
  -d '{
    "source_name": "example",
    "source_id": "12345",
    "title": "Naruto",
    "description": "A young ninja...",
    "year": 2002,
    "status": "completed",
    "genres": ["Action", "Adventure"]
  }'
```

### POST /api/v1/internal/import/episodes

Import or update episodes for an anime.

**Authentication:** Required (X-Internal-Token header)

**Request Body:**
```json
{
  "source_name": "example_source",
  "anime_source_id": "12345",
  "episodes": [
    {
      "source_episode_id": "ep_001",
      "number": 1,
      "title": "Enter: Naruto Uzumaki!",
      "is_available": true
    },
    {
      "source_episode_id": "ep_002",
      "number": 2,
      "title": "My Name is Konohamaru!",
      "is_available": true
    }
  ]
}
```

**Required Fields:**
- `source_name` (string): Must match an existing anime's source_name
- `anime_source_id` (string): Must match an existing anime's source_id
- `episodes` (array): List of episodes
  - `source_episode_id` (string): Unique ID for the episode
  - `number` (integer): Episode number (≥0)
  - `is_available` (boolean): Whether episode is available

**Optional Fields:**
- `episodes[].title` (string): Episode title

**Success Response (200 OK):**
```json
{
  "success": true,
  "total": 2,
  "imported": 2,
  "errors": []
}
```

**Partial Success (200 OK with errors):**
```json
{
  "success": false,
  "total": 3,
  "imported": 2,
  "errors": [
    "Episode 3 (ID: ep_003): validation error"
  ]
}
```

**Error Responses:**

404 Not Found (Anime not found):
```json
{
  "detail": "Anime not found: example_source/12345"
}
```

**Behavior:**
- Finds anime by (source_name, anime_source_id)
- Creates or updates episodes by source_episode_id
- Does NOT delete episodes that are not in the import
- Continues processing other episodes if one fails (resilient import)
- Returns detailed error report for failed episodes

**Example with cURL:**
```bash
curl -X POST http://localhost:8000/api/v1/internal/import/episodes \
  -H "Content-Type: application/json" \
  -H "X-Internal-Token: your-token-here" \
  -d '{
    "source_name": "example",
    "anime_source_id": "12345",
    "episodes": [
      {
        "source_episode_id": "ep_001",
        "number": 1,
        "title": "Episode 1",
        "is_available": true
      }
    ]
  }'
```

### POST /api/v1/internal/import/video

Import video source for an episode.

**Authentication:** Required (X-Internal-Token header)

**Request Body:**
```json
{
  "source_name": "example_source",
  "source_episode_id": "ep_001",
  "player": {
    "type": "iframe",
    "url": "https://player.example.com/embed/abc123",
    "source_name": "example_player",
    "priority": 10
  }
}
```

**Required Fields:**
- `source_name` (string): Must match the anime's source_name
- `source_episode_id` (string): Must match an existing episode's source_episode_id
- `player` (object):
  - `type` (string): Player type (e.g., "iframe", "direct", "hls")
  - `url` (string): Player/video URL
  - `source_name` (string): Name of the video source/player
  - `priority` (integer): Priority level (higher = preferred, default: 0)

**Success Response (200 OK):**
```json
{
  "success": true,
  "message": "Video source imported successfully"
}
```

**Error Responses:**

404 Not Found (Episode not found):
```json
{
  "detail": "Episode not found: example_source/ep_001"
}
```

**Behavior:**
- Finds episode by (source_name, source_episode_id)
- Updates existing video source if same URL and source_name exists
- Otherwise creates new video source
- Allows multiple video sources per episode
- Does NOT delete old video sources

**Example with cURL:**
```bash
curl -X POST http://localhost:8000/api/v1/internal/import/video \
  -H "Content-Type: application/json" \
  -H "X-Internal-Token: your-token-here" \
  -d '{
    "source_name": "example",
    "source_episode_id": "ep_001",
    "player": {
      "type": "iframe",
      "url": "https://player.example.com/embed/abc",
      "source_name": "player1",
      "priority": 10
    }
  }'
```

## Public API

### GET /api/v1/anime

List active anime with optional filtering and pagination.

**Authentication:** None required

**Query Parameters:**
- `skip` (integer, default: 0): Number of items to skip (pagination)
- `limit` (integer, default: 50, max: 100): Number of items to return
- `year` (integer, optional): Filter by release year
- `status` (string, optional): Filter by status ("ongoing", "completed", "upcoming")
- `genre` (string, optional): Filter by genre (case-insensitive)

**Success Response (200 OK):**
```json
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "title": "Naruto",
    "slug": "naruto",
    "description": "A young ninja's quest...",
    "year": 2002,
    "status": "completed",
    "poster": "https://example.com/posters/naruto.jpg",
    "genres": ["Action", "Adventure", "Fantasy"],
    "created_at": "2024-01-08T12:00:00Z"
  },
  {
    "id": "223e4567-e89b-12d3-a456-426614174001",
    "title": "One Piece",
    "slug": "one-piece",
    "description": "A pirate's adventure...",
    "year": 1999,
    "status": "ongoing",
    "poster": "https://example.com/posters/one-piece.jpg",
    "genres": ["Action", "Adventure", "Comedy"],
    "created_at": "2024-01-08T13:00:00Z"
  }
]
```

**Behavior:**
- Returns only anime with `is_active=true`
- Does NOT include internal fields (source_name, source_id)
- Ordered by title
- Supports pagination via skip/limit

**Examples:**

List first 10 anime:
```bash
curl http://localhost:8000/api/v1/anime?limit=10
```

Get anime from 2023:
```bash
curl http://localhost:8000/api/v1/anime?year=2023
```

Get ongoing anime:
```bash
curl http://localhost:8000/api/v1/anime?status=ongoing
```

Get action anime:
```bash
curl http://localhost:8000/api/v1/anime?genre=Action
```

Pagination (page 2, 20 items per page):
```bash
curl http://localhost:8000/api/v1/anime?skip=20&limit=20
```

### GET /api/v1/anime/{slug}

Get detailed information about a specific anime.

**Authentication:** None required

**Path Parameters:**
- `slug` (string): URL-friendly slug of the anime

**Success Response (200 OK):**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "title": "Naruto",
  "slug": "naruto",
  "description": "Naruto Uzumaki, a mischievous adolescent ninja...",
  "year": 2002,
  "status": "completed",
  "poster": "https://example.com/posters/naruto.jpg",
  "genres": ["Action", "Adventure", "Fantasy"],
  "alternative_titles": ["ナルト", "Naruto Shippuden"],
  "created_at": "2024-01-08T12:00:00Z",
  "updated_at": "2024-01-08T14:30:00Z"
}
```

**Error Response:**

404 Not Found:
```json
{
  "detail": "Anime not found: invalid-slug"
}
```

**Behavior:**
- Returns only if `is_active=true`
- Does NOT include internal fields (source_name, source_id)

**Example:**
```bash
curl http://localhost:8000/api/v1/anime/naruto
```

### GET /api/v1/anime/{slug}/episodes

Get all episodes for an anime with video sources.

**Authentication:** None required

**Path Parameters:**
- `slug` (string): URL-friendly slug of the anime

**Success Response (200 OK):**
```json
[
  {
    "id": "323e4567-e89b-12d3-a456-426614174002",
    "number": 1,
    "title": "Enter: Naruto Uzumaki!",
    "video_sources": [
      {
        "id": "423e4567-e89b-12d3-a456-426614174003",
        "type": "iframe",
        "url": "https://player1.example.com/embed/abc",
        "source_name": "player1",
        "priority": 10
      },
      {
        "id": "523e4567-e89b-12d3-a456-426614174004",
        "type": "iframe",
        "url": "https://player2.example.com/embed/xyz",
        "source_name": "player2",
        "priority": 5
      }
    ]
  },
  {
    "id": "623e4567-e89b-12d3-a456-426614174005",
    "number": 2,
    "title": "My Name is Konohamaru!",
    "video_sources": [
      {
        "id": "723e4567-e89b-12d3-a456-426614174006",
        "type": "iframe",
        "url": "https://player1.example.com/embed/def",
        "source_name": "player1",
        "priority": 10
      }
    ]
  }
]
```

**Error Response:**

404 Not Found (Anime not found):
```json
{
  "detail": "Anime not found: invalid-slug"
}
```

**Behavior:**
- Returns only episodes with `is_active=true`
- Returns only video sources with `is_active=true`
- Video sources are sorted by priority (descending - higher priority first)
- Episodes are ordered by number
- Does NOT include internal fields (source_episode_id)

**Example:**
```bash
curl http://localhost:8000/api/v1/anime/naruto/episodes
```

## Database Schema

### Anime Table

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique identifier |
| title | VARCHAR | NOT NULL, INDEXED | Anime title |
| slug | VARCHAR | NOT NULL, UNIQUE, INDEXED | URL-friendly slug |
| description | TEXT | NULLABLE | Anime description |
| year | INTEGER | NULLABLE, INDEXED | Release year |
| status | ENUM | NULLABLE, INDEXED | "ongoing", "completed", or "upcoming" |
| poster | VARCHAR | NULLABLE | Poster image URL |
| source_name | VARCHAR | NOT NULL, INDEXED | Data source identifier |
| source_id | VARCHAR | NOT NULL, INDEXED | Source-specific ID |
| genres | ARRAY/JSON | NULLABLE | List of genres |
| alternative_titles | ARRAY/JSON | NULLABLE | Alternative titles |
| is_active | BOOLEAN | NOT NULL, DEFAULT TRUE, INDEXED | Active status |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL | Last update timestamp |

**Unique Constraint:** `(source_name, source_id)`

### Episodes Table

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique identifier |
| anime_id | UUID | FOREIGN KEY, NOT NULL, INDEXED | References anime(id) |
| number | INTEGER | NOT NULL, INDEXED | Episode number |
| title | VARCHAR | NULLABLE | Episode title |
| source_episode_id | VARCHAR | NOT NULL, INDEXED | Source-specific episode ID |
| is_active | BOOLEAN | NOT NULL, DEFAULT TRUE, INDEXED | Active status |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL | Last update timestamp |

**Unique Constraint:** `(anime_id, source_episode_id)`

### VideoSources Table

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique identifier |
| episode_id | UUID | FOREIGN KEY, NOT NULL, INDEXED | References episodes(id) |
| type | VARCHAR | NOT NULL | Player type |
| url | VARCHAR | NOT NULL | Player/video URL |
| source_name | VARCHAR | NOT NULL, INDEXED | Source/player name |
| priority | INTEGER | NOT NULL, DEFAULT 0, INDEXED | Priority level |
| is_active | BOOLEAN | NOT NULL, DEFAULT TRUE, INDEXED | Active status |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL | Last update timestamp |

## Environment Variables

### Required

```bash
# Database connection
DATABASE_URL=postgresql+asyncpg://ani_user:ani_password@postgres:5432/ani_db

# Security tokens (generate with: openssl rand -hex 32)
SECRET_KEY=your-secret-key-min-32-chars-in-production
INTERNAL_TOKEN=your-internal-token-min-32-chars-in-production
```

### Optional

```bash
# App configuration
APP_NAME=Anirohi API
VERSION=1.0.0
DEBUG=true
ENV=dev

# JWT/Auth
ALGORITHM=HS256
JWT_ACCESS_TTL_MINUTES=15
REFRESH_TTL_DAYS=30
COOKIE_SECURE=false  # Set to true in production with HTTPS

# CORS (comma-separated)
ALLOWED_ORIGINS=http://localhost:3000

# Redis
REDIS_URL=redis://redis:6379/0
REDIS_MAX_CONNECTIONS=10

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60

# Observability
METRICS_ENABLED=true
TRACING_ENABLED=false
```

## Deployment

### Docker Compose

1. Copy the example environment file:
```bash
cd backend
cp .env.example .env
```

2. Generate secure tokens:
```bash
# Generate SECRET_KEY
openssl rand -hex 32

# Generate INTERNAL_TOKEN
openssl rand -hex 32
```

3. Update `backend/.env` with your tokens:
```bash
SECRET_KEY=your-generated-secret-key
INTERNAL_TOKEN=your-generated-internal-token
```

4. Start services:
```bash
# From repository root
docker compose up -d --build
```

5. Run migrations:
```bash
docker compose exec backend alembic upgrade head
```

6. Verify API is running:
```bash
curl http://localhost:8000/health
```

### Manual Deployment

1. Install dependencies:
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Run migrations:
```bash
alembic upgrade head
```

4. Start server:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Production Checklist

- [ ] Set `ENV=production` in `.env`
- [ ] Generate secure `SECRET_KEY` (≥32 characters)
- [ ] Generate secure `INTERNAL_TOKEN` (≥32 characters)
- [ ] Set `COOKIE_SECURE=true` (requires HTTPS)
- [ ] Configure proper `ALLOWED_ORIGINS` (no wildcards)
- [ ] Set `DEBUG=false`
- [ ] Configure PostgreSQL with proper credentials
- [ ] Setup Redis for caching
- [ ] Configure reverse proxy (nginx, Caddy, etc.)
- [ ] Enable HTTPS
- [ ] Setup monitoring and logging
- [ ] Configure backup strategy for database

## API Interactive Documentation

When `DEBUG=true`, interactive API documentation is available at:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Error Handling

All API endpoints follow consistent error response format:

```json
{
  "detail": "Error message here"
}
```

Common HTTP status codes:
- `200 OK`: Success
- `400 Bad Request`: Invalid request data
- `403 Forbidden`: Invalid authentication
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error

## Support

For issues or questions:
- Check the main [README.md](../../README.md)
- Review [backend documentation](./README.md)
- Check [architecture documentation](./architecture.md)

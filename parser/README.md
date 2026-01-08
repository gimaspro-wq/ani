# Parser Service

A Python service for importing anime data from Kodik and Shikimori into the backend.

## Overview

The parser service acts as a bridge between external anime data providers and the backend internal API. It:

1. Fetches anime listings from Kodik API
2. Retrieves metadata from Shikimori API
3. Imports anime, episodes, and video sources to the backend via internal API

**Key Features:**
- Idempotent operations (safe to re-run)
- Rate limiting and exponential backoff with jitter
- Concurrent requests with configurable limits
- State management for incremental runs
- Deterministic ID generation

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Parser Service                          │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │ Kodik Client │  │ Shikimori    │  │ Backend Client  │  │
│  │              │  │ Client       │  │                 │  │
│  └──────────────┘  └──────────────┘  └─────────────────┘  │
│         │                  │                   │            │
│         └──────────────────┴───────────────────┘            │
│                           │                                 │
│                  ┌────────▼────────┐                        │
│                  │  Orchestrator   │                        │
│                  └─────────────────┘                        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                           │
              ┌────────────┴───────────┐
              │                        │
         Kodik API              Shikimori API
         (video sources)        (metadata)
                                       │
                                Backend Internal API
                            (anime/episodes/video import)
```

## Environment Variables

Create a `.env` file in the `/parser` directory:

```bash
# Backend Configuration
BACKEND_BASE_URL=http://localhost:8000
INTERNAL_TOKEN=your_internal_token_here

# Concurrency and Rate Limiting
CONCURRENCY=4                    # Max concurrent requests (default: 4)
RATE_LIMIT_RPS=2                 # Requests per second (default: 2)
HTTP_TIMEOUT_SECONDS=30          # HTTP timeout (default: 30)

# Retry Configuration
MAX_RETRIES=3                    # Max retry attempts (default: 3)
BACKOFF_BASE_SECONDS=1           # Base backoff delay (default: 1)
BACKOFF_MAX_SECONDS=60           # Max backoff delay (default: 60)

# External APIs
KODIK_API_TOKEN=your_kodik_api_token_here
SHIKIMORI_BASE_URL=https://shikimori.one/api   # Optional
KODIK_BASE_URL=https://kodikapi.com            # Optional

# State Management
STATE_PATH=/tmp/parser_state.json              # State file location
```

### Required Variables

- `INTERNAL_TOKEN`: Backend internal API token (must match backend's `INTERNAL_TOKEN`)
- `KODIK_API_TOKEN`: API token for Kodik service

## Installation

```bash
cd parser
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

### Running Locally

```bash
# Activate virtual environment
source venv/bin/activate

# Run parser (all pages)
python -m parser.cli

# Run with page limit
python -m parser.cli --max-pages 5

# Run with debug logging
python -m parser.cli --debug
```

### Running with Docker

```bash
# Build the parser image
docker build -t ani-parser .

# Run as one-shot container
docker run --rm \
  --env-file .env \
  -v /tmp/parser_state:/state \
  ani-parser
```

### Cron Setup

To run the parser periodically via cron:

```bash
# Edit crontab
crontab -e

# Add entry to run daily at 3 AM
0 3 * * * cd /path/to/ani/parser && /path/to/venv/bin/python -m parser.cli >> /var/log/parser.log 2>&1

# Or with Docker
0 3 * * * docker run --rm --env-file /path/to/ani/parser/.env -v /tmp/parser_state:/state ani-parser >> /var/log/parser.log 2>&1
```

## Backend Contract

The parser uses the following backend internal API endpoints:

### 1. Import Anime

**Endpoint:** `POST /api/v1/internal/import/anime`

**Schema:**
```json
{
  "source_name": "kodik-shikimori",
  "source_id": "12345",
  "title": "Anime Title",
  "alternative_titles": ["Alternative Title"],
  "description": "Description",
  "year": 2023,
  "status": "ongoing",
  "poster": "https://example.com/poster.jpg",
  "genres": ["Action", "Adventure"]
}
```

### 2. Import Episodes

**Endpoint:** `POST /api/v1/internal/import/episodes`

**Schema:**
```json
{
  "source_name": "kodik-shikimori",
  "anime_source_id": "12345",
  "episodes": [
    {
      "source_episode_id": "12345:1",
      "number": 1,
      "title": "Episode 1 Title",
      "is_available": true
    }
  ]
}
```

### 3. Import Video Source

**Endpoint:** `POST /api/v1/internal/import/video`

**Schema:**
```json
{
  "source_name": "kodik-shikimori",
  "source_episode_id": "12345:1",
  "player": {
    "type": "iframe",
    "url": "https://kodik.cc/seria/12345/hash",
    "source_name": "kodik",
    "priority": 0
  }
}
```

## ID Generation Rules

The parser follows strict ID generation rules for consistency:

1. **Anime Source ID**: `source_id = str(shikimori_id)`
   - Example: Shikimori ID `12345` → source_id `"12345"`

2. **Episode Source ID**: `source_episode_id = "{source_id}:{episode_number}"`
   - Example: Anime `"12345"`, episode 1 → `"12345:1"`

3. **Player Source Name**: Always `"kodik"` (player provider name, not the backend source)

## Data Flow

1. **Fetch from Kodik**: Iterate through anime catalog, extract Shikimori IDs
2. **Fetch from Shikimori**: Get metadata for each anime (title, description, genres, etc.)
3. **Import Anime**: Send anime metadata to backend
4. **Determine Episodes**: Get episode list from Kodik
5. **Import Episodes**: Send episode list to backend
6. **Import Videos**: For each episode, import all available translations/players

## State Management

The parser maintains state in a JSON file to enable incremental runs:

- **Last processed page**: Tracks pagination progress
- **Processed anime**: Maps source_id → {title, episodes_count, timestamp}
- **Last run timestamp**: When the parser last completed

This ensures:
- Idempotent behavior (safe to re-run)
- Efficient incremental updates
- Recovery from interruptions

## Error Handling

The parser implements robust error handling:

- **Rate Limiting**: Respects `RATE_LIMIT_RPS` using token bucket algorithm
- **Exponential Backoff**: Retries failed requests with exponential backoff and jitter
- **Retry Logic**: Retries on 429 (rate limit), 5xx (server errors), and timeouts
- **Concurrency Control**: Limits concurrent requests to `CONCURRENCY` setting

## Development

### Running Tests

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Run with coverage
pytest --cov=parser --cov-report=html
```

### Project Structure

```
parser/
├── parser/                    # Main package
│   ├── __init__.py
│   ├── cli.py                # CLI entrypoint
│   ├── config.py             # Configuration
│   ├── orchestrator.py       # Main orchestration logic
│   ├── state.py              # State management
│   ├── clients/              # API clients
│   │   ├── __init__.py       # Base HTTP client
│   │   ├── kodik.py          # Kodik API client
│   │   ├── shikimori.py      # Shikimori API client
│   │   └── backend.py        # Backend API client
│   ├── utils/                # Utilities
│   │   └── __init__.py       # Rate limiter, ID generation
│   └── tests/                # Test files
│       ├── test_id_generation.py
│       ├── test_rate_limiting.py
│       └── test_schema_mapping.py
├── requirements.txt          # Production dependencies
├── requirements-dev.txt      # Development dependencies
├── Dockerfile                # Docker configuration
├── .env.example              # Example environment variables
└── README.md                 # This file
```

## Troubleshooting

### Common Issues

**Issue**: `Configuration error: INTERNAL_TOKEN is required`
- **Solution**: Ensure `.env` file exists with `INTERNAL_TOKEN` set

**Issue**: `Error fetching from Kodik: 401 Unauthorized`
- **Solution**: Verify `KODIK_API_TOKEN` is correct

**Issue**: `Error importing anime: 403 Forbidden`
- **Solution**: Verify `INTERNAL_TOKEN` matches backend configuration

**Issue**: Rate limiting errors (429)
- **Solution**: Reduce `RATE_LIMIT_RPS` or increase `BACKOFF_MAX_SECONDS`

### Debug Mode

Enable debug logging to see detailed information:

```bash
python -m parser.cli --debug
```

## Monitoring

The parser logs all operations to stdout:

- `INFO` level: Progress updates, successful operations
- `WARNING` level: Non-critical issues (missing data, retries)
- `ERROR` level: Failures, exceptions

Redirect logs to a file for monitoring:

```bash
python -m parser.cli >> /var/log/parser.log 2>&1
```

## Performance Tuning

Adjust these settings based on your needs:

- **CONCURRENCY**: Higher values = faster imports, but more load on APIs
- **RATE_LIMIT_RPS**: Respect API rate limits (typically 1-5 RPS)
- **MAX_RETRIES**: Balance between resilience and speed
- **BACKOFF_MAX_SECONDS**: Maximum wait time between retries

## License

See repository root LICENSE file.

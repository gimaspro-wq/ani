# Parser Service (Consumet GogoAnime)

This repository now contains a standalone parser service that collects anime metadata, episodes, and video sources from the public **consumet gogoanime** API and pushes normalized data into the backend internal API.

## Structure

```
parser/
├── client/             # HTTP + backend clients with retries and rate limiting
├── config/             # Environment-driven settings
├── normalizer/         # Dataclasses and serializers for backend payloads
├── source_adapters/    # Source-specific adapters (gogoanime)
└── main.py             # CLI entry point
```

## Configuration

Create a `.env` file from the example:

```bash
cp parser/.env.example parser/.env
```

Environment variables:

| Variable | Description | Default |
| --- | --- | --- |
| `PARSER_BACKEND_URL` | Backend base URL | `http://localhost:8000` |
| `PARSER_INTERNAL_TOKEN` | Internal API token | (required for writes) |
| `PARSER_SOURCE_LIMIT` | How many anime items to process | `5` |
| `PARSER_RPS` | Requests per second rate limit | `1.0` |
| `PARSER_REQUEST_TIMEOUT` | Request timeout (seconds) | `15` |
| `PARSER_MAX_RETRIES` | Max retries per request | `3` |
| `PARSER_BACKOFF_FACTOR` | Backoff factor for retries | `1.0` |
| `PARSER_DRY_RUN` | Skip backend writes when set to `1` | `1` |
| `CONSUMET_BASE_URL` | Source API base URL | `https://api.consumet.org/anime/gogoanime` |

You can also override the user-agent rotation list via `PARSER_USER_AGENTS` (newline-separated).

## Running

```bash
cd /home/runner/work/ani/ani
python -m parser.main --limit 10       # real import (requires token)
python -m parser.main --limit 3 --dry-run  # fetch + normalize without writes
```

## Behavior

- Fetches top-airing anime (paginated) from consumet.
- For each title, fetches episode list, then best available video source (prefers m3u8).
- Normalizes data to backend contracts:
  - `POST /api/v1/internal/import/anime`
  - `POST /api/v1/internal/import/episodes`
  - `POST /api/v1/internal/import/video`
- Resilient network handling:
  - Retry with exponential backoff
  - Global rate limiting
  - User-agent rotation
  - Per-request timeouts
- Continues processing even if a single anime/episode fails (errors are logged).

## Testing

Unit tests for the parser live in `parser/tests` and can be executed with:

```bash
PYTHONPATH=. pytest parser/tests -q
```

Tests use `httpx.MockTransport` and do not perform real network calls.

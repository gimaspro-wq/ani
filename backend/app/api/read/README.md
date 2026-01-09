# Read API routers

Read-only FastAPI routers backed solely by Redis read models:
- `read_anime.py` — catalog/detail endpoints at `/api/read/anime`
- `read_user.py` — per-user library/progress/history-last at `/api/read/me/*`

Behavior:
- Missing Redis keys return 404; there is no fallback to Postgres or rebuild-on-read.
- Payloads are served as-is from Redis and must be populated by operational rebuilds.

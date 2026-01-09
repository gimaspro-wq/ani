# Read-model infrastructure

Redis-backed read models used by `/api/read/**`:
- `redis_keys.py` — key builders
- `models/` — dataclasses for cached payloads
- `repositories/` — Redis accessors
- `events/` — rebuild handlers to snapshot Postgres into Redis

These components never mutate Postgres and are intended for operational rebuild flows, not for write-path requests.

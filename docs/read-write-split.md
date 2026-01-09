# Read / Write Split

## Write path (source of truth)

- Routes: `/api/v1/**` (auth, users, library/history/progress, anime, admin, internal import).
- Storage: PostgreSQL via SQLAlchemy models/repositories.
- Behavior: Contracts are stable; no schema or semantics changes in this effort. Rate limiting is optional and gated by `RATE_LIMIT_ENABLED`.
- Dependencies: Uses FastAPI DI, `app.core` utilities, repositories, and services. Does **not** depend on Redis read models.

## Read path (cache-first, Redis-only)

- Routes: `/api/read/**`
  - `/api/read/anime` catalog/detail from Redis.
  - `/api/read/me/*` (library/progress/history-last) from Redis per user.
- Behavior:
  - If a Redis key is missing, return 404 (no fallback to Postgres).
  - If a key exists but payload is empty, return 200 with an empty array/object.
  - No rebuild-on-read; cache is treated as authoritative once populated.
- Dependencies: `app.infrastructure.read.*` repositories + Redis client. No write-path coupling.

## Rebuild model

- Read models are (re)built out-of-band through operational triggers (manual/admin/cron) that call the handlers under `app/infrastructure/read/events/*`.
- Parser/importer runs populate write models; a separate rebuild must push snapshots to Redis.
- Missing read data signals an operational gap, not an API bug.

## Allowed interactions

- Write path may emit events to trigger rebuilds externally but should not read from Redis.
- Read path must never mutate Postgres; it only reads Redis.
- Admin tooling may orchestrate rebuilds but must keep write contracts untouched.

## Operational checks

- Monitor 404 rates on `/api/read/**` as indicators to rebuild caches.
- Ensure Redis availability for production; in non-production the app tolerates Redis absence for startup.

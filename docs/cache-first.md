# Cache-First Read Models

The API exposes cache-first endpoints that rely solely on Redis read models. The write database is never consulted for these paths.

## Redis models

- **Anime catalog**: `anime_catalog_key()` → list of `AnimeCatalogItem`
- **Anime detail**: `anime_detail_key(slug)` → `AnimeDetail`
- **User library**: `user_library_key(user_id, provider)` → list of `UserLibraryEntry`
- **User progress**: `user_progress_key(user_id, provider)` → list of `UserProgressEntry`
- **User history (last)**: `user_history_last_key(user_id, provider)` → `UserHistoryLast`

## API behavior

- Missing key ⇒ 404 (signals cache not built).
- Present but empty ⇒ 200 with empty payload.
- No automatic repopulation on read; rebuilding is explicit.

## Rebuild workflow

1. Ingest/refresh source data (parser or admin tooling updates Postgres via write APIs).
2. Run read-model rebuild handlers under `app/infrastructure/read/events/*` to snapshot Postgres state into Redis.
3. Verify by hitting `/api/read/**` endpoints; 404s should clear after a successful rebuild.

## Safety rules

- Do not route write requests through Redis.
- Do not fall back to Postgres inside read endpoints.
- Keep Redis credentials/configuration aligned with `REDIS_URL` and connection limits; Redis is required in production for read endpoints.

## Monitoring signals

- Elevated 404 on `/api/read/**` → rebuild needed or Redis unavailable.
- Redis connectivity issues during startup are fatal in production but tolerated in dev/test.

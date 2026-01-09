# Deployment Guide

Objective: production-ready deployment without changing API contracts or write-path behavior.

## Services

- **backend** (FastAPI): requires Postgres, Redis, and environment variables.
- **frontend** (Next.js): static/edge build; consumes backend APIs.
- **parser** (Python CLI): one-shot/cron importer; not a long-lived service.

## Environment (backend)

Required:
- `DATABASE_URL` — Postgres connection (asyncpg)
- `SECRET_KEY` — JWT signing key (32+ hex chars)

Recommended:
- `ALLOWED_ORIGINS` — CORS origins
- `RATE_LIMIT_ENABLED` + `RATE_LIMIT_PER_MINUTE`
- `METRICS_ENABLED`, `TRACING_ENABLED`, `OTEL_EXPORTER_OTLP_ENDPOINT`
- `REDIS_URL`, `REDIS_MAX_CONNECTIONS`
- `ENV=production`, `DEBUG=false`

Production startup validates Alembic migrations; Redis failures are fatal in production.

## Build & run (Docker)

From repo root:

```bash
# build images
docker compose build

# run services (backend + frontend + dependencies)
docker compose up -d
```

Logs:
```bash
docker compose logs -f backend
docker compose logs -f frontend
```

Health:
- Backend: `/health`
- Metrics (if enabled): `/metrics`

## Parser runs

- Run as cron/one-shot job using `parser` image or local venv.
- Needs `BACKEND_BASE_URL`, `INTERNAL_TOKEN`, `KODIK_API_TOKEN`.
- Safe to rerun; state file path can be provided for incremental runs.

## Read-model rebuilds

- After imports or data corrections, run read-model rebuild handlers (under `app/infrastructure/read/events/*`) to push snapshots to Redis.
- Expect 404s on `/api/read/**` until caches are rebuilt.

## Checklist

- [ ] `ENV=production`, `DEBUG=false`
- [ ] Strong `SECRET_KEY`
- [ ] Postgres reachable and migrated (`alembic upgrade head`)
- [ ] Redis reachable for read endpoints and rate limiting
- [ ] CORS origins configured (no wildcards in prod)
- [ ] TLS/ingress configured
- [ ] Metrics/tracing endpoints secured or disabled as required
- [ ] Parser credentials set (backend internal token, external API tokens)
- [ ] Backups and monitoring in place (HTTP 5xx, p95 latency, Redis availability)

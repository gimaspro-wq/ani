# Architecture

This monorepo contains three deployable surfaces that operate together but remain contract-stable:

- **backend/** — FastAPI service providing authentication, library/history/progress write APIs, and read-only Redis-backed endpoints. Layers: API (FastAPI routers) → application/use-cases → domain interfaces/entities → infrastructure (SQLAlchemy, Redis adapters) with cross-cutting core (config, middleware, security, logging, rate limiting, tracing).
- **frontend/** — Next.js (App Router) client with public surfaces under `src/app/**` and legacy admin under `src/app/admin/**`. Public pages consume the public API client; admin pages use legacy orpc/query stacks. Keep dependencies from admin paths out of public routes.
- **parser/** — One-shot/cron importer that ingests data from external providers (Kodik/Shikimori) and posts to backend internal endpoints.

## Layer boundaries (backend)

- **API**: FastAPI routers under `app/api/**` and `app/api/read/**`. They depend on FastAPI dependencies and schemas only.
- **Application**: Use-cases/services coordinate repositories and adapters (`app/services`, `app/application/use_cases`).
- **Domain**: Interfaces, enums, errors kept framework-agnostic (`app/domain/**`).
- **Infrastructure**: Database models/repositories, Redis adapters, security helpers (`app/db`, `app/infrastructure/**`).
- **Core**: Config, middleware, logging, tracing, rate limiting (`app/core/**`).

Allowed dependency flow: `api → application → domain ← infrastructure`; `core` is used by all layers for cross-cutting concerns.

## Read vs write surfaces

- **Write path**: `/api/v1/**` routers backed by Postgres via SQLAlchemy repositories. Contract is stable; do not change schemas or semantics.
- **Read path**: `/api/read/**` routers serve Redis read models only. Missing keys return 404; there is no rebuild-on-read and no fallback to the write database.

## Observability and safety

- Optional Prometheus metrics (`/metrics`) and OpenTelemetry tracing are enabled via settings; rate limiting is gated by `RATE_LIMIT_ENABLED`.
- Production startup validates Alembic migrations; Redis connection failures are tolerated in non-production.
- Security: JWT access tokens + refresh tokens (hashed, rotated), security headers, trace IDs, structured logging.

## Data flow highlights

1. Parser imports catalog/episodes/video sources via backend internal endpoints (`/api/v1/internal/**`).
2. Write APIs persist to Postgres.
3. Read models are populated externally (manual/admin/cron) into Redis; the API does not backfill on read.

## Frontend boundaries

- Public pages should depend on `src/lib/public-api.ts` and avoid admin-only stacks (`src/lib/orpc`, `src/lib/query`, `src/lib/search`) to keep the public surface lean.
- Admin pages stay within `src/app/admin/**` and can use the legacy stacks above.

## Deployment shape

- Services run separately (backend, frontend, parser). Compose files orchestrate local/dev runs; production deployments should keep the same boundaries and settings documented in `docs/deployment.md`.

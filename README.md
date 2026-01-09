# Ani monorepo

## Project overview

Ani is a monorepo containing three subsystems:
- **frontend**: Next.js app that serves the public anime catalog/watch experience and a legacy admin panel.
- **backend**: FastAPI service that powers authentication and data APIs. Treat as stable; no contract changes here.
- **parser**: Python importer that keeps the catalog in sync with external sources.

This README is the single source of truth for repository structure and local workflows.

## Architecture at a glance

- **frontend/**
  - `src/app` holds the public app routes.
  - `src/app/admin/**` is the legacy admin panel surface.
  - `src/lib/orpc/**`, `src/lib/query/**`, `src/lib/search/**` are admin-only infrastructure; keep public pages clear of these dependencies.
- **backend/** provides API + auth; see `backend/docs/` for details.
- **parser/** ingests anime data; see `parser/README.md`.
- Admin-only docs live in [`ADMIN_PANEL.md`](./ADMIN_PANEL.md) and [`QUICK_START_ADMIN.md`](./QUICK_START_ADMIN.md).

## Running the stack locally (high level)

Prerequisites: Node.js 18+, Python 3.11+, Docker with Compose, PostgreSQL (Compose profile provided).

1. **Backend**
   - `cd backend && cp .env.example .env` then set `SECRET_KEY` (generate with `openssl rand -hex 32`) and DB credentials.
   - Start with Docker: `docker compose up -d --build` (or add `-f docker-compose.dev.yml` for dev).
2. **Parser** (optional locally)
   - `cd parser && python -m venv venv && source venv/bin/activate`
   - `pip install -r requirements.txt && cp .env.example .env`
   - Run when needed: `python -m parser.cli run --mode full`.
3. **Frontend**
   - `cd frontend && npm ci && cp .env.example .env.local`
   - `npm run dev` (public app at http://localhost:3000).

> **Security:** Keep backend/.env, parser/.env, and frontend/.env.local out of version control (these files are gitignored; do not override that). If secrets are committed, rotate them immediately and scrub history (e.g., with git filter-repo or BFG).

## Boundaries and ownership

- **Public frontend**: routes under `frontend/src/app` (excluding `/admin`).
  - Avoid introducing dependencies on admin-only code.
  - Prefer `frontend/src/lib/public-api.ts`/fetch over `frontend/src/lib/orpc/**`, `frontend/src/lib/query/**`, or `frontend/src/lib/search/**`.
  - Legacy overlap exists and should be migrated away.
- **Admin**: lives at `frontend/src/app/admin/**` and relies on the legacy infra above. Treat as isolated and stable; changes should stay inside these paths.
- **Admin-only infrastructure** (legacy):
  - `frontend/src/app/admin/**` – legacy admin surface.
  - `frontend/src/lib/orpc/**` – admin RPC wiring.
  - `frontend/src/lib/query/**` – admin query helpers.
  - `frontend/src/lib/search/**` – admin search helpers.
- Admin docs (`ADMIN_PANEL.md`, `QUICK_START_ADMIN.md`) are for admin operators only.
- Backend and parser contracts are stable; avoid altering them as part of frontend work.

## Not implemented yet

- No media uploads/encoding pipeline (only external sources are used).
- No push/notification system.
- No mobile or desktop client bundles.
- No multi-tenant or role-based admin beyond the existing legacy admin user flow.

## CI / lint notes

- Frontend linting may emit warnings/errors from legacy admin code; these are known and isolated to admin paths.
- Prefer scoped linting when iterating on public pages; avoid refactoring admin logic while addressing lint noise.
- CodeQL/other CI jobs may report legacy patterns; treat admin-related findings separately from public app work.

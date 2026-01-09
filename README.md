# Ani monorepo

Production-ready stack for anime catalog/browsing with a FastAPI backend, Next.js frontend, and a parser/importer. Contracts are stable; write-path logic must not change.

## Components
- **backend/** — FastAPI service (auth, library/history/progress, anime, admin/internal import) plus read-only Redis-backed endpoints.
- **frontend/** — Next.js App Router. Public surface under `src/app/**`; legacy admin under `src/app/admin/**` using legacy orpc/query stacks.
- **parser/** — Python importer that ingests external data (Kodik/Shikimori) into the backend via internal endpoints.

## Documentation
- [`docs/architecture.md`](docs/architecture.md)
- [`docs/read-write-split.md`](docs/read-write-split.md)
- [`docs/cache-first.md`](docs/cache-first.md)
- [`docs/development.md`](docs/development.md)
- [`docs/deployment.md`](docs/deployment.md)
- [`docs/phase-history.md`](docs/phase-history.md)
- Admin operator notes: [`ADMIN_PANEL.md`](ADMIN_PANEL.md), [`QUICK_START_ADMIN.md`](QUICK_START_ADMIN.md)
- Parser details: [`parser/README.md`](parser/README.md)

## Quickstart (summary)

Backend:
```bash
cd backend
cp .env.example .env   # set DATABASE_URL, SECRET_KEY, Redis settings
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && pip install -r requirements-dev.txt
alembic upgrade head
uvicorn app.main:app --reload
```

Frontend:
```bash
cd frontend
npm ci
cp .env.example .env.local
npm run dev   # http://localhost:3000
```

Parser:
```bash
cd parser
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # set BACKEND_BASE_URL, INTERNAL_TOKEN, KODIK_API_TOKEN
python -m parser.cli run --mode full
```

## Boundaries
- Public frontend must avoid admin-only stacks (`src/lib/orpc`, `src/lib/query`, `src/lib/search`).
- Read endpoints (`/api/read/**`) use Redis only; missing keys return 404 and require operational rebuilds.
- Write endpoints (`/api/v1/**`) persist to Postgres; keep schemas and semantics unchanged.
- Redis is required in production for read endpoints and rate limiting; tolerated as optional in dev/test.

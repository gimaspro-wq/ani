# Development Guide

Goal: run the stack locally without altering contracts or write-path semantics.

## Prerequisites

- Node.js 18+
- Python 3.11+
- Docker + Docker Compose
- PostgreSQL (Compose profiles provided)
- Redis (for read endpoints and rate limiting)

## Backend (FastAPI)

```bash
cd backend
cp .env.example .env    # set DATABASE_URL, SECRET_KEY, optional Redis settings
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
alembic upgrade head
uvicorn app.main:app --reload
```

Tests:

```bash
pytest
```

Notes:
- Redis is optional in dev/test; startup continues without it. Production requires Redis for rate limiting and read endpoints.
- Do not change API contracts (`/api/v1/**` or `/api/read/**`).

## Frontend (Next.js)

```bash
cd frontend
npm ci
cp .env.example .env.local
npm run dev   # http://localhost:3000
```

Guidance:
- Public pages under `src/app/**` (excluding `/admin`) should use `src/lib/public-api.ts`.
- Admin surfaces under `src/app/admin/**` may use legacy stacks (`src/lib/orpc`, `src/lib/query`, `src/lib/search`); keep them isolated from public routes.

## Parser (importer)

```bash
cd parser
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # set BACKEND_BASE_URL, INTERNAL_TOKEN, KODIK_API_TOKEN
python -m parser.cli run --mode full
```

## Docker Compose (dev)

From repo root:

```bash
docker compose -f docker-compose.dev.yml up --build
```

Adjust env files for each service before starting. Production hardening is covered in `docs/deployment.md`.

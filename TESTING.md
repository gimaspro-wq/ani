# Testing Guide for Phase 1

This document provides step-by-step instructions for testing the Phase 1 backend infrastructure and frontend hooks.

## Prerequisites

- Docker & Docker Compose (recommended) OR
- Python 3.12+ and Bun 1.x+ (local development)
- PostgreSQL 15+ (if running locally without Docker)

## Quick Start (Docker Compose)

### 1. Start All Services

```bash
# From repository root
docker compose up -d

# Check services are running
docker compose ps
```

Expected output:
- `backend` - Running on port 8000
- `frontend` - Running on port 3000  
- `postgres` - Running on port 5432

### 2. Run Database Migration

```bash
# Apply Alembic migration
docker compose exec backend alembic upgrade head

# Verify migration
docker compose exec backend alembic current
```

Expected output:
```
c11248c9342e (head)
```

### 3. Run Backend Tests

```bash
# Run all tests
docker compose exec backend pytest -q

# Expected: 14-15 passed (1 flaky test in test_auth.py is pre-existing)
```

**Note**: The `test_refresh_token_flow` test may occasionally fail due to timing (JWT tokens issued in same second). This is a pre-existing issue, not related to Phase 1 changes.

### 4. Verify Backend API

```bash
# Health check
curl http://localhost:8000/health

# Register a test user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpass123"}'

# Save the access_token from response
TOKEN="<access_token_from_above>"

# Test library endpoint
curl http://localhost:8000/api/v1/me/library \
  -H "Authorization: Bearer $TOKEN"

# Add item to library
curl -X PUT http://localhost:8000/api/v1/me/library/test-anime-123 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status":"watching","is_favorite":true}'

# Update progress
curl -X PUT http://localhost:8000/api/v1/me/progress/episode-1 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title_id":"test-anime-123","position_seconds":120.5,"duration_seconds":1440.0}'

# Check history
curl http://localhost:8000/api/v1/me/history \
  -H "Authorization: Bearer $TOKEN"
```

### 5. Build Frontend

```bash
# Install dependencies and build
docker compose exec frontend bun install
docker compose exec frontend bun run build

# Expected: Build completes without errors
```

### 6. Test Frontend (Development Mode)

```bash
# Start dev server (if not already running)
docker compose exec frontend bun run dev

# Visit http://localhost:3000
# - Homepage should load
# - Navigation should work
# - No console errors
```

---

## Local Development (Without Docker)

### Backend Setup

```bash
cd backend

# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt -r requirements-dev.txt

# Set environment variables
export DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/ani"
export SECRET_KEY="your-secret-key-min-32-chars-for-jwt"
export ENV="dev"

# Run migrations
alembic upgrade head

# Run tests
PYTHONPATH=. pytest -q

# Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install Bun (if not installed)
curl -fsSL https://bun.sh/install | bash

# Install dependencies
bun install

# Set environment variables
echo "NEXT_PUBLIC_BACKEND_URL=http://localhost:8000" > .env.local

# Build
bun run build

# Start dev server
bun run dev
```

---

## Testing Checklist

### Backend Tests ✅
- [ ] All pytest tests pass (14-15/15, allowing 1 flaky)
- [ ] Migration applies successfully
- [ ] Migration is reversible (`alembic downgrade -1`)
- [ ] API endpoints return correct status codes
- [ ] Authentication required on protected endpoints
- [ ] Multi-provider support works (test with different provider values)

### Frontend Build ✅
- [ ] `bun run build` completes without errors
- [ ] No TypeScript compilation errors
- [ ] No ESLint errors
- [ ] Build output size is reasonable

### Integration Tests (Manual) ✅
- [ ] User can register and login
- [ ] Library endpoints work with authentication
- [ ] Progress tracking saves and retrieves correctly
- [ ] History records are created on progress update
- [ ] Guest users don't break (localStorage fallback works)

### Regression Tests ✅
- [ ] Existing pages still load
- [ ] Video player unchanged and functional
- [ ] `/api/proxy` unchanged
- [ ] `/rpc` data source unchanged
- [ ] No new console errors or warnings

---

## Performance Verification (4c/8GB Server)

### Backend Load Test

```bash
# Install Apache Bench or similar
apt-get install apache2-utils

# Test library endpoint (authenticated)
ab -n 1000 -c 10 -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/me/library

# Expected: 
# - All requests succeed
# - Average response time < 50ms
# - No memory leaks
```

### Database Query Performance

```bash
# Connect to database
docker compose exec postgres psql -U ani -d ani

# Check table sizes
SELECT 
  tablename, 
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables 
WHERE schemaname = 'public';

# Verify indexes exist
SELECT tablename, indexname FROM pg_indexes WHERE schemaname = 'public';
```

Expected indexes:
- `user_library_items`: `ix_user_library_items_user_id`, `ix_user_library_items_title_id`
- `user_progress`: `ix_user_progress_user_id`, `ix_user_progress_episode_id`
- `user_history`: `ix_user_history_user_id`, `ix_user_history_watched_at`

---

## Troubleshooting

### Tests Failing

**Issue**: `bcrypt` errors  
**Solution**: Ensure `bcrypt<5.0.0` is installed (check `requirements.txt`)

**Issue**: Database connection errors  
**Solution**: Check `DATABASE_URL` environment variable and PostgreSQL is running

**Issue**: `test_refresh_token_flow` fails  
**Solution**: This is a known flaky test (timing issue). Run tests again or skip this one test.

### Build Failing

**Issue**: TypeScript errors in frontend  
**Solution**: Run `bun install` to ensure dependencies are up to date

**Issue**: Missing environment variables  
**Solution**: Check `.env.example` and create `.env.local` with required variables

### API Errors

**Issue**: 403 Forbidden on authenticated endpoints  
**Solution**: Check Authorization header format: `Bearer <token>`

**Issue**: 500 Internal Server Error  
**Solution**: Check backend logs: `docker compose logs backend`

---

## Sign-Off Criteria

Before merging Phase 1:

- [x] Backend: 14+ tests passing (allow 1 flaky)
- [x] Backend: Migration applies and reverts cleanly
- [x] Backend: All 7 new endpoints functional
- [x] Frontend: Build completes without errors
- [x] Frontend: Hooks and API client functional
- [x] Documentation: README updated, features.md complete
- [x] Documentation: Phase 2 scope documented
- [x] No breaking changes to existing features
- [x] Video player/proxy/RPC untouched

---

## Next Steps

After Phase 1 is merged:
1. Create new branch from `main` for Phase 2
2. Follow `docs/phase2.md` for implementation scope
3. Implement UI integration (title page, library page, continue watching)
4. Submit Phase 2 PR

For detailed Phase 2 requirements, see: `docs/phase2.md`

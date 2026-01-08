# Anirohi - Monorepo

<p align="center">
  <strong>Stream anime. No interruptions.</strong>
</p>

## Project Structure

This is a monorepo containing:

```
ani/
├── backend/          # FastAPI authentication backend
├── frontend/         # Next.js web application  
├── docs/             # General documentation
├── docker-compose.yml # Docker services (backend + postgres)
└── README.md         # This file
```

## Quick Start

### Prerequisites

- **Frontend**: [Bun](https://bun.sh/) (recommended) or Node.js 18+
- **Backend**: Python 3.11+ and Docker (for PostgreSQL)
- **Database**: PostgreSQL 16+ (via Docker or local install)

### Development Setup

#### 1. Clone the Repository

```bash
git clone https://github.com/stalkerghostzone-lab/ani.git
cd ani
```

#### 2. Configure Backend Environment

```bash
cd backend
cp .env.example .env

# IMPORTANT: Edit backend/.env and set a secure SECRET_KEY
# Generate one with: openssl rand -hex 32
# Then update the SECRET_KEY line in backend/.env
```

See [Backend Setup Guide](backend/docs/setup.md) for detailed configuration options.

#### 3. Start Backend Services

```bash
# Return to repository root
cd ..

# Start PostgreSQL and backend API (production mode)
docker compose up -d --build

# For development with hot-reload, use:
# docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build

# The backend API will be available at http://localhost:8000
# API docs at http://localhost:8000/docs
```

**Note**: Modern Docker uses `docker compose` (with a space). The legacy `docker-compose` command still works but is deprecated.

Alternatively, run backend locally without Docker:

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Make sure PostgreSQL is running (via docker compose or locally)
# and backend/.env is configured

alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

#### 4. Start Frontend

```bash
cd frontend
bun install
cp .env.example .env.local

# Optional: Edit .env.local if you need to override defaults
# NEXT_PUBLIC_APP_URL is optional and defaults to localhost:3000

bun dev
```

The frontend will be available at [http://localhost:3000](http://localhost:3000).

## Backend

The backend is a FastAPI application providing authentication APIs.

### Features

- ✅ User registration and login
- ✅ JWT access tokens (15min TTL)
- ✅ Refresh tokens in httpOnly cookies (30 day TTL)
- ✅ Token rotation on refresh
- ✅ Password hashing with bcrypt
- ✅ CORS support
- ✅ Comprehensive test suite

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/auth/register` | POST | Register new user |
| `/api/v1/auth/login` | POST | Login with credentials |
| `/api/v1/auth/refresh` | POST | Refresh access token |
| `/api/v1/auth/logout` | POST | Logout and revoke tokens |
| `/api/v1/users/me` | GET | Get current user info |
| `/docs` | GET | Interactive API documentation |

### Backend Documentation

- [Architecture](backend/docs/architecture.md) - Backend structure and design decisions
- [Authentication](backend/docs/auth.md) - Auth flows, cookies, and token details
- [API Plan](backend/docs/api-plan.md) - MVP endpoints and excluded features

### Running Backend Tests

```bash
cd backend
pip install -r requirements-dev.txt
pytest -v
```

## Frontend

The frontend is a Next.js 16 application with React 19.

### Features

- **Clean UI** — Minimalist design focused on content
- **Fast Search** — Quick anime discovery with command menu (⌘K)
- **Trending** — Stay updated with currently popular anime
- **Schedule** — Track upcoming episode releases
- **PWA Support** — Install as a native app on any device
- **Watch Progress** — Track episode progress locally
- **Saved Series** — Save favorite anime

### Tech Stack

- [Next.js 16](https://nextjs.org/) — React framework with App Router
- [React 19](https://react.dev/) — UI library with React Compiler
- [Tailwind CSS v4](https://tailwindcss.com/) — Utility-first styling
- [shadcn/ui](https://ui.shadcn.com/) — Accessible component primitives
- [oRPC](https://orpc.dev/) — End-to-end typesafe APIs (for anime data)
- [TanStack Query](https://tanstack.com/query) — Async state management
- [Aniwatch API](https://github.com/ghoshRitesh12/aniwatch-api) — Anime data provider

### Frontend Documentation

- [Platform](docs/platform.md) - UI screens, components, user flows, features
- [Architecture](docs/architecture.md) - App startup, storage, data lifecycle, technical flows

### Commands

```bash
cd frontend
bun dev       # Start development server
bun build     # Build for production
bun start     # Start production server
bun lint      # Run ESLint
```

## Environment Variables

### Backend (`backend/.env`)

Create from example: `cp backend/.env.example backend/.env`

**Required**:
```bash
# Security (CRITICAL: CHANGE IN PRODUCTION!)
# Generate with: openssl rand -hex 32
SECRET_KEY=your-secret-key-min-32-chars-in-production
```

**Optional** (with defaults):
```bash
# App
APP_NAME=Anirohi API
DEBUG=true
ENV=dev

# Database (defaults work with docker compose)
DATABASE_URL=postgresql+asyncpg://ani_user:ani_password@postgres:5432/ani_db

# JWT/Auth
JWT_ACCESS_TTL_MINUTES=15
REFRESH_TTL_DAYS=30
COOKIE_SECURE=false  # Set to true in production with HTTPS

# CORS (comma-separated)
ALLOWED_ORIGINS=http://localhost:3000
```

See [Backend Setup Guide](backend/docs/setup.md) for complete configuration details.

### Frontend (`frontend/.env.local`)

Create from example: `cp frontend/.env.example frontend/.env.local`

**All variables are optional**:
```bash
# Override app URL if needed (defaults to window.location.origin in browser)
# NEXT_PUBLIC_APP_URL=http://localhost:3000
```

## Docker Compose Services

```yaml
services:
  postgres:    # PostgreSQL 16 database (port 5432)
  backend:     # FastAPI application (port 8000)
```

**Prerequisites**: 
- Copy `backend/.env.example` to `backend/.env` and set `SECRET_KEY`
- Generate SECRET_KEY with: `openssl rand -hex 32`

Start services:
```bash
# Production mode (no hot-reload)
docker compose up -d --build

# Development mode (with hot-reload)
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build

# View backend logs
docker compose logs -f backend

# Stop services
docker compose down

# Run migrations manually if needed
docker compose exec backend alembic upgrade head
```

## Contributing

Contributions are welcome! Feel free to open an issue or submit a pull request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is open source and available under the [MIT License](LICENSE).

---

<p align="center">
  Made with ❤️ by the Anirohi team
</p>

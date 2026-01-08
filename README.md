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

- **Frontend**: Node.js 18+
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
npm install
cp .env.example .env.local

# Optional: Edit .env.local if you need to override defaults
# NEXT_PUBLIC_APP_URL is optional and defaults to localhost:3000

npm run dev
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
- ✅ **User library management** (watching, planned, completed, dropped)
- ✅ **Watch progress tracking** (synced across devices)
- ✅ **Watch history** (recent episodes watched)
- ✅ **Multi-provider support** (ready for future data sources)

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/auth/register` | POST | Register new user |
| `/api/v1/auth/login` | POST | Login with credentials |
| `/api/v1/auth/refresh` | POST | Refresh access token |
| `/api/v1/auth/logout` | POST | Logout and revoke tokens |
| `/api/v1/users/me` | GET | Get current user info |
| `/api/v1/me/library` | GET | Get user's library items |
| `/api/v1/me/library/{title_id}` | PUT | Add/update library item |
| `/api/v1/me/library/{title_id}` | DELETE | Remove library item |
| `/api/v1/me/progress` | GET | Get watch progress |
| `/api/v1/me/progress/{episode_id}` | PUT | Update episode progress |
| `/api/v1/me/history` | GET | Get watch history |
| `/api/v1/me/import-legacy` | POST | Import legacy local data (one-time migration) |
| `/docs` | GET | Interactive API documentation |

### User Data Sync

**All user data is stored server-side** and synced across devices when logged in:

- Watch progress and history are saved only to the server
- Library status and favorites require authentication
- Offline changes are not supported (login required to track progress)
- **Legacy Data Migration**: When you first login after updating, any existing local data is automatically imported to your account

> **Note**: Search index is cached locally in IndexedDB for performance, but this is not user data.

### Backend Documentation

- [Architecture](backend/docs/architecture.md) - Backend structure and design decisions
- [Authentication](backend/docs/auth.md) - Auth flows, cookies, and token details
- [API Plan](backend/docs/api-plan.md) - MVP endpoints and excluded features
- [**Features Guide**](docs/features.md) - Library, progress, history features

### Running Backend Tests

```bash
cd backend
pip install -r requirements-dev.txt
pytest -v
```

### Running Database Migrations

After pulling updates, run migrations to update the database schema:

```bash
cd backend

# If using Docker:
docker compose exec backend alembic upgrade head

# If running locally:
source venv/bin/activate
alembic upgrade head
```

## Frontend

The frontend is a Next.js 16 application with React 19.

### Features

- **Clean UI** — Minimalist design focused on content
- **Fast Search** — Quick anime discovery with command menu (⌘K)
- **Advanced Search** — Filters by genre, year, season, type with shareable URLs
- **Client-Side Index** — Instant search with MiniSearch + IndexedDB caching
- **Trending** — Stay updated with currently popular anime
- **Schedule** — Track upcoming episode releases
- **PWA Support** — Install as a native app on any device
- **Watch Progress** — Track episode progress (synced across devices when logged in)
- **Library Management** — Organize anime by status (watching, planned, completed, dropped)
- **Favorites** — Mark anime as favorites

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
- [**Features Guide**](docs/features.md) - Library, progress, history features

### Commands

```bash
cd frontend
npm run dev       # Start development server
npm run build     # Build for production
npm run start     # Start production server
npm run lint      # Run ESLint
```

## Search & Filters

### Advanced Search

Navigate to `/search` for advanced search with filters:

- **Text search**: Search by anime title (English or Japanese)
- **Genres**: Filter by multiple genres (Action, Adventure, Comedy, etc.)
- **Type**: Filter by TV, Movie, OVA, ONA, Special
- **Year**: Filter by release year
- **Season**: Filter by season (Winter, Spring, Summer, Fall)

All filters are synced to the URL, making searches shareable:

```
/search?q=demon&type=tv&year=2019&genres=Action&genres=Fantasy
```

### Command Palette

Press `⌘K` (Mac) or `Ctrl+K` (Windows/Linux) to open the quick search palette:

- Type to search anime instantly
- Recent searches stored for quick access
- Keyboard navigation with arrow keys
- Press Enter to navigate to selected anime

### Client-Side Search Index

The app builds a local search index from popular anime for instant results:

- **Automatic**: Index built on first use from popular/recent/airing anime
- **Persistent**: Stored in IndexedDB with 24-hour cache
- **Fast**: Prefix and fuzzy matching with MiniSearch
- **Efficient**: Only necessary fields indexed to save memory

To clear the search index:
1. Open browser DevTools (F12)
2. Go to Application tab
3. Under Storage → IndexedDB → Delete `keyval-store`

Or use the console:
```javascript
indexedDB.deleteDatabase('keyval-store');
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

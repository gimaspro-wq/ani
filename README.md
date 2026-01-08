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

#### 2. Start Backend Services

```bash
# Start PostgreSQL and backend API
docker-compose up -d

# The backend API will be available at http://localhost:8000
# API docs at http://localhost:8000/docs
```

Alternatively, run backend locally:

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

#### 3. Start Frontend

```bash
cd frontend
bun install
cp .env.example .env.local

# Edit .env.local and add:
# NEXT_PUBLIC_PROXY_URL=your_proxy_url
# NEXT_PUBLIC_API_BASE_URL=http://localhost:8000

bun dev
```

The frontend will be available at [http://localhost:3000](http://localhost:3000).

## Backend

The backend is a FastAPI application providing authentication APIs.

### Features

- ✅ User registration and login
- ✅ JWT access tokens (30min TTL)
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

```bash
# App
APP_NAME=Anirohi API
DEBUG=true

# Database
DATABASE_URL=postgresql://ani_user:ani_password@postgres:5432/ani_db

# Security
SECRET_KEY=your-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=30

# CORS
ALLOWED_ORIGINS=http://localhost:3000
```

### Frontend (`frontend/.env.local`)

```bash
# Required
NEXT_PUBLIC_PROXY_URL=your_m3u8proxy_worker_url

# Optional
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
ALLOWED_ORIGINS=http://localhost:3000,https://anirohi.xyz
```

## Docker Compose Services

```yaml
services:
  postgres:    # PostgreSQL 16 database (port 5432)
  backend:     # FastAPI application (port 8000)
```

Start services:
```bash
docker-compose up -d      # Start in background
docker-compose logs -f    # View logs
docker-compose down       # Stop services
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

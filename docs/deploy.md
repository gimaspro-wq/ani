# Deployment Guide

This guide covers deploying the Anirohi application to production using Docker Compose.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Variables](#environment-variables)
- [Initial Deployment](#initial-deployment)
- [Database Management](#database-management)
- [Backup and Restore](#backup-and-restore)
- [Updating the Application](#updating-the-application)
- [Rollback Strategy](#rollback-strategy)
- [Monitoring and Health Checks](#monitoring-and-health-checks)
- [Security Considerations](#security-considerations)

## Prerequisites

- Docker Engine 24.0+ and Docker Compose v2
- Domain name (optional, for production HTTPS)
- Reverse proxy with SSL/TLS (e.g., nginx, Caddy, or Traefik)
- Minimum 1GB RAM, 10GB disk space
- PostgreSQL 16 (included in Docker Compose setup)

## Environment Variables

### Backend (`backend/.env`)

Create from the example file and customize for production:

```bash
cd backend
cp .env.example .env
```

#### Required Variables

```bash
# Security (CRITICAL: MUST CHANGE IN PRODUCTION!)
# Generate with: openssl rand -hex 32
SECRET_KEY=<your-generated-secret-key-here>
```

**How to generate a secure SECRET_KEY:**

```bash
openssl rand -hex 32
```

This generates 32 random bytes, represented as a 64-character hexadecimal string. Copy the output and set it as your `SECRET_KEY`.

#### Important Production Variables

```bash
# App
APP_NAME=Anirohi API
VERSION=1.0.0
ENV=production
DEBUG=false

# Database (update if using external PostgreSQL)
DATABASE_URL=postgresql+asyncpg://ani_user:ani_password@postgres:5432/ani_db

# JWT/Auth
JWT_ACCESS_TTL_MINUTES=15
REFRESH_TTL_DAYS=30
COOKIE_SECURE=true  # MUST be true in production with HTTPS

# CORS - Set to your frontend domain(s)
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

**Important Notes:**
- `COOKIE_SECURE=true` requires HTTPS (SSL/TLS)
- Update `ALLOWED_ORIGINS` to match your frontend domain(s)
- For `DATABASE_URL`, if using the Docker Compose PostgreSQL service, use `@postgres:5432` as the host
- If using an external database, update the connection string accordingly

#### Optional Variables

```bash
# Algorithm for JWT signing (default: HS256)
ALGORITHM=HS256
```

### Frontend (`frontend/.env.local`)

The frontend uses Next.js and most configuration is optional with sensible defaults.

```bash
cd frontend
cp .env.example .env.local
```

#### Optional Variables

```bash
# Override app URL if needed (defaults to window.location.origin in browser)
NEXT_PUBLIC_APP_URL=https://yourdomain.com

# Backend API URL (defaults to http://localhost:8000)
NEXT_PUBLIC_BACKEND_URL=https://api.yourdomain.com
```

**Note:** If your backend is on a different domain, you must set `NEXT_PUBLIC_BACKEND_URL`.

## Initial Deployment

### 1. Clone the Repository

```bash
git clone https://github.com/stalkerghostzone-lab/ani.git
cd ani
```

### 2. Configure Environment Variables

Follow the [Environment Variables](#environment-variables) section above to set up:
- `backend/.env` (required)
- `frontend/.env.local` (optional)

**Critical:** Generate and set a secure `SECRET_KEY` in `backend/.env`.

### 3. Start Services with Docker Compose

```bash
# Build and start all services (PostgreSQL + Backend)
docker compose up -d --build
```

This will:
1. Start PostgreSQL database
2. Build and start the backend API
3. Run database migrations automatically
4. Expose backend on port 8000

### 4. Verify Backend Health

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

### 5. Deploy Frontend

The frontend is a Next.js application that can be deployed separately to platforms like:
- Vercel (recommended)
- Netlify
- Cloudflare Pages
- Self-hosted with Docker

**Option A: Deploy to Vercel (Recommended)**

```bash
cd frontend
npm install -g vercel  # or use: npx vercel
vercel
```

Follow the prompts and set environment variables in the Vercel dashboard.

**Option B: Self-hosted with Docker**

Create a `frontend/Dockerfile`:

```dockerfile
FROM node:18-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:18-alpine
WORKDIR /app
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public
EXPOSE 3000
CMD ["node", "server.js"]
```

Update `frontend/next.config.ts` to enable standalone output:

```typescript
export default {
  output: 'standalone',
  // ... other config
}
```

Build and run:

```bash
docker build -t ani-frontend ./frontend
docker run -d -p 3000:3000 --name ani-frontend ani-frontend
```

```bash
docker build -t ani-frontend ./frontend
docker run -d -p 3000:3000 --name ani-frontend ani-frontend
```

### 6. Set Up Reverse Proxy (Production)

For production with HTTPS, use a reverse proxy like nginx or Caddy.

**Example nginx configuration:**

```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /docs {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
    }

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Database Management

### Running Migrations

Migrations run automatically when the backend container starts. To run manually:

```bash
# Using Docker
docker compose exec backend alembic upgrade head

# Or locally
cd backend
source venv/bin/activate
alembic upgrade head
```

### Creating New Migrations

```bash
# Using Docker
docker compose exec backend alembic revision --autogenerate -m "Description"

# Or locally
cd backend
source venv/bin/activate
alembic revision --autogenerate -m "Description"
```

### Checking Migration Status

```bash
# Using Docker
docker compose exec backend alembic current

# Show history
docker compose exec backend alembic history
```

### Reverting Migrations

```bash
# Downgrade one revision
docker compose exec backend alembic downgrade -1

# Downgrade to specific revision
docker compose exec backend alembic downgrade <revision_id>
```

## Backup and Restore

### PostgreSQL Backup

**Create a backup:**

```bash
# Backup to file
docker compose exec postgres pg_dump -U ani_user ani_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Or create compressed backup
docker compose exec postgres pg_dump -U ani_user ani_db | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz
```

**Automated daily backups (cron):**

```bash
# Add to crontab (crontab -e)
0 2 * * * cd /path/to/ani && docker compose exec -T postgres pg_dump -U ani_user ani_db | gzip > /path/to/backups/backup_$(date +\%Y\%m\%d).sql.gz
```

### PostgreSQL Restore

**Restore from backup:**

```bash
# Stop backend to prevent connections
docker compose stop backend

# Restore from SQL file
docker compose exec -T postgres psql -U ani_user ani_db < backup.sql

# Or from compressed backup
gunzip < backup.sql.gz | docker compose exec -T postgres psql -U ani_user ani_db

# Restart backend
docker compose start backend
```

**Restore to new database:**

```bash
# Create new database
docker compose exec postgres createdb -U ani_user ani_db_new

# Restore backup
docker compose exec -T postgres psql -U ani_user ani_db_new < backup.sql

# Update DATABASE_URL in backend/.env to point to ani_db_new
# Restart services
docker compose restart backend
```

### Backup Strategy Recommendations

1. **Daily automated backups** (keep last 7 days)
2. **Weekly backups** (keep last 4 weeks)
3. **Monthly backups** (keep last 12 months)
4. **Store backups off-site** (AWS S3, Google Cloud Storage, etc.)
5. **Test restore procedures regularly**

## Updating the Application

### 1. Pull Latest Changes

```bash
cd /path/to/ani
git fetch origin
git pull origin main
```

### 2. Update Backend

```bash
# Rebuild and restart backend
docker compose up -d --build backend

# Migrations run automatically on startup
# Verify backend health
curl http://localhost:8000/health
```

### 3. Update Frontend

For Vercel/Netlify: Push changes to your git repository (auto-deploys).

For self-hosted:
```bash
cd frontend
npm install
npm run build
# Restart your frontend server/container
```

### 4. Verify Deployment

- Check backend health: `curl http://localhost:8000/health`
- Check frontend loads correctly
- Test critical user flows (login, search, video playback)

## Rollback Strategy

### Quick Rollback (Basic)

If the new deployment has issues:

```bash
# 1. Stop current containers
docker compose down

# 2. Checkout previous version
git checkout <previous-commit-or-tag>

# 3. Restart services
docker compose up -d --build

# 4. If migrations were run, downgrade them
docker compose exec backend alembic downgrade -1
```

### Recommended: Tag-based Rollback

**Before deploying, tag the working version:**

```bash
git tag -a v1.0.0 -m "Stable release v1.0.0"
git push origin v1.0.0
```

**To rollback:**

```bash
# 1. List available tags
git tag -l

# 2. Checkout stable tag
git checkout v1.0.0

# 3. Rebuild and restart
docker compose down
docker compose up -d --build

# 4. Restore database backup if needed (see Backup section)
```

### Database Rollback

If migrations cause issues:

```bash
# 1. Check current migration
docker compose exec backend alembic current

# 2. View migration history
docker compose exec backend alembic history

# 3. Downgrade to previous revision
docker compose exec backend alembic downgrade <revision_id>

# Or restore from backup
docker compose stop backend
gunzip < backup_before_migration.sql.gz | docker compose exec -T postgres psql -U ani_user ani_db
docker compose start backend
```

### Rollback Checklist

- [ ] Create backup before deployment
- [ ] Tag stable releases in git
- [ ] Document migration revisions before upgrading
- [ ] Test rollback procedures in staging environment
- [ ] Have database backup ready before migrations
- [ ] Monitor application logs during and after rollback

## Monitoring and Health Checks

### Health Check Endpoint

The backend provides a health check endpoint:

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

### Container Health Monitoring

```bash
# Check container status
docker compose ps

# View logs
docker compose logs -f backend
docker compose logs -f postgres

# Check backend logs only (last 100 lines)
docker compose logs --tail=100 backend
```

### PostgreSQL Health Check

The postgres service includes a built-in health check. Verify it's healthy:

```bash
docker compose ps postgres
```

Should show status as "healthy".

### Setting Up Monitoring (Optional)

For production, consider:
- **Uptime monitoring:** UptimeRobot, Pingdom, or StatusCake
- **Log aggregation:** Logtail, Papertrail, or self-hosted ELK stack
- **Error tracking:** Sentry
- **Metrics:** Prometheus + Grafana

Example uptime monitor configuration:
- Monitor: `https://yourdomain.com/health`
- Interval: 5 minutes
- Alert if: Status code != 200 or response doesn't contain `"status": "healthy"`

## Security Considerations

### Before Production Deployment

1. **Generate secure SECRET_KEY:**
   ```bash
   openssl rand -hex 32
   ```

2. **Set environment variables:**
   - `ENV=production`
   - `DEBUG=false`
   - `COOKIE_SECURE=true` (requires HTTPS)

3. **Enable HTTPS:**
   - Use reverse proxy (nginx, Caddy) with SSL/TLS certificates
   - Use Let's Encrypt for free certificates

4. **Update CORS settings:**
   - Set `ALLOWED_ORIGINS` to your actual frontend domain(s)
   - No wildcards (`*`) in production

5. **Secure PostgreSQL:**
   - Change default database password in `docker-compose.yml`
   - Don't expose PostgreSQL port (5432) to the internet
   - Use strong passwords (min 16 characters)

6. **Network security:**
   - Place services behind firewall
   - Only expose necessary ports (80, 443)
   - Use Docker networks to isolate services

7. **Regular updates:**
   - Keep dependencies up to date
   - Monitor security advisories
   - Apply security patches promptly

### Production Checklist

- [ ] `SECRET_KEY` is unique and secure (32+ characters)
- [ ] `ENV=production` and `DEBUG=false`
- [ ] `COOKIE_SECURE=true` with HTTPS enabled
- [ ] `ALLOWED_ORIGINS` set to actual domain(s), no wildcards
- [ ] PostgreSQL password changed from defaults
- [ ] Database port (5432) not exposed to internet
- [ ] HTTPS enabled with valid SSL certificate
- [ ] Regular backups configured and tested
- [ ] Monitoring and alerting set up
- [ ] Logs are being collected and reviewed
- [ ] API documentation (`/docs`) disabled or protected in production

## Troubleshooting

### Backend won't start

```bash
# Check logs
docker compose logs backend

# Common issues:
# 1. SECRET_KEY not set - check backend/.env
# 2. Database connection failed - verify DATABASE_URL and postgres container is running
# 3. Migration failed - check alembic logs, may need to manually fix
```

### Database connection errors

```bash
# Verify postgres is running
docker compose ps postgres

# Check postgres logs
docker compose logs postgres

# Test database connection
docker compose exec postgres psql -U ani_user -d ani_db -c "SELECT 1;"
```

### Frontend can't connect to backend

1. Check `NEXT_PUBLIC_BACKEND_URL` in `frontend/.env.local`
2. Verify CORS settings in `backend/.env` include frontend domain
3. Check network connectivity between frontend and backend
4. Verify backend is accessible: `curl http://backend-url/health`

### Cookies not working

Ensure:
- `COOKIE_SECURE=false` for development (HTTP)
- `COOKIE_SECURE=true` for production with HTTPS
- Frontend and backend are on same domain or CORS is properly configured
- Browser allows third-party cookies (if on different domains)

## Ports Reference

- **3000**: Frontend (Next.js)
- **8000**: Backend API (FastAPI)
- **5432**: PostgreSQL (internal, should not be exposed publicly)

## Additional Resources

- [Backend Setup Guide](../backend/docs/setup.md)
- [Backend Architecture](../backend/docs/architecture.md)
- [Authentication Guide](../backend/docs/auth.md)
- [Frontend Platform Guide](platform.md)
- [Frontend Architecture](architecture.md)
- [Features Guide](features.md)

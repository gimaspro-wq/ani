# Deployment Guide

## Prerequisites

- Docker and Docker Compose
- PostgreSQL 16+
- Redis 7+
- Domain with SSL/TLS certificate
- 2GB+ RAM recommended
- 2+ CPU cores recommended

## Deployment Options

### 1. Docker Compose (Recommended for Small Scale)

```bash
# Clone repository
git clone https://github.com/yourusername/ani.git
cd ani

# Configure backend
cd backend
cp .env.example .env

# Edit .env with production values
# CRITICAL: Set SECRET_KEY, DATABASE_URL, and other required vars

# Return to root
cd ..

# Start services
docker compose up -d --build

# Check logs
docker compose logs -f backend

# Verify health
curl http://localhost:8000/health
```

### 2. Kubernetes (Recommended for Scale)

See `k8s/` directory for manifests (to be created).

### 3. Cloud Platforms

#### AWS ECS/Fargate

1. Push Docker image to ECR
2. Create ECS task definition
3. Deploy as Fargate service
4. Use RDS for PostgreSQL
5. Use ElastiCache for Redis
6. Use ALB for load balancing

#### Google Cloud Run

```bash
# Build and push
gcloud builds submit --tag gcr.io/PROJECT_ID/anirohi-backend

# Deploy
gcloud run deploy anirohi-backend \
  --image gcr.io/PROJECT_ID/anirohi-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars ENV=production,DEBUG=false \
  --set-secrets SECRET_KEY=projects/PROJECT_ID/secrets/secret-key:latest
```

## Production Configuration

### 1. Generate Secrets

```bash
# Generate SECRET_KEY
openssl rand -hex 32

# Generate database password
openssl rand -base64 32
```

### 2. Configure Environment

Create `.env` file with production values:

```bash
# Application
APP_NAME=Anirohi API
VERSION=1.0.0
DEBUG=false
ENV=production

# Database
DATABASE_URL=postgresql+asyncpg://ani_user:STRONG_PASSWORD@db.example.com:5432/ani_db

# Security
SECRET_KEY=<your-64-char-hex-from-openssl-rand>
ALGORITHM=HS256
JWT_ACCESS_TTL_MINUTES=15
REFRESH_TTL_DAYS=30
COOKIE_SECURE=true

# CORS - Your production domains only
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Redis
REDIS_URL=redis://:REDIS_PASSWORD@redis.example.com:6379/0
REDIS_MAX_CONNECTIONS=10

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60

# Observability
METRICS_ENABLED=true
TRACING_ENABLED=false
OTEL_SERVICE_NAME=anirohi-api
OTEL_EXPORTER_OTLP_ENDPOINT=
```

### 3. Database Setup

```bash
# Create database
psql -h db.example.com -U postgres
CREATE DATABASE ani_db;
CREATE USER ani_user WITH ENCRYPTED PASSWORD 'STRONG_PASSWORD';
GRANT ALL PRIVILEGES ON DATABASE ani_db TO ani_user;

# Run migrations
docker compose run --rm backend alembic upgrade head

# Verify
docker compose run --rm backend alembic current
```

### 4. SSL/TLS Setup

#### Using Let's Encrypt with Nginx

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /metrics {
        deny all;  # Protect metrics endpoint
    }
}
```

Generate certificate:
```bash
certbot --nginx -d api.yourdomain.com
```

## Scaling

### Horizontal Scaling

The application is stateless and can be scaled horizontally:

```yaml
# docker-compose.yml
services:
  backend:
    deploy:
      replicas: 3
    ...
```

Or with Kubernetes:
```yaml
spec:
  replicas: 3
```

### Load Balancing

Use Nginx, HAProxy, or cloud load balancers:

```nginx
upstream backend {
    least_conn;
    server backend1:8000;
    server backend2:8000;
    server backend3:8000;
}

server {
    location / {
        proxy_pass http://backend;
    }
}
```

### Database Connection Pooling

Configure in `DATABASE_URL`:
```bash
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db?min_size=5&max_size=20
```

### Redis Clustering

For high availability, use Redis Cluster or Sentinel:
```bash
REDIS_URL=redis://sentinel1:26379,sentinel2:26379,sentinel3:26379?master_name=mymaster
```

## Monitoring Setup

### 1. Prometheus

Create `prometheus.yml`:
```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'anirohi-backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'
```

Start Prometheus:
```bash
docker run -d \
  -p 9090:9090 \
  -v $(pwd)/prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus
```

### 2. Grafana

```bash
docker run -d \
  -p 3000:3000 \
  -e GF_SECURITY_ADMIN_PASSWORD=admin \
  grafana/grafana
```

Import dashboards:
- FastAPI metrics dashboard
- PostgreSQL dashboard
- Redis dashboard

### 3. Log Aggregation

#### ELK Stack

```yaml
# docker-compose.yml
services:
  elasticsearch:
    image: elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
    ports:
      - 9200:9200

  logstash:
    image: logstash:8.11.0
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf

  kibana:
    image: kibana:8.11.0
    ports:
      - 5601:5601
```

Configure backend to send logs to Logstash.

#### Loki + Grafana

```yaml
services:
  loki:
    image: grafana/loki:latest
    ports:
      - 3100:3100

  promtail:
    image: grafana/promtail:latest
    volumes:
      - /var/log:/var/log
      - ./promtail.yml:/etc/promtail/config.yml
```

## Backup Strategy

### Database Backup

```bash
# Daily backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="ani_db_$DATE.sql.gz"

pg_dump -h db.example.com -U ani_user ani_db | gzip > /backups/$BACKUP_FILE

# Upload to S3
aws s3 cp /backups/$BACKUP_FILE s3://your-backup-bucket/

# Keep last 30 days
find /backups -name "ani_db_*.sql.gz" -mtime +30 -delete
```

### Redis Backup

```bash
# Configure Redis persistence
redis-cli CONFIG SET save "900 1 300 10 60 10000"

# Or in redis.conf
save 900 1
save 300 10
save 60 10000
```

## Disaster Recovery

### Recovery Steps

1. **Deploy new infrastructure**
```bash
# Use Infrastructure as Code
terraform apply
# or
docker compose up -d
```

2. **Restore database**
```bash
# Download latest backup
aws s3 cp s3://your-backup-bucket/latest.sql.gz /tmp/

# Restore
gunzip < /tmp/latest.sql.gz | psql -h new-db.example.com -U ani_user ani_db
```

3. **Verify application**
```bash
# Check health
curl https://api.yourdomain.com/health

# Check metrics
curl https://api.yourdomain.com/metrics

# Test authentication
curl -X POST https://api.yourdomain.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test"}'
```

## Rollback Procedure

### Application Rollback

```bash
# Using Docker
docker compose down
git checkout <previous-version-tag>
docker compose up -d --build

# Using Kubernetes
kubectl rollout undo deployment/anirohi-backend
```

### Database Rollback

```bash
# Downgrade one migration
docker compose run --rm backend alembic downgrade -1

# Downgrade to specific revision
docker compose run --rm backend alembic downgrade <revision>
```

## Health Checks

### Application Health

```bash
# Liveness check
curl http://localhost:8000/health

# Metrics check
curl http://localhost:8000/metrics
```

### Database Health

```bash
docker compose run --rm backend python -c "
from app.db.database import engine
import asyncio
async def check():
    async with engine.begin() as conn:
        await conn.execute('SELECT 1')
    print('Database OK')
asyncio.run(check())
"
```

### Redis Health

```bash
redis-cli -h redis.example.com ping
```

## Performance Tuning

### Uvicorn Workers

```bash
# Run with multiple workers
uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4
```

### Database Optimization

```sql
-- Add indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_refresh_tokens_user_id ON refresh_tokens(user_id);
CREATE INDEX idx_library_items_user_id ON user_library_items(user_id);

-- Vacuum regularly
VACUUM ANALYZE;
```

### Redis Optimization

```redis
# Max memory policy
maxmemory 2gb
maxmemory-policy allkeys-lru

# Persistence
save 900 1
save 300 10
```

## Security Hardening

### Firewall Rules

```bash
# Allow only necessary ports
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp  # SSH
ufw allow 443/tcp # HTTPS
ufw allow from 10.0.0.0/8 to any port 8000  # Internal backend
ufw enable
```

### Security Scanning

```bash
# Scan Docker image
trivy image anirohi-backend:latest

# Scan dependencies
pip-audit

# SAST
bandit -r app/
```

## Troubleshooting

### Application Won't Start

1. Check logs: `docker compose logs backend`
2. Verify env vars: `docker compose config`
3. Check database connectivity
4. Verify migrations: `alembic current`

### High Memory Usage

1. Check worker count
2. Review database connection pool size
3. Monitor Redis memory usage
4. Check for memory leaks with profiler

### Slow Responses

1. Check database query performance
2. Review Redis cache hit rate
3. Monitor Prometheus metrics
4. Check network latency

### Database Connection Issues

1. Verify DATABASE_URL
2. Check connection limits
3. Review firewall rules
4. Test connectivity: `pg_isready -h host`

## Support

For deployment issues:
- GitHub Issues: [repository URL]
- Documentation: `/backend/docs/`
- Email: support@yourdomain.com

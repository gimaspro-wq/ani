# Operations Guide (Phase 7)

This document describes the operational endpoints and signals available in staging/early production.

## Health & Readiness

- **GET `/health`**  
  - Liveness probe. Returns `200` when the process is alive. No external checks.

- **GET `/ready`**  
  - Readiness probe. Returns `200` only when both Postgres and Redis are reachable.  
  - Returns `503` if either dependency is unavailable.  
  - Response shape:
    ```json
    {
      "status": "ready|not_ready",
      "checks": { "database": true|false, "redis": true|false }
    }
    ```

**If `/ready` returns 503**:
1. Verify Postgres connectivity (`DATABASE_URL`) and that the database is accepting connections.
2. Verify Redis connectivity (`REDIS_URL`) and that the instance is reachable.
3. Retry `/ready` after fixing the failing dependency; the endpoint has no caching.

## Metrics

- **GET `/metrics`** (enabled when `METRICS_ENABLED=true`)  
  - Exposes Prometheus text-format metrics:
    - `process_uptime_seconds` (gauge)
    - `http_requests_total{method, path}` (counter)
    - `http_request_duration_seconds{method, path}` (histogram)
    - `db_connection_errors_total` (counter)
    - `redis_connection_errors_total` (counter)

## Logging

- Structured JSON logs with fields: `timestamp`, `level`, `service`, `request_id`, `trace_id`, `method`, `path`, `status_code`, `duration_ms`.
- 5xx responses are logged at **ERROR** level.
- Stack traces are emitted only when `DEBUG=true`.
- No request/response payloads or sensitive values are logged.

## Startup Safety

- On startup the service logs environment, version, and commit hash (if provided via `GIT_COMMIT`, `COMMIT_SHA`, or `SOURCE_VERSION`).
- Required environment variables: `DATABASE_URL`, `SECRET_KEY`, `INTERNAL_TOKEN`, `REDIS_URL`. Missing values cause the process to exit during startup.

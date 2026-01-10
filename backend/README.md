# Backend Service

### Local Development
- Required environment variables: `DATABASE_URL`, `SECRET_KEY`, `INTERNAL_TOKEN`, `REDIS_URL`
- The backend will not start if any required variable is missing.

### Deploy to Render
- Deploy the backend as a Web Service.
- Set all required environment variables (`DATABASE_URL`, `SECRET_KEY`, `INTERNAL_TOKEN`, `REDIS_URL`) in the Render dashboard before deploying.
- Startup will fail fast and list any missing variables.

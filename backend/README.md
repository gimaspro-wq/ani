# Backend Service

### Local Development
- Backend fails fast if required environment variables are missing.
- Required variables are derived from actual usage in `app/core/config.py`.

### Deploy to Render
- Deploy the backend as a Web Service.
- Set required environment variables in the Render dashboard; they are derived from `app/core/config.py`.
- Startup will fail fast and list any missing variables.

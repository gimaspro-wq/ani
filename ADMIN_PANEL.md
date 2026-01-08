# Admin Panel Documentation

## Overview

The admin panel is a web-based interface for managing anime content in the Anirohi platform. It provides full control over anime, episodes, and video sources, with priority over the external parser.

## Features

- 🔐 **Secure Authentication**: JWT-based admin authentication
- 📊 **Dashboard**: Overview of site statistics and recent activity
- 🎬 **Anime Management**: Create, edit, and manage anime entries
- 📺 **Episode Management**: Manage episodes for each anime
- ▶️ **Video Source Management**: Handle multiple video sources per episode
- 🔒 **Admin Override**: Manual changes take priority over parser updates
- 📝 **Audit Logging**: All admin actions are logged for accountability

## Architecture

### Backend (FastAPI)

**Models:**
- `AdminUser`: Admin authentication and user management
- `AuditLog`: Tracks all admin actions
- `Anime`, `Episode`, `VideoSource`: Core content models with `admin_modified` flag

**API Endpoints:**
- `POST /api/v1/admin/login`: Admin authentication
- `GET /api/v1/admin/me`: Get current admin user
- `GET /api/v1/admin/dashboard`: Dashboard statistics
- `GET /api/v1/admin/anime`: List anime with filters
- `GET /api/v1/admin/anime/{id}`: Get anime details
- `PATCH /api/v1/admin/anime/{id}`: Update anime
- `GET /api/v1/admin/anime/{id}/episodes`: List episodes
- `POST /api/v1/admin/episodes`: Create episode
- `PATCH /api/v1/admin/episodes/{id}`: Update episode
- `GET /api/v1/admin/episodes/{id}/video`: List video sources
- `POST /api/v1/admin/video`: Create video source
- `PATCH /api/v1/admin/video/{id}`: Update video source
- `DELETE /api/v1/admin/video/{id}`: Delete video source

### Frontend (Next.js)

**Pages:**
- `/admin/login`: Admin login page
- `/admin/dashboard`: Statistics and overview
- `/admin/anime`: Anime list with search and filters
- `/admin/anime/[id]`: Edit anime and manage episodes

**Components:**
- `AdminAuthProvider`: Authentication context
- `RequireAuth`: Protected route wrapper
- `AdminNav`: Navigation component

## Setup Instructions

### 1. Backend Setup

#### Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

#### Configure Environment
Copy `.env.example` to `.env` and set the following variables:
```bash
# Admin Panel Configuration
ADMIN_EMAIL=admin@example.com
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-secure-password-here
```

#### Run Migrations
```bash
cd backend
alembic upgrade head
```

#### Create First Admin User
```bash
cd backend
export ADMIN_EMAIL=admin@example.com
export ADMIN_USERNAME=admin
export ADMIN_PASSWORD=YourSecurePassword123
python scripts/create_admin.py
```

**Output:**
```
✓ Admin user created successfully!
  Email: admin@example.com
  Username: admin

You can now login to the admin panel with these credentials.
```

#### Start Backend
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Setup

#### Install Dependencies
```bash
cd frontend
npm install
```

#### Configure Environment
Create `.env.local` file (optional):
```bash
# Backend API URL (defaults to http://localhost:8000)
NEXT_PUBLIC_API_URL=http://localhost:8000
```

#### Start Frontend
```bash
cd frontend
npm run dev
```

The frontend will be available at http://localhost:3000

### 3. Access Admin Panel

1. Navigate to http://localhost:3000/admin
2. You'll be redirected to the login page
3. Enter your admin credentials:
   - Email: admin@example.com
   - Password: YourSecurePassword123
4. After successful login, you'll be redirected to the dashboard

## Usage Guide

### Dashboard

The dashboard provides an overview of:
- Total anime count
- Active/inactive anime
- Total episodes and video sources
- Recent anime and episodes

### Managing Anime

#### List Anime
- Navigate to "Anime" from the nav menu
- Use the search bar to filter anime by title or slug
- Click "Edit" to modify an anime entry
- Toggle active/inactive status directly from the list

#### Edit Anime
- Update title, description, year, and status
- Toggle active/inactive status
- Changes are saved with the "Save Changes" button
- The `admin_modified` flag is automatically set

#### View Episodes
- Episodes are listed at the bottom of the anime edit page
- Toggle active/inactive status for each episode
- Episode count is displayed

### Admin Override Mechanism

When an admin modifies a record (anime, episode, or video source):
1. The `admin_modified` flag is set to `true`
2. Parser updates will **NOT** overwrite these fields
3. The `is_active` flag is always protected from parser updates
4. Admin changes take absolute priority

### Audit Logging

All admin actions are logged to the `audit_logs` table:
- Action type (create, update, delete)
- Resource type and ID
- Changes made (JSON format)
- Admin user who performed the action
- Timestamp

## API Authentication

Admin API endpoints require a JWT token with the `admin` claim:

```bash
# Login
curl -X POST http://localhost:8000/api/v1/admin/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "password"}'

# Response
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}

# Use token in subsequent requests
curl http://localhost:8000/api/v1/admin/dashboard \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."
```

## Security Considerations

### Production Deployment

1. **Use Strong Passwords**: Admin passwords should be at least 12 characters
2. **HTTPS Only**: Enable `COOKIE_SECURE=true` in production
3. **Secret Keys**: Generate strong secret keys:
   ```bash
   openssl rand -hex 32
   ```
4. **Environment Variables**: Never commit `.env` files to version control
5. **Access Control**: Limit admin panel access by IP if possible
6. **Regular Audits**: Review audit logs regularly

### Password Requirements

- Minimum 8 characters (enforced by backend)
- Recommended: 12+ characters with mixed case, numbers, and symbols

### Token Security

- Access tokens expire after 15 minutes (configurable)
- Tokens are stored in localStorage (frontend)
- Use HTTPS in production to prevent token interception

## Troubleshooting

### "Failed to connect to API"

**Solution:** Ensure backend is running on http://localhost:8000
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

### "Invalid credentials"

**Solution:** Verify admin user exists and password is correct
```bash
cd backend
python scripts/create_admin.py
```

### "Database migrations not applied"

**Solution:** Run migrations
```bash
cd backend
alembic upgrade head
```

### Parser overwrites admin changes

**Issue:** The `admin_modified` flag may not be set correctly

**Solution:** 
1. Check that admin updates go through the admin API endpoints
2. Verify the internal.py parser endpoints check `admin_modified` flag
3. Review audit logs to confirm admin changes were saved

## Development

### Adding New Admin Features

1. **Backend:**
   - Add endpoint to `backend/app/api/v1/admin.py`
   - Add schema to `backend/app/schemas/admin.py`
   - Update `backend/app/services/admin.py` if needed
   - Add audit logging with `log_admin_action()`

2. **Frontend:**
   - Add API method to `frontend/src/lib/admin-api.ts`
   - Create/update page in `frontend/src/app/admin/`
   - Use `RequireAuth` wrapper for protected pages
   - Use `useAdminAuth()` hook for admin context

### Running Tests

```bash
cd backend
pytest -v tests/
```

## API Reference

### Admin Authentication

#### POST /api/v1/admin/login
Login with admin credentials.

**Request:**
```json
{
  "email": "admin@example.com",
  "password": "password"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

### Dashboard

#### GET /api/v1/admin/dashboard
Get dashboard statistics.

**Response:**
```json
{
  "total_anime": 150,
  "active_anime": 140,
  "inactive_anime": 10,
  "total_episodes": 2500,
  "total_video_sources": 5000,
  "recent_anime": [...],
  "recent_episodes": [...]
}
```

### Anime Management

#### GET /api/v1/admin/anime
List anime with pagination and filters.

**Query Parameters:**
- `page`: Page number (default: 1)
- `per_page`: Items per page (default: 20, max: 100)
- `search`: Search by title or slug
- `is_active`: Filter by active status (true/false)
- `source_name`: Filter by source

#### PATCH /api/v1/admin/anime/{id}
Update anime details.

**Request:**
```json
{
  "title": "New Title",
  "description": "Updated description",
  "year": 2024,
  "status": "ongoing",
  "is_active": true
}
```

### Episode Management

#### POST /api/v1/admin/episodes
Create a new episode manually.

**Request:**
```json
{
  "anime_id": "uuid-here",
  "number": 12,
  "title": "Episode 12",
  "source_episode_id": "ep-12",
  "is_active": true
}
```

### Video Source Management

#### POST /api/v1/admin/video
Create a new video source.

**Request:**
```json
{
  "episode_id": "uuid-here",
  "type": "iframe",
  "url": "https://example.com/player",
  "source_name": "provider-name",
  "priority": 10,
  "is_active": true
}
```

## Support

For issues or questions:
1. Check this documentation
2. Review audit logs for error details
3. Check backend logs: `docker compose logs -f backend`
4. Open an issue on GitHub

## License

This project is licensed under the MIT License.

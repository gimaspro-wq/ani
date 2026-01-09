# Admin Panel Quick Start Guide

> Admin-only quick start. Skip this for public frontend work.

This guide will help you get the admin panel up and running in just a few minutes.

## Prerequisites

- Backend running (FastAPI)
- Frontend running (Next.js)
- PostgreSQL database
- Environment configured

## Step 1: Run Database Migrations

```bash
cd backend
alembic upgrade head
```

This creates the admin_users and audit_logs tables.

## Step 2: Create Your First Admin User

```bash
cd backend

# Set your admin credentials
export ADMIN_EMAIL=admin@example.com
export ADMIN_USERNAME=admin
export ADMIN_PASSWORD=YourSecurePassword123

# Run the creation script
python scripts/create_admin.py
```

You should see:
```
✓ Admin user created successfully!
  Email: admin@example.com
  Username: admin

You can now login to the admin panel with these credentials.
```

## Step 3: Access the Admin Panel

1. Open your browser and navigate to: http://localhost:3000/admin

2. You'll be redirected to the login page

3. Enter your credentials:
   - **Email:** admin@example.com
   - **Password:** YourSecurePassword123

4. Click "Sign in"

5. You'll be redirected to the dashboard! 🎉

## What You Can Do

### Dashboard
- View total anime count
- See active/inactive anime stats
- Check total episodes and video sources
- View recent anime and episodes

### Manage Anime
1. Click "Anime" in the navigation
2. Use the search bar to find specific anime
3. Click "Edit" to modify an anime entry
4. Toggle active/inactive status
5. Update title, description, year, status
6. Click "Save Changes"

### Manage Episodes
1. Edit an anime (see above)
2. Scroll down to see the episodes list
3. Toggle active/inactive for individual episodes
4. Episode count is shown at the top

### Admin Override
When you modify content through the admin panel:
- The record is marked as "admin modified"
- The parser will NOT overwrite your changes
- Your changes always have priority
- All actions are logged in the audit log

## Troubleshooting

### Can't login?
- Verify the admin user was created: Check backend logs
- Make sure backend is running on port 8000
- Check browser console for errors

### Can't see any anime?
- Import some anime data using the parser first
- Or wait for the parser to populate data automatically

### Parser overwrites my changes?
- Check that you're using the admin panel endpoints
- Verify the `admin_modified` flag is set to true in the database
- Review the parser logs to see if it's respecting the flag

## Next Steps

- Read the full [Admin Panel Documentation](ADMIN_PANEL.md)
- Review [API Reference](ADMIN_PANEL.md#api-reference)
- Check [Security Considerations](ADMIN_PANEL.md#security-considerations)

## Need Help?

- Check the [troubleshooting section](ADMIN_PANEL.md#troubleshooting)
- Review backend logs: `docker compose logs -f backend`
- Check frontend console for errors
- Open an issue on GitHub

## Production Deployment

Before deploying to production:

1. Use strong passwords (12+ characters)
2. Set `COOKIE_SECURE=true` in .env
3. Generate secure secret keys: `openssl rand -hex 32`
4. Enable HTTPS
5. Review security considerations in full documentation

---

**Congratulations!** You now have a fully functional admin panel! 🚀

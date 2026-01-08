# Phase 2: UI Integration Testing Guide

This document explains how to test the Phase 2 features implemented in this PR.

## Prerequisites

- Backend running on `http://localhost:8000`
- Frontend running on `http://localhost:3000`
- User account created (for authenticated features)

## Features to Test

### 1. Title Page Enhancements

**Location**: `/anime/[id]` (e.g., `/anime/one-piece-100`)

**Features**:
- Add to Library button with status dropdown
- Favorite toggle button  
- Episode list with progress indicators
- Existing "Save" button still works

**Test Steps**:

1. **Guest User**:
   - Navigate to any anime title page
   - Click "Add to Library" → shows login required message
   - Click "Add to Favorites" → shows login required message
   - Episode list displays correctly
   - Progress bars show for episodes you've watched (from localStorage)

2. **Authenticated User**:
   - Login to your account
   - Navigate to any anime title page
   - Click "Add to Library" → dropdown appears
   - Select "Watching" → toast shows "Added to watching"
   - Click again → dropdown shows current status highlighted
   - Change to "Completed" → status updates
   - Click "Remove from Library" → item removed
   - Click "Add to Favorites" → heart icon turns red
   - Click again → removed from favorites
   - Watch an episode → return to title page → progress bar shows on that episode

### 2. Continue Watching Section

**Location**: `/home` (home page)

**Features**:
- Shows recently watched anime
- Progress bars on cards
- Episode number badges
- Works for both guests and authenticated users

**Test Steps**:

1. **Empty State**:
   - Clear localStorage: `localStorage.clear()`
   - Refresh page
   - Section shows "Start watching anime" message

2. **Guest User with Progress**:
   - Watch any episode for at least 5 seconds
   - Navigate to home page
   - Card appears in Continue Watching section
   - Progress bar shows watch percentage
   - Episode badge shows correct number
   - Click card → goes to correct episode

3. **Authenticated User**:
   - Login and watch episodes
   - Navigate to home page
   - Continue Watching shows server-synced data
   - Most recently watched appear first

### 3. My Library Page

**Location**: `/library`

**Features**:
- Tab navigation by status
- Favorites filter
- Grid of anime cards with badges
- Empty states

**Test Steps**:

1. **Not Logged In**:
   - Navigate to `/library`
   - Shows "Login Required" message

2. **Empty Library**:
   - Login with new account
   - Navigate to `/library`
   - Shows "No anime in your library" message
   - "Browse Anime" button links to `/browse`

3. **With Library Items**:
   - Add anime to library from title pages
   - Navigate to `/library`
   - Default "All" tab shows all items
   - Click "Watching" → filters to watching items
   - Click "Planned" → filters to planned items
   - Toggle "Favorites only" → shows only favorited items
   - Status badge displays on each card (watching/planned/completed/dropped)
   - Favorite indicator (red heart) shows on favorited items
   - Click card → navigates to anime title page

### 4. Login Merge Flow

**Features**:
- Merges local progress and library to server on login
- Toast notifications for feedback
- Non-blocking background sync

**Test Steps**:

1. **Setup Local Data**:
   - Logout or use incognito mode
   - Watch several episodes as guest
   - Save some series using the "Save" button
   - Verify localStorage has data:
     ```javascript
     console.log(localStorage.getItem('anirohi-watch-progress'));
     console.log(localStorage.getItem('anirohi-saved-series'));
     ```

2. **Trigger Merge**:
   - Login to your account
   - If merge functionality is integrated with login:
     - Toast appears: "Syncing your data..."
     - After completion: "Synced X progress items and Y library items"
   - If using manual trigger (in console):
     ```javascript
     import { useLoginMerge } from '@/hooks/use-login-merge';
     const { triggerMerge } = useLoginMerge();
     triggerMerge();
     ```

3. **Verify Merge**:
   - Navigate to `/library` → see saved series added
   - Navigate to home → see progress in Continue Watching
   - Check title pages → progress bars show on watched episodes
   - Open Network tab → see PUT requests to `/api/v1/me/progress` and `/api/v1/me/library`

4. **Error Handling**:
   - Trigger merge without authentication → console warning
   - Trigger merge with no local data → console log "No local data to merge"
   - Simulate server error → toast shows partial sync message

## Docker Compose Testing

### Start Services

```bash
# From repository root
docker compose -f docker-compose.yml up -d

# Wait for services to be ready
docker compose logs -f
```

### Access Points

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### Create Test User

```bash
# Using curl
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "testpass123"}'

# Returns: {"access_token": "...", "token_type": "bearer"}
```

### Test API Endpoints

```bash
# Get token (save it as TOKEN variable)
TOKEN="your_access_token_here"

# Add to library
curl -X PUT http://localhost:8000/api/v1/me/library/one-piece-100 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "watching", "is_favorite": true}'

# Get library
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/me/library

# Update progress
curl -X PUT http://localhost:8000/api/v1/me/progress/one-piece-100-ep-1 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title_id": "one-piece-100", "position_seconds": 120.5, "duration_seconds": 1440.0}'

# Get progress
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/me/progress

# Get history
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/me/history
```

## Known Limitations

1. **Library Page**: Shows title_id instead of anime name/poster (would need to fetch from RPC)
2. **Continue Watching**: Server history doesn't include progress data (shows items but no progress bars for authenticated users)
3. **Episode IDs**: Format assumes `{title_id}-ep-{number}` - may differ from actual RPC format

## Troubleshooting

### "Please login to use this feature"
- Check localStorage: `localStorage.getItem('access_token')`
- Check backend auth: `curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/users/me`

### Progress not saving
- Check browser console for errors
- Verify backend is running: `curl http://localhost:8000/health`
- Check TanStack Query devtools for failed mutations

### Library items not showing
- Check authentication token is valid
- Verify API response: `curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/me/library`
- Check TanStack Query devtools for query state

### Build errors
- Clear build cache: `rm -rf .next`
- Reinstall dependencies: `npm install`
- Check Node version: `node --version` (should be 18+)

## Manual Testing Checklist

- [ ] Title page: Add to library (all statuses)
- [ ] Title page: Toggle favorite
- [ ] Title page: Episode list displays
- [ ] Title page: Progress bars show
- [ ] Title page: Filler badges show
- [ ] Home page: Continue watching section
- [ ] Home page: Progress bars on cards
- [ ] Home page: Empty state
- [ ] Library page: Login gate
- [ ] Library page: Tab navigation
- [ ] Library page: Favorites filter
- [ ] Library page: Empty states
- [ ] Library page: Status badges
- [ ] Library page: Favorite indicators
- [ ] Navbar: Library link works
- [ ] Guest user: Local storage fallback
- [ ] Authenticated: Server sync
- [ ] Login merge: Toast notifications
- [ ] Login merge: Data synced to server
- [ ] Responsive: Mobile view
- [ ] Responsive: Tablet view
- [ ] Responsive: Desktop view

## Performance Testing

- Library page with 100+ items loads in <2s
- Episode list with 1000+ episodes loads in <2s
- Continue watching section with 10 items loads instantly
- No memory leaks after 10 minutes of navigation
- TanStack Query cache works (no duplicate requests)

## Accessibility Testing

- [ ] Keyboard navigation works
- [ ] Screen reader compatible
- [ ] ARIA labels present
- [ ] Focus indicators visible
- [ ] Color contrast meets WCAG AA

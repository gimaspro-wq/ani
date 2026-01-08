# Phase 2: UI Integration for Library/Progress/History

> **Status**: Planned (to be implemented after Phase 1 merge)  
> **Base Branch**: `main` (after PR #3 is merged)  
> **Prerequisites**: Phase 1 backend infrastructure, hooks, and API client

## Overview

Phase 2 focuses on **UI integration** of the library management, progress tracking, and watch history features implemented in Phase 1. This phase adds user-facing components and pages without modifying the video player, proxy, or RPC data source.

## Scope

### ✅ In Scope
- Rich title page enhancements
- Continue Watching section
- My Library page
- Login merge flow UI
- Progress indicators and library controls

### ❌ Out of Scope
- Video player modifications
- `/api/proxy` changes
- `/rpc` data source changes
- Advanced search page (deferred to Phase 3)
- Enhanced command palette (deferred to Phase 3)
- Client-side search indexing (deferred to Phase 3)

## Technical Constraints

### Route Information
- **Title page route**: `frontend/src/app/anime/[id]/page.tsx`
- **`title_id`**: String slug format (e.g., `jack-of-all-trades-party-of-none-20333`)
- **`episode_id`**: String format (as received from `/rpc`)

### Library Status Values
- **Allowed statuses**: `watching`, `planned`, `completed`, `dropped`
- **Additional flag**: `favorite` (boolean)
- **Not allowed**: `on_hold` status

### Technology Stack
- Next.js 16 (App Router)
- React Server Components + Client Components
- TanStack Query (already configured in Phase 1)
- Tailwind CSS + shadcn/ui components
- TypeScript

## Acceptance Criteria

### 1. Rich Title Page (`/anime/[id]`)

**Required Features**:
- [ ] "Add to Library" button with status dropdown
  - Options: watching, planned, completed, dropped
  - Visual indication of current status
  - Persists to server (authenticated) or localStorage (guest)
  
- [ ] "Favorite" toggle button
  - Heart icon with active/inactive states
  - Syncs with library item
  
- [ ] Episode list with progress indicators
  - Show watch progress for each episode (if available)
  - Visual progress bar or percentage
  - "Continue watching" badge on last watched episode
  
- [ ] Season/Arc grouping (best-effort)
  - Group episodes by season if data available
  - Fallback to simple numbered list
  - Collapsible sections for better UX

**Implementation Notes**:
- Use `useLibrary()` hook for library status
- Use `useServerProgress()` hook for episode progress
- Handle both authenticated and guest user states
- Show loading states during API calls

### 2. Continue Watching Section

**Required Features**:
- [ ] Display section on home page (or logical location)
- [ ] Show anime cards with:
  - Thumbnail/poster image
  - Title
  - Episode progress (e.g., "Ep 5 of 12")
  - Progress bar
  - "Continue" button/link
  
- [ ] Data source logic:
  - **Authenticated users**: Fetch from `GET /api/v1/me/history` + `GET /api/v1/me/progress`
  - **Guest users**: Read from localStorage (existing hooks)
  
- [ ] Sort by most recent watch time
- [ ] Limit to 6-10 items
- [ ] Handle empty state ("Start watching anime...")

**Implementation Notes**:
- Use `useHistory()` hook for authenticated users
- Use existing `useWatchProgress()` hook for guests
- Merge and deduplicate if needed
- Link cards to `/anime/[id]?episode=[episode_id]` or `/anime/[id]`

### 3. My Library Page

**Required Features**:
- [ ] Create `/library` page
- [ ] Tab navigation by status:
  - All
  - Watching
  - Planned
  - Completed
  - Dropped
  
- [ ] Filter by favorites (checkbox/toggle)
- [ ] Grid/list view of anime cards
- [ ] Each card shows:
  - Poster image
  - Title
  - Status badge
  - Favorite indicator
  - Progress info (if watching)
  
- [ ] Empty states for each tab
- [ ] Pagination or infinite scroll (if >50 items)

**Implementation Notes**:
- Use `useLibrary({ status, favorites })` hook with filters
- URL state management with `nuqs` for filters (e.g., `/library?status=watching&favorites=true`)
- Responsive grid layout
- Handle loading and error states

### 4. Login Merge Flow

**Required Features**:
- [ ] Detect local data on login:
  - Check localStorage for progress data
  - Check localStorage for saved series (library items)
  
- [ ] Merge strategy:
  - Upload local progress → `PUT /api/v1/me/progress/{episode_id}`
  - Upload local library → `PUT /api/v1/me/library/{title_id}`
  - Server wins on conflict (latest `updated_at`)
  
- [ ] User feedback:
  - Show merge progress indicator
  - Success notification ("Library synced!")
  - Error handling with retry option
  
- [ ] Background sync:
  - Non-blocking merge process
  - Allow user to continue browsing
  - Update UI when complete

**Implementation Notes**:
- Trigger on successful login (auth callback)
- Use existing `useWatchProgress()` and `useSavedSeries()` hooks to read local data
- Batch API calls to avoid rate limiting
- Clear localStorage after successful merge (optional, or keep as backup)
- Add `isSyncing` state to prevent duplicate merges

## Verification Steps

### Build Verification
```bash
cd frontend
bun install
bun run build  # Must succeed without errors
```

### Functionality Testing
1. **Guest User Flow**:
   - Browse to title page → add to library (localStorage)
   - Watch episode → progress saved locally
   - View continue watching → see local data
   
2. **Authenticated User Flow**:
   - Login → trigger merge flow
   - Add title to library → saved to server
   - Watch episode → progress saved to server
   - View continue watching → see server data
   - Check `/library` page → see synced items
   
3. **Regression Testing**:
   - Existing pages still work
   - Video player unchanged
   - Navigation functional
   - No console errors

### Performance Testing
- Page load times <2s
- Library page with 100+ items performs well
- Progress indicators load without blocking UI
- No memory leaks with TanStack Query

## Files to Create/Modify

### New Files (Estimated)
- `frontend/src/app/library/page.tsx` - Library page
- `frontend/src/components/anime/add-to-library-button.tsx` - Library controls
- `frontend/src/components/anime/favorite-button.tsx` - Favorite toggle
- `frontend/src/components/anime/episode-list.tsx` - Episode list with progress
- `frontend/src/components/home/continue-watching.tsx` - Continue watching section
- `frontend/src/lib/auth/merge-local-data.ts` - Login merge logic
- `frontend/src/hooks/use-login-merge.ts` - Merge hook

### Modified Files (Estimated)
- `frontend/src/app/anime/[id]/page.tsx` - Add library controls + episode list
- `frontend/src/app/page.tsx` - Add continue watching section
- `frontend/src/app/login/page.tsx` or auth callback - Trigger merge
- `frontend/src/components/anime/anime-card.tsx` - Add progress indicators (if exists)

## Implementation Order

### Recommended Sequence
1. **Rich Title Page** (1-2 days)
   - Add library controls (add/favorite buttons)
   - Add episode list with progress
   - Season grouping (best-effort)
   
2. **Continue Watching** (1 day)
   - Create component
   - Add to home page
   - Handle auth/guest logic
   
3. **My Library Page** (1-2 days)
   - Create page structure
   - Tab navigation
   - Filters and grid
   
4. **Login Merge** (1 day)
   - Implement merge logic
   - Add to auth flow
   - User feedback

### Total Estimate
4-6 days of focused development

## Success Metrics

- ✅ All acceptance criteria met
- ✅ `bun run build` passes
- ✅ No TypeScript errors
- ✅ No console warnings
- ✅ Existing functionality unaffected
- ✅ Guest and authenticated flows work
- ✅ Mobile responsive
- ✅ Accessible (keyboard navigation, ARIA labels)

## Notes

- **Backend is ready**: Phase 1 provides all necessary APIs
- **Hooks are ready**: Frontend hooks with caching already implemented
- **No breaking changes**: All additions, no modifications to existing flows
- **Progressive enhancement**: Features gracefully degrade for guests

## References

- Phase 1 PR: #3
- Backend API docs: `docs/features.md`
- Frontend hooks: `frontend/src/hooks/use-library.ts`, `use-server-progress.ts`
- API client: `frontend/src/lib/api/backend.ts`

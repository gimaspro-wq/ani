# Design notes (planning only)

## Admin isolation plan

- Target structure: move the admin panel to its own package/app (e.g., `apps/admin`) so it can build, lint, and deploy independently from the public site.
- Assets to relocate together: `frontend/src/app/admin/**`, `frontend/src/lib/orpc/**`, `frontend/src/lib/query/**`, `frontend/src/lib/search/**`, admin auth context/hooks, and any admin-only UI shells.
- Dependencies to account for: oRPC client/server bindings, TanStack Query usage, admin auth/session handling, and shared UI components pulled from `frontend/src/components`.
- Blockers to track: shared UI primitives (buttons, inputs), global Tailwind/Next.js config, environment variable handling, and router configuration for the `/admin` base path. These need duplication or a shared package before extraction.
- After extraction: wire the admin app to the backend/parsers through a dedicated API client and keep the public app oblivious to admin code.

## Public frontend simplification plan

- Goal: public pages should stop depending on admin infra (`frontend/src/lib/orpc/**`, `frontend/src/lib/query/**`, `frontend/src/lib/search/**`).
- Target public data layer: `frontend/src/lib/public-api.ts` + `fetch`/typed responses. Replace existing usages in `browse`, `search`, `schedule`, and `watch` flows with this boundary.
- Migration steps: introduce public-only query helpers, re-point data fetching away from admin-only routers, and drop admin-specific types from public components.
- Keep admin-specific behaviors (parser overrides, admin-modified flags) out of public components once migrated.

## CI simplification notes

- Current lint/CodeQL noise largely originates from the legacy admin panel (e.g., loose `any` types and shared infra bindings).
- Recommended next steps:
  - Add scoped lint runs that exclude `frontend/src/app/admin/**` for public PRs, or apply separate ESLint configs per app.
  - Isolate CodeQL source roots to scan admin separately from public/frontend/backend code.
  - Add optional admin-only overrides to avoid blocking public changes on legacy warnings.

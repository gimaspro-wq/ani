# Phase History

## Phase A — Inventory
- Cataloged all Markdown docs, backend modules, infrastructure files, and their purpose/layer/usage status.
- No code changes made.

## Phase B — Dead Code Identification
- Flagged unused/uncertain items (RBAC helper, domain entity stubs, read-model event handlers) as candidates.
- Decision: **preserve** all; no deletions approved.
- No code changes made.

## Phase C — Documentation Rewrite
- Consolidated documentation into a minimal, current set:
  - `README.md` (entry point)
  - `docs/architecture.md`
  - `docs/read-write-split.md`
  - `docs/cache-first.md`
  - `docs/development.md`
  - `docs/deployment.md`
  - `docs/phase-history.md` (this file)
- Archived or stubbed historical documents; no code changes.

Status: Contracts unchanged, write path untouched, and documentation now reflects current behavior only.

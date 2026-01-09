## Cache-first read models (Phase 5)

- **Read source:** Redis read models only (anime catalog/detail, user library/progress/history-last).
- **No fallback:** If a Redis key is missing, APIs return 404. If present but empty, APIs return 200 with an empty payload. No rebuild-on-read.
- **Rebuild triggers:** External/operational only (admin/manual/cron) via read-model rebuild handlers under `app/infrastructure/read/events/`. No coupling to write path.
- **API modules:** Read endpoints live in `app/api/read/*`; existing API modules remain unchanged. `main.py` includes the read router only.
- **Write path isolation:** Domain, write services, repositories, migrations, and existing APIs remain untouched by read-path code.
- **Observability:** Missing-key 404 responses indicate cache population is required; use the rebuild handlers to repopulate.

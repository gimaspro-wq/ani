# Read-model rebuild handlers

Handlers here rebuild Redis read models from Postgres snapshots. They are invoked by operational workflows (admin/manual/cron), not automatically by API requests.
- `anime_handlers.py` — rebuild catalog/detail
- `user_library_handlers.py` — rebuild user library
- `user_progress_handlers.py` — rebuild user progress
- `user_history_handlers.py` — rebuild last history entry

No write-path logic should call these directly from request handlers; they are for out-of-band cache population.

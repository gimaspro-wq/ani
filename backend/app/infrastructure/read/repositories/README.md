# Read-model repositories

Redis accessors used by the read API and rebuild handlers:
- `anime_read_repository.py` — catalog/detail keys
- `user_read_repository.py` — library/progress/history-last keys

They only read/write Redis and must not hit Postgres or alter write-path logic.

# Read-model schemas

Dataclasses describing the shapes stored in Redis for read endpoints:
- Anime catalog/detail
- User library
- User progress
- User history (last entry)

These are cache representations only and should mirror what read endpoints serve without adding write-path concerns.

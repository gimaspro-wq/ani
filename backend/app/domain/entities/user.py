"""Pure domain user entity."""
from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class User:
    id: int
    email: str
    hashed_password: str
    is_active: bool
    created_at: datetime


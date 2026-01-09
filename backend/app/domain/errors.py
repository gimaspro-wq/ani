"""Domain-level error definitions.

Domain errors must not depend on framework or infrastructure concerns.
"""


class DomainError(Exception):
    """Base class for domain errors."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class DomainConflictError(DomainError):
    """Raised when a domain conflict occurs (e.g., duplicate resource)."""


class DomainAuthenticationError(DomainError):
    """Raised when authentication or credential validation fails."""

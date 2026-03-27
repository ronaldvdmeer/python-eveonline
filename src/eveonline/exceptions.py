"""Exceptions for the Eve Online ESI client."""

from __future__ import annotations


class EveOnlineError(Exception):
    """Base exception for Eve Online ESI errors."""


class EveOnlineConnectionError(EveOnlineError):
    """Exception raised when the ESI API is unreachable."""


class EveOnlineAuthenticationError(EveOnlineError):
    """Exception raised when authentication fails or token is invalid."""


class EveOnlineRateLimitError(EveOnlineError):
    """Exception raised when the ESI rate limit is exceeded.

    Attributes:
        retry_after: Seconds to wait before retrying, or ``None`` if the
            server did not provide the header.
    """

    def __init__(self, retry_after: int | None = None) -> None:
        """Initialize the rate limit error.

        Args:
            retry_after: Optional number of seconds the server asks us to
                wait before retrying.
        """
        self.retry_after = retry_after
        message = "ESI rate limit exceeded"
        if retry_after is not None:
            message += f", retry after {retry_after}s"
        super().__init__(message)


class EveOnlineNotFoundError(EveOnlineError):
    """Exception raised when a resource is not found (404)."""

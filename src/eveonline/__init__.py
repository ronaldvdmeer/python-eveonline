"""Async Python client for the Eve Online ESI API."""

from .client import EveOnlineClient
from .auth import AbstractAuth
from .exceptions import (
    EveOnlineError,
    EveOnlineConnectionError,
    EveOnlineAuthenticationError,
    EveOnlineRateLimitError,
)

__version__ = "0.1.0"

__all__ = [
    "EveOnlineClient",
    "AbstractAuth",
    "EveOnlineError",
    "EveOnlineConnectionError",
    "EveOnlineAuthenticationError",
    "EveOnlineRateLimitError",
    "__version__",
]

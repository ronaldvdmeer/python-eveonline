"""Async Python client for the Eve Online ESI API."""

from .auth import AbstractAuth
from .client import EveOnlineClient
from .exceptions import (
    EveOnlineAuthenticationError,
    EveOnlineConnectionError,
    EveOnlineError,
    EveOnlineRateLimitError,
)

__version__ = "0.2.0"

__all__ = [
    "AbstractAuth",
    "EveOnlineAuthenticationError",
    "EveOnlineClient",
    "EveOnlineConnectionError",
    "EveOnlineError",
    "EveOnlineRateLimitError",
    "__version__",
]

"""Async Python client for the Eve Online ESI API."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from .auth import AbstractAuth
from .client import EveOnlineClient
from .exceptions import (
    EveOnlineAuthenticationError,
    EveOnlineConnectionError,
    EveOnlineError,
    EveOnlineNotFoundError,
    EveOnlineRateLimitError,
)

try:
    __version__ = version("python-eveonline")
except PackageNotFoundError:
    __version__ = "0.0.0"

__all__ = [
    "AbstractAuth",
    "EveOnlineAuthenticationError",
    "EveOnlineClient",
    "EveOnlineConnectionError",
    "EveOnlineError",
    "EveOnlineNotFoundError",
    "EveOnlineRateLimitError",
    "__version__",
]

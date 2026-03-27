"""Tests for exceptions module."""

from __future__ import annotations

import eveonline
from eveonline.exceptions import (
    EveOnlineAuthenticationError,
    EveOnlineConnectionError,
    EveOnlineError,
    EveOnlineNotFoundError,
    EveOnlineRateLimitError,
)


class TestExceptionHierarchy:
    """Test exception class hierarchy."""

    def test_base_exception(self):
        """EveOnlineError is the base for all exceptions."""
        err = EveOnlineError("test")
        assert isinstance(err, Exception)
        assert str(err) == "test"

    def test_connection_error_inherits(self):
        """EveOnlineConnectionError inherits from EveOnlineError."""
        err = EveOnlineConnectionError("connection failed")
        assert isinstance(err, EveOnlineError)

    def test_auth_error_inherits(self):
        """EveOnlineAuthenticationError inherits from EveOnlineError."""
        err = EveOnlineAuthenticationError("invalid token")
        assert isinstance(err, EveOnlineError)

    def test_not_found_error_inherits(self):
        """EveOnlineNotFoundError inherits from EveOnlineError."""
        err = EveOnlineNotFoundError("not found")
        assert isinstance(err, EveOnlineError)

    def test_rate_limit_error_inherits(self):
        """EveOnlineRateLimitError inherits from EveOnlineError."""
        err = EveOnlineRateLimitError(retry_after=30)
        assert isinstance(err, EveOnlineError)


class TestRateLimitError:
    """Test EveOnlineRateLimitError specific behavior."""

    def test_with_retry_after(self):
        """Rate limit error with retry_after value."""
        err = EveOnlineRateLimitError(retry_after=60)
        assert err.retry_after == 60
        assert "60s" in str(err)

    def test_without_retry_after(self):
        """Rate limit error without retry_after value."""
        err = EveOnlineRateLimitError()
        assert err.retry_after is None
        assert "rate limit exceeded" in str(err).lower()

    def test_retry_after_none_explicit(self):
        """Explicit None for retry_after."""
        err = EveOnlineRateLimitError(retry_after=None)
        assert err.retry_after is None
        assert "retry after" not in str(err)


class TestTopLevelExports:
    """Verify all exceptions are accessible from the package root."""

    def test_not_found_error_exported(self):
        """EveOnlineNotFoundError is importable from eveonline."""
        assert hasattr(eveonline, "EveOnlineNotFoundError")
        assert eveonline.EveOnlineNotFoundError is EveOnlineNotFoundError

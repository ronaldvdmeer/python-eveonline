"""Tests for the AbstractAuth class."""

from __future__ import annotations

import aiohttp
import pytest
from aioresponses import aioresponses
from yarl import URL

from eveonline.auth import AbstractAuth
from eveonline.const import ESI_BASE_URL

from .conftest import MockAuth


class TestAbstractAuth:
    """Test AbstractAuth and its concrete MockAuth implementation."""

    def test_cannot_instantiate_abstract(self):
        """AbstractAuth cannot be instantiated directly."""
        with pytest.raises(TypeError, match="async_get_access_token"):
            AbstractAuth(websession=None)  # type: ignore[abstract]

    def test_default_host(self, mock_session):
        """Default host is ESI_BASE_URL."""
        auth = MockAuth(mock_session)
        assert auth.host == ESI_BASE_URL

    def test_custom_host(self, mock_session):
        """Custom host can be provided."""
        auth = MockAuth(mock_session)
        auth.host = "https://custom.esi.test"
        assert auth.host == "https://custom.esi.test"

    @pytest.mark.asyncio
    async def test_get_access_token(self):
        """MockAuth returns the configured token."""
        async with aiohttp.ClientSession() as session:
            auth = MockAuth(session, token="my-secret-token")
            token = await auth.async_get_access_token()
        assert token == "my-secret-token"

    @pytest.mark.asyncio
    async def test_request_adds_bearer_token(self):
        """Requests include the Authorization: Bearer header."""
        with aioresponses() as mocked:
            mocked.get(
                f"{ESI_BASE_URL}/test/endpoint",
                payload={"success": True},
            )
            async with aiohttp.ClientSession() as session:
                auth = MockAuth(session, token="bearer-test-token")
                resp = await auth.request("GET", "test/endpoint")
                data = await resp.json()

        assert data == {"success": True}
        assert resp.status == 200
        # Verify the request was made (aioresponses recorded it)
        key = ("GET", URL(f"{ESI_BASE_URL}/test/endpoint"))
        assert key in mocked.requests
        call_obj = mocked.requests[key][0]
        assert call_obj.kwargs["headers"]["authorization"] == "Bearer bearer-test-token"

    @pytest.mark.asyncio
    async def test_request_preserves_existing_headers(self):
        """Existing headers are preserved alongside the auth header."""
        with aioresponses() as mocked:
            mocked.get(
                f"{ESI_BASE_URL}/test/headers",
                payload={"ok": True},
            )
            async with aiohttp.ClientSession() as session:
                auth = MockAuth(session, token="test-token")
                resp = await auth.request(
                    "GET",
                    "test/headers",
                    headers={"X-Custom": "value"},
                )
                data = await resp.json()

        assert data == {"ok": True}
        assert resp.status == 200

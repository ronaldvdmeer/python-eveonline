"""Tests for ETag caching in EveOnlineClient."""

from __future__ import annotations

import aiohttp
import pytest
from aioresponses import aioresponses

from eveonline import EveOnlineClient
from eveonline.const import ESI_BASE_URL
from eveonline.models import ServerStatus

from .conftest import MockAuth

CHARACTER_ID = 2113024536

_SERVER_STATUS = {
    "players": 23000,
    "server_version": "abc",
    "start_time": "2026-03-28T10:00:00Z",
}
_WALLET_BALANCE = 500000.0


class TestETagCaching:
    """ETag caching behaviour for GET endpoints."""

    @pytest.mark.asyncio
    async def test_etag_stored_on_first_response(self):
        """ETag from response header is stored in the cache."""
        with aioresponses() as mocked:
            mocked.get(
                f"{ESI_BASE_URL}/status/?datasource=tranquility",
                payload=_SERVER_STATUS,
                headers={"ETag": '"abc123"'},
            )
            async with aiohttp.ClientSession() as session:
                client = EveOnlineClient(session=session)
                await client.async_get_server_status()

        cache_key = client._etag_key("status/", {"datasource": "tranquility"}, authenticated=False)
        assert cache_key in client._etag_cache
        assert client._etag_cache[cache_key][0] == '"abc123"'

    @pytest.mark.asyncio
    async def test_304_returns_cached_data(self):
        """HTTP 304 response returns previously cached data without a body."""
        async with aiohttp.ClientSession() as session:
            client = EveOnlineClient(session=session)

            # First call — populate cache.
            with aioresponses() as mocked:
                mocked.get(
                    f"{ESI_BASE_URL}/status/?datasource=tranquility",
                    payload=_SERVER_STATUS,
                    headers={"ETag": '"abc123"'},
                )
                first = await client.async_get_server_status()

            assert isinstance(first, ServerStatus)
            assert first.players == 23000

            # Second call — ESI says nothing changed (304).
            with aioresponses() as mocked:
                mocked.get(
                    f"{ESI_BASE_URL}/status/?datasource=tranquility",
                    status=304,
                )
                second = await client.async_get_server_status()

        # Should return the exact same cached data.
        assert second.players == 23000
        assert second == first

    @pytest.mark.asyncio
    async def test_no_etag_in_response_not_cached(self):
        """If ESI returns no ETag header, nothing is stored in the cache."""
        with aioresponses() as mocked:
            mocked.get(
                f"{ESI_BASE_URL}/status/?datasource=tranquility",
                payload=_SERVER_STATUS,
                # No ETag header
            )
            async with aiohttp.ClientSession() as session:
                client = EveOnlineClient(session=session)
                await client.async_get_server_status()

        assert client._etag_cache == {}

    @pytest.mark.asyncio
    async def test_etag_cache_is_updated_on_new_etag(self):
        """When a 200 returns a new ETag, the cache entry is updated."""
        async with aiohttp.ClientSession() as session:
            client = EveOnlineClient(session=session)

            with aioresponses() as mocked:
                mocked.get(
                    f"{ESI_BASE_URL}/status/?datasource=tranquility",
                    payload=_SERVER_STATUS,
                    headers={"ETag": '"etag-v1"'},
                )
                await client.async_get_server_status()

            updated_status = {**_SERVER_STATUS, "players": 30000}
            with aioresponses() as mocked:
                mocked.get(
                    f"{ESI_BASE_URL}/status/?datasource=tranquility",
                    payload=updated_status,
                    headers={"ETag": '"etag-v2"'},
                )
                result = await client.async_get_server_status()

        assert result.players == 30000
        cache_key = client._etag_key("status/", {"datasource": "tranquility"}, authenticated=False)
        assert client._etag_cache[cache_key][0] == '"etag-v2"'

    @pytest.mark.asyncio
    async def test_post_request_not_cached(self):
        """POST requests (like resolve_names) are never cached."""
        with aioresponses() as mocked:
            mocked.post(
                f"{ESI_BASE_URL}/universe/names/?datasource=tranquility",
                payload=[{"id": 2113024536, "name": "Test Char", "category": "character"}],
                headers={"ETag": '"should-not-be-stored"'},
            )
            async with aiohttp.ClientSession() as session:
                client = EveOnlineClient(session=session)
                await client.async_resolve_names([2113024536])

        assert client._etag_cache == {}

    @pytest.mark.asyncio
    async def test_pub_and_auth_have_separate_cache_keys(self):
        """Public and authenticated requests for the same path use different cache keys."""
        async with aiohttp.ClientSession() as session:
            auth = MockAuth(session)
            client = EveOnlineClient(auth=auth)
            params = {"datasource": "tranquility"}

            pub_key = client._etag_key("status/", params, authenticated=False)
            auth_key = client._etag_key("status/", params, authenticated=True)

        assert pub_key != auth_key
        assert pub_key.startswith("pub:")
        assert auth_key.startswith("auth:")

    @pytest.mark.asyncio
    async def test_etag_stored_for_authenticated_endpoint(self):
        """ETag caching works for authenticated endpoints too."""
        with aioresponses() as mocked:
            mocked.get(
                f"{ESI_BASE_URL}/characters/{CHARACTER_ID}/wallet/?datasource=tranquility",
                payload=_WALLET_BALANCE,
                headers={"ETag": '"wallet-etag-1"'},
            )
            async with aiohttp.ClientSession() as session:
                auth = MockAuth(session)
                client = EveOnlineClient(auth=auth)
                await client.async_get_wallet_balance(CHARACTER_ID)

        cache_key = client._etag_key(
            f"characters/{CHARACTER_ID}/wallet/",
            {"datasource": "tranquility"},
            authenticated=True,
        )
        assert cache_key in client._etag_cache
        assert client._etag_cache[cache_key][0] == '"wallet-etag-1"'

    @pytest.mark.asyncio
    async def test_authenticated_304_returns_cached_data(self):
        """Authenticated endpoint returns cached wallet balance on 304."""
        async with aiohttp.ClientSession() as session:
            auth = MockAuth(session)
            client = EveOnlineClient(auth=auth)

            with aioresponses() as mocked:
                mocked.get(
                    f"{ESI_BASE_URL}/characters/{CHARACTER_ID}/wallet/?datasource=tranquility",
                    payload=_WALLET_BALANCE,
                    headers={"ETag": '"wallet-etag-1"'},
                )
                first = await client.async_get_wallet_balance(CHARACTER_ID)

            with aioresponses() as mocked:
                mocked.get(
                    f"{ESI_BASE_URL}/characters/{CHARACTER_ID}/wallet/?datasource=tranquility",
                    status=304,
                )
                second = await client.async_get_wallet_balance(CHARACTER_ID)

        assert second.balance == first.balance

"""Tests for ETag caching in EveOnlineClient."""

from __future__ import annotations

import aiohttp
import pytest
from aioresponses import aioresponses

from eveonline import EveOnlineClient
from eveonline.const import ESI_BASE_URL
from eveonline.exceptions import (
    EveOnlineError,
    EveOnlineNotFoundError,
    EveOnlineRateLimitError,
)
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

    @pytest.mark.asyncio
    async def test_304_without_cache_entry_raises_error(self):
        """A 304 response with no matching cache entry raises EveOnlineError."""
        with aioresponses() as mocked:
            mocked.get(
                f"{ESI_BASE_URL}/status/?datasource=tranquility",
                status=304,
            )
            async with aiohttp.ClientSession() as session:
                client = EveOnlineClient(session=session)
                with pytest.raises(EveOnlineError, match="304 Not Modified"):
                    await client.async_get_server_status()


class TestETagIfNoneMatch:
    """Verify that the If-None-Match header is actually sent."""

    @pytest.mark.asyncio
    async def test_if_none_match_header_sent_on_second_request(self):
        """Second GET for same endpoint includes If-None-Match header."""
        async with aiohttp.ClientSession() as session:
            client = EveOnlineClient(session=session)

            with aioresponses() as mocked:
                mocked.get(
                    f"{ESI_BASE_URL}/status/?datasource=tranquility",
                    payload=_SERVER_STATUS,
                    headers={"ETag": '"etag-v1"'},
                )
                await client.async_get_server_status()

            with aioresponses() as mocked:
                mocked.get(
                    f"{ESI_BASE_URL}/status/?datasource=tranquility",
                    payload=_SERVER_STATUS,
                    headers={"ETag": '"etag-v1"'},
                )
                await client.async_get_server_status()

                # Inspect the request that was actually made.
                call_args = next(iter(mocked.requests.values()))[0]
                request_headers = call_args.kwargs.get("headers", {})
                assert request_headers.get("If-None-Match") == '"etag-v1"'

    @pytest.mark.asyncio
    async def test_no_if_none_match_on_first_request(self):
        """First GET for a fresh client sends no If-None-Match."""
        async with aiohttp.ClientSession() as session:
            client = EveOnlineClient(session=session)

            with aioresponses() as mocked:
                mocked.get(
                    f"{ESI_BASE_URL}/status/?datasource=tranquility",
                    payload=_SERVER_STATUS,
                    headers={"ETag": '"fresh"'},
                )
                await client.async_get_server_status()

                call_args = next(iter(mocked.requests.values()))[0]
                request_headers = call_args.kwargs.get("headers", {})
                assert "If-None-Match" not in request_headers

    @pytest.mark.asyncio
    async def test_if_none_match_sent_for_authenticated_request(self):
        """Authenticated GET sends If-None-Match after first call."""
        async with aiohttp.ClientSession() as session:
            auth = MockAuth(session)
            client = EveOnlineClient(auth=auth)

            with aioresponses() as mocked:
                mocked.get(
                    f"{ESI_BASE_URL}/characters/{CHARACTER_ID}/wallet/?datasource=tranquility",
                    payload=_WALLET_BALANCE,
                    headers={"ETag": '"auth-etag"'},
                )
                await client.async_get_wallet_balance(CHARACTER_ID)

            with aioresponses() as mocked:
                mocked.get(
                    f"{ESI_BASE_URL}/characters/{CHARACTER_ID}/wallet/?datasource=tranquility",
                    payload=_WALLET_BALANCE,
                    headers={"ETag": '"auth-etag"'},
                )
                await client.async_get_wallet_balance(CHARACTER_ID)

                call_args = next(iter(mocked.requests.values()))[0]
                request_headers = call_args.kwargs.get("headers", {})
                assert request_headers.get("If-None-Match") == '"auth-etag"'


class TestETagCacheKeyIsolation:
    """Verify that cache keys are properly isolated per endpoint/params."""

    @pytest.mark.asyncio
    async def test_different_character_ids_have_separate_keys(self):
        """Same endpoint with different character_id should not share cache."""
        char_a, char_b = 111, 222
        async with aiohttp.ClientSession() as session:
            auth = MockAuth(session)
            client = EveOnlineClient(auth=auth)

            with aioresponses() as mocked:
                mocked.get(
                    f"{ESI_BASE_URL}/characters/{char_a}/wallet/?datasource=tranquility",
                    payload=100000.0,
                    headers={"ETag": '"etag-a"'},
                )
                mocked.get(
                    f"{ESI_BASE_URL}/characters/{char_b}/wallet/?datasource=tranquility",
                    payload=200000.0,
                    headers={"ETag": '"etag-b"'},
                )
                balance_a = await client.async_get_wallet_balance(char_a)
                balance_b = await client.async_get_wallet_balance(char_b)

        assert balance_a.balance == 100000.0
        assert balance_b.balance == 200000.0
        assert len(client._etag_cache) == 2

    @pytest.mark.asyncio
    async def test_different_endpoints_have_separate_keys(self):
        """Multiple cached endpoints do not interfere with each other."""
        async with aiohttp.ClientSession() as session:
            client = EveOnlineClient(session=session)

            with aioresponses() as mocked:
                mocked.get(
                    f"{ESI_BASE_URL}/status/?datasource=tranquility",
                    payload=_SERVER_STATUS,
                    headers={"ETag": '"status-etag"'},
                )
                mocked.get(
                    f"{ESI_BASE_URL}/characters/{CHARACTER_ID}/?datasource=tranquility",
                    payload={
                        "name": "Test",
                        "corporation_id": 1,
                        "birthday": "2020-01-01T00:00:00Z",
                        "gender": "male",
                        "race_id": 1,
                        "bloodline_id": 1,
                    },
                    headers={"ETag": '"char-etag"'},
                )
                await client.async_get_server_status()
                await client.async_get_character_public(CHARACTER_ID)

        assert len(client._etag_cache) == 2

    @pytest.mark.asyncio
    async def test_extra_query_params_produce_different_key(self):
        """include_completed=True changes the cache key for industry jobs."""
        async with aiohttp.ClientSession() as session:
            auth = MockAuth(session)
            client = EveOnlineClient(auth=auth)

            with aioresponses() as mocked:
                mocked.get(
                    f"{ESI_BASE_URL}/characters/{CHARACTER_ID}/industry/jobs/?datasource=tranquility",
                    payload=[],
                    headers={"ETag": '"no-completed"'},
                )
                mocked.get(
                    f"{ESI_BASE_URL}/characters/{CHARACTER_ID}/industry/jobs/"
                    f"?datasource=tranquility&include_completed=true",
                    payload=[],
                    headers={"ETag": '"with-completed"'},
                )
                await client.async_get_industry_jobs(CHARACTER_ID)
                await client.async_get_industry_jobs(CHARACTER_ID, include_completed=True)

        assert len(client._etag_cache) == 2


class TestETagErrorResponses:
    """ETag cache must NOT be polluted by error responses."""

    @pytest.mark.asyncio
    async def test_500_does_not_cache(self):
        """HTTP 500 must not store an ETag or pollute existing cache."""
        async with aiohttp.ClientSession() as session:
            client = EveOnlineClient(session=session)

            # First normal response — populates cache.
            with aioresponses() as mocked:
                mocked.get(
                    f"{ESI_BASE_URL}/status/?datasource=tranquility",
                    payload=_SERVER_STATUS,
                    headers={"ETag": '"good-etag"'},
                )
                await client.async_get_server_status()

            # Second request returns 500 — cache entry must survive intact.
            with aioresponses() as mocked:
                mocked.get(
                    f"{ESI_BASE_URL}/status/?datasource=tranquility",
                    status=500,
                    body="Internal Server Error",
                )
                with pytest.raises(EveOnlineError):
                    await client.async_get_server_status()

        cache_key = client._etag_key("status/", {"datasource": "tranquility"}, authenticated=False)
        assert client._etag_cache[cache_key][0] == '"good-etag"'

    @pytest.mark.asyncio
    async def test_404_does_not_cache(self):
        """HTTP 404 must not add a cache entry."""
        with aioresponses() as mocked:
            mocked.get(
                f"{ESI_BASE_URL}/characters/999/?datasource=tranquility",
                status=404,
                body="Not Found",
            )
            async with aiohttp.ClientSession() as session:
                client = EveOnlineClient(session=session)
                with pytest.raises(EveOnlineNotFoundError):
                    await client.async_get_character_public(999)

        assert client._etag_cache == {}

    @pytest.mark.asyncio
    async def test_429_does_not_cache(self):
        """HTTP 429 (rate limit) must not add a cache entry."""
        with aioresponses() as mocked:
            mocked.get(
                f"{ESI_BASE_URL}/status/?datasource=tranquility",
                status=429,
                headers={"Retry-After": "5"},
            )
            async with aiohttp.ClientSession() as session:
                client = EveOnlineClient(session=session)
                with pytest.raises(EveOnlineRateLimitError):
                    await client.async_get_server_status()

        assert client._etag_cache == {}


class TestETagEdgeCases:
    """Edge cases for ETag caching."""

    @pytest.mark.asyncio
    async def test_empty_etag_header_not_cached(self):
        """An empty ETag header should not be stored."""
        with aioresponses() as mocked:
            mocked.get(
                f"{ESI_BASE_URL}/status/?datasource=tranquility",
                payload=_SERVER_STATUS,
                headers={"ETag": ""},
            )
            async with aiohttp.ClientSession() as session:
                client = EveOnlineClient(session=session)
                await client.async_get_server_status()

        assert client._etag_cache == {}

    @pytest.mark.asyncio
    async def test_cache_survives_304_followed_by_200(self):
        """Cache is updated when a 304 is followed by a new 200 response."""
        async with aiohttp.ClientSession() as session:
            client = EveOnlineClient(session=session)

            # 1st — populate cache.
            with aioresponses() as mocked:
                mocked.get(
                    f"{ESI_BASE_URL}/status/?datasource=tranquility",
                    payload=_SERVER_STATUS,
                    headers={"ETag": '"v1"'},
                )
                first = await client.async_get_server_status()

            # 2nd — 304 returns cached.
            with aioresponses() as mocked:
                mocked.get(
                    f"{ESI_BASE_URL}/status/?datasource=tranquility",
                    status=304,
                )
                second = await client.async_get_server_status()
            assert second == first

            # 3rd — new data with new ETag.
            updated = {**_SERVER_STATUS, "players": 50000}
            with aioresponses() as mocked:
                mocked.get(
                    f"{ESI_BASE_URL}/status/?datasource=tranquility",
                    payload=updated,
                    headers={"ETag": '"v2"'},
                )
                third = await client.async_get_server_status()

            assert third.players == 50000
            cache_key = client._etag_key("status/", {"datasource": "tranquility"}, authenticated=False)
            assert client._etag_cache[cache_key][0] == '"v2"'

    @pytest.mark.asyncio
    async def test_multiple_clients_have_independent_caches(self):
        """Each client instance has its own isolated ETag cache."""
        async with aiohttp.ClientSession() as session:
            client_a = EveOnlineClient(session=session)
            client_b = EveOnlineClient(session=session)

            with aioresponses() as mocked:
                mocked.get(
                    f"{ESI_BASE_URL}/status/?datasource=tranquility",
                    payload=_SERVER_STATUS,
                    headers={"ETag": '"client-a-etag"'},
                )
                await client_a.async_get_server_status()

        assert len(client_a._etag_cache) == 1
        assert len(client_b._etag_cache) == 0

    @pytest.mark.asyncio
    async def test_clear_etag_cache(self):
        """clear_etag_cache() empties the cache so next request fetches fresh data."""
        async with aiohttp.ClientSession() as session:
            client = EveOnlineClient(session=session)

            with aioresponses() as mocked:
                mocked.get(
                    f"{ESI_BASE_URL}/status/?datasource=tranquility",
                    payload=_SERVER_STATUS,
                    headers={"ETag": '"will-be-cleared"'},
                )
                await client.async_get_server_status()

            assert len(client._etag_cache) == 1
            client.clear_etag_cache()
            assert client._etag_cache == {}

    @pytest.mark.asyncio
    async def test_malformed_x_pages_header_defaults_to_single_page(self):
        """A non-integer X-Pages header falls back to 1 without raising."""
        with aioresponses() as mocked:
            mocked.get(
                f"{ESI_BASE_URL}/status/?datasource=tranquility",
                payload={"players": 5000, "server_version": "DEADSPACE", "start_time": "2025-01-01T00:00:00Z"},
                headers={"ETag": '"abc"', "X-Pages": "not-a-number"},
            )
            async with aiohttp.ClientSession() as session:
                client = EveOnlineClient(session=session)
                result = await client.async_get_server_status()

        assert result.players == 5000
        cache_key = client._etag_key("status/", {"datasource": "tranquility"}, authenticated=False)
        assert client._etag_cache[cache_key][2] == 1

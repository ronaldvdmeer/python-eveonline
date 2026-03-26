"""Tests for the EveOnlineClient — public (unauthenticated) endpoints."""

from __future__ import annotations

from datetime import UTC, datetime

import aiohttp
import pytest
from aioresponses import aioresponses

from eveonline import EveOnlineClient, EveOnlineError
from eveonline.const import ESI_BASE_URL
from eveonline.exceptions import (
    EveOnlineConnectionError,
    EveOnlineNotFoundError,
    EveOnlineRateLimitError,
)
from eveonline.models import (
    CharacterPortrait,
    CharacterPublicInfo,
    CorporationPublicInfo,
    ServerStatus,
    UniverseName,
)

CHARACTER_ID = 2113024536
CORPORATION_ID = 98000001


class TestClientInit:
    """Test EveOnlineClient initialization."""

    def test_init_with_session(self, mock_session):
        """Client can be initialized with just a session."""
        client = EveOnlineClient(session=mock_session)
        assert client._session is mock_session

    def test_init_with_auth(self, mock_auth):
        """Client can be initialized with an auth provider."""
        client = EveOnlineClient(auth=mock_auth)
        assert client._auth is mock_auth
        assert client._session is mock_auth.websession

    def test_init_auth_takes_precedence(self, mock_session, mock_auth):
        """When both are provided, auth's session is used."""
        client = EveOnlineClient(session=mock_session, auth=mock_auth)
        assert client._session is mock_auth.websession

    def test_init_no_session_no_auth_raises(self):
        """Must provide either session or auth."""
        with pytest.raises(EveOnlineError, match="Either 'session' or 'auth' must be provided"):
            EveOnlineClient()

    def test_init_custom_host(self, mock_session):
        """Custom ESI host can be provided."""
        client = EveOnlineClient(session=mock_session, host="https://custom.esi.test")
        assert client._host == "https://custom.esi.test"


class TestServerStatus:
    """Test GET /status/ endpoint."""

    @pytest.mark.asyncio
    async def test_get_server_status_success(self, server_status_data):
        """Successful server status fetch returns ServerStatus model."""
        with aioresponses() as mocked:
            mocked.get(
                f"{ESI_BASE_URL}/status/?datasource=tranquility",
                payload=server_status_data,
            )
            async with aiohttp.ClientSession() as session:
                client = EveOnlineClient(session=session)
                status = await client.async_get_server_status()

        assert isinstance(status, ServerStatus)
        assert status.players == 23451
        assert status.server_version == "2345678"
        assert status.start_time == datetime(2026, 3, 26, 11, 0, tzinfo=UTC)
        assert status.vip is False

    @pytest.mark.asyncio
    async def test_get_server_status_minimal(self):
        """Server status works with minimal fields (no vip)."""
        data = {
            "players": 100,
            "server_version": "1",
            "start_time": "2026-01-01T00:00:00Z",
        }
        with aioresponses() as mocked:
            mocked.get(
                f"{ESI_BASE_URL}/status/?datasource=tranquility",
                payload=data,
            )
            async with aiohttp.ClientSession() as session:
                client = EveOnlineClient(session=session)
                status = await client.async_get_server_status()

        assert status.players == 100
        assert status.vip is None

    @pytest.mark.asyncio
    async def test_get_server_status_connection_error(self):
        """Connection errors are wrapped in EveOnlineConnectionError."""
        with aioresponses() as mocked:
            mocked.get(
                f"{ESI_BASE_URL}/status/?datasource=tranquility",
                exception=aiohttp.ClientConnectionError("Connection refused"),
            )
            async with aiohttp.ClientSession() as session:
                client = EveOnlineClient(session=session)
                with pytest.raises(EveOnlineConnectionError, match="Failed to connect"):
                    await client.async_get_server_status()

    @pytest.mark.asyncio
    async def test_get_server_status_500_error(self):
        """HTTP 500 raises EveOnlineError."""
        with aioresponses() as mocked:
            mocked.get(
                f"{ESI_BASE_URL}/status/?datasource=tranquility",
                status=500,
                body="Internal Server Error",
            )
            async with aiohttp.ClientSession() as session:
                client = EveOnlineClient(session=session)
                with pytest.raises(EveOnlineError, match=r"ESI API error.*500"):
                    await client.async_get_server_status()

    @pytest.mark.asyncio
    async def test_get_server_status_rate_limited(self):
        """HTTP 429 raises EveOnlineRateLimitError with retry_after."""
        with aioresponses() as mocked:
            mocked.get(
                f"{ESI_BASE_URL}/status/?datasource=tranquility",
                status=429,
                headers={"Retry-After": "30"},
            )
            async with aiohttp.ClientSession() as session:
                client = EveOnlineClient(session=session)
                with pytest.raises(EveOnlineRateLimitError) as exc_info:
                    await client.async_get_server_status()
                assert exc_info.value.retry_after == 30

    @pytest.mark.asyncio
    async def test_get_server_status_error_limited_420(self):
        """HTTP 420 (error rate limit) raises EveOnlineRateLimitError."""
        with aioresponses() as mocked:
            mocked.get(
                f"{ESI_BASE_URL}/status/?datasource=tranquility",
                status=420,
                headers={"Retry-After": "60"},
            )
            async with aiohttp.ClientSession() as session:
                client = EveOnlineClient(session=session)
                with pytest.raises(EveOnlineRateLimitError) as exc_info:
                    await client.async_get_server_status()
                assert exc_info.value.retry_after == 60


class TestCharacterPublic:
    """Test GET /characters/{character_id}/ endpoint."""

    @pytest.mark.asyncio
    async def test_get_character_public_success(self, character_public_data):
        """Successful character info fetch returns all fields."""
        with aioresponses() as mocked:
            mocked.get(
                f"{ESI_BASE_URL}/characters/{CHARACTER_ID}/?datasource=tranquility",
                payload=character_public_data,
            )
            async with aiohttp.ClientSession() as session:
                client = EveOnlineClient(session=session)
                char = await client.async_get_character_public(CHARACTER_ID)

        assert isinstance(char, CharacterPublicInfo)
        assert char.character_id == CHARACTER_ID
        assert char.name == "CCP Bartender"
        assert char.corporation_id == 98000001
        assert char.gender == "male"
        assert char.race_id == 2
        assert char.bloodline_id == 4
        assert char.ancestry_id == 12
        assert char.alliance_id == 99000001
        assert char.description == "A test character"
        assert char.security_status == 1.8
        assert char.title == "Test Title"
        assert char.birthday == datetime(2015, 3, 24, 11, 37, tzinfo=UTC)

    @pytest.mark.asyncio
    async def test_get_character_public_minimal(self):
        """Character info with only required fields."""
        data = {
            "name": "Test Char",
            "corporation_id": 1,
            "birthday": "2020-01-01T00:00:00Z",
            "gender": "female",
            "race_id": 1,
            "bloodline_id": 1,
        }
        with aioresponses() as mocked:
            mocked.get(
                f"{ESI_BASE_URL}/characters/{CHARACTER_ID}/?datasource=tranquility",
                payload=data,
            )
            async with aiohttp.ClientSession() as session:
                client = EveOnlineClient(session=session)
                char = await client.async_get_character_public(CHARACTER_ID)

        assert char.name == "Test Char"
        assert char.alliance_id is None
        assert char.faction_id is None
        assert char.description is None
        assert char.title is None
        assert char.security_status is None

    @pytest.mark.asyncio
    async def test_get_character_not_found(self):
        """HTTP 404 raises EveOnlineNotFoundError."""
        with aioresponses() as mocked:
            mocked.get(
                f"{ESI_BASE_URL}/characters/999999999/?datasource=tranquility",
                status=404,
                body="Character not found",
            )
            async with aiohttp.ClientSession() as session:
                client = EveOnlineClient(session=session)
                with pytest.raises(EveOnlineNotFoundError):
                    await client.async_get_character_public(999999999)


class TestCharacterPortraitEndpoint:
    """Test GET /characters/{character_id}/portrait/ endpoint."""

    @pytest.mark.asyncio
    async def test_get_portrait_success(self, character_portrait_data):
        """Successful portrait fetch returns all image URLs."""
        with aioresponses() as mocked:
            mocked.get(
                f"{ESI_BASE_URL}/characters/{CHARACTER_ID}/portrait/?datasource=tranquility",
                payload=character_portrait_data,
            )
            async with aiohttp.ClientSession() as session:
                client = EveOnlineClient(session=session)
                portrait = await client.async_get_character_portrait(CHARACTER_ID)

        assert isinstance(portrait, CharacterPortrait)
        assert "size=64" in portrait.px64x64
        assert "size=512" in portrait.px512x512


class TestCorporationPublic:
    """Test GET /corporations/{corporation_id}/ endpoint."""

    @pytest.mark.asyncio
    async def test_get_corporation_public_success(self, corporation_public_data):
        """Successful corporation info fetch returns all fields."""
        with aioresponses() as mocked:
            mocked.get(
                f"{ESI_BASE_URL}/corporations/{CORPORATION_ID}/?datasource=tranquility",
                payload=corporation_public_data,
            )
            async with aiohttp.ClientSession() as session:
                client = EveOnlineClient(session=session)
                corp = await client.async_get_corporation_public(CORPORATION_ID)

        assert isinstance(corp, CorporationPublicInfo)
        assert corp.corporation_id == CORPORATION_ID
        assert corp.name == "C C P"
        assert corp.ticker == "CCP"
        assert corp.member_count == 256
        assert corp.ceo_id == CHARACTER_ID
        assert corp.tax_rate == 0.1
        assert corp.alliance_id == 99000001
        assert corp.date_founded == datetime(2003, 5, 6, 12, 0, tzinfo=UTC)
        assert corp.url == "https://www.eveonline.com"

    @pytest.mark.asyncio
    async def test_get_corporation_minimal(self):
        """Corporation info with only required fields."""
        data = {
            "name": "Test Corp",
            "ticker": "TST",
            "member_count": 1,
            "ceo_id": 1,
            "tax_rate": 0.0,
        }
        with aioresponses() as mocked:
            mocked.get(
                f"{ESI_BASE_URL}/corporations/{CORPORATION_ID}/?datasource=tranquility",
                payload=data,
            )
            async with aiohttp.ClientSession() as session:
                client = EveOnlineClient(session=session)
                corp = await client.async_get_corporation_public(CORPORATION_ID)

        assert corp.name == "Test Corp"
        assert corp.alliance_id is None
        assert corp.description is None
        assert corp.date_founded is None
        assert corp.url is None


class TestResolveNames:
    """Test POST /universe/names/ endpoint."""

    @pytest.mark.asyncio
    async def test_resolve_names_success(self, universe_names_data):
        """Successful name resolution returns list of UniverseName."""
        with aioresponses() as mocked:
            mocked.post(
                f"{ESI_BASE_URL}/universe/names/?datasource=tranquility",
                payload=universe_names_data,
            )
            async with aiohttp.ClientSession() as session:
                client = EveOnlineClient(session=session)
                names = await client.async_resolve_names([98000001, CHARACTER_ID])

        assert len(names) == 2
        assert all(isinstance(n, UniverseName) for n in names)
        assert names[0].id == 98000001
        assert names[0].name == "C C P"
        assert names[0].category == "corporation"
        assert names[1].name == "CCP Bartender"

    @pytest.mark.asyncio
    async def test_resolve_names_empty_list(self, mock_session):
        """Empty list returns empty result without making a request."""
        client = EveOnlineClient(session=mock_session)
        names = await client.async_resolve_names([])
        assert names == []
        mock_session.request.assert_not_called()

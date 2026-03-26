"""Tests for the EveOnlineClient — authenticated endpoints."""

from __future__ import annotations

from datetime import UTC, datetime

import aiohttp
import pytest
from aioresponses import aioresponses

from eveonline import EveOnlineClient
from eveonline.const import ESI_BASE_URL
from eveonline.exceptions import EveOnlineAuthenticationError
from eveonline.models import (
    CharacterLocation,
    CharacterOnlineStatus,
    CharacterShip,
    SkillQueueEntry,
    WalletBalance,
)

from .conftest import MockAuth

CHARACTER_ID = 2113024536


class TestAuthRequired:
    """Test that authenticated endpoints require auth."""

    @pytest.mark.asyncio
    async def test_online_without_auth_raises(self):
        """Calling authenticated endpoint without auth raises error."""
        async with aiohttp.ClientSession() as session:
            client = EveOnlineClient(session=session)
            with pytest.raises(
                EveOnlineAuthenticationError,
                match="Authentication required",
            ):
                await client.async_get_character_online(CHARACTER_ID)

    @pytest.mark.asyncio
    async def test_wallet_without_auth_raises(self):
        """Calling wallet endpoint without auth raises error."""
        async with aiohttp.ClientSession() as session:
            client = EveOnlineClient(session=session)
            with pytest.raises(EveOnlineAuthenticationError):
                await client.async_get_wallet_balance(CHARACTER_ID)

    @pytest.mark.asyncio
    async def test_location_without_auth_raises(self):
        """Calling location endpoint without auth raises error."""
        async with aiohttp.ClientSession() as session:
            client = EveOnlineClient(session=session)
            with pytest.raises(EveOnlineAuthenticationError):
                await client.async_get_character_location(CHARACTER_ID)

    @pytest.mark.asyncio
    async def test_ship_without_auth_raises(self):
        """Calling ship endpoint without auth raises error."""
        async with aiohttp.ClientSession() as session:
            client = EveOnlineClient(session=session)
            with pytest.raises(EveOnlineAuthenticationError):
                await client.async_get_character_ship(CHARACTER_ID)

    @pytest.mark.asyncio
    async def test_skill_queue_without_auth_raises(self):
        """Calling skill queue endpoint without auth raises error."""
        async with aiohttp.ClientSession() as session:
            client = EveOnlineClient(session=session)
            with pytest.raises(EveOnlineAuthenticationError):
                await client.async_get_skill_queue(CHARACTER_ID)


class TestCharacterOnline:
    """Test GET /characters/{character_id}/online/ endpoint."""

    @pytest.mark.asyncio
    async def test_get_online_status_success(self, character_online_data):
        """Successful online status fetch."""
        with aioresponses() as mocked:
            mocked.get(
                f"{ESI_BASE_URL}/characters/{CHARACTER_ID}/online/?datasource=tranquility",
                payload=character_online_data,
            )
            async with aiohttp.ClientSession() as session:
                auth = MockAuth(session)
                client = EveOnlineClient(auth=auth)
                status = await client.async_get_character_online(CHARACTER_ID)

        assert isinstance(status, CharacterOnlineStatus)
        assert status.online is True
        assert status.last_login == datetime(2026, 3, 26, 10, 0, tzinfo=UTC)
        assert status.last_logout == datetime(2026, 3, 25, 22, 0, tzinfo=UTC)
        assert status.logins == 1542

    @pytest.mark.asyncio
    async def test_get_online_status_offline(self):
        """Character that is offline."""
        data = {
            "online": False,
            "last_login": "2026-03-20T10:00:00Z",
            "last_logout": "2026-03-20T12:00:00Z",
            "logins": 500,
        }
        with aioresponses() as mocked:
            mocked.get(
                f"{ESI_BASE_URL}/characters/{CHARACTER_ID}/online/?datasource=tranquility",
                payload=data,
            )
            async with aiohttp.ClientSession() as session:
                auth = MockAuth(session)
                client = EveOnlineClient(auth=auth)
                status = await client.async_get_character_online(CHARACTER_ID)

        assert status.online is False

    @pytest.mark.asyncio
    async def test_get_online_status_forbidden(self):
        """HTTP 403 raises EveOnlineAuthenticationError."""
        with aioresponses() as mocked:
            mocked.get(
                f"{ESI_BASE_URL}/characters/{CHARACTER_ID}/online/?datasource=tranquility",
                status=403,
                body='{"error": "token is not valid for scope"}',
            )
            async with aiohttp.ClientSession() as session:
                auth = MockAuth(session)
                client = EveOnlineClient(auth=auth)
                with pytest.raises(EveOnlineAuthenticationError, match="403"):
                    await client.async_get_character_online(CHARACTER_ID)

    @pytest.mark.asyncio
    async def test_get_online_status_unauthorized(self):
        """HTTP 401 raises EveOnlineAuthenticationError."""
        with aioresponses() as mocked:
            mocked.get(
                f"{ESI_BASE_URL}/characters/{CHARACTER_ID}/online/?datasource=tranquility",
                status=401,
                body='{"error": "token expired"}',
            )
            async with aiohttp.ClientSession() as session:
                auth = MockAuth(session)
                client = EveOnlineClient(auth=auth)
                with pytest.raises(EveOnlineAuthenticationError, match="401"):
                    await client.async_get_character_online(CHARACTER_ID)


class TestCharacterLocation:
    """Test GET /characters/{character_id}/location/ endpoint."""

    @pytest.mark.asyncio
    async def test_get_location_success(self, character_location_data):
        """Successful location fetch with station."""
        with aioresponses() as mocked:
            mocked.get(
                f"{ESI_BASE_URL}/characters/{CHARACTER_ID}/location/?datasource=tranquility",
                payload=character_location_data,
            )
            async with aiohttp.ClientSession() as session:
                auth = MockAuth(session)
                client = EveOnlineClient(auth=auth)
                location = await client.async_get_character_location(CHARACTER_ID)

        assert isinstance(location, CharacterLocation)
        assert location.solar_system_id == 30002187
        assert location.station_id == 60003760
        assert location.structure_id is None

    @pytest.mark.asyncio
    async def test_get_location_in_space(self):
        """Location when character is floating in space (no station/structure)."""
        data = {"solar_system_id": 30000142}
        with aioresponses() as mocked:
            mocked.get(
                f"{ESI_BASE_URL}/characters/{CHARACTER_ID}/location/?datasource=tranquility",
                payload=data,
            )
            async with aiohttp.ClientSession() as session:
                auth = MockAuth(session)
                client = EveOnlineClient(auth=auth)
                location = await client.async_get_character_location(CHARACTER_ID)

        assert location.solar_system_id == 30000142
        assert location.station_id is None
        assert location.structure_id is None

    @pytest.mark.asyncio
    async def test_get_location_in_citadel(self):
        """Location when character is in a player structure."""
        data = {
            "solar_system_id": 30002187,
            "structure_id": 1035466617946,
        }
        with aioresponses() as mocked:
            mocked.get(
                f"{ESI_BASE_URL}/characters/{CHARACTER_ID}/location/?datasource=tranquility",
                payload=data,
            )
            async with aiohttp.ClientSession() as session:
                auth = MockAuth(session)
                client = EveOnlineClient(auth=auth)
                location = await client.async_get_character_location(CHARACTER_ID)

        assert location.structure_id == 1035466617946
        assert location.station_id is None


class TestCharacterShip:
    """Test GET /characters/{character_id}/ship/ endpoint."""

    @pytest.mark.asyncio
    async def test_get_ship_success(self, character_ship_data):
        """Successful ship fetch."""
        with aioresponses() as mocked:
            mocked.get(
                f"{ESI_BASE_URL}/characters/{CHARACTER_ID}/ship/?datasource=tranquility",
                payload=character_ship_data,
            )
            async with aiohttp.ClientSession() as session:
                auth = MockAuth(session)
                client = EveOnlineClient(auth=auth)
                ship = await client.async_get_character_ship(CHARACTER_ID)

        assert isinstance(ship, CharacterShip)
        assert ship.ship_type_id == 587
        assert ship.ship_item_id == 1000000016991
        assert ship.ship_name == "Armageddon's Rage"


class TestWalletBalance:
    """Test GET /characters/{character_id}/wallet/ endpoint."""

    @pytest.mark.asyncio
    async def test_get_wallet_balance_success(self, wallet_balance_data):
        """Successful wallet balance fetch."""
        with aioresponses() as mocked:
            mocked.get(
                f"{ESI_BASE_URL}/characters/{CHARACTER_ID}/wallet/?datasource=tranquility",
                payload=wallet_balance_data,
            )
            async with aiohttp.ClientSession() as session:
                auth = MockAuth(session)
                client = EveOnlineClient(auth=auth)
                wallet = await client.async_get_wallet_balance(CHARACTER_ID)

        assert isinstance(wallet, WalletBalance)
        assert wallet.balance == 1234567890.12

    @pytest.mark.asyncio
    async def test_get_wallet_balance_zero(self):
        """Wallet with zero balance."""
        with aioresponses() as mocked:
            mocked.get(
                f"{ESI_BASE_URL}/characters/{CHARACTER_ID}/wallet/?datasource=tranquility",
                payload=0.0,
            )
            async with aiohttp.ClientSession() as session:
                auth = MockAuth(session)
                client = EveOnlineClient(auth=auth)
                wallet = await client.async_get_wallet_balance(CHARACTER_ID)

        assert wallet.balance == 0.0


class TestSkillQueue:
    """Test GET /characters/{character_id}/skillqueue/ endpoint."""

    @pytest.mark.asyncio
    async def test_get_skill_queue_success(self, skill_queue_data):
        """Successful skill queue fetch with multiple entries."""
        with aioresponses() as mocked:
            mocked.get(
                f"{ESI_BASE_URL}/characters/{CHARACTER_ID}/skillqueue/?datasource=tranquility",
                payload=skill_queue_data,
            )
            async with aiohttp.ClientSession() as session:
                auth = MockAuth(session)
                client = EveOnlineClient(auth=auth)
                queue = await client.async_get_skill_queue(CHARACTER_ID)

        assert len(queue) == 2
        assert all(isinstance(entry, SkillQueueEntry) for entry in queue)

        first = queue[0]
        assert first.skill_id == 3435
        assert first.queue_position == 0
        assert first.finished_level == 5
        assert first.start_date == datetime(2026, 3, 20, 10, 0, tzinfo=UTC)
        assert first.finish_date == datetime(2026, 4, 1, 15, 30, tzinfo=UTC)
        assert first.training_start_sp == 45255
        assert first.level_end_sp == 256000

        second = queue[1]
        assert second.skill_id == 3413
        assert second.queue_position == 1
        assert second.finished_level == 4

    @pytest.mark.asyncio
    async def test_get_skill_queue_empty(self):
        """Empty skill queue returns empty list."""
        with aioresponses() as mocked:
            mocked.get(
                f"{ESI_BASE_URL}/characters/{CHARACTER_ID}/skillqueue/?datasource=tranquility",
                payload=[],
            )
            async with aiohttp.ClientSession() as session:
                auth = MockAuth(session)
                client = EveOnlineClient(auth=auth)
                queue = await client.async_get_skill_queue(CHARACTER_ID)

        assert queue == []

    @pytest.mark.asyncio
    async def test_get_skill_queue_paused(self):
        """Skill queue with paused entry (no finish_date)."""
        data = [
            {
                "skill_id": 3435,
                "queue_position": 0,
                "finished_level": 5,
            }
        ]
        with aioresponses() as mocked:
            mocked.get(
                f"{ESI_BASE_URL}/characters/{CHARACTER_ID}/skillqueue/?datasource=tranquility",
                payload=data,
            )
            async with aiohttp.ClientSession() as session:
                auth = MockAuth(session)
                client = EveOnlineClient(auth=auth)
                queue = await client.async_get_skill_queue(CHARACTER_ID)

        assert len(queue) == 1
        assert queue[0].start_date is None
        assert queue[0].finish_date is None
        assert queue[0].training_start_sp is None

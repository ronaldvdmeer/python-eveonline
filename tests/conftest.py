"""Common test fixtures and mock data for Eve Online ESI client tests."""

from __future__ import annotations

from unittest.mock import AsyncMock

import aiohttp
import pytest

from eveonline.auth import AbstractAuth


class MockAuth(AbstractAuth):
    """Concrete auth implementation for testing."""

    def __init__(self, websession: aiohttp.ClientSession, token: str = "mock-token") -> None:
        """Initialize mock auth."""
        super().__init__(websession)
        self._token = token

    async def async_get_access_token(self) -> str:
        """Return a mock access token."""
        return self._token


@pytest.fixture
def mock_session():
    """Create a mock aiohttp ClientSession."""
    session = AsyncMock(spec=aiohttp.ClientSession)
    return session


@pytest.fixture
def mock_auth(mock_session):
    """Create a MockAuth instance with a mock session."""
    return MockAuth(mock_session, token="test-access-token-12345")


# ---------------------------------------------------------------------------
# ESI API mock response data
# ---------------------------------------------------------------------------


@pytest.fixture
def server_status_data():
    """Mock response for GET /status/."""
    return {
        "players": 23451,
        "server_version": "2345678",
        "start_time": "2026-03-26T11:00:00Z",
        "vip": False,
    }


@pytest.fixture
def character_public_data():
    """Mock response for GET /characters/{character_id}/."""
    return {
        "name": "CCP Bartender",
        "corporation_id": 98000001,
        "birthday": "2015-03-24T11:37:00Z",
        "gender": "male",
        "race_id": 2,
        "bloodline_id": 4,
        "ancestry_id": 12,
        "alliance_id": 99000001,
        "description": "A test character",
        "security_status": 1.8,
        "title": "Test Title",
    }


@pytest.fixture
def character_portrait_data():
    """Mock response for GET /characters/{character_id}/portrait/."""
    return {
        "px64x64": "https://images.evetech.net/characters/2113024536/portrait?size=64",
        "px128x128": "https://images.evetech.net/characters/2113024536/portrait?size=128",
        "px256x256": "https://images.evetech.net/characters/2113024536/portrait?size=256",
        "px512x512": "https://images.evetech.net/characters/2113024536/portrait?size=512",
    }


@pytest.fixture
def corporation_public_data():
    """Mock response for GET /corporations/{corporation_id}/."""
    return {
        "name": "C C P",
        "ticker": "CCP",
        "member_count": 256,
        "ceo_id": 2113024536,
        "tax_rate": 0.1,
        "alliance_id": 99000001,
        "description": "The developers",
        "date_founded": "2003-05-06T12:00:00Z",
        "url": "https://www.eveonline.com",
    }


@pytest.fixture
def universe_names_data():
    """Mock response for POST /universe/names/."""
    return [
        {"id": 98000001, "name": "C C P", "category": "corporation"},
        {"id": 2113024536, "name": "CCP Bartender", "category": "character"},
    ]


@pytest.fixture
def character_online_data():
    """Mock response for GET /characters/{character_id}/online/."""
    return {
        "online": True,
        "last_login": "2026-03-26T10:00:00Z",
        "last_logout": "2026-03-25T22:00:00Z",
        "logins": 1542,
    }


@pytest.fixture
def character_location_data():
    """Mock response for GET /characters/{character_id}/location/."""
    return {
        "solar_system_id": 30002187,
        "station_id": 60003760,
    }


@pytest.fixture
def character_ship_data():
    """Mock response for GET /characters/{character_id}/ship/."""
    return {
        "ship_type_id": 587,
        "ship_item_id": 1000000016991,
        "ship_name": "Armageddon's Rage",
    }


@pytest.fixture
def wallet_balance_data():
    """Mock response for GET /characters/{character_id}/wallet/."""
    return 1234567890.12


@pytest.fixture
def skill_queue_data():
    """Mock response for GET /characters/{character_id}/skillqueue/."""
    return [
        {
            "skill_id": 3435,
            "queue_position": 0,
            "finished_level": 5,
            "start_date": "2026-03-20T10:00:00Z",
            "finish_date": "2026-04-01T15:30:00Z",
            "training_start_sp": 45255,
            "level_start_sp": 45255,
            "level_end_sp": 256000,
        },
        {
            "skill_id": 3413,
            "queue_position": 1,
            "finished_level": 4,
            "start_date": "2026-04-01T15:30:00Z",
            "finish_date": "2026-04-05T08:00:00Z",
            "training_start_sp": 8000,
            "level_start_sp": 8000,
            "level_end_sp": 45255,
        },
    ]

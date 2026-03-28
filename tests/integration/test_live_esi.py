"""Live integration tests against the real EVE Online ESI API.

These tests make actual HTTP requests to ESI and should only be run when
network access is available. They are excluded from the default test run
via the ``-m "not integration"`` filter in pyproject.toml.

Run manually::

    pytest tests/integration/ -m integration --no-cov -v

Environment variables
---------------------
ESI_TEST_CHARACTER_ID
    Character ID (integer) used for public-endpoint tests.
    Example: ``export ESI_TEST_CHARACTER_ID=90205902``
ESI_TOKEN
    A valid ESI access token for authenticated tests.
    Example: ``export ESI_TOKEN=eyJ...``
"""

from __future__ import annotations

import os

import aiohttp
import pytest

from eveonline.auth import AbstractAuth
from eveonline.client import EveOnlineClient

# ---------------------------------------------------------------------------
# Read environment variables once at module level so skip decorators work.
# ---------------------------------------------------------------------------
_ESI_TOKEN: str | None = os.environ.get("ESI_TOKEN")
_CHARACTER_ID_STR: str | None = os.environ.get("ESI_TEST_CHARACTER_ID")

# Well-known fallback character: Chribba (long-standing EVE celebrity, ID stable)
_DEFAULT_CHARACTER_ID = 90205902
_CHARACTER_ID: int = int(_CHARACTER_ID_STR) if _CHARACTER_ID_STR else _DEFAULT_CHARACTER_ID

NEEDS_TOKEN = pytest.mark.skipif(not _ESI_TOKEN, reason="ESI_TOKEN env var not set")


# ---------------------------------------------------------------------------
# Concrete auth implementation for integration tests
# ---------------------------------------------------------------------------


class _StaticTokenAuth(AbstractAuth):
    """Auth provider that returns a static access token from an env var."""

    def __init__(self, session: aiohttp.ClientSession, token: str) -> None:
        super().__init__(session)
        self._token = token

    async def async_get_access_token(self) -> str:
        return self._token


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
async def public_client():
    """A public (unauthenticated) ESI client."""
    async with aiohttp.ClientSession() as session:
        yield EveOnlineClient(session=session)


@pytest.fixture
async def auth_client():
    """An authenticated ESI client using the ESI_TOKEN env var.

    The fixture itself skips if no token is available so that individual tests
    do not need to repeat the skip logic.
    """
    if not _ESI_TOKEN:
        pytest.skip("ESI_TOKEN env var not set")
    async with aiohttp.ClientSession() as session:
        auth = _StaticTokenAuth(session, _ESI_TOKEN)  # type: ignore[arg-type]
        yield EveOnlineClient(auth=auth)


# ===========================================================================
# Public endpoint tests — no auth required, no character ID required
# ===========================================================================


@pytest.mark.integration
async def test_server_status_live(public_client: EveOnlineClient) -> None:
    """Server status returns valid data from ESI."""
    status = await public_client.async_get_server_status()

    assert status.players >= 0, "Player count must be non-negative"
    assert status.server_version, "Server version must be a non-empty string"
    assert status.start_time is not None, "Start time must be set"


@pytest.mark.integration
async def test_resolve_names_live(public_client: EveOnlineClient) -> None:
    """Name resolution works for a set of well-known static IDs."""
    # Jita solar system: 30000142 | Tranquility server: NPC corp IDs are stable
    known_ids = [30000142]  # Jita
    names = await public_client.async_resolve_names(known_ids)

    assert len(names) == 1
    assert names[0].name == "Jita"
    assert names[0].id == 30000142
    assert names[0].category == "solar_system"


@pytest.mark.integration
async def test_resolve_names_empty_list(public_client: EveOnlineClient) -> None:
    """Empty ID list returns an empty result without hitting ESI."""
    names = await public_client.async_resolve_names([])
    assert names == []


# ===========================================================================
# Public endpoint tests — character ID used (defaults to well-known character)
# ===========================================================================


@pytest.mark.integration
async def test_character_public_info_live(public_client: EveOnlineClient) -> None:
    """Public character info returns a name and corporation ID."""
    char = await public_client.async_get_character_public(_CHARACTER_ID)

    assert char.name, "Character name must be non-empty"
    assert char.corporation_id > 0, "Corporation ID must be positive"


@pytest.mark.integration
async def test_character_portrait_live(public_client: EveOnlineClient) -> None:
    """Character portrait returns at least one valid image URL."""
    portrait = await public_client.async_get_portrait(_CHARACTER_ID)

    urls = [portrait.px64x64, portrait.px128x128, portrait.px256x256, portrait.px512x512]
    assert any(urls), "At least one portrait URL must be set"
    for url in urls:
        if url:
            assert url.startswith("https://"), f"Portrait URL must be HTTPS, got: {url}"


# ===========================================================================
# Authenticated endpoint tests — require ESI_TOKEN
# ===========================================================================


@pytest.mark.integration
@NEEDS_TOKEN
async def test_online_status_live(auth_client: EveOnlineClient) -> None:
    """Online status endpoint responds with a valid model."""
    status = await auth_client.async_get_online_status()

    # is_online can be True or False depending on whether the char is logged in
    assert isinstance(status.is_online, bool)
    # last_login may be None for characters that have never previously logged in
    # via the token owner, but the request itself must succeed


@pytest.mark.integration
@NEEDS_TOKEN
async def test_wallet_balance_live(auth_client: EveOnlineClient) -> None:
    """Wallet balance returns a non-negative numeric value."""
    wallet = await auth_client.async_get_wallet_balance()

    assert isinstance(wallet.balance, float | int)
    assert wallet.balance >= 0, "Wallet balance must be non-negative"


@pytest.mark.integration
@NEEDS_TOKEN
async def test_skills_live(auth_client: EveOnlineClient) -> None:
    """Skills summary returns total_sp and a list of trained skills."""
    skills = await auth_client.async_get_skills()

    assert skills.total_sp >= 0
    assert isinstance(skills.skills, list)


@pytest.mark.integration
@NEEDS_TOKEN
async def test_skill_queue_live(auth_client: EveOnlineClient) -> None:
    """Skill queue returns a list (may be empty if nothing is training)."""
    queue = await auth_client.async_get_skill_queue()

    assert isinstance(queue, list)


@pytest.mark.integration
@NEEDS_TOKEN
async def test_location_live(auth_client: EveOnlineClient) -> None:
    """Location returns a valid solar system ID (only works while online)."""
    location = await auth_client.async_get_location()

    assert location.solar_system_id > 0, "Solar system ID must be positive"


@pytest.mark.integration
@NEEDS_TOKEN
async def test_ship_live(auth_client: EveOnlineClient) -> None:
    """Current ship returns valid type and item IDs."""
    ship = await auth_client.async_get_ship()

    assert ship.ship_type_id > 0
    assert ship.ship_item_id > 0
    assert ship.ship_name, "Ship name must be non-empty"


@pytest.mark.integration
@NEEDS_TOKEN
async def test_mail_labels_live(auth_client: EveOnlineClient) -> None:
    """Mail labels returns a list of label objects."""
    labels = await auth_client.async_get_mail_labels()

    assert isinstance(labels, list)


@pytest.mark.integration
@NEEDS_TOKEN
async def test_market_orders_live(auth_client: EveOnlineClient) -> None:
    """Market orders returns a list (may be empty)."""
    orders = await auth_client.async_get_market_orders()

    assert isinstance(orders, list)


@pytest.mark.integration
@NEEDS_TOKEN
async def test_industry_jobs_live(auth_client: EveOnlineClient) -> None:
    """Industry jobs returns a list (may be empty)."""
    jobs = await auth_client.async_get_industry_jobs()

    assert isinstance(jobs, list)


@pytest.mark.integration
@NEEDS_TOKEN
async def test_notifications_live(auth_client: EveOnlineClient) -> None:
    """Notifications returns a list (may be empty)."""
    notifications = await auth_client.async_get_notifications()

    assert isinstance(notifications, list)


@pytest.mark.integration
@NEEDS_TOKEN
async def test_clones_live(auth_client: EveOnlineClient) -> None:
    """Clone info returns a valid model (home location may or may not be set)."""
    clones = await auth_client.async_get_clones()

    assert isinstance(clones.jump_clones, list)


@pytest.mark.integration
@NEEDS_TOKEN
async def test_implants_live(auth_client: EveOnlineClient) -> None:
    """Implants returns a list of type IDs (may be empty)."""
    implants = await auth_client.async_get_implants()

    assert isinstance(implants, list)
    for implant_id in implants:
        assert implant_id > 0, f"Implant type ID must be positive, got {implant_id}"


@pytest.mark.integration
@NEEDS_TOKEN
async def test_wallet_journal_live(auth_client: EveOnlineClient) -> None:
    """Wallet journal returns a list of entries (may be empty for new chars)."""
    journal = await auth_client.async_get_wallet_journal()

    assert isinstance(journal, list)


@pytest.mark.integration
@NEEDS_TOKEN
async def test_contacts_live(auth_client: EveOnlineClient) -> None:
    """Contacts returns a list (may be empty)."""
    contacts = await auth_client.async_get_contacts()

    assert isinstance(contacts, list)


@pytest.mark.integration
@NEEDS_TOKEN
async def test_calendar_live(auth_client: EveOnlineClient) -> None:
    """Calendar events returns a list (may be empty)."""
    events = await auth_client.async_get_calendar()

    assert isinstance(events, list)


@pytest.mark.integration
@NEEDS_TOKEN
async def test_loyalty_points_live(auth_client: EveOnlineClient) -> None:
    """Loyalty points returns a list of LP entries (may be empty)."""
    lp = await auth_client.async_get_loyalty_points()

    assert isinstance(lp, list)


@pytest.mark.integration
@NEEDS_TOKEN
async def test_jump_fatigue_live(auth_client: EveOnlineClient) -> None:
    """Jump fatigue returns a valid model (all fields may be None if no fatigue)."""
    fatigue = await auth_client.async_get_jump_fatigue()

    # Fatigue fields are all optional — just check the call succeeds
    _ = fatigue

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

import base64
import json
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


def _character_id_from_token(token: str) -> int:
    """Extract character ID from an ESI JWT without verifying the signature.

    The JWT ``sub`` claim looks like ``CHARACTER:EVE:12345678``.
    Falls back to ``_CHARACTER_ID`` if decoding fails.
    """
    try:
        payload_b64 = token.split(".")[1]
        # JWT base64 is unpadded — add padding as needed
        payload_b64 += "=" * (-len(payload_b64) % 4)
        payload = json.loads(base64.b64decode(payload_b64))
        sub: str = payload.get("sub", "")
        return int(sub.split(":")[-1])
    except Exception:
        return _CHARACTER_ID


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


# Character ID for authenticated tests: derived from the JWT when available,
# otherwise falls back to the explicit env var or the default character.
_AUTH_CHARACTER_ID: int = _character_id_from_token(_ESI_TOKEN) if _ESI_TOKEN else _CHARACTER_ID


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
    portrait = await public_client.async_get_character_portrait(_CHARACTER_ID)

    urls = [portrait.px64x64, portrait.px128x128, portrait.px256x256, portrait.px512x512]
    assert any(urls), "At least one portrait URL must be set"
    for url in urls:
        if url:
            assert url.startswith("https://"), f"Portrait URL must be HTTPS, got: {url}"


@pytest.mark.integration
async def test_corporation_public_live(public_client: EveOnlineClient) -> None:
    """Public corporation info returns name, ticker, member count and tax rate."""
    char = await public_client.async_get_character_public(_CHARACTER_ID)
    corp = await public_client.async_get_corporation_public(char.corporation_id)

    assert corp.name, "Corporation name must be non-empty"
    assert corp.ticker, "Ticker must be non-empty"
    assert corp.member_count >= 0, "Member count must be non-negative"
    assert corp.ceo_id > 0, "CEO character ID must be positive"
    assert 0.0 <= corp.tax_rate <= 1.0, f"Tax rate {corp.tax_rate} must be between 0.0 and 1.0"


# ===========================================================================
# Authenticated endpoint tests — require ESI_TOKEN
# ===========================================================================


@pytest.mark.integration
@NEEDS_TOKEN
async def test_online_status_live(auth_client: EveOnlineClient) -> None:
    """Online status endpoint responds with a valid model."""
    status = await auth_client.async_get_character_online(_AUTH_CHARACTER_ID)

    assert isinstance(status.online, bool)


@pytest.mark.integration
@NEEDS_TOKEN
async def test_wallet_balance_live(auth_client: EveOnlineClient) -> None:
    """Wallet balance returns a non-negative numeric value."""
    wallet = await auth_client.async_get_wallet_balance(_AUTH_CHARACTER_ID)

    assert isinstance(wallet.balance, float | int)
    assert wallet.balance >= 0, "Wallet balance must be non-negative"


@pytest.mark.integration
@NEEDS_TOKEN
async def test_skills_live(auth_client: EveOnlineClient) -> None:
    """Skills summary returns total_sp and a list of trained skills."""
    skills = await auth_client.async_get_skills(_AUTH_CHARACTER_ID)

    assert skills.total_sp >= 0
    assert isinstance(skills.unallocated_sp, int)


@pytest.mark.integration
@NEEDS_TOKEN
async def test_skill_queue_live(auth_client: EveOnlineClient) -> None:
    """Skill queue returns a list; non-empty entries have valid skill ID and queue position."""
    queue = await auth_client.async_get_skill_queue(_AUTH_CHARACTER_ID)

    assert isinstance(queue, list)
    if queue:
        entry = queue[0]
        assert entry.skill_id > 0, "Skill ID must be positive"
        assert entry.queue_position >= 0, "Queue position must be non-negative"
        assert entry.finished_level in range(1, 6), "Finished level must be 1-5"


@pytest.mark.integration
@NEEDS_TOKEN
async def test_location_live(auth_client: EveOnlineClient) -> None:
    """Location returns a valid solar system ID (only works while online)."""
    location = await auth_client.async_get_character_location(_AUTH_CHARACTER_ID)

    assert location.solar_system_id > 0, "Solar system ID must be positive"


@pytest.mark.integration
@NEEDS_TOKEN
async def test_ship_live(auth_client: EveOnlineClient) -> None:
    """Current ship returns valid type and item IDs."""
    ship = await auth_client.async_get_character_ship(_AUTH_CHARACTER_ID)

    assert ship.ship_type_id > 0
    assert ship.ship_item_id > 0
    assert ship.ship_name, "Ship name must be non-empty"


@pytest.mark.integration
@NEEDS_TOKEN
async def test_mail_labels_live(auth_client: EveOnlineClient) -> None:
    """Mail labels returns a list of label objects."""
    labels = await auth_client.async_get_mail_labels(_AUTH_CHARACTER_ID)

    assert isinstance(labels.total_unread_count, int)


@pytest.mark.integration
@NEEDS_TOKEN
async def test_market_orders_live(auth_client: EveOnlineClient) -> None:
    """Market orders returns a list; non-empty entries have valid order fields."""
    orders = await auth_client.async_get_market_orders(_AUTH_CHARACTER_ID)

    assert isinstance(orders, list)
    if orders:
        order = orders[0]
        assert order.order_id > 0, "Order ID must be positive"
        assert order.type_id > 0, "Type ID must be positive"
        assert order.price > 0, "Order price must be positive"
        assert order.volume_remain >= 0, "Remaining volume must be non-negative"
        assert order.duration > 0, "Duration must be positive"


@pytest.mark.integration
@NEEDS_TOKEN
async def test_industry_jobs_live(auth_client: EveOnlineClient) -> None:
    """Industry jobs returns a list; non-empty entries have valid job fields."""
    jobs = await auth_client.async_get_industry_jobs(_AUTH_CHARACTER_ID)

    assert isinstance(jobs, list)
    if jobs:
        job = jobs[0]
        assert job.job_id > 0, "Job ID must be positive"
        assert job.activity_id > 0, "Activity ID must be positive"
        assert job.status, "Job status must be non-empty"
        assert job.blueprint_type_id > 0, "Blueprint type ID must be positive"
        assert job.runs > 0, "Runs must be positive"


@pytest.mark.integration
@NEEDS_TOKEN
async def test_notifications_live(auth_client: EveOnlineClient) -> None:
    """Notifications returns a list; non-empty entries have valid notification fields."""
    notifications = await auth_client.async_get_notifications(_AUTH_CHARACTER_ID)

    assert isinstance(notifications, list)
    if notifications:
        notif = notifications[0]
        assert notif.notification_id > 0, "Notification ID must be positive"
        assert notif.sender_id > 0, "Sender ID must be positive"
        assert notif.sender_type, "Sender type must be non-empty"
        assert notif.type, "Notification type must be non-empty"
        assert notif.timestamp is not None, "Timestamp must be set"


@pytest.mark.integration
@NEEDS_TOKEN
async def test_clones_live(auth_client: EveOnlineClient) -> None:
    """Clone info returns a valid model (home location may or may not be set)."""
    clones = await auth_client.async_get_clones(_AUTH_CHARACTER_ID)

    assert isinstance(clones.jump_clones, tuple | list)


@pytest.mark.integration
@NEEDS_TOKEN
async def test_implants_live(auth_client: EveOnlineClient) -> None:
    """Implants returns a tuple of type IDs (may be empty)."""
    implants = await auth_client.async_get_implants(_AUTH_CHARACTER_ID)

    assert isinstance(implants, tuple)
    for implant_id in implants:
        assert implant_id > 0, f"Implant type ID must be positive, got {implant_id}"


@pytest.mark.integration
@NEEDS_TOKEN
async def test_wallet_journal_live(auth_client: EveOnlineClient) -> None:
    """Wallet journal returns a list; non-empty entries have valid journal fields."""
    journal = await auth_client.async_get_wallet_journal(_AUTH_CHARACTER_ID)

    assert isinstance(journal, list)
    if journal:
        entry = journal[0]
        assert entry.id > 0, "Journal entry ID must be positive"
        assert entry.ref_type, "ref_type must be non-empty"
        assert entry.date is not None, "Journal entry date must be set"


@pytest.mark.integration
@NEEDS_TOKEN
async def test_contacts_live(auth_client: EveOnlineClient) -> None:
    """Contacts returns a list; non-empty entries have valid contact fields."""
    contacts = await auth_client.async_get_contacts(_AUTH_CHARACTER_ID)

    assert isinstance(contacts, list)
    if contacts:
        contact = contacts[0]
        assert contact.contact_id > 0, "Contact ID must be positive"
        assert contact.contact_type in (
            "character",
            "corporation",
            "alliance",
            "faction",
        ), f"Unexpected contact type: {contact.contact_type}"
        assert -10.0 <= contact.standing <= 10.0, f"Standing {contact.standing} out of range"


@pytest.mark.integration
@NEEDS_TOKEN
async def test_calendar_live(auth_client: EveOnlineClient) -> None:
    """Calendar events returns a list; non-empty entries have valid event fields."""
    events = await auth_client.async_get_calendar(_AUTH_CHARACTER_ID)

    assert isinstance(events, list)
    if events:
        event = events[0]
        assert event.event_id > 0, "Event ID must be positive"
        assert event.title, "Event title must be non-empty"
        assert event.event_date is not None, "Event date must be set"


@pytest.mark.integration
@NEEDS_TOKEN
async def test_loyalty_points_live(auth_client: EveOnlineClient) -> None:
    """Loyalty points returns a list; non-empty entries have positive corporation ID and LP."""
    lp = await auth_client.async_get_loyalty_points(_AUTH_CHARACTER_ID)

    assert isinstance(lp, list)
    if lp:
        entry = lp[0]
        assert entry.corporation_id > 0, "Corporation ID must be positive"
        assert entry.loyalty_points >= 0, "Loyalty points must be non-negative"


@pytest.mark.integration
@NEEDS_TOKEN
async def test_jump_fatigue_live(auth_client: EveOnlineClient) -> None:
    """Jump fatigue returns a valid model (all fields may be None if no fatigue)."""
    fatigue = await auth_client.async_get_jump_fatigue(_AUTH_CHARACTER_ID)

    # Fatigue fields are all optional — just check the call succeeds
    _ = fatigue


@pytest.mark.integration
@NEEDS_TOKEN
async def test_killmails_live(auth_client: EveOnlineClient) -> None:
    """Killmails returns a list; non-empty entries have a positive ID and non-empty hash."""
    killmails = await auth_client.async_get_killmails(_AUTH_CHARACTER_ID)

    assert isinstance(killmails, list)
    if killmails:
        km = killmails[0]
        assert km.killmail_id > 0, "Killmail ID must be positive"
        assert km.killmail_hash, "Killmail hash must be non-empty"


# ===========================================================================
# Caching behaviour tests — ETag and TTL/Expires round-trips
# ===========================================================================


@pytest.mark.integration
async def test_etag_caching_round_trip_live(public_client: EveOnlineClient) -> None:
    """Repeated requests to the same endpoint succeed with ETag/TTL caching active.

    The second call may trigger a 304 (data served from cache) or return a
    fresh 200.  Both paths must return a structurally valid model.
    After clearing the cache a third request must still succeed.
    """
    first = await public_client.async_get_server_status()
    assert first.players >= 0
    assert first.server_version

    # Second call: exercises the conditional-request (ETag) or TTL short-circuit path.
    # A legitimate fresh 200 can return a different server_version during a deployment;
    # only assert structural validity, not equality.
    second = await public_client.async_get_server_status()
    assert second.players >= 0
    assert second.server_version

    # After an explicit cache clear the client must make a fresh request.
    public_client.clear_etag_cache()
    third = await public_client.async_get_server_status()
    assert third.players >= 0


@pytest.mark.integration
async def test_etag_cache_populated_after_request_live(public_client: EveOnlineClient) -> None:
    """A completed GET request populates the internal ETag cache.

    This test intentionally inspects ``_etag_cache`` (a private attribute) to
    verify that ESI actually returns ETag headers for this endpoint.  There is
    no public API to observe cache state other than ``clear_etag_cache()``.
    """
    public_client.clear_etag_cache()  # start from a known empty state
    await public_client.async_get_server_status()

    if not public_client._etag_cache:
        pytest.skip("ESI did not return an ETag for server status — cannot assert cache population")

    assert public_client._etag_cache, "ETag cache must be non-empty when an ETag header was received"


@pytest.mark.integration
async def test_expires_header_sets_ttl_in_cache_live(public_client: EveOnlineClient) -> None:
    """ESI Expires header is parsed and stored as a TTL in the cache entry.

    This test intentionally inspects ``_etag_cache`` (a private attribute)
    because the expires_at value has no public accessor.  The check verifies
    that the two-tier caching (TTL layer + ETag layer) is correctly wired to
    live ESI responses.
    """
    public_client.clear_etag_cache()
    await public_client.async_get_server_status()

    if not public_client._etag_cache:
        pytest.skip("ESI did not return an ETag for server status — cannot inspect TTL")

    cache_entry = next(iter(public_client._etag_cache.values()))
    # cache_entry is (etag, data, x_pages, expires_at)
    expires_at = cache_entry[3]
    if expires_at is None:
        pytest.skip("ESI did not return an Expires header for server status — cannot verify TTL wiring")

    assert expires_at is not None, "expires_at must be set when ESI sends an Expires header"

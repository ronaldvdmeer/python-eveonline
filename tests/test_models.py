"""Tests for the data models."""

from __future__ import annotations

from datetime import UTC, datetime

from eveonline.models import (
    CharacterLocation,
    CharacterOnlineStatus,
    CharacterPortrait,
    CharacterPublicInfo,
    CharacterShip,
    CorporationPublicInfo,
    ServerStatus,
    SkillQueueEntry,
    UniverseName,
    WalletBalance,
)


class TestServerStatusModel:
    """Test ServerStatus dataclass."""

    def test_create_full(self):
        """Create with all fields."""
        status = ServerStatus(
            players=25000,
            server_version="123",
            start_time=datetime(2026, 1, 1, tzinfo=UTC),
            vip=False,
        )
        assert status.players == 25000
        assert status.server_version == "123"
        assert status.vip is False

    def test_create_minimal(self):
        """Create with only required fields."""
        status = ServerStatus(
            players=100,
            server_version="1",
            start_time=datetime(2026, 1, 1, tzinfo=UTC),
        )
        assert status.vip is None

    def test_frozen(self):
        """Dataclass is immutable."""
        status = ServerStatus(
            players=100,
            server_version="1",
            start_time=datetime(2026, 1, 1, tzinfo=UTC),
        )
        with __import__("pytest").raises(AttributeError):
            status.players = 200  # type: ignore[misc]


class TestCharacterPublicInfoModel:
    """Test CharacterPublicInfo dataclass."""

    def test_create_full(self):
        """Create with all fields populated."""
        char = CharacterPublicInfo(
            character_id=123,
            name="Test",
            corporation_id=456,
            birthday=datetime(2020, 1, 1, tzinfo=UTC),
            gender="male",
            race_id=1,
            bloodline_id=2,
            ancestry_id=3,
            alliance_id=789,
            faction_id=10,
            description="A character",
            title="CEO",
            security_status=5.0,
        )
        assert char.character_id == 123
        assert char.name == "Test"
        assert char.alliance_id == 789
        assert char.faction_id == 10

    def test_optional_fields_default_none(self):
        """Optional fields default to None."""
        char = CharacterPublicInfo(
            character_id=1,
            name="X",
            corporation_id=1,
            birthday=datetime(2020, 1, 1, tzinfo=UTC),
            gender="female",
            race_id=1,
            bloodline_id=1,
        )
        assert char.ancestry_id is None
        assert char.alliance_id is None
        assert char.faction_id is None
        assert char.description is None
        assert char.title is None
        assert char.security_status is None


class TestCharacterPortraitModel:
    """Test CharacterPortrait dataclass."""

    def test_all_sizes(self):
        """Portrait with all sizes."""
        p = CharacterPortrait(
            px64x64="url64",
            px128x128="url128",
            px256x256="url256",
            px512x512="url512",
        )
        assert p.px64x64 == "url64"
        assert p.px512x512 == "url512"

    def test_defaults_none(self):
        """All fields default to None."""
        p = CharacterPortrait()
        assert p.px64x64 is None
        assert p.px512x512 is None


class TestCorporationPublicInfoModel:
    """Test CorporationPublicInfo dataclass."""

    def test_create(self):
        """Create with all fields."""
        corp = CorporationPublicInfo(
            corporation_id=1,
            name="Corp",
            ticker="CRP",
            member_count=10,
            ceo_id=2,
            tax_rate=0.1,
            alliance_id=3,
            description="desc",
            date_founded=datetime(2003, 1, 1, tzinfo=UTC),
            url="https://example.com",
        )
        assert corp.ticker == "CRP"
        assert corp.tax_rate == 0.1


class TestCharacterOnlineStatusModel:
    """Test CharacterOnlineStatus dataclass."""

    def test_online(self):
        """Online character."""
        status = CharacterOnlineStatus(
            online=True,
            last_login=datetime(2026, 3, 26, tzinfo=UTC),
            logins=100,
        )
        assert status.online is True
        assert status.logins == 100

    def test_offline(self):
        """Offline character with minimal fields."""
        status = CharacterOnlineStatus(online=False)
        assert status.online is False
        assert status.last_login is None
        assert status.last_logout is None
        assert status.logins is None


class TestCharacterLocationModel:
    """Test CharacterLocation dataclass."""

    def test_in_station(self):
        """Character docked in a station."""
        loc = CharacterLocation(solar_system_id=30002187, station_id=60003760)
        assert loc.station_id == 60003760
        assert loc.structure_id is None

    def test_in_space(self):
        """Character floating in space."""
        loc = CharacterLocation(solar_system_id=30000142)
        assert loc.station_id is None
        assert loc.structure_id is None


class TestCharacterShipModel:
    """Test CharacterShip dataclass."""

    def test_create(self):
        """Create ship info."""
        ship = CharacterShip(
            ship_type_id=587,
            ship_item_id=1000000016991,
            ship_name="My Ship",
        )
        assert ship.ship_type_id == 587
        assert ship.ship_name == "My Ship"


class TestWalletBalanceModel:
    """Test WalletBalance dataclass."""

    def test_rich(self):
        """Character with ISK."""
        wallet = WalletBalance(balance=1_000_000_000.50)
        assert wallet.balance == 1_000_000_000.50

    def test_broke(self):
        """Character with zero ISK."""
        wallet = WalletBalance(balance=0.0)
        assert wallet.balance == 0.0


class TestSkillQueueEntryModel:
    """Test SkillQueueEntry dataclass."""

    def test_active(self):
        """Actively training skill."""
        entry = SkillQueueEntry(
            skill_id=3435,
            queue_position=0,
            finished_level=5,
            start_date=datetime(2026, 3, 20, tzinfo=UTC),
            finish_date=datetime(2026, 4, 1, tzinfo=UTC),
            training_start_sp=45255,
            level_start_sp=45255,
            level_end_sp=256000,
        )
        assert entry.skill_id == 3435
        assert entry.level_end_sp == 256000

    def test_paused(self):
        """Paused skill (no dates)."""
        entry = SkillQueueEntry(
            skill_id=100,
            queue_position=0,
            finished_level=3,
        )
        assert entry.start_date is None
        assert entry.finish_date is None
        assert entry.training_start_sp is None


class TestUniverseNameModel:
    """Test UniverseName dataclass."""

    def test_create(self):
        """Create resolved name."""
        name = UniverseName(id=98000001, name="C C P", category="corporation")
        assert name.id == 98000001
        assert name.name == "C C P"
        assert name.category == "corporation"

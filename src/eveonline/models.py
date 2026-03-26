"""Data models for the Eve Online ESI API."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ServerStatus:
    """EVE Online server (Tranquility) status."""

    players: int
    server_version: str
    start_time: datetime
    vip: bool | None = None


@dataclass(frozen=True)
class CharacterPublicInfo:
    """Public character information (no auth required)."""

    character_id: int
    name: str
    corporation_id: int
    birthday: datetime
    gender: str
    race_id: int
    bloodline_id: int
    ancestry_id: int | None = None
    alliance_id: int | None = None
    faction_id: int | None = None
    description: str | None = None
    title: str | None = None
    security_status: float | None = None


@dataclass(frozen=True)
class CharacterPortrait:
    """Character portrait URLs."""

    px64x64: str | None = None
    px128x128: str | None = None
    px256x256: str | None = None
    px512x512: str | None = None


@dataclass(frozen=True)
class CorporationPublicInfo:
    """Public corporation information (no auth required)."""

    corporation_id: int
    name: str
    ticker: str
    member_count: int
    ceo_id: int
    tax_rate: float
    alliance_id: int | None = None
    description: str | None = None
    date_founded: datetime | None = None
    url: str | None = None


@dataclass(frozen=True)
class CharacterOnlineStatus:
    """Character online status (requires auth)."""

    online: bool
    last_login: datetime | None = None
    last_logout: datetime | None = None
    logins: int | None = None


@dataclass(frozen=True)
class CharacterLocation:
    """Character current location (requires auth)."""

    solar_system_id: int
    station_id: int | None = None
    structure_id: int | None = None


@dataclass(frozen=True)
class CharacterShip:
    """Character current ship (requires auth)."""

    ship_type_id: int
    ship_item_id: int
    ship_name: str


@dataclass(frozen=True)
class WalletBalance:
    """Character wallet balance (requires auth)."""

    balance: float


@dataclass(frozen=True)
class SkillQueueEntry:
    """A single skill in the training queue (requires auth)."""

    skill_id: int
    queue_position: int
    finished_level: int
    start_date: datetime | None = None
    finish_date: datetime | None = None
    training_start_sp: int | None = None
    level_start_sp: int | None = None
    level_end_sp: int | None = None


@dataclass(frozen=True)
class UniverseName:
    """Resolved ID → name mapping."""

    id: int
    name: str
    category: str


@dataclass(frozen=True)
class CharacterSkillsSummary:
    """Character skills summary (requires auth)."""

    total_sp: int
    unallocated_sp: int


@dataclass(frozen=True)
class MailLabelsSummary:
    """Mail labels with unread count (requires auth)."""

    total_unread_count: int


@dataclass(frozen=True)
class IndustryJob:
    """An active industry job (requires auth)."""

    job_id: int
    activity_id: int
    status: str
    start_date: datetime
    end_date: datetime
    blueprint_type_id: int
    output_location_id: int
    runs: int
    product_type_id: int | None = None
    facility_id: int | None = None
    cost: float | None = None


@dataclass(frozen=True)
class MarketOrder:
    """A character's market order (requires auth)."""

    order_id: int
    type_id: int
    is_buy_order: bool
    price: float
    volume_remain: int
    volume_total: int
    location_id: int
    region_id: int
    issued: datetime
    duration: int
    range: str
    min_volume: int | None = None


@dataclass(frozen=True)
class JumpFatigue:
    """Character jump fatigue information (requires auth)."""

    jump_fatigue_expire_date: datetime | None = None
    last_jump_date: datetime | None = None
    last_update_date: datetime | None = None

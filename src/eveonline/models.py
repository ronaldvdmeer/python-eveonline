"""Data models for the Eve Online ESI API."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class ServerStatus:
    """EVE Online server (Tranquility) status.

    Attributes:
        players: Number of players currently online.
        server_version: Current server build version string.
        start_time: When the server was last started.
        vip: Whether VIP mode is enabled, or ``None`` if not reported.
    """

    players: int
    server_version: str
    start_time: datetime
    vip: bool | None = None


@dataclass(frozen=True, slots=True)
class CharacterPublicInfo:
    """Public character information (no auth required).

    Attributes:
        character_id: The EVE character ID.
        name: Character name.
        corporation_id: Current corporation ID.
        birthday: Character creation date.
        gender: ``"male"`` or ``"female"``.
        race_id: Numeric race identifier.
        bloodline_id: Numeric bloodline identifier.
        ancestry_id: Numeric ancestry identifier, if available.
        alliance_id: Alliance ID, if the corporation is in an alliance.
        faction_id: Faction ID, if enlisted in faction warfare.
        description: Character bio / description.
        title: Corporation title.
        security_status: Current security status.
    """

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


@dataclass(frozen=True, slots=True)
class CharacterPortrait:
    """Character portrait URLs.

    Attributes:
        px64x64: URL for the 64x64 portrait.
        px128x128: URL for the 128x128 portrait.
        px256x256: URL for the 256x256 portrait.
        px512x512: URL for the 512x512 portrait.
    """

    px64x64: str | None = None
    px128x128: str | None = None
    px256x256: str | None = None
    px512x512: str | None = None


@dataclass(frozen=True, slots=True)
class CorporationPublicInfo:
    """Public corporation information (no auth required).

    Attributes:
        corporation_id: The EVE corporation ID.
        name: Corporation name.
        ticker: Short ticker string (e.g. ``"CCP"``).
        member_count: Current number of members.
        ceo_id: Character ID of the CEO.
        tax_rate: Corporation tax rate (0.0-1.0).
        alliance_id: Alliance ID, if any.
        description: Corporation description.
        date_founded: Date the corporation was founded.
        url: Corporation website URL.
    """

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


@dataclass(frozen=True, slots=True)
class CharacterOnlineStatus:
    """Character online status (requires auth).

    Attributes:
        online: Whether the character is currently online.
        last_login: Timestamp of the last login.
        last_logout: Timestamp of the last logout.
        logins: Total number of logins.
    """

    online: bool
    last_login: datetime | None = None
    last_logout: datetime | None = None
    logins: int | None = None


@dataclass(frozen=True, slots=True)
class CharacterLocation:
    """Character current location (requires auth).

    Attributes:
        solar_system_id: Current solar system ID.
        station_id: NPC station ID, if docked.
        structure_id: Player structure ID, if docked.
    """

    solar_system_id: int
    station_id: int | None = None
    structure_id: int | None = None


@dataclass(frozen=True, slots=True)
class CharacterShip:
    """Character current ship (requires auth).

    Attributes:
        ship_type_id: Type ID of the ship.
        ship_item_id: Unique item ID of the specific ship.
        ship_name: Player-assigned name of the ship.
    """

    ship_type_id: int
    ship_item_id: int
    ship_name: str


@dataclass(frozen=True, slots=True)
class WalletBalance:
    """Character wallet balance (requires auth).

    Attributes:
        balance: ISK balance.
    """

    balance: float


@dataclass(frozen=True, slots=True)
class SkillQueueEntry:
    """A single skill in the training queue (requires auth).

    Attributes:
        skill_id: Type ID of the skill being trained.
        queue_position: Zero-based position in the queue.
        finished_level: The level being trained to.
        start_date: When training started.
        finish_date: Estimated completion time.
        training_start_sp: Skill points at training start.
        level_start_sp: Skill points at the beginning of this level.
        level_end_sp: Skill points required to finish this level.
    """

    skill_id: int
    queue_position: int
    finished_level: int
    start_date: datetime | None = None
    finish_date: datetime | None = None
    training_start_sp: int | None = None
    level_start_sp: int | None = None
    level_end_sp: int | None = None


@dataclass(frozen=True, slots=True)
class UniverseName:
    """Resolved ID → name mapping.

    Attributes:
        id: The EVE entity ID.
        name: Resolved display name.
        category: Entity category (e.g. ``"character"``, ``"corporation"``).
    """

    id: int
    name: str
    category: str


@dataclass(frozen=True, slots=True)
class CharacterSkillsSummary:
    """Character skills summary (requires auth).

    Attributes:
        total_sp: Total skill points earned.
        unallocated_sp: Unallocated (free) skill points.
    """

    total_sp: int
    unallocated_sp: int


@dataclass(frozen=True, slots=True)
class MailLabelsSummary:
    """Mail labels with unread count (requires auth).

    Attributes:
        total_unread_count: Total number of unread mail messages.
    """

    total_unread_count: int


@dataclass(frozen=True, slots=True)
class IndustryJob:
    """An active industry job (requires auth).

    Attributes:
        job_id: Unique job identifier.
        activity_id: Industry activity type (1=manufacturing, etc.).
        status: Job status string (``"active"``, ``"delivered"``, etc.).
        start_date: When the job was started.
        end_date: When the job will complete.
        blueprint_type_id: Type ID of the blueprint used.
        output_location_id: Location ID for the job output.
        runs: Number of runs.
        product_type_id: Type ID of the produced item, if applicable.
        facility_id: Facility ID where the job runs.
        cost: Installation cost in ISK.
    """

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


@dataclass(frozen=True, slots=True)
class MarketOrder:
    """A character's market order (requires auth).

    Attributes:
        order_id: Unique order identifier.
        type_id: Type ID of the item.
        is_buy_order: ``True`` for buy orders, ``False`` for sell.
        price: Price per unit in ISK.
        volume_remain: Units remaining.
        volume_total: Total units originally listed.
        location_id: Station or structure ID.
        region_id: Region the order is placed in.
        issued: When the order was created or last updated.
        duration: Order duration in days.
        range: Order range string (e.g. ``"region"``, ``"station"``).
        min_volume: Minimum purchase volume, if applicable.
    """

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


@dataclass(frozen=True, slots=True)
class JumpFatigue:
    """Character jump fatigue information (requires auth).

    Attributes:
        jump_fatigue_expire_date: When jump fatigue expires.
        last_jump_date: Timestamp of the last jump.
        last_update_date: When this data was last updated.
    """

    jump_fatigue_expire_date: datetime | None = None
    last_jump_date: datetime | None = None
    last_update_date: datetime | None = None


@dataclass(frozen=True, slots=True)
class CharacterNotification:
    """A character notification (requires auth).

    Attributes:
        notification_id: Unique notification identifier.
        sender_id: ID of the entity that sent the notification.
        sender_type: Sender category (``"character"``, ``"corporation"``, etc.).
        type: Notification type string (e.g. ``"StructureUnderAttack"``).
        timestamp: When the notification was sent.
        is_read: Whether the notification has been read.
        text: Notification body text (YAML-encoded by EVE).
    """

    notification_id: int
    sender_id: int
    sender_type: str
    type: str
    timestamp: datetime
    is_read: bool | None = None
    text: str | None = None


@dataclass(frozen=True, slots=True)
class JumpClone:
    """A single jump clone (part of CharacterClones).

    Attributes:
        jump_clone_id: Unique jump clone identifier.
        location_id: Station or structure ID where the clone is stored.
        location_type: ``"station"`` or ``"structure"``.
        implants: Type IDs of implants installed in this clone.
        name: Player-assigned name, if any.
    """

    jump_clone_id: int
    location_id: int
    location_type: str
    implants: tuple[int, ...]
    name: str | None = None


@dataclass(frozen=True, slots=True)
class CloneHomeLocation:
    """Home station / structure for clone bay (part of CharacterClones).

    Attributes:
        location_id: Station or structure ID.
        location_type: ``"station"`` or ``"structure"``.
    """

    location_id: int
    location_type: str


@dataclass(frozen=True, slots=True)
class CharacterClones:
    """Character clone information (requires auth).

    Attributes:
        home_location: Home station/structure for medical clone.
        jump_clones: List of jump clones.
        last_clone_jump_date: When the character last jumped clones.
        last_station_change_date: When the home station was last changed.
    """

    home_location: CloneHomeLocation | None
    jump_clones: tuple[JumpClone, ...]
    last_clone_jump_date: datetime | None = None
    last_station_change_date: datetime | None = None


@dataclass(frozen=True, slots=True)
class WalletJournalEntry:
    """A single wallet journal entry (requires auth).

    Attributes:
        id: Unique journal entry identifier.
        date: When the transaction occurred.
        ref_type: Reference type (e.g. ``"market_escrow"``, ``"bounty_prizes"``).
        description: Human-readable description.
        amount: ISK amount (positive = income, negative = expense).
        balance: ISK balance after this entry.
        first_party_id: ID of the first party involved.
        second_party_id: ID of the second party involved.
        reason: Additional reason text, if any.
    """

    id: int
    date: datetime
    ref_type: str
    description: str
    amount: float | None = None
    balance: float | None = None
    first_party_id: int | None = None
    second_party_id: int | None = None
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class CharacterContact:
    """A character contact entry (requires auth).

    Attributes:
        contact_id: ID of the contact (character, corp, alliance, or faction).
        contact_type: ``"character"``, ``"corporation"``, ``"alliance"``, or ``"faction"``.
        standing: Contact standing (-10.0 to +10.0).
        is_blocked: Whether the contact is blocked.
        is_watched: Whether the contact is on the watch list.
        label_ids: IDs of labels assigned to this contact.
    """

    contact_id: int
    contact_type: str
    standing: float
    is_blocked: bool | None = None
    is_watched: bool | None = None
    label_ids: tuple[int, ...] | None = None


@dataclass(frozen=True, slots=True)
class CalendarEvent:
    """An upcoming calendar event (requires auth).

    Attributes:
        event_id: Unique event identifier.
        event_date: When the event takes place.
        title: Event title.
        importance: 0 = normal, 1 = important.
        event_response: ``"not_responded"``, ``"accepted"``, ``"declined"``, or ``"tentative"``.
    """

    event_id: int
    event_date: datetime
    title: str
    importance: int | None = None
    event_response: str | None = None


@dataclass(frozen=True, slots=True)
class LoyaltyPoints:
    """Loyalty points for a single corporation (requires auth).

    Attributes:
        corporation_id: The corporation ID.
        loyalty_points: Number of LP accumulated.
    """

    corporation_id: int
    loyalty_points: int


@dataclass(frozen=True, slots=True)
class CharacterKillmail:
    """A killmail reference from a character's recent kill/loss history (requires auth).

    This represents a reference to a killmail, not the full killmail detail.
    Use the ``killmail_id`` and ``killmail_hash`` to fetch the full killmail
    from ``GET /killmails/{killmail_id}/{killmail_hash}/`` if needed.

    Attributes:
        killmail_id: Unique killmail identifier.
        killmail_hash: Hash string required to fetch the full killmail detail.
    """

    killmail_id: int
    killmail_hash: str

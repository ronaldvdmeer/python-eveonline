"""Async client for the Eve Online ESI API."""

from __future__ import annotations

import contextlib
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from typing import Any, overload

from aiohttp import ClientSession

from .auth import AbstractAuth
from .const import ESI_BASE_URL, ESI_DATASOURCE
from .exceptions import (
    EveOnlineAuthenticationError,
    EveOnlineConnectionError,
    EveOnlineError,
    EveOnlineNotFoundError,
    EveOnlineRateLimitError,
)
from .models import (
    CalendarEvent,
    CharacterClones,
    CharacterContact,
    CharacterKillmail,
    CharacterLocation,
    CharacterNotification,
    CharacterOnlineStatus,
    CharacterPortrait,
    CharacterPublicInfo,
    CharacterShip,
    CharacterSkillsSummary,
    CloneHomeLocation,
    CorporationPublicInfo,
    IndustryJob,
    JumpClone,
    JumpFatigue,
    LoyaltyPoints,
    MailLabelsSummary,
    MarketOrder,
    ServerStatus,
    SkillQueueEntry,
    UniverseName,
    WalletBalance,
    WalletJournalEntry,
)


class EveOnlineClient:
    """Async client for the Eve Online ESI API.

    This client supports two modes:

    1. **Unauthenticated**: For public endpoints (server status, character
       public info, corporation info, universe lookups). Only requires an
       aiohttp session.

    2. **Authenticated**: For character-specific endpoints (online status,
       wallet, location, skills). Requires an ``AbstractAuth`` implementation
       that provides access tokens.

    Example (unauthenticated)::

        async with aiohttp.ClientSession() as session:
            client = EveOnlineClient(session=session)
            status = await client.async_get_server_status()
            print(f"Players online: {status.players}")

    Example (authenticated)::

        auth = MyAuth(session)  # Your AbstractAuth implementation
        client = EveOnlineClient(auth=auth)
        online = await client.async_get_character_online(character_id)
        print(f"Online: {online.online}")
    """

    def __init__(
        self,
        session: ClientSession | None = None,
        auth: AbstractAuth | None = None,
        host: str = ESI_BASE_URL,
    ) -> None:
        """Initialize the client.

        Args:
            session: aiohttp session for unauthenticated requests.
                     If ``auth`` is provided, its session is used instead.
            auth: Authentication provider for authenticated endpoints.
            host: ESI API base URL. Defaults to the official ESI endpoint.
        """
        self._auth = auth
        self._host = host
        # ETag cache: maps cache_key -> (etag, cached_response_data, x_pages, expires_at)
        self._etag_cache: dict[str, tuple[str, Any, int, datetime | None]] = {}

        if auth is not None:
            self._session = auth.websession
        elif session is not None:
            self._session = session
        else:
            msg = "Either 'session' or 'auth' must be provided"
            raise EveOnlineError(msg)

    def clear_etag_cache(self) -> None:
        """Clear the ETag cache, forcing fresh responses on the next requests."""
        self._etag_cache.clear()

    # -------------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------------

    def _etag_key(self, path: str, params: dict[str, Any], authenticated: bool) -> str:
        """Build a deterministic cache key for an ESI endpoint.

        Args:
            path: API path relative to the ESI base URL.
            params: Query parameters (must already contain ``datasource``).
            authenticated: Whether the request uses OAuth.

        Returns:
            A string key unique to this endpoint + parameter combination.
        """
        sorted_params = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
        auth_prefix = "auth" if authenticated else "pub"
        return f"{auth_prefix}:{path}?{sorted_params}"

    def _build_etag_headers(self, method: str, cache_key: str) -> dict[str, str]:
        """Return an ``If-None-Match`` header dict if a cached ETag exists.

        Args:
            method: HTTP method (only ``"GET"`` uses ETags).
            cache_key: Cache key produced by :meth:`_etag_key`.

        Returns:
            A headers dict with ``If-None-Match`` set, or an empty dict.
        """
        if method == "GET" and cache_key in self._etag_cache:
            return {"If-None-Match": self._etag_cache[cache_key][0]}
        return {}

    def _store_etag(self, method: str, cache_key: str, response: Any, data: Any, *, x_pages: int = 1) -> None:
        """Cache the ETag and expiry from a successful GET response.

        Args:
            method: HTTP method (only ``"GET"`` responses are cached).
            cache_key: Cache key produced by :meth:`_etag_key`.
            response: The aiohttp response object.
            data: Parsed JSON data to cache alongside the ETag.
            x_pages: Total number of pages from the ``X-Pages`` header.
        """
        etag = response.headers.get("ETag")
        if method == "GET" and etag:
            self._etag_cache[cache_key] = (
                etag,
                data,
                x_pages,
                self._parse_expires(response),
            )

    @staticmethod
    def _parse_expires(response: Any) -> datetime | None:
        """Parse the ``Expires`` header into a timezone-aware datetime.

        Args:
            response: The aiohttp response object.

        Returns:
            A UTC-aware :class:`datetime` from the ``Expires`` header, or
            ``None`` if the header is absent or cannot be parsed.
        """
        if not (expires_str := response.headers.get("Expires")):
            return None
        with contextlib.suppress(TypeError, ValueError):
            parsed: datetime = parsedate_to_datetime(expires_str)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=UTC)
            return parsed
        return None

    @staticmethod
    def _parse_retry_after(response: Any) -> int | None:
        """Extract the Retry-After delay in seconds from a rate-limit response.

        Args:
            response: The aiohttp response object.

        Returns:
            The delay in seconds, or ``None`` if the header is absent or
            cannot be parsed as an integer.
        """
        if (retry_after := response.headers.get("Retry-After")) is None:
            return None
        try:
            return int(retry_after)
        except ValueError:
            return None

    def _get_fresh_cached(self, method: str, cache_key: str) -> tuple[Any, int] | None:
        """Return cached ``(data, x_pages)`` if the entry is still within its TTL.

        Args:
            method: HTTP method (only ``"GET"`` cache entries are considered).
            cache_key: Cache key produced by :meth:`_etag_key`.

        Returns:
            A ``(data, x_pages)`` tuple if a fresh cache entry exists,
            or ``None`` if the cache is empty, expired, or the method is not GET.
        """
        if method != "GET":
            return None
        cached = self._etag_cache.get(cache_key)
        if cached is None or cached[3] is None:
            return None
        if datetime.now(UTC) < cached[3]:
            return cached[1], cached[2]
        return None

    async def _finalize_response(self, method: str, cache_key: str, response: Any) -> tuple[Any, int]:
        """Parse the response JSON, store ETag/Expires, and return ``(data, x_pages)``.

        Args:
            method: HTTP method used for the request.
            cache_key: Cache key produced by :meth:`_etag_key`.
            response: The aiohttp response object for a successful 2xx GET.

        Returns:
            A ``(data, x_pages)`` tuple ready to be returned by the caller.
        """
        data = await response.json()
        try:
            x_pages = int(response.headers.get("X-Pages", "1"))
        except (TypeError, ValueError):
            x_pages = 1
        self._store_etag(method, cache_key, response, data, x_pages=x_pages)
        return data, x_pages

    async def _request_full(
        self, method: str, path: str, *, authenticated: bool = False, **kwargs: Any
    ) -> tuple[Any, int]:
        """Make a request to the ESI API and return the data with pagination info.

        Two caching layers are applied for GET requests:

        1. **TTL caching** — if a cache entry exists with an ``Expires`` value
           that has not passed, the cached data is returned immediately without
           making any HTTP request.
        2. **ETag caching** — when the TTL has expired (or no ``Expires`` was
           stored), a ``If-None-Match`` header is sent if a cached ETag exists.
           A ``304 Not Modified`` response returns the previously cached data
           without downloading a response body.

        Args:
            method: HTTP method.
            path: API path relative to ESI base URL.
            authenticated: Whether this request requires authentication.
            **kwargs: Additional arguments for the HTTP request.

        Returns:
            A ``(data, x_pages)`` tuple where *data* is the parsed JSON
            response and *x_pages* is the total number of pages from the
            ``X-Pages`` response header (``1`` if the header is absent).

        Raises:
            EveOnlineAuthenticationError: If auth is required but not provided,
                or if the token is invalid/expired.
            EveOnlineConnectionError: If the ESI API is unreachable.
            EveOnlineRateLimitError: If the rate limit is exceeded.
            EveOnlineNotFoundError: If the resource is not found.
            EveOnlineError: For other ESI API errors.
        """
        params: dict[str, Any] = dict(kwargs.pop("params", {}) or {})
        params.setdefault("datasource", ESI_DATASOURCE)
        cache_key = self._etag_key(path, params, authenticated)

        # Short-circuit if the cached data is still fresh (Expires not yet reached).
        if (fresh := self._get_fresh_cached(method, cache_key)) is not None:
            return fresh

        headers = {**dict(kwargs.pop("headers", {}) or {}), **self._build_etag_headers(method, cache_key)}

        try:
            if authenticated:
                if self._auth is None:
                    msg = "Authentication required but no auth provider configured"
                    raise EveOnlineAuthenticationError(msg)
                response = await self._auth.request(method, path, params=params, headers=headers, **kwargs)
            else:
                response = await self._session.request(
                    method,
                    f"{self._host}/{path}",
                    params=params,
                    headers=headers,
                    **kwargs,
                )
        except EveOnlineError:
            raise
        except Exception as err:
            msg = f"Failed to connect to ESI API: {err}"
            raise EveOnlineConnectionError(msg) from err

        if response.status in (401, 403):
            text = await response.text()
            msg = f"Authentication failed ({response.status}): {text}"
            raise EveOnlineAuthenticationError(msg)

        if response.status == 304:
            # Not Modified — return the data we cached earlier if it still exists.
            # Also refresh the Expires timestamp if the server sent an updated one.
            response.release()
            if (cached := self._etag_cache.get(cache_key)) is None:
                msg = (
                    f"Received 304 Not Modified from ESI, but no matching ETag "
                    f"cache entry exists for key {cache_key!r}."
                )
                raise EveOnlineError(msg)
            expires_at = self._parse_expires(response) or cached[3]
            self._etag_cache[cache_key] = (cached[0], cached[1], cached[2], expires_at)
            return cached[1], cached[2]

        if response.status == 404:
            response.release()
            msg = f"Resource not found: {path}"
            raise EveOnlineNotFoundError(msg)

        if response.status in (420, 429):
            response.release()
            raise EveOnlineRateLimitError(retry_after=self._parse_retry_after(response))

        if response.status >= 400:
            text = await response.text()
            msg = f"ESI API error ({response.status}): {text}"
            raise EveOnlineError(msg)

        return await self._finalize_response(method, cache_key, response)

    async def _request(self, method: str, path: str, *, authenticated: bool = False, **kwargs: Any) -> Any:
        """Make a request to the ESI API.

        Thin wrapper around :meth:`_request_full` that discards pagination
        metadata. Use for non-paginated endpoints.

        Args:
            method: HTTP method.
            path: API path relative to ESI base URL.
            authenticated: Whether this request requires authentication.
            **kwargs: Additional arguments for the HTTP request.

        Returns:
            Parsed JSON response.
        """
        data, _ = await self._request_full(method, path, authenticated=authenticated, **kwargs)
        return data

    async def _request_all_pages(self, path: str, *, authenticated: bool = False, **kwargs: Any) -> list[Any]:
        """Fetch all pages of a paginated ESI GET endpoint.

        Sends ``?page=1``, reads the ``X-Pages`` response header to determine
        the total page count, then fetches any remaining pages sequentially.
        Results from all pages are combined into a single flat list.

        Args:
            path: API path relative to ESI base URL.
            authenticated: Whether this request requires authentication.
            **kwargs: Additional arguments forwarded to each page request.

        Returns:
            A flat list containing the combined JSON objects from all pages.
        """
        base_params: dict[str, Any] = dict(kwargs.pop("params", {}) or {})

        page1_data, total_pages = await self._request_full(
            "GET", path, authenticated=authenticated, params={**base_params, "page": 1}, **kwargs
        )
        all_data: list[Any] = list(page1_data)

        for page in range(2, total_pages + 1):
            page_data, _ = await self._request_full(
                "GET", path, authenticated=authenticated, params={**base_params, "page": page}, **kwargs
            )
            all_data.extend(page_data)

        return all_data

    @staticmethod
    @overload
    def _parse_datetime(value: str) -> datetime: ...

    @staticmethod
    @overload
    def _parse_datetime(value: None) -> None: ...

    @staticmethod
    @overload
    def _parse_datetime(value: str | None) -> datetime | None: ...

    @staticmethod
    def _parse_datetime(value: str | None) -> datetime | None:
        """Parse an ISO 8601 datetime string from ESI.

        Args:
            value: An ISO 8601 string (e.g. ``"2025-01-15T12:34:56Z"``) or
                ``None``.

        Returns:
            A :class:`~datetime.datetime` when *value* is a string, or
            ``None`` when *value* is ``None``.
        """
        if value is None:
            return None
        return datetime.fromisoformat(value)

    # -------------------------------------------------------------------------
    # Public endpoints (no auth required)
    # -------------------------------------------------------------------------

    async def async_get_server_status(self) -> ServerStatus:
        """Get the current Tranquility server status.

        Returns:
            ServerStatus with player count, version, and start time.
        """
        data = await self._request("GET", "status/")
        return ServerStatus(
            players=data["players"],
            server_version=data["server_version"],
            start_time=self._parse_datetime(data["start_time"]),
            vip=data.get("vip"),
        )

    async def async_get_character_public(self, character_id: int) -> CharacterPublicInfo:
        """Get public information about a character.

        Args:
            character_id: The Eve Online character ID.

        Returns:
            CharacterPublicInfo with name, corporation, and more.
        """
        data = await self._request("GET", f"characters/{character_id}/")
        return CharacterPublicInfo(
            character_id=character_id,
            name=data["name"],
            corporation_id=data["corporation_id"],
            birthday=self._parse_datetime(data["birthday"]),
            gender=data["gender"],
            race_id=data["race_id"],
            bloodline_id=data["bloodline_id"],
            ancestry_id=data.get("ancestry_id"),
            alliance_id=data.get("alliance_id"),
            faction_id=data.get("faction_id"),
            description=data.get("description"),
            title=data.get("title"),
            security_status=data.get("security_status"),
        )

    async def async_get_character_portrait(self, character_id: int) -> CharacterPortrait:
        """Get a character's portrait URLs.

        Args:
            character_id: The Eve Online character ID.

        Returns:
            CharacterPortrait with image URLs at various resolutions.
        """
        data = await self._request("GET", f"characters/{character_id}/portrait/")
        return CharacterPortrait(
            px64x64=data.get("px64x64"),
            px128x128=data.get("px128x128"),
            px256x256=data.get("px256x256"),
            px512x512=data.get("px512x512"),
        )

    async def async_get_corporation_public(self, corporation_id: int) -> CorporationPublicInfo:
        """Get public information about a corporation.

        Args:
            corporation_id: The Eve Online corporation ID.

        Returns:
            CorporationPublicInfo with name, ticker, member count, and more.
        """
        data = await self._request("GET", f"corporations/{corporation_id}/")
        return CorporationPublicInfo(
            corporation_id=corporation_id,
            name=data["name"],
            ticker=data["ticker"],
            member_count=data["member_count"],
            ceo_id=data["ceo_id"],
            tax_rate=data["tax_rate"],
            alliance_id=data.get("alliance_id"),
            description=data.get("description"),
            date_founded=self._parse_datetime(data.get("date_founded")),
            url=data.get("url"),
        )

    async def async_resolve_names(self, ids: list[int]) -> list[UniverseName]:
        """Resolve a list of IDs to names.

        Args:
            ids: List of Eve Online entity IDs (characters, corps, etc.).

        Returns:
            List of UniverseName with id, name, and category.
        """
        if not ids:
            return []

        data = await self._request("POST", "universe/names/", json=ids)
        return [
            UniverseName(
                id=entry["id"],
                name=entry["name"],
                category=entry["category"],
            )
            for entry in data
        ]

    # -------------------------------------------------------------------------
    # Authenticated endpoints (auth required)
    # -------------------------------------------------------------------------

    async def async_get_character_online(self, character_id: int) -> CharacterOnlineStatus:
        """Get a character's online status.

        Requires scope: ``esi-location.read_online.v1``

        Args:
            character_id: The Eve Online character ID.

        Returns:
            CharacterOnlineStatus with online flag and login/logout times.
        """
        data = await self._request("GET", f"characters/{character_id}/online/", authenticated=True)
        return CharacterOnlineStatus(
            online=data["online"],
            last_login=self._parse_datetime(data.get("last_login")),
            last_logout=self._parse_datetime(data.get("last_logout")),
            logins=data.get("logins"),
        )

    async def async_get_character_location(self, character_id: int) -> CharacterLocation:
        """Get a character's current location.

        Requires scope: ``esi-location.read_location.v1``

        Args:
            character_id: The Eve Online character ID.

        Returns:
            CharacterLocation with solar system, station, or structure ID.
        """
        data = await self._request("GET", f"characters/{character_id}/location/", authenticated=True)
        return CharacterLocation(
            solar_system_id=data["solar_system_id"],
            station_id=data.get("station_id"),
            structure_id=data.get("structure_id"),
        )

    async def async_get_character_ship(self, character_id: int) -> CharacterShip:
        """Get a character's current ship.

        Requires scope: ``esi-location.read_ship_type.v1``

        Args:
            character_id: The Eve Online character ID.

        Returns:
            CharacterShip with ship type, item ID, and name.
        """
        data = await self._request("GET", f"characters/{character_id}/ship/", authenticated=True)
        return CharacterShip(
            ship_type_id=data["ship_type_id"],
            ship_item_id=data["ship_item_id"],
            ship_name=data["ship_name"],
        )

    async def async_get_wallet_balance(self, character_id: int) -> WalletBalance:
        """Get a character's wallet balance.

        Requires scope: ``esi-wallet.read_character_wallet.v1``

        Args:
            character_id: The Eve Online character ID.

        Returns:
            WalletBalance with ISK balance.
        """
        data = await self._request("GET", f"characters/{character_id}/wallet/", authenticated=True)
        # Wallet endpoint returns a raw float, not a JSON object
        return WalletBalance(balance=float(data))

    async def async_get_skill_queue(self, character_id: int) -> list[SkillQueueEntry]:
        """Get a character's skill training queue.

        Requires scope: ``esi-skills.read_skillqueue.v1``

        Args:
            character_id: The Eve Online character ID.

        Returns:
            List of SkillQueueEntry, ordered by queue_position.
        """
        data = await self._request("GET", f"characters/{character_id}/skillqueue/", authenticated=True)
        return [
            SkillQueueEntry(
                skill_id=entry["skill_id"],
                queue_position=entry["queue_position"],
                finished_level=entry["finished_level"],
                start_date=self._parse_datetime(entry.get("start_date")),
                finish_date=self._parse_datetime(entry.get("finish_date")),
                training_start_sp=entry.get("training_start_sp"),
                level_start_sp=entry.get("level_start_sp"),
                level_end_sp=entry.get("level_end_sp"),
            )
            for entry in data
        ]

    async def async_get_skills(self, character_id: int) -> CharacterSkillsSummary:
        """Get a character's total and unallocated skill points.

        Requires scope: ``esi-skills.read_skills.v1``

        Args:
            character_id: The Eve Online character ID.

        Returns:
            CharacterSkillsSummary with total SP and unallocated SP.
        """
        data = await self._request("GET", f"characters/{character_id}/skills/", authenticated=True)
        return CharacterSkillsSummary(
            total_sp=data["total_sp"],
            unallocated_sp=data.get("unallocated_sp", 0),
        )

    async def async_get_mail_labels(self, character_id: int) -> MailLabelsSummary:
        """Get a character's mail labels with unread counts.

        Requires scope: ``esi-mail.read_mail.v1``

        Args:
            character_id: The Eve Online character ID.

        Returns:
            MailLabelsSummary with total unread count.
        """
        data = await self._request("GET", f"characters/{character_id}/mail/labels/", authenticated=True)
        return MailLabelsSummary(
            total_unread_count=data.get("total_unread_count", 0),
        )

    async def async_get_industry_jobs(self, character_id: int, *, include_completed: bool = False) -> list[IndustryJob]:
        """Get a character's industry jobs.

        Requires scope: ``esi-industry.read_character_jobs.v1``

        Args:
            character_id: The Eve Online character ID.
            include_completed: Whether to include completed jobs.

        Returns:
            List of IndustryJob entries.
        """
        params: dict[str, str] = {}
        if include_completed:
            params["include_completed"] = "true"
        data = await self._request(
            "GET", f"characters/{character_id}/industry/jobs/", authenticated=True, params=params
        )
        return [
            IndustryJob(
                job_id=entry["job_id"],
                activity_id=entry["activity_id"],
                status=entry["status"],
                start_date=self._parse_datetime(entry["start_date"]),
                end_date=self._parse_datetime(entry["end_date"]),
                blueprint_type_id=entry["blueprint_type_id"],
                output_location_id=entry["output_location_id"],
                runs=entry["runs"],
                product_type_id=entry.get("product_type_id"),
                facility_id=entry.get("facility_id"),
                cost=entry.get("cost"),
            )
            for entry in data
        ]

    async def async_get_market_orders(self, character_id: int) -> list[MarketOrder]:
        """Get a character's open market orders.

        Requires scope: ``esi-markets.read_character_orders.v1``

        Args:
            character_id: The Eve Online character ID.

        Returns:
            List of MarketOrder entries.
        """
        data = await self._request("GET", f"characters/{character_id}/orders/", authenticated=True)
        return [
            MarketOrder(
                order_id=entry["order_id"],
                type_id=entry["type_id"],
                is_buy_order=entry.get("is_buy_order", False),
                price=entry["price"],
                volume_remain=entry["volume_remain"],
                volume_total=entry["volume_total"],
                location_id=entry["location_id"],
                region_id=entry["region_id"],
                issued=self._parse_datetime(entry["issued"]),
                duration=entry["duration"],
                range=entry["range"],
                min_volume=entry.get("min_volume"),
            )
            for entry in data
        ]

    async def async_get_jump_fatigue(self, character_id: int) -> JumpFatigue:
        """Get a character's jump fatigue information.

        Requires scope: ``esi-characters.read_fatigue.v1``

        Args:
            character_id: The Eve Online character ID.

        Returns:
            JumpFatigue with expiry date and last jump info.
        """
        data = await self._request("GET", f"characters/{character_id}/fatigue/", authenticated=True)
        return JumpFatigue(
            jump_fatigue_expire_date=self._parse_datetime(data.get("jump_fatigue_expire_date")),
            last_jump_date=self._parse_datetime(data.get("last_jump_date")),
            last_update_date=self._parse_datetime(data.get("last_update_date")),
        )

    async def async_get_notifications(self, character_id: int) -> list[CharacterNotification]:
        """Get a character's recent notifications.

        Requires scope: ``esi-characters.read_notifications.v1``

        Args:
            character_id: The Eve Online character ID.

        Returns:
            List of CharacterNotification entries, newest first.
        """
        data = await self._request("GET", f"characters/{character_id}/notifications/", authenticated=True)
        return [
            CharacterNotification(
                notification_id=entry["notification_id"],
                sender_id=entry["sender_id"],
                sender_type=entry["sender_type"],
                type=entry["type"],
                timestamp=self._parse_datetime(entry["timestamp"]),
                is_read=entry.get("is_read"),
                text=entry.get("text"),
            )
            for entry in data
        ]

    async def async_get_clones(self, character_id: int) -> CharacterClones:
        """Get a character's clone information.

        Requires scope: ``esi-clones.read_clones.v1``

        Args:
            character_id: The Eve Online character ID.

        Returns:
            CharacterClones with home location and jump clones.
        """
        data = await self._request("GET", f"characters/{character_id}/clones/", authenticated=True)

        home_loc = data.get("home_location")
        home_location: CloneHomeLocation | None = None
        if home_loc:
            home_location = CloneHomeLocation(
                location_id=home_loc["location_id"],
                location_type=home_loc["location_type"],
            )

        jump_clones = tuple(
            JumpClone(
                jump_clone_id=jc["jump_clone_id"],
                location_id=jc["location_id"],
                location_type=jc["location_type"],
                implants=tuple(jc.get("implants", [])),
                name=jc.get("name"),
            )
            for jc in data.get("jump_clones", [])
        )

        return CharacterClones(
            home_location=home_location,
            jump_clones=jump_clones,
            last_clone_jump_date=self._parse_datetime(data.get("last_clone_jump_date")),
            last_station_change_date=self._parse_datetime(data.get("last_station_change_date")),
        )

    async def async_get_implants(self, character_id: int) -> tuple[int, ...]:
        """Get the type IDs of a character's active implants.

        Requires scope: ``esi-clones.read_implants.v1``

        Args:
            character_id: The Eve Online character ID.

        Returns:
            Tuple of implant type IDs.
        """
        data = await self._request("GET", f"characters/{character_id}/implants/", authenticated=True)
        return tuple(data)

    async def async_get_wallet_journal(self, character_id: int) -> list[WalletJournalEntry]:
        """Get a character's wallet journal (recent transactions).

        All pages are fetched automatically. ESI returns up to 50 entries
        per page; characters with long transaction histories will require
        multiple pages.

        Requires scope: ``esi-wallet.read_character_wallet.v1``

        Args:
            character_id: The Eve Online character ID.

        Returns:
            List of WalletJournalEntry entries across all pages, newest first.
        """
        data = await self._request_all_pages(f"characters/{character_id}/wallet/journal/", authenticated=True)
        return [
            WalletJournalEntry(
                id=entry["id"],
                date=self._parse_datetime(entry["date"]),
                ref_type=entry["ref_type"],
                description=entry.get("description", ""),
                amount=entry.get("amount"),
                balance=entry.get("balance"),
                first_party_id=entry.get("first_party_id"),
                second_party_id=entry.get("second_party_id"),
                reason=entry.get("reason"),
            )
            for entry in data
        ]

    async def async_get_contacts(self, character_id: int) -> list[CharacterContact]:
        """Get a character's contacts.

        All pages are fetched automatically. ESI returns up to 500 contacts
        per page.

        Requires scope: ``esi-characters.read_contacts.v1``

        Args:
            character_id: The Eve Online character ID.

        Returns:
            List of CharacterContact entries across all pages.
        """
        data = await self._request_all_pages(f"characters/{character_id}/contacts/", authenticated=True)
        return [
            CharacterContact(
                contact_id=entry["contact_id"],
                contact_type=entry["contact_type"],
                standing=entry["standing"],
                is_blocked=entry.get("is_blocked"),
                is_watched=entry.get("is_watched"),
                label_ids=tuple(entry["label_ids"]) if entry.get("label_ids") else None,
            )
            for entry in data
        ]

    async def async_get_calendar(self, character_id: int) -> list[CalendarEvent]:
        """Get a character's upcoming calendar events.

        Requires scope: ``esi-calendar.read_calendar_events.v1``

        Args:
            character_id: The Eve Online character ID.

        Returns:
            List of CalendarEvent entries.
        """
        data = await self._request("GET", f"characters/{character_id}/calendar/", authenticated=True)
        return [
            CalendarEvent(
                event_id=entry["event_id"],
                event_date=self._parse_datetime(entry["event_date"]),
                title=entry["title"],
                importance=entry.get("importance"),
                event_response=entry.get("event_response"),
            )
            for entry in data
        ]

    async def async_get_loyalty_points(self, character_id: int) -> list[LoyaltyPoints]:
        """Get a character's loyalty points per corporation.

        Requires scope: ``esi-characters.read_loyalty.v1``

        Args:
            character_id: The Eve Online character ID.

        Returns:
            List of LoyaltyPoints entries.
        """
        data = await self._request("GET", f"characters/{character_id}/loyalty/points/", authenticated=True)
        return [
            LoyaltyPoints(
                corporation_id=entry["corporation_id"],
                loyalty_points=entry["loyalty_points"],
            )
            for entry in data
        ]

    async def async_get_killmails(self, character_id: int) -> list[CharacterKillmail]:
        """Get a character's recent killmail references.

        All pages are fetched automatically. ESI returns up to 50 entries
        per page; characters with high kill activity will require multiple pages.

        Requires scope: ``esi-killmails.read_killmails.v1``

        Args:
            character_id: The Eve Online character ID.

        Returns:
            List of CharacterKillmail entries across all pages.
        """
        data = await self._request_all_pages(f"characters/{character_id}/killmails/recent/", authenticated=True)
        return [
            CharacterKillmail(
                killmail_id=entry["killmail_id"],
                killmail_hash=entry["killmail_hash"],
            )
            for entry in data
        ]

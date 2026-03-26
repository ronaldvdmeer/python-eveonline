"""Async client for the Eve Online ESI API."""

from __future__ import annotations

from datetime import datetime
from typing import Any

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

        if auth is not None:
            self._session = auth.websession
        elif session is not None:
            self._session = session
        else:
            msg = "Either 'session' or 'auth' must be provided"
            raise EveOnlineError(msg)

    # -------------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------------

    async def _request(self, method: str, path: str, *, authenticated: bool = False, **kwargs: Any) -> Any:
        """Make a request to the ESI API.

        Args:
            method: HTTP method.
            path: API path relative to ESI base URL.
            authenticated: Whether this request requires authentication.
            **kwargs: Additional arguments for the HTTP request.

        Returns:
            Parsed JSON response.

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

        try:
            if authenticated:
                if self._auth is None:
                    msg = "Authentication required but no auth provider configured"
                    raise EveOnlineAuthenticationError(msg)
                response = await self._auth.request(method, path, params=params, **kwargs)
            else:
                response = await self._session.request(
                    method,
                    f"{self._host}/{path}",
                    params=params,
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

        if response.status == 404:
            msg = f"Resource not found: {path}"
            raise EveOnlineNotFoundError(msg)

        if response.status in (420, 429):
            retry_after = response.headers.get("Retry-After")
            raise EveOnlineRateLimitError(retry_after=int(retry_after) if retry_after else None)

        if response.status >= 400:
            text = await response.text()
            msg = f"ESI API error ({response.status}): {text}"
            raise EveOnlineError(msg)

        return await response.json()

    @staticmethod
    def _parse_datetime(value: str | None) -> datetime | None:
        """Parse an ISO8601 datetime string from ESI."""
        if value is None:
            return None
        # ESI returns times like "2025-01-15T12:34:56Z"
        return datetime.fromisoformat(value.replace("Z", "+00:00"))

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
            start_time=datetime.fromisoformat(data["start_time"].replace("Z", "+00:00")),
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
            birthday=datetime.fromisoformat(data["birthday"].replace("Z", "+00:00")),
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

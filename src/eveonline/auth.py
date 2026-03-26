"""Abstract authentication for the Eve Online ESI API."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from aiohttp import ClientResponse, ClientSession

from .const import ESI_BASE_URL


class AbstractAuth(ABC):
    """Abstract class to make authenticated requests to the ESI API.

    This follows the Home Assistant API library pattern where the library
    provides an abstract auth class, and the integration (or standalone user)
    provides a concrete implementation that handles token management.

    Example usage::

        class MyAuth(AbstractAuth):
            async def async_get_access_token(self) -> str:
                return self._my_token_manager.get_token()

        auth = MyAuth(session)
        client = EveOnlineClient(auth=auth)
    """

    def __init__(
        self,
        websession: ClientSession,
        host: str = ESI_BASE_URL,
    ) -> None:
        """Initialize the auth.

        Args:
            websession: An aiohttp ClientSession for making requests.
            host: The ESI API base URL. Defaults to the official ESI endpoint.
        """
        self.websession = websession
        self.host = host

    @abstractmethod
    async def async_get_access_token(self) -> str:
        """Return a valid access token for the ESI API."""

    async def request(self, method: str, path: str, **kwargs: Any) -> ClientResponse:
        """Make an authenticated request to the ESI API.

        Args:
            method: HTTP method (GET, POST, etc.).
            path: API path (e.g., "characters/12345/wallet/").
            **kwargs: Additional arguments passed to aiohttp request.

        Returns:
            The aiohttp ClientResponse.
        """
        headers: dict[str, str] = dict(kwargs.pop("headers", {}) or {})
        access_token = await self.async_get_access_token()
        headers["authorization"] = f"Bearer {access_token}"

        return await self.websession.request(
            method,
            f"{self.host}/{path}",
            **kwargs,
            headers=headers,
        )

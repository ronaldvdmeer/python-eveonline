# Quickstart

## Installation

```bash
pip install python-eveonline
```

## Public endpoints (no authentication)

Public endpoints only require an `aiohttp.ClientSession`. No Eve SSO token needed.

```python
import asyncio
import aiohttp
from eveonline import EveOnlineClient

async def main():
    async with aiohttp.ClientSession() as session:
        client = EveOnlineClient(session=session)

        # Server status
        status = await client.async_get_server_status()
        print(f"{status.players} players online (v{status.server_version})")

        # Public character info
        char = await client.async_get_character_public(2117905894)
        print(f"{char.name} — corporation {char.corporation_id}")

        # Resolve IDs to names
        names = await client.async_resolve_names([2117905894, 98553333])
        for n in names:
            print(f"{n.id} → {n.name} ({n.category})")

asyncio.run(main())
```

## Authenticated endpoints

Character-specific endpoints require an OAuth2 access token via an `AbstractAuth` implementation.
See the [Authentication](authentication.md) guide for details on implementing your own.

```python
from eveonline import EveOnlineClient
from eveonline.auth import AbstractAuth
import aiohttp

class SimpleAuth(AbstractAuth):
    """Minimal auth example — returns a static token."""

    def __init__(self, session: aiohttp.ClientSession, token: str) -> None:
        super().__init__(session)
        self._token = token

    async def async_get_access_token(self) -> str:
        return self._token


async def main():
    async with aiohttp.ClientSession() as session:
        auth = SimpleAuth(session, "your-access-token-here")
        client = EveOnlineClient(auth=auth)

        character_id = 2117905894

        online = await client.async_get_character_online(character_id)
        print(f"Online: {online.online}")

        wallet = await client.async_get_wallet_balance(character_id)
        print(f"Wallet: {wallet.balance:,.2f} ISK")

        location = await client.async_get_character_location(character_id)
        print(f"Solar system: {location.solar_system_id}")

asyncio.run(main())
```

## All response types are frozen dataclasses

Every API response is a `@dataclass(frozen=True)` — fields are read-only and hashable.
Optional fields (e.g. `vip`, `station_id`) default to `None` when not returned by the API.

```python
status = await client.async_get_server_status()
print(status.players)       # int
print(status.vip)           # bool | None

location = await client.async_get_character_location(character_id)
print(location.solar_system_id)  # always present
print(location.station_id)       # int | None — None when in space
```

## Automatic pagination

Some endpoints return large datasets across multiple pages. The client fetches all pages automatically and returns a single combined list:

```python
# Fetches all pages automatically — no manual paging needed
journal = await client.async_get_wallet_journal(character_id)
print(f"{len(journal)} journal entries total")
```

Paginated endpoints: `async_get_wallet_journal()`, `async_get_contacts()`, `async_get_killmails()`.

## Request caching

The client caches ESI responses automatically using two layers:

1. **TTL** — If ESI returns an `Expires` header, repeated calls before that time skip the HTTP request entirely.
2. **ETag / 304** — Once the TTL expires, the client sends `If-None-Match`. If the data is unchanged, ESI returns `304 Not Modified` and no response body is downloaded.

Both layers are transparent and require no configuration. To force fresh data, call `clear_etag_cache()`:

```python
client.clear_etag_cache()
status = await client.async_get_server_status()  # fresh request
```

See [Endpoints](endpoints.md#request-caching) for the full caching reference.

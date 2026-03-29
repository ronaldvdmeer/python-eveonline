# python-eveonline Documentation

Async Python client library for the [Eve Online ESI API](https://esi.evetech.net/ui/).

## Pages

- [**Quickstart**](quickstart.md) — Installation and first API calls
- [**Authentication**](authentication.md) — Implementing `AbstractAuth` for token management
- [**Endpoints**](endpoints.md) — Full reference of all available API methods
- [**Error Handling**](error-handling.md) — Exception hierarchy and best practices

## Key features

- **Two-layer caching** — respects the ESI `Expires` header to skip HTTP requests entirely within the cache window, and sends `If-None-Match` with the cached ETag so unchanged responses return HTTP 304 without a response body. Both layers work automatically with no configuration required.
- **Automatic pagination** — paginated endpoints (`async_get_wallet_journal()`, `async_get_contacts()`, `async_get_killmails()`) fetch all pages transparently and return a single combined list.
- **23 endpoints** covering public and auth-gated ESI resources — see [Endpoints](endpoints.md) for the full list.
- **Typed models** — all responses are frozen dataclasses with full type annotations and PEP 561 `py.typed` marker.
- **Abstract auth** — bring your own token source by implementing `AbstractAuth`.

## At a glance

```python
import asyncio
import aiohttp
from eveonline import EveOnlineClient

async def main():
    async with aiohttp.ClientSession() as session:
        client = EveOnlineClient(session=session)
        status = await client.async_get_server_status()
        print(f"{status.players} players online — version {status.server_version}")

asyncio.run(main())
```

## Requirements

- Python 3.11+
- aiohttp 3.9+

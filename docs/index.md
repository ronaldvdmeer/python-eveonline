# python-eveonline Documentation

Async Python client library for the [Eve Online ESI API](https://esi.evetech.net/ui/).

## Pages

- [**Quickstart**](quickstart.md) — Installation and first API calls
- [**Authentication**](authentication.md) — Implementing `AbstractAuth` for token management
- [**Endpoints**](endpoints.md) — Full reference of all available API methods
- [**Error Handling**](error-handling.md) — Exception hierarchy and best practices

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

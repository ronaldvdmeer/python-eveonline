# python-eveonline

Async Python client library for the [Eve Online ESI API](https://esi.evetech.net/ui/).

## Features

- Fully async (aiohttp)
- Typed models (frozen dataclasses)
- Public endpoints: server status, character info, corporation info, portraits, name resolution
- Authenticated endpoints: online status, location, ship, wallet, skill queue
- AbstractAuth pattern for Home Assistant OAuth2 integration
- PEP 561 typed package (py.typed)
- 100% test coverage

## Installation

```bash
pip install python-eveonline
```

## Quick Start

```python
import asyncio
import aiohttp
from eveonline import EveOnlineClient

async def main():
    async with aiohttp.ClientSession() as session:
        client = EveOnlineClient(session=session)
        status = await client.async_get_server_status()
        print(f"{status.players} players online")

asyncio.run(main())
```

## License

MIT

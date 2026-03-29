# python-eveonline

[![PyPI](https://img.shields.io/pypi/v/python-eveonline.svg)](https://pypi.org/project/python-eveonline/)
[![Python](https://img.shields.io/pypi/pyversions/python-eveonline.svg)](https://pypi.org/project/python-eveonline/)
[![License](https://img.shields.io/github/license/ronaldvdmeer/python-eveonline.svg)](https://github.com/ronaldvdmeer/python-eveonline/blob/main/LICENSE)
[![GitHub Release](https://img.shields.io/github/v/release/ronaldvdmeer/python-eveonline.svg)](https://github.com/ronaldvdmeer/python-eveonline/releases)

Async Python client library for the [Eve Online ESI API](https://esi.evetech.net/ui/).

Built for use with [Home Assistant](https://www.home-assistant.io/) but can be used standalone in any async Python project.

## Features

- **Fully async** — built on [aiohttp](https://docs.aiohttp.org/)
- **Typed models** — all API responses are frozen dataclasses with full type annotations
- **23 endpoints** — public (server, character, corporation, universe) and authenticated (wallet, skills, location, industry, market, mail, notifications, clones, fatigue, contacts, calendar, loyalty, killmails)
- **Abstract auth** — implement `AbstractAuth` to plug in any OAuth2 token source
- **Type-safe** — PEP 561 compatible (`py.typed`), strict mypy configuration
- **Tested** — ≥98% test coverage

## Installation

```bash
pip install python-eveonline
```

## Quick start

```python
import asyncio
import aiohttp
from eveonline import EveOnlineClient

async def main():
    async with aiohttp.ClientSession() as session:
        client = EveOnlineClient(session=session)
        status = await client.async_get_server_status()
        print(f"{status.players} players online (v{status.server_version})")

asyncio.run(main())
```

## Documentation

- [**Quickstart**](docs/quickstart.md) — public and authenticated endpoint examples
- [**Authentication**](docs/authentication.md) — implementing `AbstractAuth`, required OAuth scopes
- [**Endpoints**](docs/endpoints.md) — full reference with field tables for all 23 methods
- [**Error Handling**](docs/error-handling.md) — exception hierarchy, rate limiting, ESI cache times

## License

[MIT](LICENSE)

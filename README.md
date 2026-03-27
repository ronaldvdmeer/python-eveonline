# python-eveonline

[![PyPI](https://img.shields.io/pypi/v/python-eveonline.svg)](https://pypi.org/project/python-eveonline/)
[![Python](https://img.shields.io/pypi/pyversions/python-eveonline.svg)](https://pypi.org/project/python-eveonline/)
[![License](https://img.shields.io/github/license/ronaldvdmeer/python-eveonline.svg)](https://github.com/ronaldvdmeer/python-eveonline/blob/main/LICENSE)
[![GitHub Release](https://img.shields.io/github/v/release/ronaldvdmeer/python-eveonline.svg)](https://github.com/ronaldvdmeer/python-eveonline/releases)

Async Python client library for the [Eve Online ESI API](https://esi.evetech.net/ui/).

Built for use with [Home Assistant](https://www.home-assistant.io/) but can be used standalone in any async Python project.

## Features

- **Fully async** — built on [aiohttp](https://docs.aiohttp.org/)
- **Typed models** — all API responses are frozen dataclasses
- **Public endpoints** — server status, character info, corporation info, portraits, universe name resolution
- **Authenticated endpoints** — online status, location, ship, wallet, skills, skill queue, mail, industry jobs, market orders, jump fatigue
- **Abstract auth** — implement `AbstractAuth` to provide your own token management (e.g. Home Assistant OAuth2)
- **Type-safe** — PEP 561 compatible (`py.typed`), strict mypy configuration
- **Tested** — 100% test coverage

## Installation

```bash
pip install python-eveonline
```

## Quick start

### Public endpoints (no authentication required)

```python
import asyncio
import aiohttp
from eveonline import EveOnlineClient

async def main():
    async with aiohttp.ClientSession() as session:
        client = EveOnlineClient(session=session)
        status = await client.async_get_server_status()
        print(f"{status.players} players online (version {status.server_version})")

asyncio.run(main())
```

### Authenticated endpoints

To access character-specific data, implement the `AbstractAuth` class with your own token management:

```python
from eveonline import EveOnlineClient
from eveonline.auth import AbstractAuth

class MyAuth(AbstractAuth):
    async def async_get_access_token(self) -> str:
        return "your-access-token"

auth = MyAuth(websession)
client = EveOnlineClient(auth=auth)

online = await client.async_get_character_online(character_id)
wallet = await client.async_get_wallet_balance(character_id)
```

## Available endpoints

| Method | Scope required | Returns |
|--------|---------------|---------|
| `async_get_server_status()` | — | `ServerStatus` |
| `async_get_character_public(id)` | — | `CharacterPublicInfo` |
| `async_get_character_portrait(id)` | — | `CharacterPortrait` |
| `async_get_corporation_public(id)` | — | `CorporationPublicInfo` |
| `async_resolve_names(ids)` | — | `list[UniverseName]` |
| `async_get_character_online(id)` | `esi-location.read_online.v1` | `CharacterOnlineStatus` |
| `async_get_character_location(id)` | `esi-location.read_location.v1` | `CharacterLocation` |
| `async_get_character_ship(id)` | `esi-location.read_ship_type.v1` | `CharacterShip` |
| `async_get_wallet_balance(id)` | `esi-wallet.read_character_wallet.v1` | `WalletBalance` |
| `async_get_skills(id)` | `esi-skills.read_skills.v1` | `CharacterSkillsSummary` |
| `async_get_skill_queue(id)` | `esi-skills.read_skillqueue.v1` | `list[SkillQueueEntry]` |
| `async_get_mail_labels(id)` | `esi-mail.read_mail.v1` | `MailLabelsSummary` |
| `async_get_industry_jobs(id)` | `esi-industry.read_character_jobs.v1` | `list[IndustryJob]` |
| `async_get_market_orders(id)` | `esi-markets.read_character_orders.v1` | `list[MarketOrder]` |
| `async_get_jump_fatigue(id)` | `esi-characters.read_fatigue.v1` | `JumpFatigue` |

## Error handling

All exceptions inherit from `EveOnlineError`:

```python
from eveonline import EveOnlineClient, EveOnlineError
from eveonline.exceptions import (
    EveOnlineAuthenticationError,  # 401/403 or missing auth
    EveOnlineConnectionError,      # Network/connection failures
    EveOnlineRateLimitError,       # 429 with optional retry_after
)

try:
    status = await client.async_get_server_status()
except EveOnlineAuthenticationError:
    # Token expired or invalid
    ...
except EveOnlineRateLimitError as err:
    # Back off for err.retry_after seconds
    ...
except EveOnlineError:
    # Any other ESI error
    ...
```

## License

[MIT](LICENSE)

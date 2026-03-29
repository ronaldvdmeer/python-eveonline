# Authentication

Authenticated ESI endpoints require an OAuth2 access token obtained via [Eve SSO](https://docs.esi.evetech.net/docs/sso/).

`python-eveonline` does **not** handle the OAuth2 flow itself — it provides the `AbstractAuth` base class and you supply the token. This keeps the library flexible: it works standalone, with Home Assistant, or with any other OAuth2 framework.

## Implementing AbstractAuth

Subclass `AbstractAuth` and implement `async_get_access_token()`:

```python
from eveonline.auth import AbstractAuth
import aiohttp

class MyAuth(AbstractAuth):
    def __init__(self, session: aiohttp.ClientSession, token_manager) -> None:
        super().__init__(session)
        self._token_manager = token_manager

    async def async_get_access_token(self) -> str:
        """Return a valid (non-expired) access token."""
        return await self._token_manager.get_fresh_token()
```

The library calls `async_get_access_token()` on every authenticated request, so your implementation should handle token refresh internally.

## Using auth with the client

```python
async with aiohttp.ClientSession() as session:
    auth = MyAuth(session, token_manager)
    client = EveOnlineClient(auth=auth)

    # All authenticated endpoints are now available
    online = await client.async_get_character_online(character_id)
```

## Required OAuth scopes

Each endpoint requires specific Eve SSO scopes. The full list of scopes used by this library:

| Scope | Used by |
|---|---|
| `esi-location.read_online.v1` | `async_get_character_online()` |
| `esi-location.read_location.v1` | `async_get_character_location()` |
| `esi-location.read_ship_type.v1` | `async_get_character_ship()` |
| `esi-wallet.read_character_wallet.v1` | `async_get_wallet_balance()`, `async_get_wallet_journal()` |
| `esi-skills.read_skills.v1` | `async_get_skills()` |
| `esi-skills.read_skillqueue.v1` | `async_get_skill_queue()` |
| `esi-mail.read_mail.v1` | `async_get_mail_labels()` |
| `esi-industry.read_character_jobs.v1` | `async_get_industry_jobs()` |
| `esi-markets.read_character_orders.v1` | `async_get_market_orders()` |
| `esi-characters.read_fatigue.v1` | `async_get_jump_fatigue()` |
| `esi-characters.read_notifications.v1` | `async_get_notifications()` |
| `esi-clones.read_clones.v1` | `async_get_clones()` |
| `esi-clones.read_implants.v1` | `async_get_implants()` |
| `esi-characters.read_contacts.v1` | `async_get_contacts()` |
| `esi-calendar.read_calendar_events.v1` | `async_get_calendar()` |
| `esi-characters.read_loyalty.v1` | `async_get_loyalty_points()` |
| `esi-killmails.read_killmails.v1` | `async_get_killmails()` |

The `DEFAULT_SCOPES` constant exports a recommended baseline set of scopes as a tuple:

```python
from eveonline.const import DEFAULT_SCOPES

# Use when requesting authorization from Eve SSO
print(DEFAULT_SCOPES)
```

## Home Assistant integration

For Home Assistant, `AbstractAuth` maps directly to `OAuth2Session`. The `eveonline` integration implements this as `AsyncConfigEntryAuth`:

```python
class AsyncConfigEntryAuth(AbstractAuth):
    def __init__(self, session: ClientSession, oauth_session: OAuth2Session) -> None:
        super().__init__(session)
        self._oauth_session = oauth_session

    async def async_get_access_token(self) -> str:
        await self._oauth_session.async_ensure_token_valid()
        return self._oauth_session.token["access_token"]
```

## Authentication errors

If a token is invalid or expired and cannot be refreshed, `async_get_access_token()` should raise an exception. The client translates HTTP 401/403 responses into `EveOnlineAuthenticationError`. See [Error Handling](error-handling.md).

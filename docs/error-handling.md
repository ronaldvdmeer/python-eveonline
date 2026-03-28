# Error Handling

All exceptions inherit from `EveOnlineError` and are exported from the top-level package.

## Exception hierarchy

```
EveOnlineError                    — base for all library errors
  EveOnlineConnectionError        — network unreachable / timeout
  EveOnlineAuthenticationError    — HTTP 401 or 403
  EveOnlineRateLimitError         — HTTP 420 or 429
  EveOnlineNotFoundError          — HTTP 404 on a required endpoint
```

## Importing exceptions

```python
from eveonline import (
    EveOnlineError,
    EveOnlineConnectionError,
    EveOnlineAuthenticationError,
    EveOnlineRateLimitError,
    EveOnlineNotFoundError,
)
```

## Basic error handling

```python
from eveonline import EveOnlineClient, EveOnlineError

try:
    status = await client.async_get_server_status()
except EveOnlineError as err:
    print(f"ESI error: {err}")
```

## Handling specific errors

```python
from eveonline import (
    EveOnlineAuthenticationError,
    EveOnlineRateLimitError,
    EveOnlineConnectionError,
    EveOnlineNotFoundError,
)
import asyncio

try:
    wallet = await client.async_get_wallet_balance(character_id)

except EveOnlineAuthenticationError:
    # Token expired or revoked — trigger re-authentication
    await trigger_reauth()

except EveOnlineRateLimitError as err:
    # ESI error budget exceeded (HTTP 420/429)
    wait = err.retry_after or 60  # retry_after may be None
    print(f"Rate limited, waiting {wait}s")
    await asyncio.sleep(wait)

except EveOnlineConnectionError:
    # Network issue or ESI unreachable
    print("Could not reach ESI API")

except EveOnlineNotFoundError:
    # Resource does not exist
    print("Character not found")
```

## Rate limiting details

ESI uses an **error-rate limiter**, not a simple request-rate limit. Each error response consumes from an error budget tracked by the `X-ESI-Error-Limit-Remain` response header.

When the budget is exhausted, ESI returns HTTP **420** with a `Retry-After` header. The library raises `EveOnlineRateLimitError` in this case.

```python
except EveOnlineRateLimitError as err:
    if err.retry_after is not None:
        await asyncio.sleep(err.retry_after)
    else:
        await asyncio.sleep(60)  # safe default
```

`retry_after` is `None` when the server does not include the header or when the header value cannot be parsed as an integer.

## ESI caching headers

ESI endpoints each have a server-side cache duration. Fetching within the cache window returns the same data. Common cache times:

| Endpoint | Cache duration |
|---|---|
| `/status/` | 30 seconds |
| `/characters/{id}/online/` | 60 seconds |
| `/characters/{id}/wallet/` | 120 seconds |
| `/characters/{id}/skills/` | 120 seconds |
| `/characters/{id}/skillqueue/` | 120 seconds |
| `/characters/{id}/industry/jobs/` | 300 seconds |
| `/characters/{id}/orders/` | 1200 seconds |
| `/universe/names/` | 3600 seconds |

The library does **not** cache responses client-side. Consider polling at intervals aligned with these cache times to avoid redundant fetches.

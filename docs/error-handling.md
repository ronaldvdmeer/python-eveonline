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

The client automatically caches ESI responses to reduce traffic and ESI error-budget consumption. See [Endpoints — Request caching](endpoints.md#request-caching) for the full reference including cache durations, TTL behaviour, ETag/304 handling, and `clear_etag_cache()`.

# Copilot Instructions — python-eveonline

Async Python client library for the [Eve Online ESI API](https://esi.evetech.net/ui/), primarily built as the dependency for the Home Assistant `eveonline` integration.

## Architecture

```
src/eveonline/
  auth.py       AbstractAuth — subclass to provide token management
  client.py     EveOnlineClient — all API calls live here
  models.py     Frozen dataclasses for every API response
  exceptions.py EveOnlineError hierarchy
  const.py      ESI_BASE_URL, DEFAULT_SCOPES (tuple), ESI_DATASOURCE
  __init__.py   Public re-exports (EveOnlineClient, all exceptions, models)
```

`EveOnlineClient` accepts either a plain `aiohttp.ClientSession` (public endpoints) or an `AbstractAuth` subclass (authenticated endpoints). Never add state to the client — it is stateless by design.

## Models

All models are `@dataclass(frozen=True, slots=True)`. Every field has a docstring `Attributes:` section. Optional fields default to `None`. Required `datetime` fields use `datetime.fromisoformat()` directly; optional `datetime` fields use the `_parse_datetime()` helper in `client.py`.

```python
@dataclass(frozen=True, slots=True)
class ServerStatus:
    """..."""
    players: int
    vip: bool | None = None  # optional always last, defaulting to None
```

## Adding a new endpoint

1. Add a model to `models.py` (frozen+slots dataclass)
2. Add the method to `EveOnlineClient` in `client.py` — use `_fetch_required()` for endpoints that must succeed, `_fetch_optional()` for ones that may return 404, `_fetch_list()` for arrays
3. Export the model from `__init__.py`
4. Add tests in `tests/test_client_authenticated.py` or `tests/test_client_public.py` using `aioresponses`

## Testing

```bash
pip install ".[dev]"
pytest              # runs all tests + coverage (must stay ≥ 90%, target 100%)
ruff check src/ tests/
ruff format src/ tests/
mypy src/
pylint src/eveonline/
```

Tests use `aioresponses` to mock HTTP — never use real ESI in tests. The `MockAuth` fixture is in `tests/conftest.py`.

## Releases

- Bump version in `pyproject.toml` (single source — `importlib.metadata.version()` reads it at runtime)
- Commit, tag `vX.Y.Z`, push tag → CI publishes to PyPI automatically
- Create GitHub release with changelog via `gh release create vX.Y.Z --title "vX.Y.Z" --notes-file <file>`
- `skip-existing: true` is set in the publish workflow so re-pushing a tag never 400s

## Exception hierarchy

```
EveOnlineError
  EveOnlineConnectionError   — network unreachable
  EveOnlineAuthenticationError — 401/403
  EveOnlineRateLimitError    — 420/429; has .retry_after: int | None
  EveOnlineNotFoundError     — 404 on required fetch
```

## Key conventions

- `from __future__ import annotations` in every file
- All public symbols exported from `__init__.py`
- `DEFAULT_SCOPES` is a `tuple`, not a list
- `Retry-After` header parsed with try/except — may be numeric seconds or an HTTP date
- CI tests Python 3.11, 3.12, 3.13 in parallel

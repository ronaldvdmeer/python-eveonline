"""Tests for constants module."""

from __future__ import annotations

from eveonline.const import (
    DEFAULT_SCOPES,
    ESI_BASE_URL,
    ESI_DATASOURCE,
    SCOPE_READ_LOCATION,
    SCOPE_READ_ONLINE,
    SCOPE_READ_SHIP_TYPE,
    SCOPE_READ_SKILLQUEUE,
    SCOPE_READ_SKILLS,
    SCOPE_READ_WALLET,
    SSO_AUTHORIZE_URL,
    SSO_TOKEN_URL,
)


class TestConstants:
    """Test that constants are correctly defined."""

    def test_esi_base_url(self):
        """ESI base URL points to latest."""
        assert ESI_BASE_URL == "https://esi.evetech.net/latest"

    def test_esi_datasource(self):
        """Datasource is Tranquility."""
        assert ESI_DATASOURCE == "tranquility"

    def test_sso_urls(self):
        """SSO URLs point to EVE login."""
        assert "login.eveonline.com" in SSO_AUTHORIZE_URL
        assert "login.eveonline.com" in SSO_TOKEN_URL

    def test_scope_format(self):
        """All scopes follow the esi-*.v1 format."""
        scopes = [
            SCOPE_READ_ONLINE,
            SCOPE_READ_LOCATION,
            SCOPE_READ_SHIP_TYPE,
            SCOPE_READ_WALLET,
            SCOPE_READ_SKILLS,
            SCOPE_READ_SKILLQUEUE,
        ]
        for scope in scopes:
            assert scope.startswith("esi-")
            assert scope.endswith(".v1")

    def test_default_scopes_contains_essentials(self):
        """Default scopes include online status and wallet."""
        assert SCOPE_READ_ONLINE in DEFAULT_SCOPES
        assert SCOPE_READ_WALLET in DEFAULT_SCOPES
        assert SCOPE_READ_LOCATION in DEFAULT_SCOPES

    def test_default_scopes_is_list(self):
        """Default scopes is a list."""
        assert isinstance(DEFAULT_SCOPES, list)
        assert len(DEFAULT_SCOPES) > 0

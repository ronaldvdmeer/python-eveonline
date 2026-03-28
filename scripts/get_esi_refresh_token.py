#!/usr/bin/env python3
"""One-time helper script to obtain an ESI refresh token via the OAuth2 flow.

Run this script ONCE locally to get the refresh token, then store
the output values as GitHub repository secrets.

Usage::

    python scripts/get_esi_refresh_token.py

Prerequisites
-------------
1. Go to https://developers.eveonline.com/ and create an application.
2. Set the callback URL to: http://localhost:12345/callback
3. Select the scopes you need (the script will suggest all scopes used by the
   integration tests).
4. Copy the Client ID and Client Secret and paste them when prompted.
"""

from __future__ import annotations

import base64
import html
import json
import secrets
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

# ---------------------------------------------------------------------------
# EVE SSO constants
# ---------------------------------------------------------------------------
ESI_SSO_AUTHORIZE = "https://login.eveonline.com/v2/oauth/authorize"
ESI_SSO_TOKEN = "https://login.eveonline.com/v2/oauth/token"
CALLBACK_PORT = 12345
CALLBACK_URL = f"http://localhost:{CALLBACK_PORT}/callback"

# All scopes required by the integration tests
INTEGRATION_SCOPES = " ".join([
    "esi-location.read_online.v1",
    "esi-location.read_location.v1",
    "esi-location.read_ship_type.v1",
    "esi-wallet.read_character_wallet.v1",
    "esi-skills.read_skills.v1",
    "esi-skills.read_skillqueue.v1",
    "esi-characters.read_fatigue.v1",
    "esi-mail.read_mail.v1",
    "esi-industry.read_character_jobs.v1",
    "esi-markets.read_character_orders.v1",
    "esi-characters.read_notifications.v1",
    "esi-clones.read_clones.v1",
    "esi-clones.read_implants.v1",
    "esi-characters.read_contacts.v1",
    "esi-calendar.read_calendar_events.v1",
    "esi-characters.read_loyalty.v1",
])


# ---------------------------------------------------------------------------
# Simple one-shot HTTP server to capture the OAuth2 callback
# ---------------------------------------------------------------------------
class _CallbackHandler(BaseHTTPRequestHandler):
    """Handles a single OAuth2 redirect and stores the authorization code."""

    auth_code: str | None = None
    state_received: str | None = None

    def do_GET(self) -> None:  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        _CallbackHandler.auth_code = params.get("code", [None])[0]
        _CallbackHandler.state_received = params.get("state", [None])[0]

        body = b"<html><body><h2>Authorization successful!</h2><p>You can close this tab.</p></body></html>"
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args: Any) -> None:  # noqa: ANN401
        pass  # suppress access log noise


# ---------------------------------------------------------------------------
# OAuth2 helpers
# ---------------------------------------------------------------------------
def _exchange_code(client_id: str, client_secret: str, code: str) -> dict[str, Any]:
    """Exchange an authorization code for access + refresh tokens."""
    creds = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    data = urllib.parse.urlencode({
        "grant_type": "authorization_code",
        "code": code,
    }).encode()
    req = urllib.request.Request(
        ESI_SSO_TOKEN,
        data=data,
        headers={
            "Authorization": f"Basic {creds}",
            "Content-Type": "application/x-www-form-urlencoded",
            "Host": "login.eveonline.com",
        },
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())  # type: ignore[no-any-return]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    print("=" * 60)
    print("  EVE Online ESI — Refresh Token Setup")
    print("=" * 60)
    print()
    print("Go to https://developers.eveonline.com/ and create an app.")
    print(f"Set the callback URL to:  {CALLBACK_URL}")
    print()

    client_id = input("Client ID     : ").strip()
    client_secret = input("Client Secret : ").strip()
    character_id = input("Character ID (for ESI_TEST_CHARACTER_ID secret): ").strip()

    state = secrets.token_urlsafe(16)
    auth_url = (
        f"{ESI_SSO_AUTHORIZE}"
        f"?response_type=code"
        f"&client_id={urllib.parse.quote(client_id)}"
        f"&redirect_uri={urllib.parse.quote(CALLBACK_URL)}"
        f"&scope={urllib.parse.quote(INTEGRATION_SCOPES)}"
        f"&state={state}"
    )

    print()
    print("Opening browser for EVE SSO login…")
    print(f"URL: {auth_url}")
    webbrowser.open(auth_url)

    # Wait for the callback
    print(f"\nWaiting for OAuth2 callback on port {CALLBACK_PORT}…")
    server = HTTPServer(("localhost", CALLBACK_PORT), _CallbackHandler)
    server.handle_request()  # handles exactly one request, then returns

    if _CallbackHandler.state_received != state:
        print("\n[ERROR] State mismatch — possible CSRF attempt. Aborting.")
        return

    code = _CallbackHandler.auth_code
    if not code:
        print("\n[ERROR] No authorization code received. Aborting.")
        return

    print("\nExchanging authorization code for tokens…")
    token_data = _exchange_code(client_id, client_secret, html.unescape(code))

    refresh_token = token_data.get("refresh_token", "")
    if not refresh_token:
        print("\n[ERROR] No refresh token in response:", token_data)
        return

    print()
    print("=" * 60)
    print("  SUCCESS — add the following GitHub repository secrets:")
    print("  (Settings → Secrets and variables → Actions)")
    print("=" * 60)
    print()
    print(f"  ESI_CLIENT_ID         = {client_id}")
    print(f"  ESI_CLIENT_SECRET     = {client_secret}")
    print(f"  ESI_REFRESH_TOKEN     = {refresh_token}")
    if character_id:
        print(f"  ESI_TEST_CHARACTER_ID = {character_id}")
    print()


if __name__ == "__main__":
    main()

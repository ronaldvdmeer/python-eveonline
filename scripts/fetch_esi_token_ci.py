"""CI helper: exchange an ESI refresh token for a fresh access token.

Called by the GitHub Actions integration job.  Reads credentials from
environment variables and writes the resulting access token to GITHUB_ENV
so subsequent steps can use it as ``ESI_TOKEN``.

If any required environment variable is missing the script exits cleanly
(exit code 0) without writing anything — pytest will then skip all
authenticated integration tests automatically via ``pytest.mark.skipif``.
"""

from __future__ import annotations

import base64
import json
import os
import sys
import urllib.parse
import urllib.request

ESI_TOKEN_URL = "https://login.eveonline.com/v2/oauth/token"


def main() -> None:
    client_id = os.environ.get("ESI_CLIENT_ID", "")
    client_secret = os.environ.get("ESI_CLIENT_SECRET", "")
    refresh_token = os.environ.get("ESI_REFRESH_TOKEN", "")

    if not all([client_id, client_secret, refresh_token]):
        print("ESI credentials not configured — authenticated tests will be skipped.")
        sys.exit(0)

    creds = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    data = urllib.parse.urlencode({
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }).encode()

    req = urllib.request.Request(
        ESI_TOKEN_URL,
        data=data,
        headers={
            "Authorization": f"Basic {creds}",
            "Content-Type": "application/x-www-form-urlencoded",
            "Host": "login.eveonline.com",
        },
    )

    try:
        with urllib.request.urlopen(req) as resp:
            access_token: str = json.loads(resp.read())["access_token"]
    except Exception as exc:  # noqa: BLE001
        print(f"[ERROR] Failed to fetch ESI access token: {exc}")
        sys.exit(1)

    github_env = os.environ.get("GITHUB_ENV", "")
    if github_env:
        with open(github_env, "a") as fh:
            fh.write(f"ESI_TOKEN={access_token}\n")
        print("ESI access token written to GITHUB_ENV.")
    else:
        # Running locally — just print the token (useful for debugging)
        print(f"ESI_TOKEN={access_token}")


if __name__ == "__main__":
    main()

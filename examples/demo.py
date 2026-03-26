"""Example usage of the Eve Online ESI client."""

import asyncio

import aiohttp

from eveonline import EveOnlineClient


async def main() -> None:
    """Demo: fetch public Eve Online data (no auth required)."""
    async with aiohttp.ClientSession() as session:
        client = EveOnlineClient(session=session)

        # Server status
        status = await client.async_get_server_status()
        print(f"Server: {status.server_version}")
        print(f"Players online: {status.players}")
        print(f"Start time: {status.start_time}")
        print()

        # Look up a well-known character: CCP Bartender (2113024536)
        character = await client.async_get_character_public(2113024536)
        print(f"Character: {character.name}")
        print(f"Corporation ID: {character.corporation_id}")
        print(f"Birthday: {character.birthday}")
        print()

        # Resolve corporation name
        names = await client.async_resolve_names([character.corporation_id])
        if names:
            print(f"Corporation: {names[0].name}")
        print()

        # Portrait
        portrait = await client.async_get_character_portrait(2113024536)
        print(f"Portrait 256px: {portrait.px256x256}")


if __name__ == "__main__":
    asyncio.run(main())

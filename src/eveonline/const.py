"""Constants for the Eve Online ESI API."""

from typing import Final

# ESI API
ESI_BASE_URL: Final = "https://esi.evetech.net/latest"
ESI_DATASOURCE: Final = "tranquility"

# EVE SSO
SSO_AUTHORIZE_URL: Final = "https://login.eveonline.com/v2/oauth/authorize"
SSO_TOKEN_URL: Final = "https://login.eveonline.com/v2/oauth/token"
SSO_JWKS_URL: Final = "https://login.eveonline.com/oauth/jwks"

# Scopes
SCOPE_READ_ONLINE: Final = "esi-location.read_online.v1"
SCOPE_READ_LOCATION: Final = "esi-location.read_location.v1"
SCOPE_READ_SHIP_TYPE: Final = "esi-location.read_ship_type.v1"
SCOPE_READ_WALLET: Final = "esi-wallet.read_character_wallet.v1"
SCOPE_READ_SKILLS: Final = "esi-skills.read_skills.v1"
SCOPE_READ_SKILLQUEUE: Final = "esi-skills.read_skillqueue.v1"
SCOPE_READ_KILLMAILS: Final = "esi-killmails.read_killmails.v1"
SCOPE_READ_CLONES: Final = "esi-clones.read_clones.v1"
SCOPE_READ_IMPLANTS: Final = "esi-clones.read_implants.v1"
SCOPE_READ_NOTIFICATIONS: Final = "esi-characters.read_notifications.v1"
SCOPE_READ_FATIGUE: Final = "esi-characters.read_fatigue.v1"
SCOPE_READ_MAIL: Final = "esi-mail.read_mail.v1"
SCOPE_READ_INDUSTRY_JOBS: Final = "esi-industry.read_character_jobs.v1"
SCOPE_READ_MARKET_ORDERS: Final = "esi-markets.read_character_orders.v1"

# Default scopes for a typical Home Assistant integration
DEFAULT_SCOPES: Final = [
    SCOPE_READ_ONLINE,
    SCOPE_READ_LOCATION,
    SCOPE_READ_SHIP_TYPE,
    SCOPE_READ_WALLET,
    SCOPE_READ_SKILLS,
    SCOPE_READ_SKILLQUEUE,
    SCOPE_READ_FATIGUE,
    SCOPE_READ_MAIL,
    SCOPE_READ_INDUSTRY_JOBS,
    SCOPE_READ_MARKET_ORDERS,
]

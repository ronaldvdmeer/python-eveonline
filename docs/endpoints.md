# Endpoint Reference

All methods are `async` and belong to `EveOnlineClient`. Public endpoints only need a `session`; authenticated endpoints require `auth`.

---

## Public endpoints

### `async_get_server_status()`

Get the current Tranquility server status.

```python
status = await client.async_get_server_status()
```

**Returns:** `ServerStatus`

| Field | Type | Description |
|---|---|---|
| `players` | `int` | Players currently online |
| `server_version` | `str` | Server build version |
| `start_time` | `datetime` | When the server last started |
| `vip` | `bool \| None` | VIP mode active |

---

### `async_get_character_public(character_id)`

Get public information about any character.

```python
char = await client.async_get_character_public(2117905894)
print(char.name, char.corporation_id)
```

**Returns:** `CharacterPublicInfo`

| Field | Type | Description |
|---|---|---|
| `character_id` | `int` | EVE character ID |
| `name` | `str` | Character name |
| `corporation_id` | `int` | Current corporation |
| `birthday` | `datetime` | Character creation date |
| `gender` | `str` | `"male"` or `"female"` |
| `race_id` | `int` | Race identifier |
| `bloodline_id` | `int` | Bloodline identifier |
| `ancestry_id` | `int \| None` | Ancestry identifier |
| `alliance_id` | `int \| None` | Alliance, if any |
| `security_status` | `float \| None` | Security standing |

---

### `async_get_character_portrait(character_id)`

Get portrait image URLs for a character.

```python
portrait = await client.async_get_character_portrait(2117905894)
print(portrait.px256x256)  # URL to 256x256 image
```

**Returns:** `CharacterPortrait`

| Field | Type | Description |
|---|---|---|
| `px64x64` | `str \| None` | 64×64 portrait URL |
| `px128x128` | `str \| None` | 128×128 portrait URL |
| `px256x256` | `str \| None` | 256×256 portrait URL |
| `px512x512` | `str \| None` | 512×512 portrait URL |

---

### `async_get_corporation_public(corporation_id)`

Get public information about a corporation.

```python
corp = await client.async_get_corporation_public(98553333)
print(corp.name, corp.ticker, corp.member_count)
```

**Returns:** `CorporationPublicInfo`

| Field | Type | Description |
|---|---|---|
| `corporation_id` | `int` | Corporation ID |
| `name` | `str` | Corporation name |
| `ticker` | `str` | Ticker symbol |
| `member_count` | `int` | Number of members |
| `ceo_id` | `int` | CEO character ID |
| `tax_rate` | `float` | Tax rate (0.0–1.0) |
| `alliance_id` | `int \| None` | Alliance, if any |
| `date_founded` | `datetime \| None` | Founding date |

---

### `async_resolve_names(ids)`

Resolve a list of EVE entity IDs to names and categories.

```python
names = await client.async_resolve_names([2117905894, 98553333, 30000142])
for n in names:
    print(f"{n.name} ({n.category})")
# → Jita (solar_system), CCP (corporation), ...
```

**Returns:** `list[UniverseName]`

| Field | Type | Description |
|---|---|---|
| `id` | `int` | Entity ID |
| `name` | `str` | Display name |
| `category` | `str` | `"character"`, `"corporation"`, `"solar_system"`, etc. |

Returns an empty list when called with an empty `ids` list.

---

## Authenticated endpoints

All authenticated endpoints require `EveOnlineClient(auth=...)`. See [Authentication](authentication.md) for scope details.

---

### `async_get_character_online(character_id)`

Scope: `esi-location.read_online.v1`

```python
status = await client.async_get_character_online(character_id)
if status.online:
    print(f"Online since {status.last_login}")
```

**Returns:** `CharacterOnlineStatus`

| Field | Type | Description |
|---|---|---|
| `online` | `bool` | Currently online |
| `last_login` | `datetime \| None` | Last login time |
| `last_logout` | `datetime \| None` | Last logout time |
| `logins` | `int \| None` | Total login count |

---

### `async_get_character_location(character_id)`

Scope: `esi-location.read_location.v1`

```python
loc = await client.async_get_character_location(character_id)
print(f"System: {loc.solar_system_id}")
if loc.station_id:
    print(f"Docked at station {loc.station_id}")
```

**Returns:** `CharacterLocation`

| Field | Type | Description |
|---|---|---|
| `solar_system_id` | `int` | Current solar system |
| `station_id` | `int \| None` | NPC station, if docked |
| `structure_id` | `int \| None` | Player structure, if docked |

---

### `async_get_character_ship(character_id)`

Scope: `esi-location.read_ship_type.v1`

```python
ship = await client.async_get_character_ship(character_id)
print(f"In: {ship.ship_name} (type {ship.ship_type_id})")
```

**Returns:** `CharacterShip`

| Field | Type | Description |
|---|---|---|
| `ship_type_id` | `int` | Ship type ID |
| `ship_item_id` | `int` | Unique item ID of this ship |
| `ship_name` | `str` | Player-assigned name |

---

### `async_get_wallet_balance(character_id)`

Scope: `esi-wallet.read_character_wallet.v1`

```python
wallet = await client.async_get_wallet_balance(character_id)
print(f"{wallet.balance:,.2f} ISK")
```

**Returns:** `WalletBalance`

| Field | Type | Description |
|---|---|---|
| `balance` | `float` | ISK balance |

---

### `async_get_skills(character_id)`

Scope: `esi-skills.read_skills.v1`

```python
skills = await client.async_get_skills(character_id)
print(f"{skills.total_sp:,} SP total, {skills.unallocated_sp:,} unallocated")
```

**Returns:** `CharacterSkillsSummary`

| Field | Type | Description |
|---|---|---|
| `total_sp` | `int` | Total skill points |
| `unallocated_sp` | `int` | Free/unallocated skill points |

---

### `async_get_skill_queue(character_id)`

Scope: `esi-skills.read_skillqueue.v1`

```python
queue = await client.async_get_skill_queue(character_id)
if queue:
    current = queue[0]  # position 0 is actively training
    print(f"Training skill {current.skill_id} to level {current.finished_level}")
    print(f"Finishes: {current.finish_date}")
```

**Returns:** `list[SkillQueueEntry]`, ordered by `queue_position`

| Field | Type | Description |
|---|---|---|
| `skill_id` | `int` | Skill type ID |
| `queue_position` | `int` | Position in queue (0 = active) |
| `finished_level` | `int` | Level being trained to |
| `start_date` | `datetime \| None` | Training start time |
| `finish_date` | `datetime \| None` | Estimated finish time |
| `level_end_sp` | `int \| None` | SP required to complete level |

---

### `async_get_mail_labels(character_id)`

Scope: `esi-mail.read_mail.v1`

```python
mail = await client.async_get_mail_labels(character_id)
print(f"{mail.total_unread_count} unread messages")
```

**Returns:** `MailLabelsSummary`

| Field | Type | Description |
|---|---|---|
| `total_unread_count` | `int` | Total unread mail count |

---

### `async_get_industry_jobs(character_id, *, include_completed=False)`

Scope: `esi-industry.read_character_jobs.v1`

```python
jobs = await client.async_get_industry_jobs(character_id)
active = [j for j in jobs if j.status == "active"]
print(f"{len(active)} active jobs")
```

**Returns:** `list[IndustryJob]`

| Field | Type | Description |
|---|---|---|
| `job_id` | `int` | Job ID |
| `activity_id` | `int` | Activity (1=manufacturing, 3=TE research, etc.) |
| `status` | `str` | `"active"`, `"delivered"`, `"cancelled"`, etc. |
| `start_date` | `datetime` | Job start time |
| `end_date` | `datetime` | Scheduled completion time |
| `runs` | `int` | Number of runs |
| `cost` | `float \| None` | Installation cost in ISK |

Pass `include_completed=True` to also return delivered/cancelled jobs.

---

### `async_get_market_orders(character_id)`

Scope: `esi-markets.read_character_orders.v1`

```python
orders = await client.async_get_market_orders(character_id)
buy_orders = [o for o in orders if o.is_buy_order]
sell_orders = [o for o in orders if not o.is_buy_order]
print(f"{len(buy_orders)} buy / {len(sell_orders)} sell orders")
```

**Returns:** `list[MarketOrder]`

| Field | Type | Description |
|---|---|---|
| `order_id` | `int` | Order ID |
| `type_id` | `int` | Item type ID |
| `is_buy_order` | `bool` | `True` for buy, `False` for sell |
| `price` | `float` | Price per unit in ISK |
| `volume_remain` | `int` | Units remaining |
| `volume_total` | `int` | Original volume |
| `region_id` | `int` | Region |
| `issued` | `datetime` | Order creation/update time |

---

### `async_get_jump_fatigue(character_id)`

Scope: `esi-characters.read_fatigue.v1`

```python
fatigue = await client.async_get_jump_fatigue(character_id)
if fatigue.jump_fatigue_expire_date:
    print(f"Fatigue expires: {fatigue.jump_fatigue_expire_date}")
```

**Returns:** `JumpFatigue`

| Field | Type | Description |
|---|---|---|
| `jump_fatigue_expire_date` | `datetime \| None` | When fatigue expires |
| `last_jump_date` | `datetime \| None` | Last jump timestamp |
| `last_update_date` | `datetime \| None` | Data update timestamp |

---

### `async_get_notifications(character_id)`

Scope: `esi-characters.read_notifications.v1`

```python
notifications = await client.async_get_notifications(character_id)
unread = [n for n in notifications if not n.is_read]
print(f"{len(unread)} unread notifications")
```

**Returns:** `list[CharacterNotification]`

| Field | Type | Description |
|---|---|---|
| `notification_id` | `int` | Notification ID |
| `sender_id` | `int` | Sender entity ID |
| `sender_type` | `str` | `"character"`, `"corporation"`, etc. |
| `type` | `str` | Notification type (e.g. `"StructureUnderAttack"`) |
| `timestamp` | `datetime` | When the notification was sent |
| `is_read` | `bool \| None` | Whether it has been read |
| `text` | `str \| None` | YAML-encoded notification body |

---

### `async_get_clones(character_id)`

Scope: `esi-clones.read_clones.v1`

```python
clones = await client.async_get_clones(character_id)
print(f"Home: {clones.home_location.location_id}")
print(f"{len(clones.jump_clones)} jump clones")
```

**Returns:** `CharacterClones`

| Field | Type | Description |
|---|---|---|
| `home_location` | `CloneHomeLocation \| None` | Medical clone station/structure |
| `jump_clones` | `tuple[JumpClone, ...]` | List of jump clones |
| `last_clone_jump_date` | `datetime \| None` | Last clone jump |
| `last_station_change_date` | `datetime \| None` | Last home station change |

`CloneHomeLocation` fields: `location_id` (int), `location_type` (str).

`JumpClone` fields: `jump_clone_id` (int), `location_id` (int), `location_type` (str), `implants` (tuple[int, ...]), `name` (str | None).

---

### `async_get_implants(character_id)`

Scope: `esi-clones.read_implants.v1`

```python
implants = await client.async_get_implants(character_id)
print(f"{len(implants)} active implants: {implants}")
```

**Returns:** `tuple[int, ...]` — type IDs of active implants.

---

### `async_get_wallet_journal(character_id)`

Scope: `esi-wallet.read_character_wallet.v1`

```python
journal = await client.async_get_wallet_journal(character_id)
for entry in journal[:5]:
    print(f"{entry.date}: {entry.ref_type} {entry.amount:+,.2f} ISK")
```

**Returns:** `list[WalletJournalEntry]`

| Field | Type | Description |
|---|---|---|
| `id` | `int` | Journal entry ID |
| `date` | `datetime` | Transaction time |
| `ref_type` | `str` | Transaction type (e.g. `"bounty_prizes"`) |
| `description` | `str` | Human-readable description |
| `amount` | `float \| None` | ISK amount (+income / −expense) |
| `balance` | `float \| None` | Balance after transaction |
| `first_party_id` | `int \| None` | First party ID |
| `second_party_id` | `int \| None` | Second party ID |
| `reason` | `str \| None` | Additional reason text |

---

### `async_get_contacts(character_id)`

Scope: `esi-characters.read_contacts.v1`

```python
contacts = await client.async_get_contacts(character_id)
friends = [c for c in contacts if c.standing > 0]
print(f"{len(friends)} friendly contacts")
```

**Returns:** `list[CharacterContact]`

| Field | Type | Description |
|---|---|---|
| `contact_id` | `int` | Contact entity ID |
| `contact_type` | `str` | `"character"`, `"corporation"`, `"alliance"`, `"faction"` |
| `standing` | `float` | Standing (-10.0 to +10.0) |
| `is_blocked` | `bool \| None` | Whether blocked |
| `is_watched` | `bool \| None` | Whether on watch list |
| `label_ids` | `tuple[int, ...] \| None` | Assigned label IDs |

---

### `async_get_calendar(character_id)`

Scope: `esi-calendar.read_calendar_events.v1`

```python
events = await client.async_get_calendar(character_id)
for event in events:
    print(f"{event.event_date}: {event.title}")
```

**Returns:** `list[CalendarEvent]`

| Field | Type | Description |
|---|---|---|
| `event_id` | `int` | Event ID |
| `event_date` | `datetime` | Event start time |
| `title` | `str` | Event title |
| `importance` | `int \| None` | 0 = normal, 1 = important |
| `event_response` | `str \| None` | `"accepted"`, `"declined"`, `"tentative"`, `"not_responded"` |

---

### `async_get_loyalty_points(character_id)`

Scope: `esi-characters.read_loyalty.v1`

```python
lp = await client.async_get_loyalty_points(character_id)
for entry in lp:
    print(f"Corp {entry.corporation_id}: {entry.loyalty_points:,} LP")
```

**Returns:** `list[LoyaltyPoints]`

| Field | Type | Description |
|---|---|---|
| `corporation_id` | `int` | Corporation ID |
| `loyalty_points` | `int` | LP accumulated |

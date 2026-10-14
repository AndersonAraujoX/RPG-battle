# WebSocket Multiplayer Protocol Specification
**Project:** Cerco da Fortaleza contra Isectum (RPG-battle Godot 4 Migration)  
**Author:** `m6_spec_miner_1` (Specification Miner)  
**Target Client:** `godot_project/scripts/network/WebSocketClient.gd`  
**Authoritative Sources:**
- `src/server/protocol.py` (Message types, Pydantic schemas)
- `src/server/room_manager.py` (Room lifecycle, connection pool, broadcast rules)
- `src/server/app.py` (FastAPI routes, WebSocket endpoint, query parameters, dispatch logic)
- `src/server/session.py` (CoopSession authoritative engine, rules, state serialization, anti-cheat)
- `tests/test_coop_server.py` (Canonical validation suite for authority, synchrony, and integration)
- `web/coop/app.js` (Reference frontend client implementation)

---

## 1. Executive Summary

The multiplayer co-op architecture of RPG-battle is an **authoritative server model** over WebSockets with supplementary HTTP REST endpoints.
- The server (`src/server/app.py` running via Uvicorn on port 8000) maintains complete authoritative control over:
  - Game state, turns, phases, and rounds.
  - Tactical grid (20x20) occupancy and terrain modifications.
  - Hero action points (Movement, Work, Excavation), decks, hands, and discards.
  - Combat resolution (D20 attack rolls vs target AC, damage application, enemy defeat, and team victory).
  - Enemy AI advance and melee/ranged attacks.
  - Anti-cheat privacy (each player's secret hand is only delivered to that specific player; all other players receive an empty array `hand: []` with only `cards_count`).
- Communication is asynchronous JSON-based message framing across persistent WebSocket connections.
- The protocol supports up to **4 players per room**, automated room creation, graceful disconnection flagging (`connected: false`), and stateful seamless reconnection using the persistent `player_id`.

---

## 2. Network Topology & Connection Endpoints

### 2.1 Transport Protocols
- **WebSocket (RFC 6455):** Bidirectional, event-driven, text-frame JSON communication for live gameplay.
- **HTTP/1.1 REST:** Stateless queries for pre-flight connectivity, hero roster catalog, room listing, and creation.
- **Default Port:** `8000` (e.g. `http://127.0.0.1:8000`, `ws://127.0.0.1:8000/ws/...`).
- **CORS:** Enabled for all origins (`*`) with credentials, methods, and headers allowed.

### 2.2 HTTP REST Endpoints
| Method | Endpoint | Query / Body | Response Status | Response Schema | Description |
|---|---|---|---|---|---|
| `GET` | `/api/health` | None | `200 OK` | `{"status": "ok", "active_rooms": int, "total_heroes": int}` | Health check and server metric summary |
| `GET` | `/api/heroes` | None | `200 OK` | Array of 7 Hero Descriptor Objects (see schema below) | Roster of playable heroes with stats & icons |
| `GET` | `/api/rooms` | None | `200 OK` | Array of Room Objects: `[{"room_id": str, "players_count": int, "max_players": 4, "fase": str, "created_at": float}]` | Lists active rooms; runs idle room cleanup (>300s) |
| `POST` | `/api/rooms` | Query: `room_id: Optional[str]` | `200 OK` | `{"room_id": str, "fase": str, "players_count": int, "created_at": float}` | Creates or gets room with uppercase code |

#### Hero Descriptor Object (`GET /api/heroes`)
```json
{
  "nome": "Aquele",
  "classe": "Guerreiro",
  "icone": "🌑",
  "sprite_url": "/assets/images/characters/heroes/Aquele.png",
  "hp_base": 50,
  "ac": 16,
  "descricao": "Guerreiro sombrio implacável com alto poder de absorção e contra-ataques brutais.",
  "especial": "Ataque Furioso & Vanguarda"
}
```
*Playable Heroes:* `"Aquele"` (Guerreiro), `"Stark"` (Paladino), `"Elden"` (Mago), `"Doom"` (Ladino), `"Gruu"` (Bárbaro), `"Kuro"` (Ladino), `"Darwin"` (Druida).

### 2.3 WebSocket Connection Endpoint & Handshake

#### URL Scheme
```
ws://{host}:{port}/ws/{room_id}/{player_id}?player_name={player_name}
```
or `wss://` when TLS is terminated.

#### Path & Query Parameters
- `{room_id}` (string, path parameter): Alphanumeric room code (e.g. `"SALA01"`, `"K7N9W2"`).
  - Normalization: Automatically upper-cased and whitespace-stripped (`room_id.upper().strip()`).
  - Auto-creation: If the room does not exist upon connection, the server creates it automatically.
- `{player_id}` (string, path parameter): Unique client session identifier (e.g. `"p_abc1234"` or UUID).
  - Used as session key to preserve hero assignment, hand, and position across temporary disconnections.
- `player_name` (string, query parameter, default: `"Aventureiro"`): Display name for the player in the room and combat log.

#### Handshake Sequence
1. **Connect:** Client initiates WebSocket handshake.
2. **Accept:** Server executes `await websocket.accept()`.
3. **Room Check:** Server retrieves or creates the `Room`.
4. **Capacity Check:** Server executes `room.session.add_player(player_id, player_name)`:
   - **Case A: Room Full (> 4 players and `player_id` is new):**
     * Server transmits an `ERROR` message:
       ```json
       {
         "type": "ERROR",
         "payload": {
           "mensagem": "A sala atingiu o limite de 4 jogadores."
         }
       }
       ```
     * Server executes `await websocket.close()`.
   - **Case B: Existing Player (Reconnection):**
     * Sets `player.connected = True`. Preserves hero, hand, AP, and position.
   - **Case C: New Player (< 4 players):**
     * Adds player to `room.session.jogadores` with `ready = False`, `hero_name = None`.
     * Adds log: `[SALA] ⚔️ {player_name} entrou na sala.`
5. **Connection Pool:** Server stores connection in `room.connections[player_id] = websocket`.
6. **Initial Broadcast:** Server immediately broadcasts personalized `STATE_UPDATE` to all connected clients in the room.

---

## 3. Message Framing & Serialization Rules

### 3.1 Frame Structure
All WebSocket frames are text frames containing a single serialized JSON object formatted as:
```json
{
  "type": "<MessageType>",
  "payload": { ... }
}
```

### 3.2 Canonical Message Types (`MessageType` Enum)
```python
# Client -> Server
JOIN_ROOM      = "JOIN_ROOM"       # Conceptual; handled via WS connection URL
SELECT_HERO    = "SELECT_HERO"     # Chooses hero class during LOBBY
START_GAME     = "START_GAME"      # Begins match when all heroes chosen
SELECT_CARD    = "SELECT_CARD"     # Locks secret card during SELECAO_CARTAS
MOVE_HERO      = "MOVE_HERO"       # Moves hero during ACAO_LIVRE
ATTACK_TARGET  = "ATTACK_TARGET"   # Attacks enemy during ACAO_LIVRE
WORK_ACTION    = "WORK_ACTION"     # Mines/repairs adjacent tile during ACAO_LIVRE
END_ROUND      = "END_ROUND"       # Concludes action phase, draws cards, advances round
CHAT_MESSAGE   = "CHAT_MESSAGE"    # Sends text chat to combat log
PING           = "PING"            # Keepalive ping frame

# Server -> Client
STATE_UPDATE   = "STATE_UPDATE"    # Comprehensive full-state synchronization
ACTION_REJECTED= "ACTION_REJECTED" # Informs client why an action was invalid
ERROR          = "ERROR"           # Fatal or high-level error message
PONG           = "PONG"            # Keepalive pong response
ROOM_STATE     = "ROOM_STATE"      # Legacy enum entry
GAME_STARTED   = "GAME_STARTED"    # Legacy enum entry
CARD_LOCKED    = "CARD_LOCKED"     # Legacy enum entry
ROUND_RESOLVED = "ROUND_RESOLVED"  # Legacy enum entry
COMBAT_LOG     = "COMBAT_LOG"      # Legacy enum entry
```

---

## 4. Client -> Server Messages (Detailed Schemas)

### 4.1 `SELECT_HERO`
Player selects a hero during the lobby phase.

**JSON Payload:**
```json
{
  "type": "SELECT_HERO",
  "payload": {
    "hero_name": "Aquele"
  }
}
```
- `hero_name` (String, required): Must match one of `["Aquele", "Stark", "Elden", "Doom", "Gruu", "Kuro", "Darwin"]`.
- **Validation Rules:**
  1. Game phase must be `"LOBBY"`.
  2. `hero_name` must be registered in `CLASSES_HEROIS`.
  3. `hero_name` must not be already selected by another player in the room.
- **Success Outcome:**
  - Player's `hero_name` is set, `ready` becomes `True`.
  - Log entry: `[LOBBY] 🛡️ {player_name} escolheu {hero_name}.`
  - Broadcasts `STATE_UPDATE`.
- **Failure Outcome:**
  - Sends `ACTION_REJECTED`: `{"acao": "SELECT_HERO", "motivo": "<reason>"}`.

---

### 4.2 `START_GAME`
Starts the match once all connected players are ready with chosen heroes.

**JSON Payload:**
```json
{
  "type": "START_GAME",
  "payload": {}
}
```
- **Validation Rules:**
  1. Game phase must be `"LOBBY"`.
  2. At least 1 player must be in the room (`len(jogadores) > 0`).
  3. Every connected player must have selected a valid hero (`p.hero_name is not None`).
- **Success Outcome:**
  - `fase` transitions to `"SELECAO_CARTAS"`.
  - `round_atual` initialized to `1`.
  - Instantiates heroes on the board at fixed coordinates:
    * Index 0: `(9, 10)`
    * Index 1: `(10, 10)`
    * Index 2: `(9, 11)`
    * Index 3: `(10, 11)`
  - Decks prepared for each hero from 12 basic action cards (`CARTAS_BASICAS`), shuffled, and 4 cards dealt to `mao` (hand).
  - Initial wave of Isectum invaders spawned at perimeter locations:
    * `(2, 2)`, `(17, 2)`, `(2, 17)`, `(17, 17)`, `(10, 2)`, `(10, 18)`.
    * Enemy types: `TrabalhadorIsectum` (HP 18, AC 11), `GuerreiroIsectum` (HP 30, AC 14), `ExploradorIsectum` (HP 22, AC 13).
  - Broadcasts `STATE_UPDATE`.
- **Failure Outcome:**
  - Sends `ACTION_REJECTED`: `{"acao": "START_GAME", "motivo": "Nem todos os jogadores escolheram seus heróis."}`.

---

### 4.3 `SELECT_CARD`
Locks in a card from the player's hand during simultaneous turn synchrony.

**JSON Payload:**
```json
{
  "type": "SELECT_CARD",
  "payload": {
    "card_idx": 0
  }
}
```
- `card_idx` (Integer, required): 0-based index in the player's secret `hand` array.
- **Validation Rules:**
  1. Game phase must be `"SELECAO_CARTAS"`.
  2. Player must exist and hero must be alive (`hp_atual > 0`).
  3. Index must be valid (`0 <= card_idx < len(mao)`).
- **Success Outcome:**
  - Card locked in `cartas_selecionadas[player_id] = {"idx": card_idx, "carta": carta}`.
  - Log entry: `[CARTAS] 🃏 {player_name} ({hero_name}) travou uma carta secreta.`
  - **Auto-Resolution:** If all living heroes have locked a card:
    * Automatically triggers `session.resolve_round()`.
    * Transitions phase to `"ACAO_LIVRE"`.
    * Resolves Team / Supreme synergies (see Section 7).
    * Deducts cards from hands into discard piles.
    * Converts card values into Action Points:
      - Movement AP: `max(1, mov // 5)` if `mov >= 5` else `max(1, mov)`.
      - Work AP: `carta.trabalho`.
      - Excavation AP: `carta.escavacao`.
    * Enemy AI step: Enemies step 1 tile toward nearest hero or attack if adjacent (`dist == 1`, 3-7 damage).
  - Broadcasts `STATE_UPDATE`.
- **Failure Outcome:**
  - Sends `ACTION_REJECTED`.

---

### 4.4 `MOVE_HERO`
Moves the player's hero along an A* path during free action phase.

**JSON Payload:**
```json
{
  "type": "MOVE_HERO",
  "payload": {
    "dest_x": 10,
    "dest_y": 12
  }
}
```
- `dest_x` (Integer, required): Target X coordinate (0 to 19).
- `dest_y` (Integer, required): Target Y coordinate (0 to 19).
- **Validation Rules:**
  1. Game phase must be `"ACAO_LIVRE"`.
  2. Player authorized; hero alive (`hp_atual > 0`).
  3. Within grid bounds: `0 <= dest_x < 20` and `0 <= dest_y < 20`.
  4. Target tile is not a wall: `terrain_grid[dest_y][dest_x] != TERRENO_PAREDE` (3).
  5. Target tile is not occupied: `grid[dest_y][dest_x] is None`.
  6. Valid path exists: `len(caminho) > 0`.
  7. Sufficient Movement AP: `player.pontos_movimento >= len(caminho)`.
- **Success Outcome:**
  - Hero old position cleared, new position set.
  - `player.pontos_movimento -= len(caminho)`.
  - Log: `[MOVIMENTO] 🏃 {hero_name} moveu-se para ({dest_x}, {dest_y}).`
  - Broadcasts `STATE_UPDATE`.
- **Failure Outcome:**
  - Sends `ACTION_REJECTED`.

---

### 4.5 `ATTACK_TARGET`
Attacks an enemy occupying the specified grid coordinate.

**JSON Payload:**
```json
{
  "type": "ATTACK_TARGET",
  "payload": {
    "target_x": 11,
    "target_y": 12,
    "habilidade": null
  }
}
```
- `target_x` (Integer, required): Target cell X.
- `target_y` (Integer, required): Target cell Y.
- `habilidade` (String or null, optional): Special ability name if triggered.
- **Validation Rules:**
  1. Game phase must be `"ACAO_LIVRE"`.
  2. Hero alive.
  3. Alive enemy present at `(target_x, target_y)`.
  4. Range check (Manhattan distance `|dx| + |dy|`):
     - `alcance_max = 8` if hero is `"Elden"` (Mago).
     - `alcance_max = 2` for all other classes.
     - Distance must be `<= alcance_max`.
- **Combat Resolution:**
  - D20 roll: `d20 = random.randint(1, 20)`.
  - Armor Class: `ac_alvo = alvo.ac_base + cobertura_bonus`.
  - Hit check: `(d20 + 4 >= ac_alvo) or (d20 == 20)`.
  - On Hit:
    * Damage: `random.randint(6, 14)`.
    * Target HP reduced.
    * If enemy defeated (`hp_atual <= 0`):
      - Enemy removed from grid.
      - Team receives +1 Cristal (`recursos["cristal"] += 1`).
      - Victory check: If all enemies defeated -> `fase = "VITORIA"`.
  - Broadcasts `STATE_UPDATE`.
- **Failure Outcome:**
  - Sends `ACTION_REJECTED`.

---

### 4.6 `WORK_ACTION`
Clears adjacent debris/rocks or harvests materials using Work/Excavation AP.

**JSON Payload:**
```json
{
  "type": "WORK_ACTION",
  "payload": {
    "target_x": 10,
    "target_y": 11,
    "tipo": "minerar"
  }
}
```
- `target_x` (Integer, required): Adjacent target tile X.
- `target_y` (Integer, required): Adjacent target tile Y.
- `tipo` (String, optional, default: `"minerar"`): `"minerar"`, `"reparar"`, or `"coletar"`.
- **Validation Rules:**
  1. Game phase must be `"ACAO_LIVRE"`.
  2. Adjacency: `|hero.x - target_x| + |hero.y - target_y| <= 1`.
  3. AP check: `player.pontos_escavacao > 0` or `player.pontos_trabalho > 0`.
  4. Terrain check: Target must be `TERRENO_ROCHA` (4), `TERRENO_FLORESTA` (1), or `TERRENO_BARRIL` (5).
- **Success Outcome:**
  - Terrain transforms to `TERRENO_NORMAL` (0).
  - Deducts 1 Excavation AP (or 1 Work AP if Excavation is 0).
  - Team gains resources: `recursos["madeira"] += 1`, `recursos["metal"] += 1`.
  - Broadcasts `STATE_UPDATE`.
- **Failure Outcome:**
  - Sends `ACTION_REJECTED`.

---

### 4.7 `END_ROUND`
Ends free actions for the round, refills hands, and initiates next synchrony round.

**JSON Payload:**
```json
{
  "type": "END_ROUND",
  "payload": {}
}
```
- **Validation Rules:**
  1. Game phase must be `"ACAO_LIVRE"`.
  2. Player must be authorized.
- **Success Outcome:**
  - Action points reset to 0 for all players.
  - Hand refill: Each player draws from their deck until hand size reaches 4. If deck is exhausted, discard pile is reshuffled into deck.
  - Round counter incremented (`round_atual += 1`).
  - Phase resets to `"SELECAO_CARTAS"`.
  - Locked card slots cleared (`cartas_selecionadas` set to None for all living heroes).
  - Active synergy cleared (`sinergia_ativa = null`).
  - Broadcasts `STATE_UPDATE`.
- **Failure Outcome:**
  - Sends `ACTION_REJECTED`.

---

### 4.8 `CHAT_MESSAGE`
Sends a text chat message to the room's combat log.

**JSON Payload:**
```json
{
  "type": "CHAT_MESSAGE",
  "payload": {
    "text": "Inimigo avança pelo flanco oeste!"
  }
}
```
- `text` (String, required): Message string.
- **Behavior:**
  - Formats author as: `"💬 {player_name} ({hero_name})"` or `"💬 {player_name}"`.
  - Appends entry to `combat_log` with color `"#c084fc"`.
  - Broadcasts `STATE_UPDATE`.

---

### 4.9 `PING`
Keepalive ping message from client.

**JSON Payload:**
```json
{
  "type": "PING",
  "payload": {}
}
```
- **Behavior:** Server responds with `PONG`.

---

## 5. Server -> Client Messages & State Payloads

### 5.1 `STATE_UPDATE` (Core Synchronization Frame)
Sent on every state mutation. Uses **Anti-Cheat Hand Filtering**: the server serializes `hand` ONLY for the receiving player (`is_me = true`). All other players receive `hand: []` with `cards_count` and `card_locked`.

**Schema:**
```json
{
  "type": "STATE_UPDATE",
  "payload": {
    "room_id": "ABCDEF",
    "fase": "LOBBY",
    "round": 1,
    "sinergia_ativa": null,
    "recursos": {
      "madeira": 0,
      "couro": 0,
      "metal": 0,
      "cristal": 0
    },
    "heroes": [
      {
        "player_id": "p_123456",
        "player_name": "Alice",
        "hero_name": "Aquele",
        "sprite_url": "/assets/images/characters/heroes/Aquele.png",
        "hp_atual": 50,
        "hp_max": 50,
        "ac": 16,
        "pos_x": 9,
        "pos_y": 10,
        "pontos_movimento": 2,
        "pontos_trabalho": 0,
        "pontos_escavacao": 0,
        "cards_count": 4,
        "hand": [
          {
            "id": "marcha_1",
            "nome": "Marcha",
            "simbolo": "M",
            "tipo": "basica",
            "movimento": 15,
            "trabalho": 0,
            "escavacao": 0,
            "descricao": "+15 Movimento"
          }
        ],
        "is_me": true,
        "card_locked": false,
        "ready": true,
        "connected": true
      }
    ],
    "enemies": [
      {
        "id": "TrabalhadorIsectum_1",
        "nome": "TrabalhadorIsectum_1",
        "tipo": "TrabalhadorIsectum",
        "sprite_url": "/assets/images/characters/monsters/isectum/besouro_gorgulho.png",
        "hp_atual": 18,
        "hp_max": 18,
        "pos_x": 2,
        "pos_y": 2
      }
    ],
    "grid_terreno": [
      [3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3],
      [3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3]
    ],
    "combat_log": [
      {
        "autor": "CERCO",
        "texto": "🚨 O cerco Isectum começou! Escolham suas cartas para o Round 1.",
        "cor": "#e11d48"
      }
    ]
  }
}
```

#### Field Specifications:
- `room_id` (String): Normalized room code.
- `fase` (String): Current phase: `"LOBBY"`, `"SELECAO_CARTAS"`, `"ACAO_LIVRE"`, `"VITORIA"`, `"DERROTA"`.
- `round` (Integer): 1-based round index.
- `sinergia_ativa` (Object or null):
  * When active: `{"tipo": "supremo" | "equipe", "categoria": "movimento" | "trabalho" | "escavacao" | "upgrade", "mensagem": str}`.
- `recursos` (Object): `{ "madeira": int, "couro": int, "metal": int, "cristal": int }`.
- `heroes` (Array of Player/Hero State Objects):
  * `player_id` (str)
  * `player_name` (str)
  * `hero_name` (str or null)
  * `sprite_url` (str or null)
  * `hp_atual` (int)
  * `hp_max` (int)
  * `ac` (int)
  * `pos_x` (int)
  * `pos_y` (int)
  * `pontos_movimento` (int)
  * `pontos_trabalho` (int)
  * `pontos_escavacao` (int)
  * `cards_count` (int): Number of cards currently held in hand.
  * `hand` (Array of Card Objects): Complete card list for recipient player; empty array `[]` for other players!
  * `is_me` (bool): `true` if this hero belongs to the recipient client.
  * `card_locked` (bool): `true` if player has locked their secret card for the current round.
  * `ready` (bool): `true` if player picked a hero.
  * `connected` (bool): `true` if WebSocket connection is active; `false` if disconnected.
- `enemies` (Array of Enemy State Objects):
  * `id` (str)
  * `nome` (str)
  * `tipo` (str: `"TrabalhadorIsectum"`, `"GuerreiroIsectum"`, `"ExploradorIsectum"`)
  * `sprite_url` (str)
  * `hp_atual` (int)
  * `hp_max` (int)
  * `pos_x` (int)
  * `pos_y` (int)
- `grid_terreno` (Array of 20 Arrays of 20 Integers): 20x20 terrain code matrix.
- `combat_log` (Array of Log Objects): Up to 20 most recent log entries `[{"autor": str, "texto": str, "cor": str}]`.

---

### 5.2 `ACTION_REJECTED`
Sent exclusively to the client whose request failed validation.

**Schema:**
```json
{
  "type": "ACTION_REJECTED",
  "payload": {
    "acao": "MOVE_HERO",
    "motivo": "Pontos de movimento insuficientes (1 disponíveis, 3 necessários)."
  }
}
```
- `acao` (String): The action that failed (e.g. `"SELECT_HERO"`, `"START_GAME"`, `"SELECT_CARD"`, `"MOVE_HERO"`, `"ATTACK_TARGET"`, `"WORK_ACTION"`, `"END_ROUND"`).
- `motivo` (String): Human-readable Portuguese explanation of why the action was rejected.
- **Client Reaction:**
  - Play error / miss audio effect.
  - Emit signal `action_rejected(action, reason)`.
  - Update UI feedback without corrupting local state.

---

### 5.3 `ERROR`
Sent upon fatal connection-level errors (e.g. room full).

**Schema:**
```json
{
  "type": "ERROR",
  "payload": {
    "mensagem": "A sala atingiu o limite de 4 jogadores."
  }
}
```
- **Client Reaction:** Display dialog and close WebSocket connection. Avoid immediate auto-reconnect.

---

### 5.4 `PONG`
Heartbeat response.

**Schema:**
```json
{
  "type": "PONG",
  "payload": {}
}
```

---

## 6. Game State Machine & Phase Transitions

```
                    ┌─────────────────────────┐
                    │          LOBBY          │
                    │  (Join, Select Hero)    │
                    └────────────┬────────────┘
                                 │ START_GAME
                                 ▼
                    ┌─────────────────────────┐
          ┌────────►│     SELECAO_CARTAS      │◄─────────────────────────┐
          │         │ (Lock 1 Card in Secret) │                          │
          │         └────────────┬────────────┘                          │
          │                      │ All living heroes locked              │
          │                      ▼                                       │
          │         ┌─────────────────────────┐                          │
          │         │       ACAO_LIVRE        │                          │
          │         │ (Synergies applied,     │                          │
          │         │  AP granted, Enemies    │                          │
          │         │  advance, Move/Atk/Mine)│                          │
          │         └────────────┬────────────┘                          │
          │                      │                                       │
          │                      │ END_ROUND                             │
          │                      │ (Draw to 4,                           │
          │                      │  Round += 1)                          │
          │                      └───────────────────────────────────────┘
          │
          │ All enemies dead
          ▼
   ┌─────────────┐
   │   VITORIA   │
   └─────────────┘
```

---

## 7. Synergy System & Simultaneous Resolution

When all living heroes have selected a card (`SELECT_CARD`), `session.resolve_round()` is automatically executed:

### 7.1 Category Classification
Each played card is mapped to a focus category:
- `tipo == "upgrade"` -> `"upgrade"`
- `escavacao > 0` -> `"escavacao"`
- `trabalho > 0` -> `"trabalho"`
- Otherwise -> `"movimento"`

### 7.2 Synergy Rules
1. **Supreme Synchrony (Sincronia Suprema):**
   - Condition: All players choose the **exact same** category (and >= 2 players).
   - Team Bonus: **+2 Cristais** (`recursos["cristal"] += 2`) PLUS the category bonus.
   - Banner Message: `"🌟 SINCRONIA PERFEITA: Todos jogaram {CAT}! +2 Cristais Bônus!"`
2. **Team Synergy (Sincronia de Equipe):**
   - Condition: 2 or more players choose the same category.
   - Banner Message: `"⚡ SINCRONIA DE EQUIPE: {count}x {CAT} combinados!"`
3. **Category Bonuses (applied to all players):**
   - `"movimento"`: +2 Movement AP to each player.
   - `"trabalho"`: +2 Work AP to each player AND +1 Madeira to team resources.
   - `"escavacao"`: +3 Excavation AP to each player.

---

## 8. Terrain Matrix & Asset Mapping

The 20x20 grid is serialized in `grid_terreno` as a 20x20 array of integer codes:
| Code | Name | Description | Walkable | Blocks LOS | Mineable / Destructible | Godot Asset |
|---|---|---|---|---|---|---|
| `0` | `TERRENO_NORMAL` | Open ground | Yes | No | No | `res://assets/images/environment/terreno_normal.png` |
| `1` | `TERRENO_FLORESTA` | Forest | Yes (cost 2) | No | Yes (yields wood/metal) | `res://assets/images/environment/terreno_floresta.png` |
| `2` | `TERRENO_DIFICIL` | Difficult ground | Yes (cost 2) | No | No | `res://assets/images/environment/terreno_dificil.png` |
| `3` | `TERRENO_PAREDE` | Fortress wall | No (blocked) | Yes | No | `res://assets/images/environment/terreno_muralha_lo.png` / `parede.png` |
| `4` | `TERRENO_ROCHA` | Rock / Rubble | No (blocked) | Yes | Yes (yields wood/metal) | `res://assets/images/environment/terreno_rocha.png` |
| `5` | `TERRENO_BARRIL` | Barrel / Debris | No (blocked) | Yes | Yes (yields wood/metal) | `res://assets/images/environment/terreno_barril.png` |
| `6` | `TERRENO_FOGO` | Hazard / Fire | Yes (damage) | No | No | `res://assets/images/environment/terreno_fogo.png` |

---

## 9. Keepalive, Disconnection & Reconnection Rules

### 9.1 Keepalive / Heartbeat
- **Interval:** 15 to 30 seconds of client inactivity.
- Client sends `{"type": "PING", "payload": {}}`.
- Server responds with `{"type": "PONG", "payload": {}}`.

### 9.2 Disconnection
- When a WebSocket connection drops:
  - `room.remove_connection(player_id)` removes the socket from `room.connections`.
  - In `session.remove_player(player_id)`:
    * If `fase == "LOBBY"`: Player is purged from `session.jogadores`.
    * If `fase != "LOBBY"` (match ongoing): Player is **retained** in `session.jogadores`, with `connected` set to `false`.
    * Log entry added: `[SALA] ⚠️ {player_name} desconectou-se.`
    * Broadcasts `STATE_UPDATE` with `connected: false` for that hero.
- Idle Room Cleanup: `RoomManager.cleanup_empty_rooms(max_idle_seconds=300.0)` removes rooms with 0 active connections older than 5 minutes.

### 9.3 Reconnection
- If the disconnected client reconnects to `/ws/{room_id}/{player_id}` with the **same `player_id`**:
  - `session.add_player()` finds the existing entry.
  - Flags `connected = true`.
  - Reassociates the new WebSocket connection.
  - Fully retains hero assignment, current HP, coordinates, hand, deck, discard pile, and action points.
  - Server broadcasts `STATE_UPDATE` to all players, seamlessly resuming gameplay.

---

## Features Discovered
| # | Category | Feature | Description | Inputs | Outputs | Error Behavior | Discovered Via |
|---|----------|---------|-------------|--------|---------|----------------|----------------|
| 1 | Connection | WS Handshake | Dynamic room creation & player registration with query parameters | `room_id`, `player_id`, `player_name` query param | WS Accept + Initial `STATE_UPDATE` broadcast | Rejects with `ERROR` + close if room full (>4 players) | `src/server/app.py:162-195` |
| 2 | Lobby | Select Hero | Players choose unique hero from 7 classes | `{"type": "SELECT_HERO", "payload": {"hero_name": str}}` | `STATE_UPDATE` with updated `hero_name` and `ready=true` | `ACTION_REJECTED` if taken, invalid class, or match started | `src/server/session.py:132-150` |
| 3 | Lobby | Start Game | Transitions room to match when all players have selected heroes | `{"type": "START_GAME", "payload": {}}` | `STATE_UPDATE` (`fase="SELECAO_CARTAS"`, spawns heroes, decks, enemies) | `ACTION_REJECTED` if room empty or players missing heroes | `src/server/session.py:153-188` |
| 4 | Synchrony | Lock Secret Card | Players lock 1 card from hand during synchrony phase | `{"type": "SELECT_CARD", "payload": {"card_idx": int}}` | `STATE_UPDATE` (`card_locked=true`); auto-resolves when all locked | `ACTION_REJECTED` if wrong phase, invalid index, or hero dead | `src/server/session.py:213-237` |
| 5 | Synchrony | Synergy Resolution | Evaluates team combos (Supreme +2 crystals, Team AP bonus) | Automatic when all alive heroes lock card | `STATE_UPDATE` (`fase="ACAO_LIVRE"`, AP granted, enemies step/attack) | None (fallback to no synergy if types diverse) | `src/server/session.py:238-336` |
| 6 | Free Action | Hero Movement | Grid A* path movement consuming movement AP | `{"type": "MOVE_HERO", "payload": {"dest_x": int, "dest_y": int}}` | `STATE_UPDATE` with updated `pos_x`, `pos_y` and deducted AP | `ACTION_REJECTED` if out of bounds, wall, occupied, no path, low AP | `src/server/session.py:376-419` |
| 7 | Free Action | Hero Attack | Ranged or melee D20 attack vs enemy AC (natural 20 auto-hits) | `{"type": "ATTACK_TARGET", "payload": {"target_x": int, "target_y": int, "habilidade": null}}` | `STATE_UPDATE` (enemy HP reduced or eliminated, crystals +1, victory check) | `ACTION_REJECTED` if no enemy, out of range, or wrong phase | `src/server/session.py:420-475` |
| 8 | Free Action | Work / Mining | Clears adjacent rubble/forest to yield wood/metal materials | `{"type": "WORK_ACTION", "payload": {"target_x": int, "target_y": int, "tipo": str}}` | `STATE_UPDATE` (terrain becomes 0, resources +1 wood/metal, AP deducted) | `ACTION_REJECTED` if not adjacent, no AP, or non-mineable tile | `src/server/session.py:476-510` |
| 9 | Free Action | End Round | Ends free action phase, refills hands up to 4, advances round | `{"type": "END_ROUND", "payload": {}}` | `STATE_UPDATE` (`fase="SELECAO_CARTAS"`, `round += 1`, cards drawn) | `ACTION_REJECTED` if not in `ACAO_LIVRE` | `src/server/session.py:511-535` |
| 10 | Social | Chat Message | Broadcasts player chat message to combat log | `{"type": "CHAT_MESSAGE", "payload": {"text": str}}` | `STATE_UPDATE` with formatted log line `[💬 player (hero)] text` | Ignored if trimmed text is empty | `src/server/app.py:287-296` |
| 11 | Heartbeat | Ping / Pong | Keepalive ping frame to verify socket liveness | `{"type": "PING", "payload": {}}` | `{"type": "PONG", "payload": {}}` | Closes socket on keepalive timeout | `src/server/protocol.py:24` |
| 12 | Anti-Cheat | Hand Privacy | Filters card details so players only see their own hand | Recipient `player_id` evaluated during serialization | `is_me=true` gets full hand; other players get `hand=[]` and `cards_count` | N/A | `src/server/session.py:575-577` |
| 13 | Session | Reconnection | Seamless reconnection retaining hero, hand, deck, and position | Reconnect with identical `player_id` | `connected=true`, full state restored without reset | If disconnected during LOBBY, player is removed | `src/server/session.py:123-131` |
| 14 | REST API | Health & Catalog | Queries server status and full 7-hero stat catalog | `GET /api/health`, `GET /api/heroes` | JSON response with status, active rooms, hero descriptors | Standard HTTP 4xx/5xx | `src/server/app.py:125-140` |
| 15 | REST API | Room Management | Lists active rooms and creates new room codes | `GET /api/rooms`, `POST /api/rooms` | JSON list of rooms or created room payload | Triggers idle cleanup (>300s) | `src/server/app.py:141-158` |

---

## Edge Cases
| # | Feature | Input | Observed Behavior |
|---|---------|-------|-------------------|
| 1 | Connection Handshake | 5th player attempts to join room | Server responds with `{"type": "ERROR", "payload": {"mensagem": "A sala atingiu o limite de 4 jogadores."}}` and immediately executes `websocket.close()`. |
| 2 | Room ID Formatting | Lowercase or whitespace room code e.g. `"  sala12  "` | Automatically normalized to `"SALA12"` with `.upper().strip()`. |
| 3 | Hero Selection | Player selects hero already taken by peer | Rejection: `ACTION_REJECTED` with `"O herói {name} já foi escolhido por {peer}."`. Selection does not change. |
| 4 | Hero Selection | Player selects non-existent class name `"Ninja"` | Rejection: `ACTION_REJECTED` with `"Classe de herói 'Ninja' inválida."`. |
| 5 | Hero Selection | Player tries to switch hero after game started | Rejection: `ACTION_REJECTED` with `"O jogo já começou. Não é possível trocar de herói."`. |
| 6 | Match Start | `START_GAME` called with only 1 player who selected hero | Allowed! Match successfully starts with 1 hero; deck and enemies spawned. |
| 7 | Match Start | `START_GAME` called while one player hasn't picked | Rejection: `ACTION_REJECTED` with `"Nem todos os jogadores escolheram seus heróis."`. |
| 8 | Card Selection | `SELECT_CARD` called during `LOBBY` or `ACAO_LIVRE` | Rejection: `ACTION_REJECTED` with `"Não estamos na fase de seleção de cartas."`. |
| 9 | Card Selection | `card_idx` out of bounds (`-1` or `>= len(mao)`) | Rejection: `ACTION_REJECTED` with `"Índice de carta inválido."`. |
| 10 | Card Selection | Defeated hero (`hp_atual <= 0`) selects card | Rejection: `ACTION_REJECTED` with `"Seu herói está derrotado e não pode agir."`. Living players still proceed. |
| 11 | Movement | `MOVE_HERO` during `SELECAO_CARTAS` | Rejection: `ACTION_REJECTED` with `"Movimento liberado apenas na fase de Ação Livre."`. |
| 12 | Movement | `MOVE_HERO` with destination out of bounds (`(-1, 5)` or `(20, 20)`) | Rejection: `ACTION_REJECTED` with `"Coordenadas fora do tabuleiro."`. |
| 13 | Movement | `MOVE_HERO` targeting wall (`TERRENO_PAREDE` = 3) | Rejection: `ACTION_REJECTED` with `"Destino bloqueado por parede intransponível."`. |
| 14 | Movement | `MOVE_HERO` targeting cell occupied by another hero or enemy | Rejection: `ACTION_REJECTED` with `"A célula de destino já está ocupada."`. |
| 15 | Movement | `MOVE_HERO` when path is blocked by surrounded obstacles | Rejection: `ACTION_REJECTED` with `"Não há caminho desimpedido até o destino."`. |
| 16 | Movement | `MOVE_HERO` requires 3 steps but player only has 1 AP | Rejection: `ACTION_REJECTED` with `"Pontos de movimento insuficientes (1 disponíveis, 3 necessários)."`. |
| 17 | Attack | Attacking cell with no living enemy | Rejection: `ACTION_REJECTED` with `"Não há nenhum invasor vivo no alvo indicado."`. |
| 18 | Attack | Melee hero attacking target at distance 3 | Rejection: `ACTION_REJECTED` with `"Alvo fora de alcance (distância 3 > alcance 2)."`. |
| 19 | Attack | Mago (Elden) attacking target at distance 8 | Allowed! Elden has special class rule `alcance_max = 8`. |
| 20 | Attack | Attack roll natural 20 | Auto-hits regardless of target AC or cover bonus. |
| 21 | Attack | Final enemy killed by attack | Phase automatically transitions to `"VITORIA"`. |
| 22 | Mining | `WORK_ACTION` targeting non-adjacent tile (`dist > 1`) | Rejection: `ACTION_REJECTED` with `"Você precisa estar adjacente ao recurso para interagir."`. |
| 23 | Mining | `WORK_ACTION` targeting normal ground or wall | Rejection: `ACTION_REJECTED` with `"Não há obstáculo ou recurso escavável nesta posição."`. |
| 24 | Mining | `WORK_ACTION` with 0 work and 0 excavation AP | Rejection: `ACTION_REJECTED` with `"Sem pontos de trabalho ou escavação disponíveis."`. |
| 25 | Draw Pile Exhaustion | Player draws cards at `END_ROUND` with empty draw pile | Server automatically copies `descarte` into `deck`, clears `descarte`, shuffles `deck`, and completes drawing to 4 cards. |
| 26 | Client Disconnect | Player disconnects during combat | Player remains in `jogadores` with `connected = false`. Team sees `connected: false` in `STATE_UPDATE`. |
| 27 | Client Disconnect | Player disconnects during `LOBBY` | Player is cleanly deleted from `jogadores`. Hero selection freed. |
| 28 | Client Reconnect | Disconnected player reconnects with same `player_id` | Restored immediately: `connected = true`, hero, HP, hand, AP intact. |
| 29 | Hand Privacy | Player inspecting network packets of other heroes | Hand of all other heroes is transmitted as `[]` (empty list); cards are kept secret on server until played. |

---

## 10. Architectural Recommendations for Godot 4 `WebSocketClient.gd`

1. **Inheritance & Lifecycle:**
   - Extend `Node` with `class_name WebSocketClient`.
   - Polling via `_process(delta)` calling `_ws_peer.poll()`.
2. **Signals to Expose:**
   - `connection_established(room_id: String, player_id: String)`
   - `connection_closed(code: int, reason: String)`
   - `connection_error(error_message: String)`
   - `state_updated(state_data: Dictionary)`
   - `action_rejected(action: String, reason: String)`
   - `chat_message_received(author: String, text: String, color: String)`
3. **Signal Integration with `EventBus.gd`:**
   - On incoming `STATE_UPDATE`: emit `EventBus.network_message_received("STATE_UPDATE", payload)`.
   - On connection state change: emit `EventBus.network_connection_status_changed(connected, room_id)`.
4. **Typed Action Methods:**
   - `select_hero(hero_name: String) -> void`
   - `start_game() -> void`
   - `select_card(card_index: int) -> void`
   - `move_hero(dest_x: int, dest_y: int) -> void`
   - `attack_target(target_x: int, target_y: int, ability: String = "") -> void`
   - `work_action(target_x: int, target_y: int, action_type: String = "minerar") -> void`
   - `end_round() -> void`
   - `send_chat(text: String) -> void`
   - `send_ping() -> void`
5. **Mock Injection for GUT Unit Testing:**
   - Support injecting a mock `PacketPeer` / simulated socket so that 100% of network client tests can run offline and headless in GUT without a running FastAPI server.

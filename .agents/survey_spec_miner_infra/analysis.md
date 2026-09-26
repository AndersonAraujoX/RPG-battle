# Specification Analysis: Infrastructure, WebSocket Co-op Protocol & Asset Inventory

**Author**: `survey_spec_miner_infra`  
**Date**: 2026-09-26  
**Scope**: WebSocket Co-op Protocol, Audio/Visual Assets Catalog, Godot 4 CLI & Environment Probing, and GUT Headless Testing Architecture.

---

## Features Discovered

| # | Category | Feature | Description | Inputs | Outputs | Error Behavior | Discovered Via |
|---|----------|---------|-------------|--------|---------|----------------|----------------|
| 1 | WebSocket Protocol | Endpoint Connection Handshake | Connects a client to a multiplayer room session via WebSocket with query params | URL: `/ws/{room_id}/{player_id}?player_name={str}` | Connection accepted; initial `STATE_UPDATE` broadcast | Returns `ERROR` and closes socket if room is full (>4 players) | `src/server/app.py:162`, `src/server/room_manager.py:45` |
| 2 | WebSocket Protocol | Room Lifecycle Management | Creates and tracks room instances with unique 6-character alphanumeric codes, cleans idle rooms | `room_id: Optional[str]`, `max_idle_seconds=300.0` | Room instance with `CoopSession`, lock, and connection pool | Cleans up empty rooms older than 300s | `src/server/room_manager.py:102` |
| 3 | WebSocket Protocol | Hero Selection (`SELECT_HERO`) | Player reserves a unique hero class during `LOBBY` phase | `hero_name: str` (e.g. "Aquele", "Stark", "Elden") | `STATE_UPDATE` broadcast with hero assigned and player ready | `ACTION_REJECTED` if game already started, hero unknown, or already taken | `src/server/app.py:203`, `src/server/session.py:132` |
| 4 | WebSocket Protocol | Start Game (`START_GAME`) | Initiates combat once all connected players picked heroes | Empty payload `{}` | Phase transitions `LOBBY` -> `SELECAO_CARTAS`, spawns wave, deals 4 cards | `ACTION_REJECTED` if room is empty or any player has not selected a hero | `src/server/app.py:215`, `src/server/session.py:153` |
| 5 | WebSocket Protocol | Card Lock & Synchrony (`SELECT_CARD`) | Player locks a secret tactical card for simultaneous round resolution | `card_idx: int` (0-indexed hand position) | Card marked locked; auto-triggers `resolve_round()` if all alive picked | `ACTION_REJECTED` if not in `SELECAO_CARTAS`, hero dead, or invalid index | `src/server/app.py:226`, `src/server/session.py:213` |
| 6 | WebSocket Protocol | Synergy Resolution & AP Economy | Server computes team/supreme synchrony bonuses, discards cards, advances enemies 1 step | Internal trigger from `select_card` | `fase = "ACAO_LIVRE"`, movement/work/excavation points granted, enemy advance | None; fallback to base card points if no synergy matched | `src/server/session.py:238`, `tests/test_coop_server.py:286` |
| 7 | WebSocket Protocol | Hero Tactical Move (`MOVE_HERO`) | Moves hero along shortest A* path on 20x20 grid, consuming movement AP | `dest_x: int`, `dest_y: int` | Hero repositioned on grid, AP deducted, movement log added | `ACTION_REJECTED` if not `ACAO_LIVRE`, unauthorized, out-of-bounds, wall, occupied, or insufficient AP | `src/server/app.py:238`, `src/server/session.py:376` |
| 8 | WebSocket Protocol | Tactical Attack (`ATTACK_TARGET`) | Attacks enemy within range (Mage=8, Melee=2) using D&D 5e d20 vs AC (+cover) | `target_x: int`, `target_y: int`, `habilidade: Optional[str]` | Combat log entry with damage, target HP reduced, crystal on death | `ACTION_REJECTED` if not `ACAO_LIVRE`, no live enemy, or target out of range | `src/server/app.py:251`, `src/server/session.py:420` |
| 9 | WebSocket Protocol | Mining / Work Action (`WORK_ACTION`) | Clears adjacent obstacle (ROCHA, FLORESTA, BARRIL) for resources | `target_x: int`, `target_y: int`, `tipo: str` ("minerar", "reparar", etc.) | Terrain cleared to NORMAL, +1 madeira, +1 metal, AP deducted | `ACTION_REJECTED` if dist > 1, no work/excavation AP, or tile not mineable | `src/server/app.py:264`, `src/server/session.py:476` |
| 10 | WebSocket Protocol | End Round (`END_ROUND`) | Concludes player free actions, draws up to 4 cards, increments round | Empty payload `{}` | Hand refilled from deck/discard, AP reset, `fase = "SELECAO_CARTAS"` | `ACTION_REJECTED` if not in `ACAO_LIVRE` phase or unauthorized player | `src/server/app.py:277`, `src/server/session.py:511` |
| 11 | WebSocket Protocol | In-Game Chat (`CHAT_MESSAGE`) | Broadcasts player chat message to combat log | `text: str` | Log entry broadcast with player/hero name prefix in purple `#c084fc` | Ignored if string is empty or whitespace only | `src/server/app.py:288` |
| 12 | WebSocket Protocol | Anti-Cheat Hidden Hand Synchronization | Server filters card hands so each player only sees their own private cards | Outgoing `to_dict(for_player_id)` | `STATE_UPDATE` payload where `hand` is empty `[]` for opponents | None; hard server authority guarantee | `src/server/room_manager.py:80`, `src/server/session.py:575` |
| 13 | REST API | Server Health Check | Health endpoint reporting server status, active rooms, hero count | `GET /api/health` | `{"status": "ok", "active_rooms": int, "total_heroes": int}` | None | `src/server/app.py:125` |
| 14 | REST API | Heroes Catalog | REST endpoint providing all hero base stats, classes, sprites, and descriptions | `GET /api/heroes` | Array of hero objects (Aquele, Stark, Elden, Doom, Gruu, Kuro, Darwin) | None | `src/server/app.py:135` |
| 15 | REST API | Room Listing & Creation | REST endpoints for querying active lobbies and creating rooms | `GET /api/rooms`, `POST /api/rooms?room_id={str}` | Room list or newly created room metadata | None | `src/server/app.py:141`, `src/server/app.py:148` |
| 16 | Audio Assets | BGM & SFX Sound System | Complete collection of 11 OGG audio files for UI, combat, cutscenes, and levels | Audio file paths in `assets/sounds/` | Audio streams mapped to `AudioStreamPlayer` | Falls back gracefully or logs error if missing | `src/states/game_setup.py:34`, `assets/sounds/` |
| 17 | Visual Assets | Character Roster & Animation Sheets | High-res character portraits and 4x4 animated spritesheets (256x256 frames) | Files in `assets/images/characters/` | Texture2D / SpriteFrames for `Character.tscn` | Falls back to default portrait `Aquele.png` | `src/config.py:333`, `assets/images/` |
| 18 | Visual Assets | Isectum Swarm Spritesheet & Matrix | 26 sliced 32x32 transparent insect icons + 6x5 master spritesheet | Files in `assets/images/characters/monsters/isectum/` | 32x32 `Sprite2D` / `AnimatedSprite2D` textures | Fallback to larva or bug emoji | `tools/slice_sprites.py:33`, `src/castas_isectum.py` |
| 19 | Visual Assets | 2D Tactical Terrain Textures | 12 terrain textures (1024x1024) for 20x20 grid (Normal, Floresta, Parede, Rocha, etc.) | Files in `assets/images/environment/` | TileSet / TileMapLayer textures | Color fallback if texture missing | `src/config.py:388`, `web/coop/app.js:601` |
| 20 | Visual Assets | UI, Cards & Story Cutscenes | UI backdrops, world map, card frame, and 5-slide intro cutscene textures | Files in `assets/images/ui/`, `assets/images/environment/card/` | Control / TextureRect nodes | None | `src/cutscene.py:26`, `assets/images/ui/` |
| 21 | Godot 4 CLI | Headless Engine Runner | Godot 4 executable capability for headless execution and build verification | `godot --headless -s ...` | Process exit code (0 = success, >0 = failure) | Command not found inside sandboxed container | System probe, `ORIGINAL_REQUEST.md:57` |
| 22 | GUT Testing | Automated Headless Unit Testing | GUT test runner executing GDScript tests autonomously via CLI | `godot --headless -s addons/gut/gut_cmdln.gd -gexit` | Detailed test summary, assertion counts, exit code 0/1 | Exits with code > 0 if any assertion fails or error occurs | `addons/gut/`, `ORIGINAL_REQUEST.md:57` |

---

## Edge Cases

| # | Feature | Input | Observed Behavior |
|---|---------|-------|-------------------|
| 1 | Room Connection | 5th player connects to a room with 4 active players | Server responds with `{"type": "ERROR", "payload": {"mensagem": "A sala atingiu o limite de 4 jogadores."}}` and immediately closes the WebSocket. |
| 2 | Hero Selection | Player tries to choose a hero already taken by another player in the room | Server sends `ACTION_REJECTED` with reason `O herói {hero_name} já foi escolhido por {outro_jogador}`. The selecting player remains without a hero. |
| 3 | Hero Selection | Player sends invalid/unknown hero string (e.g. "Batman") | Server sends `ACTION_REJECTED` with reason `Classe de herói 'Batman' inválida.`. |
| 4 | Hero Selection | Player attempts to select/change hero after combat has already started (`fase != "LOBBY"`) | Server sends `ACTION_REJECTED` with reason `O jogo já começou. Não é possível trocar de herói.`. |
| 5 | Game Start | Player triggers `START_GAME` while some connected players have not chosen a hero | Server sends `ACTION_REJECTED` with reason `Nem todos os jogadores escolheram seus heróis.`. Game remains in `LOBBY`. |
| 6 | Movement Phase Check | Player sends `MOVE_HERO` during `SELECAO_CARTAS` or `LOBBY` | Server sends `ACTION_REJECTED` with reason `Movimento liberado apenas na fase de Ação Livre.`. |
| 7 | Movement Authority | Player sends `MOVE_HERO` with a spoofed or foreign `player_id` | Server rejects with `Jogador não autorizado.`. Only the owner of the hero can command movement. |
| 8 | Movement Boundary & Wall | Player sends `dest_x: -1` or coordinates on a `TERRENO_PAREDE` tile | Server rejects out-of-bounds coordinates or blocked wall tiles without deducting movement points. |
| 9 | Movement AP Shortage | Destination requires 4 steps via A* path, but hero only has 2 `pontos_movimento` | Server sends `ACTION_REJECTED` with reason `Pontos de movimento insuficientes (2 disponíveis, 4 necessários).`. Position unchanged. |
| 10 | Card Selection Secrecy | Player 2 inspects incoming `STATE_UPDATE` during `SELECAO_CARTAS` | Player 2 receives `hand: []` for Player 1, and only sees their own cards in `hand`. Player 1's `card_locked` boolean is visible. |
| 11 | Attack Range | Melee hero (range 2) attempts `ATTACK_TARGET` on an enemy 5 tiles away | Server rejects with `Alvo fora de alcance (distância 5 > alcance 2).`. Attack does not consume action. |
| 12 | Attack on Dead / Empty Tile | `ATTACK_TARGET` targeting coordinates where enemy is already dead or empty | Server rejects with `Não há nenhum invasor vivo no alvo indicado.`. |
| 13 | Cover Bonus vs AC | Target is behind obstacle/rock providing half cover | Server adds `obter_bonificacao_cobertura(tx, ty)` (+2 AC) to target base AC when calculating hit roll `(d20 + 4) >= (ac_base + 2)`. |
| 14 | Critical Hit (Natural 20) | Attack roll d20 produces 20 | Attack automatically hits regardless of target AC or cover bonuses. |
| 15 | Resource Mining Adjacency | Player double-clicks or triggers `WORK_ACTION` on a rock at distance 2 | Server rejects with `Você precisa estar adjacente ao recurso para interagir.` (Manhattan distance must be <= 1). |
| 16 | Resource Mining Depleted AP | Player tries `WORK_ACTION` with 0 `pontos_escavacao` and 0 `pontos_trabalho` | Server rejects with `Sem pontos de trabalho ou escavação disponíveis.`. |
| 17 | Deck Exhaustion & Reshuffle | Player completes turn via `END_ROUND`, but draw deck has fewer than required cards | Server draws remaining deck cards, moves all cards from `descarte` back to `deck`, shuffles them, and finishes drawing up to 4 cards. |
| 18 | Player Disconnection & Reconnection | Player disconnects during combat and reconnects with same `player_id` | Server marks `connected = False` upon disconnect, but preserves hero instance, HP, position, hand, and discard. Upon reconnect, marks `connected = True` and resyncs state. |
| 19 | Victory Condition | Last living enemy on the board drops to 0 HP | Enemy is removed from grid, +1 crystal awarded, phase switches to `VITORIA`, and victory message broadcast to combat log. |
| 20 | Headless CLI Execution | Godot binary executed without display server (`--headless`) | Engine boots with `DisplayServerHeadless`, avoids OpenGL/Vulkan window initialization, executes target script, and exits cleanly. |

---

## 1. WebSocket Co-op Protocol Technical Specification

### 1.1 Architecture & Topology
The multiplayer co-op architecture is **strictly authoritative**:
- **Host / Server**: FastAPI + WebSockets running on port `8000`.
- **Clients**: Godot 4 client (using native `WebSocketPeer`) and web client (`web/coop/app.js`).
- **State Model**: Server maintains the master `Tabuleiro` (20x20), hero instances, enemy AI, card decks, discard piles, action points, and game phase. Clients only send intents (`ClientMessage`) and render received state (`ServerMessage`).

### 1.2 REST Endpoints
| Method | Path | Query / Body | Description | Response Schema |
|--------|------|--------------|-------------|-----------------|
| `GET` | `/api/health` | None | Service liveness and room count | `{"status": "ok", "active_rooms": int, "total_heroes": int}` |
| `GET` | `/api/heroes` | None | Playable heroes roster | Array of `HERO_INFO` objects |
| `GET` | `/api/rooms` | None | Active rooms list | Array of `{"room_id": str, "players_count": int, "max_players": 4, "fase": str, "created_at": float}` |
| `POST` | `/api/rooms` | `room_id: Optional[str]` | Room creation | `{"room_id": str, "fase": str, "players_count": int, "created_at": float}` |

### 1.3 WebSocket Connection & Lifecycle
- **Endpoint**: `ws://<host>:<port>/ws/{room_id}/{player_id}?player_name={player_name}`
- **Lifecycle Phases**:
  1. `LOBBY`:
     - Players connect and are added to `session.jogadores`.
     - Max 4 players per room.
     - Each player selects a unique hero (`SELECT_HERO`).
     - Once all players have chosen heroes, any player can trigger `START_GAME`.
  2. `SELECAO_CARTAS` (Simultaneous Synchrony Round):
     - Each player receives a hand of 4 cards (drawn from personal deck).
     - Each player secretly selects 1 card (`SELECT_CARD`).
     - Opponents cannot see selected card details (anti-cheat).
     - Once all living players lock their cards, the server automatically calculates synergies and resolves the round.
  3. `ACAO_LIVRE` (Tactical Free Action):
     - Players gain movement, work, and excavation action points based on cards played + synergy bonuses.
     - Enemies advance 1 step towards the nearest hero or attack if adjacent.
     - Players can perform free actions in any order:
       * `MOVE_HERO` (pathfinding on grid)
       * `ATTACK_TARGET` (D&D 5e d20 attack against insects)
       * `WORK_ACTION` (mine rocks/forests for wood/metal)
       * `CHAT_MESSAGE` (tactical communication)
     - When finished, player invokes `END_ROUND` to draw cards, reset points, and start next round.
  4. `VITORIA` / `DERROTA`:
     - `VITORIA`: Triggered when all `session.inimigos` have `hp_atual <= 0`.
     - `DERROTA`: Triggered when all player heroes have `hp_atual <= 0`.

### 1.4 Message Schemas (JSON Typed)

#### Client -> Server (`ClientMessage`)
All client messages follow the envelope:
```json
{
  "type": "<MessageType>",
  "payload": { ... }
}
```

1. **`SELECT_HERO`**
   ```json
   {
     "type": "SELECT_HERO",
     "payload": { "hero_name": "Aquele" }
   }
   ```
2. **`START_GAME`**
   ```json
   {
     "type": "START_GAME",
     "payload": {}
   }
   ```
3. **`SELECT_CARD`**
   ```json
   {
     "type": "SELECT_CARD",
     "payload": { "card_idx": 0 }
   }
   ```
4. **`MOVE_HERO`**
   ```json
   {
     "type": "MOVE_HERO",
     "payload": { "dest_x": 10, "dest_y": 9 }
   }
   ```
5. **`ATTACK_TARGET`**
   ```json
   {
     "type": "ATTACK_TARGET",
     "payload": { "target_x": 12, "target_y": 9, "habilidade": null }
   }
   ```
6. **`WORK_ACTION`**
   ```json
   {
     "type": "WORK_ACTION",
     "payload": { "target_x": 10, "target_y": 8, "tipo": "minerar" }
   }
   ```
7. **`END_ROUND`**
   ```json
   {
     "type": "END_ROUND",
     "payload": {}
   }
   ```
8. **`CHAT_MESSAGE`**
   ```json
   {
     "type": "CHAT_MESSAGE",
     "payload": { "text": "Protejam o flanco direito!" }
   }
   ```

#### Server -> Client (`ServerMessage`)

1. **`STATE_UPDATE`** (Broadcast after every state mutation, tailored per player for private hand):
   ```json
   {
     "type": "STATE_UPDATE",
     "payload": {
       "room_id": "SALA99",
       "fase": "ACAO_LIVRE",
       "round": 1,
       "sinergia_ativa": {
         "tipo": "equipe",
         "categoria": "movimento",
         "mensagem": "⚡ SINCRONIA DE EQUIPE: 2x MOVIMENTO combinados!"
       },
       "recursos": {
         "madeira": 0,
         "couro": 0,
         "metal": 0,
         "cristal": 0
       },
       "heroes": [
         {
           "player_id": "p1",
           "player_name": "Alice",
           "hero_name": "Aquele",
           "sprite_url": "/assets/images/characters/heroes/Aquele.png",
           "hp_atual": 48,
           "hp_max": 48,
           "ac": 17,
           "pos_x": 9,
           "pos_y": 10,
           "pontos_movimento": 4,
           "pontos_trabalho": 0,
           "pontos_escavacao": 0,
           "cards_count": 3,
           "hand": [
             {
               "id": "investida_rapida",
               "nome": "Investida Rápida",
               "movimento": 15,
               "trabalho": 0,
               "escavacao": 0,
               "descricao": "Garante alta mobilidade para reposicionamento tático."
             }
           ],
           "is_me": true,
           "card_locked": true,
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
       "grid_terreno": [ ["NORMAL", ...], ... ],
       "combat_log": [
         {
           "autor": "ROUND",
           "texto": "⚡ Round 1 resolvido! Ações livres liberadas para a equipe.",
           "cor": "#10b981"
         }
       ]
     }
   }
   ```
2. **`ACTION_REJECTED`**
   ```json
   {
     "type": "ACTION_REJECTED",
     "payload": {
       "acao": "MOVE_HERO",
       "motivo": "Pontos de movimento insuficientes (0 disponíveis, 2 necessários)."
     }
   }
   ```
3. **`ERROR`**
   ```json
   {
     "type": "ERROR",
     "payload": {
       "mensagem": "A sala atingiu o limite de 4 jogadores."
     }
   }
   ```

---

## 2. Audio & Visual Assets Catalog

### 2.1 Audio Assets Inventory (`assets/sounds/`)
All audio files are encoded in standard OGG Vorbis format:

| File Name | Size (Bytes) | Category | Intended Godot Node | In-Game Trigger / Event |
|-----------|--------------|----------|---------------------|-------------------------|
| `menu.ogg` | 502,096 | Music (BGM) | `AudioStreamPlayer` (Bus: Music, Loop) | Main Menu, Lobby, Hero Selection screen |
| `battle1.ogg` | 505,660 | Music (BGM) | `AudioStreamPlayer` (Bus: Music, Loop) | Tactical Combat, Siege mode, Boss encounters |
| `intro.ogg` | 185,098 | Music (BGM) | `AudioStreamPlayer` (Bus: Music) | Story prologue / cinematic cutscene |
| `attack.ogg` | 33,218 | SFX | `AudioStreamPlayer2D` (Bus: SFX) | Attack executed against enemy or obstacle |
| `hit.ogg` | 44,608 | SFX | `AudioStreamPlayer2D` (Bus: SFX) | Enemy receives damage from attack |
| `damage.ogg` | 44,608 | SFX | `AudioStreamPlayer2D` (Bus: SFX) | Hero receives damage from enemy attack |
| `critical_hit.ogg` | 111,960 | SFX | `AudioStreamPlayer2D` (Bus: SFX) | Natural 20 critical attack |
| `miss.ogg` | 30,099 | SFX | `AudioStreamPlayer` (Bus: SFX) | Attack misses AC or `ACTION_REJECTED` received |
| `heal.ogg` | 90,159 | SFX | `AudioStreamPlayer2D` (Bus: SFX) | Healing spell or potion applied |
| `level_up.ogg` | 25,992 | SFX | `AudioStreamPlayer` (Bus: SFX) | Wave victory, card upgrade, synergy supreme |
| `button_click.ogg` | 10,381 | SFX | `AudioStreamPlayer` (Bus: UI) | UI button pressed, card selected, tab clicked |

### 2.2 Visual Assets Catalog (`assets/images/`)

#### A. Hero Portraits & Classes (`assets/images/characters/heroes/`)
| File Name | Resolution | Format | Role / Class Mapping |
|-----------|------------|--------|----------------------|
| `Aquele.png` | 162x169 | RGBA PNG | Protagonist Warrior (Aquele) portrait |
| `Koema.png` | 658x379 | RGBA PNG | Protagonist Mage (Koema) portrait |
| `Novak.png` | 548x455 | RGBA PNG | Protagonist Fighter (Novak) portrait |
| `Rilem.png` | 441x565 | RGBA PNG | Protagonist Ranger (Rilem) portrait |
| `Yukito.png` | 544x459 | RGBA PNG | Protagonist Paladin (Yukito) portrait |
| `guerreiro.png` | 676x369 | RGBA PNG | Generic Warrior class portrait |
| `paladino.png` | 676x369 | RGBA PNG | Stark / Paladin class portrait |
| `mago.png` | 676x369 | RGBA PNG | Elden / Mage class portrait |
| `ladino.png` | 676x369 | RGBA PNG | Doom & Kuro / Rogue class portrait |
| `barbaro.png` | 676x369 | RGBA PNG | Gruu / Barbarian class portrait |
| `druida.png` | 676x369 | RGBA PNG | Darwin / Druid class portrait |
| `arqueiro.png` | 676x369 | RGBA PNG | Generic Archer class portrait |
| `clerigo.png` | 676x369 | RGBA PNG | Cleric class portrait |
| `bruxo.png` | 500x500 | RGBA PNG | Warlock class portrait |

#### B. Animated Characters & Spritesheets (`assets/images/characters/animation/processed/` & `silver_roses/`)
| File Name | Resolution | Layout | Frame Size | Notes |
|-----------|------------|--------|------------|-------|
| `aquele.png` | 1024x1024 | 4x4 Grid | 256x256 | Defringed alpha sprite frames for Aquele |
| `darwin.png` | 1024x1024 | 4x4 Grid | 256x256 | Defringed alpha sprite frames for Darwin |
| `gruu.png` | 1024x1024 | 4x4 Grid | 256x256 | Defringed alpha sprite frames for Gruu |
| `doom.png` | 768x1024 | 3x4 Grid | 256x256 | Defringed alpha sprite frames for Doom |
| `elden.png` | 768x1024 | 3x4 Grid | 256x256 | Defringed alpha sprite frames for Elden |
| `kuro.png` | 768x1024 | 3x4 Grid | 256x256 | Defringed alpha sprite frames for Kuro |
| `stark.png` | 768x1024 | 3x4 Grid | 256x256 | Defringed alpha sprite frames for Stark |
| `sword_isnet_clean.png` | 915 KB | 3x4 Grid | Silver Roses Guerreiro |
| `archer_sem_halo.png` | 1,027 KB | 3x4 Grid | Silver Roses Arqueiro |
| `mine_sem_halo.png` | 871 KB | 3x4 Grid | Silver Roses Minerador |

#### C. Bosses & Monsters (`assets/images/characters/bosses/` & `monsters/`)
| File Name | Category | Resolution | Notes |
|-----------|----------|------------|-------|
| `Sienna.png` | Boss | 175 KB PNG | High-mobility Boss Sienna / Sienna Phoenix |
| `chefe.png` | Boss | 535 KB PNG | Dungeon Boss / Chefe |
| `dragao_anciao.png` | Monster | 378 KB PNG | Ancient Dragon (DragaoAnciao, HP 400, AC 22) |
| `lorde_lich.png` | Monster | 185 KB PNG | Lord Lich (LordeLich, HP 280, AC 17) |
| `rei_goblin.png` | Monster | 169 KB PNG | Goblin King (ReiGoblin, HP 250, AC 18) |
| `goblin.png` | Monster | 91 KB PNG | Goblin (HP 7, AC 15) |
| `kobold.png` | Monster | 73 KB PNG | Kobold (HP 5, AC 12) |
| `esqueleto.png` | Monster | 174 KB PNG | Skeleton (HP 13, AC 13) |

#### D. Isectum Swarm Catalog (`assets/images/characters/monsters/isectum/`)
All 26 castas are individual 32x32 transparent PNGs, sliced directly from `isectum_spritesheet.png` (1024x1024, 6 columns x 5 rows):
1. `vespa_cacadora.png` (0,0) — Vespa Caçadora
2. `abelha_tecela.png` (1,0) — Abelha Tecelã
3. `formiga_correicao.png` (2,0) — Formiga Correição
4. `libelula_blindada.png` (3,0) — Libélula Blindada
5. `louva_deus.png` (4,0) — Louva-a-Deus
6. `viuva_canibal.png` (5,0) — Viúva Canibal
7. `besouro_rinoceronte.png` (0,1) — Besouro Rinoceronte
8. `vagalume_sombras.png` (1,1) — Vagalume das Sombras
9. `aranha_clepto.png` (2,1) — Aranha Cleptomaníaca
10. `mariposa_esfinge.png` (3,1) — Mariposa Esfinge
11. `besouro_unicornio.png` (4,1) — Besouro Unicórnio
12. `infiltrador.png` (5,1) — Infiltrador Isectum
13. `centopeia_olhos.png` (0,2) — Centopeia de Olhos
14. `besouro_gorgulho.png` (1,2) — Besouro Gorgulho (Trabalhador)
15. `efemera_mimetica.png` (2,2) — Efêmera Mimética
16. `cigarra_ressonante.png` (3,2) — Cigarra Ressonante
17. `larva_carniceira.png` (4,2) — Larva Carniceira
18. `viuva_negra.png` (5,2) — Viúva Negra
19. `mosca_tse_tse.png` (0,3) — Mosca Tsé-Tsé
20. `gafanhoto_praga.png` (2,3) — Gafanhoto da Praga
21. `escaravelho_necrofago.png` (3,3) — Escaravelho Necrófago
22. `vespa_joia.png` (4,3) — Vespa Joia
23. `enxame_rainha.png` (5,3) — Rainha do Enxame
24. `carrapato_vampiro.png` (3,4) — Carrapato Vampiro
25. `brutamonte.png` (4,4) — Brutamonte Isectum

#### E. Environment & Terrain Tiles (`assets/images/environment/`)
Each terrain tile is a 1024x1024 texture mapped directly to the tactical grid:
- `terreno_normal.png` (`TERRENO_NORMAL`): Base stone dungeon floor.
- `terreno_floresta.png` (`TERRENO_FLORESTA`): Dense forest / natural terrain.
- `terreno_dificil.png` (`TERRENO_DIFICIL`): Difficult mud / gravel ground (2x movement cost).
- `terreno_parede.png` (`TERRENO_PAREDE`): Impassable solid stone wall.
- `terreno_fogo.png` (`TERRENO_FOGO`): Fire hazard terrain.
- `terreno_rocha.png` (`TERRENO_ROCHA`): Mineable rock obstacle (+1 metal on excavation).
- `terreno_barril.png` (`TERRENO_BARRIL`): Destructible wood barrel (+1 madeira).
- `terreno_campo.png` (`TERRENO_CAMPO`): Open exterior field.
- `terreno_exterior.png` (`TERRENO_EXTERIOR`): Outdoor fortress boundary.
- `terreno_corredor.png` (`TERRENO_CORREDOR`): Narrow corridor floor.
- `terreno_muralha_lo.png` (`TERRENO_MURALHA_LO`): Fortress rampart wall.
- `terreno_subsolo.png` (`TERRENO_SUBSOLO`): Dark subterranean cavern floor.

#### F. UI, Cards & Story Cutscenes
- `pixelCardAssest.png` (`assets/images/environment/card/`): 720x299 pixel-art card template for `Card.tscn`.
- `menu_background.png` (`assets/images/ui/`): 1024x1024 main menu background illustration.
- `mapa_mundo.png` (`assets/images/ui/`): 1024x1024 world campaign selection map.
- `logo.png` & `logo_backup.png` (`assets/images/ui/`): RPG-battle main logo.
- Cutscene story slides (`assets/images/ui/`):
  * `intro_world.png`: World lore slide 1.
  * `intro_destruction.png`: Desolation / fall of the empire slide 2.
  * `intro_villains.png`: Gathering of the insect swarm slide 3.
  * `intro_gathering.png`: Meeting of the champions slide 4.
  * `intro_heroes.png`: Final hero vanguard slide 5.

---

## 3. Godot 4 Installation & System Investigation

### 3.1 Probing Results
- Direct CLI command `godot --version` exited with `bash: godot: command not found`.
- Neither `godot`, `godot4`, nor `godot-engine` are in PATH inside the current sandboxed container.
- Probing the user configuration on host revealed:
  * `~/.config/godot/editor_settings-4.7.tres` exists and was modified on 2026-09-25.
  * `~/.cache/godot` contains thumbnail caches for Godot 4 projects.
  * Recent project was active at `/home/anderson/Documents/projeto/Slender - Schorodinger/godot_slender/`.
  * Flatpak applications installed: OBS, RustDesk, Steam, Obsidian, ProtonUp-Qt (no standalone Godot flatpak).
- Container sandbox boundary:
  * Mounts are restricted (`/bin`, `/usr`, `/lib`, `/home/anderson/Documents/projeto/RPG-battle`, `.cache`, `.cargo`, `.config`, `.npm`, `.rustup`).
  * Outbound internet access is disabled (DNS resolution for external domains fails).

### 3.2 Requirements for Godot 4 Execution & Porting
1. **Engine Version**: Godot 4.3 or 4.2 stable (Linux x86_64).
2. **Binary Availability**: To execute headless testing via CLI, the `godot` binary should either:
   - Be linked into `/usr/local/bin/godot` or `~/.local/bin/godot` in PATH; or
   - Be placed locally in the project repository under `tools/godot` or `bin/godot` with execution permissions (`chmod +x`).
3. **Project File Architecture (`godot_project/project.godot`)**:
   - `config_version=5`
   - `display/window/size/viewport_width=1280`
   - `display/window/size/viewport_height=720`
   - `display/window/stretch/mode="canvas_items"`
   - `display/window/stretch/aspect="keep"`
   - `rendering/renderer/rendering_method="gl_compatibility"`
   - Autoload singletons:
     * `GameManager="*res://src/core/GameManager.gd"`
     * `EventBus="*res://src/core/EventBus.gd"`
     * `DataManager="*res://src/core/DataManager.gd"`
   - Editor plugins:
     * `enabled=PackedStringArray("res://addons/gut/plugin.cfg")`

---

## 4. GUT Test Framework & Headless CLI Architecture

### 4.1 GUT Directory Setup
```
godot_project/
├── addons/
│   └── gut/                    # GUT 4.x addon files
│       ├── gut.gd              # Core GUT engine
│       ├── test.gd             # Base GutTest class
│       ├── gut_cmdln.gd        # Headless command-line runner
│       ├── plugin.cfg          # Godot plugin definition
│       └── ...
├── test/
│   ├── unit/                   # Unit test scripts
│   │   ├── test_tabuleiro.gd   # A*, grid limits, terrain cost tests
│   │   ├── test_combate.gd     # D&D 5e d20, AC, advantage, criticals
│   │   ├── test_cerco.gd       # Cards, synergy, excavation economy
│   │   └── test_protocol.gd    # JSON serialization / deserialization
│   └── integration/
└── .gutconfig.json             # Root GUT configuration file
```

### 4.2 `.gutconfig.json` Specification
```json
{
  "dirs": [
    "res://test/unit/"
  ],
  "include_subdirs": true,
  "prefix": "test_",
  "suffix": ".gd",
  "log_level": 1,
  "exit_on_finish": true,
  "should_exit": true
}
```

### 4.3 Headless CLI Invocation
To execute the canonical automated test suite headlessly via CLI:
```bash
godot --headless -s addons/gut/gut_cmdln.gd -gdir=res://test/unit -ginclude_subdirs -gprefix=test_ -gsuffix=.gd -gexit
```
- `--headless`: Disables display server, windowing, and audio output.
- `-s addons/gut/gut_cmdln.gd`: Runs the GUT command-line scene script.
- `-gdir=res://test/unit`: Points to the test suite directory.
- `-gexit`: Forces Godot to terminate with exit code 0 if all tests pass, or exit code > 0 if any assertion fails.

### 4.4 Canonical GDScript Unit Test Template (`GutTest`)
Following the strict Arrange-Act-Assert (AAA) pattern mandated by project standards:

```gdscript
# test/unit/test_combate.gd
extends GutTest

var rules_engine = null

func before_each():
    # Arrange shared fixtures
    rules_engine = CombatRules.new()

func after_each():
    rules_engine = null

func test_ataque_acerto_critico_natural_20():
    # Arrange
    var atacante_mod = 2
    var alvo_ac = 25  # AC inalcançável normalmente
    var roll_d20 = 20

    # Act
    var resultado = rules_engine.resolver_ataque(roll_d20, atacante_mod, alvo_ac)

    # Assert
    assert_true(resultado.acertou, "Natural 20 deve sempre acertar independente da AC")
    assert_true(resultado.is_critico, "Natural 20 deve ser registrado como crítico")

func test_meia_cobertura_concede_mais_dois_ac():
    # Arrange
    var base_ac = 14
    var tem_meia_cobertura = true

    # Act
    var ac_efetiva = rules_engine.calcular_ac_efetiva(base_ac, tem_meia_cobertura)

    # Assert
    assert_eq(ac_efetiva, 16, "Meia cobertura deve conceder exatamente +2 de AC")
```

---

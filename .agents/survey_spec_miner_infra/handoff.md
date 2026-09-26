# Handoff Report — Infrastructure, WebSocket Protocol & Assets Survey

**Agent**: `survey_spec_miner_infra`  
**Date**: 2026-09-26  
**Type**: Hard Handoff  
**Workspace Path**: `/home/anderson/Documents/projeto/RPG-battle/.agents/survey_spec_miner_infra/`  
**Recipient**: Orchestrator (`parent`)

---

## 1. Observation

1. **WebSocket Protocol & Server Files**:
   - `src/server/protocol.py` lines 14-35 defines `MessageType` enum with 9 client-to-server types (`JOIN_ROOM`, `SELECT_HERO`, `START_GAME`, `SELECT_CARD`, `MOVE_HERO`, `ATTACK_TARGET`, `WORK_ACTION`, `END_ROUND`, `CHAT_MESSAGE`) and 8 server-to-client types (`ROOM_STATE`, `GAME_STARTED`, `CARD_LOCKED`, `ROUND_RESOLVED`, `STATE_UPDATE`, `COMBAT_LOG`, `ACTION_REJECTED`, `ERROR`).
   - `src/server/app.py` lines 162-306 defines `@app.websocket("/ws/{room_id}/{player_id}")` with query parameter `player_name`, handling message loop, rejecting unknown heroes or out-of-turn actions via `ACTION_REJECTED`.
   - `src/server/room_manager.py` lines 24-101 defines `Room` with max 4 players (`add_player`), individual `send_personal`, `broadcast`, and `broadcast_state()` sending `STATE_UPDATE`.
   - `src/server/session.py` lines 575-581 enforces anti-cheat privacy:
     `"hand": p.get("mao", []) if is_me else []`
     Opponents only see `cards_count` and `card_locked: bool`.
   - `tests/test_coop_server.py` lines 22-432 defines 15 unit and integration tests verifying room lifecycle, hero selection rejection, boundary checks, and simultaneous synchrony round resolution.

2. **Asset Directory Inventory**:
   - `assets/sounds/` contains 11 OGG files: 3 BGM tracks (`menu.ogg` [502 KB], `battle1.ogg` [505 KB], `intro.ogg` [185 KB]) and 8 SFX tracks (`attack.ogg` [33 KB], `hit.ogg` [44 KB], `damage.ogg` [44 KB], `critical_hit.ogg` [111 KB], `miss.ogg` [30 KB], `heal.ogg` [90 KB], `level_up.ogg` [25 KB], `button_click.ogg` [10 KB]).
   - `assets/images/characters/heroes/` contains 14 PNG portraits: 5 specific heroes (`Aquele.png` [162x169], `Koema.png` [658x379], `Novak.png` [548x455], `Rilem.png` [441x565], `Yukito.png` [544x459]) and 9 class portraits (676x369 / 500x500).
   - `assets/images/characters/animation/processed/` contains 7 processed spritesheets (`aquele.png`, `darwin.png`, `gruu.png` [1024x1024]; `doom.png`, `elden.png`, `kuro.png`, `stark.png` [768x1024]) configured with 256x256 frames per `src/config.py:333`.
   - `assets/images/characters/monsters/isectum/` contains 26 sliced 32x32 transparent PNGs corresponding to the 24+ Isectum castes in `src/castas_isectum.py`.
   - `assets/images/environment/` contains 12 terrain textures (1024x1024) corresponding to `TERRENO_*` constants.
   - `assets/images/environment/card/` contains `pixelCardAssest.png` (720x299).
   - `assets/images/ui/` contains 9 files including `menu_background.png` (1024x1024), `mapa_mundo.png` (1024x1024), `logo.png`, and 5 story cutscene slides (`intro_*.png`).

3. **System Environment & Godot CLI Probe**:
   - Command `godot --version` exited with code 127: `bash: godot: command not found`.
   - Probing the host files in `~/.config/godot` revealed `editor_settings-4.7.tres` (modified Sep 25, 2026) and recent directory `/home/anderson/Documents/projeto/Slender - Schorodinger/godot_slender/`.
   - The sandboxed container environment has isolated mounts (`/bin`, `/usr`, `/lib`, `/home/anderson/Documents/projeto/RPG-battle`, `.cache`, `.cargo`, `.config`, `.npm`, `.rustup`) and DNS resolution fails for external network queries (`curl: (6) Could not resolve host: github.com`).
   - `godot_project/` directory does not yet exist.

---

## 2. Logic Chain

1. From Observation 1, the WebSocket Co-op protocol relies on an authoritative server with strict message typing and hidden information protection. The Godot 4 client must implement native `WebSocketPeer` polling in its game loop, connecting to `/ws/{room_id}/{player_id}?player_name={name}`, sending typed payloads (`SELECT_HERO`, `SELECT_CARD`, `MOVE_HERO`, `ATTACK_TARGET`, `WORK_ACTION`, `END_ROUND`, `CHAT_MESSAGE`), and parsing incoming `STATE_UPDATE` to drive the 20x20 grid UI, action points, and team roster.
2. From Observation 2, all necessary visual and audio assets already exist in `assets/` in production-ready formats (PNG for textures/sprites, OGG Vorbis for music and SFX). No placeholder assets need to be synthesized. For Godot 4:
   - Terrains map to `TileSet` / `TileMapLayer` from `assets/images/environment/`.
   - Hero animations map to `SpriteFrames` from `assets/images/characters/animation/processed/` with 256x256 frame slicing.
   - Insects map to `Sprite2D` / `AnimatedSprite2D` using the 32x32 PNGs in `assets/images/characters/monsters/isectum/`.
   - Sounds map to `AudioStreamPlayer` (BGM / UI) and `AudioStreamPlayer2D` (spatial combat SFX).
3. From Observation 3, the host system has Godot 4.x configured, but the sandboxed CLI environment lacks the `godot` binary in PATH and cannot download packages over the internet. Therefore, to ensure automated GUT test execution via CLI (`godot --headless -s addons/gut/gut_cmdln.gd -gexit`), the project must structure `godot_project/` with standard Godot 4 project files and `.gutconfig.json`, and the orchestrator / user should mount or symlink the host Godot 4 binary into PATH (or provide a local standalone binary under `tools/godot`).

---

## 3. Caveats

- **Network Sandbox**: Outbound internet is disabled in this subagent environment, preventing `curl`/`wget` download of the GUT zip or Godot engine from GitHub. GUT addons must be placed locally in `godot_project/addons/gut/` from local files or generated GDScript scripts.
- **Pygame in Python Environment**: The global Python in this container lacks `pygame` and `starlette`, which prevents running Python Pygame tests without the specific venv. However, the server architecture and protocol are fully documented and analyzed via source inspection and Starlette test definitions.

---

## 4. Conclusion

All technical specifications for Infrastructure, WebSocket Co-op Protocol, Asset Inventory, and GUT Headless Testing have been comprehensively extracted and documented:
1. Complete schema, lifecycle, and anti-cheat specifications for the WebSocket Co-op client are ready for implementation in GDScript.
2. An exhaustive asset catalog linking 100% of images (portraits, animations, 26 Isectum sprites, 12 terrains, UI slides) and sounds (3 music, 8 SFX) to Godot 4 node equivalents is compiled.
3. System status for Godot 4 and headless test requirements via GUT CLI runner are documented with explicit `.gutconfig.json` and `project.godot` templates.
4. Comprehensive findings have been committed to `/home/anderson/Documents/projeto/RPG-battle/.agents/survey_spec_miner_infra/analysis.md`.

---

## 5. Verification Method

To independently verify the findings in this report:

1. **Inspect Detailed Analysis**:
   ```bash
   cat /home/anderson/Documents/projeto/RPG-battle/.agents/survey_spec_miner_infra/analysis.md
   ```
2. **Verify Server Protocol Definition**:
   ```bash
   python3 -c "from src.server.protocol import MessageType; print([m.value for m in MessageType])"
   ```
3. **Verify Asset Inventory Existence**:
   ```bash
   ls -la assets/sounds/*.ogg
   ls -la assets/images/characters/monsters/isectum/*.png | wc -l # Expect 26
   ls -la assets/images/characters/animation/processed/*.png | wc -l # Expect 7
   ```
4. **Verify Godot CLI Status**:
   ```bash
   which godot || echo "Godot binary not in container PATH"
   ```

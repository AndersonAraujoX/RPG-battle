# Task Assignment: Infra, Protocol & Assets Survey

## Objective
Extract technical specifications for the WebSocket Co-op protocol, asset inventory (audio/images), Godot 4 project architecture, and GUT test runner requirements.

## Working Directory
`/home/anderson/Documents/projeto/RPG-battle/.agents/survey_spec_miner_infra`

## Authoritative Inputs
- `/home/anderson/Documents/projeto/RPG-battle/.agents/ORIGINAL_REQUEST.md` (MUST READ FIRST)
- `/home/anderson/Documents/projeto/RPG-battle/src/server/protocol.py`
- `/home/anderson/Documents/projeto/RPG-battle/src/server/room_manager.py`
- `/home/anderson/Documents/projeto/RPG-battle/assets/` (`assets/images/`, `assets/sounds/`)
- Existing `godot_project/` directory (if present)

## Scope & Investigation Questions
1. **WebSocket Co-op Protocol**:
   - URL endpoint format: `/ws/{room_id}/{player_id}`.
   - Message schema/types: `SELECT_HERO`, `SELECT_CARD`, `MOVE_HERO`, `ATTACK_TARGET`, `WORK_ACTION`, `STATE_UPDATE`, and any other message types.
   - Payload fields, types, serialization and deserialization expectations, state sync lifecycle.
2. **Audio & Visual Assets Catalog**:
   - Inventory of all sound effects (`assets/sounds/`) and visual assets (`assets/images/`).
   - Format, naming conventions, and intended mappings to Godot `AudioStreamPlayer`, `Texture2D`, `AnimatedSprite2D`, UI themes.
3. **Godot 4 Architecture & GUT Setup**:
   - Project requirements: Godot 4, Compatibility renderer, 1280x720, Autoloads (`GameManager.gd`, `EventBus.gd`, `DataManager.gd`).
   - Check if `godot` binary is installed on system (`godot --version`).
   - GUT test framework setup: check `godot_project/addons/gut` presence, GUT command line runner (`godot --headless -s addons/gut/gut_cmdln.gd -gexit`), headless test execution requirements.

## Deliverables
- Write comprehensive spec analysis report to `/home/anderson/Documents/projeto/RPG-battle/.agents/survey_spec_miner_infra/analysis.md`.
- Write handoff to `/home/anderson/Documents/projeto/RPG-battle/.agents/survey_spec_miner_infra/handoff.md`.
- Send completion message to orchestrator with summary and paths.

## 2026-09-26T12:30:23Z
You are survey_spec_miner_infra.
Your working directory is /home/anderson/Documents/projeto/RPG-battle/.agents/survey_spec_miner_infra/
You MUST read /home/anderson/Documents/projeto/RPG-battle/.agents/ORIGINAL_REQUEST.md first.
Then read /home/anderson/Documents/projeto/RPG-battle/.agents/survey_spec_miner_infra/DISPATCH.md for your detailed task assignment.

Your mission is to extract technical specifications for the WebSocket Co-op protocol (src/server/protocol.py, room_manager.py, message types, schemas, lifecycle), catalog audio/visual assets in assets/ (images, sounds), investigate Godot 4 installation and requirements on the system (godot CLI), and establish requirements for the GUT test framework setup in godot_project/addons/gut and headless testing via CLI.
Write your complete technical findings to /home/anderson/Documents/projeto/RPG-battle/.agents/survey_spec_miner_infra/analysis.md and your handoff report to /home/anderson/Documents/projeto/RPG-battle/.agents/survey_spec_miner_infra/handoff.md.
When finished, send a message to orchestrator with a concise summary and report paths.

# Task Assignment: m6_spec_miner_1

## Objective
Extract the complete, authoritative specification for the WebSocket Multiplayer protocol from `src/server/protocol.py` and `src/server/room_manager.py` to enable the Godot 4 GDScript implementation in `godot_project/scripts/network/WebSocketClient.gd`.

## Inputs & Context Files
- /home/anderson/Documents/projeto/RPG-battle/.agents/ORIGINAL_REQUEST.md (MANDATORY: read first)
- /home/anderson/Documents/projeto/RPG-battle/PROJECT.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/skills/organizacao_refatoracao/SKILL.md
- /home/anderson/Documents/projeto/RPG-battle/src/server/protocol.py
- /home/anderson/Documents/projeto/RPG-battle/src/server/room_manager.py

## Detailed Scope
1. Document the exact connection handshake: endpoint path `/ws/{room_id}/{player_id}?player_name={name}`, query parameters, initial messages.
2. List all Client -> Server message types (`SELECT_HERO`, `SELECT_CARD`, `MOVE_HERO`, `ATTACK_TARGET`, `WORK_ACTION`, `CHAT`, `PING`, etc.) with their exact payload fields, types, and validation rules.
3. List all Server -> Client message types (`STATE_UPDATE`, `CHAT`, `PONG`, `ERROR`, `PLAYER_JOINED`, `PLAYER_LEFT`, `TURN_CHANGE`, etc.) with their exact payload fields, structures, and expected client reactions.
4. Document heartbeat / keepalive mechanisms (PING/PONG intervals, timeout rules).
5. Document error codes, disconnect reasons, and expected reconnection behavior.

## Output Requirements
- Write your comprehensive specification report to:
  `/home/anderson/Documents/projeto/RPG-battle/.agents/m6_spec_miner_1/spec_report.md`
- Write your completion handoff to:
  `/home/anderson/Documents/projeto/RPG-battle/.agents/m6_spec_miner_1/handoff.md`
- Update `progress.md` with timestamps during your work.
- Send a completion message via `send_message` back to orchestrator (`parent`).

## 2026-10-01T05:42:42Z
You are m6_spec_miner_1. Your working directory is /home/anderson/Documents/projeto/RPG-battle/.agents/m6_spec_miner_1.

Read your task instructions at:
/home/anderson/Documents/projeto/RPG-battle/.agents/m6_spec_miner_1/DISPATCH.md

Also read:
- /home/anderson/Documents/projeto/RPG-battle/.agents/ORIGINAL_REQUEST.md (MANDATORY: read first)
- /home/anderson/Documents/projeto/RPG-battle/PROJECT.md
- /home/anderson/Documents/projeto/RPG-battle/src/server/protocol.py
- /home/anderson/Documents/projeto/RPG-battle/src/server/room_manager.py

Extract the full protocol specification (all message types, schemas, connection endpoints, serialization rules) and write:
1. /home/anderson/Documents/projeto/RPG-battle/.agents/m6_spec_miner_1/spec_report.md
2. /home/anderson/Documents/projeto/RPG-battle/.agents/m6_spec_miner_1/handoff.md

Update progress.md as you work. When finished, send a message to parent (5dbb519a-f6c3-4b1f-b7e0-6ec494d60de9) with your summary and handoff path.

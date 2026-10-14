# Task Assignment: m6_worker_1

## Objective
Implement `godot_project/scripts/network/WebSocketClient.gd` and its comprehensive GUT test suite in `godot_project/test/unit/test_websocket_client.gd`.

## Exclusive Write Ownership
You own and may ONLY create/modify:
- `godot_project/scripts/network/WebSocketClient.gd`
- `godot_project/test/unit/test_websocket_client.gd`
Do NOT modify files owned by other modules.

## Inputs & Context Files (MANDATORY: read first)
- /home/anderson/Documents/projeto/RPG-battle/.agents/ORIGINAL_REQUEST.md
- /home/anderson/Documents/projeto/RPG-battle/PROJECT.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/skills/organizacao_refatoracao/SKILL.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/m6_spec_miner_1/spec_report.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/m6_explorer_1/architecture_report.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/m6_explorer_2/test_strategy_report.md
- /home/anderson/Documents/projeto/RPG-battle/godot_project/scripts/autoloads/EventBus.gd
- /home/anderson/Documents/projeto/RPG-battle/godot_project/scripts/autoloads/GameManager.gd

## Implementation Requirements
1. `WebSocketClient.gd`:
   - `class_name WebSocketClient extends Node`
   - Native Godot 4 `WebSocketPeer` support with dependency injection seam (`set_peer(peer)` / `get_peer()`) allowing `MockWebSocketPeer` in unit tests.
   - Connect to `/ws/{room_id}/{player_id}?player_name={name}` with URL encoding and query parameters.
   - Connection lifecycle FSM: `DISCONNECTED`, `CONNECTING`, `CONNECTED`, `CLOSING`, `RECONNECTING`.
   - Polling via `_process(delta)` and public `poll(delta: float = 0.0)`.
   - Typed client methods for sending all protocol messages:
     * `send_select_hero(hero_name: String) -> Error`
     * `send_start_game() -> Error`
     * `send_select_card(card_idx: int) -> Error`
     * `send_move_hero(dest_x: int, dest_y: int) -> Error`
     * `send_attack_target(target_x: int, target_y: int, habilidade: String = "") -> Error`
     * `send_work_action(target_x: int, target_y: int, tipo: String = "minerar") -> Error`
     * `send_end_round() -> Error`
     * `send_chat(mensagem: String) -> Error`
     * `send_ping() -> Error`
   - Input validation before sending (bounds checking `[0, 19]`, non-empty strings, connection state check).
   - Typed incoming packet parsing:
     * Dispatches to `EventBus.network_message_received` and `EventBus.network_connection_status_changed`.
     * Signals: `connected_to_server(room_id, player_id)`, `connection_closed(code, reason)`, `connection_error(code, reason)`, `message_received(type, payload)`, `state_update_received(data)`, `action_rejected(reason)`, `chat_received(sender, text)`.
   - Exponential backoff auto-reconnection on unexpected disconnects (`code != 1000`).

2. `test_websocket_client.gd`:
   - Extends `GutTest`.
   - Uses `autofree()` on created nodes to guarantee 0 ObjectDB leaks upon test suite exit.
   - Implements `MockWebSocketPeer extends RefCounted` that mimics Godot 4 `WebSocketPeer` states and packet queues.
   - Follows strict Arrange-Act-Assert (AAA) structure.
   - Implements tests covering:
     * Happy path connection, packet sending, packet receiving, signal propagation.
     * Edge cases: malformed JSON, unknown message types, missing payload fields, negative/out-of-bounds coordinates, empty strings.
     * Error handling: unexpected disconnects, close codes, reconnection triggers.
     * Anti-cheat hand privacy verification in mock `STATE_UPDATE`.
     * Clean shutdown and 0 memory leaks.

3. Testing & Verification:
   - Run the GUT tests:
     `/home/anderson/Documents/projeto/RPG-battle/godot_project/bin/godot --headless --path /home/anderson/Documents/projeto/RPG-battle/godot_project -s addons/gut/gut_cmdln.gd -gexit -gtest=res://test/unit/test_websocket_client.gd`
   - Run full suite:
     `/home/anderson/Documents/projeto/RPG-battle/godot_project/run_gut_tests.sh`
   - Verify 100% pass and 0 ObjectDB leaks.

## MANDATORY INTEGRITY WARNING
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## Output Requirements
- Write your implementation and tests.
- Run tests and confirm results.
- Write your completion handoff report to:
  `/home/anderson/Documents/projeto/RPG-battle/.agents/m6_worker_1/handoff.md`
- Update `progress.md` with timestamps during your work.
- Send a completion message via `send_message` back to orchestrator (`parent`).

## 2026-10-01T05:49:58Z
You are m6_worker_1. Your working directory is /home/anderson/Documents/projeto/RPG-battle/.agents/m6_worker_1.

Read your task instructions at:
/home/anderson/Documents/projeto/RPG-battle/.agents/m6_worker_1/DISPATCH.md

Also read:
- /home/anderson/Documents/projeto/RPG-battle/.agents/ORIGINAL_REQUEST.md (MANDATORY: read first)
- /home/anderson/Documents/projeto/RPG-battle/PROJECT.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/skills/organizacao_refatoracao/SKILL.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/m6_spec_miner_1/spec_report.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/m6_explorer_1/architecture_report.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/m6_explorer_2/test_strategy_report.md

Exclusive Write Ownership:
- godot_project/scripts/network/WebSocketClient.gd
- godot_project/test/unit/test_websocket_client.gd

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Implement WebSocketClient.gd and test_websocket_client.gd. Run the tests via Godot headless CLI, verify 100% pass and 0 ObjectDB memory leaks, write your handoff to:
/home/anderson/Documents/projeto/RPG-battle/.agents/m6_worker_1/handoff.md
And send a message back to parent (5dbb519a-f6c3-4b1f-b7e0-6ec494d60de9) when done.

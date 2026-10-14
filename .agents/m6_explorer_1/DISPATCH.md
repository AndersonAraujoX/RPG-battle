# Task Assignment: m6_explorer_1

## Objective
Investigate Godot 4 `WebSocketPeer` architecture, state lifecycle, reconnection strategies, signal integration with `EventBus.gd`, and clean client architecture for `godot_project/scripts/network/WebSocketClient.gd`.

## Inputs & Context Files
- /home/anderson/Documents/projeto/RPG-battle/.agents/ORIGINAL_REQUEST.md (MANDATORY: read first)
- /home/anderson/Documents/projeto/RPG-battle/PROJECT.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/skills/organizacao_refatoracao/SKILL.md
- /home/anderson/Documents/projeto/RPG-battle/godot_project/scripts/autoloads/EventBus.gd
- /home/anderson/Documents/projeto/RPG-battle/godot_project/scripts/autoloads/GameManager.gd

## Detailed Scope
1. Analyze Godot 4 `WebSocketPeer` API:
   - Creation, connection initialization (`connect_to_url`), TLS options, polling (`poll()`), state transitions (`STATE_CONNECTING`, `STATE_OPEN`, `STATE_CLOSING`, `STATE_CLOSED`).
   - Packet receiving (`get_available_packet_count()`, `get_packet().get_string_from_utf8()`) and packet sending (`put_packet()`).
2. Design the `WebSocketClient.gd` architecture:
   - Is it a `Node` that can be added to the scene tree or instantiated dynamically?
   - Handling `_process(delta)` polling safely.
   - Signals emitted by `WebSocketClient`: `connected_to_server`, `connection_closed`, `connection_error(code, reason)`, `message_received(type, payload)`, `state_update_received(data)`, etc.
   - Typed methods for sending actions: `send_select_hero(...)`, `send_select_card(...)`, `send_move_hero(...)`, `send_attack_target(...)`, `send_work_action(...)`, `send_chat(...)`, `send_ping()`.
   - Reconnection mechanism: backoff strategy, state preservation, auto-reconnect toggle.
   - Dependency injection / mockability: how to allow unit testing without requiring an active network socket (e.g. injecting a mock peer or simulated packet feed).

## Output Requirements
- Write your architecture & design recommendations to:
  `/home/anderson/Documents/projeto/RPG-battle/.agents/m6_explorer_1/architecture_report.md`
- Write your completion handoff to:
  `/home/anderson/Documents/projeto/RPG-battle/.agents/m6_explorer_1/handoff.md`
- Update `progress.md` with timestamps during your work.
- Send a completion message via `send_message` back to orchestrator (`parent`).

## 2026-10-01T05:42:42Z
You are m6_explorer_1. Your working directory is /home/anderson/Documents/projeto/RPG-battle/.agents/m6_explorer_1.

Read your task instructions at:
/home/anderson/Documents/projeto/RPG-battle/.agents/m6_explorer_1/DISPATCH.md

Also read:
- /home/anderson/Documents/projeto/RPG-battle/.agents/ORIGINAL_REQUEST.md (MANDATORY: read first)
- /home/anderson/Documents/projeto/RPG-battle/PROJECT.md
- /home/anderson/Documents/projeto/RPG-battle/godot_project/scripts/autoloads/EventBus.gd
- /home/anderson/Documents/projeto/RPG-battle/godot_project/scripts/autoloads/GameManager.gd

Investigate Godot 4 WebSocketPeer API, connection state machine, packet handling, typed send methods, reconnection logic, and mock injection for testing.
Write:
1. /home/anderson/Documents/projeto/RPG-battle/.agents/m6_explorer_1/architecture_report.md
2. /home/anderson/Documents/projeto/RPG-battle/.agents/m6_explorer_1/handoff.md

Update progress.md as you work. When finished, send a message to parent (5dbb519a-f6c3-4b1f-b7e0-6ec494d60de9) with your summary and handoff path.

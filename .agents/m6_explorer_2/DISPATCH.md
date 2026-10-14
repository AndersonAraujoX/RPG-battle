# Task Assignment: m6_explorer_2

## Objective
Investigate existing GUT test suites in `godot_project/test/unit/` to establish testing patterns, mock strategies, zero-leak cleanup conventions, and Arrange-Act-Assert (AAA) test templates for `godot_project/test/unit/test_websocket_client.gd`.

## Inputs & Context Files
- /home/anderson/Documents/projeto/RPG-battle/.agents/ORIGINAL_REQUEST.md (MANDATORY: read first)
- /home/anderson/Documents/projeto/RPG-battle/PROJECT.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/skills/organizacao_refatoracao/SKILL.md
- /home/anderson/Documents/projeto/RPG-battle/godot_project/test/unit/test_cerco_deck.gd
- /home/anderson/Documents/projeto/RPG-battle/godot_project/test/unit/test_isectum_castes.gd
- /home/anderson/Documents/projeto/RPG-battle/godot_project/test/unit/test_fortress_board.gd

## Detailed Scope
1. Examine how existing GUT tests manage Node lifecycle, teardown, and memory:
   - Use of `autofree()`, `autoqfree()`, or manual `free()` / `queue_free()`.
   - How `before_each()` and `after_each()` ensure 0 ObjectDB leaks.
2. Design testing strategy for `WebSocketClient`:
   - Unit tests must run headless and offline without requiring a live FastAPI server.
   - Design mock peer / test harness to test:
     * Happy path: connection state transitions, sending typed packets, receiving and parsing JSON packets, signal emissions.
     * Edge cases: malformed JSON, unknown message types, empty payloads, missing required fields.
     * Network failures: unexpected disconnect, connection refused, timeout, ping/pong latency.
     * Reconnection logic: retry counts, state reset, event dispatch.
3. Formulate concrete test case specifications with Arrange-Act-Assert structure matching the mandatory rules.

## Output Requirements
- Write your testing strategy report to:
  `/home/anderson/Documents/projeto/RPG-battle/.agents/m6_explorer_2/test_strategy_report.md`
- Write your completion handoff to:
  `/home/anderson/Documents/projeto/RPG-battle/.agents/m6_explorer_2/handoff.md`
- Update `progress.md` with timestamps during your work.
- Send a completion message via `send_message` back to orchestrator (`parent`).

## 2026-10-01T05:42:42Z
Received dispatch:
Investigate GUT testing patterns, zero-leak node lifecycle (autofree/free), mock socket strategies, and formulate concrete AAA test case specifications for test_websocket_client.gd.


# Task Assignment: m6_challenger_2

## Objective
Empirically verify robustness and adversarial resilience of `godot_project/scripts/network/WebSocketClient.gd`.

## Inputs & Context Files (MANDATORY: read first)
- /home/anderson/Documents/projeto/RPG-battle/.agents/ORIGINAL_REQUEST.md
- /home/anderson/Documents/projeto/RPG-battle/PROJECT.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/skills/organizacao_refatoracao/SKILL.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/m6_worker_1/handoff.md
- /home/anderson/Documents/projeto/RPG-battle/godot_project/scripts/network/WebSocketClient.gd
- /home/anderson/Documents/projeto/RPG-battle/godot_project/test/unit/test_websocket_client.gd
- /home/anderson/Documents/projeto/RPG-battle/src/server/session.py

## Challenger Mission
1. Verify protocol edge cases and empirical behavior:
   - Simulate sudden connection loss mid-game and verify auto-reconnect backoff progression.
   - Verify that anti-cheat hand privacy is correctly handled when reading `STATE_UPDATE` (verifying `is_me` flag).
   - Test concurrent calls to `send_*` while `STATE_CONNECTING` vs `STATE_OPEN` vs `STATE_CLOSED`.
   - Test injection of corrupt UTF-8 or mixed binary/text frames.
2. Execute the verification commands:
   - Run isolated WebSocket test suite:
     `/home/anderson/Documents/projeto/RPG-battle/godot_project/bin/godot --headless --path /home/anderson/Documents/projeto/RPG-battle/godot_project -s addons/gut/gut_cmdln.gd -gexit -gtest=res://test/unit/test_websocket_client.gd`
   - Run the full suite:
     `/home/anderson/Documents/projeto/RPG-battle/godot_project/run_gut_tests.sh`
   - Verify 0 ObjectDB leaks under `./godot_project/bin/godot --headless --verbose --path ./godot_project -s addons/gut/gut_cmdln.gd -gexit`.
3. Issue a definitive verdict: `APPROVE` or `REQUEST_CHANGES`.

## Output Requirements
- Write your challenger report to:
  `/home/anderson/Documents/projeto/RPG-battle/.agents/m6_challenger_2/challenger_report.md`
- Write your completion handoff to:
  `/home/anderson/Documents/projeto/RPG-battle/.agents/m6_challenger_2/handoff.md`
- Update `progress.md` with timestamps during your work.
- Send a completion message via `send_message` back to orchestrator (`parent`) with your explicit verdict.

## 2026-10-01T05:57:14Z
You are m6_challenger_2. Your working directory is /home/anderson/Documents/projeto/RPG-battle/.agents/m6_challenger_2.
Verify protocol resilience: mid-game connection drop, reconnect state recovery, anti-cheat hand privacy handling, concurrent send state transitions, corrupted frame injection. Run test commands and verify 0 leaks. Issue a definitive verdict: APPROVE or REQUEST_CHANGES.


# Task Assignment: m6_reviewer_2

## Objective
Conduct an independent adversarial and robustness review of `godot_project/scripts/network/WebSocketClient.gd` and `godot_project/test/unit/test_websocket_client.gd`.

## Inputs & Context Files (MANDATORY: read first)
- /home/anderson/Documents/projeto/RPG-battle/.agents/ORIGINAL_REQUEST.md
- /home/anderson/Documents/projeto/RPG-battle/PROJECT.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/skills/organizacao_refatoracao/SKILL.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/m6_worker_1/handoff.md
- /home/anderson/Documents/projeto/RPG-battle/godot_project/scripts/network/WebSocketClient.gd
- /home/anderson/Documents/projeto/RPG-battle/godot_project/test/unit/test_websocket_client.gd
- /home/anderson/Documents/projeto/RPG-battle/src/server/session.py

## Review Criteria
1. Robustness & Fault Tolerance:
   - Behavior when receiving unexpected payloads, non-JSON strings, empty packets, null fields.
   - Behavior when connection closes abnormally (`code != 1000`) vs cleanly (`code == 1000`).
   - Exponential backoff algorithm correctness and retry termination.
2. Test Quality & AAA Conformance:
   - Does every test in `test_websocket_client.gd` follow Arrange-Act-Assert?
   - Are edge cases (empty strings, negative coordinates, out-of-bounds, invalid state) rigorously tested?
   - Is `autofree` used properly? Are there any dangling nodes or ObjectDB leaks?
3. Test Execution & Verification:
   - Run the test suite:
     `/home/anderson/Documents/projeto/RPG-battle/godot_project/bin/godot --headless --path /home/anderson/Documents/projeto/RPG-battle/godot_project -s addons/gut/gut_cmdln.gd -gexit -gtest=res://test/unit/test_websocket_client.gd`
   - Run the full suite:
     `/home/anderson/Documents/projeto/RPG-battle/godot_project/run_gut_tests.sh`
   - Confirm 0 ObjectDB memory leaks and 100% pass rate.
4. Issue a definitive verdict: `APPROVE` or `REQUEST_CHANGES`.

## Output Requirements
- Write your review report to:
  `/home/anderson/Documents/projeto/RPG-battle/.agents/m6_reviewer_2/review_report.md`
- Write your completion handoff to:
  `/home/anderson/Documents/projeto/RPG-battle/.agents/m6_reviewer_2/handoff.md`
- Update `progress.md` with timestamps during your work.
- Send a completion message via `send_message` back to orchestrator (`parent`) with your explicit verdict.

## 2026-10-01T05:57:14Z

You are m6_reviewer_2. Your working directory is /home/anderson/Documents/projeto/RPG-battle/.agents/m6_reviewer_2.

Read your task instructions at:
/home/anderson/Documents/projeto/RPG-battle/.agents/m6_reviewer_2/DISPATCH.md

Also read:
- /home/anderson/Documents/projeto/RPG-battle/.agents/ORIGINAL_REQUEST.md (MANDATORY: read first)
- /home/anderson/Documents/projeto/RPG-battle/PROJECT.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/skills/organizacao_refatoracao/SKILL.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/m6_worker_1/handoff.md
- /home/anderson/Documents/projeto/RPG-battle/godot_project/scripts/network/WebSocketClient.gd
- /home/anderson/Documents/projeto/RPG-battle/godot_project/test/unit/test_websocket_client.gd
- /home/anderson/Documents/projeto/RPG-battle/src/server/session.py

Review robustness, fault tolerance, exponential backoff, AAA test structure, edge cases. Run GUT tests. Issue a definitive verdict: APPROVE or REQUEST_CHANGES.
Write:
1. /home/anderson/Documents/projeto/RPG-battle/.agents/m6_reviewer_2/review_report.md
2. /home/anderson/Documents/projeto/RPG-battle/.agents/m6_reviewer_2/handoff.md

Update progress.md as you work. Send a message to parent (5dbb519a-f6c3-4b1f-b7e0-6ec494d60de9) with your verdict and handoff path.


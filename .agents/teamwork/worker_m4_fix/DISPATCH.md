# Dispatch — Milestone M4 Remediation Worker

## Mission
Apply the remediation fixes requested by Reviewer 2 for Milestone M4.

## Reference Materials
- `/home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/reviewer_m4_2/handoff.md`
- `/home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/challenger_m4_1/handoff.md`
- `/home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/challenger_m4_2/handoff.md`

## Required Fixes
1. **Fix `test_run_combat_integration.gd:279-282`**:
   `RunSession.start_new()` rejects heroes with 0 HP. Start the session with positive HP for Stark (e.g. `{"aquele": 30, "stark": 20, "lysander": 20}`), and then invoke `run.damage_hero("stark", 9999)` to make Stark fall legitimately. Ensure all 8 assertions in `test_cerco_game_controller_ingests_run_session_with_living_heroes_only` execute cleanly without script errors.
2. **Fix `RunCombatBridge.gd:149-159`**:
   Check `var was_alive: bool = run_state.is_hero_alive(hid)` BEFORE calling `run_state.damage_hero(hid, 9999)`. If `was_alive`, append to `summary["newly_fallen"]`.
3. **Fix `CercoGameController.gd:175`**:
   Pass `EventBus` explicitly to `RelicManager.new(run_state_ref, eb)`. Use `get_node_or_null("/root/EventBus")` if `EventBus` isn't already cached.
4. **Fix `CombatEncounterGenerator.gd:83`**:
   Align docstrings and signature: `generate_encounter(node: RunNode, floor_index: int = 0, custom_rng: RandomNumberGenerator = null) -> Dictionary`.
5. Run `bash godot_project/run_gut_tests.sh` and ensure 100% of all tests pass with exit code 0.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## Deliverable
Deliver your report to:
`/home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/worker_m4_fix/handoff.md`


## 2026-10-16T03:15:41Z
Received dispatch message:
You are the M4 Remediation Worker.
Your working directory is: /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/worker_m4_fix

Tasks:
1. In `test_run_combat_integration.gd:279-282`: start run session with positive HP for Stark (e.g. {"aquele": 30, "stark": 20, "lysander": 20}), then call `run.damage_hero("stark", 9999)` so Stark falls legitimately. Verify all 8 assertions execute without script errors.
2. In `RunCombatBridge.gd:149-159`: check `var was_alive: bool = run_state.is_hero_alive(hid)` BEFORE calling `run_state.damage_hero(hid, 9999)`. If `was_alive`, append to `summary["newly_fallen"]`.
3. In `CercoGameController.gd:175`: pass `EventBus` explicitly: `RelicManager.new(run_state_ref, get_node_or_null("/root/EventBus"))`.
4. In `CombatEncounterGenerator.gd:83`: align docstrings and signature.
5. Run `bash godot_project/run_gut_tests.sh` from `/home/anderson/Documents/projeto/RPG-battle` and verify 100% of all tests pass with exit code 0.

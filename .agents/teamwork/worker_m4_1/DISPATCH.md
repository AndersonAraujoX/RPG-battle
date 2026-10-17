# Dispatch — Milestone M4 Implementation Worker

## Mission
Implement Milestone M4: Full Tactical Combat Integration into Run Map Nodes (COMBAT, ELITE, SIEGE, BOSS), Persistent Hero HP, and Permadeath.

## Exclusive File Ownership
The Worker exclusively owns and edits/creates:
- `godot_project/scripts/run/combat/RunCombatBridge.gd`
- `godot_project/scripts/run/combat/CombatEncounterGenerator.gd`
- `godot_project/scripts/run/RunMapScreen.gd`
- `godot_project/scripts/main/CercoGameController.gd`
- `godot_project/test/unit/test_run_combat_integration.gd`
- `godot_project/test/unit/test_combat_encounter_generator.gd`

## Reference Designs & Handoffs to Read First
- `/home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/ORIGINAL_REQUEST.md`
- `/home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/orchestrator_1/PROJECT.md`
- `/home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m4_1/handoff.md` (Combat Bridge & Controller Hooks)
- `/home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m4_2/handoff.md` (Combat Encounter Generator)
- `/home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m4_3/handoff.md` (HP Persistence, Permadeath & GUT Test Suite Design)

## Verification Requirement
Run `bash godot_project/run_gut_tests.sh` from `/home/anderson/Documents/projeto/RPG-battle`.
Ensure 100% of all tests pass (the baseline 808 + all new M4 tests) with 0 failures, 0 errors, and exit code 0.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## Deliverable
Deliver your handoff report to:
`/home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/worker_m4_1/handoff.md`

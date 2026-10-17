# Dispatch — Milestone M4: Persistent HP, Permadeath & GUT Test Design Explorer

## Mission
Design the two-way HP persistence, Permadeath rules, and the complete GUT unit test suites for Milestone M4.

## Input Files
- `/home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/ORIGINAL_REQUEST.md`
- `/home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/orchestrator_1/PROJECT.md`
- `/home/anderson/Documents/projeto/RPG-battle/godot_project/scripts/run/RunState.gd`
- `/home/anderson/Documents/projeto/RPG-battle/godot_project/scripts/main/CercoGameController.gd`
- Existing GUT run tests: `godot_project/test/unit/test_run_map_and_state.gd`

## Deliverables
- Design end-of-battle HP synchronization:
  - Unit HP -> `RunState.hero_hp[hero_id]`.
  - Fallen heroes (HP 0 or failed death saves) -> `RunState.fallen_heroes`.
  - Party wipe -> `RunState.status = Status.DEFEAT` -> Game Over screen with amber calculation.
  - Battle victory -> mark node complete, open M3 RewardModal, return to `RunMapScreen`.
- Design GUT unit test suites:
  - `godot_project/test/unit/test_run_combat_integration.gd`
  - `godot_project/test/unit/test_combat_encounter_generator.gd`
  Ensuring strict AAA format, headless safety bare-node checks, zero leaks.
- Deliver report to `/home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m4_3/handoff.md`.

## 2026-10-16T02:23:39Z
You are the M4 Persistent HP & Permadeath Explorer.
Your working directory is: /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m4_3
You must read:
- /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/ORIGINAL_REQUEST.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/orchestrator_1/PROJECT.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m4_3/DISPATCH.md
- /home/anderson/Documents/projeto/RPG-battle/godot_project/scripts/run/RunState.gd
- /home/anderson/Documents/projeto/RPG-battle/godot_project/scripts/main/CercoGameController.gd

Design the roundtrip HP persistence, permadeath tracking, win/loss routing, and GUT test suite design for test_run_combat_integration.gd and test_combat_encounter_generator.gd.
Deliver report to /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m4_3/handoff.md.
When done, notify orchestrator via send_message.

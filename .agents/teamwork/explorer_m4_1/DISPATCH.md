# Dispatch — Milestone M4: Combat Bridge & Controller Hook Explorer

## Mission
Design the tactical combat bridge between the roguelike run and `Main.tscn` / `CercoGameController.gd`.

## Input Files
- `/home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/ORIGINAL_REQUEST.md`
- `/home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/orchestrator_1/PROJECT.md`
- `/home/anderson/Documents/projeto/RPG-battle/godot_project/scripts/run/RunSession.gd`
- `/home/anderson/Documents/projeto/RPG-battle/godot_project/scripts/run/RunState.gd`
- `/home/anderson/Documents/projeto/RPG-battle/godot_project/scripts/run/RunNode.gd`
- `/home/anderson/Documents/projeto/RPG-battle/godot_project/scripts/run/RunMapScreen.gd`
- `/home/anderson/Documents/projeto/RPG-battle/godot_project/scripts/main/CercoGameController.gd`

## Deliverables
- Design `godot_project/scripts/run/combat/RunCombatBridge.gd` (`RefCounted`).
- Specify how `RunMapScreen.gd` transitions to combat when a combat node is clicked (`COMBAT`, `ELITE`, `SIEGE`, `BOSS`).
- Specify how `CercoGameController.gd` detects `RunSession.has_active_run()`, ingests surviving heroes, current HP, and deck, while preserving standalone Cerco mode when no run is active.
- Deliver report to `/home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m4_1/handoff.md`.


## 2026-10-16T02:23:39Z
You are the M4 Combat Bridge Explorer.
Your working directory is: /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m4_1
You must read:
- /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/ORIGINAL_REQUEST.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/orchestrator_1/PROJECT.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m4_1/DISPATCH.md
- /home/anderson/Documents/projeto/RPG-battle/godot_project/scripts/run/RunSession.gd
- /home/anderson/Documents/projeto/RPG-battle/godot_project/scripts/run/RunMapScreen.gd
- /home/anderson/Documents/projeto/RPG-battle/godot_project/scripts/main/CercoGameController.gd

Design the bridge between RunMapScreen and Main.tscn (RunCombatBridge.gd) and controller hooks in CercoGameController.gd.
Deliver report to /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m4_1/handoff.md.
When done, notify orchestrator via send_message.

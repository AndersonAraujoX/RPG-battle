# Dispatch — Milestone M4: Combat Encounter Generator Explorer

## Mission
Design the procedural encounter generation system for Milestone M4 based on `IsectumCastes.gd`, Act index, floor index, and node type.

## Input Files
- `/home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/ORIGINAL_REQUEST.md`
- `/home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/orchestrator_1/PROJECT.md`
- `/home/anderson/Documents/projeto/RPG-battle/CAMPANHA_ROGUELIKE.md`
- `/home/anderson/Documents/projeto/RPG-battle/godot_project/scripts/cerco/IsectumCastes.gd`
- `/home/anderson/Documents/projeto/RPG-battle/godot_project/scripts/run/RunNode.gd`

## Deliverables
- Design `godot_project/scripts/run/combat/CombatEncounterGenerator.gd` (`RefCounted`).
- Specify enemy squad composition algorithms:
  - Act 1: Tier 1 castes (`larva_carniceira`, `formiga_acida`, `besouro_gorgulho`, `gafanhoto_praga`).
  - `COMBAT`: 3-4 basic enemies.
  - `SIEGE`: 4-6 enemies with siege/brutamontes castes.
  - `ELITE`: heavy insects (`escaravelho_couracado` or `tarantula_golias`).
  - `BOSS`: Act 1 boss `viuva_canibal` with web hazards.
- Deterministic RNG seeding support.
- Deliver report to `/home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m4_2/handoff.md`.

## 2026-10-16T02:23:39Z
You are the M4 Encounter Generator Explorer.
Your working directory is: /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m4_2
You must read:
- /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/ORIGINAL_REQUEST.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/orchestrator_1/PROJECT.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m4_2/DISPATCH.md
- /home/anderson/Documents/projeto/RPG-battle/godot_project/scripts/cerco/IsectumCastes.gd
- /home/anderson/Documents/projeto/RPG-battle/godot_project/scripts/run/RunNode.gd

Design CombatEncounterGenerator.gd with deterministic squad generation by Act, floor, and node type (COMBAT, SIEGE, ELITE, BOSS - viuva_canibal).
Deliver report to /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m4_2/handoff.md.
When done, notify orchestrator via send_message.

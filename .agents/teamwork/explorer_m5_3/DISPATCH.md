# Dispatch — Milestone M5: Act II Encounter Integration & GUT Test Architecture Explorer

## Mission
Design the Act II integration in `CombatEncounterGenerator.gd` and the architecture for Milestone M5 GUT unit test suites (`test_act2_mechanics.gd` and `test_boss_swarm_queen.gd`).

## Input Files
- `/home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/ORIGINAL_REQUEST.md`
- `/home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/orchestrator_1/PROJECT.md`
- `/home/anderson/Documents/projeto/RPG-battle/CAMPANHA_ROGUELIKE.md`
- `/home/anderson/Documents/projeto/RPG-battle/godot_project/scripts/run/combat/CombatEncounterGenerator.gd`
- `/home/anderson/Documents/projeto/RPG-battle/godot_project/scripts/run/combat/RunCombatBridge.gd`
- `/home/anderson/Documents/projeto/RPG-battle/godot_project/test/unit/test_combat_encounter_generator.gd`

## Deliverables
1. Design Act II updates to `CombatEncounterGenerator.gd`:
   - Act 2 enemy selection pool using Tier 2 Castes:
     - Louva-Deus Ceifador (`louva_deus_ceifador`)
     - Vespa Caçadora (`vespa_cacadora`)
     - Aranha Clepto (`aranha_clepto`)
     - Libélula Blindada (`libelula_blindada`)
     - Infiltrador / Vagalume das Sombras (`infiltrador`, `vagalume_sombras`)
   - Act 2 ELITE pool: Mini-boss Cigarra Ressonante (`cigarra_ressonante`).
   - Act 2 BOSS: Rainha do Enxame (`rainha_do_enxame`) with Royal Guards and initial cocoons.
   - Cocoon placement logic in Act 2 combat encounters.
2. Design comprehensive GUT test suites:
   - `godot_project/test/unit/test_act2_mechanics.gd`:
     - TorchLighting Chebyshev radius 3 calculation, boundary tests, empty hero array, dead hero positions ignored, `tocha_eterna` relic radius boost (+2).
     - ChitinCocoon countdown decrement, HP damage, cancellation on death before hatch, hatch behavior (spawn T2 unit, 5 acid damage to adjacent cells).
     - Cigarra Ressonante `pulso_sonico` AoE clustering trigger, stun status application.
   - `godot_project/test/unit/test_boss_swarm_queen.gd`:
     - Rainha do Enxame stats and initialization.
     - Royal Guard damage reduction passive (50% damage reduction when Royal Guard is present, normal damage when all guards are defeated).
     - `chamado_da_rainha` 2-turn periodic brood summoning.
     - Transition narrative hook upon defeat.
3. Verify test compliance: strict Arrange-Act-Assert (AAA), `autofree` cleanup, bare-node safety, deterministic RNG.
4. Deliver report to `/home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m5_3/handoff.md`.

## 2026-10-16T10:12:31Z
Received message from orchestrator:
- Sender: aa7d5d2d-ef0f-482c-be6b-93c1793915c2
- Content:
You are Explorer 3 for Milestone M5 (Act II Encounters & GUT Test Architecture).
Your working directory is: /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m5_3
You must read:
- /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/ORIGINAL_REQUEST.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/orchestrator_1/PROJECT.md
- /home/anderson/Documents/projeto/RPG-battle/CAMPANHA_ROGUELIKE.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m5_3/DISPATCH.md
- /home/anderson/Documents/projeto/RPG-battle/godot_project/scripts/run/combat/CombatEncounterGenerator.gd
- /home/anderson/Documents/projeto/RPG-battle/godot_project/test/unit/test_combat_encounter_generator.gd

Design:
1. Act II additions to `CombatEncounterGenerator.gd`:
   - Tier 2 caste enemy pools for Act 2 COMBAT, SIEGE, ELITE (Cigarra Ressonante), and BOSS (Rainha do Enxame).
   - Cocoon placement integration into encounter data.
2. Comprehensive GUT test suites:
   - `godot_project/test/unit/test_act2_mechanics.gd`
   - `godot_project/test/unit/test_boss_swarm_queen.gd`
Verify AAA pattern, bare-node headless safety, autofree cleanup, and deterministic seeding.
Deliver report to /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m5_3/handoff.md.
When finished, notify orchestrator via send_message.

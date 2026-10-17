## 2026-10-16T10:24:11Z
You are the M5 Implementation Worker.
Your working directory is: /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/worker_m5_1

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

You must read before starting:
- /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/ORIGINAL_REQUEST.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/orchestrator_1/PROJECT.md
- /home/anderson/Documents/projeto/RPG-battle/CAMPANHA_ROGUELIKE.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/worker_m5_1/DISPATCH.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m5_1/handoff.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m5_2/handoff.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m5_3/handoff.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m5_3/proposed_CombatEncounterGenerator.gd
- /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m5_3/proposed_test_act2_mechanics.gd
- /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m5_3/proposed_test_boss_swarm_queen.gd
- /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m5_3/proposed_test_combat_encounter_generator_additions.gd

Your mission:
Implement Milestone M5 (Act II: Túneis Vivos):
1. Implement `godot_project/scripts/tactical/TorchLighting.gd` (RefCounted):
   - Chebyshev visibility radius 3 around living heroes.
   - Relic synergy: `tocha_eterna` increases radius by +2 (radius 5).
   - Methods: `update_visibility(heroes_positions: Array[Vector2i], bonus_radius: int = 0, grid = null) -> void`, `is_cell_lit(cell: Vector2i) -> bool`, `get_lit_cells() -> Array[Vector2i]`, `can_target_cell(attacker, target, range: int) -> bool`, `get_shroud_modifiers(enemy_pos: Vector2i) -> Dictionary`.
2. Implement `godot_project/scripts/entities/ChitinCocoon.gd` (RefCounted):
   - 15 HP, 10 AC, 3-turn hatch countdown.
   - `apply_damage(amount: int) -> int`: reduces HP, destroys at <= 0 and cancels hatch.
   - `tick_round(grid = null, rng = null) -> Dictionary`: decrements countdown; on 0, spawns Tier 2 unit in adjacent free cell and deals 5 acid damage burst to adjacent cells.
3. Implement `godot_project/scripts/entities/bosses/CigarraRessonante.gd` (extends `Character`):
   - Elite mini-boss (70-90 HP, def 80, AC 15, move speed 5, flyer).
   - Stun immunity (`add_status_effect("stunned")` blocked).
   - `pulso_sonico(target_pos: Vector2i, heroes: Array, rng = null) -> Dictionary`: checks if >= 2 heroes are clustered (Chebyshev distance <= 2); if clustered, deals AoE damage and applies Stun for 1 round. If isolated, deals damage without stun.
4. Implement `godot_project/scripts/entities/bosses/RainhaDoEnxame.gd` (extends `Character`):
   - Act II Boss (180-220 HP, def 200, AC 16).
   - Royal Guard protection: 50% damage reduction while any Royal Guard is alive (`has_living_royal_guard() -> bool`).
   - `chamado_da_rainha(grid = null, count: int = 2, rng = null) -> Array`: brood summon every 2 turns.
   - Transition narrative quote on defeat: *"Vocês matam a carne, mas a Mente é eterna! Enquanto os Três Corações baterem, o Rei jamais cairá!"*.
5. Update `godot_project/scripts/run/combat/CombatEncounterGenerator.gd` using the blueprint from `proposed_CombatEncounterGenerator.gd` (Act 2 pools, Tier 2 caste aliases, mini-boss Cigarra Ressonante for Act 2 ELITE, Boss Rainha do Enxame with Royal Guards and transition hook, and ChitinCocoon generation).
6. Implement the GUT unit test suites:
   - `godot_project/test/unit/test_act2_mechanics.gd`
   - `godot_project/test/unit/test_boss_swarm_queen.gd`
   - Incorporate Act 2 tests in `godot_project/test/unit/test_combat_encounter_generator.gd` or dedicated suite.
   Ensure strict AAA pattern, bare-node headless safety, autofree cleanup, and deterministic seeding.
7. Execute `bash godot_project/run_gut_tests.sh` from `/home/anderson/Documents/projeto/RPG-battle` and verify 100% of all tests pass (the baseline 873 + all new M5 tests) with exit code 0.
8. Deliver handoff report to `/home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/worker_m5_1/handoff.md`.
When complete, notify orchestrator via send_message.

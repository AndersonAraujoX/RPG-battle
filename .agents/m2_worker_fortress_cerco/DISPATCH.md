## 2026-10-01T00:40:00Z
You are the Milestone 2 Implementation Worker (Cerco da Fortaleza & Juiz de Combate) for RPG-battle Godot 4.

Your working directory is:
/home/anderson/Documents/projeto/RPG-battle/.agents/m2_worker_fortress_cerco

You MUST read these files first:
- /home/anderson/Documents/projeto/RPG-battle/.agents/ORIGINAL_REQUEST.md (Authoritative request with Strategic Pivot to Cerco)
- /home/anderson/Documents/projeto/RPG-battle/PROJECT.md (Milestones & Contracts for Cerco)
- /home/anderson/Documents/projeto/RPG-battle/.agents/skills/organizacao_refatoracao/SKILL.md (Code standards, AAA unit tests, SOLID)
- /home/anderson/Documents/projeto/RPG-battle/src/juiz_combate.py (Reference Python Cerco combat engine)
- /home/anderson/Documents/projeto/RPG-battle/src/cerco/ (Reference Cerco board and states)

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Exclusively Owned Files:
- godot_project/scripts/cerco/FortressBoard.gd
- godot_project/scripts/cerco/CercoCombatJudge.gd
- godot_project/test/unit/test_fortress_board.gd
- godot_project/test/unit/test_cerco_combat_judge.gd

Your Objectives:
1. Implement `godot_project/scripts/cerco/FortressBoard.gd`:
   - 20x20 discrete grid (Vector2i(0,0) to Vector2i(19,19)), cell validation.
   - 17 logical zones:
     * Core: CAMARA_CENTRAL (Victory condition if overrun)
     * Workshops: CARPINTARIA (Wood), CURTUME (Leather), FUNDICAO (Metal/Crystal)
     * Courtyard: PATIO_CENTRAL
     * 4 Walls: MURALHA_NORTE, MURALHA_SUL, MURALHA_LESTE, MURALHA_OESTE
     * 4 Towers: TORRE_NOROESTE, TORRE_NORDESTE, TORRE_SUDOESTE, TORRE_SUDESTE
     * 4 Spawns: SPAWN_NORTE, SPAWN_SUL, SPAWN_LESTE, SPAWN_OESTE
   - Complete 400-cell mapping: every coordinate in 0..19, 0..19 maps to exactly one zone.
   - Elevation levels: 0 for Spawns, Patio, Workshops, Camara; 1 for Walls; 2 for Towers.
   - Adjacency & Invasion Graph: `get_adjacent_zones(zone_id) -> Array[String]` and `get_next_invasion_zones(zone_id) -> Array[String]`.
   - Wall integrity system: each wall has max HP (e.g. 100), `damage_wall(wall_id, amount)`, `repair_wall(wall_id, amount)`, `is_wall_breached(wall_id)`.
   - Unit tracking: `place_unit(unit_id, pos)`, `move_unit(unit_id, to_pos)`, `remove_unit(unit_id)`, `get_units_in_zone(zone_id) -> Array[String]`.

2. Implement `godot_project/scripts/cerco/CercoCombatJudge.gd`:
   - Custom D6 dice: enum `D6Face { IMPACTO, DISPARO, CRITICO, ESQUIVA, NULO }`.
   - Roll generator: `roll_cerco_dice(num_dice, has_advantage, has_disadvantage) -> Array[D6Face]`. Support deterministic injection for unit testing via optional `forced_rolls`.
   - Melee resolution: 2 impactos = 1 damage (`(impacts + 2*crits) / 2`). Armor deduction.
   - Tower Ranged resolution: 1 disparo de balestra = 1 damage (`shots + 2*crits`).
   - Elevation bonuses/penalties: Tower down to Ground/Wall gains elevation advantage (+1 die); Ground up to Tower suffers disadvantage.
   - Brutamontes rules: 3 circles of HP. Each successful damage application ticks off 1 circle.
   - Infiltradores: bypasses unbreached walls if no defenders are stationed on the wall.
   - Catapulta: deals direct siege damage to wall HP (`resolve_catapult_siege_damage(wall_id, damage)`).

3. Create Comprehensive GUT Test Suites:
   - `test/unit/test_fortress_board.gd`:
     * Validate all 17 zones and their coordinates within 20x20 (full 400 cell coverage, no duplicates, no missing cells).
     * Validate elevation mapping (0, 1, 2).
     * Validate adjacency graph and invasion pathways towards Camara Central.
     * Validate wall damage, breach at 0 HP, and repair.
     * Validate unit placement, movement, and querying.
     * Strict AAA structure.
   - `test/unit/test_cerco_combat_judge.gd`:
     * Validate D6 custom roll mechanics, face enum values, and deterministic roll evaluation.
     * Validate Melee math: 2 impactos = 1 damage, odd impacts round down, crits count as 2 impacts, armor deduction.
     * Validate Tower Balestra: 1 shot = 1 damage, elevation advantage bonus.
     * Validate Brutamontes 3-circle HP tracking.
     * Validate Infiltrador wall bypass (free when 0 defenders, blocked when >= 1 defender).
     * Validate Catapult direct siege damage to walls and breach triggering.
     * Strict AAA structure.

4. Execution and Verification:
   - Run `./godot_project/run_gut_tests.sh` and ensure 100% tests pass (all previous M1 tests + new Cerco tests).
   - Verify 0 ObjectDB leaks at exit under `./godot_project/bin/godot --headless --verbose --path ./godot_project -s addons/gut/gut_cmdln.gd -gexit`.
   - Write comprehensive `handoff.md` and report back to parent.

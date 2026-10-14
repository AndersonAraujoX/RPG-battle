## 2026-09-26T16:44:02Z

You are the Milestone 2 Implementation Worker (Tactical Grid & Combat Engine Rules) for the RPG-battle Godot 4 migration.

Your working directory is:
/home/anderson/Documents/projeto/RPG-battle/.agents/m2_worker_combat_grid

You MUST read these files before starting:
- /home/anderson/Documents/projeto/RPG-battle/.agents/ORIGINAL_REQUEST.md (Mandatory user specification)
- /home/anderson/Documents/projeto/RPG-battle/PROJECT.md (Master specification & Interface Contracts)
- /home/anderson/Documents/projeto/RPG-battle/.agents/skills/organizacao_refatoracao/SKILL.md (Code standards, SOLID, AAA tests)
- /home/anderson/Documents/projeto/RPG-battle/.agents/m2_explorer_grid/handoff.md (Detailed Tactical Grid specifications)
- /home/anderson/Documents/projeto/RPG-battle/.agents/m2_explorer_combat_rules/handoff.md (Detailed D&D 5e Combat Rules specifications)
- /home/anderson/Documents/projeto/RPG-battle/.agents/m2_explorer_conditions/handoff.md (Detailed 23 Status Conditions specifications)

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Exclusively Owned Files:
- godot_project/scripts/tactical/TacticalGrid.gd
- godot_project/scripts/combat/CombatRules.gd
- godot_project/scripts/combat/AttackResult.gd
- godot_project/scripts/combat/DamageResult.gd
- godot_project/scripts/combat/DeathSaveResult.gd
- godot_project/scripts/combat/StatusCondition.gd
- godot_project/scripts/combat/StatusManager.gd
- godot_project/test/unit/test_tactical_grid.gd
- godot_project/test/unit/test_combat_rules.gd
- godot_project/test/unit/test_status_conditions.gd

Your Objectives:
1. Implement `TacticalGrid.gd`:
   - 20x20 grid (Vector2i(0,0) to Vector2i(19,19)), cell validation, terrain types (Normal 1.0, Difficult 2.0, Wall, Rock, Forest, Barrel, Water, Ice, Fire, Poison pool).
   - Destructible cover (Forest, Rock, Barrel have 20 HP, convert to difficult terrain when destroyed).
   - AStar2D 8-way movement: orthogonal cost 1.0 * terrain_cost, diagonal cost sqrt(2) * terrain_cost.
   - Corner-cutting prevention on diagonal moves.
   - Dynamic unit occupancy (register, unregister, query, avoid occupied cells during pathfinding).
   - Bresenham Line of Sight (`has_line_of_sight(from_pos, to_pos, ignore_units)`).
   - Cover calculations: `get_raycast_cover` (0, 2, or 1000 AC), `get_adjacent_cover_bonus` (0, 3, or 5 AC), `get_total_cover_bonus`.

2. Implement `CombatRules.gd` and Result Resources:
   - Ability modifier: `floori((float(stat) - 10.0) / 2.0)`.
   - Proficiency bonus: `1 + ceili(float(level) / 4.0)`.
   - Advantage / Disadvantage cancellation rule (both true -> normal 1d20 roll).
   - Attack resolution: d20 + attack_mod vs AC + cover_bonus. Nat 20 auto-hit & crit, Nat 1 auto-miss. Auto-crit if target Paralyzed/Unconscious within 1 tile.
   - 14 damage types, immunities (0), resistances (0.5), vulnerabilities (2.0), min damage floor.
   - Death Saving Throws FSM: 1 (2 fails), 2-9 (1 fail), 10-19 (1 success), 20 (revives with 1 HP). 3 successes = Stable, 3 failures = Dead. Damage at 0 HP adds 1 failure (crit adds 2). Massive damage instant death.

3. Implement `StatusCondition.gd` and `StatusManager.gd`:
   - All 23 conditions: Paralyzed, Poisoned, Stunned, Blinded, Charmed, Deafened, Frightened, Grappled, Incapacitated, Invisible, Petrified, Prone, Restrained, Unconscious, Bleeding, Burning, Frozen, Confused, Cursed, Blessed, Hasted, Slowed, Doomed.
   - Apply, tick, DoT (Poison flat 2, Bleed 5% max hp, Burn 1d6 fire, Curse 3 flat), duration decrement, expiration, removal, and immunity checking.
   - Query methods for combat effects (cannot act, speed mult, advantage/disadvantage grants, auto-crit).
   - Integration with EventBus signals (`status_applied`, `status_removed`, `unit_damaged`).

4. Write Comprehensive Unit Tests following Strict AAA (Arrange-Act-Assert):
   - `test/unit/test_tactical_grid.gd`: Bounds, costs, AStar2D paths, corner-cutting, obstacles, occupancy, Bresenham LoS, cover bonuses, hazard triggers.
   - `test/unit/test_combat_rules.gd`: Ability modifiers (positive, zero, negative stats), proficiency levels, advantage/disadvantage/cancellation, crits, misses, cover AC, damage types, resistances, immunities, vulnerabilities, death save states, massive damage.
   - `test/unit/test_status_conditions.gd`: All 23 conditions, application, stacking/duration refresh, DoT ticks, expiry, combat query modifiers, auto-crit triggers.
   - Teardown safety: ensure zero ObjectDB leaks, zero warnings during positive test flows.

5. Verification:
   - Run `./godot_project/run_gut_tests.sh` and ensure 100% tests pass with exit code 0.
   - Run `./godot_project/bin/godot --headless --verbose --path ./godot_project -s addons/gut/gut_cmdln.gd -gexit` and verify 0 ObjectDB leaks at exit.
   - Write comprehensive handoff.md in your working directory and notify parent.

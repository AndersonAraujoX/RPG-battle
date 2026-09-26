# Task Assignment: Rules & Combat Engine Survey

## Objective
Survey the reference Python codebase for tactical combat rules, grid navigation, and combat resolution to establish a complete specification for migration to Godot Engine 4 (GDScript statically typed).

## Working Directory
`/home/anderson/Documents/projeto/RPG-battle/.agents/survey_explorer_rules`

## Authoritative Inputs
- `/home/anderson/Documents/projeto/RPG-battle/.agents/ORIGINAL_REQUEST.md` (MUST READ FIRST)
- `/home/anderson/Documents/projeto/RPG-battle/src/motor_combate.py`
- `/home/anderson/Documents/projeto/RPG-battle/src/tabuleiro.py`
- `/home/anderson/Documents/projeto/RPG-battle/src/juiz_combate.py`
- `/home/anderson/Documents/projeto/RPG-battle/tests/`

## Scope & Investigation Questions
1. **Grid & Navigation**:
   - 20x20 grid coordinates, boundaries, obstacle/wall representations.
   - Pathfinding algorithms, movement cost calculation, terrain types.
   - Elevation, Line of Sight (LoS), cover calculation (half cover +2 AC, three-quarters cover, total cover/blocked).
2. **Combat Math & D&D 5e Mechanics**:
   - d20 rolls, attack modifiers, Armor Class (AC) formulas.
   - Advantage / Disadvantage system and cancellation rules.
   - Critical Hits (natural 20, damage dice doubling or specific formula).
   - Death Saving Throws (mechanics, successes/failures, stabilization, natural 20 / natural 1 effects).
   - Status Conditions: Envenenado (Poisoned), Atordoado (Stunned), Foco (Focus), Sangramento (Bleeding), and any others present in code. Exact duration, tick timing, attribute impacts.
3. **Canonical Tests & Edge Cases**:
   - Analyze tests in `tests/` to see what exact edge cases, assertions, and invariants are tested.
   - Identify any hidden formulas, rounding rules, or random seed handling.

## Deliverables
- Write comprehensive analysis report to `/home/anderson/Documents/projeto/RPG-battle/.agents/survey_explorer_rules/analysis.md`.
- Write handoff to `/home/anderson/Documents/projeto/RPG-battle/.agents/survey_explorer_rules/handoff.md`.
- Send completion message to orchestrator with summary and paths.

## 2026-09-26T12:30:23Z
You are survey_explorer_rules.
Your working directory is /home/anderson/Documents/projeto/RPG-battle/.agents/survey_explorer_rules/
You MUST read /home/anderson/Documents/projeto/RPG-battle/.agents/ORIGINAL_REQUEST.md first.
Then read /home/anderson/Documents/projeto/RPG-battle/.agents/survey_explorer_rules/DISPATCH.md for your detailed task assignment.

Your mission is to explore and analyze the reference Python codebase for tactical combat rules, grid navigation, and combat resolution (D&D 5e mechanics, 20x20 grid, AStar2D, line of sight, cover, status conditions, damage formulas, and unit tests in tests/).
Write your complete technical findings to /home/anderson/Documents/projeto/RPG-battle/.agents/survey_explorer_rules/analysis.md and your handoff report to /home/anderson/Documents/projeto/RPG-battle/.agents/survey_explorer_rules/handoff.md.
When finished, send a message to orchestrator with a concise summary and report paths.

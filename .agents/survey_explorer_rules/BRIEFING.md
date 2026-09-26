# BRIEFING — 2026-09-26T12:30:23Z

## Mission
Survey reference Python codebase for tactical combat rules, grid navigation, and combat resolution to establish a complete specification for Godot 4 GDScript migration.

## 🔒 My Identity
- Archetype: explorer
- Roles: survey_explorer_rules
- Working directory: /home/anderson/Documents/projeto/RPG-battle/.agents/survey_explorer_rules/
- Original parent: 78d1f55b-e175-4f36-a462-ec295a59b44a
- Milestone: Survey & Specification Phase

## 🔒 Key Constraints
- Read-only investigation — do NOT implement
- Write only to .agents/survey_explorer_rules/
- Complete specification for tactical combat rules, grid navigation, and combat resolution (D&D 5e mechanics, 20x20 grid, AStar2D, line of sight, cover, status conditions, damage formulas, and unit tests) for Godot 4 migration

## Current Parent
- Conversation ID: 78d1f55b-e175-4f36-a462-ec295a59b44a
- Updated: 2026-09-26T12:30:23Z

## Investigation State
- **Explored paths**: `src/tabuleiro.py`, `src/motor_combate.py`, `src/juiz_combate.py`, `src/condicoes.py`, `src/personagens/personagem_base.py`, `src/personagens/status_efeito.py`, `src/utils.py`, `src/config.py`, `src/perks.py`, `dados/personagens.json`, and all 27 test files in `tests/`
- **Key findings**: Complete mathematical parity rules documented: 20x20 grid coordinates, 8-way A* pathfinding (difficult terrain cost=2), Chebyshev distance, Bresenham LoS and raycast cover (+2 soft, 1000 wall), adjacent tactical cover (+3 forest/barrel, +5 rock/wall), D&D 5e d20 advantage cancellation, critical hit dice doubling, death saves state machine (nat 20 revive, nat 1 double fail, 3 succ stabilized, 3 fail dead), 14 damage types, 23 status conditions, Cerco custom D6 mechanics (impacts // 2, balestra shots, elevation +/-1 D6, Brutamonte 3-circle HP reset per turn)
- **Unexplored areas**: None within the rules/combat survey scope. Ready for Godot 4 implementation.

## Key Decisions Made
- Mapped Godot 4 `AStar2D` with 400 point IDs (`y * 20 + x`), 8-way diagonal connections, weight scale 2.0 for difficult terrain.
- Formalized decoupled pure GDScript class architecture (`CombatRules.gd`, `TacticalGrid.gd`, `DeathSaves.gd`, `StatusEffectManager.gd`, `CercoCombatJudge.gd`) for headless GUT testing.
- Created canonical invariant verification matrix linking every Python test assertion in `tests/` to GUT equivalents.

## Artifact Index
- analysis.md — Full technical analysis and GDScript migration specification
- handoff.md — 5-component handoff report
- progress.md — Liveness heartbeat

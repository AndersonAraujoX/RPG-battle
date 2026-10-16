# BRIEFING — 2026-10-16T01:14:30Z

## Mission
Inspect and map existing Godot codebase architecture (run scripts, combat system, node resolution, hero persistence, data models) to provide architectural blueprint for Milestones M3-M8.

## 🔒 My Identity
- Archetype: explorer
- Roles: Codebase Architecture Explorer
- Working directory: /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_survey_1
- Original parent: aa7d5d2d-ef0f-482c-be6b-93c1793915c2
- Milestone: Survey Phase

## 🔒 Key Constraints
- Read-only investigation — do NOT implement
- Do NOT write or modify source code or tests
- Deliver comprehensive findings report in /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_survey_1/handoff.md
- Use send_message to communicate back to parent orchestrator

## Current Parent
- Conversation ID: aa7d5d2d-ef0f-482c-be6b-93c1793915c2
- Updated: 2026-10-16T01:08:00Z

## Investigation State
- **Explored paths**:
  - `CAMPANHA_ROGUELIKE.md`
  - `godot_project/scripts/run/` (`RunNode.gd`, `RunMap.gd`, `RunMapGenerator.gd`, `RunState.gd`, `RunNodeResolver.gd`, `RunSession.gd`, `RunMapScreen.gd`, `RunMapCanvas.gd`)
  - `godot_project/scenes/run/RunMapScreen.tscn`
  - `godot_project/scripts/autoload/` (`GameManager.gd`, `EventBus.gd`, `DataManager.gd`, `AudioManager.gd`)
  - `godot_project/scripts/main/` (`CercoGameController.gd`, `Menu.gd`, `GameOverScene.gd`)
  - `godot_project/scenes/main/` (`Main.tscn`, `Menu.tscn`, `GameOver.tscn`)
  - `godot_project/scripts/cerco/` (`FortressBoard.gd`, `IsectumCastes.gd`, `ThreatDeck.gd`, `CercoDeck.gd`, `WorkshopEconomy.gd`, `CercoSetup.gd`, `CercoCombatJudge.gd`, `CercoSyncRound.gd`)
  - `godot_project/scripts/tactical/TacticalGrid.gd`
  - `godot_project/scripts/combat/CombatRules.gd`
  - `godot_project/scripts/entities/Character.gd`
  - `godot_project/scenes/ui/` (`HUD.tscn`, `GameOverModal.tscn`, `OptionsMenu.tscn`)
  - `godot_project/test/unit/` (729 green tests verified)
  - `dados/fases/` (`fase_01` to `fase_12`) and `dados/personagens.json`
- **Key findings**:
  - Full GUT test suite (31 scripts, 729 tests) is 100% passing.
  - Run state machine (`RunState`) already tracks party, HP per hero, permadeath (`fallen_heroes`), gold, deck, relics, amber calculation, and acts.
  - `RunSession` is an existing static singleton holding `RunSession.current: RunState` without needing an extra Godot Autoload.
  - Combat resolution in `RunNodeResolver` is currently a placeholder rolling random damage.
  - Combat view and simulation exist in `Main.tscn` (`CercoGameController` + `HUD.tscn` + `FortressBoardView`), which currently spawns units from hardcoded lists or `ThreatDeck`.
  - Tactical grid (`TacticalGrid.gd`) implements full 20x20 cell layout, D&D 5e covers, AStar pathfinding, and line of sight.
  - `IsectumCastes.gd` has 24 canonical castes with stats and aliases, but `rei_isectum` (3x3 multi-phase boss) and `cigarra_ressonante` (mini-boss) need concrete implementation / boss orchestration for M5 and M6.
  - Reward modal ("Pick 1 of 3 cards"), Forge shop, and Relic system connected to `EventBus` are cleanly scoped for M3.
  - Meta-progression file `user://meta_save.json` and Ascension levels 1..10 are clearly mapped for M7 & M8.
- **Unexplored areas**: None within the exploration scope; all requested subsystems and milestone architectures have been mapped.

## Key Decisions Made
- Organized findings into structured 5-component handoff report (`handoff.md`).
- Documented exact integration hooks for M3 through M8, file paths, class names, and test patterns.

## Artifact Index
- /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_survey_1/handoff.md — Final comprehensive architectural survey report

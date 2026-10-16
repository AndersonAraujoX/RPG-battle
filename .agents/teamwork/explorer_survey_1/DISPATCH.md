# Dispatch — Survey Phase: Codebase Architecture Explorer

## Mission
Investigate `/home/anderson/Documents/projeto/RPG-battle/godot_project` and `/home/anderson/Documents/projeto/RPG-battle/dados/` to map existing architecture relevant to Milestones M3-M8.

## Scope Boundaries
- Read-only exploration and analysis of codebase.
- Do NOT write or modify source code or tests.
- Deliver report to `/home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_survey_1/handoff.md`.

## Deliverables
- Analyze `godot_project/scripts/run/` (`RunNode.gd`, `RunMap.gd`, `RunMapGenerator.gd`, `RunState.gd`, `RunNodeResolver.gd`, `RunSession.gd`, `RunMapScreen.gd`).
- Analyze how combat is handled in `Main.tscn`, `FortressBoard.tscn`, `scripts/cerco/`, `IsectumCastes.gd`, and event systems.
- Detail how nodes currently resolve and how combat node transitions should work.
- Map hero data structures, deck representation, inventory, relics, and HP persistence.
- Identify exact file locations where new components or integrations should be placed.


## 2026-10-16T01:07:38Z
From orchestrator (aa7d5d2d-ef0f-482c-be6b-93c1793915c2):
You are the Codebase Architecture Explorer for Survey Phase.
Your working directory is: /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_survey_1
You must read:
- /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/ORIGINAL_REQUEST.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_survey_1/DISPATCH.md
- Godot project files under /home/anderson/Documents/projeto/RPG-battle/godot_project/scripts/run/ and /home/anderson/Documents/projeto/RPG-battle/godot_project/scripts/cerco/

Your mission is to inspect and map:
- Existing run architecture (RunNode, RunMap, RunState, RunNodeResolver, RunSession, RunMapScreen, etc.)
- Existing combat system (Main.tscn, FortressBoard.tscn, cerco scripts, IsectumCastes, EventBus)
- How node resolution currently works and how combat nodes (COMBAT, ELITE, SIEGE, BOSS) should be connected
- How hero HP, deck, inventory, relics, and game states are structured and persisted
- Proposed architecture and code layout for Milestones M3 through M8

Deliver your comprehensive findings report in /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_survey_1/handoff.md.
When finished, send a message to the orchestrator summarizing completion.

# Dispatch — Milestone M3: Relics Architecture Explorer

## Mission
Design the Relics System for Milestone M3: `RelicData.gd` and `RelicManager.gd`.

## Input Files
- `/home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/ORIGINAL_REQUEST.md`
- `/home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/orchestrator_1/PROJECT.md`
- `/home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/spec_miner_survey_1/handoff.md`
- `/home/anderson/Documents/projeto/RPG-battle/godot_project/scripts/run/RunState.gd`
- `/home/anderson/Documents/projeto/RPG-battle/godot_project/scripts/autoload/EventBus.gd`

## Deliverables
- Design `godot_project/scripts/run/relics/RelicData.gd` (`RefCounted`) with virtual hook methods.
- Design `godot_project/scripts/run/relics/RelicManager.gd` (`RefCounted`) connecting `RunState.relics` to `EventBus` signals.
- Specify the catalog of 10 canonical relics (effects, bonuses, signal triggers, gold cost).
- Design the GUT test suite `godot_project/test/unit/test_relic_system.gd` (Arrange-Act-Assert, zero leaks, headless safety).
- Write report to `/home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m3_1/handoff.md`.

## 2026-10-16T01:16:55Z
From: aa7d5d2d-ef0f-482c-be6b-93c1793915c2
Priority: MESSAGE_PRIORITY_HIGH
Content:
You are the M3 Relics Explorer.
Your working directory is: /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m3_1
You must read:
- /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/ORIGINAL_REQUEST.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/orchestrator_1/PROJECT.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/spec_miner_survey_1/handoff.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m3_1/DISPATCH.md

Design the complete Relics subsystem:
- godot_project/scripts/run/relics/RelicData.gd
- godot_project/scripts/run/relics/RelicManager.gd
- 10 canonical relics catalog with EventBus hooks
- GUT test suite design for godot_project/test/unit/test_relic_system.gd

Deliver your report to /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m3_1/handoff.md.
When done, send a message to orchestrator.

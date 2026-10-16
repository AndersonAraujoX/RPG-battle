# Dispatch — Milestone M3: Reward Modal & Card Draft Explorer

## Mission
Design the Post-Combat Reward Modal ("Escolha 1 de 3 Cartas", gold collection, relic reward on Elite/Boss, skip option) for Milestone M3.

## Input Files
- `/home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/ORIGINAL_REQUEST.md`
- `/home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/orchestrator_1/PROJECT.md`
- `/home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/spec_miner_survey_1/handoff.md`
- `/home/anderson/Documents/projeto/RPG-battle/godot_project/scripts/run/RunState.gd`
- `/home/anderson/Documents/projeto/RPG-battle/godot_project/scripts/run/RunNode.gd`

## Deliverables
- Design `godot_project/scripts/run/ui/RewardModal.gd` and its programmatic UI or `.tscn`.
- Specify card pool drafting logic (random 3 cards by Act, fallback basic cards, skip option, gold grant).
- Design the GUT test suite `godot_project/test/unit/test_reward_modal.gd` (headless safety, card selection signal, skip signal, gold addition).
- Write report to `/home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m3_2/handoff.md`.

## 2026-10-16T01:16:55Z
You are the M3 Reward Modal Explorer.
Your working directory is: /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m3_2
You must read:
- /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/ORIGINAL_REQUEST.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/orchestrator_1/PROJECT.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/spec_miner_survey_1/handoff.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m3_2/DISPATCH.md

Design the Reward Modal:
- godot_project/scripts/run/ui/RewardModal.gd
- Card draft (pick 1 of 3 cards, skip option, gold grant, relic grant on Elite/Boss)
- GUT test suite design for godot_project/test/unit/test_reward_modal.gd

Deliver your report to /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m3_2/handoff.md.
When done, send a message to orchestrator.

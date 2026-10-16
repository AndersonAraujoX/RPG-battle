# Dispatch — Survey Phase: Spec Miner

## Mission
Analyze `/home/anderson/Documents/projeto/RPG-battle/CAMPANHA_ROGUELIKE.md` and `/home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/ORIGINAL_REQUEST.md` to extract the complete technical specification for Milestones M3 through M8.

## Scope Boundaries
- Read-only exploration and analysis of specifications.
- Do NOT write source code or tests.
- Deliver report to `/home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/spec_miner_survey_1/handoff.md`.

## Deliverables
Detailed breakdown for:
- M3: Rewards ("Escolha 1 de 3 Cartas", skip, gold), Relics system (EventBus triggers, types, effects), Forge (shop buying/removing cards, buying relics).
- M4: Node combat integration (COMBAT, ELITE, SIEGE, BOSS), transition to tactical board, persistent HP across nodes, permadeath rules.
- M5: Act II (Túneis Vivos) - torch light/darkness system, chitin cocoons/eggs hatching logic, cicada resonante mini-boss, queen of the swarm boss.
- M6: Act III - 3 Hive Hearts (phases 09, 10, 11) mechanics & permanent debuffs on King Isectum; Phase 12 Final Boss King Isectum (3x3 entity, 3 phases: Trono de Âmbar, Muralha Viva, Coroa Quebrada).
- M7 & M8: Meta-progression (`user://meta_save.json`), Royal Amber accumulation, unlockable heroes & runic cards, Ascension levels 1-10, Victory/Defeat screen statistics.


## 2026-10-16T01:07:38Z
You are the Spec Miner for Survey Phase.
Your working directory is: /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/spec_miner_survey_1
You must read:
- /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/ORIGINAL_REQUEST.md
- /home/anderson/Documents/projeto/RPG-battle/CAMPANHA_ROGUELIKE.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/spec_miner_survey_1/DISPATCH.md

Your mission is to extract the complete feature inventory, specifications, formulas, data schemas, signals, and edge cases for Milestones M3 to M8:
- M3: Post-combat rewards, Relics system, Forge / Merchant
- M4: Node combat integration (COMBAT, ELITE, SIEGE, BOSS), persistent HP, permadeath
- M5: Act II (Túneis Vivos) - torch light/darkness, cocoons/eggs, cicada resonante, queen of the swarm
- M6: Act III - 3 Hive Hearts (fase_09, 10, 11) & King Isectum final boss (3x3, 3 phases)
- M7 & M8: Meta-progression (user://meta_save.json), Royal Amber, Hero & runic card unlock, Ascension 1-10, Victory/Defeat screens with stats

Deliver your comprehensive findings report in /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/spec_miner_survey_1/handoff.md.
When finished, send a message to the orchestrator summarizing completion.

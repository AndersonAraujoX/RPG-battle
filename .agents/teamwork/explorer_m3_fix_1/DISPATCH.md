# Dispatch — Milestone M3 Remediation Explorer 1 (Relic Catalog & ID Prefix Normalization)

## Mission
Analyze the defects reported by Reviewers and Challengers regarding Relic IDs and design a unified fix strategy:
1. `RewardModal.gd` defines `ELITE_RELICS` and `BOSS_RELICS` containing IDs not registered in `RelicManager.gd` (`pedra_afiar`, `armadura_carapaca`, etc.).
   Map `ELITE_RELICS` and `BOSS_RELICS` to use ONLY the 10 canonical relics from `RelicManager.gd`.
2. Prefix normalization: Ensure consistent IDs (with or without `reliquia_` prefix, using an alias/normalization function `normalize_id()` in `RelicManager.gd`) across `RewardModal`, `ForgeScreen`, `RunState`, and tests.
3. Fix typo `reliquia_coroa_de_quitina` vs `coroa_quitina`.

## Deliverables
Detailed code-level fix recommendations in:
`/home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m3_fix_1/handoff.md`

## 2026-10-16T01:53:11Z
From: aa7d5d2d-ef0f-482c-be6b-93c1793915c2
You are Remediation Explorer 1 for Milestone M3.
Your working directory is: /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m3_fix_1
You must read:
- /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/ORIGINAL_REQUEST.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/orchestrator_1/PROJECT.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m3_fix_1/DISPATCH.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/reviewer_m3_1/handoff.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/reviewer_m3_2/handoff.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/challenger_m3_1/handoff.md

Investigate Relic ID normalization and catalog synchronization between RewardModal, ForgeScreen, and RelicManager.
Recommend concrete GDScript diffs/replacements for RewardModal.gd, ForgeScreen.gd, and RelicManager.gd.
Deliver report to /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m3_fix_1/handoff.md.
When finished, notify orchestrator via send_message.

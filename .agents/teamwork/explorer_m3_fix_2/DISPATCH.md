# Dispatch — Milestone M3 Remediation Explorer 2 (Relic Logic & Signal Integrity)

## Mission
Analyze the defects reported regarding Relic behavior and design a concrete fix strategy:
1. `RelicBolsaDoMercador.on_combat_victory()` currently increments `rewards["gold"] += 10` AND calls `p_run_state.add_gold(10)`. Downstream, `RewardModal` also adds `rewards["gold"]`, resulting in double reward (+20g).
   Determine whether `on_combat_victory()` should only mutate `rewards["gold"]` or only call `add_gold()`.
2. `RelicFrascoFeromonio.gd`: Ensure it only cancels negative conditions (`envenenado`, `atordoado`, `amedrontado`, `imobilizado`) applied to ALLIED heroes, and does not clear conditions on enemies.
3. `RelicManager.unregister_relic()`: Ensure it properly disconnects signals and frees relic data instances when relics are removed from `RunState.relics`.

## Deliverables
Detailed code-level fix recommendations in:
`/home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m3_fix_2/handoff.md`

## 2026-10-16T01:53:11Z
You are Remediation Explorer 2 for Milestone M3.
Your working directory is: /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m3_fix_2
You must read:
- /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/ORIGINAL_REQUEST.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/orchestrator_1/PROJECT.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m3_fix_2/DISPATCH.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/reviewer_m3_1/handoff.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/reviewer_m3_2/handoff.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/challenger_m3_1/handoff.md

Investigate Relic logic: RelicBolsaDoMercador double gold reward, RelicFrascoFeromonio friendly unit check, and RelicManager.unregister_relic signal unbinding.
Recommend concrete GDScript diffs/replacements for RelicData.gd and RelicManager.gd.
Deliver report to /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m3_fix_2/handoff.md.
When finished, notify orchestrator via send_message.

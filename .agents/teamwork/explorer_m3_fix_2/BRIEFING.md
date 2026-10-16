# BRIEFING — 2026-10-16T02:04:00Z

## Mission
Investigate Relic defects (RelicBolsaDoMercador double gold reward, RelicFrascoFeromonio friendly unit check, and RelicManager.unregister_relic signal unbinding) and produce concrete GDScript diffs/replacements for RelicData.gd and RelicManager.gd.

## 🔒 My Identity
- Archetype: explorer
- Roles: investigation, synthesis
- Working directory: /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m3_fix_2
- Original parent: aa7d5d2d-ef0f-482c-be6b-93c1793915c2
- Milestone: M3 Remediation

## 🔒 Key Constraints
- Read-only investigation — do NOT implement directly in source code
- Deliver report to /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m3_fix_2/handoff.md
- Recommend concrete GDScript diffs/replacements for RelicData.gd and RelicManager.gd
- Provide complete verification method and test plan

## Current Parent
- Conversation ID: aa7d5d2d-ef0f-482c-be6b-93c1793915c2
- Updated: not yet

## Investigation State
- **Explored paths**:
  - `godot_project/scripts/run/relics/RelicData.gd`
  - `godot_project/scripts/run/relics/RelicManager.gd`
  - `godot_project/scripts/run/ui/RewardModal.gd`
  - `godot_project/scripts/run/RunState.gd`
  - `godot_project/scripts/combat/StatusManager.gd`
  - `godot_project/test/unit/test_relic_system.gd`
  - `godot_project/test/unit/test_relic_stress_adversarial.gd`
  - Reviewer 1 & 2 handoffs, Challenger 1 handoff
- **Key findings**:
  1. `RelicBolsaDoMercador`: Calling `p_run_state.add_gold(10)` inside `on_combat_victory` mutates persistent state during modifier calculation. When downstream `RewardModal` collects `offered_gold`, gold is awarded twice (+35 total instead of +25). Fix: eliminate `p_run_state.add_gold(10)` from calculation.
  2. `RelicFrascoFeromonio`: `on_status_applied` ignored `_unit_id` and `_run_state`, cancelling debuffs applied to enemies and exhausting charge. Fix: assert `p_run_state != null and p_run_state.heroes.has(unit_id)`, and support canonical PT-BR/EN status names (`envenenado`, `atordoado`, etc.).
  3. `RelicManager.unregister_relic`: Missed prefix normalization, did not deactivate instances (`is_active = false`), did not prune orphan relics on `sync_from_run_state()`, and bypassed `run_state.remove_relic()`. Fix: two-way sync, canonical ID keying, and explicit instance deactivation.
- **Unexplored areas**: None within the M3 relic remediation scope.

## Key Decisions Made
- `on_combat_victory()` must be a pure functional calculation mutating only the dictionary (`rewards["gold"] = int(rewards.get("gold", 0)) + 10`).
- Generated complete replacement files `proposed_RelicData.gd`, `proposed_RelicManager.gd`, unified patch `relic_remediation.patch`, and test suite additions `proposed_test_additions.gd`.

## Artifact Index
- /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m3_fix_2/DISPATCH.md — Dispatch instructions
- /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m3_fix_2/BRIEFING.md — Working memory index
- /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m3_fix_2/progress.md — Liveness heartbeat
- /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m3_fix_2/proposed_RelicData.gd — Proposed clean replacement for RelicData.gd
- /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m3_fix_2/proposed_RelicManager.gd — Proposed clean replacement for RelicManager.gd
- /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m3_fix_2/relic_remediation.patch — Unified diff patch for easy application
- /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m3_fix_2/proposed_test_additions.gd — Unit tests covering happy path, edge cases, and adversarial stress
- /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m3_fix_2/handoff.md — Final 5-component handoff report

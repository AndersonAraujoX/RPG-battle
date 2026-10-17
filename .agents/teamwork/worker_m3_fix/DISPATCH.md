# Dispatch — Milestone M3 Remediation Worker

## Mission
Apply the unified fixes designed by the 3 Remediation Explorers to resolve all issues identified in Milestone M3 gate evaluation.

## Reference Materials to Ingest
- `/home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/ORIGINAL_REQUEST.md`
- `/home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/orchestrator_1/PROJECT.md`
- `/home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m3_fix_1/handoff.md` (relic_id_normalization.patch)
- `/home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m3_fix_2/handoff.md` (relic_remediation.patch, proposed_RelicData.gd, proposed_RelicManager.gd)
- `/home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m3_fix_3/handoff.md` (runstate_and_forgescreen_remediation.patch)

## Mandatory Tasks
1. Apply Relic ID normalization across `RelicManager.gd`, `RewardModal.gd`, `ForgeScreen.gd`, and `RunState.gd`.
2. Apply Relic logic fixes: `RelicBolsaDoMercador` single gold reward, `RelicFrascoFeromonio` friendly target check, and `RelicManager.unregister_relic` signal unbinding.
3. Declare `card_purges_count: int = 0` in `RunState.gd`, include in `to_dict()` and `from_dict()`.
4. Fix typed array assignment in `ForgeScreen.gd:176`.
5. Update and run all GUT tests:
   `bash godot_project/run_gut_tests.sh`
   Verify 100% of all tests pass (800+ assertions, all suites, exit code 0).

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## Deliverable
Deliver your report to:
`/home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/worker_m3_fix/handoff.md`


## 2026-10-16T02:05:05Z
You are the M3 Remediation Worker.
Your working directory is: /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/worker_m3_fix

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

You must read before starting:
- /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/ORIGINAL_REQUEST.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/orchestrator_1/PROJECT.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/worker_m3_fix/DISPATCH.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m3_fix_1/handoff.md and patch relic_id_normalization.patch
- /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m3_fix_2/handoff.md and patch relic_remediation.patch
- /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m3_fix_3/handoff.md and patch runstate_and_forgescreen_remediation.patch

Tasks:
1. Apply the Relic ID normalization and catalog synchronization fixes across `RelicManager.gd`, `RewardModal.gd`, and `ForgeScreen.gd`.
2. Apply the Relic logic fixes in `RelicData.gd` (`RelicBolsaDoMercador` single gold reward, `RelicFrascoFeromonio` friendly target condition) and `RelicManager.gd` (`unregister_relic` signal unbinding).
3. In `RunState.gd`, declare `var card_purges_count: int = 0` and serialize it in `to_dict()` and `from_dict()`.
4. In `ForgeScreen.gd:176`, fix the typed array assignment `var empty_relics: Array[String] = []`.
5. Update unit test assertions in `test_reward_modal.gd`, `test_forge_system.gd`, and `test_relic_system.gd` to match the normalized catalog and rules.
6. Run `bash godot_project/run_gut_tests.sh` from `/home/anderson/Documents/projeto/RPG-battle` and verify 100% of all tests pass with exit code 0.

Deliver your detailed handoff report to:
`/home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/worker_m3_fix/handoff.md`
When complete, notify orchestrator via send_message.

# Dispatch — Milestone M3 Worker

## Mission
Implement Milestone M3: Post-Combat Rewards, Forge, and Relics System, and write the complete GUT test suites.

## Exclusive File Ownership
The Worker exclusively owns and creates:
- `godot_project/scripts/run/relics/RelicData.gd`
- `godot_project/scripts/run/relics/RelicManager.gd`
- `godot_project/scripts/run/ui/RewardModal.gd`
- `godot_project/scripts/run/ui/RewardModal.tscn` (optional if programmatic)
- `godot_project/scripts/run/ui/ForgeScreen.gd`
- `godot_project/scripts/run/ui/ForgeScreen.tscn` (optional if programmatic)
- `godot_project/test/unit/test_relic_system.gd`
- `godot_project/test/unit/test_reward_modal.gd`
- `godot_project/test/unit/test_forge_system.gd`

## Reference Designs & Handoffs to Read First
- `/home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/ORIGINAL_REQUEST.md`
- `/home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/orchestrator_1/PROJECT.md`
- `/home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m3_1/handoff.md` (Relics Architecture & Catalog)
- `/home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m3_2/handoff.md` (Reward Modal & Card Draft)
- `/home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m3_3/handoff.md` (Forge Screen & Shop Economy)

## Verification Requirement
Run `bash godot_project/run_gut_tests.sh` from the project root `/home/anderson/Documents/projeto/RPG-battle`.
Ensure 100% of all tests pass (the baseline 729 + all new M3 tests) with 0 failures, 0 errors, and exit code 0.
Document exact test counts and command output in your handoff report.

## Deliverable
Deliver your handoff report to:
`/home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/worker_m3_1/handoff.md`
## 2026-10-16T01:26:59Z
[Message] sender=aa7d5d2d-ef0f-482c-be6b-93c1793915c2 priority=MESSAGE_PRIORITY_HIGH
Implement Milestone M3:
1. Create `godot_project/scripts/run/relics/RelicData.gd` and `godot_project/scripts/run/relics/RelicManager.gd` with the 10 canonical relics and EventBus signal hooks.
2. Create `godot_project/scripts/run/ui/RewardModal.gd` (and scene if needed) supporting 1-of-3 card draft by Act, skip option, gold grant, guaranteed relic on Elite/Boss, and headless safety.
3. Create `godot_project/scripts/run/ui/ForgeScreen.gd` (and scene if needed) supporting card purchases, relic purchases, progressive deck purging (50g + 25g/purge), 5-card minimum safe deck limit, and headless safety.
4. Implement the GUT unit test suites:
   - `godot_project/test/unit/test_relic_system.gd`
   - `godot_project/test/unit/test_reward_modal.gd`
   - `godot_project/test/unit/test_forge_system.gd`
   Ensure strict AAA pattern, headless safety bare-node checks, deterministic seeds, and zero leaks.
5. Execute the test runner: `bash godot_project/run_gut_tests.sh` from `/home/anderson/Documents/projeto/RPG-battle` and verify 100% of all tests pass (the baseline 729 + all new M3 tests) with exit code 0.
Deliver handoff to `.agents/teamwork/worker_m3_1/handoff.md`.

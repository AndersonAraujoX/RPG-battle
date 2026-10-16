# Implementation Plan — Tactical Roguelike Campaign (M3 - M8)

## Overview
Implement and verify Milestones M3 to M8 in Godot 4 with strict unit test coverage (GUT 4) and 100% test passing guarantee (`bash godot_project/run_gut_tests.sh`).

## Execution Pipeline

### Phase 0: Survey & Mapping [COMPLETED]
- [x] Survey specification document `CAMPANHA_ROGUELIKE.md` & `ORIGINAL_REQUEST.md` (`spec_miner_survey_1`)
- [x] Map existing codebase architecture, nodes, run state & combat systems (`explorer_survey_1`)
- [x] Verify GUT test suite baseline (729/729 tests passing, exit code 0) & guidelines (`explorer_survey_2`)
- [x] Synthesize findings into `PROJECT.md` Feature Inventory (30 features, 20 edge cases)

### Milestone M3: Post-Combat Rewards, Forge & Relics System [IN_PROGRESS]
1. Explorer: Investigate detailed file design for `RelicData`, `RelicManager`, `RewardModal`, `ForgeScreen`.
2. Worker: Implement M3 components + write GUT test suites:
   - `godot_project/scripts/run/relics/RelicData.gd`
   - `godot_project/scripts/run/relics/RelicManager.gd`
   - `godot_project/scripts/run/ui/RewardModal.gd`
   - `godot_project/scripts/run/ui/ForgeScreen.gd`
   - `godot_project/test/unit/test_relic_system.gd`
   - `godot_project/test/unit/test_reward_modal.gd`
   - `godot_project/test/unit/test_forge_system.gd`
3. Reviewer & Challenger: Review code quality, run all GUT tests, verify AAA and zero leaks.
4. Forensic Auditor: Verify authenticity and integrity.
5. Gate Evaluation -> Pass to M4.

### Milestone M4: Tactical Combat Integration & Permadeath [PLANNED]
1. Explorer: Design `RunCombatBridge`, `CombatEncounterGenerator`, and integration hooks in `CercoGameController` and `RunMapScreen`.
2. Worker: Implement M4 components + write GUT test suites:
   - `godot_project/scripts/run/combat/RunCombatBridge.gd`
   - `godot_project/scripts/run/combat/CombatEncounterGenerator.gd`
   - Connect `RunMapScreen` node transitions to `Main.tscn`
   - Bidirectional HP persistence and Permadeath checks in `RunState`
   - `godot_project/test/unit/test_run_combat_integration.gd`
   - `godot_project/test/unit/test_combat_encounter_generator.gd`
3. Reviewer & Challenger -> Auditor -> Gate check -> Pass to M5.

### Milestone M5: Act II Mechanics & Content (Living Tunnels) [PLANNED]
1. Explorer -> Worker -> Reviewer -> Challenger -> Auditor -> Gate check.
   - `godot_project/scripts/tactical/TorchLighting.gd`
   - `godot_project/scripts/entities/ChitinCocoon.gd`
   - `godot_project/scripts/entities/bosses/CigarraRessonante.gd`
   - `godot_project/scripts/entities/bosses/RainhaDoEnxame.gd`
   - `godot_project/test/unit/test_act2_mechanics.gd`
   - `godot_project/test/unit/test_boss_swarm_queen.gd`

### Milestone M6: Act III Content & King Isectum Final Boss (3x3, 3 Phases) [PLANNED]
1. Explorer -> Worker -> Reviewer -> Challenger -> Auditor -> Gate check.
   - `godot_project/scripts/run/HiveHeartsTracker.gd`
   - `godot_project/scripts/entities/bosses/ReiIsectumBoss.gd`
   - `godot_project/test/unit/test_hive_hearts.gd`
   - `godot_project/test/unit/test_king_isectum_boss.gd`

### Milestone M7 & M8: Permanent Meta-Progression & Ascension 1-10 [PLANNED]
1. Explorer -> Worker -> Reviewer -> Challenger -> Auditor -> Gate check.
   - `godot_project/scripts/run/meta/MetaSaveManager.gd` (`user://meta_save.json`)
   - `godot_project/scripts/run/ui/BarracksScreen.gd`
   - `godot_project/scripts/run/meta/AscensionModifiers.gd`
   - `godot_project/scripts/run/ui/RunSummaryModal.gd`
   - `godot_project/test/unit/test_meta_progression.gd`
   - `godot_project/test/unit/test_ascension_system.gd`
   - `godot_project/test/unit/test_run_summary_screen.gd`

### Final E2E Verification & Reporting [PLANNED]
- Run full GUT test suite via `bash godot_project/run_gut_tests.sh`.
- Confirm 100% test pass with 0 failures, 0 errors.
- Final handoff report to Sentinel / caller.

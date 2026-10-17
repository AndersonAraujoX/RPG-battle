# Forensic Audit Report — Milestone M4: Tactical Combat Integration, Persistent Hero HP, and Permadeath

**Auditor**: Forensic Auditor (`auditor_m4_1`)  
**Date**: 2026-10-16  
**Target**: Milestone M4 Deliverables  
**Integrity Mode**: Demo (per `ORIGINAL_REQUEST.md`)  
**Verdict**: **CLEAN**

---

## 1. Forensic Audit Checklist & Results

| Check | Requirement | Result | Evidence / Details |
|---|---|:---:|---|
| **Check 1** | No fake/facade implementations or hardcoded test returns | **PASS** | Grep analysis for `TODO`, `FIXME`, `HACK`, `STUB`, `DUMMY`, `MOCK` returned 0 matches in `godot_project/scripts/run/combat/`. No branch detects test runner to return artificial success payloads. |
| **Check 2** | `CombatEncounterGenerator.gd` genuinely maps castes dynamically | **PASS** | `resolve_caste_id()` maps alias names to canonical constants in `IsectumCastes`. Stats (HP, AC, speed, attack dice, attack range, trait) are retrieved directly from `IsectumCastes.get_caste(cid)`. Squads are generated via deterministic seed hashing (`compute_encounter_seed`) with anti-collision spatial placement. |
| **Check 3** | `RunCombatBridge.gd` genuinely persists HP and enforces permadeath | **PASS** | `setup_combat()` strictly inspects `run_state.get_living_heroes()`, omitting fallen heroes from `party`. `sync_combat_result()` applies differential damage/healing, clamps between `0` and `max_hp`, moves zero-HP heroes into `fallen_heroes`, and explicitly zeroes fallen hero HP even if anomalous positive HP is reported (anti-resurrection safeguard in lines 140-142). |
| **Check 4** | GUT test suites have strict, meaningful assertions | **PASS** | `test_combat_encounter_generator.gd` (13 tests) and `test_run_combat_integration.gd` (15 tests) utilize AAA structure, testing boundaries, anti-collision, seed determinism, overheal clamping, defeat transitions, and standalone isolation. No tautological or trivially passing assertions. |
| **Check 5** | Independent execution of GUT test suite (`bash godot_project/run_gut_tests.sh`) | **PASS** | 38 test suites executed, 836 tests run, 836 passed, 0 failures, 8343 assertions passed, exit code 0. |
| **Check 6** | Pre-populated artifact detection | **PASS** | No pre-existing test logs, result files, or fabricated verification artifacts were committed to the repository. |
| **Check 7** | Zero-regression standalone compatibility | **PASS** | `CercoGameController._should_setup_from_run_session()` cleanly isolates active run sessions from standalone matches, preserving 100% passing status on all legacy test suites. |

---

## 2. Five-Component Handoff Report

### 1. Observation
1. **Source Inspection — `CombatEncounterGenerator.gd`**:
   - `resolve_caste_id()` accurately maps aliases (`larva_carniceira` -> `IsectumCastes.ID_LARVA_NECROTICA`, `viuva_canibal` -> `IsectumCastes.ID_TECE_TEIA`, `batedor` -> `IsectumCastes.ID_ZANGAO_INVASOR`, etc.).
   - Unit dictionaries are populated from `IsectumCastes.get_caste(cid)`:
     ```gdscript
     var cid: String = resolve_caste_id(raw_id)
     var caste: IsectumCasteData = IsectumCastes.get_caste(cid)
     var base_hp: int = caste.hp if caste != null else 4
     var base_ac: int = caste.ac if caste != null else 12
     ```
   - Seed computation uses dynamic prime multipliers:
     ```gdscript
     (base_seed + (act * p1) + (floor_index * p2) + (node_id * p3)) & 0x7FFFFFFF
     ```
2. **Source Inspection — `RunCombatBridge.gd`**:
   - Permadeath exclusion during setup:
     ```gdscript
     var living: Array[String] = run_state.get_living_heroes()
     for i in range(living.size()):
         var hid: String = living[i]
         var cur_hp: int = int(run_state.hero_hp.get(hid, 1))
         ...
         party_data.append(h_info)
     ```
   - Anti-resurrection guard during result sync:
     ```gdscript
     for hid in run_state.heroes:
         if run_state.fallen_heroes.has(hid):
             run_state.hero_hp[hid] = 0
             continue
     ```
3. **Source Inspection — `CercoGameController.gd`**:
   - Decoupled run-mode hook:
     ```gdscript
     if _should_setup_from_run_session():
         _setup_from_run_session()
     else:
         _setup_standalone_cerco()
     ```
   - Spawns only heroes present in `encounter_config["party"]` with exact persisted HP.
   - On victory, invokes `RunCombatBridge.sync_combat_result()` and mounts `RewardModal` for card drafting and loot.
4. **Empirical Test Execution**:
   - Command: `bash godot_project/run_gut_tests.sh`
   - Output summary:
     ```text
     ============================================================
                         TEST SUMMARY                            
     ============================================================
     Test Scripts Executed:   38
     Tests Run:               836
     Tests Passed:            836
     Tests Failed:            0
     Total Assertions:        8343
     Assertions Passed:       8343
     Assertions Failed:       0
     ============================================================
     ==> All GUT tests passed successfully! (Exit code: 0)
     ```

### 2. Logic Chain
1. The user's `ORIGINAL_REQUEST.md` (Integrity mode: demo) specifies three core requirements for M4:
   - Connect `COMBAT`, `ELITE`, `SIEGE`, `BOSS` nodes to tactical arena `Main.tscn` / `FortressBoard.tscn` with appropriate enemy compositions.
   - Continuous HP persistence between combats.
   - Permadeath: fallen heroes remain fallen and do not enter subsequent battles.
2. The code in `CombatEncounterGenerator.gd` and `RunCombatBridge.gd` directly addresses these requirements with genuine procedural generation and mediator methods.
3. Verification of `test_combat_encounter_generator.gd` and `test_run_combat_integration.gd` confirms that all assertions verify real functional invariants (caste catalog retrieval, HP delta application, permadeath enforcement, scene safety).
4. Running the full test suite in headless mode independently confirmed 836/836 passing tests with zero runtime failures or errors.
5. No prohibited shortcuts, facades, stubs, or hardcoded return values were detected.

### 3. Caveats
- Headless test execution requires bypassing `SceneTree.change_scene_to_file()` to avoid terminating the GUT test runner; this is safely handled in `RunMapScreen._is_in_gut_runner()`.
- No caveats regarding code integrity, correctness, or test validity.

### 4. Conclusion
The implementation of Milestone M4 meets all ground-truth requirements from `ORIGINAL_REQUEST.md` and `PROJECT.md`. There are no integrity violations, facade implementations, or hardcoded test returns. The verdict is **CLEAN**. Milestone M4 is APPROVED.

### 5. Verification Method
To independently reproduce this verification:
```bash
cd /home/anderson/Documents/projeto/RPG-battle
bash godot_project/run_gut_tests.sh
```
Expected: 38 test scripts, 836 tests passed, 0 failed, exit code 0.

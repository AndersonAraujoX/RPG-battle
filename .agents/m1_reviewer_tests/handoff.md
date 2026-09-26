# Handoff Report: Milestone 1 Tests & Harness Review

**Reviewer**: `m1_reviewer_tests`  
**Milestone**: M1 (Foundation & Core Infrastructure)  
**Date**: 2026-09-26  
**Type**: Hard Handoff (Review Complete)  
**Verdict**: **REQUEST_CHANGES**

---

## 1. Observation

1. **Test Execution Command & Output**:
   Ran `./godot_project/run_gut_tests.sh` from `/home/anderson/Documents/projeto/RPG-battle`.
   Command output:
   ```text
   Godot Engine v4.7.2.stable.official.ed1daf0bf - https://godotengine.org

   ============================================================
                       GUT TEST RUNNER                         
   ============================================================
   Scanning directory: res://test/unit/
   Found 1 test script(s).

   --- Running Suite: res://test/unit/test_autoloads.gd ---
     [PASS] test_game_manager_initial_state_is_menu
     [PASS] test_game_manager_change_state_updates_current_and_previous
     [PASS] test_game_manager_emits_state_changed_signal
     [PASS] test_game_manager_all_valid_transitions
   WARNING: [GameManager] Invalid state transition: COMBATE_TATICO -> CERCO_ISECTUM
        at: push_warning (core/variant/variant_utility.cpp:1033)
        GDScript backtrace (most recent call first):
            [0] change_state (res://scripts/autoload/GameManager.gd:68)
            [1] test_game_manager_is_in_combat_flag (res://test/unit/test_autoloads.gd:110)
     [PASS] test_game_manager_is_in_combat_flag
     [PASS] test_game_manager_get_state_name_mapping
     [PASS] test_game_manager_transition_to_same_state_is_noop
   WARNING: [GameManager] Invalid state transition: MENU -> FIM_DE_JOGO
        at: push_warning (core/variant/variant_utility.cpp:1033)
        GDScript backtrace (most recent call first):
            [0] change_state (res://scripts/autoload/GameManager.gd:68)
            [1] test_game_manager_reset_state_restores_menu (res://test/unit/test_autoloads.gd:136)
     [PASS] test_game_manager_reset_state_restores_menu
   WARNING: [GameManager] Invalid state transition: COMBATE_TATICO -> CERCO_ISECTUM
        at: push_warning (core/variant/variant_utility.cpp:1033)
        GDScript backtrace (most recent call first):
            [0] change_state (res://scripts/autoload/GameManager.gd:68)
            [1] test_game_manager_rapid_sequential_transitions (res://test/unit/test_autoloads.gd:154)
   WARNING: [GameManager] Invalid state transition: COMBATE_TATICO -> MULTIPLAYER_LOBBY
        at: push_warning (core/variant/variant_utility.cpp:1033)
        GDScript backtrace (most recent call first):
            [0] change_state (res://scripts/autoload/GameManager.gd:68)
            [1] test_game_manager_rapid_sequential_transitions (res://test/unit/test_autoloads.gd:154)
     [PASS] test_game_manager_rapid_sequential_transitions
   ...
   ============================================================
                       TEST SUMMARY                            
   ============================================================
   Test Scripts Executed:   1
   Tests Run:               44
   Tests Passed:            44
   Tests Failed:            0
   Total Assertions:        97
   Assertions Passed:       97
   Assertions Failed:       0
   ============================================================

   WARNING: 74 ObjectDB instances were leaked at exit (run with `--verbose` for details).
      at: cleanup (core/object/object.cpp:2536)
   ERROR: 12 resources still in use at exit (run with --verbose for details).
      at: clear (core/io/resource.cpp:822)
   ==> All GUT tests passed successfully! (Exit code: 0)
   ```

2. **Source Code Inspection - False Positive State Transitions**:
   - In `godot_project/scripts/autoload/GameManager.gd`, lines 25–31 define:
     ```gdscript
     const VALID_TRANSITIONS: Dictionary = {
         GameState.MENU: [GameState.COMBATE_TATICO, GameState.CERCO_ISECTUM, GameState.MULTIPLAYER_LOBBY],
         GameState.COMBATE_TATICO: [GameState.FIM_DE_JOGO, GameState.MENU],
         GameState.CERCO_ISECTUM: [GameState.FIM_DE_JOGO, GameState.MENU],
         GameState.MULTIPLAYER_LOBBY: [GameState.CERCO_ISECTUM, GameState.COMBATE_TATICO, GameState.MENU],
         GameState.FIM_DE_JOGO: [GameState.MENU, GameState.COMBATE_TATICO, GameState.CERCO_ISECTUM]
     }
     ```
   - In `godot_project/test/unit/test_autoloads.gd`, line 110:
     `_gm.change_state(_gm.GameState.CERCO_ISECTUM)` is called when `current_state` is `COMBATE_TATICO`. This transition is rejected by `can_transition_to()`, returning `false`. `_gm.current_state` remains `COMBATE_TATICO`. Line 111 asserts `assert_true(_gm.is_in_combat(), "CERCO_ISECTUM is combat")` and passes by coincidence because `COMBATE_TATICO` is also combat.
   - In `godot_project/test/unit/test_autoloads.gd`, line 136:
     `_gm.change_state(_gm.GameState.FIM_DE_JOGO)` is called when `current_state` is `MENU`. This transition is rejected, returning `false`. `_gm.current_state` remains `MENU`. `reset_state()` on line 138 is called on a state that was already `MENU`.
   - In `godot_project/test/unit/test_autoloads.gd`, line 154:
     `_gm.change_state(s)` inside the loop attempts `COMBATE_TATICO -> CERCO_ISECTUM` and `COMBATE_TATICO -> MULTIPLAYER_LOBBY`. Both return `false` and fail silently because the return value is unasserted.

3. **Source Code Inspection - AAA Pattern Violations**:
   In `godot_project/test/unit/test_autoloads.gd`:
   - Line 96: `# Act & Assert`
   - Line 103: `# Arrange & Act & Assert`
   - Line 117: `# Arrange & Act & Assert`
   - Line 290: `# Act & Assert`
   - Lines 301, 346, 371, 476, 483, 502: `# Arrange & Act`
   - Line 387: `assert_true(_dm.is_data_loaded())` placed inside `# Arrange`.

4. **ObjectDB Leaks**:
   Inspected verbose run via `./godot_project/bin/godot --headless --path ./godot_project -s addons/gut/gut_cmdln.gd -gexit --verbose`. 74 leaked ObjectDB instances (AudioStreamPlaybackOggVorbis, OggPacketSequencePlayback, etc.) and 12 uncollected audio resources at exit.

5. **Omitted Singleton Features**:
   - `DataManager.gd`: `get_isectum_caste()`, `get_all_isectum_castes()`, `has_caste()`, `get_card_data()`, `get_all_cards()`, `has_card()`, `get_hero_duplicate()`.
   - `GameManager.gd`: `can_transition_to()`, `change_state_and_scene()`, `get_state_payload()`.
   - `AudioManager.gd`: `set_bus_muted()`, `is_bus_muted()`, pitch scaling, EventBus audio request signals.
   - `EventBus.gd`: 11 signals and all telemetry methods (`reset_telemetry()`, `get_emission_count()`, `emit_logged()`).

---

## 2. Logic Chain

1. **Step 1 (From Observation 1)**: `./godot_project/run_gut_tests.sh` passes 44 tests with exit code 0, confirming the Godot 4 headless runner functions correctly.
2. **Step 2 (From Observation 1 and 2)**: The runner logs runtime engine warnings (`WARNING: [GameManager] Invalid state transition`). Tracing these lines revealed that tests in `test_autoloads.gd` attempted illegal FSM transitions that `GameManager.gd` explicitly prohibits.
3. **Step 3 (From Observation 2)**: Because `change_state()` return values were ignored in those tests, `current_state` never transitioned to `CERCO_ISECTUM` or `FIM_DE_JOGO`. The assertions succeeded only because prior state values persisted, constituting **false-positive test verification**.
4. **Step 4 (From Observation 3)**: GEMINI.md §4 and the dispatch instructions mandate strict Arrange-Act-Assert (AAA) structure. 10 test functions explicitly violate this by merging Arrange, Act, and Assert steps.
5. **Step 5 (From Observation 4)**: 74 ObjectDB instances leak at process exit due to active SFX players not being stopped or cleared during test suite teardown.
6. **Step 6 (From Observation 5)**: Significant surface area of the M1 singletons (castes, cards, payloads, mute controls, signals) remains unexercised by unit tests.
7. **Conclusion Step**: Therefore, Milestone 1 cannot be approved in its current state and requires targeted corrections.

---

## 3. Caveats

- **Host Asset Integrity**: 5 PNG images from the original Python repository remain malformed in `assets/images/`, as noted by `m1_worker_core`. This is unrelated to the M1 unit tests and did not influence this verdict.
- **Implementation Quality**: The underlying GDScript implementation of the singletons (`GameManager.gd`, `EventBus.gd`, `DataManager.gd`, `AudioManager.gd`) is well-structured and fully functional; the issues lie specifically within the test assertions, test structure, and teardown cleanup.

---

## 4. Conclusion

**Verdict: REQUEST_CHANGES**

Milestone 1 test harness and test suite require the following revisions from `m1_worker_core`:
1. **Fix false-positive state transition tests**: Update `test_game_manager_is_in_combat_flag`, `test_game_manager_reset_state_restores_menu`, and `test_game_manager_rapid_sequential_transitions` to use valid transition sequences and assert `change_state()` return values (`assert_true(...)`).
2. **Strict AAA Compliance**: Refactor all 10 non-compliant test functions in `test_autoloads.gd` into distinct `# Arrange`, `# Act`, and `# Assert` blocks without interleaving.
3. **Eliminate Memory Leaks**: Add `stop_all_sfx()` and proper stream cleanup in `AudioManager.gd`, invoking it in `after_each()` of `test_autoloads.gd`, and ensure autoload cleanup in `gut_cmdln.gd`.
4. **Complete Singleton Coverage**: Add test cases for `DataManager` (castes, cards, duplicates), `GameManager` (payloads, `can_transition_to`), `AudioManager` (mute, pitch), and `EventBus` (untested signals, telemetry).

---

## 5. Verification Method

To independently verify the resolution of these findings:

1. **Run Full Test Suite**:
   ```bash
   ./godot_project/run_gut_tests.sh
   ```
   **Verification Criteria**:
   - Exit code must be 0.
   - All tests pass.
   - **Zero** `[GameManager] Invalid state transition` runtime warnings appear during the test run.

2. **Check for Memory Leaks**:
   ```bash
   ./godot_project/bin/godot --headless --path ./godot_project -s addons/gut/gut_cmdln.gd -gexit --verbose
   ```
   **Verification Criteria**:
   - No `WARNING: ObjectDB instances were leaked at exit` warning or resource leak errors.

3. **Verify AAA Structure & Coverage**:
   Inspect `godot_project/test/unit/test_autoloads.gd`:
   - No merged `# Arrange & Act`, `# Act & Assert`, or `# Arrange & Act & Assert` comments.
   - Separate test methods for each singleton feature (castes, cards, payloads, mute).

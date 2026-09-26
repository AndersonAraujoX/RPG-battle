# Milestone 1 Tests & Test Harness Review Analysis

**Reviewer**: `m1_reviewer_tests`  
**Date**: 2026-09-26  
**Target Code**: `godot_project/test/unit/test_autoloads.gd`, `godot_project/run_gut_tests.sh`, `godot_project/.gutconfig.json`, `godot_project/addons/gut/`  
**Verdict**: **REQUEST_CHANGES**

---

## 1. Executive Summary

Milestone 1 established the Godot 4 base project configuration, Custom Resources, Autoload singletons (`GameManager`, `EventBus`, `DataManager`, `AudioManager`), and a headless GUT test runner. The test suite `./godot_project/run_gut_tests.sh` executes 44 tests and reports exit code 0.

However, an in-depth adversarial and quality review revealed **critical logic defects in the unit tests that produce false-positive passes**, **multiple violations of the mandatory Arrange-Act-Assert (AAA) pattern**, **ObjectDB memory leaks at exit**, and **omissions of required edge case and feature coverage** across the singletons.

---

## 2. Review Findings

### 🔴 Finding 1 [Critical]: Masked Test Failures & False-Positive Assertions in `GameManager`
- **Location**: `godot_project/test/unit/test_autoloads.gd`, lines 102–115, 134–142, and 143–158.
- **Problem**:
  In `GameManager.gd`, state transitions are strictly governed by `VALID_TRANSITIONS`. Three tests attempt illegal transitions which fail and return `false`, but the tests do not assert the return value of `change_state()`. Consequently, state transitions fail silently, leaving the state machine in an unintended state, and downstream assertions pass only by coincidence (false positives).

  1. **`test_game_manager_is_in_combat_flag` (lines 102–115)**:
     ```gdscript
     _gm.change_state(_gm.GameState.COMBATE_TATICO) # returns true -> state is COMBATE_TATICO
     assert_true(_gm.is_in_combat(), "COMBATE_TATICO is combat")

     _gm.change_state(_gm.GameState.CERCO_ISECTUM) # ILLEGAL! COMBATE_TATICO cannot transition to CERCO_ISECTUM
     assert_true(_gm.is_in_combat(), "CERCO_ISECTUM is combat") # FALSE POSITIVE: passes because state is STILL COMBATE_TATICO!
     ```
     Transition from `COMBATE_TATICO` to `CERCO_ISECTUM` is prohibited by `VALID_TRANSITIONS[GameState.COMBATE_TATICO] = [GameState.FIM_DE_JOGO, GameState.MENU]`. The call outputs a warning and returns `false`. State remains `COMBATE_TATICO`. `CERCO_ISECTUM` was **never tested**.

  2. **`test_game_manager_reset_state_restores_menu` (lines 134–142)**:
     ```gdscript
     # Arrange
     _gm.change_state(_gm.GameState.FIM_DE_JOGO) # ILLEGAL! MENU cannot transition to FIM_DE_JOGO
     # Act
     _gm.reset_state()
     # Assert
     assert_eq(_gm.current_state, _gm.GameState.MENU)
     ```
     `VALID_TRANSITIONS[GameState.MENU]` only permits transitions to `COMBATE_TATICO`, `CERCO_ISECTUM`, or `MULTIPLAYER_LOBBY`. Transitioning to `FIM_DE_JOGO` returns `false` and leaves `_gm.current_state` as `MENU`. `reset_state()` then runs on a state that was **already `MENU`**. The test passes vacuously without validating reset behavior from an active non-menu state.

  3. **`test_game_manager_rapid_sequential_transitions` (lines 143–158)**:
     The sequence array includes `[COMBATE_TATICO, CERCO_ISECTUM, MULTIPLAYER_LOBBY, FIM_DE_JOGO, MENU]`.
     - `COMBATE_TATICO -> CERCO_ISECTUM` fails (`false`).
     - `COMBATE_TATICO -> MULTIPLAYER_LOBBY` fails (`false`).
     Both intermediate transitions are rejected by the engine with warnings. The test never verifies whether transitions succeed, hiding the breakdown of the sequential chain.

- **Impact**: Tests provide an illusion of verification while masking illegal transitions and failing to exercise target states.
- **Suggested Fix**:
  - In `test_game_manager_is_in_combat_flag`: Reset to `MENU` before transitioning to `CERCO_ISECTUM`, or follow a valid path (`MENU -> CERCO_ISECTUM`). Always assert `assert_true(_gm.change_state(...))`.
  - In `test_game_manager_reset_state_restores_menu`: Transition to a valid non-menu state (`COMBATE_TATICO` or `CERCO_ISECTUM`), assert that the state is indeed non-menu, then execute `reset_state()`.
  - In `test_game_manager_rapid_sequential_transitions`: Use a valid transition path (e.g., `MENU -> COMBATE_TATICO -> FIM_DE_JOGO -> CERCO_ISECTUM -> MENU`) and assert `assert_true(success)` at every step.

---

### 🟠 Finding 2 [Major]: Pervasive Violations of Mandatory Arrange-Act-Assert (AAA) Pattern
- **Location**: `godot_project/test/unit/test_autoloads.gd`, lines 96, 103, 117, 290, 301, 346, 371, 387, 476, 483, 502.
- **Problem**:
  The user rules and `GEMINI.md § 4` strictly dictate the AAA structure for every test. In `test_autoloads.gd`, 10 test functions violate this standard:
  - Lines 96, 290: Use `# Act & Assert` comments with merged operations.
  - Lines 103, 117: Use `# Arrange & Act & Assert` comments with interleaved steps.
  - Lines 301, 346, 371, 476, 483, 502: Use `# Arrange & Act` comments with merged setup and invocation.
  - Line 387: In `test_data_manager_clear_cache`, an assertion (`assert_true(_dm.is_data_loaded())`) is executed inside the `# Arrange` block, and state re-arming is performed after `# Assert`.
  - Lines 220–248: Multiple distinct signals (`status_applied` and `status_removed`; `card_selected` and `round_resolved`) are bundled into compound test methods rather than isolated single-responsibility tests.
- **Impact**: Breaks project testing guidelines, reduces test readability, and obscures failure diagnostics.
- **Suggested Fix**: Refactor all test methods into three distinct, cleanly separated blocks (`# Arrange`, `# Act`, `# Assert`), ensuring one primary behavior per test.

---

### 🟠 Finding 3 [Major]: Memory Leaks & Resource Orphanage at Headless Exit
- **Location**: `godot_project/scripts/autoload/AudioManager.gd`, `godot_project/addons/gut/gut_cmdln.gd`, `godot_project/test/unit/test_autoloads.gd`.
- **Problem**:
  When running `./godot_project/run_gut_tests.sh --verbose`, the Godot engine reports:
  ```text
  WARNING: 74 ObjectDB instances were leaked at exit (run with `--verbose` for details).
     at: cleanup (core/object/object.cpp:2536)
  ERROR: 12 resources still in use at exit (run with --verbose for details).
     at: clear (core/io/resource.cpp:817)
  ```
  The leaked instances include:
  - 12 `AudioStreamPlaybackOggVorbis`
  - 12 `OggPacketSequencePlayback`
  - 6 `AudioStreamOggVorbis`
  - 6 `OggPacketSequence`
  Causes:
  1. `AudioManager.gd` allocates 12 pooled `AudioStreamPlayer` nodes and plays multiple sound effects during `test_audio_manager_sfx_pool_rapid_fire`, but lacks a `stop_all_sfx()` cleanup method.
  2. `test_autoloads.gd`'s `after_each()` only calls `_am.stop_bgm(0.0)` while leaving all 12 SFX players active with assigned streams.
  3. `gut_cmdln.gd` adds singleton nodes to `root` via `_initialize_autoloads()`, but fails to remove and free them before `quit(exit_code)`.
- **Impact**: Violates test isolation and clean resource disposal standards; leaves orphan memory references in engine processes.
- **Suggested Fix**:
  - Add `stop_all_sfx()` and `reset()` methods to `AudioManager.gd` to stop all players and clear streams.
  - Call `_am.stop_all_sfx()` in `after_each()` of `test_autoloads.gd`.
  - In `gut_cmdln.gd`, clean up all dynamically added autoload nodes before quitting.

---

### 🟠 Finding 4 [Major]: Coverage Gaps in Singleton Features & Edge Cases
- **Location**: `godot_project/scripts/autoload/`, `godot_project/test/unit/test_autoloads.gd`.
- **Problem**:
  Several public contracts and features implemented in M1 are completely omitted from `test_autoloads.gd`:
  1. **`DataManager.gd`**:
     - `get_isectum_caste()`, `get_all_isectum_castes()`, and `has_caste()` have zero unit tests.
     - `get_card_data()`, `get_all_cards()`, and `has_card()` have zero unit tests.
     - `get_hero_duplicate()` (deep copy verification) is never tested.
     - Invalid root JSON data structure (e.g. JSON array `"[1, 2, 3]"` instead of a dictionary) is not tested.
  2. **`GameManager.gd`**:
     - `can_transition_to(target_state)` direct query is not tested.
     - `change_state_and_scene()` is not tested.
     - `state_payload` delivery and retrieval (`get_state_payload()`) is never tested.
  3. **`AudioManager.gd`**:
     - Bus mute controls: `set_bus_muted()`, `is_bus_muted()` are never tested.
     - SFX pitch clamping (`pitch_scale` parameter in `play_sfx()`) is not tested.
     - EventBus signal reactivity: `AudioManager` subscribes to `EventBus.audio_play_sfx_requested` and `audio_play_bgm_requested`, but this integration is never verified.
  4. **`EventBus.gd`**:
     - 11 of the 19 signals (including `turn_changed`, `synergy_triggered`, `network_message_received`, `combat_log_entry_added`, `floating_text_requested`) are untested.
     - Telemetry helpers (`reset_telemetry()`, `get_emission_count()`, `emit_logged()`) are completely untested.
- **Impact**: Downstream milestones (M2–M6) rely on these unverified functions, risking regressions.
- **Suggested Fix**: Add dedicated test methods covering these functions and edge cases with strict AAA formatting.

---

### 🟡 Finding 5 [Minor]: Vacuous Assertion in `test_audio_manager_headless_safety`
- **Location**: `godot_project/test/unit/test_autoloads.gd`, lines 501–508.
- **Problem**:
  ```gdscript
  func test_audio_manager_headless_safety():
      # Arrange & Act
      _am.play_bgm("intro", 0.0)
      _am.play_sfx("miss")
      _am.stop_bgm(0.0)
      # Assert: headless dummy driver executes commands smoothly
      pass_test("AudioManager runs safely in headless execution mode")
  ```
  `pass_test()` is called unconditionally without verifying any observable state (such as `assert_false(_am.is_bgm_playing())` or validating player state).
- **Suggested Fix**: Replace unconditional `pass_test()` with concrete assertions verifying audio state transitions.

---

## 3. Verified Claims vs Observed Reality

| Upstream Claim | Verification Method | Result | Notes |
|---|---|:---:|---|
| "Godot 4 binary runs headless" | `./godot_project/run_gut_tests.sh` | **PASS** | Godot v4.7.2 executes cleanly via CLI |
| "All 44 unit tests pass with exit code 0" | CLI execution | **PASS** | Exit code 0, 44 tests passed, 97 assertions |
| "Strict Arrange-Act-Assert (AAA) compliance" | Ast / Code inspection | **FAIL** | 10 tests violate AAA structure (Finding 2) |
| "Validates all GameManager state transitions" | State machine trace | **FAIL** | 3 tests have illegal transitions masking failures (Finding 1) |
| "Zero leaks and clean isolation" | CLI `--verbose` inspection | **FAIL** | 74 ObjectDB leaks and 12 unreleased resources (Finding 3) |
| "Complete singleton coverage" | API & Call-site audit | **FAIL** | Castes, cards, payloads, mute, and 11 signals untested (Finding 4) |

---

## 4. Adversarial Stress-Test Results

1. **Stress-Testing Transition Rejection**:
   Attempting `change_state(GameState.CERCO_ISECTUM)` from `GameState.COMBATE_TATICO` returns `false` as expected by `GameManager`, but the existing unit test assumed it succeeded, proving that the test suite was not verifying return values.
2. **Stress-Testing Memory Teardown**:
   Calling `play_sfx()` 16 times in headless mode leaves audio playback stream instances bound in memory indefinitely because no stop or flush is invoked during teardown.
3. **Stress-Testing Corrupt JSON Payloads**:
   `DataManager.gd` gracefully rejects malformed JSON strings, but `test_autoloads.gd` only tests an unclosed string. Passing non-dictionary roots (e.g. `[1, 2, 3]`) or non-object values should also be tested to verify `json.data is Dictionary` branching.

---

## 5. Conclusion & Action Items

While the underlying GDScript architecture and Godot configuration are solid, the unit test suite contains **critical false-positive assertions**, **AAA non-compliance**, and **resource leaks** that must be corrected before Milestone 1 can be certified.

### Required Actions for `m1_worker_core`:
1. Fix all illegal state transitions in `test_game_manager_is_in_combat_flag`, `test_game_manager_reset_state_restores_menu`, and `test_game_manager_rapid_sequential_transitions`, asserting `change_state()` return values.
2. Standardize all test cases to strict **Arrange-Act-Assert (AAA)** with explicit comment headers and clean phase separation.
3. Add `stop_all_sfx()` and teardown cleanup to eliminate the 74 ObjectDB memory leaks at exit.
4. Add missing unit tests for `DataManager` (castes, cards, duplicate), `AudioManager` (bus mute, pitch scale), `GameManager` (payloads, `can_transition_to`), and `EventBus` (untested signals, telemetry).
5. Ensure `./godot_project/run_gut_tests.sh` passes cleanly with zero invalid transition warnings and zero ObjectDB leaks.

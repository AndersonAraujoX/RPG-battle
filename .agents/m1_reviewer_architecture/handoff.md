# Handoff Report: Milestone 1 Architecture Review & Adversarial Critique

**Author**: `m1_reviewer_architecture`  
**Milestone**: M1 (Foundation & Core Infrastructure)  
**Date**: 2026-09-26  
**Type**: Hard Handoff  
**Verdict**: **REQUEST_CHANGES**  

---

## 1. Observation

1. **Test Execution & Silent Failure Warnings**:
   Command executed:
   ```bash
   ./godot_project/run_gut_tests.sh
   ```
   Result: 44 tests passed, 97 assertions evaluated, exit code 0.
   However, during test execution, the engine output logged multiple warnings during positive tests:
   ```text
   WARNING: [GameManager] Invalid state transition: COMBATE_TATICO -> CERCO_ISECTUM
        at: push_warning (core/variant/variant_utility.cpp:1033)
        GDScript backtrace (most recent call first):
            [0] change_state (res://scripts/autoload/GameManager.gd:68)
            [1] test_game_manager_is_in_combat_flag (res://test/unit/test_autoloads.gd:110)
   WARNING: [GameManager] Invalid state transition: MENU -> FIM_DE_JOGO
        at: push_warning (core/variant/variant_utility.cpp:1033)
        GDScript backtrace (most recent call first):
            [0] change_state (res://scripts/autoload/GameManager.gd:68)
            [1] test_game_manager_reset_state_restores_menu (res://test/unit/test_autoloads.gd:136)
   WARNING: [GameManager] Invalid state transition: COMBATE_TATICO -> CERCO_ISECTUM
        [0] change_state (res://scripts/autoload/GameManager.gd:68)
        [1] test_game_manager_rapid_sequential_transitions (res://test/unit/test_autoloads.gd:154)
   WARNING: [GameManager] Invalid state transition: COMBATE_TATICO -> MULTIPLAYER_LOBBY
        [0] change_state (res://scripts/autoload/GameManager.gd:68)
        [1] test_game_manager_rapid_sequential_transitions (res://test/unit/test_autoloads.gd:154)
   ```

2. **Shutdown ObjectDB and Resource Leaks**:
   Command executed:
   ```bash
   ./godot_project/bin/godot --headless --verbose --path ./godot_project -s addons/gut/gut_cmdln.gd -gexit
   ```
   Verbatim output at shutdown:
   ```text
   WARNING: 74 ObjectDB instances were leaked at exit (run with `--verbose` for details).
      at: cleanup (core/object/object.cpp:2536)
   Leaked instance: OggPacketSequence:9223372067607414324 - Reference count: 33
   Leaked instance: AudioStreamOggVorbis:9223372067624191541 - Reference count: 16
   ...
   Leaked instance: AudioStreamPlaybackOggVorbis:9223372071432619595 - Reference count: 1
   Leaked instance: OggPacketSequencePlayback:9223372071449396815 - Reference count: 1
   ...
   ERROR: 12 resources still in use at exit.
      at: clear (core/io/resource.cpp:817)
   Resource still in use: res://assets/sounds/attack.ogg::OggPacketSequence_4ha8j (OggPacketSequence)
   Resource still in use: res://assets/sounds/attack.ogg (AudioStreamOggVorbis)
   ...
   ```

3. **DataManager Entity Segregation**:
   In `godot_project/scripts/autoload/DataManager.gd`, lines 148–153:
   ```gdscript
   func get_all_heroes() -> Array[CharacterData]:
       var result: Array[CharacterData] = []
       for c in _characters_cache.values():
           result.append(c)
       return result
   ```
   And `godot_project/dados/personagens.json` contains 28 entries including `ReiGoblin`, `LordeLich`, `DragaoAnciao`, `OrcChefe`, `EsqueletoArqueiro`, `Zangao_01`.
   `get_all_heroes()` returns all 28 entries, mixing playable heroes and hostile bosses.

4. **EventBus Argument Hardcoding**:
   In `godot_project/scripts/autoload/EventBus.gd`, lines 64–78:
   ```gdscript
   match args.size():
       0: emit_signal(sig_name)
       ...
       6: emit_signal(sig_name, args[0], args[1], args[2], args[3], args[4], args[5])
   ```
   Signals with 7+ arguments are not matched and are dropped.

5. **Direct Singleton Coupling**:
   In `godot_project/scripts/autoload/GameManager.gd`, lines 147–159:
   `GameManager` calls `get_node("/root/AudioManager").play_bgm(...)` directly instead of dispatching `EventBus.audio_play_bgm_requested`.

---

## 2. Logic Chain

1. **Derivation of Finding 1 (Masked Test Assertions)**:
   - In `GameManager.gd`, `VALID_TRANSITIONS` forbids `COMBATE_TATICO -> CERCO_ISECTUM` and `MENU -> FIM_DE_JOGO`.
   - In `test_autoloads.gd:test_game_manager_is_in_combat_flag()`, line 110 calls `_gm.change_state(_gm.GameState.CERCO_ISECTUM)` from `COMBATE_TATICO`.
   - `change_state()` rejects the transition, pushes a warning, and returns `false`.
   - The test does not assert the return value, so `current_state` remains `COMBATE_TATICO`.
   - Line 111 asserts `assert_true(_gm.is_in_combat(), "CERCO_ISECTUM is combat")`.
   - Because `is_in_combat()` returns true for either `COMBATE_TATICO` or `CERCO_ISECTUM`, the assertion passes purely because the state was STILL `COMBATE_TATICO`.
   - Therefore, `CERCO_ISECTUM` was never validated as a combat state. The test is a false positive.
   - Similarly, `test_game_manager_reset_state_restores_menu()` calls `change_state(FIM_DE_JOGO)` from `MENU`, which is rejected. `current_state` was already `MENU`, so `reset_state()` was never tested from a non-menu state.

2. **Derivation of Finding 2 (Shutdown Leaks)**:
   - `AudioManager.gd` allocates 12 `AudioStreamPlayer` nodes for `_sfx_pool`.
   - Unit tests (`test_audio_manager_sfx_pool_rapid_fire`, `test_audio_manager_headless_safety`) call `_am.play_sfx()`, initiating stream playbacks.
   - In `test_autoloads.gd:after_each()`, only `_am.stop_bgm(0.0)` is called; none of the pooled SFX players are stopped.
   - Upon engine termination, active audio stream playback instances are still held by the AudioServer, leading directly to 74 leaked ObjectDB instances and 12 unreleased resources.

3. **Derivation of Finding 3 (Hero vs Enemy Collection)**:
   - `personagens.json` contains both hero classes (`Guerreiro`, `Mago`) and monsters/bosses (`ReiGoblin`, `LordeLich`).
   - `DataManager.gd` caches all entries in `_characters_cache`.
   - `get_all_heroes()` iterates through `_characters_cache.values()` with no team filter.
   - Calling `get_all_heroes()` therefore returns bosses and monsters to any caller expecting playable heroes.

---

## 3. Caveats

- **No Malicious Fraud / Facades**:
  The implementation is substantive and mathematically genuine. All D&D 5e modifier formulas, ability scores, dice formulas, and fallback catalogs reflect real game logic. The issues identified are design and test implementation defects, not deliberate cheating or empty stubs.
- **Headless Environment Scope**:
  Visual node rendering in `Main.tscn` and live WebSocket networking are deferred to Milestones M2/M3/M5/M6 per `PROJECT.md` roadmap.

---

## 4. Conclusion

**Verdict: REQUEST_CHANGES**

Milestone 1 provides a functional foundation, but cannot be approved in its current state due to:
1. Three false-positive unit tests in `test_autoloads.gd` that pass by accident while masking rejected state transitions.
2. 74 leaked ObjectDB instances and 12 leaked resources at engine shutdown due to missing SFX player teardown in `AudioManager`.
3. Entity collection pollution in `DataManager.get_all_heroes()`.
4. Hardcoded argument limits in `EventBus.emit_logged`.
5. Direct singleton coupling in `GameManager`.

All required fixes are localized, well-defined, and actionable. Once the worker addresses these items, Milestone 1 will be ready for re-review and approval.

---

## 5. Verification Method

To independently verify whether these changes have been resolved:

1. **Run Headless GUT Runner with Warning Check**:
   ```bash
   ./godot_project/run_gut_tests.sh
   ```
   **Pass Condition**: 0 warnings emitted during positive test cases (`test_game_manager_is_in_combat_flag`, `test_game_manager_reset_state_restores_menu`, `test_game_manager_rapid_sequential_transitions`). Warnings should only occur during explicit negative tests (`test_game_manager_invalid_state_transition_rejected`, etc.).

2. **Verify Clean Shutdown (0 Leaks)**:
   ```bash
   ./godot_project/bin/godot --headless --verbose --path ./godot_project -s addons/gut/gut_cmdln.gd -gexit
   ```
   **Pass Condition**: 0 ObjectDB instances leaked at exit, 0 resources still in use at exit.

3. **Verify Hero Segregation**:
   Verify that `DataManager.get_all_heroes()` returns only characters with `team == "A"` (or canonical hero classes/heroes), excluding `ReiGoblin` and `LordeLich`.

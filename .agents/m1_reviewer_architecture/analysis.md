# Architecture Review & Adversarial Challenge Report: Milestone 1

**Reviewer**: `m1_reviewer_architecture`  
**Date**: 2026-09-26  
**Milestone**: M1 — Foundation & Core Infrastructure  
**Verdict**: **REQUEST_CHANGES**  
**Overall Risk Assessment**: **MEDIUM-HIGH**  

---

## Part 1: Quality & Architecture Review

### 1. Executive Summary

Milestone 1 successfully lays out the core skeleton for the Godot Engine 4 migration of **RPG-battle**:
- Viewport (1280x720), pixel art rendering filter, and `gl_compatibility` renderer configured in `godot_project/project.godot`.
- Autoload singletons (`EventBus.gd`, `DataManager.gd`, `GameManager.gd`, `AudioManager.gd`) established with static typing.
- Custom Resources (`CharacterData.gd`, `IsectumCasteData.gd`, `CardData.gd`) implemented with D&D 5e modifier math and bilingual Cerco getters.
- A functional headless test runner script (`run_gut_tests.sh`) executing 44 unit tests with exit code 0.
- Assets (`assets/sounds/`, `assets/images/`) and data (`dados/personagens.json`) mirrored cleanly inside `godot_project/`.

However, adversarial stress testing and execution log auditing revealed **critical test masking defects**, **memory leaks on engine shutdown**, **semantic data collection errors**, and **avoidable singleton coupling**. While there is no deliberate fraud or facade implementation (the codebase is genuine and functional), the test suite contains false-positive validations that mask unexecuted state branches, and `AudioStreamPlayback` resources leak at engine exit.

---

### 2. Review Dimensions Evaluation

| Dimension | Rating | Evaluation |
|---|---|---|
| **Correctness & Interface Conformance** | ⚠️ Needs Work | Autoload APIs conform to `PROJECT.md` contracts, but `DataManager.get_all_heroes()` leaks enemies/bosses into hero collections, and `GameManager` test flows mask illegal state transitions. |
| **Clean Architecture & SOLID** | ⚠️ Acceptable with Gaps | S, O, L, I principles are respected. However, `GameManager` directly couples to `/root/AudioManager` instead of using the dedicated `EventBus` audio signals. |
| **Type Safety & GDScript 4 Standards** | ✅ Good | Extensive use of static typing, class_name declarations, and `@export` attributes. Minor untyped arrays in `CharacterData.gd` (`dado_vida`, `dado_dano`, `perks`, `imunidades`). |
| **Error Handling & Resilience** | ✅ Good | `DataManager` handles missing files and corrupted JSON gracefully; `AudioManager` clamps volumes and pitch; `GameManager` validates transitions. |
| **Test Quality & Verification Integrity** | ❌ Defective | 3 tests in `test_autoloads.gd` pass by accident because `GameManager.change_state()` fails silently without assertion, testing states that were never actually reached. 74 ObjectDB instances leak on exit. |

---

### 3. Detailed Findings

#### [Major] Finding 1: Masked Test Assertions in `test_autoloads.gd` (False-Positive Validation)

- **Where**: `godot_project/test/unit/test_autoloads.gd`: lines 102–115, 134–142, and 143–158.
- **What**: Three tests in `test_autoloads.gd` attempt invalid state transitions that are rejected by `GameManager.VALID_TRANSITIONS`. Because the tests do not assert the return value of `change_state()` at intermediate steps, the state never changes, and subsequent assertions pass purely by coincidence:
  1. `test_game_manager_is_in_combat_flag`:
     ```gdscript
     _gm.change_state(_gm.GameState.COMBATE_TATICO)
     assert_true(_gm.is_in_combat(), "COMBATE_TATICO is combat")

     _gm.change_state(_gm.GameState.CERCO_ISECTUM) # REJECTED: COMBATE_TATICO -> CERCO_ISECTUM is illegal!
     assert_true(_gm.is_in_combat(), "CERCO_ISECTUM is combat") # Passes only because state is STILL COMBATE_TATICO!
     ```
     `is_in_combat()` was never actually verified while the FSM was in `CERCO_ISECTUM`.
  2. `test_game_manager_reset_state_restores_menu`:
     ```gdscript
     _gm.change_state(_gm.GameState.FIM_DE_JOGO) # REJECTED: MENU -> FIM_DE_JOGO is illegal!
     _gm.reset_state()
     assert_eq(_gm.current_state, _gm.GameState.MENU) # Passes only because state was already MENU!
     ```
     `reset_state()` was never verified resetting from an altered state; it was called while already in `MENU`.
  3. `test_game_manager_rapid_sequential_transitions`:
     Transitions `COMBATE_TATICO -> CERCO_ISECTUM` and `COMBATE_TATICO -> MULTIPLAYER_LOBBY` fail silently with warnings. The loop ends on `FIM_DE_JOGO -> MENU`, passing the final check while hiding two failed transitions.
- **Why**: Tests that pass by accident give a false sense of security. Downstream milestones relying on `GameManager` state transitions could introduce regressions that these tests would fail to catch.
- **Suggestion**:
  - In `test_game_manager_is_in_combat_flag`: Transition `MENU -> COMBATE_TATICO`, verify, then transition `COMBATE_TATICO -> MENU -> CERCO_ISECTUM`, asserting `assert_true(result)` at each step.
  - In `test_game_manager_reset_state_restores_menu`: Transition `MENU -> COMBATE_TATICO` first (or `MENU -> COMBATE_TATICO -> FIM_DE_JOGO`), assert `assert_true(success)`, and only then call `reset_state()`.
  - In `test_game_manager_rapid_sequential_transitions`: Use a valid transition sequence (e.g., `MENU -> MULTIPLAYER_LOBBY -> COMBATE_TATICO -> FIM_DE_JOGO -> MENU`) and assert `assert_true(result)` on each step.

---

#### [Major] Finding 2: Engine Shutdown Memory & Resource Leaks (74 ObjectDB Leaks, 12 Leaked Resources)

- **Where**: `godot_project/scripts/autoload/AudioManager.gd` & `godot_project/test/unit/test_autoloads.gd`.
- **What**: Running `./godot_project/bin/godot --headless --verbose --path ./godot_project -s addons/gut/gut_cmdln.gd -gexit` produces:
  ```text
  WARNING: 74 ObjectDB instances were leaked at exit.
  Leaked instance: AudioStreamPlaybackOggVorbis (multiple)
  Leaked instance: OggPacketSequencePlayback (multiple)
  ERROR: 12 resources still in use at exit.
  Resource still in use: res://assets/sounds/attack.ogg
  Resource still in use: res://assets/sounds/battle1.ogg
  ...
  ```
- **Why**: `AudioManager` allocates a pool of 12 `AudioStreamPlayer` nodes. When tests trigger SFX via `play_sfx()`, the audio streams play. In `test_autoloads.gd:after_each()`, `_am.stop_bgm(0.0)` is called, but the SFX players are never stopped or reset. Their internal playback objects remain bound to the audio server upon exit, generating ObjectDB leak warnings.
- **Suggestion**:
  - Add `func stop_all() -> void` to `AudioManager.gd` that stops `_bgm_player_a`, `_bgm_player_b`, and every player in `_sfx_pool`, setting their streams to `null` if necessary.
  - Call `_am.stop_all()` inside `after_each()` in `test_autoloads.gd`.

---

#### [Medium] Finding 3: `DataManager.get_all_heroes()` Returns Enemies and Bosses

- **Where**: `godot_project/scripts/autoload/DataManager.gd`: lines 148–153.
- **What**:
  ```gdscript
  func get_all_heroes() -> Array[CharacterData]:
      var result: Array[CharacterData] = []
      for c in _characters_cache.values():
          result.append(c)
      return result
  ```
  `_characters_cache` stores every entry in `personagens.json`, which includes `ReiGoblin`, `LordeLich`, `DragaoAnciao`, `OrcChefe`, `EsqueletoArqueiro`, `Zangao_01`, etc.
  Calling `get_all_heroes()` returns 28 characters, 17 of which are monsters and bosses with `team = "B"`.
- **Why**: Violates the principle of least astonishment. Downstream UI rosters (M3, M5) or character pickers calling `DataManager.get_all_heroes()` will inadvertently populate hero rosters with end-game bosses.
- **Suggestion**:
  - Filter `get_all_heroes()` to only return characters where `c.team == "A"` (or where `CANONICAL_HERO_IDS.has(c.id)` or `CANONICAL_CLASS_IDS.has(c.id)`).
  - Provide a separate method `get_all_characters()` or `get_all_enemies()` for the complete catalog or hostile units.

---

#### [Minor] Finding 4: `EventBus.emit_logged` Hardcoded 6-Argument Limit

- **Where**: `godot_project/scripts/autoload/EventBus.gd`: lines 64–78.
- **What**: `emit_logged` uses a `match args.size(): 0..6` statement. If an event has 7 or more arguments, the signal emission is silently dropped.
- **Why**: Arbitrary parameter limits create fragile code. Godot 4 GDScript supports dynamic callable invocation natively.
- **Suggestion**:
  Replace lines 64–78 with idiomatic Godot 4 syntax:
  ```gdscript
  if has_signal(sig_name):
      Callable(self, sig_name).callv(args)
  ```

---

#### [Minor] Finding 5: `GameManager` Couples Directly to `AudioManager` Bypassing `EventBus`

- **Where**: `godot_project/scripts/autoload/GameManager.gd`: lines 147–159.
- **What**: In `_enter_state()`, `GameManager` directly accesses `/root/AudioManager`:
  ```gdscript
  if has_node("/root/AudioManager"):
      get_node("/root/AudioManager").play_bgm("menu")
  ```
  Meanwhile, `EventBus.gd` already defines `signal audio_play_bgm_requested(track_name: String, crossfade: bool)`, and `AudioManager.gd` connects to it in `_connect_event_bus()`.
- **Why**: Bypassing the `EventBus` creates unnecessary tight coupling between singletons, defeating the purpose of an event-driven decoupled architecture.
- **Suggestion**:
  Use `EventBus.audio_play_bgm_requested.emit(...)` or dispatch via `EventBus` so `GameManager` has zero direct dependencies on `AudioManager`.

---

## Part 2: Adversarial Critique & Stress Testing

### 1. Overall Risk Assessment: **MEDIUM-HIGH**

While the core functionality works under happy-path conditions, the test harness currently provides false security in state machine validation and leaks engine resources on shutdown.

### 2. Adversarial Challenges

#### Challenge A: Cache Mutation Exploit (Shared Mutable Resource State)
- **Assumption Challenged**: Downstream callers treat `DataManager.get_hero_data(id)` as a read-only template.
- **Attack Scenario**: A combat unit script calls `var hero = DataManager.get_hero_data("Guerreiro")`. During combat, `hero.hp -= 8`. Because `_characters_cache` stores the raw reference, the global template for `Guerreiro` is permanently corrupted in memory. Subsequent battles or team members initialized from `get_hero_data("Guerreiro")` will spawn with 4 HP instead of 12 HP.
- **Blast Radius**: Game-wide state corruption across battle transitions and stage restarts.
- **Mitigation**:
  1. Clearly document that `get_hero_data()` returns the canonical immutable template and require entities to use `get_hero_duplicate(id)`.
  2. Or, provide an explicit method `create_character_instance(id)` that always returns `duplicate_data()`.

#### Challenge B: Illegal State Transition Cascades
- **Assumption Challenged**: FSM transitions will always be initiated sequentially along permitted paths.
- **Attack Scenario**: Network or UI race conditions fire an event attempting to jump from `COMBATE_TATICO` to `CERCO_ISECTUM`. `can_transition_to()` returns `false`, but the calling code assumes the transition succeeded and changes the camera or input context.
- **Blast Radius**: Desynchronization between `GameManager.current_state` and the active scene/UI layer.
- **Mitigation**: Ensure `change_state_and_scene` handles failure explicitly, and ensure test suites rigorously verify both permitted and rejected transitions.

---

### 3. Stress Test Results

| Scenario | Expected Behavior | Actual Behavior | Result |
|---|---|---|---|
| Direct CLI headless test run (`./run_gut_tests.sh`) | 44 tests pass, exit code 0 | 44 passed, exit code 0 | ✅ PASS |
| Verbose engine shutdown inspection (`--verbose`) | Clean resource teardown, 0 leaks | 74 ObjectDB leaks, 12 resources in use | ❌ FAIL (Finding 2) |
| `GameManager` invalid transition warning inspection | Warnings emitted only during negative test cases | Warnings emitted during positive tests (`test_game_manager_is_in_combat_flag`) | ❌ FAIL (Finding 1) |
| `DataManager.get_all_heroes()` filter test | Returns only playable heroes (Team A) | Returns all 28 entries including bosses (`ReiGoblin`, `LordeLich`) | ❌ FAIL (Finding 3) |
| JSON malformed / missing file resilience | Graceful fallback, no crash | Graceful `false` return, logged error | ✅ PASS |
| Audio volume clamping (`[-1.0, 2.5]`) | Clamped to `[0.0, 1.0]` | Accurately clamped | ✅ PASS |
| D&D 5e modifier calculation (`forca = 16`, `con = 14`) | +3 Str, +2 Con, 12 Max HP | Correct (+3, +2, 12 HP) | ✅ PASS |

---

## Part 3: Verified Claims & Coverage

### Verified Claims
- `project.godot`: 1280x720, pixel art nearest filter (0), `gl_compatibility` renderer confirmed.
- `default_bus_layout.tres`: Master, BGM, SFX buses configured confirmed.
- `EventBus.gd`: 19 signals matching `PROJECT.md` contract confirmed.
- `DataManager.gd`: Loads `dados/personagens.json` without hardcoded dummy stats confirmed.
- `CharacterData.gd`: D&D 5e modifier formula `floor((stat - 10) / 2)` and proficiency bonus `1 + ceil(level / 4)` mathematically correct.
- GUT framework: autonomous CLI headless execution with exit code 0 confirmed.

### Unverified Items
- Visual node rendering in `Main.tscn` (deferred to M2/M3 per project roadmap).
- WebSocket network connectivity (deferred to M6 per project roadmap).

---

## Part 4: Required Changes for Approval

Before Milestone 1 can be formally approved, the following fixes are requested:

1. **Fix Defective Unit Tests in `test_autoloads.gd`**:
   - Fix `test_game_manager_is_in_combat_flag` to route through legal states (`MENU -> COMBATE_TATICO -> MENU -> CERCO_ISECTUM`) and assert `result == true` at each transition.
   - Fix `test_game_manager_reset_state_restores_menu` to change state legally first (e.g. to `COMBATE_TATICO`) before calling `reset_state()`.
   - Fix `test_game_manager_rapid_sequential_transitions` to use a valid transition sequence and assert each transition.
2. **Resolve ObjectDB / Resource Leaks at Exit**:
   - Add `stop_all()` to `AudioManager.gd` to stop all players in `_sfx_pool`.
   - Call `_am.stop_all()` in `test_autoloads.gd:after_each()`.
3. **Filter `DataManager.get_all_heroes()`**:
   - Ensure `get_all_heroes()` returns only playable heroes (`team == "A"`). Add `get_all_characters()` if access to the full catalog (including bosses) is required.
4. **Clean up `EventBus.emit_logged`**:
   - Use `Callable(self, sig_name).callv(args)` to support arbitrary argument counts.
5. **Decouple `GameManager` from `AudioManager`**:
   - Use `EventBus.audio_play_bgm_requested.emit()` instead of direct `get_node("/root/AudioManager")`.

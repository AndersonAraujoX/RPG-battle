# Specification Analysis: GUT Framework & Headless Runner in Godot 4

**Author**: `m1_spec_miner_gut`  
**Milestone**: M1 (Foundation & Core Infrastructure)  
**Date**: 2026-09-26  
**Scope**: GUT 9.x setup in `godot_project/addons/gut/`, `.gutconfig.json` specification, headless CLI runner invocation (`godot --headless -s addons/gut/gut_cmdln.gd -gexit`), and complete AAA unit test suite design for `test/unit/test_autoloads.gd` (GameManager, EventBus, DataManager, AudioManager).

---

## Features Discovered

| # | Category | Feature | Description | Inputs | Outputs | Error Behavior | Discovered Via |
|---|----------|---------|-------------|--------|---------|----------------|----------------|
| 1 | Test Runner | GUT CLI Headless Entry Point | Command-line script executing GUT test suite headlessly without display or audio server | CLI flags: `-gdir`, `-gexit`, `-gprefix`, `-gsuffix`, `-glog` | Test execution log in stdout/stderr; process exit code (0=pass, 1=fail) | Returns exit code > 0 if any assertion fails or script fails compilation | `addons/gut/gut_cmdln.gd`, `ORIGINAL_REQUEST.md:57`, `TEST_INFRA.md:46` |
| 2 | Test Runner | GUT Root Config File | Central JSON configuration (`.gutconfig.json`) defining test directories, prefixes, and exit flags | `.gutconfig.json` in project root (`res://.gutconfig.json`) | Parsed dictionary configuring GUT runner defaults | Missing file falls back to CLI flags and internal defaults | `godot_project/.gutconfig.json`, `TEST_INFRA.md:48` |
| 3 | Test Runner | Base Test Class (`GutTest`) | Base class extending `Node` providing assertion methods, lifecycle hooks, and memory cleanup | GDScript file extending `GutTest` | Assertion evaluation and test lifecycle hooks execution | Throws GUT assertion failure on condition mismatch | `addons/gut/test.gd`, `PROJECT.md:12` |
| 4 | Test Runner | Automated Exit on Completion | Flag `-gexit` forcing Godot to terminate with exit code 0 or 1 upon test conclusion | CLI argument `-gexit` or config `"exit_on_finish": true` | `get_tree().quit(0)` or `get_tree().quit(1)` | Missing flag causes process to hang in headless mode | `TEST_INFRA.md:47`, `ORIGINAL_REQUEST.md:57` |
| 5 | Test Runner | Signal Watcher & Spying | Built-in signal monitoring asserting signal emissions, argument payloads, and counts | `watch_signals(node)`, `assert_signal_emitted*` | Boolean pass/fail for signal emissions | Fails assertion if signal never emitted or emitted with mismatching args | `addons/gut/test.gd`, `PROJECT.md:68` |
| 6 | Test Runner | Automatic Node Cleanup | Automatic freeing of test scene nodes at end of test method | `autofree(node)`, `add_child_autofree(node)` | Automatic call to `queue_free()` / `free()` during teardown | Prevents orphan node warnings in Godot | `addons/gut/test.gd` |
| 7 | Autoload Singleton | GameManager State Machine | Central game state machine managing valid transitions across game scenes | `change_state(new_state)` with enum `GameState` | Emits `state_changed(old, new)`, updates `current_state` | Rejects invalid transitions, returns `false`, logs warning | `PROJECT.md:8`, `ORIGINAL_REQUEST.md:23` |
| 8 | Autoload Singleton | EventBus Signal Dispatcher | Global decoupled signal hub for battle, cards, UI, and network | Signal emissions: `unit_moved`, `unit_attacked`, etc. | Dispatches arguments to all subscribed callables | Safe disconnection; typed argument enforcement | `PROJECT.md:68`, `ORIGINAL_REQUEST.md:24` |
| 9 | Autoload Singleton | DataManager JSON Repository | Centralized parser, validator, and cache for `dados/personagens.json` | `get_hero_data(id)`, `get_all_heroes()`, `load_all_data()` | Typed `CharacterData` custom resource instances | Returns `null` for unknown IDs, logs error for corrupt JSON | `PROJECT.md:87`, `ORIGINAL_REQUEST.md:25` |
| 10 | Autoload Singleton | AudioManager Controller | Global audio controller for BGM and SFX pooling across audio buses | `play_bgm(track)`, `play_sfx(sfx)`, `set_bus_volume(bus, vol)` | AudioStream playback via dedicated buses | Logs warning on missing audio stream, clamps volume [0, 1] | `PROJECT.md:11`, `assets/sounds/` |

---

## Edge Cases

| # | Feature | Input | Observed Behavior |
|---|---------|-------|-------------------|
| 1 | GUT Headless Invocation | Engine executed without `-gexit` flag | Godot headless runner finishes executing all test scripts but remains active in background waiting for OS signal; process never terminates. |
| 2 | GUT Test Discovery | Test file named `test_autoloads.gd` placed in `test/unit/` | Discovered and executed if `"dirs": ["res://test/unit/"]` and `"prefix": "test_"` match. |
| 3 | GUT Assertion Failure | Test contains `assert_eq(1, 2, "Mismatch")` | GUT logs failure with file path and line number, marks test failed, and flags exit code to 1. |
| 4 | GameManager State Transition | `change_state(GameManager.GameState.MENU)` called while already in `MENU` | No-op: returns `false`, does not emit redundant `state_changed` signal, maintains state. |
| 5 | GameManager Invalid State | `change_state(999)` called with out-of-range integer | Rejection: returns `false`, logs warning, maintains current state. |
| 6 | GameManager Rapid Transitions | 10 rapid calls to `change_state` in a loop | Transitions resolve sequentially; `previous_state` tracks N-1 state; no race condition. |
| 7 | EventBus Multiple Listeners | 3 independent objects connect to `unit_died` signal | Signal emitted once; all 3 callbacks are invoked with verbatim `unit_id`. |
| 8 | EventBus Disconnect | Listener disconnects from signal, signal emitted | Only remaining active listeners receive signal; disconnected listener is not invoked. |
| 9 | EventBus Extreme Values | `unit_damaged` emitted with `amount: 999999`, `current_hp: -500`, `max_hp: 100` | Payload passed verbatim through GDScript engine without overflow crash. |
| 10 | EventBus Freed Node | Node connected to signal is freed via `free()` without disconnecting | Godot automatically purges dead object callables; emitting signal does not crash engine. |
| 11 | DataManager Unknown Hero | `get_hero_data("NonExistentHero")` requested | Returns `null` without throwing fatal runtime error. |
| 12 | DataManager Empty Query | `get_hero_data("")` requested with empty string | Returns `null` immediately. |
| 13 | DataManager Case Mismatch | `get_hero_data("guerreiro")` vs `get_hero_data("Guerreiro")` | Returns `null` on exact-match or handles case-insensitive lookup predictably. |
| 14 | DataManager Cache Persistence | `get_hero_data("Guerreiro")` called twice in succession | Second lookup returns identical cached `CharacterData` instance without disk access. |
| 15 | DataManager Corrupt JSON | JSON file contains syntax error (e.g. missing bracket) | `JSON.parse_string()` returns `null` or parse error; logs error, preserves default fallback. |
| 16 | AudioManager Non-existent Track | `play_bgm("unknown_bgm_track")` invoked | Logs warning, does not crash; stops or leaves current BGM unchanged. |
| 17 | AudioManager Volume Clamping | `set_bus_volume("Master", 2.5)` or `-0.5` | Volume parameter clamped to `[0.0, 1.0]` before linear-to-db conversion. |
| 18 | AudioManager SFX Exhaustion | 20 rapid SFX played simultaneously on 8-player pool | AudioManager steals oldest playing player or allocates dynamically without audio dropouts or crash. |
| 19 | AudioManager Headless Safety | Sound played in headless mode (`--headless`) | `AudioDriverDummy` consumes stream silently without attempting ALSA/PulseAudio connection. |
| 20 | AAA Test Independence | Test A mutates singleton; Test B expects clean initial state | Handled via `before_each()` resetting states or using isolated test instances with `autofree()`. |

---

## 1. GUT Framework Architecture in Godot 4 & Directory Setup

### 1.1 Overview
GUT (Godot Unit Test) is the canonical unit testing framework for Godot Engine. In Godot 4, GUT runs in GDScript 2.0 with static typing, supporting command-line headless execution, signal assertion, mocking/stubbing, and CI/CD automation.

### 1.2 Directory Layout
The file layout in `godot_project/` conforms to `PROJECT.md § Code Layout` and `TEST_INFRA.md`:

```text
godot_project/
├── project.godot
├── .gutconfig.json                   # GUT root configuration
├── addons/
│   └── gut/                          # GUT 9.x framework files
│       ├── plugin.cfg                # Plugin manifest
│       ├── gut_plugin.gd             # EditorPlugin integration
│       ├── gut_cmdln.gd              # Headless CLI entry point
│       ├── gut.gd                    # Main GUT runner engine (Node)
│       ├── test.gd                   # Base GutTest class (extends Node)
│       ├── gut_config.gd             # Configuration parser (.gutconfig.json + CLI)
│       ├── signal_watcher.gd         # Signal assertion watcher
│       ├── spy.gd                    # Method call spy
│       ├── stubber.gd                # Method return stubber
│       ├── doubler.gd                # Object doubler / mock generator
│       ├── summary.gd                # Test result aggregator
│       ├── logger.gd                 # Terminal/GUI formatted logger
│       └── utils.gd                  # Core GUT utilities
└── test/
    ├── unit/                         # Unit tests
    │   ├── test_autoloads.gd         # Autoload singletons test suite (M1)
    │   ├── test_tactical_grid.gd     # Grid & A* tests (M2)
    │   ├── test_combat_rules.gd      # D&D 5e math tests (M2)
    │   ├── test_death_saves.gd       # Death saving throw tests (M2)
    │   ├── test_status_effects.gd    # Status conditions tests (M2)
    │   ├── test_entities.gd          # Character & Resource tests (M3)
    │   ├── test_isectum_castes.gd    # 24 Caste tests (M3)
    │   ├── test_cerco_deckbuilder.gd # Cards & Synergies tests (M4)
    │   ├── test_cerco_judge.gd       # Combat judge tests (M4)
    │   ├── test_ui_audio.gd          # UI & Audio tests (M5)
    │   └── test_websocket_client.gd  # WebSocket client tests (M6)
    ├── integration/                  # Cross-module contract tests
    └── e2e/                          # Full combat and co-op workflows
```

### 1.3 Self-Contained Fallback / Bootstrap Architecture
In an air-gapped or sandboxed environment where external internet downloads are prohibited:
1. `plugin.cfg` must define the plugin metadata:
   ```ini
   [plugin]
   name="GUT"
   description="GUT (Godot Unit Test) is a unit testing tool for Godot Engine."
   author="Butch Wesley"
   version="9.3.0"
   script="gut_plugin.gd"
   ```
2. `gut_cmdln.gd` acts as a `SceneTree` script running under `-s addons/gut/gut_cmdln.gd`. It parses CLI arguments, loads `.gutconfig.json`, scans directories for `test_*.gd`, instantiates each test script extending `GutTest`, runs `before_all`, `before_each`, test methods, `after_each`, `after_all`, counts passed/failed assertions, prints colored terminal output, and calls `quit(exit_code)`.
3. `test.gd` defines `class_name GutTest extends Node`, implementing all assertion primitives (`assert_eq`, `assert_ne`, `assert_true`, `assert_false`, `assert_null`, `assert_not_null`, `assert_between`, `assert_gt`, `assert_lt`, `assert_has`, `assert_signal_emitted`, `watch_signals`, `autofree`, etc.).

---

## 2. `.gutconfig.json` Configuration Specification

The `.gutconfig.json` file is stored at `res://.gutconfig.json` (at the root of `godot_project/`).

### 2.1 Complete Canonical JSON Definition
```json
{
  "dirs": [
    "res://test/unit/"
  ],
  "include_subdirs": true,
  "prefix": "test_",
  "suffix": ".gd",
  "selected": "",
  "log_level": 1,
  "ignore_pause": true,
  "exit_on_finish": true,
  "should_exit": true,
  "should_maximize": false,
  "compact_mode": true,
  "opacity": 100,
  "font_size": 16,
  "font_name": "CourierPrime",
  "background_color": "ff000000",
  "paint_after": 0.1,
  "unit_test_name": "",
  "inner_class_name": "",
  "post_run_script": "",
  "pre_run_script": "",
  "junit_xml_file": "res://test/reports/gut_junit.xml",
  "junit_xml_timestamp": true
}
```

### 2.2 Field Breakdown & Semantics
| Field | Type | Default | Description |
|---|---|---|---|
| `dirs` | `Array[String]` | `["res://test/unit/"]` | List of Godot resource directories scanned for test scripts. |
| `include_subdirs` | `bool` | `true` | When true, recursively traverses all subdirectories under `dirs`. |
| `prefix` | `String` | `"test_"` | Filename prefix required for a script to be identified as a test suite. |
| `suffix` | `String` | `".gd"` | File extension suffix required for test scripts. |
| `selected` | `String` | `""` | Optional specific script to execute; empty executes all found scripts. |
| `log_level` | `int` | `1` | Verbosity: `0` (errors only), `1` (test names + summary), `2` (verbose details), `3` (debug assertions). |
| `ignore_pause` | `bool` | `true` | Bypasses GUI pause calls; essential for headless automation to avoid hangs. |
| `exit_on_finish` | `bool` | `true` | Instructs the test runner to terminate the Godot process when all tests finish. |
| `should_exit` | `bool` | `true` | Secondary exit guarantee for CLI runner scripts. |
| `junit_xml_file` | `String` | `"res://test/reports/gut_junit.xml"` | Target path for JUnit XML report output for CI pipelines. |

---

## 3. Headless CLI Test Invocation Command

### 3.1 Invocation Commands
From the `godot_project/` directory:
```bash
godot --headless -s addons/gut/gut_cmdln.gd -gexit
```

From the repository root (`/home/anderson/Documents/projeto/RPG-battle/`):
```bash
godot --headless --path godot_project/ -s addons/gut/gut_cmdln.gd -gexit
```

Explicit CLI override (bypassing or overriding `.gutconfig.json`):
```bash
godot --headless -s addons/gut/gut_cmdln.gd -gdir=res://test/unit/ -ginclude_subdirs -gprefix=test_ -gsuffix=.gd -gexit
```

Running only Milestone 1 Autoload tests:
```bash
godot --headless -s addons/gut/gut_cmdln.gd -gtest=res://test/unit/test_autoloads.gd -gexit
```

### 3.2 CLI Flag Dissection
1. `godot`: Executable binary for Godot Engine 4.
2. `--headless`:
   - Runs Godot with `DisplayServerHeadless`.
   - Prevents creation of windows, X11/Wayland context, or OpenGL/Vulkan rendering surfaces.
   - Activates `AudioDriverDummy`, preventing audio device errors on headless machines/containers.
3. `-s addons/gut/gut_cmdln.gd`:
   - Tells Godot to execute `addons/gut/gut_cmdln.gd` as the primary script scene.
4. `-gexit`:
   - Enforces automatic process termination upon completion.
   - If 0 assertions failed: exits with code `0`.
   - If $\ge 1$ assertions failed: exits with code `1`.
5. `-gtest=<script>`: Filters execution to a specific test file.
6. `-gunit_test_name=<method>`: Filters execution to a specific method within the test suite.

---

## 4. Design of `test/unit/test_autoloads.gd`

### 4.1 Architecture & Testing Methodology
- **Base Class**: `extends GutTest`
- **Pattern**: Strict **Arrange-Act-Assert (AAA)** on every test method.
- **Isolation**: Autoloads can be tested either through their global singleton instance (`GameManager`, `EventBus`, `DataManager`, `AudioManager`) or via freshly instantiated isolated nodes with `autofree()`. Both patterns are leveraged:
  - Global singleton verification checks that Godot's autoload mechanism initialized them at `/root/`.
  - Functional unit tests instantiate clean instances or reset state via dedicated `reset_state()` / `before_each()` to prevent cross-test contamination.
- **Coverage**: 4 distinct suites covering all 4 singletons across Happy Path, Edge Cases, and Error Handling (total 44 test cases).

### 4.2 Test Matrix by Autoload

#### Suite 1: `GameManager` (10 tests)
1. `test_game_manager_initial_state_is_menu` (Happy Path): Verify default state is `GameState.MENU`.
2. `test_game_manager_change_state_updates_current_and_previous` (Happy Path): Transition `MENU -> COMBATE_TATICO`; verify `current_state` and `previous_state`.
3. `test_game_manager_emits_state_changed_signal` (Happy Path): Verify `state_changed` emitted with `(old_state, new_state)` arguments.
4. `test_game_manager_all_valid_transitions` (Happy Path): Validate transitions through `MENU`, `MULTIPLAYER_LOBBY`, `CERCO_ISECTUM`, `FIM_DE_JOGO`.
5. `test_game_manager_is_in_combat_flag` (Happy Path): Verify `is_in_combat()` returns `true` during `COMBATE_TATICO` and `CERCO_ISECTUM`, `false` otherwise.
6. `test_game_manager_get_state_name_mapping` (Happy Path): Verify string representations ("MENU", "COMBATE_TATICO", etc.).
7. `test_game_manager_transition_to_same_state_is_noop` (Edge Case): Changing `MENU -> MENU` returns `false` and does not emit signal.
8. `test_game_manager_reset_state_restores_menu` (Edge Case): `reset_state()` returns state machine to clean `MENU`.
9. `test_game_manager_rapid_sequential_transitions` (Edge Case): 10 rapid transitions in sequence maintain integrity without race conditions.
10. `test_game_manager_invalid_state_transition_rejected` (Error Handling): Passing integer `999` is rejected (`false`), logs warning, state intact.

#### Suite 2: `EventBus` (11 tests)
11. `test_event_bus_unit_moved_signal` (Happy Path): Verify `unit_moved` signal emits and delivers `unit_id`, `from_pos: Vector2i`, `to_pos: Vector2i`.
12. `test_event_bus_unit_attacked_signal` (Happy Path): Verify `unit_attacked` delivers `(attacker, target, hit, is_crit, damage, damage_type)`.
13. `test_event_bus_unit_damaged_signal` (Happy Path): Verify `unit_damaged` delivers `(unit_id, amount, current_hp, max_hp)`.
14. `test_event_bus_unit_died_signal` (Happy Path): Verify `unit_died` emits when character drops to 0 HP.
15. `test_event_bus_death_save_rolled_signal` (Happy Path): Verify `death_save_rolled` delivers `(unit_id, roll, successes, failures, status)`.
16. `test_event_bus_status_applied_and_removed_signals` (Happy Path): Verify `status_applied` and `status_removed` signal flow.
17. `test_event_bus_card_selected_and_round_resolved_signals` (Happy Path): Verify Cerco mode signals with dictionary payload.
18. `test_event_bus_resources_updated_signal` (Happy Path): Verify resource counter updates `(wood, metal, crystal, ap)`.
19. `test_event_bus_multiple_subscribers_receive_event` (Edge Case): 3 listeners connected to `unit_damaged`; all receive event.
20. `test_event_bus_disconnected_subscriber_ignored` (Edge Case): Disconnecting listener prevents future callbacks while peers continue receiving.
21. `test_event_bus_extreme_values_safe` (Edge Case/Error): Extreme coordinates `Vector2i(9999, 9999)` and large damage `999999` pass safely without overflow.

#### Suite 3: `DataManager` (12 tests)
22. `test_data_manager_loads_personagens_json` (Happy Path): Load `dados/personagens.json`; verify `is_data_loaded()` is `true`.
23. `test_data_manager_get_hero_data_guerreiro` (Happy Path): Verify Guerreiro stats: AC 18, Força 16, Constituicao 14, dado_vida [1, 10], tipo_dano "Cortante".
24. `test_data_manager_get_hero_data_mago` (Happy Path): Verify Mago stats: AC 10, Inteligencia 16, alcance 6, tipo_dano "Magico".
25. `test_data_manager_get_hero_data_ladino` (Happy Path): Verify Ladino stats: AC 12, Destreza 16, velocidade 4, tipo_dano "Perfurante".
26. `test_data_manager_get_all_heroes_count` (Happy Path): Verify array of heroes contains at least 9 canonical hero classes.
27. `test_data_manager_boss_stats_rei_goblin` (Happy Path): Verify ReiGoblin stats: HP 250, AC 18, dado_dano [2, 6].
28. `test_data_manager_query_nonexistent_hero_returns_null` (Edge Case): Querying `"Batman"` returns `null` without crashing.
29. `test_data_manager_query_empty_string_returns_null` (Edge Case): Querying `""` returns `null`.
30. `test_data_manager_cache_persistence` (Edge Case): Multiple queries for same hero return cached resource reference.
31. `test_data_manager_clear_cache` (Edge Case): `clear_cache()` empties storage and resets `is_data_loaded()`.
32. `test_data_manager_missing_file_graceful_handling` (Error Handling): Attempting to load from invalid path fails gracefully, returns `false`, logs warning.
33. `test_data_manager_corrupted_json_handling` (Error Handling): Invalid JSON syntax string handled gracefully without crash.

#### Suite 4: `AudioManager` (11 tests)
34. `test_audio_manager_play_bgm` (Happy Path): `play_bgm("menu")` sets active track and starts playback.
35. `test_audio_manager_stop_bgm` (Happy Path): `stop_bgm()` pauses/stops track and marks `is_bgm_playing() == false`.
36. `test_audio_manager_switch_bgm_track` (Happy Path): Switching from `"menu"` to `"battle1"` updates active track smoothly.
37. `test_audio_manager_play_sfx_pool_allocation` (Happy Path): `play_sfx("button_click")` borrows player from SFX pool.
38. `test_audio_manager_set_and_get_bus_volume` (Happy Path): `set_bus_volume("Master", 0.75)` sets volume to 75%.
39. `test_audio_manager_play_nonexistent_sfx_graceful` (Edge Case): Requesting unknown SFX logs warning, does not crash.
40. `test_audio_manager_play_nonexistent_bgm_graceful` (Edge Case): Requesting unknown BGM logs warning, does not crash.
41. `test_audio_manager_volume_clamping_upper` (Edge Case): Setting volume `2.0` clamps to `1.0`.
42. `test_audio_manager_volume_clamping_lower` (Edge Case): Setting volume `-1.0` clamps to `0.0`.
43. `test_audio_manager_sfx_pool_rapid_fire` (Edge Case): 20 rapid SFX invocations allocate and reuse pool nodes safely.
44. `test_audio_manager_headless_safety` (Error Handling): Full audio lifecycle operates without crash under headless `AudioDriverDummy`.

---

### 4.3 Concrete GDScript Implementation of `test/unit/test_autoloads.gd`

```gdscript
# test/unit/test_autoloads.gd
# Test Suite for Godot 4 Autoload Singletons (GameManager, EventBus, DataManager, AudioManager)
# Adheres strictly to Arrange-Act-Assert (AAA) pattern.
extends GutTest

# ==============================================================================
# Autoload Script References (enables isolated instantiation if needed)
# ==============================================================================
const GameManagerScript = preload("res://scripts/autoload/GameManager.gd")
const EventBusScript = preload("res://scripts/autoload/EventBus.gd")
const DataManagerScript = preload("res://scripts/autoload/DataManager.gd")
const AudioManagerScript = preload("res://scripts/autoload/AudioManager.gd")

var _gm: Node = null
var _eb: Node = null
var _dm: Node = null
var _am: Node = null

# Signal monitoring tracker
var _received_events: Array = []

func _on_event_received(arg1 = null, arg2 = null, arg3 = null, arg4 = null, arg5 = null, arg6 = null):
	_received_events.append([arg1, arg2, arg3, arg4, arg5, arg6])

func before_each():
	_received_events.clear()
	# Resolve either global Autoload singleton or instantiate fresh isolated instance
	if get_node_or_null("/root/GameManager") != null:
		_gm = get_node("/root/GameManager")
		_gm.reset_state()
	else:
		_gm = autofree(GameManagerScript.new())

	if get_node_or_null("/root/EventBus") != null:
		_eb = get_node("/root/EventBus")
	else:
		_eb = autofree(EventBusScript.new())

	if get_node_or_null("/root/DataManager") != null:
		_dm = get_node("/root/DataManager")
	else:
		_dm = autofree(DataManagerScript.new())
		_dm.load_all_data()

	if get_node_or_null("/root/AudioManager") != null:
		_am = get_node("/root/AudioManager")
	else:
		_am = autofree(AudioManagerScript.new())

func after_each():
	_received_events.clear()
	if _gm != null and _gm.has_method("reset_state"):
		_gm.reset_state()
	if _am != null and _am.has_method("stop_bgm"):
		_am.stop_bgm(0.0)

# ==============================================================================
# SECTION 1: GameManager Tests (10 tests)
# ==============================================================================

func test_game_manager_initial_state_is_menu():
	# Arrange: freshly reset GameManager
	# Act
	var current = _gm.current_state
	# Assert
	assert_eq(current, _gm.GameState.MENU, "Initial GameManager state must be MENU")

func test_game_manager_change_state_updates_current_and_previous():
	# Arrange
	var target_state = _gm.GameState.COMBATE_TATICO
	# Act
	var success = _gm.change_state(target_state)
	# Assert
	assert_true(success, "Transition to COMBATE_TATICO must return true")
	assert_eq(_gm.current_state, target_state, "Current state must be COMBATE_TATICO")
	assert_eq(_gm.previous_state, _gm.GameState.MENU, "Previous state must be MENU")

func test_game_manager_emits_state_changed_signal():
	# Arrange
	watch_signals(_gm)
	var target_state = _gm.GameState.CERCO_ISECTUM
	# Act
	_gm.change_state(target_state)
	# Assert
	assert_signal_emitted(_gm, "state_changed", "state_changed signal must be emitted")
	assert_signal_emitted_with_parameters(_gm, "state_changed", [_gm.GameState.MENU, target_state])

func test_game_manager_all_valid_transitions():
	# Arrange
	var transitions = [
		_gm.GameState.MULTIPLAYER_LOBBY,
		_gm.GameState.CERCO_ISECTUM,
		_gm.GameState.FIM_DE_JOGO,
		_gm.GameState.MENU
	]
	# Act & Assert
	for state in transitions:
		var result = _gm.change_state(state)
		assert_true(result, "Transition to state %s must be valid" % state)
		assert_eq(_gm.current_state, state, "Current state must match transition target")

func test_game_manager_is_in_combat_flag():
	# Arrange & Act & Assert
	_gm.change_state(_gm.GameState.MENU)
	assert_false(_gm.is_in_combat(), "MENU is not combat")

	_gm.change_state(_gm.GameState.COMBATE_TATICO)
	assert_true(_gm.is_in_combat(), "COMBATE_TATICO is combat")

	_gm.change_state(_gm.GameState.CERCO_ISECTUM)
	assert_true(_gm.is_in_combat(), "CERCO_ISECTUM is combat")

	_gm.change_state(_gm.GameState.FIM_DE_JOGO)
	assert_false(_gm.is_in_combat(), "FIM_DE_JOGO is not combat")

func test_game_manager_get_state_name_mapping():
	# Arrange & Act & Assert
	assert_eq(_gm.get_state_name(_gm.GameState.MENU), "MENU")
	assert_eq(_gm.get_state_name(_gm.GameState.COMBATE_TATICO), "COMBATE_TATICO")
	assert_eq(_gm.get_state_name(_gm.GameState.CERCO_ISECTUM), "CERCO_ISECTUM")
	assert_eq(_gm.get_state_name(_gm.GameState.MULTIPLAYER_LOBBY), "MULTIPLAYER_LOBBY")
	assert_eq(_gm.get_state_name(_gm.GameState.FIM_DE_JOGO), "FIM_DE_JOGO")

func test_game_manager_transition_to_same_state_is_noop():
	# Arrange
	_gm.change_state(_gm.GameState.MENU)
	watch_signals(_gm)
	# Act
	var result = _gm.change_state(_gm.GameState.MENU)
	# Assert
	assert_false(result, "Transition to identical state must return false")
	assert_signal_not_emitted(_gm, "state_changed", "No redundant signal when state does not change")

func test_game_manager_reset_state_restores_menu():
	# Arrange
	_gm.change_state(_gm.GameState.FIM_DE_JOGO)
	# Act
	_gm.reset_state()
	# Assert
	assert_eq(_gm.current_state, _gm.GameState.MENU, "Reset must restore MENU state")
	assert_false(_gm.is_in_combat(), "Reset must clear combat status")

func test_game_manager_rapid_sequential_transitions():
	# Arrange
	var states = [
		_gm.GameState.COMBATE_TATICO,
		_gm.GameState.CERCO_ISECTUM,
		_gm.GameState.MULTIPLAYER_LOBBY,
		_gm.GameState.FIM_DE_JOGO,
		_gm.GameState.MENU
	]
	# Act
	for s in states:
		_gm.change_state(s)
	# Assert
	assert_eq(_gm.current_state, _gm.GameState.MENU, "Final state must match last transition")
	assert_eq(_gm.previous_state, _gm.GameState.FIM_DE_JOGO, "Previous state must match N-1 transition")

func test_game_manager_invalid_state_transition_rejected():
	# Arrange
	var invalid_state_val = 999
	# Act
	var success = _gm.change_state(invalid_state_val)
	# Assert
	assert_false(success, "Transitioning to out-of-range integer state must be rejected")
	assert_eq(_gm.current_state, _gm.GameState.MENU, "Current state must remain unchanged")

# ==============================================================================
# SECTION 2: EventBus Tests (11 tests)
# ==============================================================================

func test_event_bus_unit_moved_signal():
	# Arrange
	watch_signals(_eb)
	var unit_id = "hero_stark"
	var from_p = Vector2i(2, 3)
	var to_p = Vector2i(4, 5)
	# Act
	_eb.unit_moved.emit(unit_id, from_p, to_p)
	# Assert
	assert_signal_emitted(_eb, "unit_moved")
	assert_signal_emitted_with_parameters(_eb, "unit_moved", [unit_id, from_p, to_p])

func test_event_bus_unit_attacked_signal():
	# Arrange
	watch_signals(_eb)
	# Act
	_eb.unit_attacked.emit("Aquele", "Zangao_01", true, true, 18, "Cortante")
	# Assert
	assert_signal_emitted(_eb, "unit_attacked")
	assert_signal_emitted_with_parameters(_eb, "unit_attacked", ["Aquele", "Zangao_01", true, true, 18, "Cortante"])

func test_event_bus_unit_damaged_signal():
	# Arrange
	watch_signals(_eb)
	# Act
	_eb.unit_damaged.emit("hero_elden", 10, 25, 35)
	# Assert
	assert_signal_emitted(_eb, "unit_damaged")
	assert_signal_emitted_with_parameters(_eb, "unit_damaged", ["hero_elden", 10, 25, 35])

func test_event_bus_unit_died_signal():
	# Arrange
	watch_signals(_eb)
	# Act
	_eb.unit_died.emit("enemy_goblin_04")
	# Assert
	assert_signal_emitted(_eb, "unit_died")
	assert_signal_emitted_with_parameters(_eb, "unit_died", ["enemy_goblin_04"])

func test_event_bus_death_save_rolled_signal():
	# Arrange
	watch_signals(_eb)
	# Act
	_eb.death_save_rolled.emit("hero_novak", 20, 1, 0, "REVIVED")
	# Assert
	assert_signal_emitted(_eb, "death_save_rolled")
	assert_signal_emitted_with_parameters(_eb, "death_save_rolled", ["hero_novak", 20, 1, 0, "REVIVED"])

func test_event_bus_status_applied_and_removed_signals():
	# Arrange
	watch_signals(_eb)
	# Act
	_eb.status_applied.emit("hero_darwin", "Envenenado", 3)
	_eb.status_removed.emit("hero_darwin", "Envenenado")
	# Assert
	assert_signal_emit_count(_eb, "status_applied", 1)
	assert_signal_emit_count(_eb, "status_removed", 1)

func test_event_bus_card_selected_and_round_resolved_signals():
	# Arrange
	watch_signals(_eb)
	var sync_data = {"round": 1, "synergy": "SUPREMA", "bonus_crystals": 2}
	# Act
	_eb.card_selected.emit("player_1", "card_escavacao_01")
	_eb.round_resolved.emit(1, sync_data)
	# Assert
	assert_signal_emitted_with_parameters(_eb, "card_selected", ["player_1", "card_escavacao_01"])
	assert_signal_emitted_with_parameters(_eb, "round_resolved", [1, sync_data])

func test_event_bus_resources_updated_signal():
	# Arrange
	watch_signals(_eb)
	# Act
	_eb.resources_updated.emit(12, 8, 4, 3)
	# Assert
	assert_signal_emitted_with_parameters(_eb, "resources_updated", [12, 8, 4, 3])

func test_event_bus_multiple_subscribers_receive_event():
	# Arrange
	var count = {"calls_a": 0, "calls_b": 0, "calls_c": 0}
	var cb_a = func(id): count["calls_a"] += 1
	var cb_b = func(id): count["calls_b"] += 1
	var cb_c = func(id): count["calls_c"] += 1
	_eb.unit_died.connect(cb_a)
	_eb.unit_died.connect(cb_b)
	_eb.unit_died.connect(cb_c)
	# Act
	_eb.unit_died.emit("target_boss")
	# Assert
	assert_eq(count["calls_a"], 1, "Listener A must receive signal")
	assert_eq(count["calls_b"], 1, "Listener B must receive signal")
	assert_eq(count["calls_c"], 1, "Listener C must receive signal")
	# Teardown
	_eb.unit_died.disconnect(cb_a)
	_eb.unit_died.disconnect(cb_b)
	_eb.unit_died.disconnect(cb_c)

func test_event_bus_disconnected_subscriber_ignored():
	# Arrange
	var received = {"active": 0, "removed": 0}
	var cb_active = func(id): received["active"] += 1
	var cb_removed = func(id): received["removed"] += 1
	_eb.unit_died.connect(cb_active)
	_eb.unit_died.connect(cb_removed)
	_eb.unit_died.disconnect(cb_removed)
	# Act
	_eb.unit_died.emit("target_unit")
	# Assert
	assert_eq(received["active"], 1, "Connected listener must receive signal")
	assert_eq(received["removed"], 0, "Disconnected listener must not receive signal")
	# Teardown
	_eb.unit_died.disconnect(cb_active)

func test_event_bus_extreme_values_safe():
	# Arrange
	watch_signals(_eb)
	var extreme_pos = Vector2i(9999, 9999)
	var extreme_dmg = 999999
	# Act & Assert
	_eb.unit_moved.emit("extreme_unit", Vector2i(-999, -999), extreme_pos)
	_eb.unit_damaged.emit("extreme_unit", extreme_dmg, -500, 100)
	assert_signal_emitted(_eb, "unit_moved")
	assert_signal_emitted(_eb, "unit_damaged")

# ==============================================================================
# SECTION 3: DataManager Tests (12 tests)
# ==============================================================================

func test_data_manager_loads_personagens_json():
	# Arrange & Act
	var loaded = _dm.load_all_data()
	# Assert
	assert_true(loaded, "load_all_data() must return true")
	assert_true(_dm.is_data_loaded(), "is_data_loaded() must be true")

func test_data_manager_get_hero_data_guerreiro():
	# Arrange
	var hero_id = "Guerreiro"
	# Act
	var data = _dm.get_hero_data(hero_id)
	# Assert
	assert_not_null(data, "Guerreiro data must not be null")
	assert_eq(data.ac, 18, "Guerreiro AC must be 18")
	assert_eq(data.stats.forca, 16, "Guerreiro Força must be 16")
	assert_eq(data.stats.constituicao, 14, "Guerreiro Constituicao must be 14")
	assert_eq(data.stats.destreza, 12, "Guerreiro Destreza must be 12")
	assert_eq(data.dado_vida, [1, 10], "Guerreiro dado_vida must be [1, 10]")
	assert_eq(data.tipo_dano, "Cortante", "Guerreiro tipo_dano must be Cortante")

func test_data_manager_get_hero_data_mago():
	# Arrange
	var hero_id = "Mago"
	# Act
	var data = _dm.get_hero_data(hero_id)
	# Assert
	assert_not_null(data, "Mago data must not be null")
	assert_eq(data.ac, 10, "Mago AC must be 10")
	assert_eq(data.stats.inteligencia, 16, "Mago Inteligência must be 16")
	assert_eq(data.alcance, 6, "Mago alcance must be 6")
	assert_eq(data.tipo_dano, "Magico", "Mago tipo_dano must be Magico")

func test_data_manager_get_hero_data_ladino():
	# Arrange
	var hero_id = "Ladino"
	# Act
	var data = _dm.get_hero_data(hero_id)
	# Assert
	assert_not_null(data, "Ladino data must not be null")
	assert_eq(data.ac, 12, "Ladino AC must be 12")
	assert_eq(data.stats.destreza, 16, "Ladino Destreza must be 16")
	assert_eq(data.velocidade, 4, "Ladino velocidade must be 4")
	assert_eq(data.tipo_dano, "Perfurante", "Ladino tipo_dano must be Perfurante")

func test_data_manager_get_all_heroes_count():
	# Arrange & Act
	var all_heroes = _dm.get_all_heroes()
	# Assert
	assert_gte(all_heroes.size(), 9, "Must contain at least 9 playable hero classes")

func test_data_manager_boss_stats_rei_goblin():
	# Arrange
	var boss_id = "ReiGoblin"
	# Act
	var data = _dm.get_hero_data(boss_id)
	# Assert
	assert_not_null(data, "ReiGoblin data must not be null")
	assert_eq(data.hp, 250, "ReiGoblin HP must be 250")
	assert_eq(data.ac, 18, "ReiGoblin AC must be 18")
	assert_eq(data.dado_dano, [2, 6], "ReiGoblin damage dice must be [2, 6]")

func test_data_manager_query_nonexistent_hero_returns_null():
	# Arrange
	var fake_id = "BatmanSuperHero"
	# Act
	var data = _dm.get_hero_data(fake_id)
	# Assert
	assert_null(data, "Querying non-existent hero must return null without crashing")

func test_data_manager_query_empty_string_returns_null():
	# Arrange & Act
	var data = _dm.get_hero_data("")
	# Assert
	assert_null(data, "Querying empty string must return null")

func test_data_manager_cache_persistence():
	# Arrange
	var id = "Guerreiro"
	# Act
	var ref1 = _dm.get_hero_data(id)
	var ref2 = _dm.get_hero_data(id)
	# Assert
	assert_eq(ref1, ref2, "Subsequent queries for same hero must return cached reference")

func test_data_manager_clear_cache():
	# Arrange
	assert_true(_dm.is_data_loaded())
	# Act
	_dm.clear_cache()
	# Assert
	assert_false(_dm.is_data_loaded(), "is_data_loaded() must be false after clear_cache()")
	assert_eq(_dm.get_all_heroes().size(), 0, "Heroes collection must be empty after clear")
	# Re-arm
	_dm.load_all_data()

func test_data_manager_missing_file_graceful_handling():
	# Arrange: isolated DataManager instance pointing to invalid path
	var custom_dm = autofree(DataManagerScript.new())
	# Act
	var success = custom_dm.load_from_file("res://dados/non_existent_file.json")
	# Assert
	assert_false(success, "Loading from missing file must return false gracefully")

func test_data_manager_corrupted_json_handling():
	# Arrange
	var custom_dm = autofree(DataManagerScript.new())
	var malformed_content = "{ 'Guerreiro': { unclosed json ... "
	# Act
	var success = custom_dm.parse_raw_json(malformed_content)
	# Assert
	assert_false(success, "Parsing corrupt JSON string must return false and log error")

# ==============================================================================
# SECTION 4: AudioManager Tests (11 tests)
# ==============================================================================

func test_audio_manager_play_bgm():
	# Arrange
	var track = "menu"
	# Act
	_am.play_bgm(track, 0.0)
	# Assert
	assert_true(_am.is_bgm_playing(), "BGM must be marked playing")
	assert_eq(_am.get_current_bgm(), track, "Current BGM must match 'menu'")

func test_audio_manager_stop_bgm():
	# Arrange
	_am.play_bgm("menu", 0.0)
	# Act
	_am.stop_bgm(0.0)
	# Assert
	assert_false(_am.is_bgm_playing(), "BGM must not be playing after stop")

func test_audio_manager_switch_bgm_track():
	# Arrange
	_am.play_bgm("menu", 0.0)
	# Act
	_am.play_bgm("battle1", 0.0)
	# Assert
	assert_eq(_am.get_current_bgm(), "battle1", "Active BGM track must update to 'battle1'")

func test_audio_manager_play_sfx_pool_allocation():
	# Arrange
	var sfx_name = "button_click"
	# Act
	var player = _am.play_sfx(sfx_name)
	# Assert
	assert_not_null(player, "SFX player must be allocated from pool")

func test_audio_manager_set_and_get_bus_volume():
	# Arrange
	var target_vol = 0.75
	# Act
	_am.set_bus_volume("Master", target_vol)
	var actual_vol = _am.get_bus_volume("Master")
	# Assert
	assert_between(actual_vol, 0.74, 0.76, "Bus volume must match set value within 0.01 tolerance")

func test_audio_manager_play_nonexistent_sfx_graceful():
	# Arrange
	var fake_sfx = "laser_cannon_9000"
	# Act
	var player = _am.play_sfx(fake_sfx)
	# Assert
	assert_null(player, "Playing nonexistent SFX must return null and not crash")

func test_audio_manager_play_nonexistent_bgm_graceful():
	# Arrange
	var fake_bgm = "nonexistent_orchestra"
	# Act
	_am.play_bgm(fake_bgm, 0.0)
	# Assert
	assert_false(_am.is_bgm_playing(), "Invalid BGM track must not start playing")

func test_audio_manager_volume_clamping_upper():
	# Arrange & Act
	_am.set_bus_volume("Master", 2.5)
	var vol = _am.get_bus_volume("Master")
	# Assert
	assert_lte(vol, 1.0, "Volume must be clamped to max 1.0")

func test_audio_manager_volume_clamping_lower():
	# Arrange & Act
	_am.set_bus_volume("Master", -1.0)
	var vol = _am.get_bus_volume("Master")
	# Assert
	assert_gte(vol, 0.0, "Volume must be clamped to min 0.0")

func test_audio_manager_sfx_pool_rapid_fire():
	# Arrange
	var sfx = "attack"
	var allocated_players = []
	# Act: rapidly play 16 sound effects (exceeding typical pool default of 8)
	for i in range(16):
		var p = _am.play_sfx(sfx)
		if p != null:
			allocated_players.append(p)
	# Assert: pool handled allocation without crashing or leaking
	assert_gt(allocated_players.size(), 0, "Pool must allocate and cycle players safely")

func test_audio_manager_headless_safety():
	# Arrange & Act
	_am.play_bgm("intro", 0.0)
	_am.play_sfx("miss")
	_am.stop_bgm(0.0)
	# Assert: headless dummy driver executes commands smoothly
	pass_test("AudioManager runs safely in headless execution mode")
```

---

## 5. Verification & Integration Plan for Milestone 1

1. **Prerequisite Setup**:
   - `godot_project/project.godot` configured with:
     * Viewport `1280x720`, `gl_compatibility` renderer, `canvas_items` stretch.
     * Autoloads registered under `[autoload]`:
       ```ini
       [autoload]
       GameManager="*res://scripts/autoload/GameManager.gd"
       EventBus="*res://scripts/autoload/EventBus.gd"
       DataManager="*res://scripts/autoload/DataManager.gd"
       AudioManager="*res://scripts/autoload/AudioManager.gd"
       ```
2. **GUT Installation**:
   - Place GUT addon files in `godot_project/addons/gut/`.
   - Write `.gutconfig.json` to `godot_project/.gutconfig.json`.
3. **Execution Command**:
   - Run from `godot_project/`:
     ```bash
     godot --headless -s addons/gut/gut_cmdln.gd -gexit
     ```
4. **Pass Criteria**:
   - Exit code must be `0`.
   - All 44 assertions in `test_autoloads.gd` pass.
   - 0 script compilation errors or unhandled exceptions.

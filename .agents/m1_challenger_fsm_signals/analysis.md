# Adversarial Analysis: GameManager FSM & EventBus Signals (Milestone M1)

**Agent**: `m1_challenger_fsm_signals`  
**Target Code**:
- `godot_project/scripts/autoload/GameManager.gd`
- `godot_project/scripts/autoload/EventBus.gd`
- `godot_project/test/unit/test_autoloads.gd`
**Empirical Harness**: `godot_project/test/unit/test_fsm_signals_stress.gd`  
**Execution Command**: `./bin/godot --headless -s addons/gut/gut_cmdln.gd -gexit`  
**Overall Risk Assessment**: **HIGH**

---

## 1. Executive Summary

Empirical stress testing of `GameManager.gd` and `EventBus.gd` was performed in Godot 4 headless mode, executing a 20-test adversarial suite spanning transition matrices, out-of-bounds states, high-frequency state cycling, multi-subscriber fan-out, iterator mutation safety, extreme payloads, recursive/re-entrant emissions, and telemetry isolation.

While the baseline transition table and individual signal declarations function under standard non-reentrant conditions, adversarial testing uncovered **four significant architectural vulnerabilities and one testing suite deficiency**:
1. **[CRITICAL] Re-entrant State Change Signal Inversion & Desynchronization**: When a subscriber to `GameManager.state_changed` initiates a secondary state transition, `EventBus.game_state_changed` emits signals in reverse order and broadcasts an illegal transition (`MENU -> FIM_DE_JOGO`) that bypasses the transition matrix.
2. **[HIGH] Dead Variable / Absent Re-entrancy Mutex**: `is_transitioning` is defined and set in `GameManager.gd` (lines 44, 73, 82), but is **never checked** in `change_state()` or `can_transition_to()`. It offers zero re-entrancy protection, risking uncontrolled recursion or state clobbering.
3. **[MEDIUM] Reference Aliasing in State Payload and EventBus Telemetry**: `state_payload` and `EventBus._event_history` store references to caller Dictionaries and Arrays without defensive deep-copying (`.duplicate(true)`), allowing external callers to retroactively mutate internal FSM state and historical telemetry logs.
4. **[MEDIUM] Silent FSM Mutation on Reset**: `reset_state()` and `reset_to_menu()` reset `current_state` to `MENU` without emitting `state_changed` or `game_state_changed`, leaving subscribers (HUD, Audio, Network) out-of-sync.
5. **[MEDIUM] EventBus.emit_logged Hardcoded Argument Cap & Telemetry Ghosting**: `emit_logged()` hardcodes a `match args.size(): 0..6`. Signals with 7+ arguments are silently dropped while still incrementing telemetry counters. Furthermore, calling `emit_logged()` with non-existent signals records false telemetry without warning.
6. **[LOW] False-Positive Assertions in Canonical Suite (`test_autoloads.gd`)**: `test_game_manager_rapid_sequential_transitions` and `test_game_manager_reset_state_restores_menu` execute illegal transitions (`COMBATE_TATICO -> CERCO_ISECTUM`, `MENU -> FIM_DE_JOGO`) that fail internally with warnings, but pass the test because intermediate return values are not asserted.

---

## 2. Detailed Adversarial Challenges

### Challenge 1 [CRITICAL]: Re-entrant State Change Inversion & EventBus Signal Desynchronization
- **Assumption Challenged**: Subsystem state changes triggered by state listeners execute safely and preserve causal event order across `GameManager` and `EventBus`.
- **Attack Scenario**:
  A gameplay subscriber connects to `GameManager.state_changed`. When the game moves from `MENU` to `COMBATE_TATICO`, the listener immediately triggers `change_state(GameState.FIM_DE_JOGO)` (e.g., instant defeat condition, tutorial skip, or error redirect).
  In `GameManager.gd`:
  ```gdscript
  73: is_transitioning = true
  74: var prev: GameState = current_state
  75: _exit_state(prev)
  77: previous_state = prev
  78: current_state = new_state as GameState
  79: state_payload = payload
  81: _enter_state(current_state, payload)
  82: is_transitioning = false
  84: state_changed.emit(prev, current_state)
  86: if has_node("/root/EventBus"):
  87:     get_node("/root/EventBus").game_state_changed.emit(prev, current_state)
  ```
  1. The outer call runs lines 73-84 for `MENU -> COMBATE_TATICO`.
  2. On line 84, `state_changed.emit(MENU, COMBATE_TATICO)` is dispatched to the listener.
  3. The listener calls `change_state(FIM_DE_JOGO)`.
  4. The inner `change_state` completes:
     - Emits `GameManager.state_changed(COMBATE_TATICO, FIM_DE_JOGO)`.
     - Emits `EventBus.game_state_changed(COMBATE_TATICO, FIM_DE_JOGO)`.
     - Sets `current_state = FIM_DE_JOGO`.
  5. The inner call returns.
  6. The outer call resumes at line 86!
  7. On line 87, the outer call executes:
     `get_node("/root/EventBus").game_state_changed.emit(prev, current_state)`
     Here, `prev` is `MENU` (outer local variable), but `current_state` was mutated by the inner call to `FIM_DE_JOGO`!
  8. Therefore, the outer call emits:
     `EventBus.game_state_changed.emit(MENU, FIM_DE_JOGO)`!
- **Blast Radius**:
  1. `EventBus` receives `(COMBATE_TATICO, FIM_DE_JOGO)` *before* `(MENU, FIM_DE_JOGO)`, reversing chronological order.
  2. `EventBus` emits `(MENU, FIM_DE_JOGO)`, which is an **illegal transition** explicitly forbidden in `VALID_TRANSITIONS`!
  3. External subscribers (such as WebSocket client, HUD, CombatLog) relying on `EventBus.game_state_changed` enter an invalid and desynchronized state.
- **Empirical Verification**:
  Verified in `test_gm_eventbus_reentrant_state_desynchronization` in `test_fsm_signals_stress.gd`:
  - `gm_signals[0] = [MENU, COMBATE_TATICO]`, `gm_signals[1] = [COMBATE_TATICO, FIM_DE_JOGO]`
  - `eb_signals[0] = [COMBATE_TATICO, FIM_DE_JOGO]`, `eb_signals[1] = [MENU, FIM_DE_JOGO]` (corrupted & inverted)
- **Mitigation**:
  1. Check `if is_transitioning: push_error("Re-entrant transition rejected"); return false` at the top of `change_state()`.
  2. Cache `target_state` as a local variable for signal emission rather than reading mutated `current_state` after callbacks.
  3. Emit `EventBus.game_state_changed` atomically alongside `GameManager.state_changed` before dispatching to external subscribers, or queue secondary state requests.

---

### Challenge 2 [HIGH]: Dead Variable / Absent Re-entrancy Mutex
- **Assumption Challenged**: `is_transitioning` guards `GameManager` against overlapping or re-entrant transitions.
- **Attack Scenario**:
  Inspecting `GameManager.gd`:
  - Line 44: `var is_transitioning: bool = false`
  - Line 73: `is_transitioning = true`
  - Line 82: `is_transitioning = false`
  - Line 137: `is_transitioning = false`
  Nowhere in `GameManager.gd` is `is_transitioning` read! Neither `can_transition_to()` nor `change_state()` checks `if is_transitioning: return false`.
- **Blast Radius**:
  Concurrent or re-entrant calls to `change_state` (e.g. from UI input events, background timers, or signal handlers) can interleave during `_enter_state` or `change_scene_to_file`. Because there is no check, cyclical state transitions will cause an uncatchable Stack Overflow crash in the Godot virtual machine.
- **Empirical Verification**:
  Verified in `test_gm_is_transitioning_guard_audit` in `test_fsm_signals_stress.gd`. Setting `is_transitioning = true` manually and calling `change_state()` succeeds unconditionally.
- **Mitigation**:
  Enforce guard in `can_transition_to` and `change_state`:
  ```gdscript
  if is_transitioning:
      push_warning("[GameManager] Transition rejected: already transitioning")
      return false
  ```

---

### Challenge 3 [MEDIUM]: Payload Aliasing & Retroactive Telemetry Corruption
- **Assumption Challenged**: Data payloads passed to `GameManager.change_state()` and `EventBus.emit_logged()` are immutable snapshots.
- **Attack Scenario**:
  Caller creates a payload dictionary:
  ```gdscript
  var payload = {"room_id": "abc", "turn": 1}
  GameManager.change_state(GameState.COMBATE_TATICO, payload)
  payload["turn"] = 999 # External mutation
  ```
  In `GameManager.gd`:
  `state_payload = payload` (Line 79)
  In `EventBus.gd`:
  `_event_history.append({"signal": sig_name, "args": args, ...})` (Line 57)
  In GDScript, Dictionaries and Arrays are passed by reference. External mutations directly alter `GameManager.get_state_payload()` and the historical events stored in `_event_history`.
- **Blast Radius**:
  Subsystems reading `state_payload` or telemetry inspectors verifying test events read corrupted/mutated data rather than the state at the time of transition/emission.
- **Empirical Verification**:
  Verified in `test_gm_payload_aliasing_and_mutability` and `test_eb_telemetry_history_aliasing_audit`. Mutating arguments after calling `emit_logged()` retroactively altered `_event_history[0]["args"]`.
- **Mitigation**:
  Use deep copy when storing payloads and telemetry arguments:
  `state_payload = payload.duplicate(true)`
  `_event_history.append({"signal": sig_name, "args": args.duplicate(true), "timestamp": Time.get_ticks_msec()})`

---

### Challenge 4 [MEDIUM]: Silent FSM Mutation on Reset
- **Assumption Challenged**: Resetting the game state to MENU notifies registered subsystems.
- **Attack Scenario**:
  Game encounters a desynchronization or ends, calling `GameManager.reset_state()` or `GameManager.reset_to_menu()`.
  Lines 133-141:
  ```gdscript
  func reset_state() -> void:
      current_state = GameState.MENU
      previous_state = GameState.MENU
      state_payload.clear()
      is_transitioning = false
  ```
  Neither `state_changed` nor `EventBus.game_state_changed` is emitted.
- **Blast Radius**:
  The HUD, combat arena, audio BGM, and WebSocket client remain in combat/cerco state while the internal state is MENU.
- **Empirical Verification**:
  Verified in `test_gm_reset_state_does_not_emit_signals`.
- **Mitigation**:
  Either call `change_state(GameState.MENU)` inside `reset_state()`, or emit a dedicated `game_reset` signal on `EventBus`.

---

### Challenge 5 [MEDIUM]: EventBus.emit_logged Argument Limit & Ghost Telemetry
- **Assumption Challenged**: `emit_logged` safely dispatches any valid signal and provides accurate telemetry.
- **Attack Scenario**:
  1. `emit_logged()` uses a `match args.size():` block with cases from 0 to 6. If a signal has 7 arguments or if 7 arguments are passed, the signal is silently dropped.
  2. Calling `emit_logged("ghost_signal", [])` increments `_emission_counts["ghost_signal"]` and logs to `_event_history` even when `has_signal(sig_name)` is `false`.
- **Blast Radius**:
  Tests or monitoring relying on `get_emission_count()` will report that signals were emitted when they were not. Future signals with 7+ arguments will fail silently.
- **Empirical Verification**:
  Verified in `test_eb_emit_logged_argument_count_limit` and `test_eb_emit_logged_nonexistent_signal`.
- **Mitigation**:
  1. Check `has_signal(sig_name)` before incrementing counters or history.
  2. Use `Callable(self, sig_name).callv(args)` or handle default cases instead of hardcoded 0..6 pattern matching.

---

### Challenge 6 [LOW]: False-Positive Assertions in `test_autoloads.gd`
- **Assumption Challenged**: All 44 tests in `test_autoloads.gd` validate valid FSM flows.
- **Attack Scenario**:
  In `test_game_manager_rapid_sequential_transitions`:
  ```gdscript
  var states = [
      _gm.GameState.COMBATE_TATICO,
      _gm.GameState.CERCO_ISECTUM,    # INVALID: COMBATE_TATICO -> CERCO_ISECTUM
      _gm.GameState.MULTIPLAYER_LOBBY,# INVALID: COMBATE_TATICO -> MULTIPLAYER_LOBBY
      _gm.GameState.FIM_DE_JOGO,      # VALID: COMBATE_TATICO -> FIM_DE_JOGO
      _gm.GameState.MENU              # VALID: FIM_DE_JOGO -> MENU
  ]
  for s in states:
      _gm.change_state(s) # Return value ignored!
  assert_eq(_gm.current_state, _gm.GameState.MENU)
  assert_eq(_gm.previous_state, _gm.GameState.FIM_DE_JOGO)
  ```
  The test attempted 2 illegal transitions that generated engine warnings and failed internally. The test passed only because the final transition happened to be valid, masking the fact that transitions 2 and 3 failed completely.
- **Mitigation**:
  Assert the boolean return value of every `change_state()` call in `test_autoloads.gd`.

---

## 3. Stress Test Results Summary

Suite: `res://test/unit/test_fsm_signals_stress.gd`  
Executed via: `./bin/godot --headless -s addons/gut/gut_cmdln.gd -gexit`

| # | Test Name | Scenario / Stress Dimension | Expected Behavior | Actual Behavior | Result |
|---|---|---|---|---|---|
| 1 | `test_gm_exhaustive_transition_matrix` | All 25 pairs in 5x5 state space | Only valid transitions succeed; invalid transitions return false without state change | Exactly matches `VALID_TRANSITIONS` specification | **PASS** |
| 2 | `test_gm_out_of_bounds_states` | States: -1000, -1, 5, 6, 99, 999999 | Rejected cleanly with false return | Returns false, state remains MENU | **PASS** |
| 3 | `test_gm_high_frequency_state_cycling` | 750 rapid sequential transitions | Zero memory leak, final state matches exactly | Completed 750 cycles with 100% state consistency | **PASS** |
| 4 | `test_gm_payload_aliasing_and_mutability` | External mutation of payload dictionary | Documented finding: caller mutations affect `state_payload` | Stored payload aliased to caller dict | **PASS (Finding Confirmed)** |
| 5 | `test_gm_extreme_payload_handling` | 10k string, nulls, depth 20 dict, INT64_MIN | Handled without crash or corruption | Payload stored and retrieved intact | **PASS** |
| 6 | `test_gm_reentrant_state_change_from_signal` | Listener triggers secondary transition | State completes at target, no lockup | Ends at FIM_DE_JOGO, but uncovers signal inversion | **PASS** |
| 7 | `test_gm_is_transitioning_guard_audit` | Call transition with `is_transitioning = true` | Should block if guarded | Not blocked; proves `is_transitioning` is dead variable | **PASS (Finding Confirmed)** |
| 8 | `test_gm_reset_state_does_not_emit_signals` | Call `reset_state()` from combat | Verify if signal is emitted | No signal emitted; proves silent state mutation | **PASS (Finding Confirmed)** |
| 9 | `test_eb_high_throughput_burst` | 10,000 signals emitted in single frame | 10,000 received with 0 drops | Exactly 10,000 received, zero drops | **PASS** |
| 10 | `test_eb_multi_subscriber_fanout` | 50 subscribers x 100 signals (5,000 calls) | All 50 receive all 100 signals | Exactly 5,000 deliveries recorded | **PASS** |
| 11 | `test_eb_subscriber_self_disconnect_during_callback` | Listener disconnects itself during emission | Exactly 1 call executed | 1 call executed, clean disconnect | **PASS** |
| 12 | `test_eb_peer_disconnect_during_emission` | Subscriber A disconnects Subscriber B during dispatch | B receives <=1 call, 0 on subsequent | Safe dispatch, no crash or corrupted iterator | **PASS** |
| 13 | `test_eb_recursive_bounded_reentrancy` | Signal handler emits same signal up to depth 10 | Recursion terminates cleanly at depth 10 | Reached depth 10 without stack overflow | **PASS** |
| 14 | `test_eb_cross_signal_cascading` | `unit_damaged` triggers `unit_died` | Clean cascading signal propagation | Triggered `unit_died` on fatal damage | **PASS** |
| 15 | `test_eb_extreme_and_boundary_payloads` | INT32 min/max Vector2i, INT64 max damage, 500-key dict | Handled without crash or truncation | All extreme payloads safely transmitted | **PASS** |
| 16 | `test_eb_emit_logged_telemetry_ring_buffer` | 150 logged events | Capped at `MAX_HISTORY = 100`, FIFO eviction | Size capped at 100, oldest evicted | **PASS** |
| 17 | `test_eb_emit_logged_nonexistent_signal` | Call `emit_logged` for unregistered signal | Handled without engine crash | Increments count despite non-existence | **PASS (Finding Confirmed)** |
| 18 | `test_eb_emit_logged_argument_count_limit` | Call `emit_logged` with 7 arguments | Handled safely without crash | Match exhausted, emission skipped | **PASS (Finding Confirmed)** |
| 19 | `test_gm_eventbus_reentrant_state_desynchronization` | Re-entrant transition during `state_changed` | Audits EventBus signal sequence | EventBus receives inverted & illegal `[MENU, FIM_DE_JOGO]` | **PASS (Defect Confirmed)** |
| 20 | `test_eb_telemetry_history_aliasing_audit` | Mutate argument dict after `emit_logged` | Audits telemetry history isolation | History corrupted retroactively | **PASS (Defect Confirmed)** |

---

## 4. Unchallenged Areas

1. **Scene File Transitions (`change_state_and_scene`)**:
   Scene files (`Menu.tscn`, `Main.tscn`, etc.) are not yet implemented in Milestone M1 (`headless_test_mode = true`). Integration with `get_tree().change_scene_to_file()` could not be tested against real packed scenes.
2. **Multi-Threaded Signal Emission**:
   GDScript signals were tested on the main game loop thread. Signal emissions across Godot worker threads (`WorkerThreadPool` or custom `Thread`) were not evaluated as the game loop is single-threaded in M1.

# Challenger Adversarial Report: Milestone 6 (WebSocketClient & Network Resilience)

**Agent**: `m6_challenger_2` (EMPIRICAL CHALLENGER / Critic / Specialist)  
**Date**: 2026-10-01  
**Target Module**: `godot_project/scripts/network/WebSocketClient.gd`  
**Test Suite Created**: `godot_project/test/unit/test_websocket_adversarial.gd`  
**Definitive Verdict**: **`APPROVE`**  

---

## Challenge Summary

- **Overall risk assessment**: **LOW**
- **Test Executions**:
  - `test_websocket_client.gd` (Worker): 47 tests, 121 assertions — 100% PASS
  - `test_websocket_adversarial.gd` (Challenger 2): 15 tests, 120 assertions — 100% PASS
  - `test_websocket_stress_adversarial.gd` (Challenger 1): 22 tests, 294 assertions — 100% PASS
  - Total full suite (`run_gut_tests.sh`): 15 scripts, 463 tests, 3564 assertions — 100% PASS (Exit code: 0)
  - Memory integrity: **0 ObjectDB memory leaks** under Godot 4.7.2 headless verbose execution.

The implementation in `godot_project/scripts/network/WebSocketClient.gd` demonstrates exceptional resilience, robust architectural encapsulation, defensive input validation, proper anti-cheat data isolation, and clean offline testability via peer dependency injection.

---

## Empirical Challenge Dimensions & Findings

### [Low] Challenge 1: Heterogeneous / Non-String Primitives in Optional Payload Metadata
- **Assumption challenged**: That incoming JSON dictionary payloads for events like `COMBAT_LOG` or `CHAT_MESSAGE` will always contain strings for optional visual metadata (`cor`, `autor`, `texto`).
- **Attack scenario**: An adversarial or buggy server sends numeric or float primitives in visual metadata fields (e.g. `{"cor": 9999, "autor": 123}`).
- **Empirical observation**: In `WebSocketClient._dispatch_message` (lines 413-415):
  ```gdscript
  var cor: String = payload.get("cor", "#cbd5e1")
  var autor: String = payload.get("autor", "LOG")
  var txt: String = payload.get("texto", "")
  ```
  GDScript static typing logs a runtime script warning/error: `Trying to assign value of type 'float' to a variable of type 'String'`. The client does not crash and test suites pass, but the dispatch block for that specific event may be interrupted.
- **Blast radius**: Isolated to individual log or chat message formatting if the backend violates protocol types.
- **Mitigation (Hardening Recommendation)**: Coerce metadata safely via `str(payload.get("cor", "#cbd5e1"))` or validate `if payload.get("cor") is String:`.

---

### [Low] Challenge 2: Corrupted Non-UTF8 Raw Byte Injection
- **Assumption challenged**: That receiving corrupted binary packets or invalid UTF-8 byte sequences (e.g. `[0xFF, 0xFE, 0xFD]`) might cause engine-level decoding crashes or unhandled exceptions in the packet processing loop.
- **Attack scenario**: Injecting invalid leading and continuation byte combinations directly into the socket buffer.
- **Empirical observation**: Godot's `get_string_from_utf8()` handles invalid byte sequences safely by replacing unparseable bytes with Unicode replacement character `` (U+FFFD). The resulting string is subsequently rejected by `JSON.parse()`, safely emitting `protocol_error` without terminating the process or corrupting internal state.
- **Stress Test**: `test_adversarial_corrupt_non_utf8_binary_frame_injection` & `test_adversarial_mixed_corrupt_and_valid_packet_interleaving`.
- **Result**: PASS (0 crashes, exact signal emissions).

---

### [Low] Challenge 3: Anti-Cheat Hand Privacy & State Mutation
- **Assumption challenged**: That querying or mutating the client's cached game state (`get_last_state()`) could accidentally mutate internal state or expose opponent cards.
- **Attack scenario**:
  1. Server sends `STATE_UPDATE` according to `src/server/session.py` (lines 575–577), where local player has `is_me = true` with full hand array, and opponents have `is_me = false` with empty hand array `[]`.
  2. A local HUD or script obtains `get_last_state()` and attempts to tamper with the array in-place or insert fraudulent cards.
- **Empirical observation**: `WebSocketClient.gd` stores `_last_received_state = payload.duplicate(true)` and `get_last_state()` returns a deep duplicate via `_last_received_state.duplicate(true)`. In-place mutations to the returned dictionary have zero effect on internal state, preserving strict integrity.
- **Stress Test**: `test_adversarial_anti_cheat_state_mutation_isolation` & `test_adversarial_anti_cheat_multi_player_privacy_enforcement`.
- **Result**: PASS.

---

### [Low] Challenge 4: Mid-Game Sudden Socket Loss & Backoff Progression
- **Assumption challenged**: That an abnormal network disconnect (`code 1006`) mid-game could discard current state, loop indefinitely, or fail to recover on reconnect.
- **Attack scenario**: A socket collapse occurs while the client is in `ACAO_LIVRE` at Round 4. The client is subjected to consecutive reconnection failures before restoring the socket.
- **Empirical observation**:
  - The client transitions immediately to `ConnectionState.RECONNECTING`.
  - The cached `_last_received_state` is preserved throughout the outage.
  - Backoff progression follows:
    - Attempt 1: 1.0s
    - Attempt 2: 2.0s
    - Attempt 3: 4.0s
    - Attempt 4: 8.0s (or capped at `reconnect_max_delay`)
  - Once maximum attempts are exceeded, `reconnect_failed` is emitted and state transitions cleanly to `DISCONNECTED`.
  - If the socket re-establishes, `reconnected` signal is emitted, `reconnect_attempts` resets to 0, and subsequent authoritative `STATE_UPDATE` packets resume gameplay seamlessly.
- **Stress Test**: `test_adversarial_midgame_disconnect_preserves_state_and_reconnects` & `test_adversarial_exponential_backoff_timing_progression`.
- **Result**: PASS.

---

### [Low] Challenge 5: Concurrent Calls to Send Methods in Invalid States
- **Assumption challenged**: That calling `send_*` methods when the client is in `CONNECTING`, `RECONNECTING`, `CLOSING`, or `DISCONNECTED` states might enqueue ghost packets, corrupt buffers, or crash if `_peer` is null.
- **Attack scenario**: Calling all 10 transmission methods across each non-connected state, calling with null `_peer`, simulating underlying buffer saturation (`ERR_UNAVAILABLE`), and firing a 50-packet burst in `CONNECTED` state.
- **Empirical observation**: All send methods guard against invalid states with:
  ```gdscript
  if _connection_state != ConnectionState.CONNECTED or _peer == null:
      return ERR_UNCONFIGURED
  ```
  And coordinate/string bounds checking returns `ERR_INVALID_PARAMETER` before any packet is framed. Rapid-fire packets in `CONNECTED` state are delivered in strict FIFO order without packet loss.
- **Stress Test**: `test_adversarial_send_calls_rejected_during_connecting_state`, `test_adversarial_send_calls_rejected_during_reconnecting_state`, `test_adversarial_send_when_peer_fails_with_buffer_full`, `test_adversarial_concurrent_rapid_fire_packet_burst`, `test_adversarial_send_with_null_peer_safe`.
- **Result**: PASS.

---

## Stress Test Results Matrix

| Scenario / Test Case | Expected Behavior | Actual Behavior | Result |
|---|---|---|---|
| `test_adversarial_midgame_disconnect_preserves_state_and_reconnects` | State preserved during drop, auto-reconnects, accepts new state | Round 4 retained, reconnected emitted, updated to Round 5 | **PASS** |
| `test_adversarial_exponential_backoff_timing_progression` | Delays progress: 1.0s, 2.0s, 4.0s, 8.0s, then reconnect_failed | Exact sequence observed and validated | **PASS** |
| `test_adversarial_reconnect_capping_at_max_delay` | Delay caps at `reconnect_max_delay` (3.0s) | Delay capped at 3.0s | **PASS** |
| `test_adversarial_anti_cheat_state_mutation_isolation` | Mutating `get_last_state()` does not mutate internal cache | Deep duplicate prevents mutation leak | **PASS** |
| `test_adversarial_anti_cheat_multi_player_privacy_enforcement` | Opponent hands hidden `[]`, local hand visible | Opponent hands empty, local hand intact | **PASS** |
| `test_adversarial_send_calls_rejected_during_connecting_state` | All 10 send methods return `ERR_UNCONFIGURED` | All 10 returned `ERR_UNCONFIGURED` | **PASS** |
| `test_adversarial_send_calls_rejected_during_reconnecting_state` | Send calls blocked in `RECONNECTING` | Blocked, returned `ERR_UNCONFIGURED` | **PASS** |
| `test_adversarial_send_when_peer_fails_with_buffer_full` | Propagates underlying peer error code | Returned `ERR_UNAVAILABLE` | **PASS** |
| `test_adversarial_concurrent_rapid_fire_packet_burst` | 50 rapid sends queued and transmitted in FIFO order | 50/50 transmitted in exact order | **PASS** |
| `test_adversarial_send_with_null_peer_safe` | Null peer handled gracefully without crash | Returned `ERR_UNCONFIGURED` safely | **PASS** |
| `test_adversarial_corrupt_non_utf8_binary_frame_injection` | Corrupted byte frame does not crash; emits protocol_error | Emitted `protocol_error`, 0 crashes | **PASS** |
| `test_adversarial_truncated_json_payload_triggers_protocol_error` | Truncated JSON emits `protocol_error` | Emitted `protocol_error`, 0 crashes | **PASS** |
| `test_adversarial_payload_with_null_and_unexpected_types` | Null/non-dict payload coerced safely to `{}` | Sanitized to `{}`, emitted `packet_received` | **PASS** |
| `test_adversarial_extreme_payload_size_and_special_characters` | 100KB payload with emojis/BBCode ingested safely | Ingested and emitted signals cleanly | **PASS** |
| `test_adversarial_mixed_corrupt_and_valid_packet_interleaving` | Interleaved valid/corrupt packets processed accurately | 3 valid processed, 3 protocol errors logged | **PASS** |

---

## Unchallenged Areas

- **Live TLS Certificate Validation over Internet Sockets**: Untested in live external network conditions because the project's testing architecture is strictly isolated offline via headless GUT mocks to prevent flaky network dependencies and comply with test isolation constraints.

---

## Conclusion & Verdict

The network client implementation satisfies all requirements under stress:
1. **Mid-game disconnection**: Seamlessly handles socket drops, preserves game state, and transitions through exponential backoff.
2. **Anti-cheat privacy**: Strictly enforces hand hiding for remote peers and mutation isolation for cached state updates.
3. **Concurrent state transitions**: Rejects transmissions across all non-connected states with `ERR_UNCONFIGURED` and delivers ordered bursts in connected state.
4. **Corrupted frame injection**: Decodes and sanitizes corrupt binary/UTF-8 frames without crashing or leaking memory.
5. **Memory integrity**: 0 ObjectDB memory leaks across 463 tests.

**Definitive Verdict: `APPROVE`**.

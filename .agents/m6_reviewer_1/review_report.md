# Milestone 6 Review & Adversarial Audit Report

**Reviewer**: `m6_reviewer_1` (Reviewer & Adversarial Critic)  
**Target Delivery**: Milestone 6 — `WebSocketClient.gd` & `test_websocket_client.gd`  
**Date**: 2026-10-01  
**Project**: Cerco da Fortaleza contra Isectum (Godot Engine 4)  

---

## 1. Review Summary

**Verdict**: **APPROVE**  
**Integrity Status**: **CLEAN (No integrity violations detected)**  
**Overall Risk Assessment**: **LOW**

The implementation of `godot_project/scripts/network/WebSocketClient.gd` and its companion test harness `godot_project/test/unit/test_websocket_client.gd` demonstrates exemplary code quality, rigorous adherence to GDScript static typing, full protocol parity with the authoritative FastAPI server (`src/server/protocol.py`, `src/server/app.py`, `src/server/room_manager.py`), clean separation of concerns via dependency injection (`set_peer`), and flawless integration with the global autoload singletons (`EventBus`, `GameManager`).

The test suite of 47 isolated unit tests executes offline in headless Godot 4 in ~10ms, achieving a 100% pass rate with zero ObjectDB memory leaks, followed by 100% pass rate across the full 13-suite regression test runner (426/426 tests passed, 3150 assertions).

---

## 2. Integrity Audit (Anti-Cheating & Facade Check)

| Integrity Dimension | Evaluation | Evidence |
|---|---|---|
| **Hardcoded Test Outputs** | NONE | Source code contains no test-specific bypasses, hardcoded strings, or mocked responses. |
| **Dummy / Facade Logic** | NONE | Complete real socket lifecycle handling, framing, buffer decoding, envelope parsing, exponential backoff, and signal emissions. |
| **Task Shortcuts** | NONE | Custom `MockWebSocketPeer` extends `RefCounted` and accurately reproduces Godot 4 `WebSocketPeer` states, packet queues, and error injection. |
| **Fabricated Verification** | NONE | Test commands independently executed via CLI; exit code 0 and assertion counts independently verified. |
| **Self-Certification** | NONE | Independent verification confirms 47 tests passed in isolation and 426 tests passed in full suite without regression. |

---

## 3. Findings

### [Minor] Finding 1: TLS Certificate Verification Mode (`TLSOptions.client_unsafe()`)
- **What**: When connecting with `use_tls = true`, the client unconditionally instantiates `TLSOptions.client_unsafe()`.
- **Where**: `godot_project/scripts/network/WebSocketClient.gd:237`
- **Why**: `client_unsafe()` disables peer TLS verification, which is ideal for local development or self-signed development certificates, but in production against public domains with valid CA certificates, `TLSOptions.client()` would provide stronger cryptographic guarantees against MITM attacks.
- **Suggestion**: In a future deployment configuration phase, expose an `@export var tls_verify: bool = false` property to allow toggling strict verification for production servers.
- **Risk Level**: Low (acceptable for current development/LAN co-op milestone).

### [Minor] Finding 2: Unbounded Ingestion Loop per Poll Tick
- **What**: In `_process_incoming_packets()`, a `while` loop drains all packets returned by `_peer.get_available_packet_count()`.
- **Where**: `godot_project/scripts/network/WebSocketClient.gd:357`
- **Why**: If a malicious or runaway server/proxy injects tens of thousands of packets in a single frame, processing them synchronously in one tick could cause a noticeable framerate dip.
- **Suggestion**: Consider introducing a configurable `const MAX_PACKETS_PER_POLL: int = 100` safeguard in future polish passes.
- **Risk Level**: Low (max 4 players per room with low-frequency tick updates).

---

## 4. Adversarial Challenges & Stress-Testing

### Challenge 1: Double-Connect in `RECONNECTING` State
- **Assumption Challenged**: Client prevents conflicting connections when already active.
- **Attack Scenario**: User code or UI button calls `connect_to_server()` while the client is waiting in `RECONNECTING` backoff.
- **Observation**: `connect_to_server()` checks `if _connection_state == ConnectionState.CONNECTED or _connection_state == ConnectionState.CONNECTING: return ERR_ALREADY_IN_USE`. When in `RECONNECTING`, it allows the call, overwriting `_last_url`, zeroing `reconnect_attempts`, setting `is_reconnecting = false`, and immediately calling `_do_connect()`.
- **Blast Radius**: None. The call effectively cancels the scheduled backoff and redirects to the newly specified endpoint, behaving as an intentional override.
- **Mitigation / Status**: Behavior is safe and deterministic.

### Challenge 2: Non-Dictionary or Corrupted Payload Envelopes
- **Assumption Challenged**: Server always provides a dictionary payload for incoming packets.
- **Attack Scenario**: Incoming packet JSON is valid syntax but `"payload"` is an integer, array, or null (e.g. `{"type": "PING", "payload": 123}`).
- **Observation**: Line 381 implements explicit type guarding:
  ```gdscript
  var payload: Dictionary = dict.get("payload", {}) if (dict.get("payload") is Dictionary) else {}
  ```
  If payload is not a Dictionary, it cleanly defaults to `{}` without throwing a GDScript type cast error or crashing the game.
- **Mitigation / Status**: Passed with flying colors.

### Challenge 3: Negative Coordinates and Board Boundary Flooding
- **Assumption Challenged**: Client enforces authoritative bounds before sending packets to the server.
- **Attack Scenario**: Client UI attempts to dispatch actions with negative coordinates (`-1`) or overflow grid indices (`20`, `999`).
- **Observation**: All typed action methods (`send_move_hero`, `send_attack_target`, `send_work_action`) explicitly validate:
  ```gdscript
  if dest_x < 0 or dest_x >= 20 or dest_y < 0 or dest_y >= 20:
      return ERR_INVALID_PARAMETER
  ```
  And `send_select_card` requires `card_idx >= -1` (permitting `-1` for card cancellation).
- **Mitigation / Status**: Pre-transmission filtering is robust and prevents invalid packets from reaching the network layer.

### Challenge 4: Anti-Cheat & Fog-of-War Card Privacy
- **Assumption Challenged**: Client state updates respect private hand masking.
- **Attack Scenario**: Inspect whether `WebSocketClient.gd` leaks or synthesizes other players' secret cards.
- **Observation**: Section 8 test `test_anti_cheat_hand_privacy_in_state_update` verifies that the client faithfully stores only what the authoritative server broadcasts (`session.to_dict(for_player_id=pid)`), keeping peer hands empty `[]` while preserving `cards_count`.
- **Mitigation / Status**: Perfectly conforms to authoritative server architecture.

---

## 5. Verified Claims

| Claim from Worker | Verification Method | Result |
|---|---|---|
| `WebSocketClient.gd` extends `Node` with discrete FSM | Inspected file structure lines 2-48 | **PASS** |
| Dependency Injection seam via `set_peer(Variant)` | Inspected lines 83-88, validated in unit tests | **PASS** |
| Implements 9 client message types from `protocol.py` | Cross-referenced against `protocol.py` and `app.py` | **PASS** |
| Bounds validation `[0, 19]` on movement, attack, work | Tested in section 5 unit tests and code inspection | **PASS** |
| Exponential backoff auto-reconnect on abnormal disconnects | Tested in section 7 unit tests (5 tests) | **PASS** |
| Clean disconnect (1000) does not trigger auto-reconnect | Verified in `test_auto_reconnect_does_not_trigger_on_clean_disconnect` | **PASS** |
| 47 unit tests pass with 0 failures in isolated run | Headless Godot runner CLI execution | **PASS** (47/47) |
| Full test suite passes with 0 failures across 13 suites | `run_gut_tests.sh` execution | **PASS** (426/426) |
| Zero ObjectDB memory leaks | GUT runner log inspection, no leak warnings | **PASS** (0 leaks) |

---

## 6. Coverage Gaps & Unverified Items

- **Coverage Gaps**: None. All functional requirements for Milestone 6 networking and unit testing are thoroughly covered.
- **Unverified Items**: None. Both isolated and full regression suites were executed independently.

---

## 7. Conclusion

The Milestone 6 deliverables meet all required standards:
- **Clean Architecture & SOLID**: Single responsibility, decoupled from native network sockets via DI, event-driven integration with EventBus.
- **GDScript Strict Typing**: Fully annotated signatures, properties, constants, and return types.
- **Reliability & Resilience**: Exponential backoff, defensive JSON ingestion, graceful handling of malformed frames.
- **Quality & Verification**: 100% test success rate, zero memory leaks, thorough AAA test coverage.

**Final Verdict**: **APPROVE**. Ready for integration and advancement to subsequent milestones.

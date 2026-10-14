# Handoff Report — m6_explorer_2

**Task**: GUT Testing Patterns, Zero-Leak Lifecycle & Mock Socket Strategy for `test_websocket_client.gd`  
**Date**: 2026-10-01T05:50:00Z  
**Author**: `m6_explorer_2` (Explorer)  
**Recipient**: `parent` (Orchestrator: `5dbb519a-f6c3-4b1f-b7e0-6ec494d60de9` / `f20fc092-e007-463e-91bf-9caf443e006b`)  
**Artifact**: `/home/anderson/Documents/projeto/RPG-battle/.agents/m6_explorer_2/test_strategy_report.md`

---

## 1. Observation

1. **GUT Architecture and Synchronous Execution**:
   - `godot_project/addons/gut/test.gd:88-97`:
     ```gdscript
     func autofree(node: Node) -> Node:
         if node != null and not _autofree_nodes.has(node):
             _autofree_nodes.append(node)
             if not node.is_inside_tree() and is_inside_tree():
                 add_child(node)
         return node

     func add_child_autofree(node: Node) -> Node:
         add_child(node)
         return autofree(node)
     ```
   - `godot_project/addons/gut/test.gd:65-73`:
     ```gdscript
     func _internal_after_each() -> void:
         for node in _autofree_nodes:
             if is_instance_valid(node):
                 if node.get_parent() != null:
                     node.get_parent().remove_child(node)
                 node.free()
         _autofree_nodes.clear()
     ```
   - `godot_project/addons/gut/gut_cmdln.gd:192-197`:
     ```gdscript
     test_instance.call(m_name)

     if test_instance.has_method("after_each"):
         test_instance.after_each()
     test_instance._internal_after_each()
     ```
     `test_instance.call(m_name)` runs synchronously. No test in the current repository uses `await` (grep search across `godot_project/test/unit/` returned 0 occurrences).
   - Running `./run_gut_tests.sh` executes 12 test suites, 379 tests, 3034 assertions, with 0 failures and 0 ObjectDB leaks in under 1 second.

2. **Network Layer Status**:
   - `godot_project/scripts/network/` is currently an empty directory.
   - Autoload `EventBus.gd:29-32` already exposes the required network relay signals:
     ```gdscript
     # ── Network Signals ─────────────────────────────────────────────────────────
     signal network_message_received(message_type: String, payload: Dictionary)
     signal network_connection_status_changed(connected: bool, room_id: String)
     ```
   - Autoload `GameManager.gd:14` includes `GameState.MULTIPLAYER_LOBBY` with valid transitions to/from `MENU`, `CERCO_ISECTUM`, and `COMBATE_TATICO`.

3. **Protocol and Server Contract**:
   - `src/server/protocol.py:14-35`: Defines canonical message types including `SELECT_HERO`, `SELECT_CARD`, `MOVE_HERO`, `ATTACK_TARGET`, `WORK_ACTION`, `START_GAME`, `END_ROUND`, `CHAT_MESSAGE`, `STATE_UPDATE`, `ACTION_REJECTED`, `COMBAT_LOG`.
   - `src/server/app.py:202-296`: Enforces websocket endpoint at `/ws/{room_id}/{player_id}?player_name={name}` and expects payload wrapping `{"type": str, "payload": dict}`.
   - `tests/test_coop_server.py:374-426`: Confirms server authority and step-by-step multiplayer synchrony flow.

---

## 2. Logic Chain

1. **Why Live Sockets Must Not Be Used**:
   - Based on Observation 1, the test runner is headless, offline, and runs tests synchronously.
   - Attempting to open real TCP connections in unit tests would introduce OS port conflicts, external process dependencies (FastAPI server), race conditions, and network latency that would break the deterministic <1ms test cycle.
   - Furthermore, simulating edge cases (malformed JSON strings, premature disconnects with specific close codes like 1006, server timeouts) on real sockets is unreliable and slow.

2. **Why MockWebSocketPeer (RefCounted) Guarantees Zero Leaks**:
   - In Godot 4, `WebSocketPeer` inherits from `PacketPeer` -> `RefCounted`.
   - Implementing `MockWebSocketPeer extends RefCounted` ensures that the mock socket is automatically collected by Godot's reference counter when the owning `WebSocketClient` or test reference is nulled.
   - The `WebSocketClient` itself inherits from `Node`. By wrapping every instantiation in `autofree(WebSocketClientScript.new())` inside `before_each()`, the GUT framework registers the instance in `_autofree_nodes` and automatically removes it from the tree and frees it via `node.free()` in `_internal_after_each()`.
   - This ensures a 100% leak-free ObjectDB lifecycle without manual error-prone cleanup.

3. **How Synchronous Testing with `poll()` Works**:
   - `WebSocketClient.gd` must expose a public `poll()` method that polls its injected peer.
   - Instead of waiting for asynchronous background frames, a GUT unit test:
     a) **Arranges** the state (enqueues simulated packets or alters `ready_state` on `MockWebSocketPeer`);
     b) **Acts** by calling `client.poll()` or `client.send_*()`;
     c) **Asserts** the resulting signal emissions or packet contents immediately.

---

## 3. Caveats

1. **Integration Testing vs Unit Testing**:
   - This specification covers offline unit testing with a mock peer. Full integration testing against a running FastAPI instance requires an external test runner script or separate integration harness outside of headless GUT.
2. **WebSocket TLS Verification**:
   - `TLSOptions` in Godot 4 are tested for URL formatting and client option passing, but actual certificate validation is bypassed in unit mock mode.
3. **No Direct Production Code Written**:
   - In compliance with the explorer archetype, no GDScript files were created in `godot_project/scripts/network/` or `godot_project/test/unit/`. All test case specifications, mock designs, and architectural blueprints are delivered in `.agents/m6_explorer_2/test_strategy_report.md`.

---

## 4. Conclusion

The testing strategy for `WebSocketClient.gd` is fully formulated and ready for implementation:
1. **Mock Harness**: `MockWebSocketPeer` (extending `RefCounted`) completely decouples `WebSocketClient` from real network sockets, providing deterministic packet injection, error simulation, and zero memory leaks.
2. **Test Suite Specification**: 35 concrete Arrange-Act-Assert test cases defined across 7 functional sections covering lifecycle, connection handshake, outgoing typed packets, incoming server events, adversarial JSON payloads, disconnects, and auto-reconnect backoff.
3. **EventBus Integration**: Full validation of signal propagation to `EventBus.network_message_received` and `EventBus.network_connection_status_changed`.

---

## 5. Verification Method

To verify the test strategy once implemented by the worker agent:

1. **Inspect Strategy Report**:
   ```bash
   cat /home/anderson/Documents/projeto/RPG-battle/.agents/m6_explorer_2/test_strategy_report.md
   ```

2. **Execute Headless GUT Test Suite**:
   ```bash
   /home/anderson/Documents/projeto/RPG-battle/godot_project/run_gut_tests.sh
   ```

3. **Targeted Execution of the WebSocket Suite**:
   ```bash
   /home/anderson/Documents/projeto/RPG-battle/godot_project/bin/godot --headless \
     --path /home/anderson/Documents/projeto/RPG-battle/godot_project \
     -s addons/gut/gut_cmdln.gd -gexit -gtest=res://test/unit/test_websocket_client.gd
   ```

4. **Invalidation Conditions**:
   - Any test requiring a live FastAPI process running on port 8000.
   - Any test leaving orphaned `Node` instances in the `ObjectDB`.
   - Any test failing to adhere to the Arrange-Act-Assert structure.

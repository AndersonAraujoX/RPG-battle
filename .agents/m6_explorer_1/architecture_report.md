# Architecture Report: Godot 4 WebSocketClient & Networking Engine

**Author**: `m6_explorer_1`  
**Milestone**: M6 (Multiplayer Client & WebSocket Architecture)  
**Target Component**: `godot_project/scripts/network/WebSocketClient.gd`  
**Status**: Ready for Implementation  
**Date**: 2026-10-01  

---

## 1. Executive Summary & Objective

This report establishes the complete architectural blueprint and design specification for the multiplayer network client in **Cerco da Fortaleza contra Isectum** (Godot 4). The game server operates as an authoritative FastAPI WebSocket application (`src/server/app.py`), orchestrating co-op tactical siege rounds, card synchronization, and swarm invasion logic.

The Godot 4 client must connect to the server endpoint `/ws/{room_id}/{player_id}?player_name={name}`, serialize typed game actions into canonical JSON frames, deserialize incoming server messages, dispatch events through the global `EventBus.gd`, and maintain connection resilience.

Crucially, the architecture must support **100% offline, deterministic unit testing via GUT** without requiring an active network socket or running server, while guaranteeing **zero ObjectDB memory leaks**.

---

## 2. Godot 4 `WebSocketPeer` Technical Analysis

### 2.1 Engine Evolution: Godot 3 vs Godot 4
In Godot 3, WebSocket communication relied on high-level `WebSocketClient` and `WebSocketServer` nodes with built-in signals (`connection_established`, `data_received`). In Godot 4, these nodes were removed entirely. Godot 4 introduces **`WebSocketPeer`**, a low-level, non-blocking packet peer:
- `WebSocketPeer` extends `PacketPeer` -> `RefCounted` -> `Object`. It is **not** a `Node`.
- It does **not** emit built-in signals for incoming packets or state changes.
- It relies entirely on explicit **polling** (`poll()`) to drive TCP I/O, TLS handshakes, ping/pong frames, and packet buffers.

### 2.2 Ready States & Lifecycle
`WebSocketPeer` defines four discrete states via `WebSocketPeer.State`:
```gdscript
enum State {
    STATE_CONNECTING = 0, # Handshake in progress
    STATE_OPEN = 1,       # Connection active, ready for I/O
    STATE_CLOSING = 2,    # Close frame sent/received, closing TCP
    STATE_CLOSED = 3      # Connection closed or failed to open
}
```

#### State Transition Semantics:
1. **Initiation (`connect_to_url`)**:
   - `var err: Error = peer.connect_to_url(url, tls_options)`
   - State becomes `STATE_CONNECTING`.
   - Returns `OK` if socket initialization started, or `ERR_INVALID_PARAMETER` / `ERR_CANT_CREATE`.
2. **Handshake Completion**:
   - Driven by successive calls to `peer.poll()`.
   - On HTTP 101 Switching Protocols, state transitions from `STATE_CONNECTING` to `STATE_OPEN`.
3. **Closing & Teardown**:
   - Clean shutdown: `peer.close(code, reason)`. Transitions to `STATE_CLOSING`, then `STATE_CLOSED`.
   - Abnormal disconnect (network drop, server reset): transitions directly to `STATE_CLOSED`.
   - Close diagnostics:
     - `peer.get_close_code() -> int` (e.g., 1000 = Normal Closure, 1001 = Going Away, 1006 = Abnormal / TCP reset).
     - `peer.get_close_reason() -> String` (human-readable string sent in close frame).

### 2.3 Buffer & Packet Handling
- **Packet Ingestion**:
  ```gdscript
  while peer.get_available_packet_count() > 0:
      var packet: PackedByteArray = peer.get_packet()
      if peer.was_string_packet():
          var text: String = packet.get_string_from_utf8()
          # Parse JSON and dispatch
  ```
- **Packet Egress**:
  - Godot 4 provides `peer.send_text(string: String) -> Error`. This is the preferred, type-safe API for JSON text frames.
  - Alternatively: `peer.put_packet(string.to_utf8_buffer())` (with `set_write_mode(WRITE_MODE_TEXT)`).
- **Buffer Configurations**:
  - `peer.inbound_buffer_size = 65536` (64 KB)
  - `peer.outbound_buffer_size = 65536` (64 KB)
  - `peer.max_queued_packets = 2048`
- **TLS Configuration**:
  - Insecure WebSocket (`ws://`): pass `null` for `tls_client_options`.
  - Secure WebSocket (`wss://`): pass `TLSOptions.client()` or `TLSOptions.client_unsafe()` (for self-signed certs in development).

---

## 3. `WebSocketClient.gd` Component Architecture

### 3.1 Inheritance & Scene Lifecycle
`WebSocketClient.gd` is designed as a **`Node`**:
```gdscript
class_name WebSocketClient
extends Node
```
- **Why `Node`?**
  1. Integrates with Godot's frame execution via `_process(delta)`.
  2. Can be mounted into scenes (e.g. `Lobby.tscn`, `FortressBoard.tscn`) or registered as a dynamic child node.
  3. Controls polling activity via `set_process(true/false)`, preventing wasteful CPU cycles when disconnected.
  4. Can also be instantiated dynamically in GUT unit tests (`autofree(WebSocketClient.new())`) and stepped deterministically using a public `poll()` method.

### 3.2 Internal Connection State Machine
To handle transitions, timeouts, and reconnects robustly, `WebSocketClient` implements an explicit internal state machine:

```
[DISCONNECTED] ───────── connect_to_server() ────────► [CONNECTING]
       ▲                                                     │
       │                                            handshake success
       │                                                     ▼
 [RECONNECTING] ◄──── unexpected drop / retry ───────── [CONNECTED]
       │                                                     │
max retries / manual disconnect               disconnect_from_server()
       │                                                     ▼
       └──────────────────────────────────────────────► [CLOSING]
                                                             │
                                                        peer closed
                                                             ▼
                                                       [DISCONNECTED]
```

#### Connection States (`enum ClientConnectionState`):
- `DISCONNECTED`: Idle, no peer active. `_process` is paused.
- `CONNECTING`: `connect_to_url` executed. Polling active. Connection timeout timer running.
- `CONNECTED`: Handshake complete (`peer.get_ready_state() == STATE_OPEN`). Ready to transmit/receive.
- `CLOSING`: Client requested close (`peer.close()`). Waiting for peer to reach `STATE_CLOSED`.
- `RECONNECTING`: Connection lost unexpectedly; waiting on backoff timer before initiating next attempt.

### 3.3 Signals Specification
`WebSocketClient` emits fine-grained, strongly-typed local signals and forwards relevant messages to `EventBus.gd`:

#### Local Signals:
```gdscript
## Connection lifecycle
signal connected_to_server(room_id: String, player_id: String)
signal connection_closed(code: int, reason: String)
signal connection_error(error_message: String)
signal state_changed(old_state: int, new_state: int)
signal reconnect_attempt(current_attempt: int, max_attempts: int, delay_seconds: float)
signal reconnect_failed()

## Wire message events
signal message_received(message_type: String, payload: Dictionary)
signal state_update_received(game_state: Dictionary)
signal action_rejected(action: String, reason: String)
signal server_error(error_message: String)
signal chat_received(author: String, text: String, color: String)
```

#### EventBus Integration:
Upon receiving messages, `WebSocketClient` triggers:
- `EventBus.network_connection_status_changed.emit(true/false, room_id)`
- `EventBus.network_message_received.emit(message_type, payload)`
- If `action_rejected`: `EventBus.combat_log_entry_added.emit("[color=#ef4444]⚠️ %s: %s[/color]" % [action, reason])`
- If `chat_received`: `EventBus.combat_log_entry_added.emit("[color=%s]%s: %s[/color]" % [color, author, text])`

---

## 4. Typed Send Methods & Wire Protocol

The FastAPI server (`src/server/protocol.py`) enforces strict JSON envelopes:
```json
{
  "type": "<MESSAGE_TYPE>",
  "payload": { ... }
}
```

### 4.1 Complete Protocol Inventory (All 17 MessageTypes)

#### Client -> Server Message Types:
| Method Signature | MessageType | Payload Schema | Description |
|------------------|-------------|----------------|-------------|
| `send_join_room(room_id: String, player_name: String) -> Error` | `JOIN_ROOM` | `{"room_id": room_id, "player_name": player_name}` | Explicit lobby join frame (complements URL query handshake) |
| `send_select_hero(hero_name: String) -> Error` | `SELECT_HERO` | `{"hero_name": hero_name}` | Selects hero character in lobby |
| `send_start_game() -> Error` | `START_GAME` | `{}` | Host requests transition to game start |
| `send_select_card(card_idx: int) -> Error` | `SELECT_CARD` | `{"card_idx": card_idx}` | Locks in card during Synchrony phase |
| `send_move_hero(dest_x: int, dest_y: int) -> Error` | `MOVE_HERO` | `{"dest_x": dest_x, "dest_y": dest_y}` | Free action: move hero on 20x20 grid |
| `send_attack_target(tx: int, ty: int, skill: String = "") -> Error` | `ATTACK_TARGET` | `{"target_x": tx, "target_y": ty, "habilidade": skill}` | Free action: attack enemy or structure |
| `send_work_action(tx: int, ty: int, kind: String = "minerar") -> Error` | `WORK_ACTION` | `{"target_x": tx, "target_y": ty, "tipo": kind}` | Free action: mine rock / repair wall |
| `send_end_round() -> Error` | `END_ROUND` | `{}` | Declares player has finished free actions |
| `send_chat(text: String) -> Error` | `CHAT_MESSAGE` | `{"text": text}` | Sends chat message to room |
| `send_ping() -> Error` | `PING` | `{"timestamp": Time.get_ticks_msec()}` | Client heartbeat / latency check |

#### Server -> Client Message Types:
| Server MessageType | Expected Payload Structure | Client Reaction / Signal |
|--------------------|----------------------------|--------------------------|
| `STATE_UPDATE` | Full game state (`fase`, `round`, `heroes`, `enemies`, `recursos`, `combat_log`) | Emits `state_update_received(payload)`, caches state, updates UI |
| `ROOM_STATE` | Lobby player list & readiness (`players`, `fase`, `room_id`) | Emits `room_state_received(payload)`, updates lobby roster |
| `GAME_STARTED` | `{}` or match initialization payload | Notifies `GameManager` to transition from `MULTIPLAYER_LOBBY` to `CERCO_ISECTUM` |
| `CARD_LOCKED` | `{"player_id": id, "locked": true}` | Highlights that teammate selected their card in HUD |
| `ROUND_RESOLVED` | `{"round_number": num, "sync_results": dict}` | Triggers `EventBus.round_resolved` and synchrony combo animation |
| `COMBAT_LOG` | `{"autor": author, "texto": text, "cor": color}` | Appends formatted entry to `EventBus.combat_log_entry_added` |
| `ACTION_REJECTED` | `{"acao": action, "motivo": reason}` | Emits `action_rejected(action, reason)`, displays warning banner |
| `ERROR` | `{"mensagem": error_str}` | Emits `server_error(error_str)`, displays alert modal |

### Parameter Validation & Guards:
Every typed method executes defensive checks before serializing:
1. **Connection Guard**: If `_connection_state != ClientConnectionState.CONNECTED`, the method returns `ERR_UNCONFIGURED` and does not attempt transmission.
2. **Range / Boundary Validation**:
   - `dest_x`, `dest_y`, `target_x`, `target_y` must be within `[0, 19]`.
   - `card_idx` must be `>= 0` (or `-1` to deselect).
   - `hero_name` and `text` must not be empty.
   - If invalid, returns `ERR_INVALID_PARAMETER` and logs a warning.

---

## 5. Resilience & Reconnection Strategy

### 5.1 Reconnection Policy
Network blips and temporary disconnects must not crash or leave the client stranded.
- **Configurable Properties**:
  - `auto_reconnect: bool = true`
  - `reconnect_initial_delay: float = 1.0`
  - `reconnect_max_delay: float = 30.0`
  - `reconnect_multiplier: float = 2.0`
  - `reconnect_jitter: float = 0.25` (avoids synchronized reconnect stampedes)
  - `max_reconnect_attempts: int = 5`

### 5.2 Backoff Algorithm
When an abnormal disconnect occurs (`close_code != 1000` and `auto_reconnect == true`):
```gdscript
func _schedule_reconnect() -> void:
    if _reconnect_attempts >= max_reconnect_attempts:
        _set_state(ClientConnectionState.DISCONNECTED)
        reconnect_failed.emit()
        return

    _reconnect_attempts += 1
    var base_delay: float = min(reconnect_max_delay, reconnect_initial_delay * pow(reconnect_multiplier, _reconnect_attempts - 1))
    var jitter: float = randf_range(-reconnect_jitter, reconnect_jitter) * base_delay
    var actual_delay: float = max(0.5, base_delay + jitter)

    _set_state(ClientConnectionState.RECONNECTING)
    reconnect_attempt.emit(_reconnect_attempts, max_reconnect_attempts, actual_delay)
    _reconnect_timer = actual_delay
```

### 5.3 State Resynchronization
Because the server session (`CoopSession`) is authoritative:
- When the client re-establishes connection to `/ws/{room_id}/{player_id}?player_name={name}`, the server recognizes `player_id`.
- The server automatically transmits a fresh `STATE_UPDATE` payload containing:
  - Current phase (`fase`: `LOBBY`, `SELECAO_CARTAS`, `ACAO_LIVRE`, etc.)
  - Current round, resources, heroes, enemies, and personal hand of cards.
- The client receives `STATE_UPDATE`, replaces its local cached state, and notifies `GameManager` and the UI, seamlessly restoring the match!

---

## 6. Dependency Injection & Offline Mocking Strategy

### 6.1 The Problem
In GUT headless tests (`godot --headless`), attempting network calls to real ports will either fail with `ERR_CANT_CONNECT`, hang the test process, or make tests flaky and dependent on external server state. Furthermore, Godot 4's `WebSocketPeer` is a C++ engine class; it cannot easily be partially mocked by subclassing.

### 6.2 The Solution: Peer Abstraction & Duck Typing
We define a formal contract that both `WebSocketPeer` and `MockWebSocketPeer` satisfy:

```gdscript
# Contract required by WebSocketClient:
- poll() -> void
- get_ready_state() -> int
- get_available_packet_count() -> int
- get_packet() -> PackedByteArray
- was_string_packet() -> bool
- send_text(text: String) -> Error
- close(code: int, reason: String) -> void
- get_close_code() -> int
- get_close_reason() -> String
- connect_to_url(url: String, tls_options: TLSOptions) -> Error
```

### 6.3 `MockWebSocketPeer` Implementation
A lightweight test double implemented in pure GDScript (either as a helper class or standalone test asset `res://test/unit/mock_websocket_peer.gd`):

```gdscript
class_name MockWebSocketPeer
extends RefCounted

var ready_state: int = 3 # STATE_CLOSED
var close_code: int = 1000
var close_reason: String = ""
var connected_url: String = ""

var _incoming_packets: Array[PackedByteArray] = []
var _was_string: Array[bool] = []
var _sent_packets: Array[String] = []

func connect_to_url(url: String, _tls: Variant = null) -> Error:
    connected_url = url
    ready_state = 0 # STATE_CONNECTING
    return OK

func poll() -> void:
    pass

func get_ready_state() -> int:
    return ready_state

func get_available_packet_count() -> int:
    return _incoming_packets.size()

func get_packet() -> PackedByteArray:
    if _incoming_packets.is_empty():
        return PackedByteArray()
    _was_string.pop_front()
    return _incoming_packets.pop_front()

func was_string_packet() -> bool:
    return true

func send_text(text: String) -> Error:
    if ready_state != 1: # STATE_OPEN
        return ERR_UNCONFIGURED
    _sent_packets.append(text)
    return OK

func close(code: int = 1000, reason: String = "") -> void:
    ready_state = 3 # STATE_CLOSED
    close_code = code
    close_reason = reason

func get_close_code() -> int:
    return close_code

func get_close_reason() -> String:
    return close_reason

# ── Test Harness Helpers ──────────────────────────────────────────────────────

func simulate_connected() -> void:
    ready_state = 1 # STATE_OPEN

func simulate_disconnect(code: int = 1006, reason: String = "Server dropped") -> void:
    ready_state = 3 # STATE_CLOSED
    close_code = code
    close_reason = reason

func inject_message(type: String, payload: Dictionary = {}) -> void:
    var json_str = JSON.stringify({"type": type, "payload": payload})
    _incoming_packets.append(json_str.to_utf8_buffer())
    _was_string.append(true)

func get_sent_packets() -> Array[String]:
    return _sent_packets.duplicate()

func get_last_sent_json() -> Dictionary:
    if _sent_packets.is_empty():
        return {}
    var res = JSON.parse_string(_sent_packets.back())
    return res if res is Dictionary else {}
```

### 6.4 Dependency Injection in `WebSocketClient`
`WebSocketClient` provides a clean injection seam:
```gdscript
## Inject custom peer for unit testing (MockWebSocketPeer)
func set_peer(peer_instance: Variant) -> void:
    _peer = peer_instance
```
In production, `WebSocketClient` instantiates `WebSocketPeer.new()`. In test suites, `set_peer(mock_peer)` is called immediately after instantiation.

---

## 7. Concrete GDScript Implementation Blueprint

Below is the production-ready GDScript architecture for `godot_project/scripts/network/WebSocketClient.gd`:

```gdscript
# res://scripts/network/WebSocketClient.gd
class_name WebSocketClient
extends Node

## Autoritativo WebSocket Client for Co-op Cerco contra Isectum.
## Communicates with FastAPI backend (/ws/{room_id}/{player_id}).

# ── Signals ──────────────────────────────────────────────────────────────────
signal connected_to_server(room_id: String, player_id: String)
signal connection_closed(code: int, reason: String)
signal connection_error(error_message: String)
signal state_changed(old_state: int, new_state: int)
signal reconnect_attempt(current_attempt: int, max_attempts: int, delay_seconds: float)
signal reconnect_failed()

signal message_received(message_type: String, payload: Dictionary)
signal state_update_received(game_state: Dictionary)
signal action_rejected(action: String, reason: String)
signal server_error(error_message: String)
signal chat_received(author: String, text: String, color: String)

# ── Connection State Enum ────────────────────────────────────────────────────
enum ConnectionState {
    DISCONNECTED = 0,
    CONNECTING = 1,
    CONNECTED = 2,
    CLOSING = 3,
    RECONNECTING = 4
}

# ── Configuration & Properties ───────────────────────────────────────────────
@export var server_url: String = "ws://127.0.0.1:8000"
@export var connect_timeout_seconds: float = 10.0
@export var auto_reconnect: bool = true
@export var max_reconnect_attempts: int = 5
@export var reconnect_initial_delay: float = 1.0
@export var reconnect_max_delay: float = 30.0
@export var reconnect_multiplier: float = 2.0
@export var debug_logging: bool = false

# ── Internal State ───────────────────────────────────────────────────────────
var _connection_state: ConnectionState = ConnectionState.DISCONNECTED
var _peer: Variant = null
var _room_id: String = ""
var _player_id: String = ""
var _player_name: String = "Aventureiro"
var _connect_timer: float = 0.0
var _reconnect_timer: float = 0.0
var _reconnect_attempts: int = 0
var _last_received_state: Dictionary = {}

func _init() -> void:
    name = "WebSocketClient"

func _ready() -> void:
    set_process(false)

# ── Public Injection & Peer Management ───────────────────────────────────────

## Injects custom peer instance (used by MockWebSocketPeer in GUT unit tests)
func set_peer(peer_instance: Variant) -> void:
    _peer = peer_instance

func get_connection_state() -> ConnectionState:
    return _connection_state

func is_connected_to_server() -> bool:
    return _connection_state == ConnectionState.CONNECTED

func get_last_state() -> Dictionary:
    return _last_received_state.duplicate(true)

# ── Connection Lifecycle ─────────────────────────────────────────────────────

func connect_to_room(room_id: String, player_id: String, player_name: String = "Aventureiro") -> Error:
    if _connection_state == ConnectionState.CONNECTED or _connection_state == ConnectionState.CONNECTING:
        push_warning("[WebSocketClient] Already connecting or connected.")
        return ERR_ALREADY_IN_USE

    _room_id = room_id.strip_edges().to_upper()
    _player_id = player_id.strip_edges()
    _player_name = player_name.strip_edges()
    _reconnect_attempts = 0

    return _initiate_connection()

func disconnect_from_server(code: int = 1000, reason: String = "Client disconnect") -> void:
    _reconnect_attempts = max_reconnect_attempts # Prevent auto-reconnect on intentional disconnect
    if _peer != null:
        _set_state(ConnectionState.CLOSING)
        _peer.close(code, reason)
    else:
        _set_state(ConnectionState.DISCONNECTED)

# ── Process & Polling ────────────────────────────────────────────────────────

func _process(delta: float) -> void:
    poll(delta)

## Explicit poll step, callable both by _process and synchronously in GUT tests
func poll(delta: float = 0.016) -> void:
    if _connection_state == ConnectionState.RECONNECTING:
        _reconnect_timer -= delta
        if _reconnect_timer <= 0.0:
            _initiate_connection()
        return

    if _peer == null:
        return

    _peer.poll()
    var ready_state: int = _peer.get_ready_state()

    match _connection_state:
        ConnectionState.CONNECTING:
            _connect_timer -= delta
            if ready_state == 1: # WebSocketPeer.STATE_OPEN
                _on_connected()
            elif ready_state == 3 or _connect_timer <= 0.0: # WebSocketPeer.STATE_CLOSED
                _on_connect_failed("Connection timed out or refused.")

        ConnectionState.CONNECTED:
            if ready_state == 1:
                _process_incoming_packets()
            elif ready_state == 3 or ready_state == 2:
                _on_connection_lost()

        ConnectionState.CLOSING:
            if ready_state == 3:
                _on_closed_cleanly()

# ── Internal Connection Helpers ──────────────────────────────────────────────

func _initiate_connection() -> Error:
    if _peer == null:
        _peer = WebSocketPeer.new()

    var full_url: String = "%s/ws/%s/%s?player_name=%s" % [
        server_url.trim_suffix("/"),
        _room_id,
        _player_id,
        _player_name.uri_encode()
    ]

    var err: Error = _peer.connect_to_url(full_url)
    if err != OK:
        connection_error.emit("Failed to connect to %s: code %d" % [full_url, err])
        _set_state(ConnectionState.DISCONNECTED)
        return err

    _connect_timer = connect_timeout_seconds
    _set_state(ConnectionState.CONNECTING)
    set_process(true)
    return OK

func _on_connected() -> void:
    _reconnect_attempts = 0
    _set_state(ConnectionState.CONNECTED)
    connected_to_server.emit(_room_id, _player_id)
    if has_node("/root/EventBus"):
        get_node("/root/EventBus").network_connection_status_changed.emit(true, _room_id)

func _on_connect_failed(reason: String) -> void:
    connection_error.emit(reason)
    _handle_disconnect_or_reconnect(1006, reason)

func _on_connection_lost() -> void:
    var code: int = _peer.get_close_code() if _peer.has_method("get_close_code") else 1006
    var reason: String = _peer.get_close_reason() if _peer.has_method("get_close_reason") else "Connection lost"
    _handle_disconnect_or_reconnect(code, reason)

func _on_closed_cleanly() -> void:
    var code: int = _peer.get_close_code() if _peer.has_method("get_close_code") else 1000
    var reason: String = _peer.get_close_reason() if _peer.has_method("get_close_reason") else "Clean close"
    _set_state(ConnectionState.DISCONNECTED)
    set_process(false)
    connection_closed.emit(code, reason)
    if has_node("/root/EventBus"):
        get_node("/root/EventBus").network_connection_status_changed.emit(false, _room_id)

func _handle_disconnect_or_reconnect(code: int, reason: String) -> void:
    connection_closed.emit(code, reason)
    if has_node("/root/EventBus"):
        get_node("/root/EventBus").network_connection_status_changed.emit(false, _room_id)

    if auto_reconnect and _reconnect_attempts < max_reconnect_attempts and code != 1000:
        _reconnect_attempts += 1
        var delay: float = min(reconnect_max_delay, reconnect_initial_delay * pow(reconnect_multiplier, _reconnect_attempts - 1))
        _reconnect_timer = delay
        _set_state(ConnectionState.RECONNECTING)
        reconnect_attempt.emit(_reconnect_attempts, max_reconnect_attempts, delay)
    else:
        _set_state(ConnectionState.DISCONNECTED)
        set_process(false)
        if _reconnect_attempts >= max_reconnect_attempts:
            reconnect_failed.emit()

func _set_state(new_state: ConnectionState) -> void:
    if _connection_state == new_state:
        return
    var old_state: ConnectionState = _connection_state
    _connection_state = new_state
    state_changed.emit(old_state, new_state)

# ── Incoming Message Processing ──────────────────────────────────────────────

func _process_incoming_packets() -> void:
    while _peer.get_available_packet_count() > 0:
        var packet: PackedByteArray = _peer.get_packet()
        var text: String = packet.get_string_from_utf8()
        if text.is_empty():
            continue

        var parsed: Variant = JSON.parse_string(text)
        if not (parsed is Dictionary):
            push_warning("[WebSocketClient] Received non-dictionary JSON: %s" % text)
            continue

        var msg: Dictionary = parsed as Dictionary
        var msg_type: String = msg.get("type", "")
        var payload: Dictionary = msg.get("payload", {})

        _dispatch_message(msg_type, payload)

func _dispatch_message(type: String, payload: Dictionary) -> void:
    message_received.emit(type, payload)

    if has_node("/root/EventBus"):
        get_node("/root/EventBus").network_message_received.emit(type, payload)

    match type:
        "STATE_UPDATE":
            _last_received_state = payload.duplicate(true)
            state_update_received.emit(payload)
        "ROOM_STATE":
            _last_received_state = payload.duplicate(true)
            state_update_received.emit(payload)
        "GAME_STARTED":
            if has_node("/root/GameManager"):
                get_node("/root/GameManager").change_state(2) # GameState.CERCO_ISECTUM
        "CARD_LOCKED":
            pass # UI highlights teammate card lock
        "ROUND_RESOLVED":
            if has_node("/root/EventBus"):
                get_node("/root/EventBus").round_resolved.emit(payload.get("round_number", 0), payload.get("sync_results", {}))
        "COMBAT_LOG":
            if has_node("/root/EventBus"):
                var cor: String = payload.get("cor", "#cbd5e1")
                var autor: String = payload.get("autor", "LOG")
                var txt: String = payload.get("texto", "")
                get_node("/root/EventBus").combat_log_entry_added.emit("[color=%s]%s: %s[/color]" % [cor, autor, txt])
        "ACTION_REJECTED":
            action_rejected.emit(payload.get("acao", ""), payload.get("motivo", ""))
            if has_node("/root/EventBus"):
                get_node("/root/EventBus").combat_log_entry_added.emit(
                    "[color=#ef4444]⚠️ %s: %s[/color]" % [payload.get("acao", ""), payload.get("motivo", "")]
                )
        "ERROR":
            server_error.emit(payload.get("mensagem", ""))
        "CHAT_MESSAGE":
            chat_received.emit(payload.get("autor", ""), payload.get("texto", ""), payload.get("cor", "#ffffff"))

# ── Typed Send Methods ───────────────────────────────────────────────────────

func send_message(type: String, payload: Dictionary = {}) -> Error:
    if _connection_state != ConnectionState.CONNECTED or _peer == null:
        push_warning("[WebSocketClient] Cannot send message: client is not connected.")
        return ERR_UNCONFIGURED

    var envelope: Dictionary = {
        "type": type,
        "payload": payload
    }
    var json_str: String = JSON.stringify(envelope)
    return _peer.send_text(json_str)

func send_select_hero(hero_name: String) -> Error:
    if hero_name.strip_edges().is_empty():
        return ERR_INVALID_PARAMETER
    return send_message("SELECT_HERO", {"hero_name": hero_name})

func send_start_game() -> Error:
    return send_message("START_GAME", {})

func send_select_card(card_idx: int) -> Error:
    if card_idx < -1:
        return ERR_INVALID_PARAMETER
    return send_message("SELECT_CARD", {"card_idx": card_idx})

func send_move_hero(dest_x: int, dest_y: int) -> Error:
    if dest_x < 0 or dest_x >= 20 or dest_y < 0 or dest_y >= 20:
        return ERR_INVALID_PARAMETER
    return send_message("MOVE_HERO", {"dest_x": dest_x, "dest_y": dest_y})

func send_attack_target(target_x: int, target_y: int, habilidade: String = "") -> Error:
    if target_x < 0 or target_x >= 20 or target_y < 0 or target_y >= 20:
        return ERR_INVALID_PARAMETER
    var payload: Dictionary = {"target_x": target_x, "target_y": target_y}
    if not habilidade.is_empty():
        payload["habilidade"] = habilidade
    return send_message("ATTACK_TARGET", payload)

func send_work_action(target_x: int, target_y: int, tipo: String = "minerar") -> Error:
    if target_x < 0 or target_x >= 20 or target_y < 0 or target_y >= 20:
        return ERR_INVALID_PARAMETER
    return send_message("WORK_ACTION", {"target_x": target_x, "target_y": target_y, "tipo": tipo})

func send_end_round() -> Error:
    return send_message("END_ROUND", {})

func send_chat(text: String) -> Error:
    if text.strip_edges().is_empty():
        return ERR_INVALID_PARAMETER
    return send_message("CHAT_MESSAGE", {"text": text.strip_edges()})

func send_ping() -> Error:
    return send_message("PING", {"timestamp": Time.get_ticks_msec()})
```

---

## 8. Integration with GameManager & Game Flow

The relationship between `WebSocketClient`, `GameManager`, and `EventBus` adheres strictly to inversion of control:
1. **Lobby Join**:
   - In `Lobby.tscn`, player enters name and room code.
   - UI calls `WebSocketClient.connect_to_room(code, player_id, name)`.
   - On `connected_to_server`: UI displays players in room.
2. **Game Start**:
   - Host clicks "Iniciar Partida" -> `send_start_game()`.
   - Server changes phase to `SELECAO_CARTAS` and broadcasts `STATE_UPDATE`.
   - `WebSocketClient` receives `STATE_UPDATE`, emits `state_update_received(payload)`.
   - `GameManager` (or scene coordinator) transitions state to `GameState.CERCO_ISECTUM`.
3. **Turn Execution**:
   - Players select cards via `send_select_card(idx)`.
   - Server resolves synchrony combos, sets phase to `ACAO_LIVRE`, broadcasts `STATE_UPDATE`.
   - Fortress board renders actions, allows players to spend movement and free actions (`send_move_hero`, `send_attack_target`, `send_work_action`).
   - When finished, player clicks end turn -> `send_end_round()`.

---

## 9. Recommendations for M6 Implementers & Reviewers

1. **File Placement**:
   - Implementation file: `godot_project/scripts/network/WebSocketClient.gd`
   - Test double: `godot_project/test/unit/mock_websocket_peer.gd` (or embedded in test suite)
   - Unit test suite: `godot_project/test/unit/test_websocket_client.gd`
2. **Memory Safety & Zero Leaks**:
   - `WebSocketClient` extends `Node`. In GUT tests, always instantiate via `autofree(WebSocketClient.new())`.
   - Any injected `MockWebSocketPeer` (extending `RefCounted`) will be cleaned up automatically once references drop.
   - Always clear custom connections in `after_each()`.
3. **Coverage Targets**:
   - Happy Path: Connection handshake, open transition, typed sending (8 actions), incoming message parsing, EventBus signal emission.
   - Edge Cases: Empty strings, out-of-bound grid coordinates, malformed JSON, unknown message types, unexpected disconnect during transmission.
   - Fault Tolerance: Timeout handling, exponential backoff progression, max retry exhaustion, manual disconnect during reconnecting.


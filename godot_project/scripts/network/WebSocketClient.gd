# res://scripts/network/WebSocketClient.gd
class_name WebSocketClient
extends Node

## Autoritativo WebSocket Client for Co-op Cerco contra Isectum.
## Communicates with FastAPI backend (/ws/{room_id}/{player_id}?player_name={name}).
## Adheres to RFC 6455 framing, typed event envelopes, and zero-leak lifecycle.

# ── Signals ──────────────────────────────────────────────────────────────────
## Connection lifecycle signals
signal connected_to_server(room_id: String, player_id: String)
signal connection_closed(code: int, reason: String)
signal connection_error(code: int, reason: String)
signal connection_failed(reason: String)
signal state_changed(old_state: int, new_state: int)
signal reconnecting(attempt: int, max_attempts: int)
signal reconnect_attempt(current_attempt: int, max_attempts: int, delay_seconds: float)
signal reconnect_failed()
signal reconnected()

## Message and game state signals
signal message_received(type: String, payload: Dictionary)
signal packet_received(type: String, payload: Dictionary)
signal state_update_received(data: Dictionary)
signal room_state_received(data: Dictionary)
signal action_rejected(action: String, reason: String)
signal action_rejected_received(action: String, reason: String)
signal chat_received(sender: String, text: String, color: String)
signal combat_log_received(logs: Array)
signal game_started_received()
signal server_error(error_message: String)
signal protocol_error(error_message: String)

# ── Connection State Machine Enum & Constants ────────────────────────────────
enum ConnectionState {
	DISCONNECTED = 0,
	CONNECTING = 1,
	CONNECTED = 2,
	CLOSING = 3,
	RECONNECTING = 4
}

const STATE_DISCONNECTED = ConnectionState.DISCONNECTED
const STATE_CONNECTING = ConnectionState.CONNECTING
const STATE_CONNECTED = ConnectionState.CONNECTED
const STATE_CLOSING = ConnectionState.CLOSING
const STATE_RECONNECTING = ConnectionState.RECONNECTING

# ── Configuration Properties ─────────────────────────────────────────────────
@export var server_url: String = "ws://127.0.0.1:8000"
@export var connect_timeout_seconds: float = 10.0
@export var auto_reconnect: bool = true
@export var max_reconnect_attempts: int = 5
@export var reconnect_initial_delay: float = 1.0
@export var reconnect_max_delay: float = 30.0
@export var reconnect_multiplier: float = 2.0
@export var debug_logging: bool = false

# ── Public Session Identifiers & Metrics ─────────────────────────────────────
var room_id: String = ""
var player_id: String = ""
var player_name: String = "Aventureiro"
var reconnect_attempts: int = 0
var is_reconnecting: bool = false

# ── Internal State ───────────────────────────────────────────────────────────
var _connection_state: ConnectionState = ConnectionState.DISCONNECTED
var _peer: Variant = null
var _connect_timer: float = 0.0
var _reconnect_timer: float = 0.0
var _last_received_state: Dictionary = {}
var _last_url: String = ""

func _init() -> void:
	name = "WebSocketClient"

func _ready() -> void:
	set_process(false)

# ── Peer Dependency Injection & Status Inspection ────────────────────────────

## Injects custom peer instance (used by MockWebSocketPeer in unit tests)
func set_peer(peer_instance: Variant) -> void:
	_peer = peer_instance

## Retrieves current peer instance
func get_peer() -> Variant:
	return _peer

## Returns current connection FSM state enum
func get_connection_state() -> ConnectionState:
	return _connection_state

## Returns whether client is currently in CONNECTED state
func is_connected_to_server() -> bool:
	return _connection_state == ConnectionState.CONNECTED

## Returns deep copy of the most recently received game state update
func get_last_state() -> Dictionary:
	return _last_received_state.duplicate(true)

## Resets client internal state, buffers, timers, and drops peer connection
func reset_state() -> void:
	room_id = ""
	player_id = ""
	player_name = "Aventureiro"
	reconnect_attempts = 0
	is_reconnecting = false
	_connect_timer = 0.0
	_reconnect_timer = 0.0
	_last_received_state.clear()
	_last_url = ""
	if _peer != null and _peer.has_method("close"):
		_peer.close(1000, "Reset")
	_set_state(ConnectionState.DISCONNECTED)
	set_process(false)

# ── Connection Lifecycle Methods ─────────────────────────────────────────────

## Initiates connection with explicit host, port, and TLS configuration
func connect_to_server(p_room_id: String, p_player_id: String, p_player_name: String = "Aventureiro", p_host: String = "127.0.0.1", p_port: int = 8000, p_use_tls: bool = false) -> Error:
	if p_room_id.strip_edges().is_empty() or p_player_id.strip_edges().is_empty():
		push_warning("[WebSocketClient] room_id and player_id cannot be empty.")
		return ERR_INVALID_PARAMETER

	if _connection_state == ConnectionState.CONNECTED or _connection_state == ConnectionState.CONNECTING:
		push_warning("[WebSocketClient] Already connecting or connected.")
		return ERR_ALREADY_IN_USE

	room_id = p_room_id.strip_edges().to_upper()
	player_id = p_player_id.strip_edges()
	player_name = p_player_name.strip_edges()
	reconnect_attempts = 0
	is_reconnecting = false

	var scheme: String = "wss" if p_use_tls else "ws"
	var url: String = "%s://%s:%d/ws/%s/%s?player_name=%s" % [
		scheme,
		p_host.strip_edges(),
		p_port,
		room_id,
		player_id,
		player_name.uri_encode()
	]
	return _do_connect(url, p_use_tls)

## Initiates connection using configured server_url
func connect_to_room(p_room_id: String, p_player_id: String, p_player_name: String = "Aventureiro") -> Error:
	if p_room_id.strip_edges().is_empty() or p_player_id.strip_edges().is_empty():
		push_warning("[WebSocketClient] room_id and player_id cannot be empty.")
		return ERR_INVALID_PARAMETER

	if _connection_state == ConnectionState.CONNECTED or _connection_state == ConnectionState.CONNECTING:
		push_warning("[WebSocketClient] Already connecting or connected.")
		return ERR_ALREADY_IN_USE

	room_id = p_room_id.strip_edges().to_upper()
	player_id = p_player_id.strip_edges()
	player_name = p_player_name.strip_edges()
	reconnect_attempts = 0
	is_reconnecting = false

	var base_url: String = server_url.trim_suffix("/")
	var url: String = "%s/ws/%s/%s?player_name=%s" % [
		base_url,
		room_id,
		player_id,
		player_name.uri_encode()
	]
	var use_tls: bool = base_url.begins_with("wss://")
	return _do_connect(url, use_tls)

## Closes connection gracefully and prevents subsequent auto-reconnect
func disconnect_from_server(code: int = 1000, reason: String = "Client disconnect") -> void:
	reconnect_attempts = max_reconnect_attempts
	is_reconnecting = false
	if _peer != null:
		if _peer.has_method("close"):
			_peer.close(code, reason)
		_set_state(ConnectionState.DISCONNECTED)
		set_process(false)
		connection_closed.emit(code, reason)
		if has_node("/root/EventBus"):
			get_node("/root/EventBus").network_connection_status_changed.emit(false, room_id)
	else:
		_set_state(ConnectionState.DISCONNECTED)
		set_process(false)

# ── Polling & Process Loop ───────────────────────────────────────────────────

func _process(delta: float) -> void:
	poll(delta)

## Synchronous poll step, callable both by _process and explicitly in unit tests
func poll(delta: float = 0.016) -> void:
	if _connection_state == ConnectionState.RECONNECTING:
		_reconnect_timer -= delta
		if _reconnect_timer <= 0.0:
			_attempt_reconnect()
		return

	if _peer == null:
		return

	if _peer.has_method("poll"):
		_peer.poll()

	var ready_state: int = _peer.get_ready_state() if _peer.has_method("get_ready_state") else 3

	match _connection_state:
		ConnectionState.CONNECTING:
			_connect_timer -= delta
			if ready_state == 1: # WebSocketPeer.STATE_OPEN
				_on_connected()
			elif ready_state == 3 or (connect_timeout_seconds > 0.0 and _connect_timer <= 0.0): # STATE_CLOSED / timeout
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

func _do_connect(url: String, use_tls: bool = false) -> Error:
	_last_url = url
	if _peer == null:
		_peer = WebSocketPeer.new()

	var tls: Variant = null
	if use_tls:
		tls = TLSOptions.client_unsafe()

	var err: Error = OK
	if _peer.has_method("connect_to_url"):
		err = _peer.connect_to_url(url, tls)
	else:
		err = ERR_UNCONFIGURED

	if err != OK:
		var err_msg: String = "Failed to connect to %s (code %d)" % [url, err]
		push_warning("[WebSocketClient] " + err_msg)
		connection_error.emit(err, err_msg)
		connection_failed.emit(err_msg)
		_set_state(ConnectionState.DISCONNECTED)
		set_process(false)
		return err

	_connect_timer = connect_timeout_seconds
	_set_state(ConnectionState.CONNECTING)
	set_process(true)
	return OK

func _attempt_reconnect() -> void:
	if _last_url.is_empty():
		_set_state(ConnectionState.DISCONNECTED)
		is_reconnecting = false
		reconnect_failed.emit()
		return

	var err: Error = OK
	if _peer != null and _peer.has_method("connect_to_url"):
		err = _peer.connect_to_url(_last_url)

	if err == OK:
		_connect_timer = connect_timeout_seconds
		_set_state(ConnectionState.CONNECTING)
	else:
		_handle_reconnect_retry_or_fail()

func _handle_reconnect_retry_or_fail() -> void:
	if reconnect_attempts >= max_reconnect_attempts:
		_set_state(ConnectionState.DISCONNECTED)
		is_reconnecting = false
		set_process(false)
		reconnect_failed.emit()
	else:
		reconnect_attempts += 1
		var delay: float = min(reconnect_max_delay, reconnect_initial_delay * pow(reconnect_multiplier, reconnect_attempts - 1))
		_reconnect_timer = delay
		_set_state(ConnectionState.RECONNECTING)
		is_reconnecting = true
		reconnecting.emit(reconnect_attempts, max_reconnect_attempts)
		reconnect_attempt.emit(reconnect_attempts, max_reconnect_attempts, delay)

func _on_connected() -> void:
	var was_reconnecting: bool = is_reconnecting or (_connection_state == ConnectionState.RECONNECTING)
	reconnect_attempts = 0
	is_reconnecting = false
	_set_state(ConnectionState.CONNECTED)
	if was_reconnecting:
		reconnected.emit()
	connected_to_server.emit(room_id, player_id)
	if has_node("/root/EventBus"):
		get_node("/root/EventBus").network_connection_status_changed.emit(true, room_id)

func _on_connect_failed(reason: String) -> void:
	connection_error.emit(ERR_CANT_CONNECT, reason)
	connection_failed.emit(reason)
	_handle_disconnect_or_reconnect(1006, reason)

func _on_connection_lost() -> void:
	var code: int = _peer.get_close_code() if _peer.has_method("get_close_code") else 1006
	var reason: String = _peer.get_close_reason() if _peer.has_method("get_close_reason") else "Connection lost"
	if code == -1:
		code = 1006
	if reason.is_empty():
		reason = "Connection dropped"
	_handle_disconnect_or_reconnect(code, reason)

func _on_closed_cleanly() -> void:
	var code: int = _peer.get_close_code() if _peer.has_method("get_close_code") else 1000
	var reason: String = _peer.get_close_reason() if _peer.has_method("get_close_reason") else "Clean close"
	if code == -1:
		code = 1000
	_set_state(ConnectionState.DISCONNECTED)
	set_process(false)
	connection_closed.emit(code, reason)
	if has_node("/root/EventBus"):
		get_node("/root/EventBus").network_connection_status_changed.emit(false, room_id)

func _handle_disconnect_or_reconnect(code: int, reason: String) -> void:
	connection_closed.emit(code, reason)
	if has_node("/root/EventBus"):
		get_node("/root/EventBus").network_connection_status_changed.emit(false, room_id)

	if auto_reconnect and code != 1000 and reconnect_attempts < max_reconnect_attempts:
		reconnect_attempts += 1
		var delay: float = min(reconnect_max_delay, reconnect_initial_delay * pow(reconnect_multiplier, reconnect_attempts - 1))
		_reconnect_timer = delay
		_set_state(ConnectionState.RECONNECTING)
		is_reconnecting = true
		reconnecting.emit(reconnect_attempts, max_reconnect_attempts)
		reconnect_attempt.emit(reconnect_attempts, max_reconnect_attempts, delay)
	else:
		_set_state(ConnectionState.DISCONNECTED)
		is_reconnecting = false
		set_process(false)
		if auto_reconnect and code != 1000 and reconnect_attempts >= max_reconnect_attempts:
			reconnect_failed.emit()

func _set_state(new_state: ConnectionState) -> void:
	if _connection_state == new_state:
		return
	var old_state: ConnectionState = _connection_state
	_connection_state = new_state
	state_changed.emit(old_state, new_state)

# ── Packet Ingestion & Dispatching ───────────────────────────────────────────

func _process_incoming_packets() -> void:
	while _peer != null and _peer.has_method("get_available_packet_count") and _peer.get_available_packet_count() > 0:
		var packet: PackedByteArray = _peer.get_packet()
		if packet.is_empty():
			continue
		var text: String = packet.get_string_from_utf8()
		if text.strip_edges().is_empty():
			continue

		var json: JSON = JSON.new()
		var parse_err: Error = json.parse(text)
		if parse_err != OK:
			protocol_error.emit("JSON parse error on packet: %s" % text)
			continue

		if not (json.data is Dictionary):
			protocol_error.emit("Root JSON element is not a dictionary: %s" % text)
			continue

		var dict: Dictionary = json.data as Dictionary
		if not dict.has("type") or not (dict["type"] is String):
			protocol_error.emit("Missing or non-string 'type' field: %s" % text)
			continue

		var msg_type: String = dict["type"]
		var payload: Dictionary = dict.get("payload", {}) if (dict.get("payload") is Dictionary) else {}

		_dispatch_message(msg_type, payload)

func _dispatch_message(type: String, payload: Dictionary) -> void:
	message_received.emit(type, payload)
	packet_received.emit(type, payload)

	if has_node("/root/EventBus"):
		get_node("/root/EventBus").network_message_received.emit(type, payload)

	match type:
		"STATE_UPDATE":
			_last_received_state = payload.duplicate(true)
			state_update_received.emit(payload)
		"ROOM_STATE":
			_last_received_state = payload.duplicate(true)
			room_state_received.emit(payload)
			state_update_received.emit(payload)
		"GAME_STARTED":
			game_started_received.emit()
			if has_node("/root/GameManager"):
				get_node("/root/GameManager").change_state(2) # GameState.CERCO_ISECTUM
		"CARD_LOCKED":
			pass
		"ROUND_RESOLVED":
			if has_node("/root/EventBus"):
				get_node("/root/EventBus").round_resolved.emit(payload.get("round_number", 0), payload.get("sync_results", {}))
		"COMBAT_LOG":
			var logs: Array = payload.get("logs", [])
			combat_log_received.emit(logs)
			if has_node("/root/EventBus"):
				var cor: String = payload.get("cor", "#cbd5e1")
				var autor: String = payload.get("autor", "LOG")
				var txt: String = payload.get("texto", "")
				if not txt.is_empty():
					get_node("/root/EventBus").combat_log_entry_added.emit("[color=%s]%s: %s[/color]" % [cor, autor, txt])
				for entry in logs:
					get_node("/root/EventBus").combat_log_entry_added.emit(str(entry))
		"ACTION_REJECTED":
			var acao: String = payload.get("acao", "")
			var motivo: String = payload.get("motivo", "")
			action_rejected.emit(acao, motivo)
			action_rejected_received.emit(acao, motivo)
			if has_node("/root/EventBus"):
				get_node("/root/EventBus").combat_log_entry_added.emit(
					"[color=#ef4444]⚠️ %s: %s[/color]" % [acao, motivo]
				)
		"ERROR":
			var msg: String = payload.get("mensagem", "")
			server_error.emit(msg)
		"CHAT_MESSAGE":
			var sender: String = payload.get("autor", "")
			var text: String = payload.get("texto", payload.get("text", ""))
			var color: String = payload.get("cor", "#ffffff")
			chat_received.emit(sender, text, color)
			if has_node("/root/EventBus"):
				get_node("/root/EventBus").combat_log_entry_added.emit("[color=%s]%s: %s[/color]" % [color, sender, text])

# ── Typed Protocol Send Methods (Client -> Server) ───────────────────────────

## Sends a raw framed JSON message to the server
func send_message(type: String, payload: Dictionary = {}) -> Error:
	if _connection_state != ConnectionState.CONNECTED or _peer == null:
		push_warning("[WebSocketClient] Cannot send message: client is not connected.")
		return ERR_UNCONFIGURED

	var envelope: Dictionary = {
		"type": type,
		"payload": payload
	}
	var json_str: String = JSON.stringify(envelope)
	if _peer.has_method("send_text"):
		return _peer.send_text(json_str)
	elif _peer.has_method("put_packet"):
		return _peer.put_packet(json_str.to_utf8_buffer())
	return FAILED

## Selects hero in lobby phase
func send_select_hero(hero_name: String) -> Error:
	if hero_name.strip_edges().is_empty():
		return ERR_INVALID_PARAMETER
	return send_message("SELECT_HERO", {"hero_name": hero_name.strip_edges()})

## Requests start of game from lobby
func send_start_game() -> Error:
	return send_message("START_GAME", {})

## Locks secret card during synchrony phase (card_idx >= -1)
func send_select_card(card_idx: int) -> Error:
	if card_idx < -1:
		return ERR_INVALID_PARAMETER
	return send_message("SELECT_CARD", {"card_idx": card_idx})

## Moves hero along grid coordinates [0, 19]
func send_move_hero(dest_x: int, dest_y: int) -> Error:
	if dest_x < 0 or dest_x >= 20 or dest_y < 0 or dest_y >= 20:
		return ERR_INVALID_PARAMETER
	return send_message("MOVE_HERO", {"dest_x": dest_x, "dest_y": dest_y})

## Attacks target enemy on grid coordinates [0, 19]
func send_attack_target(target_x: int, target_y: int, habilidade: String = "") -> Error:
	if target_x < 0 or target_x >= 20 or target_y < 0 or target_y >= 20:
		return ERR_INVALID_PARAMETER
	var payload: Dictionary = {"target_x": target_x, "target_y": target_y}
	if not habilidade.is_empty():
		payload["habilidade"] = habilidade
	return send_message("ATTACK_TARGET", payload)

## Performs work / mining / repairing action on adjacent tile [0, 19]
func send_work_action(target_x: int, target_y: int, tipo: String = "minerar") -> Error:
	if target_x < 0 or target_x >= 20 or target_y < 0 or target_y >= 20:
		return ERR_INVALID_PARAMETER
	return send_message("WORK_ACTION", {"target_x": target_x, "target_y": target_y, "tipo": tipo})

## Signals end of free actions for the round
func send_end_round() -> Error:
	return send_message("END_ROUND", {})

## Sends a text chat message to the room
func send_chat(mensagem: String) -> Error:
	if mensagem.strip_edges().is_empty():
		return ERR_INVALID_PARAMETER
	return send_message("CHAT_MESSAGE", {"text": mensagem.strip_edges()})

## Alias for send_chat
func send_chat_message(text: String) -> Error:
	return send_chat(text)

## Sends keepalive ping frame
func send_ping() -> Error:
	return send_message("PING", {})

# res://test/unit/test_websocket_stress_adversarial.gd
extends GutTest

## Adversarial & Stress Testing Suite for WebSocketClient.gd (Milestone 6)
## Empirical challenger verification covering:
## - Burst packet injection (100 to 500 queued packets, mixed valid/invalid/corrupted)
## - Rapid connect / disconnect / reconnect cycling under various states
## - Massive payload strings (large chat messages, huge combat logs, deep state updates)
## - Boundary and adversarial coordinate inputs (-1, 20, 99999, null strings, emojis)
## - Heterogeneous / Type-mismatched payload resilience

const WebSocketClientScript = preload("res://scripts/network/WebSocketClient.gd")

# ==============================================================================
# MOCK WEBSOCKET PEER EXTENSION FOR STRESS TESTING
# ==============================================================================

class StressMockWebSocketPeer extends RefCounted:
	enum State {
		STATE_CONNECTING = 0,
		STATE_OPEN = 1,
		STATE_CLOSING = 2,
		STATE_CLOSED = 3
	}

	var ready_state: int = State.STATE_CLOSED
	var connect_url: String = ""
	var sent_packets: Array[String] = []
	var incoming_packets: Array[PackedByteArray] = []
	var close_code: int = -1
	var close_reason: String = ""
	var should_fail_connect: bool = false
	var should_fail_send: bool = false
	var poll_count: int = 0

	func connect_to_url(url: String, _tls: Variant = null) -> Error:
		connect_url = url
		if should_fail_connect:
			ready_state = State.STATE_CLOSED
			return ERR_CANT_CONNECT
		ready_state = State.STATE_CONNECTING
		return OK

	func poll() -> void:
		poll_count += 1

	func get_ready_state() -> int:
		return ready_state

	func send_text(text: String) -> Error:
		if should_fail_send or ready_state != State.STATE_OPEN:
			return ERR_UNAVAILABLE
		sent_packets.append(text)
		return OK

	func put_packet(buffer: PackedByteArray) -> Error:
		if should_fail_send or ready_state != State.STATE_OPEN:
			return ERR_UNAVAILABLE
		sent_packets.append(buffer.get_string_from_utf8())
		return OK

	func get_available_packet_count() -> int:
		return incoming_packets.size()

	func get_packet() -> PackedByteArray:
		if incoming_packets.is_empty():
			return PackedByteArray()
		return incoming_packets.pop_front()

	func was_string_packet() -> bool:
		return true

	func close(code: int = 1000, reason: String = "") -> void:
		ready_state = State.STATE_CLOSED
		close_code = code
		close_reason = reason

	func get_close_code() -> int:
		return close_code

	func get_close_reason() -> String:
		return close_reason

	# ── Test Helpers ─────────────────────────────────────────────────────────

	func simulate_connection_established() -> void:
		ready_state = State.STATE_OPEN

	func simulate_receive_text(text: String) -> void:
		incoming_packets.append(text.to_utf8_buffer())

	func simulate_receive_raw_bytes(bytes: PackedByteArray) -> void:
		incoming_packets.append(bytes)

	func simulate_receive_json(dict: Dictionary) -> void:
		simulate_receive_text(JSON.stringify(dict))

	func simulate_abnormal_disconnect(code: int = 1006, reason: String = "Abnormal Disconnect") -> void:
		ready_state = State.STATE_CLOSED
		close_code = code
		close_reason = reason

	func clear() -> void:
		sent_packets.clear()
		incoming_packets.clear()
		ready_state = State.STATE_CLOSED
		connect_url = ""
		close_code = -1
		close_reason = ""
		should_fail_connect = false
		should_fail_send = false
		poll_count = 0


# ==============================================================================
# FIXTURES
# ==============================================================================

var _client: Node = null
var _mock_peer: StressMockWebSocketPeer = null

func before_each() -> void:
	_client = autofree(WebSocketClientScript.new())
	_mock_peer = StressMockWebSocketPeer.new()
	_client.set_peer(_mock_peer)

func after_each() -> void:
	if _client != null and is_instance_valid(_client) and _client.has_method("reset_state"):
		_client.reset_state()
	_client = null
	_mock_peer = null

func _connect_client() -> void:
	_client.connect_to_server("FORTALEZA_STRESS", "player_challenger", "Aquele")
	_mock_peer.simulate_connection_established()
	_client.poll()


# ==============================================================================
# 1. BURST PACKET INJECTION TESTS
# ==============================================================================

func test_burst_100_packets_queued_before_single_poll() -> void:
	# Arrange
	_connect_client()
	watch_signals(_client)
	var expected_count: int = 100

	# Act: Queue 100 packets into peer incoming buffer before calling poll()
	for i in range(expected_count):
		_mock_peer.simulate_receive_json({
			"type": "CHAT_MESSAGE",
			"payload": {
				"autor": "SwarmBot_%d" % i,
				"texto": "Burst attack %d" % i,
				"cor": "#ff0000"
			}
		})

	# Single poll drains entire queue
	_client.poll()

	# Assert
	assert_signal_emit_count(_client, "packet_received", expected_count, "All 100 burst packets must be processed")
	assert_signal_emit_count(_client, "chat_received", expected_count, "All 100 chat messages must be dispatched")
	assert_eq(_mock_peer.get_available_packet_count(), 0, "Incoming packet queue must be fully drained")


func test_burst_500_packets_stress_throughput() -> void:
	# Arrange
	_connect_client()
	watch_signals(_client)
	var total_packets: int = 500

	# Act: Queue 500 alternating packets
	for i in range(total_packets):
		if i % 2 == 0:
			_mock_peer.simulate_receive_json({
				"type": "STATE_UPDATE",
				"payload": {"round": i, "status": "active"}
			})
		else:
			_mock_peer.simulate_receive_json({
				"type": "COMBAT_LOG",
				"payload": {"logs": ["Log entry %d" % i]}
			})

	_client.poll()

	# Assert
	assert_signal_emit_count(_client, "packet_received", total_packets, "All 500 packets must be ingested")
	assert_signal_emit_count(_client, "state_update_received", 250, "Exactly 250 STATE_UPDATE signals")
	assert_signal_emit_count(_client, "combat_log_received", 250, "Exactly 250 COMBAT_LOG signals")
	assert_eq(_mock_peer.get_available_packet_count(), 0, "Buffer should be empty")


func test_burst_mixed_valid_invalid_and_corrupted_packets() -> void:
	# Arrange: Interleave valid packets, malformed JSON, empty frames, and corrupted bytes
	_connect_client()
	watch_signals(_client)

	# 1. Valid packet
	_mock_peer.simulate_receive_json({"type": "STATE_UPDATE", "payload": {"step": 1}})
	# 2. Empty byte array
	_mock_peer.simulate_receive_raw_bytes(PackedByteArray())
	# 3. Whitespace only
	_mock_peer.simulate_receive_text("   \n\t  ")
	# 4. Corrupted raw bytes (invalid UTF-8 sequence 0xFF 0xFE 0xFD)
	_mock_peer.simulate_receive_raw_bytes(PackedByteArray([255, 254, 253]))
	# 5. Malformed JSON syntax
	_mock_peer.simulate_receive_text("{\"type\": unclosed...")
	# 6. Valid packet after corruption
	_mock_peer.simulate_receive_json({"type": "STATE_UPDATE", "payload": {"step": 2}})
	# 7. Non-dictionary root (array)
	_mock_peer.simulate_receive_text("[1, 2, 3]")
	# 8. Valid packet
	_mock_peer.simulate_receive_json({"type": "STATE_UPDATE", "payload": {"step": 3}})

	# Act
	_client.poll()

	# Assert
	# Exactly 3 valid packets should be processed
	assert_signal_emit_count(_client, "state_update_received", 3, "All 3 valid packets must be processed despite errors")
	# protocol_error must be emitted for the malformed syntax and root array
	assert_signal_emitted(_client, "protocol_error", "Protocol error should be emitted for bad packets")
	assert_eq(_mock_peer.get_available_packet_count(), 0, "All items in queue must be consumed")


# ==============================================================================
# 2. RAPID CONNECT / DISCONNECT / RECONNECT CYCLING
# ==============================================================================

func test_rapid_connect_disconnect_cycling_50_iterations() -> void:
	# Arrange
	var iterations: int = 50

	# Act: Rapidly connect and disconnect without state desynchronization
	for i in range(iterations):
		var err: Error = _client.connect_to_server("ROOM_%d" % i, "player_%d" % i, "Hero")
		assert_eq(err, OK, "Cycle %d: connect_to_server should succeed" % i)
		assert_eq(_client.get_connection_state(), WebSocketClientScript.STATE_CONNECTING)

		_mock_peer.simulate_connection_established()
		_client.poll()
		assert_eq(_client.get_connection_state(), WebSocketClientScript.STATE_CONNECTED)

		_client.disconnect_from_server(1000, "Normal reset")
		assert_eq(_client.get_connection_state(), WebSocketClientScript.STATE_DISCONNECTED)

	# Assert
	assert_eq(_client.get_connection_state(), WebSocketClientScript.STATE_DISCONNECTED)
	assert_false(_client.is_connected_to_server())
	assert_false(_client.is_reconnecting)


func test_disconnect_while_connecting_aborts_cleanly() -> void:
	# Arrange
	_client.connect_to_server("ROOM_ABORT", "p_abort", "Stark")
	assert_eq(_client.get_connection_state(), WebSocketClientScript.STATE_CONNECTING)
	watch_signals(_client)

	# Act: Disconnect before connection is established
	_client.disconnect_from_server(1000, "Aborted during handshake")

	# Assert
	assert_eq(_client.get_connection_state(), WebSocketClientScript.STATE_DISCONNECTED)
	assert_signal_emitted(_client, "connection_closed")
	assert_false(_client.is_reconnecting)


func test_rapid_abnormal_disconnect_and_reconnect_recovery() -> void:
	# Arrange: Connect with auto-reconnect enabled
	_connect_client()
	_client.auto_reconnect = true
	_client.max_reconnect_attempts = 5
	_client.reconnect_initial_delay = 0.05
	_client.reconnect_multiplier = 1.0

	# Act: Trigger drop -> poll to enter RECONNECTING -> advance timer -> poll to re-open
	for cycle in range(3):
		_mock_peer.simulate_abnormal_disconnect(1006, "Drop %d" % cycle)
		_client.poll()
		assert_eq(_client.get_connection_state(), WebSocketClientScript.STATE_RECONNECTING, "Cycle %d: should be RECONNECTING" % cycle)

		# Fast-forward reconnect timer
		_client.poll(1.0)
		assert_eq(_client.get_connection_state(), WebSocketClientScript.STATE_CONNECTING, "Cycle %d: should be CONNECTING" % cycle)

		# Reconnection succeeds
		_mock_peer.simulate_connection_established()
		_client.poll()
		assert_eq(_client.get_connection_state(), WebSocketClientScript.STATE_CONNECTED, "Cycle %d: should be CONNECTED" % cycle)
		assert_eq(_client.reconnect_attempts, 0, "Reconnect counter must be reset on success")


func test_client_reset_state_idempotence_and_stability() -> void:
	# Arrange: Put client into dirty state
	_connect_client()
	_client.reconnect_attempts = 3
	_client.is_reconnecting = true

	# Act: Call reset_state 10 times consecutively
	for i in range(10):
		_client.reset_state()

	# Assert
	assert_eq(_client.get_connection_state(), WebSocketClientScript.STATE_DISCONNECTED)
	assert_eq(_client.room_id, "")
	assert_eq(_client.player_id, "")
	assert_eq(_client.reconnect_attempts, 0)
	assert_false(_client.is_reconnecting)


# ==============================================================================
# 3. MASSIVE PAYLOAD STRINGS & LARGE BUFFERS
# ==============================================================================

func test_massive_chat_message_payload_100kb() -> void:
	# Arrange
	_connect_client()
	watch_signals(_client)

	# Generate a 100,000 character string
	var chunk: String = "Fortaleza_Resiste_Ao_Enxame_Isectum_1234567890_" # 47 chars
	var repeats: int = int(100000.0 / chunk.length()) + 1
	var huge_text: String = chunk.repeat(repeats)

	# Act: Simulate receiving this massive chat message
	_mock_peer.simulate_receive_json({
		"type": "CHAT_MESSAGE",
		"payload": {
			"autor": "General",
			"texto": huge_text,
			"cor": "#00ff00"
		}
	})
	_client.poll()

	# Assert
	assert_signal_emitted(_client, "chat_received")
	assert_signal_emitted(_client, "packet_received")


func test_massive_combat_log_array_payload_500_entries() -> void:
	# Arrange
	_connect_client()
	watch_signals(_client)

	var large_logs: Array = []
	for i in range(500):
		large_logs.append("[DADOS D6] Round %d: Soldado rolou [Impacto, Balestra] contra Inseto Infiltrador" % i)

	# Act
	_mock_peer.simulate_receive_json({
		"type": "COMBAT_LOG",
		"payload": {
			"logs": large_logs,
			"autor": "JUIZ_COMBATE",
			"texto": "Resumo de Combate Massivo",
			"cor": "#e2e8f0"
		}
	})
	_client.poll()

	# Assert
	assert_signal_emitted(_client, "combat_log_received")


func test_massive_state_update_with_deep_nested_structures() -> void:
	# Arrange
	_connect_client()
	watch_signals(_client)

	# Create a rich board state with 20x20 grid cells and 24 castes
	var board_cells: Array = []
	for y in range(20):
		for x in range(20):
			board_cells.append({
				"x": x,
				"y": y,
				"terrain": "normal",
				"elevation": 0,
				"occupied_by": "isectum_%d_%d" % [x, y] if (x + y) % 4 == 0 else null
			})

	var heavy_state: Dictionary = {
		"room_id": "STRESS_ROOM",
		"fase": "CERCO_COMBATE",
		"round": 42,
		"board": board_cells,
		"resources": {"madeira": 150, "couro": 80, "metal": 200, "cristal": 99},
		"wall_hp": {"norte": 20, "sul": 15, "leste": 8, "oeste": 0}
	}

	# Act
	_mock_peer.simulate_receive_json({"type": "STATE_UPDATE", "payload": heavy_state})
	_client.poll()

	# Assert
	assert_signal_emitted(_client, "state_update_received")
	var last_state: Dictionary = _client.get_last_state()
	assert_eq(last_state.get("round"), 42)
	assert_eq((last_state.get("board", []) as Array).size(), 400)


func test_send_large_chat_message_client_to_server() -> void:
	# Arrange
	_connect_client()
	var large_str: String = "ESTRATEGIA_DEFENSIVA_".repeat(1000) # ~21KB

	# Act
	var err: Error = _client.send_chat(large_str)

	# Assert
	assert_eq(err, OK, "Client should successfully frame and send large chat strings")
	assert_eq(_mock_peer.sent_packets.size(), 1)
	var sent = _mock_peer.sent_packets[0]
	assert_true(sent.length() > 20000, "Sent packet should contain the full serialized payload")


func test_special_characters_emojis_accents_and_bbcode() -> void:
	# Arrange
	_connect_client()
	watch_signals(_client)

	var complex_text: String = "🛡️ Muralha Norte em Chamas! ⚔️ Ataque dos Insetos! [b]Câmara Central[/b] & Fundição!"

	# Act
	_mock_peer.simulate_receive_json({
		"type": "CHAT_MESSAGE",
		"payload": {
			"autor": "🛡️ Capitão ⚔️",
			"texto": complex_text,
			"cor": "#fbbf24"
		}
	})
	_client.poll()

	# Assert
	assert_signal_emitted(_client, "chat_received")
	assert_signal_emitted_with_parameters(_client, "chat_received", ["🛡️ Capitão ⚔️", complex_text, "#fbbf24"])


# ==============================================================================
# 4. BOUNDARY INPUTS ON COORDINATE COMMANDS & VALIDATION
# ==============================================================================

func test_boundary_coordinates_move_hero() -> void:
	# Arrange
	_connect_client()

	# Act & Assert: Valid boundaries [0, 19]
	assert_eq(_client.send_move_hero(0, 0), OK, "Corner (0,0) must be valid")
	assert_eq(_client.send_move_hero(19, 0), OK, "Corner (19,0) must be valid")
	assert_eq(_client.send_move_hero(0, 19), OK, "Corner (0,19) must be valid")
	assert_eq(_client.send_move_hero(19, 19), OK, "Corner (19,19) must be valid")
	assert_eq(_client.send_move_hero(10, 10), OK, "Center (10,10) must be valid")

	# Act & Assert: Out of bounds (negative, upper limit, extreme values)
	assert_eq(_client.send_move_hero(-1, 0), ERR_INVALID_PARAMETER, "dest_x = -1 must be rejected")
	assert_eq(_client.send_move_hero(0, -1), ERR_INVALID_PARAMETER, "dest_y = -1 must be rejected")
	assert_eq(_client.send_move_hero(20, 0), ERR_INVALID_PARAMETER, "dest_x = 20 must be rejected")
	assert_eq(_client.send_move_hero(0, 20), ERR_INVALID_PARAMETER, "dest_y = 20 must be rejected")
	assert_eq(_client.send_move_hero(99999, 0), ERR_INVALID_PARAMETER, "dest_x = 99999 must be rejected")
	assert_eq(_client.send_move_hero(0, 99999), ERR_INVALID_PARAMETER, "dest_y = 99999 must be rejected")
	assert_eq(_client.send_move_hero(-99999, -99999), ERR_INVALID_PARAMETER, "Extreme negatives must be rejected")
	assert_eq(_client.send_move_hero(20, 20), ERR_INVALID_PARAMETER, "(20,20) must be rejected")


func test_boundary_coordinates_attack_target() -> void:
	# Arrange
	_connect_client()

	# Valid corners
	assert_eq(_client.send_attack_target(0, 0), OK)
	assert_eq(_client.send_attack_target(19, 19, "golpe_de_balestra"), OK)

	# Invalid corners
	assert_eq(_client.send_attack_target(-1, 5), ERR_INVALID_PARAMETER)
	assert_eq(_client.send_attack_target(5, -1), ERR_INVALID_PARAMETER)
	assert_eq(_client.send_attack_target(20, 5), ERR_INVALID_PARAMETER)
	assert_eq(_client.send_attack_target(5, 20), ERR_INVALID_PARAMETER)
	assert_eq(_client.send_attack_target(99999, 99999), ERR_INVALID_PARAMETER)


func test_boundary_coordinates_work_action() -> void:
	# Arrange
	_connect_client()

	# Valid
	assert_eq(_client.send_work_action(0, 0, "minerar"), OK)
	assert_eq(_client.send_work_action(19, 19, "reparar"), OK)

	# Invalid
	assert_eq(_client.send_work_action(-1, 10), ERR_INVALID_PARAMETER)
	assert_eq(_client.send_work_action(10, -1), ERR_INVALID_PARAMETER)
	assert_eq(_client.send_work_action(20, 10), ERR_INVALID_PARAMETER)
	assert_eq(_client.send_work_action(10, 20), ERR_INVALID_PARAMETER)
	assert_eq(_client.send_work_action(-9999, 9999), ERR_INVALID_PARAMETER)


func test_select_card_boundary_values() -> void:
	# Arrange
	_connect_client()

	# card_idx = -1 means unselecting/passing card
	assert_eq(_client.send_select_card(-1), OK, "card_idx = -1 must be valid")
	assert_eq(_client.send_select_card(0), OK, "card_idx = 0 must be valid")
	assert_eq(_client.send_select_card(4), OK, "card_idx = 4 must be valid")
	assert_eq(_client.send_select_card(999), OK, "Large positive index is technically valid integer")

	# card_idx < -1 is strictly invalid
	assert_eq(_client.send_select_card(-2), ERR_INVALID_PARAMETER, "card_idx = -2 must be rejected")
	assert_eq(_client.send_select_card(-99999), ERR_INVALID_PARAMETER, "card_idx = -99999 must be rejected")


func test_adversarial_hero_name_inputs() -> void:
	# Arrange
	_connect_client()

	# Valid hero names
	assert_eq(_client.send_select_hero("Aquele"), OK)
	assert_eq(_client.send_select_hero("Stark"), OK)
	assert_eq(_client.send_select_hero("Herói_Com_Acentuação"), OK)
	assert_eq(_client.send_select_hero("🛡️ Paladino ⚔️"), OK)

	# Invalid hero names
	assert_eq(_client.send_select_hero(""), ERR_INVALID_PARAMETER, "Empty string must be rejected")
	assert_eq(_client.send_select_hero("     "), ERR_INVALID_PARAMETER, "Whitespace only must be rejected")
	assert_eq(_client.send_select_hero("\t\n"), ERR_INVALID_PARAMETER, "Tabs/newlines only must be rejected")


func test_adversarial_chat_message_inputs() -> void:
	# Arrange
	_connect_client()

	# Valid chat
	assert_eq(_client.send_chat("Olá fortaleza!"), OK)
	assert_eq(_client.send_chat("🛡️ ⚔️ 🔥"), OK)

	# Invalid chat
	assert_eq(_client.send_chat(""), ERR_INVALID_PARAMETER, "Empty chat rejected")
	assert_eq(_client.send_chat("   "), ERR_INVALID_PARAMETER, "Whitespace chat rejected")
	assert_eq(_client.send_chat_message("\n\t  "), ERR_INVALID_PARAMETER, "Whitespace alias rejected")


# ==============================================================================
# 5. HETEROGENEOUS & TYPE-MISMATCHED PAYLOAD RESILIENCE
# ==============================================================================

func test_combat_log_payload_with_null_or_heterogeneous_entries() -> void:
	# Arrange: Server sends non-array or weirdly typed fields in COMBAT_LOG
	_connect_client()
	watch_signals(_client)

	# logs as mixed types (integers, dicts, nulls inside array)
	_mock_peer.simulate_receive_json({
		"type": "COMBAT_LOG",
		"payload": {
			"logs": [123, null, {"foo": "bar"}, "valid log"],
			"cor": 9999, # non-string cor
			"autor": null, # null autor
			"texto": 456 # non-string texto
		}
	})

	# Act: Must not crash
	_client.poll()

	# Assert
	assert_signal_emitted(_client, "combat_log_received")


func test_chat_message_payload_with_heterogeneous_types() -> void:
	# Arrange
	_connect_client()
	watch_signals(_client)

	# Server sends numbers for autor and texto
	_mock_peer.simulate_receive_json({
		"type": "CHAT_MESSAGE",
		"payload": {
			"autor": "12345",
			"texto": "Chat text as string",
			"cor": "#ffffff"
		}
	})

	# Act
	_client.poll()

	# Assert
	assert_signal_emitted(_client, "chat_received")


func test_round_resolved_with_missing_or_corrupted_payload() -> void:
	# Arrange
	_connect_client()
	watch_signals(_client)

	# Payload without round_number or sync_results
	_mock_peer.simulate_receive_json({
		"type": "ROUND_RESOLVED",
		"payload": {}
	})

	# Act
	_client.poll()

	# Assert
	assert_signal_emitted(_client, "packet_received")


func test_action_rejected_with_unicode_reason() -> void:
	# Arrange
	_connect_client()
	watch_signals(_client)

	_mock_peer.simulate_receive_json({
		"type": "ACTION_REJECTED",
		"payload": {
			"acao": "MOVE_HERO",
			"motivo": "Posição ocupada por um Inseto Brutamontes! 🛡️"
		}
	})

	# Act
	_client.poll()

	# Assert
	assert_signal_emitted_with_parameters(_client, "action_rejected_received", [
		"MOVE_HERO",
		"Posição ocupada por um Inseto Brutamontes! 🛡️"
	])

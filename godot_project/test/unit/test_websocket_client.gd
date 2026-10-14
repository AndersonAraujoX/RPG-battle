# res://test/unit/test_websocket_client.gd
extends GutTest

## Suíte Canônica de Testes GUT para Milestone 6:
## Cliente de Rede Co-op WebSocket (WebSocketClient.gd)
##
## Adere estritamente ao padrão Arrange-Act-Assert (AAA), isolamento offline via Mock
## e garantia absoluta de zero vazamentos de memória no ObjectDB.

# ==============================================================================
# MOCK WEBSOCKET PEER (Test Double em GDScript puro, estende RefCounted)
# ==============================================================================

class MockWebSocketPeer extends RefCounted:
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

	# ── Funções Auxiliares do Test Harness ────────────────────────────────────

	func simulate_connection_established() -> void:
		ready_state = State.STATE_OPEN

	func simulate_receive_text(text: String) -> void:
		incoming_packets.append(text.to_utf8_buffer())

	func simulate_receive_json(dict: Dictionary) -> void:
		simulate_receive_text(JSON.stringify(dict))

	func simulate_server_disconnect(code: int = 1000, reason: String = "Normal Closure") -> void:
		ready_state = State.STATE_CLOSED
		close_code = code
		close_reason = reason

	func simulate_abnormal_disconnect(code: int = 1006, reason: String = "Abnormal Disconnect") -> void:
		ready_state = State.STATE_CLOSED
		close_code = code
		close_reason = reason

	func get_last_sent_json() -> Dictionary:
		if sent_packets.is_empty():
			return {}
		var json: JSON = JSON.new()
		if json.parse(sent_packets.back()) == OK and (json.data is Dictionary):
			return json.data as Dictionary
		return {}

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
# TEST FIXTURES & LIFECYCLE
# ==============================================================================

const WebSocketClientScript = preload("res://scripts/network/WebSocketClient.gd")

var _client: Node = null
var _mock_peer: MockWebSocketPeer = null

func before_each() -> void:
	_client = autofree(WebSocketClientScript.new())
	_mock_peer = MockWebSocketPeer.new()
	_client.set_peer(_mock_peer)

func after_each() -> void:
	if _client != null and is_instance_valid(_client) and _client.has_method("reset_state"):
		_client.reset_state()
	_client = null
	_mock_peer = null


# ==============================================================================
# SEÇÃO 1: Ciclo de Vida, Instanciação e Gestão de Memória Zero-Leak
# ==============================================================================

func test_client_instantiation_default_state() -> void:
	# Arrange: Cliente instanciado no before_each()
	# Act: Consultar propriedades e métodos de estado inicial
	var state = _client.get_connection_state()
	var is_conn = _client.is_connected_to_server()
	var rid = _client.room_id
	var pid = _client.player_id

	# Assert
	assert_eq(state, WebSocketClientScript.STATE_DISCONNECTED, "Cliente deve iniciar como STATE_DISCONNECTED")
	assert_false(is_conn, "Cliente não deve reportar conectado inicialmente")
	assert_eq(rid, "", "room_id inicial deve ser vazio")
	assert_eq(pid, "", "player_id inicial deve ser vazio")


func test_client_peer_injection() -> void:
	# Arrange: MockWebSocketPeer já injetado em _client
	# Act: Obter instância do peer injetado
	var peer = _client.get_peer()

	# Assert
	assert_eq(peer, _mock_peer, "Peer retornado deve ser exatamente a instância injetada")
	assert_eq(_mock_peer.get_ready_state(), MockWebSocketPeer.State.STATE_CLOSED, "Mock deve iniciar fechado")


func test_client_autofree_lifecycle_zero_leaks() -> void:
	# Arrange: Instanciação adicional encapsulada em autofree()
	var extra_client: Node = autofree(WebSocketClientScript.new())

	# Act: Resetar e verificar validade da instância
	extra_client.reset_state()

	# Assert
	assert_not_null(extra_client, "extra_client não deve ser nulo")
	assert_true(is_instance_valid(extra_client), "extra_client deve ser uma instância válida de nó")


func test_client_reset_state_clears_buffers_and_subscriptions() -> void:
	# Arrange: Configurar valores de sessão e estado transitório
	_client.room_id = "ROOM_TEST"
	_client.player_id = "player_123"
	_client.reconnect_attempts = 4
	_client.is_reconnecting = true

	# Act: Invocar limpeza explícita
	_client.reset_state()

	# Assert
	assert_eq(_client.room_id, "", "room_id deve ser resetado para vazio")
	assert_eq(_client.player_id, "", "player_id deve ser resetado para vazio")
	assert_eq(_client.reconnect_attempts, 0, "reconnect_attempts deve ser zerado")
	assert_false(_client.is_reconnecting, "is_reconnecting deve ser falso após reset")


# ==============================================================================
# SEÇÃO 2: Handshake de Conexão & Formação de URLs
# ==============================================================================

func test_connect_to_server_url_generation_standard() -> void:
	# Arrange: Cliente pronto com mock peer
	# Act: Conectar via connect_to_server padrão ws://
	var err: Error = _client.connect_to_server("SALAX", "p_10", "Guerreiro", "127.0.0.1", 8000, false)

	# Assert
	assert_eq(err, OK, "Conexão inicial com parâmetros válidos deve retornar OK")
	assert_eq(_mock_peer.connect_url, "ws://127.0.0.1:8000/ws/SALAX/p_10?player_name=Guerreiro", "URL gerada deve coincidir com o padrão FastAPI")
	assert_eq(_client.get_connection_state(), WebSocketClientScript.STATE_CONNECTING, "Estado deve transicionar para CONNECTING")


func test_connect_to_server_url_generation_tls_wss() -> void:
	# Arrange: Cliente pronto com mock peer
	# Act: Conectar via connect_to_server seguro wss://
	var err: Error = _client.connect_to_server("SALA_PROD", "p_99", "Mago", "game.servidor.com", 443, true)

	# Assert
	assert_eq(err, OK, "Conexão TLS válida deve retornar OK")
	assert_eq(_mock_peer.connect_url, "wss://game.servidor.com:443/ws/SALA_PROD/p_99?player_name=Mago", "URL WSS deve ser gerada com protocolo wss e porta 443")


func test_poll_detects_connection_open_and_emits_signal() -> void:
	# Arrange: Iniciar conexão e preparar mock para abrir socket
	watch_signals(_client)
	_client.connect_to_server("SALAX", "p_1", "Heroi")
	_mock_peer.simulate_connection_established()

	# Act: Processar frame via poll()
	_client.poll()

	# Assert
	assert_signal_emitted(_client, "connected_to_server", "connected_to_server deve ser emitido quando peer abre")
	assert_eq(_client.get_connection_state(), WebSocketClientScript.STATE_CONNECTED, "Estado deve ser CONNECTED")
	assert_true(_client.is_connected_to_server(), "is_connected_to_server() deve retornar true")


func test_connect_fails_when_peer_returns_error() -> void:
	# Arrange: Configurar mock para rejeitar conexão
	watch_signals(_client)
	_mock_peer.should_fail_connect = true

	# Act: Tentar conexão
	var err: Error = _client.connect_to_server("SALA1", "p1", "Nome")

	# Assert
	assert_ne(err, OK, "Erro do peer deve propagar código de falha")
	assert_signal_emitted(_client, "connection_failed", "connection_failed deve ser emitido em recusa")
	assert_eq(_client.get_connection_state(), WebSocketClientScript.STATE_DISCONNECTED, "Estado deve permanecer DISCONNECTED")


func test_connect_called_while_already_connected_is_rejected() -> void:
	# Arrange: Estabelecer conexão prévia
	_client.connect_to_server("SALAX", "p1", "Nome")
	_mock_peer.simulate_connection_established()
	_client.poll()

	# Act: Tentar nova conexão sobre socket ativo
	var err: Error = _client.connect_to_server("OUTRA_SALA", "p2", "Nome2")

	# Assert
	assert_eq(err, ERR_ALREADY_IN_USE, "Conexão redundante deve ser rejeitada com ERR_ALREADY_IN_USE")
	assert_eq(_client.room_id, "SALAX", "room_id ativo não deve ser sobrescrito")


func test_connect_validates_required_parameters() -> void:
	# Arrange: Cliente pronto
	# Act: Testar parâmetros vazios
	var r1: Error = _client.connect_to_server("", "p1", "Hero")
	var r2: Error = _client.connect_to_server("ROOM", "", "Hero")

	# Assert
	assert_eq(r1, ERR_INVALID_PARAMETER, "room_id vazio deve retornar ERR_INVALID_PARAMETER")
	assert_eq(r2, ERR_INVALID_PARAMETER, "player_id vazio deve retornar ERR_INVALID_PARAMETER")


# ==============================================================================
# SEÇÃO 3: Mensagens Tipadas Enviadas (Client -> Server)
# ==============================================================================

func _connect_client_helper() -> void:
	_client.connect_to_server("SALA_TEST", "p_me", "Aventureiro")
	_mock_peer.simulate_connection_established()
	_client.poll()


func test_send_select_hero_formats_and_sends_packet() -> void:
	# Arrange: Conectar cliente
	_connect_client_helper()

	# Act: Enviar seleção de herói
	var err: Error = _client.send_select_hero("Aquele")

	# Assert
	assert_eq(err, OK, "Envio deve ser bem sucedido")
	var data = _mock_peer.get_last_sent_json()
	assert_eq(data.get("type"), "SELECT_HERO")
	assert_eq(data.get("payload", {}).get("hero_name"), "Aquele")


func test_send_start_game_formats_and_sends_packet() -> void:
	# Arrange: Conectar cliente
	_connect_client_helper()

	# Act: Enviar início de partida
	var err: Error = _client.send_start_game()

	# Assert
	assert_eq(err, OK, "Envio deve retornar OK")
	var data = _mock_peer.get_last_sent_json()
	assert_eq(data.get("type"), "START_GAME")
	assert_eq((data.get("payload", {}) as Dictionary).size(), 0)


func test_send_select_card_formats_and_sends_packet() -> void:
	# Arrange: Conectar cliente
	_connect_client_helper()

	# Act: Travar carta pelo índice 2
	var err: Error = _client.send_select_card(2)

	# Assert
	assert_eq(err, OK, "Envio de carta deve retornar OK")
	var data = _mock_peer.get_last_sent_json()
	assert_eq(data.get("type"), "SELECT_CARD")
	assert_eq(data.get("payload", {}).get("card_idx"), 2)


func test_send_move_hero_formats_and_sends_packet() -> void:
	# Arrange: Conectar cliente
	_connect_client_helper()

	# Act: Enviar movimento para (7, 12)
	var err: Error = _client.send_move_hero(7, 12)

	# Assert
	assert_eq(err, OK, "Envio de movimento deve retornar OK")
	var data = _mock_peer.get_last_sent_json()
	assert_eq(data.get("type"), "MOVE_HERO")
	assert_eq(data.get("payload", {}).get("dest_x"), 7)
	assert_eq(data.get("payload", {}).get("dest_y"), 12)


func test_send_attack_target_formats_and_sends_packet() -> void:
	# Arrange: Conectar cliente
	_connect_client_helper()

	# Act: Atacar alvo em (10, 10) com habilidade especial
	var err: Error = _client.send_attack_target(10, 10, "golpe_pesado")

	# Assert
	assert_eq(err, OK, "Envio de ataque deve retornar OK")
	var data = _mock_peer.get_last_sent_json()
	assert_eq(data.get("type"), "ATTACK_TARGET")
	assert_eq(data.get("payload", {}).get("target_x"), 10)
	assert_eq(data.get("payload", {}).get("target_y"), 10)
	assert_eq(data.get("payload", {}).get("habilidade"), "golpe_pesado")


func test_send_work_action_formats_and_sends_packet() -> void:
	# Arrange: Conectar cliente
	_connect_client_helper()

	# Act: Enviar ação de trabalho minerar em (5, 5)
	var err: Error = _client.send_work_action(5, 5, "minerar")

	# Assert
	assert_eq(err, OK, "Envio de trabalho deve retornar OK")
	var data = _mock_peer.get_last_sent_json()
	assert_eq(data.get("type"), "WORK_ACTION")
	assert_eq(data.get("payload", {}).get("target_x"), 5)
	assert_eq(data.get("payload", {}).get("target_y"), 5)
	assert_eq(data.get("payload", {}).get("tipo"), "minerar")


func test_send_end_round_formats_and_sends_packet() -> void:
	# Arrange: Conectar cliente
	_connect_client_helper()

	# Act: Enviar finalização de turno
	var err: Error = _client.send_end_round()

	# Assert
	assert_eq(err, OK, "Envio de END_ROUND deve retornar OK")
	var data = _mock_peer.get_last_sent_json()
	assert_eq(data.get("type"), "END_ROUND")


func test_send_chat_message_formats_and_sends_packet() -> void:
	# Arrange: Conectar cliente
	_connect_client_helper()

	# Act: Enviar mensagem de chat via send_chat_message e send_chat
	var err: Error = _client.send_chat_message("Inimigos na muralha norte!")

	# Assert
	assert_eq(err, OK, "Envio de chat deve retornar OK")
	var data = _mock_peer.get_last_sent_json()
	assert_eq(data.get("type"), "CHAT_MESSAGE")
	assert_eq(data.get("payload", {}).get("text"), "Inimigos na muralha norte!")


func test_send_ping_packet() -> void:
	# Arrange: Conectar cliente
	_connect_client_helper()

	# Act: Enviar frame keepalive PING
	var err: Error = _client.send_ping()

	# Assert
	assert_eq(err, OK, "Envio de PING deve retornar OK")
	var data = _mock_peer.get_last_sent_json()
	assert_eq(data.get("type"), "PING")


func test_generic_send_message_payload() -> void:
	# Arrange: Conectar cliente
	_connect_client_helper()

	# Act: Enviar mensagem arbitrária tipada
	var err: Error = _client.send_message("CUSTOM_ACTION", {"param": 42})

	# Assert
	assert_eq(err, OK, "Envio genérico deve retornar OK")
	var data = _mock_peer.get_last_sent_json()
	assert_eq(data.get("type"), "CUSTOM_ACTION")
	assert_eq(data.get("payload", {}).get("param"), 42)


# ==============================================================================
# SEÇÃO 4: Recepção de Pacotes do Servidor & Sinais
# ==============================================================================

func test_receive_state_update_emits_signals() -> void:
	# Arrange: Conectar e monitorar sinais
	_connect_client_helper()
	watch_signals(_client)
	var state_dict: Dictionary = {"room_id": "R1", "fase": "LOBBY"}

	# Act: Simular recebimento de STATE_UPDATE
	_mock_peer.simulate_receive_json({"type": "STATE_UPDATE", "payload": state_dict})
	_client.poll()

	# Assert
	assert_signal_emitted(_client, "state_update_received")
	assert_signal_emitted_with_parameters(_client, "packet_received", ["STATE_UPDATE", state_dict])
	assert_eq(_client.get_last_state(), state_dict)


func test_receive_action_rejected_emits_signal() -> void:
	# Arrange: Conectar e monitorar sinais
	_connect_client_helper()
	watch_signals(_client)

	# Act: Simular recebimento de ACTION_REJECTED
	_mock_peer.simulate_receive_json({
		"type": "ACTION_REJECTED",
		"payload": {"acao": "SELECT_HERO", "motivo": "Heroi ja escolhido"}
	})
	_client.poll()

	# Assert
	assert_signal_emitted_with_parameters(_client, "action_rejected_received", ["SELECT_HERO", "Heroi ja escolhido"])


func test_receive_combat_log_emits_signal() -> void:
	# Arrange: Conectar e monitorar sinais
	_connect_client_helper()
	watch_signals(_client)

	# Act: Simular COMBAT_LOG
	_mock_peer.simulate_receive_json({
		"type": "COMBAT_LOG",
		"payload": {"logs": ["[DADOS] D6 rolou 4"]}
	})
	_client.poll()

	# Assert
	assert_signal_emitted(_client, "combat_log_received")


func test_receive_multiple_packets_in_single_poll() -> void:
	# Arrange: Conectar e monitorar sinais
	_connect_client_helper()
	watch_signals(_client)

	# Act: Enfileirar 3 pacotes sucessivos e executar poll único
	_mock_peer.simulate_receive_json({"type": "ROOM_STATE", "payload": {"sala": "S1"}})
	_mock_peer.simulate_receive_json({"type": "STATE_UPDATE", "payload": {"round": 1}})
	_mock_peer.simulate_receive_json({"type": "COMBAT_LOG", "payload": {"logs": ["Log 1"]}})
	_client.poll()

	# Assert
	assert_signal_emit_count(_client, "packet_received", 3)


func test_event_bus_relay_of_network_message() -> void:
	# Arrange: Conectar cliente e monitorar EventBus global
	_connect_client_helper()
	var eb: Node = get_node_or_null("/root/EventBus")
	if eb == null:
		pass_test("EventBus singleton não presente no ambiente isolado")
		return
	watch_signals(eb)

	# Act: Injetar pacote tipado
	_mock_peer.simulate_receive_json({"type": "STATE_UPDATE", "payload": {"fase": "COMBATE"}})
	_client.poll()

	# Assert
	assert_signal_emitted_with_parameters(eb, "network_message_received", ["STATE_UPDATE", {"fase": "COMBATE"}])


func test_receive_game_started_emits_specific_signal() -> void:
	# Arrange: Conectar e monitorar sinais
	_connect_client_helper()
	watch_signals(_client)

	# Act: Injetar GAME_STARTED
	_mock_peer.simulate_receive_json({"type": "GAME_STARTED", "payload": {}})
	_client.poll()

	# Assert
	assert_signal_emitted(_client, "game_started_received")


# ==============================================================================
# SEÇÃO 5: Cargas Adversariais, Robustez & Casos de Borda
# ==============================================================================

func test_receive_empty_string_ignored_safely() -> void:
	# Arrange: Conectar e monitorar sinais
	_connect_client_helper()
	watch_signals(_client)

	# Act: Injetar string vazia
	_mock_peer.simulate_receive_text("")
	_client.poll()

	# Assert
	assert_signal_not_emitted(_client, "packet_received")


func test_receive_whitespace_string_ignored_safely() -> void:
	# Arrange: Conectar e monitorar sinais
	_connect_client_helper()
	watch_signals(_client)

	# Act: Injetar espaços e tabulações
	_mock_peer.simulate_receive_text("   \t \n  ")
	_client.poll()

	# Assert
	assert_signal_not_emitted(_client, "packet_received")


func test_receive_malformed_syntax_json_rejected() -> void:
	# Arrange: Conectar e monitorar sinais
	_connect_client_helper()
	watch_signals(_client)

	# Act: Injetar JSON sintaticamente inválido
	_mock_peer.simulate_receive_text("{'key': unclosed_val")
	_client.poll()

	# Assert
	assert_signal_not_emitted(_client, "packet_received")
	assert_signal_emitted(_client, "protocol_error")


func test_receive_root_array_json_rejected() -> void:
	# Arrange: Conectar e monitorar sinais
	_connect_client_helper()
	watch_signals(_client)

	# Act: Injetar JSON que é array na raiz em vez de dicionário
	_mock_peer.simulate_receive_text("[{\"type\": \"TEST\"}]")
	_client.poll()

	# Assert
	assert_signal_not_emitted(_client, "packet_received")
	assert_signal_emitted(_client, "protocol_error")


func test_receive_primitive_root_json_rejected() -> void:
	# Arrange: Conectar e monitorar sinais
	_connect_client_helper()
	watch_signals(_client)

	# Act: Injetar JSON numérico ou booleano
	_mock_peer.simulate_receive_text("12345")
	_client.poll()

	# Assert
	assert_signal_not_emitted(_client, "packet_received")
	assert_signal_emitted(_client, "protocol_error")


func test_receive_missing_type_field_rejected() -> void:
	# Arrange: Conectar e monitorar sinais
	_connect_client_helper()
	watch_signals(_client)

	# Act: Injetar dicionário sem campo "type"
	_mock_peer.simulate_receive_text("{\"payload\": {\"data\": 1}}")
	_client.poll()

	# Assert
	assert_signal_not_emitted(_client, "packet_received")
	assert_signal_emitted(_client, "protocol_error")


func test_receive_non_string_type_field_rejected() -> void:
	# Arrange: Conectar e monitorar sinais
	_connect_client_helper()
	watch_signals(_client)

	# Act: Injetar dicionário com "type" numérico
	_mock_peer.simulate_receive_text("{\"type\": 100, \"payload\": {}}")
	_client.poll()

	# Assert
	assert_signal_not_emitted(_client, "packet_received")
	assert_signal_emitted(_client, "protocol_error")


func test_receive_missing_payload_defaults_to_empty_dict() -> void:
	# Arrange: Conectar e monitorar sinais
	_connect_client_helper()
	watch_signals(_client)

	# Act: Injetar pacote que contém somente "type"
	_mock_peer.simulate_receive_text("{\"type\": \"HEARTBEAT\"}")
	_client.poll()

	# Assert
	assert_signal_emitted_with_parameters(_client, "packet_received", ["HEARTBEAT", {}])


func test_receive_unknown_message_type_graceful() -> void:
	# Arrange: Conectar e monitorar sinais
	_connect_client_helper()
	watch_signals(_client)

	# Act: Injetar tipo desconhecido
	_mock_peer.simulate_receive_json({"type": "UNKNOWN_FUTURE_EVENT", "payload": {"foo": "bar"}})
	_client.poll()

	# Assert: Cliente propaga o pacote sem quebrar
	assert_signal_emitted_with_parameters(_client, "packet_received", ["UNKNOWN_FUTURE_EVENT", {"foo": "bar"}])


func test_send_message_when_disconnected_returns_error() -> void:
	# Arrange: Cliente explicitamente desconectado
	# Act: Tentar enviar mensagem
	var res: Error = _client.send_select_hero("Stark")

	# Assert
	assert_eq(res, ERR_UNCONFIGURED, "Tentativa de envio desconectado deve retornar ERR_UNCONFIGURED")
	assert_eq(_mock_peer.sent_packets.size(), 0, "Nenhum pacote deve ser enviado ao peer")


func test_send_methods_boundary_and_empty_validation() -> void:
	# Arrange: Conectar cliente
	_connect_client_helper()

	# Act & Assert: Testar validações de limites e valores vazios
	assert_eq(_client.send_select_hero(""), ERR_INVALID_PARAMETER, "Heroi vazio deve falhar")
	assert_eq(_client.send_select_hero("   "), ERR_INVALID_PARAMETER, "Heroi de espacos deve falhar")
	assert_eq(_client.send_select_card(-2), ERR_INVALID_PARAMETER, "Indice < -1 deve falhar")
	assert_eq(_client.send_move_hero(-1, 5), ERR_INVALID_PARAMETER, "dest_x < 0 deve falhar")
	assert_eq(_client.send_move_hero(20, 5), ERR_INVALID_PARAMETER, "dest_x >= 20 deve falhar")
	assert_eq(_client.send_move_hero(5, -1), ERR_INVALID_PARAMETER, "dest_y < 0 deve falhar")
	assert_eq(_client.send_move_hero(5, 20), ERR_INVALID_PARAMETER, "dest_y >= 20 deve falhar")
	assert_eq(_client.send_attack_target(-1, 0), ERR_INVALID_PARAMETER, "target_x < 0 deve falhar")
	assert_eq(_client.send_attack_target(0, 20), ERR_INVALID_PARAMETER, "target_y >= 20 deve falhar")
	assert_eq(_client.send_work_action(-1, 0), ERR_INVALID_PARAMETER, "work target_x < 0 deve falhar")
	assert_eq(_client.send_work_action(0, 20), ERR_INVALID_PARAMETER, "work target_y >= 20 deve falhar")
	assert_eq(_client.send_chat(""), ERR_INVALID_PARAMETER, "Chat vazio deve falhar")


# ==============================================================================
# SEÇÃO 6: Falhas de Rede, Quedas & Encerramento de Conexão
# ==============================================================================

func test_clean_server_disconnect_emits_connection_closed() -> void:
	# Arrange: Conectar e monitorar sinais
	_connect_client_helper()
	watch_signals(_client)

	# Act: Servidor fecha conexão com código 1000 normal
	_mock_peer.simulate_server_disconnect(1000, "Room Closed")
	_client.poll()

	# Assert
	assert_signal_emitted_with_parameters(_client, "connection_closed", [1000, "Room Closed"])
	assert_eq(_client.get_connection_state(), WebSocketClientScript.STATE_DISCONNECTED)


func test_abnormal_disconnect_emits_connection_closed() -> void:
	# Arrange: Conectar e monitorar sinais
	_connect_client_helper()
	watch_signals(_client)

	# Act: Queda anormal com código 1006
	_mock_peer.simulate_abnormal_disconnect(1006, "Abnormal Disconnect")
	_client.poll()

	# Assert
	assert_signal_emitted_with_parameters(_client, "connection_closed", [1006, "Abnormal Disconnect"])


func test_disconnect_from_server_client_initiated() -> void:
	# Arrange: Conectar cliente
	_connect_client_helper()

	# Act: Cliente solicita fechamento deliberado
	_client.disconnect_from_server(1000, "Player Quit")

	# Assert
	assert_eq(_mock_peer.close_code, 1000)
	assert_eq(_mock_peer.close_reason, "Player Quit")
	assert_eq(_client.get_connection_state(), WebSocketClientScript.STATE_DISCONNECTED)


func test_poll_when_peer_is_null_safe() -> void:
	# Arrange: Cliente novo sem peer atribuído
	var standalone: Node = autofree(WebSocketClientScript.new())

	# Act: Poll seguro
	standalone.poll()

	# Assert
	assert_eq(standalone.get_connection_state(), WebSocketClientScript.STATE_DISCONNECTED)


# ==============================================================================
# SEÇÃO 7: Lógica de Reconexão Automática & Backoff
# ==============================================================================

func test_auto_reconnect_disabled_by_default_or_toggleable() -> void:
	# Arrange: Cliente conectado com auto_reconnect desabilitado
	_connect_client_helper()
	_client.auto_reconnect = false

	# Act: Queda anormal
	_mock_peer.simulate_abnormal_disconnect(1006, "Drop")
	_client.poll()

	# Assert
	assert_false(_client.is_reconnecting, "Não deve entrar em modo de reconexão")
	assert_eq(_client.reconnect_attempts, 0, "reconnect_attempts deve ser 0")


func test_auto_reconnect_triggers_on_unexpected_disconnect() -> void:
	# Arrange: Cliente com auto_reconnect habilitado
	_connect_client_helper()
	_client.auto_reconnect = true
	_client.max_reconnect_attempts = 3
	watch_signals(_client)

	# Act: Queda anormal
	_mock_peer.simulate_abnormal_disconnect(1006, "Network Drop")
	_client.poll()

	# Assert
	assert_signal_emitted_with_parameters(_client, "reconnecting", [1, 3])
	assert_true(_client.is_reconnecting)


func test_auto_reconnect_does_not_trigger_on_clean_disconnect() -> void:
	# Arrange: Cliente com auto_reconnect habilitado
	_connect_client_helper()
	_client.auto_reconnect = true
	watch_signals(_client)

	# Act: Fechamento normal código 1000
	_mock_peer.simulate_server_disconnect(1000, "Normal Closure")
	_client.poll()

	# Assert
	assert_false(_client.is_reconnecting, "Fechamento limpo 1000 não deve agendar reconexão")
	assert_signal_not_emitted(_client, "reconnecting")


func test_reconnect_retry_counter_and_failure_signal() -> void:
	# Arrange: Cliente com limite estrito de 2 tentativas
	_connect_client_helper()
	_client.auto_reconnect = true
	_client.max_reconnect_attempts = 2
	watch_signals(_client)

	# Act:
	# Queda 1 -> tentativa 1 agendada
	_mock_peer.simulate_abnormal_disconnect(1006)
	_client.poll()
	# Forçar timer a disparar próxima tentativa
	_client.poll(100.0)
	# Segunda falha -> tentativa 2 agendada
	_mock_peer.simulate_abnormal_disconnect(1006)
	_client.poll()
	# Forçar timer -> estoura max_attempts
	_client.poll(100.0)
	_mock_peer.simulate_abnormal_disconnect(1006)
	_client.poll()

	# Assert
	assert_signal_emitted(_client, "reconnect_failed", "reconnect_failed deve ser emitido após esgotar tentativas")
	assert_false(_client.is_reconnecting)


func test_reconnect_success_resets_retry_counter() -> void:
	# Arrange: Cliente após queda anormal em estado de reconexão
	_connect_client_helper()
	_client.auto_reconnect = true
	_mock_peer.simulate_abnormal_disconnect(1006)
	_client.poll()
	watch_signals(_client)

	# Act: Simular expiração do timer de retry e restabelecimento da conexão no mock
	_client.poll(100.0) # Aciona tentativa de reconexão (connect_to_url)
	_mock_peer.simulate_connection_established() # Mock transiciona para STATE_OPEN
	_client.poll() # Cliente detecta STATE_OPEN e emite reconnected

	# Assert
	assert_signal_emitted(_client, "reconnected")
	assert_eq(_client.reconnect_attempts, 0)
	assert_false(_client.is_reconnecting)
	assert_true(_client.is_connected_to_server())


# ==============================================================================
# SEÇÃO 8: Anti-Cheat Hand Privacy Verification
# ==============================================================================

func test_anti_cheat_hand_privacy_in_state_update() -> void:
	# Arrange: Conectar cliente
	_connect_client_helper()
	watch_signals(_client)

	# Act: Simular STATE_UPDATE onde apenas o jogador local possui cartas visíveis
	var update_payload: Dictionary = {
		"room_id": "TEST_ROOM",
		"fase": "SELECAO_CARTAS",
		"round": 1,
		"heroes": [
			{
				"player_id": "p_me",
				"player_name": "Aventureiro",
				"hero_name": "Aquele",
				"is_me": true,
				"cards_count": 4,
				"hand": [
					{"id": "marcha_1", "nome": "Marcha"},
					{"id": "trabalho_1", "nome": "Trabalho"}
				]
			},
			{
				"player_id": "p_peer",
				"player_name": "OutroJogador",
				"hero_name": "Stark",
				"is_me": false,
				"cards_count": 4,
				"hand": []
			}
		]
	}
	_mock_peer.simulate_receive_json({"type": "STATE_UPDATE", "payload": update_payload})
	_client.poll()

	# Assert
	var state: Dictionary = _client.get_last_state()
	var heroes: Array = state.get("heroes", [])
	assert_eq(heroes.size(), 2, "Devem existir 2 heróis no payload")

	var me = heroes[0]
	assert_true(me.get("is_me"), "Herói 0 deve ser o jogador local (is_me = true)")
	assert_eq((me.get("hand", []) as Array).size(), 2, "Jogador local deve ter sua mão completa preservada")

	var peer = heroes[1]
	assert_false(peer.get("is_me"), "Herói 1 não deve ser o jogador local (is_me = false)")
	assert_eq((peer.get("hand", []) as Array).size(), 0, "Mão do peer deve ser mascarada como vazia []")
	assert_eq(peer.get("cards_count"), 4, "cards_count do peer deve indicar 4 cartas")

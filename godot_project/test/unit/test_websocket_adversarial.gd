# res://test/unit/test_websocket_adversarial.gd
extends GutTest

## Suíte Adversarial de Testes GUT (Milestone 6 - Challenger 2)
## Validação empírica de resiliência a falhas, corrupção de dados,
## privacidade anti-cheat e transições concorrentes de estado no WebSocketClient.gd.

# ==============================================================================
# MOCK WEBSOCKET PEER EXPANDIDO PARA TESTES ADVERSARIAIS
# ==============================================================================

class AdversarialMockPeer extends RefCounted:
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
	var send_error_code: Error = ERR_UNAVAILABLE
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
		if should_fail_send:
			return send_error_code
		if ready_state != State.STATE_OPEN:
			return ERR_UNAVAILABLE
		sent_packets.append(text)
		return OK

	func put_packet(buffer: PackedByteArray) -> Error:
		if should_fail_send:
			return send_error_code
		if ready_state != State.STATE_OPEN:
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

	# ── Funções de Injeção de Falhas ──────────────────────────────────────────

	func simulate_connection_established() -> void:
		ready_state = State.STATE_OPEN

	func simulate_receive_bytes(bytes: PackedByteArray) -> void:
		incoming_packets.append(bytes)

	func simulate_receive_text(text: String) -> void:
		incoming_packets.append(text.to_utf8_buffer())

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
		send_error_code = ERR_UNAVAILABLE
		poll_count = 0


# ==============================================================================
# FIXTURES E SETUP
# ==============================================================================

const WebSocketClientScript = preload("res://scripts/network/WebSocketClient.gd")

var _client: Node = null
var _mock_peer: AdversarialMockPeer = null

func before_each() -> void:
	_client = autofree(WebSocketClientScript.new())
	_mock_peer = AdversarialMockPeer.new()
	_client.set_peer(_mock_peer)

func after_each() -> void:
	if _client != null and is_instance_valid(_client) and _client.has_method("reset_state"):
		_client.reset_state()
	_client = null
	_mock_peer = null

func _connect_client_helper() -> void:
	_client.connect_to_server("SALAX", "player_challenger", "Challenger")
	_mock_peer.simulate_connection_established()
	_client.poll()


# ==============================================================================
# SEÇÃO 1: Queda no Meio da Partida, Recuperação de Estado e Progressão de Backoff
# ==============================================================================

func test_adversarial_midgame_disconnect_preserves_state_and_reconnects() -> void:
	# Arrange: Conectar cliente e receber estado rico de meio de jogo
	_connect_client_helper()
	watch_signals(_client)
	var midgame_state: Dictionary = {
		"room_id": "SALAX",
		"fase": "ACAO_LIVRE",
		"round": 4,
		"recursos": {"madeira": 12, "couro": 5, "metal": 8, "cristal": 3},
		"sinergia_ativa": {"tipo": "supremo", "categoria": "movimento"},
		"heroes": [
			{"player_id": "player_challenger", "hero_name": "Aquele", "hp_atual": 42, "is_me": true, "hand": [{"id": "c1"}]}
		]
	}
	_mock_peer.simulate_receive_json({"type": "STATE_UPDATE", "payload": midgame_state})
	_client.poll()
	assert_eq(_client.get_last_state().get("round"), 4, "Estado recebido pré-queda deve ser Round 4")

	# Act 1: Queda repentina de rede no meio da partida (código 1006)
	_mock_peer.simulate_abnormal_disconnect(1006, "Midgame socket collapse")
	_client.poll()

	# Assert 1: Deve entrar em RECONNECTING, manter o estado prévio e emitir sinais
	assert_eq(_client.get_connection_state(), WebSocketClientScript.STATE_RECONNECTING)
	assert_true(_client.is_reconnecting)
	assert_eq(_client.get_last_state().get("round"), 4, "Estado prévio não deve ser destruído na queda")
	assert_signal_emitted_with_parameters(_client, "connection_closed", [1006, "Midgame socket collapse"])
	assert_signal_emitted(_client, "reconnecting")

	# Act 2: Avançar tempo para o timer de reconexão disparar e mock aceitar conexão
	_client.poll(2.0) # Dispara _attempt_reconnect
	_mock_peer.simulate_connection_established()
	_client.poll()

	# Assert 2: Reconexão confirmada
	assert_signal_emitted(_client, "reconnected")
	assert_true(_client.is_connected_to_server())
	assert_eq(_client.reconnect_attempts, 0)

	# Act 3: Servidor envia STATE_UPDATE autoritativo pós-reconexão
	var recovered_state: Dictionary = midgame_state.duplicate(true)
	recovered_state["round"] = 5
	_mock_peer.simulate_receive_json({"type": "STATE_UPDATE", "payload": recovered_state})
	_client.poll()

	# Assert 3: Novo estado atualizado corretamente
	assert_eq(_client.get_last_state().get("round"), 5, "Cliente deve processar STATE_UPDATE pós-reconexão")


func test_adversarial_exponential_backoff_timing_progression() -> void:
	# Arrange: Configurar parâmetros determinísticos de backoff
	_client.reconnect_initial_delay = 1.0
	_client.reconnect_multiplier = 2.0
	_client.reconnect_max_delay = 10.0
	_client.max_reconnect_attempts = 4
	_client.auto_reconnect = true
	_connect_client_helper()
	watch_signals(_client)

	# Act & Assert 1: Falha 1 -> delay = 1.0s
	_mock_peer.simulate_abnormal_disconnect(1006)
	_client.poll()
	assert_signal_emitted_with_parameters(_client, "reconnect_attempt", [1, 4, 1.0])
	assert_eq(_client.reconnect_attempts, 1)

	# Act & Assert 2: Avançar 1.0s -> tentativa conecta -> falha imediatamente -> delay = 2.0s
	_client.poll(1.0)
	_mock_peer.simulate_abnormal_disconnect(1006)
	_client.poll()
	assert_signal_emitted_with_parameters(_client, "reconnect_attempt", [2, 4, 2.0])
	assert_eq(_client.reconnect_attempts, 2)

	# Act & Assert 3: Avançar 2.0s -> delay = 4.0s
	_client.poll(2.0)
	_mock_peer.simulate_abnormal_disconnect(1006)
	_client.poll()
	assert_signal_emitted_with_parameters(_client, "reconnect_attempt", [3, 4, 4.0])
	assert_eq(_client.reconnect_attempts, 3)

	# Act & Assert 4: Avançar 4.0s -> tentativa 4 -> delay = 8.0s (ou limitado por max_delay)
	_client.poll(4.0)
	_mock_peer.simulate_abnormal_disconnect(1006)
	_client.poll()
	assert_signal_emitted_with_parameters(_client, "reconnect_attempt", [4, 4, 8.0])
	assert_eq(_client.reconnect_attempts, 4)

	# Act & Assert 5: Esgotar tentativas máximas
	_client.poll(8.0)
	_mock_peer.simulate_abnormal_disconnect(1006)
	_client.poll()
	assert_signal_emitted(_client, "reconnect_failed")
	assert_eq(_client.get_connection_state(), WebSocketClientScript.STATE_DISCONNECTED)
	assert_false(_client.is_reconnecting)


func test_adversarial_reconnect_capping_at_max_delay() -> void:
	# Arrange: Configurar teto baixo de max_delay = 3.0s
	_client.reconnect_initial_delay = 1.0
	_client.reconnect_multiplier = 4.0
	_client.reconnect_max_delay = 3.0
	_client.max_reconnect_attempts = 3
	_client.auto_reconnect = true
	_connect_client_helper()
	watch_signals(_client)

	# Act 1: Falha 1 -> delay = 1.0
	_mock_peer.simulate_abnormal_disconnect(1006)
	_client.poll()
	assert_signal_emitted_with_parameters(_client, "reconnect_attempt", [1, 3, 1.0])

	# Act 2: Falha 2 -> 1.0 * 4.0 = 4.0, mas limitado a max_delay 3.0
	_client.poll(1.0)
	_mock_peer.simulate_abnormal_disconnect(1006)
	_client.poll()
	assert_signal_emitted_with_parameters(_client, "reconnect_attempt", [2, 3, 3.0])


# ==============================================================================
# SEÇÃO 2: Anti-Cheat Hand Privacy e Isolamento de Estado
# ==============================================================================

func test_adversarial_anti_cheat_state_mutation_isolation() -> void:
	# Arrange: Conectar e receber payload autoritativo
	_connect_client_helper()
	var original_hand: Array = [
		{"id": "marcha_01", "nome": "Marcha Rápida", "movimento": 2},
		{"id": "escavacao_01", "nome": "Escavação Profunda", "escavacao": 3}
	]
	var payload: Dictionary = {
		"room_id": "ANTI_CHEAT_ROOM",
		"heroes": [
			{
				"player_id": "player_challenger",
				"hero_name": "Aquele",
				"is_me": true,
				"hand": original_hand
			},
			{
				"player_id": "adversary_player",
				"hero_name": "Stark",
				"is_me": false,
				"hand": []
			}
		]
	}
	_mock_peer.simulate_receive_json({"type": "STATE_UPDATE", "payload": payload})
	_client.poll()

	# Act: Obter estado do cliente e tentar mutar a mão localmente
	var retrieved_state: Dictionary = _client.get_last_state()
	var heroes: Array = retrieved_state.get("heroes", [])
	var my_hero: Dictionary = heroes[0]
	var opponent_hero: Dictionary = heroes[1]

	# Tentar adulterar a mão e injetar cartas no oponente
	(my_hero["hand"] as Array).clear()
	(opponent_hero["hand"] as Array).append({"id": "carta_hackeada", "nome": "Cheat"})

	# Assert: O estado interno no cliente deve permanecer inviolado (deep copy)
	var fresh_state: Dictionary = _client.get_last_state()
	var fresh_my_hero: Dictionary = fresh_state["heroes"][0]
	var fresh_opponent: Dictionary = fresh_state["heroes"][1]

	assert_eq((fresh_my_hero["hand"] as Array).size(), 2, "Mutação externa não deve alterar a mão local em _last_received_state")
	assert_eq((fresh_opponent["hand"] as Array).size(), 0, "Mutação externa não deve adulterar a mão do oponente no estado interno")


func test_adversarial_anti_cheat_multi_player_privacy_enforcement() -> void:
	# Arrange: Partida de 4 jogadores
	_connect_client_helper()
	var four_player_state: Dictionary = {
		"room_id": "ROOM_4P",
		"heroes": [
			{"player_id": "p1", "is_me": false, "hand": []},
			{"player_id": "player_challenger", "is_me": true, "hand": [{"id": "card_x"}]},
			{"player_id": "p3", "is_me": false, "hand": []},
			{"player_id": "p4", "is_me": false, "hand": []}
		]
	}
	_mock_peer.simulate_receive_json({"type": "STATE_UPDATE", "payload": four_player_state})
	_client.poll()

	# Act & Assert
	var state = _client.get_last_state()
	var heroes: Array = state.get("heroes", [])
	assert_eq(heroes.size(), 4)

	for h in heroes:
		var hero_dict: Dictionary = h
		if hero_dict.get("player_id") == "player_challenger":
			assert_true(hero_dict.get("is_me"), "Jogador local deve ser marcado como is_me=true")
			assert_eq((hero_dict.get("hand", []) as Array).size(), 1, "Mão do jogador local visível")
		else:
			assert_false(hero_dict.get("is_me"), "Outro jogador deve ter is_me=false")
			assert_eq((hero_dict.get("hand", []) as Array).size(), 0, "Mão de oponentes deve ser vazia")


# ==============================================================================
# SEÇÃO 3: Envio de Mensagens em Estados Concorrentes & Inválidos
# ==============================================================================

func test_adversarial_send_calls_rejected_during_connecting_state() -> void:
	# Arrange: Iniciar conexão mas NÃO abrir socket ainda (permanece STATE_CONNECTING)
	_client.connect_to_server("SALAX", "p_challenger")
	assert_eq(_client.get_connection_state(), WebSocketClientScript.STATE_CONNECTING)

	# Act & Assert: Todas as chamadas de envio devem retornar ERR_UNCONFIGURED
	assert_eq(_client.send_select_hero("Aquele"), ERR_UNCONFIGURED, "send_select_hero deve falhar em CONNECTING")
	assert_eq(_client.send_start_game(), ERR_UNCONFIGURED, "send_start_game deve falhar em CONNECTING")
	assert_eq(_client.send_select_card(0), ERR_UNCONFIGURED, "send_select_card deve falhar em CONNECTING")
	assert_eq(_client.send_move_hero(5, 5), ERR_UNCONFIGURED, "send_move_hero deve falhar em CONNECTING")
	assert_eq(_client.send_attack_target(6, 6), ERR_UNCONFIGURED, "send_attack_target deve falhar em CONNECTING")
	assert_eq(_client.send_work_action(7, 7), ERR_UNCONFIGURED, "send_work_action deve falhar em CONNECTING")
	assert_eq(_client.send_end_round(), ERR_UNCONFIGURED, "send_end_round deve falhar em CONNECTING")
	assert_eq(_client.send_chat("Ola"), ERR_UNCONFIGURED, "send_chat deve falhar em CONNECTING")
	assert_eq(_client.send_ping(), ERR_UNCONFIGURED, "send_ping deve falhar em CONNECTING")
	assert_eq(_client.send_message("CUSTOM", {}), ERR_UNCONFIGURED, "send_message deve falhar em CONNECTING")


func test_adversarial_send_calls_rejected_during_reconnecting_state() -> void:
	# Arrange: Conectar e depois derrubar para RECONNECTING
	_connect_client_helper()
	_client.auto_reconnect = true
	_mock_peer.simulate_abnormal_disconnect(1006)
	_client.poll()
	assert_eq(_client.get_connection_state(), WebSocketClientScript.STATE_RECONNECTING)

	# Act & Assert: Envio rejeitado em RECONNECTING
	assert_eq(_client.send_move_hero(1, 1), ERR_UNCONFIGURED, "Envio deve ser bloqueado em RECONNECTING")
	assert_eq(_client.send_chat("Socorro"), ERR_UNCONFIGURED, "Chat deve ser bloqueado em RECONNECTING")


func test_adversarial_send_when_peer_fails_with_buffer_full() -> void:
	# Arrange: Conectar cliente, mas configurar mock para simular erro de envio do socket
	_connect_client_helper()
	_mock_peer.should_fail_send = true
	_mock_peer.send_error_code = ERR_UNAVAILABLE

	# Act: Tentar enviar mensagem
	var err: Error = _client.send_move_hero(10, 10)

	# Assert: Erro do peer deve propagar diretamente
	assert_eq(err, ERR_UNAVAILABLE, "Erro de transmissão do peer deve ser repassado ao chamador")


func test_adversarial_concurrent_rapid_fire_packet_burst() -> void:
	# Arrange: Conectar cliente
	_connect_client_helper()

	# Act: Disparar rajada de 50 ações seguidas
	for i in range(50):
		var err = _client.send_move_hero(i % 20, (i * 2) % 20)
		assert_eq(err, OK, "Envio em rajada #%d deve retornar OK" % i)

	# Assert: Todos os 50 pacotes devem ter sido despachados em ordem FIFO
	assert_eq(_mock_peer.sent_packets.size(), 50, "Todos os 50 pacotes devem estar no buffer de envio")
	var first_json: Dictionary = JSON.parse_string(_mock_peer.sent_packets[0])
	var last_json: Dictionary = JSON.parse_string(_mock_peer.sent_packets[49])
	assert_eq(first_json["payload"]["dest_x"], 0)
	assert_eq(last_json["payload"]["dest_x"], 49 % 20)


func test_adversarial_send_with_null_peer_safe() -> void:
	# Arrange: Cliente sem peer
	var client_no_peer: Node = autofree(WebSocketClientScript.new())
	client_no_peer.set_peer(null)

	# Act & Assert: Nenhuma chamada deve causar crash
	assert_eq(client_no_peer.send_move_hero(5, 5), ERR_UNCONFIGURED)
	assert_eq(client_no_peer.send_message("TEST", {}), ERR_UNCONFIGURED)


# ==============================================================================
# SEÇÃO 4: Injeção de Cargas Corrompidas, Bytes Inválidos & Payloads Hostis
# ==============================================================================

func test_adversarial_corrupt_non_utf8_binary_frame_injection() -> void:
	# Arrange: Conectar e vigiar sinais
	_connect_client_helper()
	watch_signals(_client)

	# Act: Injetar sequência de bytes inválidos não-UTF8 (e.g. 0xFF 0xFE 0xFD)
	var corrupt_bytes: PackedByteArray = PackedByteArray([0xFF, 0xFE, 0xFD, 0x80, 0x81])
	_mock_peer.simulate_receive_bytes(corrupt_bytes)
	_client.poll()

	# Assert: Cliente trata caracteres de substituição Unicode (U+FFFD), falha no parse JSON e emite protocol_error com segurança
	assert_signal_not_emitted(_client, "packet_received")
	assert_signal_emitted(_client, "protocol_error")


func test_adversarial_truncated_json_payload_triggers_protocol_error() -> void:
	# Arrange: Conectar e vigiar sinais
	_connect_client_helper()
	watch_signals(_client)

	# Act: Injetar JSON truncado pela metade
	_mock_peer.simulate_receive_text("{\"type\": \"STATE_UPDATE\", \"payload\": {\"round\": 1, \"recursos\":")
	_client.poll()

	# Assert: Deve emitir protocol_error e não quebrar o cliente
	assert_signal_emitted(_client, "protocol_error")
	assert_signal_not_emitted(_client, "packet_received")
	assert_signal_not_emitted(_client, "state_update_received")


func test_adversarial_payload_with_null_and_unexpected_types() -> void:
	# Arrange: Conectar e vigiar sinais
	_connect_client_helper()
	watch_signals(_client)

	# Act 1: "payload" é nulo em vez de dicionário
	_mock_peer.simulate_receive_text("{\"type\": \"PING\", \"payload\": null}")
	_client.poll()

	# Assert 1: Deve converter para dicionário vazio {} e aceitar com segurança
	assert_signal_emitted_with_parameters(_client, "packet_received", ["PING", {}])

	# Act 2: "payload" é string em vez de dicionário
	_mock_peer.simulate_receive_text("{\"type\": \"CUSTOM\", \"payload\": \"string_invalida\"}")
	_client.poll()

	# Assert 2: Converte payload não-dicionário para {}
	assert_signal_emitted_with_parameters(_client, "packet_received", ["CUSTOM", {}])

	# Act 3: "payload" é número
	_mock_peer.simulate_receive_text("{\"type\": \"NUMERIC_PAYLOAD\", \"payload\": 999}")
	_client.poll()

	# Assert 3: Seguro
	assert_signal_emitted_with_parameters(_client, "packet_received", ["NUMERIC_PAYLOAD", {}])


func test_adversarial_extreme_payload_size_and_special_characters() -> void:
	# Arrange: Conectar e vigiar sinais
	_connect_client_helper()
	watch_signals(_client)

	# Criar string de 10.000 caracteres com emojis, BBCode e quebras de linha
	var long_str: String = "⚔️ [b]Ataque Crítico![/b] 🛡️ <script>alert('xss')</script> "
	for _i in range(100):
		long_str += "Texto longo de teste com símbolos especiais ✨ 虫 "

	var extreme_payload: Dictionary = {
		"autor": "HostileEntity",
		"texto": long_str,
		"cor": "#ef4444"
	}

	# Act: Injetar pacote gigante
	_mock_peer.simulate_receive_json({"type": "CHAT_MESSAGE", "payload": extreme_payload})
	_client.poll()

	# Assert: Cliente processa sem estouro de pilha ou falha
	assert_signal_emitted(_client, "chat_received")
	assert_signal_emitted(_client, "packet_received")


func test_adversarial_mixed_corrupt_and_valid_packet_interleaving() -> void:
	# Arrange: Conectar e vigiar sinais
	_connect_client_helper()
	watch_signals(_client)

	# Act: Enfileirar intercalação de pacotes válidos e hostis no mesmo ciclo de poll
	# 1. Byte corrompido
	_mock_peer.simulate_receive_bytes(PackedByteArray([0xFE, 0xED, 0xFA, 0xCE]))
	# 2. Pacote válido CHAT
	_mock_peer.simulate_receive_json({"type": "CHAT_MESSAGE", "payload": {"autor": "P1", "texto": "Oi"}})
	# 3. JSON sintaticamente quebrado
	_mock_peer.simulate_receive_text("{'broken_json': true,")
	# 4. Pacote válido STATE_UPDATE
	_mock_peer.simulate_receive_json({"type": "STATE_UPDATE", "payload": {"round": 99}})
	# 5. Pacote com tipo não-string
	_mock_peer.simulate_receive_text("{\"type\": [1, 2, 3]}")
	# 6. Pacote válido COMBAT_LOG
	_mock_peer.simulate_receive_json({"type": "COMBAT_LOG", "payload": {"logs": ["Log OK"]}})

	# Processar tudo de uma só vez
	_client.poll()

	# Assert:
	# - 3 pacotes válidos devem ser emitidos (CHAT, STATE_UPDATE, COMBAT_LOG)
	assert_signal_emit_count(_client, "packet_received", 3)
	assert_signal_emitted(_client, "chat_received")
	assert_signal_emitted(_client, "state_update_received")
	assert_signal_emitted(_client, "combat_log_received")
	# - 3 erros de protocolo registrados (bytes corrompidos, JSON quebrado e tipo não-string)
	assert_signal_emit_count(_client, "protocol_error", 3)
	# - Estado final preservado com o último pacote válido
	assert_eq(_client.get_last_state().get("round"), 99)

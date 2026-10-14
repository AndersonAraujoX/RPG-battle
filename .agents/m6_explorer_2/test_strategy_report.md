# Relatório Estratégico de Testes GUT: WebSocketClient (Milestone 6)

**Data de Elaboração**: 2026-10-01  
**Autor**: `m6_explorer_2` (Agente Explorer de Testes e Arquitetura GUT)  
**Destino**: `/home/anderson/Documents/projeto/RPG-battle/.agents/m6_explorer_2/test_strategy_report.md`  
**Alvo**: Especificação Completa para `godot_project/test/unit/test_websocket_client.gd`

---

## 1. Sumário Executivo

Este documento estabelece o projeto arquitetural e a especificação detalhada da suíte de testes unitários automatizados para o cliente de rede `WebSocketClient.gd` (Godot Engine 4.7), garantindo 100% de paridade com o protocolo multijogador definido no servidor FastAPI (`src/server/protocol.py`, `src/server/room_manager.py`).

### Pilares Fundamentais:
1. **Execução Headless e Offline**: Os testes unitários não dependem de um servidor FastAPI ativo, de portas abertas (`localhost:8000`) ou de sockets de rede reais do SO.
2. **Ciclo de Vida Zero-Leak (ObjectDB)**: Eliminação rigorosa de nós e objetos órfãos na memória da Godot Engine através do uso sistemático de `autofree()`, `add_child_autofree()` e descarte de referências (`RefCounted`).
3. **Padrão Obrigatório Arrange-Act-Assert (AAA)**: Estruturação estrita de todos os casos de teste em três etapas explícitas, cobrindo o caminho feliz (*happy path*), casos de borda (*edge cases*) e resiliência a falhas/exceções.
4. **Isolamento por Injeção de Dependência**: Criação do `MockWebSocketPeer` em GDScript puro, permitindo controlar e inspecionar pacotes trafegados, forçar códigos de erro e alternar estados de conexão de forma determinística e síncrona.

---

## 2. Anatomia do Framework GUT & Gestão de Memória na Godot 4

### 2.1 Análise da Implementação Local do GUT (`addons/gut/test.gd`)
A inspeção do framework local revela as seguintes características operacionais críticas:

- **Herança de `GutTest`**: `GutTest extends Node`. Cada suíte de teste é instanciada como um nó adicionado temporariamente à raiz da cena pelo executor headless (`gut_cmdln.gd:169`).
- **Execução Síncrona**: Em `gut_cmdln.gd:192`, o método `test_instance.call(m_name)` é executado **de forma síncrona**. Não há suporte a corrotinas implícitas (`await`) no laço principal do test runner. Logo, todos os testes de rede devem ser simulados e avaliados sem bloqueios assíncronos de tempo real.
- **Mecanismo `autofree(node: Node) -> Node`**:
  * Registra o nó no array interno `_autofree_nodes: Array[Node]`.
  * Se o nó não estiver na árvore e a suíte estiver, executa automaticamente `add_child(node)`.
  * No hook interno `_internal_after_each()`, executado após cada teste:
    ```gdscript
    for node in _autofree_nodes:
        if is_instance_valid(node):
            if node.get_parent() != null:
                node.get_parent().remove_child(node)
            node.free()
    _autofree_nodes.clear()
    ```
- **Monitoramento de Sinais (`watch_signals`)**:
  * Ao chamar `watch_signals(target)`, a classe `SignalReceiver` é dinamicamente acoplada a todos os sinais do objeto, registrando cada disparo em um array `emissions`.
  * No `_internal_after_each()`, todas as conexões de sinais criadas por `watch_signals` são desconectadas e limpas para evitar referências suspensas (*dangling callables*).

### 2.2 Distinção de Ciclo de Vida: `Node` vs `RefCounted`

| Tipo | Herança | Coleta de Memória | Risco de Leak no GUT | Estratégia de Mitigação |
|---|---|---|---|---|
| **WebSocketClient** | `Node` | Explícita (`free()`) | **ALTO**. Se instanciado com `.new()` sem `autofree()`, vaza no `ObjectDB`. | Sempre encapsular em `autofree(WebSocketClient.new())` ou `add_child_autofree(...)`. |
| **MockWebSocketPeer** | `RefCounted` | Automática por contagem de referências | **BAIXO**. Liberado assim que variáveis locais/membros forem zeradas (`null`). | Manter como `RefCounted`; anular referências no `after_each()`. |
| **Data Resources / Payloads** | `RefCounted` / `Resource` | Automática | **BAIXO**. Coletado ao sair do escopo. | Não requer chamada manual a `free()`. |

---

## 3. Arquitetura do Mock: `MockWebSocketPeer`

Para possibilitar testes offline determinísticos, o `WebSocketClient` deve receber seu peer de rede via **Injeção de Dependências**.

### 3.1 Interface do Peer de Rede
O `WebSocketClient.gd` deve definir uma propriedade ou setter de peer:
```gdscript
var socket: RefCounted = null # WebSocketPeer ou MockWebSocketPeer
```
Quando em produção, instancia `WebSocketPeer.new()`. Quando em testes, recebe uma instância injetada de `MockWebSocketPeer`.

### 3.2 Implementação do `MockWebSocketPeer`
O `MockWebSocketPeer` herda de `RefCounted` e espelha rigorosamente a API do `WebSocketPeer` da Godot 4:

```gdscript
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

	func connect_to_url(url: String, _tls: TLSOptions = null) -> Error:
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

	func close(code: int = 1000, reason: String = "") -> void:
		ready_state = State.STATE_CLOSED
		close_code = code
		close_reason = reason

	func get_close_code() -> int:
		return close_code

	func get_close_reason() -> String:
		return close_reason

	# ── Funções Auxiliares de Teste (Harness) ──
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

	func get_last_sent_json() -> Dictionary:
		if sent_packets.is_empty():
			return {}
		var json: JSON = JSON.new()
		if json.parse(sent_packets.back()) == OK and json.data is Dictionary:
			return json.data
		return {}

	func clear() -> void:
		sent_packets.clear()
		incoming_packets.clear()
		ready_state = State.STATE_CLOSED
		connect_url = ""
		close_code = -1
		close_reason = ""
```

---

## 4. Matriz de Cobertura e Especificações AAA dos Casos de Teste

A suíte `godot_project/test/unit/test_websocket_client.gd` é dividida em **7 seções temáticas**, totalizando **35 casos de teste** rigorosamente estruturados em Arrange-Act-Assert.

---

### SEÇÃO 1: Ciclo de Vida, Instanciação e Gestão de Memória Zero-Leak

#### Teste 1.1: `test_client_instantiation_default_state`
- **Objetivo**: Garantir que o cliente inicializa no estado desconectado, com buffers vazios e parâmetros zerados.
- **Arrange**: Instanciar `WebSocketClient` via `autofree()`.
- **Act**: Consultar `client.get_connection_state()`, `client.room_id`, `client.player_id`.
- **Assert**:
  * `assert_eq(client.get_connection_state(), WebSocketClient.STATE_DISCONNECTED)`
  * `assert_eq(client.room_id, "")`
  * `assert_eq(client.player_id, "")`
  * `assert_false(client.is_connected_to_server())`

#### Teste 1.2: `test_client_peer_injection`
- **Objetivo**: Validar a injeção do `MockWebSocketPeer` no cliente sem criar nós espúrios.
- **Arrange**: Criar `client = autofree(WebSocketClient.new())` e `mock = MockWebSocketPeer.new()`.
- **Act**: Executar `client.set_peer(mock)`.
- **Assert**:
  * `assert_eq(client.get_peer(), mock)`
  * `assert_eq(client.get_peer().get_ready_state(), MockWebSocketPeer.State.STATE_CLOSED)`

#### Teste 1.3: `test_client_autofree_lifecycle_zero_leaks`
- **Objetivo**: Confirmar que o nó e seus timers/sub-recursos são reciclados sem vazamentos no `ObjectDB`.
- **Arrange**: Criar cliente com `autofree(WebSocketClient.new())`.
- **Act**: Invocar `client.reset_state()`.
- **Assert**:
  * `assert_not_null(client)`
  * `assert_true(is_instance_valid(client))`
  * Ao final do teste, o runner `_internal_after_each()` remove e limpa o nó.

#### Teste 1.4: `test_client_reset_state_clears_buffers_and_subscriptions`
- **Objetivo**: Verificar se `reset_state()` limpa dados de sala, herói selecionado e tentativas de reconexão.
- **Arrange**: Cliente configurado com dados de sala simulados (`room_id = "ROOM1"`, `reconnect_attempts = 3`).
- **Act**: Invocar `client.reset_state()`.
- **Assert**:
  * `assert_eq(client.room_id, "")`
  * `assert_eq(client.reconnect_attempts, 0)`

---

### SEÇÃO 2: Handshake de Conexão & Formação de URLs

#### Teste 2.1: `test_connect_to_server_url_generation_standard`
- **Objetivo**: Verificar a montagem correta da URL WS com query parameters conforme `src/server/app.py`.
- **Arrange**: Cliente com mock peer injetado.
- **Act**: `client.connect_to_server("SALAX", "p_10", "Guerreiro", "127.0.0.1", 8000, false)`.
- **Assert**:
  * `assert_eq(mock.connect_url, "ws://127.0.0.1:8000/ws/SALAX/p_10?player_name=Guerreiro")`
  * `assert_eq(client.get_connection_state(), WebSocketClient.STATE_CONNECTING)`

#### Teste 2.2: `test_connect_to_server_url_generation_tls_wss`
- **Objetivo**: Testar conexão segura com esquema `wss://`.
- **Arrange**: Cliente com mock peer injetado.
- **Act**: `client.connect_to_server("SALA_PROD", "p_99", "Mago", "game.servidor.com", 443, true)`.
- **Assert**:
  * `assert_eq(mock.connect_url, "wss://game.servidor.com:443/ws/SALA_PROD/p_99?player_name=Mago")`

#### Teste 2.3: `test_poll_detects_connection_open_and_emits_signal`
- **Objetivo**: Validar transição de estado `CONNECTING -> OPEN` durante o `poll()` e emissão do sinal `connected_to_server`.
- **Arrange**:
  * Cliente configurado e monitorado via `watch_signals(client)`.
  * `client.connect_to_server("SALAX", "p_1", "Herói")`.
  * `mock.simulate_connection_established()`.
- **Act**: `client.poll()`.
- **Assert**:
  * `assert_signal_emitted(client, "connected_to_server")`
  * `assert_eq(client.get_connection_state(), WebSocketClient.STATE_CONNECTED)`
  * `assert_true(client.is_connected_to_server())`

#### Teste 2.4: `test_connect_fails_when_peer_returns_error`
- **Objetivo**: Tratar recusa imediata de conexão pelo driver de rede.
- **Arrange**: Mock configurado com `mock.should_fail_connect = true`. `watch_signals(client)`.
- **Act**: `var ok: bool = client.connect_to_server("SALA1", "p1", "Nome")`.
- **Assert**:
  * `assert_false(ok)`
  * `assert_signal_emitted(client, "connection_failed")`
  * `assert_eq(client.get_connection_state(), WebSocketClient.STATE_DISCONNECTED)`

#### Teste 2.5: `test_connect_called_while_already_connected_is_rejected`
- **Objetivo**: Prevenir conexões redundantes ou sobrescrita acidental de socket ativo.
- **Arrange**: Cliente já conectado (`client.is_connected_to_server() == true`).
- **Act**: `var res = client.connect_to_server("OUTRA_SALA", "p2", "Nome2")`.
- **Assert**:
  * `assert_false(res)`
  * `assert_eq(client.room_id, "SALAX")`

#### Teste 2.6: `test_connect_validates_required_parameters`
- **Objetivo**: Rejeitar parâmetros vazios de `room_id` ou `player_id`.
- **Arrange**: Cliente com mock peer.
- **Act**:
  * `var r1 = client.connect_to_server("", "p1", "Hero")`
  * `var r2 = client.connect_to_server("ROOM", "", "Hero")`
- **Assert**:
  * `assert_false(r1)`
  * `assert_false(r2)`

---

### SEÇÃO 3: Mensagens Tipadas Enviadas (Client -> Server)

Todos os testes desta seção verificam a serialização correta do envelope `{"type": "<TIPO>", "payload": { ... }}` conforme especificado em `src/server/protocol.py`.

#### Teste 3.1: `test_send_select_hero_formats_and_sends_packet`
- **Arrange**: Cliente conectado com mock.
- **Act**: `var ok = client.send_select_hero("Aquele")`.
- **Assert**:
  * `assert_true(ok)`
  * `var data = mock.get_last_sent_json()`
  * `assert_eq(data["type"], "SELECT_HERO")`
  * `assert_eq(data["payload"]["hero_name"], "Aquele")`

#### Teste 3.2: `test_send_start_game_formats_and_sends_packet`
- **Arrange**: Cliente conectado com mock.
- **Act**: `var ok = client.send_start_game()`.
- **Assert**:
  * `assert_true(ok)`
  * `var data = mock.get_last_sent_json()`
  * `assert_eq(data["type"], "START_GAME")`
  * `assert_eq(data["payload"].size(), 0)`

#### Teste 3.3: `test_send_select_card_formats_and_sends_packet`
- **Arrange**: Cliente conectado com mock.
- **Act**: `var ok = client.send_select_card(2)`.
- **Assert**:
  * `assert_true(ok)`
  * `var data = mock.get_last_sent_json()`
  * `assert_eq(data["type"], "SELECT_CARD")`
  * `assert_eq(data["payload"]["card_idx"], 2)`

#### Teste 3.4: `test_send_move_hero_formats_and_sends_packet`
- **Arrange**: Cliente conectado com mock.
- **Act**: `var ok = client.send_move_hero(7, 12)`.
- **Assert**:
  * `assert_true(ok)`
  * `var data = mock.get_last_sent_json()`
  * `assert_eq(data["type"], "MOVE_HERO")`
  * `assert_eq(data["payload"]["dest_x"], 7)`
  * `assert_eq(data["payload"]["dest_y"], 12)`

#### Teste 3.5: `test_send_attack_target_formats_and_sends_packet`
- **Arrange**: Cliente conectado com mock.
- **Act**: `var ok = client.send_attack_target(10, 10, "golpe_pesado")`.
- **Assert**:
  * `assert_true(ok)`
  * `var data = mock.get_last_sent_json()`
  * `assert_eq(data["type"], "ATTACK_TARGET")`
  * `assert_eq(data["payload"]["target_x"], 10)`
  * `assert_eq(data["payload"]["target_y"], 10)`
  * `assert_eq(data["payload"]["habilidade"], "golpe_pesado")`

#### Teste 3.6: `test_send_work_action_formats_and_sends_packet`
- **Arrange**: Cliente conectado com mock.
- **Act**: `var ok = client.send_work_action(5, 5, "minerar")`.
- **Assert**:
  * `assert_true(ok)`
  * `var data = mock.get_last_sent_json()`
  * `assert_eq(data["type"], "WORK_ACTION")`
  * `assert_eq(data["payload"]["target_x"], 5)`
  * `assert_eq(data["payload"]["target_y"], 5)`
  * `assert_eq(data["payload"]["tipo"], "minerar")`

#### Teste 3.7: `test_send_end_round_formats_and_sends_packet`
- **Arrange**: Cliente conectado com mock.
- **Act**: `var ok = client.send_end_round()`.
- **Assert**:
  * `assert_true(ok)`
  * `var data = mock.get_last_sent_json()`
  * `assert_eq(data["type"], "END_ROUND")`

#### Teste 3.8: `test_send_chat_message_formats_and_sends_packet`
- **Arrange**: Cliente conectado com mock.
- **Act**: `var ok = client.send_chat_message("Inimigos na muralha norte!")`.
- **Assert**:
  * `assert_true(ok)`
  * `var data = mock.get_last_sent_json()`
  * `assert_eq(data["type"], "CHAT_MESSAGE")`
  * `assert_eq(data["payload"]["text"], "Inimigos na muralha norte!")`

#### Teste 3.9: `test_send_ping_packet`
- **Arrange**: Cliente conectado com mock.
- **Act**: `var ok = client.send_ping()`.
- **Assert**:
  * `assert_true(ok)`
  * `var data = mock.get_last_sent_json()`
  * `assert_eq(data["type"], "PING")`

#### Teste 3.10: `test_generic_send_message_payload`
- **Arrange**: Cliente conectado com mock; dicionário customizado de payload.
- **Act**: `var ok = client.send_message("CUSTOM_ACTION", {"param": 42})`.
- **Assert**:
  * `assert_true(ok)`
  * `var data = mock.get_last_sent_json()`
  * `assert_eq(data["type"], "CUSTOM_ACTION")`
  * `assert_eq(data["payload"]["param"], 42)`

---

### SEÇÃO 4: Recepção de Pacotes do Servidor & Integração com EventBus

#### Teste 4.1: `test_receive_state_update_emits_signals`
- **Arrange**:
  * Cliente conectado, monitorado via `watch_signals(client)`.
  * Servidor envia `{"type": "STATE_UPDATE", "payload": {"room_id": "R1", "fase": "LOBBY"}}`.
  * `mock.simulate_receive_json(...)`.
- **Act**: `client.poll()`.
- **Assert**:
  * `assert_signal_emitted(client, "state_update_received")`
  * `assert_signal_emitted_with_parameters(client, "packet_received", ["STATE_UPDATE", {"room_id": "R1", "fase": "LOBBY"}])`

#### Teste 4.2: `test_receive_action_rejected_emits_signal`
- **Arrange**:
  * Mock insere pacote: `{"type": "ACTION_REJECTED", "payload": {"acao": "SELECT_HERO", "motivo": "Heroi ja escolhido"}}`.
  * `watch_signals(client)`.
- **Act**: `client.poll()`.
- **Assert**:
  * `assert_signal_emitted_with_parameters(client, "action_rejected_received", ["SELECT_HERO", "Heroi ja escolhido"])`

#### Teste 4.3: `test_receive_combat_log_emits_signal`
- **Arrange**:
  * Mock insere pacote: `{"type": "COMBAT_LOG", "payload": {"logs": ["[DADOS] D6 rolou 4"]}}`.
  * `watch_signals(client)`.
- **Act**: `client.poll()`.
- **Assert**:
  * `assert_signal_emitted(client, "combat_log_received")`

#### Teste 4.4: `test_receive_multiple_packets_in_single_poll`
- **Arrange**:
  * Mock enfileira 3 pacotes sucessivos: `ROOM_STATE`, `STATE_UPDATE` e `COMBAT_LOG`.
  * `watch_signals(client)`.
- **Act**: `client.poll()`.
- **Assert**:
  * `assert_signal_emit_count(client, "packet_received", 3)`

#### Teste 4.5: `test_event_bus_relay_of_network_message`
- **Arrange**:
  * Monitorar `EventBus` via `watch_signals(EventBus)`.
  * Injetar pacote no mock.
- **Act**: `client.poll()`.
- **Assert**:
  * `assert_signal_emitted_with_parameters(EventBus, "network_message_received", ["STATE_UPDATE", {"fase": "COMBATE"}])`

#### Teste 4.6: `test_receive_game_started_emits_specific_signal`
- **Arrange**: Mock insere pacote `{"type": "GAME_STARTED", "payload": {}}`.
- **Act**: `client.poll()`.
- **Assert**: `assert_signal_emitted(client, "game_started_received")`

---

### SEÇÃO 5: Cargas Adversariais, Robustez & Casos de Borda

#### Teste 5.1: `test_receive_empty_string_ignored_safely`
- **Arrange**: Mock recebe payload em branco: `""`. `watch_signals(client)`.
- **Act**: `client.poll()`.
- **Assert**:
  * `assert_signal_not_emitted(client, "packet_received")`
  * Nenhum crash ou erro de execução.

#### Teste 5.2: `test_receive_whitespace_string_ignored_safely`
- **Arrange**: Mock recebe payload de espaços e quebras de linha: `"   \t \n  "`.
- **Act**: `client.poll()`.
- **Assert**: `assert_signal_not_emitted(client, "packet_received")`

#### Teste 5.3: `test_receive_malformed_syntax_json_rejected`
- **Arrange**:
  * Mock enfileira JSON inválido: `"{'key': unclosed_val"`.
  * `watch_signals(client)`.
- **Act**: `client.poll()`.
- **Assert**:
  * `assert_signal_not_emitted(client, "packet_received")`
  * `assert_signal_emitted(client, "protocol_error")`

#### Teste 5.4: `test_receive_root_array_json_rejected`
- **Arrange**: Mock envia um array JSON na raiz: `[{"type": "TEST"}]`.
- **Act**: `client.poll()`.
- **Assert**:
  * Envelope rejeitado pois espera-se um dicionário com chave `"type"`.
  * `assert_signal_not_emitted(client, "packet_received")`

#### Teste 5.5: `test_receive_primitive_root_json_rejected`
- **Arrange**: Mock envia números ou booleanos: `"12345"` ou `"true"`.
- **Act**: `client.poll()`.
- **Assert**: `assert_signal_not_emitted(client, "packet_received")`

#### Teste 5.6: `test_receive_missing_type_field_rejected`
- **Arrange**: Dicionário sem a chave `"type"`: `{"payload": {"data": 1}}`.
- **Act**: `client.poll()`.
- **Assert**: `assert_signal_not_emitted(client, "packet_received")`

#### Teste 5.7: `test_receive_non_string_type_field_rejected`
- **Arrange**: Chave `"type"` numérica: `{"type": 100, "payload": {}}`.
- **Act**: `client.poll()`.
- **Assert**: `assert_signal_not_emitted(client, "packet_received")`

#### Teste 5.8: `test_receive_missing_payload_defaults_to_empty_dict`
- **Arrange**: Pacote contendo apenas `"type"`: `{"type": "HEARTBEAT"}`.
- **Act**: `client.poll()`.
- **Assert**:
  * `assert_signal_emitted_with_parameters(client, "packet_received", ["HEARTBEAT", {}])`

#### Teste 5.9: `test_receive_unknown_message_type_graceful`
- **Arrange**: Pacote com tipo desconhecido: `{"type": "UNKNOWN_FUTURE_EVENT", "payload": {}}`.
- **Act**: `client.poll()`.
- **Assert**:
  * Cliente emite `packet_received` sem falha catastrófica.

#### Teste 5.10: `test_send_message_when_disconnected_returns_false`
- **Arrange**: Cliente no estado `DISCONNECTED`.
- **Act**: `var res = client.send_select_hero("Stark")`.
- **Assert**:
  * `assert_false(res)`
  * Mock não recebe nenhum pacote.

---

### SEÇÃO 6: Falhas de Rede, Quedas & Encerramento de Conexão

#### Teste 6.1: `test_clean_server_disconnect_emits_connection_closed`
- **Arrange**:
  * Cliente conectado.
  * Mock simula fechamento normal: `mock.simulate_server_disconnect(1000, "Room Closed")`.
  * `watch_signals(client)`.
- **Act**: `client.poll()`.
- **Assert**:
  * `assert_signal_emitted_with_parameters(client, "connection_closed", [1000, "Room Closed", true])`
  * `assert_eq(client.get_connection_state(), WebSocketClient.STATE_DISCONNECTED)`

#### Teste 6.2: `test_abnormal_disconnect_emits_connection_closed`
- **Arrange**:
  * Mock simula queda inesperada: `mock.simulate_abnormal_disconnect()` (código 1006).
  * `watch_signals(client)`.
- **Act**: `client.poll()`.
- **Assert**:
  * `assert_signal_emitted_with_parameters(client, "connection_closed", [1006, "Abnormal Disconnect", false])`

#### Teste 6.3: `test_disconnect_from_server_client_initiated`
- **Arrange**: Cliente conectado com mock.
- **Act**: `client.disconnect_from_server(1000, "Player Quit")`.
- **Assert**:
  * `assert_eq(mock.close_code, 1000)`
  * `assert_eq(mock.close_reason, "Player Quit")`
  * `assert_eq(client.get_connection_state(), WebSocketClient.STATE_DISCONNECTED)`

#### Teste 6.4: `test_poll_when_peer_is_null_safe`
- **Arrange**: Cliente instanciado sem peer atribuído.
- **Act**: `client.poll()`.
- **Assert**:
  * A chamada executa de forma segura sem crash (*null pointer safety*).

---

### SEÇÃO 7: Lógica de Reconexão Automática & Backoff

#### Teste 7.1: `test_auto_reconnect_disabled_by_default_or_toggleable`
- **Arrange**: Cliente instanciado com flag `auto_reconnect = false`.
- **Act**: Mock simula queda anormal (código 1006). `client.poll()`.
- **Assert**:
  * `assert_false(client.is_reconnecting)`
  * `assert_eq(client.reconnect_attempts, 0)`

#### Teste 7.2: `test_auto_reconnect_triggers_on_unexpected_disconnect`
- **Arrange**:
  * Cliente configurado com `auto_reconnect = true` e `max_reconnect_attempts = 3`.
  * `watch_signals(client)`.
  * Mock simula código 1006.
- **Act**: `client.poll()`.
- **Assert**:
  * `assert_signal_emitted_with_parameters(client, "reconnecting", [1, 3])`
  * `assert_true(client.is_reconnecting)`

#### Teste 7.3: `test_auto_reconnect_does_not_trigger_on_clean_disconnect`
- **Arrange**:
  * `client.auto_reconnect = true`.
  * Mock simula desconexão limpa código 1000 ("Normal Closure").
- **Act**: `client.poll()`.
- **Assert**:
  * `assert_false(client.is_reconnecting)`
  * `assert_signal_not_emitted(client, "reconnecting")`

#### Teste 7.4: `test_reconnect_retry_counter_and_failure_signal`
- **Arrange**:
  * Cliente com `max_reconnect_attempts = 2`.
  * Mock configurado para falhar novas conexões (`mock.should_fail_connect = true`).
  * `watch_signals(client)`.
- **Act**:
  * Simular 1ª falha e tentativa.
  * Simular 2ª falha e tentativa excedida.
- **Assert**:
  * `assert_signal_emitted(client, "reconnect_failed")`
  * `assert_false(client.is_reconnecting)`

#### Teste 7.5: `test_reconnect_success_resets_retry_counter`
- **Arrange**: Cliente estava em processo de reconexão (`reconnect_attempts = 2`).
- **Act**: Mock restabelece conexão (`mock.simulate_connection_established()`). `client.poll()`.
- **Assert**:
  * `assert_signal_emitted(client, "reconnected")`
  * `assert_eq(client.reconnect_attempts, 0)`
  * `assert_false(client.is_reconnecting)`

---

## 5. Estrutura do Arquivo de Teste (`test_websocket_client.gd`)

Abaixo está o esqueleto padronizado para o arquivo de teste:

```gdscript
# res://test/unit/test_websocket_client.gd
extends GutTest

## Suíte Canônica de Testes GUT para Milestone 6:
## Cliente de Rede Co-op WebSocket (WebSocketClient.gd)
##
## Adere estritamente ao padrão Arrange-Act-Assert (AAA) e zero ObjectDB leaks.

const WebSocketClientScript = preload("res://scripts/network/WebSocketClient.gd")

var _client: Node = null
var _mock_peer: RefCounted = null

func before_each() -> void:
	_client = autofree(WebSocketClientScript.new())
	_mock_peer = MockWebSocketPeer.new()
	_client.set_peer(_mock_peer)

func after_each() -> void:
	if _client != null and _client.has_method("reset_state"):
		_client.reset_state()
	_client = null
	_mock_peer = null

# ==============================================================================
# SEÇÕES 1 A 7: IMPLEMENTAÇÃO DOS 35 CASOS DE TESTE AAA
# ==============================================================================
```

---

## 6. Verificação Automatizada e Critérios de Aceite

A verificação deve ser executada pelo runner oficial do projeto:

```bash
/home/anderson/Documents/projeto/RPG-battle/godot_project/run_gut_tests.sh
```

### Critérios Obrigatórios:
- **Taxa de Sucesso**: 100% dos testes aprovados (Exit code: 0).
- **Vazamentos no ObjectDB**: 0 vazamentos na saída do console.
- **Isolamento de Rede**: Nenhum socket real de SO aberto durante a execução.
- **Performance**: Execução completa da suíte de 35 testes em menos de 100ms.

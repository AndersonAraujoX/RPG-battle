# res://test/unit/test_forge_system.gd
extends GutTest

## Testes unitários para o sistema da Forja Anã (ForgeScreen e serviços do nó FORGE).
## Valida geração determinística de inventário (3 cartas, 2 relíquias), compra com ouro,
## serviço de expurgo com custo progressivo, limite de segurança de 5 cartas no deck,
## exclusão de relíquias duplicadas, e integração de descontos com RelicManager.

var _state: RunState
var _generator: RunMapGenerator
var _rng: RandomNumberGenerator
var _forge: ForgeScreen

func before_each() -> void:
	_generator = RunMapGenerator.new(6, 3, 2)
	_rng = RandomNumberGenerator.new()
	_rng.seed = 1337
	_state = RunState.new(_generator, _rng)
	
	var starter_deck: Array[String] = [
		"movimento", "movimento", "movimento",
		"trabalho", "trabalho",
		"escavacao", "escavacao",
		"ataque", "ataque", "defesa"
	] # 10 cartas
	_state.start_run({"aquele": 30, "stark": 34, "elden": 26}, starter_deck, 1337)
	_state.gold = 200 # Saldo suficiente para compras nos testes
	
	_forge = autofree(ForgeScreen.new())
	_forge.setup(_state, null, _rng)

func after_each() -> void:
	RunSession.clear()
	_forge = null
	_state = null
	_generator = null
	_rng = null

# ── 1. Headless Safety & Inicialização ───────────────────────────────────────

func test_forge_bare_node_headless_safety() -> void:
	# Arrange
	var bare: ForgeScreen = autofree(ForgeScreen.new())

	# Act & Assert (não deve falhar nem disparar null pointer em modo headless)
	bare._ready()
	bare.refresh_ui()
	assert_not_null(bare, "Bare ForgeScreen deve inicializar com segurança sem .tscn")

func test_forge_setup_generates_inventory_sizes() -> void:
	# Arrange & Act já realizados no before_each()
	
	# Assert
	assert_eq(_forge.card_inventory.size(), 3, "Forja deve oferecer exatamente 3 cartas")
	assert_eq(_forge.relic_inventory.size(), 2, "Forja deve oferecer exatamente 2 relíquias")
	assert_eq(_forge.purges_performed, 0, "Expurgos começam em zero")

# ── 2. Compra de Cartas ──────────────────────────────────────────────────────

func test_buy_card_happy_path() -> void:
	# Arrange
	var initial_gold: int = _state.gold
	var initial_deck_size: int = _state.deck.size()
	var slot0: Dictionary = _forge.card_inventory[0]
	var cost: int = int(slot0["cost"])
	var card_id: String = slot0["id"]

	# Act
	var success: bool = _forge.buy_card(0)

	# Assert
	assert_true(success, "Compra de carta com ouro suficiente deve ter sucesso")
	assert_eq(_state.gold, initial_gold - cost, "Ouro deve ser deduzido com exatidão")
	assert_eq(_state.deck.size(), initial_deck_size + 1, "Deck deve ter +1 carta")
	assert_true(_state.deck.has(card_id), "Carta comprada deve constar no deck")
	assert_true(_forge.card_inventory[0]["sold"], "Slot deve estar marcado como vendido")

func test_buy_card_insufficient_gold_fails() -> void:
	# Arrange
	_state.gold = 10 # Insuficiente para qualquer carta (preço mínimo 45)
	var initial_deck_size: int = _state.deck.size()

	# Act
	var success: bool = _forge.buy_card(0)

	# Assert
	assert_false(success, "Compra com ouro insuficiente deve falhar")
	assert_eq(_state.gold, 10, "Ouro não deve sofrer alteração")
	assert_eq(_state.deck.size(), initial_deck_size, "Nenhuma carta adicionada ao deck")
	assert_false(_forge.card_inventory[0]["sold"], "Slot continua disponível para compra")

func test_buy_card_already_sold_slot_fails() -> void:
	# Arrange
	_forge.buy_card(0) # Primeira compra: sucesso
	var gold_after_first: int = _state.gold

	# Act: Tentar comprar o mesmo slot novamente
	var second_buy: bool = _forge.buy_card(0)

	# Assert
	assert_false(second_buy, "Slot já vendido não pode ser comprado novamente")
	assert_eq(_state.gold, gold_after_first, "Nenhum ouro adicional debitado")

# ── 3. Compra de Relíquias ───────────────────────────────────────────────────

func test_buy_relic_happy_path() -> void:
	# Arrange
	var initial_gold: int = _state.gold
	var slot0: Dictionary = _forge.relic_inventory[0]
	var cost: int = int(slot0["cost"])
	var relic_id: String = slot0["id"]

	# Act
	var success: bool = _forge.buy_relic(0)

	# Assert
	assert_true(success, "Compra de relíquia com ouro suficiente deve ter sucesso")
	assert_eq(_state.gold, initial_gold - cost, "Ouro deduzido corretamente")
	assert_true(_state.has_relic(relic_id), "Relíquia adicionada ao RunState.relics")
	assert_true(_forge.relic_inventory[0]["sold"], "Slot marcado como vendido")

func test_relic_inventory_excludes_already_owned_relics() -> void:
	# Arrange: Adicionar todas as relíquias exceto duas ao estado
	_state.add_relic("martelo_runico")
	_state.add_relic("escudo_ancestral")
	_state.add_relic("bolsa_do_mercador")
	_state.add_relic("amuleto_ambar")
	_state.add_relic("dente_da_viuva")
	_state.add_relic("tocha_eterna")
	_state.add_relic("oleo_alquimico")
	_state.add_relic("frasco_feromonio")
	# Restam apenas: "coroa_quitina" e "relogio_da_forja"

	# Act: Regerar inventário
	_forge.generate_inventory()

	# Assert
	for slot in _forge.relic_inventory:
		assert_false(_state.has_relic(slot["id"]), "Relíquias já possuídas não podem ser oferecidas no mercado")

# ── 4. Serviço de Expurgo de Cartas (Deck Thinning) ──────────────────────────

func test_card_purge_progressive_cost() -> void:
	# Arrange & Assert Custo Inicial
	assert_eq(_forge.get_current_purge_cost(), 50, "1ª remoção deve custar 50 ouro")
	var initial_deck_size: int = _state.deck.size()

	# Act 1: 1º Expurgo
	var p1: bool = _forge.purge_card("movimento")

	# Assert 1
	assert_true(p1, "1º expurgo com saldo suficiente deve ter sucesso")
	assert_eq(_state.deck.size(), initial_deck_size - 1, "Deck reduzido em 1 carta")
	assert_eq(_forge.purges_performed, 1, "Contador de expurgos incrementado para 1")
	assert_eq(_forge.get_current_purge_cost(), 75, "2ª remoção deve custar 75 ouro (50 + 25)")

	# Act 2: Resetar permissão de visita para testar o custo da 2ª remoção
	_forge.purge_used_this_visit = false
	var p2: bool = _forge.purge_card("trabalho")

	# Assert 2
	assert_true(p2, "2º expurgo deve ser realizado com sucesso")
	assert_eq(_forge.purges_performed, 2, "Contador de expurgos incrementado para 2")
	assert_eq(_forge.get_current_purge_cost(), 100, "3ª remoção deve custar 100 ouro (50 + 50)")

func test_card_purge_enforces_minimum_safe_deck_limit() -> void:
	# Arrange: Reduzir deck artificialmente até exatamente 5 cartas
	_state.deck = ["carta_1", "carta_2", "carta_3", "carta_4", "carta_5"]
	assert_eq(_state.deck.size(), 5)

	# Act: Tentar expurgar com deck no limite mínimo
	var check: Dictionary = _forge.can_purge_card()
	var success: bool = _forge.purge_card("carta_1")

	# Assert
	assert_false(check["can"], "can_purge_card deve retornar falso no limite mínimo")
	assert_true(check["reason"].contains("Deck mínimo"), "Motivo deve citar deck mínimo")
	assert_false(success, "purge_card deve falhar quando deck <= 5 cartas")
	assert_eq(_state.deck.size(), 5, "Nenhuma carta removida do deck")
	assert_eq(_state.gold, 200, "Nenhum ouro deduzido na tentativa bloqueada")

func test_card_purge_single_use_per_visit() -> void:
	# Arrange
	_forge.purge_card("movimento")
	assert_true(_forge.purge_used_this_visit)

	# Act: Tentar expurgar segunda vez na mesma visita
	var check: Dictionary = _forge.can_purge_card()
	var success: bool = _forge.purge_card("trabalho")

	# Assert
	assert_false(check["can"], "Não pode expurgar duas vezes na mesma visita da Forja")
	assert_false(success, "Segunda tentativa de expurgo na mesma visita rejeitada")

# ── 5. Desconto de Relíquias (RelicManager Integration) ───────────────────────

func test_forge_discount_with_relogio_da_forja() -> void:
	# Arrange: Conceder a relíquia relogio_da_forja ao estado
	_state.add_relic("relogio_da_forja")

	# Act: Regerar inventário com a relíquia ativa
	_forge.generate_inventory()

	# Assert: Itens devem receber 20% de desconto
	var card_slot = _forge.card_inventory[0]
	var base_card_cost: int = int(card_slot["base_cost"])
	var expected_card_cost: int = int(round(float(base_card_cost) * 0.80))
	assert_eq(int(card_slot["cost"]), expected_card_cost, "Carta deve ter 20% de desconto")

	var purge_cost: int = _forge.get_current_purge_cost()
	assert_eq(purge_cost, 40, "Expurgo base de 50g deve cair para 40g (50 * 0.80)")

# ── 6. Saída e Conclusão de Nó ───────────────────────────────────────────────

func test_close_forge_completes_current_node() -> void:
	# Arrange: Mover estado para um nó de forja
	var forge_node: RunNode = RunNode.new(9999, 1, 1, 0, RunNode.NodeType.FORGE)
	var added: bool = _state.map.add_node(forge_node)
	assert_true(added, "Nó deve ser adicionado ao mapa")
	_state.current_node_id = 9999
	assert_false(forge_node.visited)

	var signal_emitted: Array = []
	_forge.forge_closed.connect(func(): signal_emitted.append(true))

	# Act
	_forge.close_forge()

	# Assert
	assert_eq(signal_emitted.size(), 1, "Sinal forge_closed deve ser emitido")
	assert_true(forge_node.visited, "Nó FORGE deve ser marcado como concluído ao sair")

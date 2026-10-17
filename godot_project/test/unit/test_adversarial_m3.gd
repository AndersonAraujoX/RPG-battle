# res://test/unit/test_adversarial_m3.gd
extends GutTest

## Testes Adversariais Empíricos para o Milestone M3 (Challenger 2).
## Stress-testa:
## 1. Economia extrema (0 ouro, compra exata de ouro, tentativas de ouro negativo).
## 2. Invariante de deck mínimo seguro de 5 cartas e expurgo com Bigorna Ancestral.
## 3. Reentrância, duplo clique rápido e injeção de IDs inválidos em RewardModal e ForgeScreen.
## 4. Exaustão de pools de cartas e relíquias (jogador que possui 100% das relíquias).
## 5. Falhas de limite, bounds checking de slots e estabilidade headless.

var _state: RunState
var _generator: RunMapGenerator
var _rng: RandomNumberGenerator
var _manager: RelicManager

func before_each() -> void:
	_generator = RunMapGenerator.new(6, 3, 2)
	_rng = RandomNumberGenerator.new()
	_rng.seed = 4242
	_state = RunState.new(_generator, _rng)
	
	var starter_deck: Array[String] = [
		"movimento", "movimento", "movimento",
		"trabalho", "trabalho",
		"escavacao", "escavacao",
		"ataque", "ataque", "defesa"
	] # 10 cartas
	_state.start_run({"aquele": 30, "stark": 34, "elden": 26}, starter_deck, 4242)
	_state.gold = 100
	
	_manager = RelicManager.new(_state)

func after_each() -> void:
	if _manager != null:
		_manager.unregister_all()
		_manager = null
	RunSession.clear()
	_state = null
	_generator = null
	_rng = null

# ==============================================================================
# GRUPO A: Economia Extrema (0 Ouro, Compra Exata, Ouro Negativo)
# ==============================================================================

func test_forge_zero_gold_rejects_card_purchase() -> void:
	# Arrange
	_state.gold = 0
	var forge: ForgeScreen = autofree(ForgeScreen.new())
	forge.setup(_state, _manager, _rng)
	var initial_deck_size: int = _state.deck.size()

	# Act
	var result: bool = forge.buy_card(0)

	# Assert
	assert_false(result, "Compra de carta com 0 de ouro deve ser terminantemente rejeitada")
	assert_eq(_state.gold, 0, "Ouro deve permanecer em 0")
	assert_eq(_state.deck.size(), initial_deck_size, "Deck não deve receber nova carta")
	assert_false(forge.card_inventory[0]["sold"], "Slot não pode ser marcado como vendido")

func test_forge_zero_gold_rejects_relic_purchase() -> void:
	# Arrange
	_state.gold = 0
	var forge: ForgeScreen = autofree(ForgeScreen.new())
	forge.setup(_state, _manager, _rng)
	var initial_relics_count: int = _state.relics.size()

	# Act
	var result: bool = forge.buy_relic(0)

	# Assert
	assert_false(result, "Compra de relíquia com 0 de ouro deve ser terminantemente rejeitada")
	assert_eq(_state.gold, 0, "Ouro deve permanecer em 0")
	assert_eq(_state.relics.size(), initial_relics_count, "Nenhuma relíquia adicionada")
	assert_false(forge.relic_inventory[0]["sold"], "Slot não pode ser marcado como vendido")

func test_forge_zero_gold_rejects_card_purge() -> void:
	# Arrange
	_state.gold = 0
	var forge: ForgeScreen = autofree(ForgeScreen.new())
	forge.setup(_state, _manager, _rng)
	var initial_deck_size: int = _state.deck.size()

	# Act
	var check: Dictionary = forge.can_purge_card()
	var result: bool = forge.purge_card("movimento")

	# Assert
	assert_false(check["can"], "can_purge_card deve retornar falso com 0 de ouro")
	assert_true(check["reason"].contains("Ouro insuficiente"), "Motivo deve apontar ouro insuficiente")
	assert_false(result, "purge_card deve falhar com 0 de ouro")
	assert_eq(_state.deck.size(), initial_deck_size, "Nenhuma carta removida")
	assert_eq(_state.gold, 0, "Ouro permanece 0")

func test_forge_exact_gold_card_purchase_leaves_zero_gold() -> void:
	# Arrange
	var forge: ForgeScreen = autofree(ForgeScreen.new())
	forge.setup(_state, _manager, _rng)
	var card_cost: int = int(forge.card_inventory[0]["cost"])
	_state.gold = card_cost # Saldo exatamente igual ao preço
	var card_id: String = forge.card_inventory[0]["id"]
	var initial_deck_size: int = _state.deck.size()

	# Act: Compra com saldo exato
	var first_buy: bool = forge.buy_card(0)

	# Assert
	assert_true(first_buy, "Compra com saldo exato deve ter sucesso")
	assert_eq(_state.gold, 0, "Ouro deve resultar exatamente em zero")
	assert_eq(_state.deck.size(), initial_deck_size + 1, "Deck aumentou em 1 carta")
	assert_true(_state.deck.has(card_id), "Carta comprada está no deck")
	assert_true(forge.card_inventory[0]["sold"], "Slot 0 está vendido")

	# Tentativa imediata de compra seguinte com saldo 0
	var second_buy: bool = forge.buy_card(1)
	assert_false(second_buy, "Compra subsequente com 0 de ouro restante deve falhar")

func test_forge_exact_gold_relic_purchase_leaves_zero_gold() -> void:
	# Arrange
	var forge: ForgeScreen = autofree(ForgeScreen.new())
	forge.setup(_state, _manager, _rng)
	var relic_cost: int = int(forge.relic_inventory[0]["cost"])
	_state.gold = relic_cost # Saldo exatamente igual ao preço
	var relic_id: String = forge.relic_inventory[0]["id"]

	# Act
	var success: bool = forge.buy_relic(0)

	# Assert
	assert_true(success, "Compra de relíquia com saldo exato deve ter sucesso")
	assert_eq(_state.gold, 0, "Ouro deve zerar com exatidão")
	assert_true(_state.has_relic(relic_id), "Relíquia foi concedida ao RunState")
	assert_true(forge.relic_inventory[0]["sold"], "Slot vendido")

func test_forge_exact_gold_purge_leaves_zero_gold() -> void:
	# Arrange: Deck com 6 cartas, ouro exatamente 50 (custo do 1º expurgo)
	_state.deck = ["c1", "c2", "c3", "c4", "c5", "c6"]
	_state.gold = 50
	var forge: ForgeScreen = autofree(ForgeScreen.new())
	forge.setup(_state, _manager, _rng)

	# Act
	var success: bool = forge.purge_card("c6")

	# Assert
	assert_true(success, "Expurgo com saldo exato de 50g deve ter sucesso")
	assert_eq(_state.gold, 0, "Ouro deve zerar com exatidão")
	assert_eq(_state.deck.size(), 5, "Deck reduzido para exatamente 5 cartas")
	assert_false(_state.deck.has("c6"), "Carta c6 foi removida")

	# Agora reseta a visita da forja e tenta expurgar novamente:
	# Deve ser bloqueado por AMBOS os motivos: Deck mínimo (5 cartas) E 0 de ouro!
	forge.purge_used_this_visit = false
	var check2: Dictionary = forge.can_purge_card()
	assert_false(check2["can"], "Expurgo seguinte deve ser barrado")
	assert_true(check2["reason"].contains("Deck mínimo"), "Bloqueio de deck mínimo tem prioridade")

func test_negative_gold_protection_in_runstate_and_forge() -> void:
	# Arrange
	_state.gold = 50

	# Act & Assert RunState
	var spend_neg: bool = _state.spend_gold(-10)
	assert_false(spend_neg, "spend_gold negativo deve retornar falso")
	assert_eq(_state.gold, 50, "Ouro inalterado após tentativa de gasto negativo")

	var add_neg: bool = _state.add_gold(-20)
	assert_false(add_neg, "add_gold negativo deve retornar falso")
	assert_eq(_state.gold, 50, "Ouro inalterado após tentativa de adição negativa")

	# Se estado for forçado artificialmente a ouro negativo:
	_state.gold = -10
	var forge: ForgeScreen = autofree(ForgeScreen.new())
	forge.setup(_state, _manager, _rng)

	assert_false(forge.buy_card(0), "Tentativa de compra de carta com saldo negativo deve falhar")
	assert_false(forge.buy_relic(0), "Tentativa de compra de relíquia com saldo negativo deve falhar")
	assert_false(forge.purge_card("movimento"), "Tentativa de expurgo com saldo negativo deve falhar")

# ==============================================================================
# GRUPO B: Limite Mínimo de 5 Cartas e Expurgo
# ==============================================================================

func test_purge_when_deck_has_exactly_5_cards_is_strictly_blocked() -> void:
	# Arrange: Deck com exatamente 5 cartas e muito ouro
	_state.deck = ["carta_a", "carta_b", "carta_c", "carta_d", "carta_e"]
	_state.gold = 500
	var forge: ForgeScreen = autofree(ForgeScreen.new())
	forge.setup(_state, _manager, _rng)

	# Act
	var check: Dictionary = forge.can_purge_card()
	var result: bool = forge.purge_card("carta_a")

	# Assert
	assert_false(check["can"], "can_purge_card deve retornar falso com deck em 5 cartas")
	assert_true(check["reason"].contains("Deck mínimo atingido (5 cartas)"), "Mensagem informativa explícita")
	assert_false(result, "purge_card deve retornar falso")
	assert_eq(_state.deck.size(), 5, "Nenhuma carta pode ser removida")
	assert_eq(_state.gold, 500, "Nenhum ouro pode ser debitado")

func test_purge_when_deck_has_fewer_than_5_cards_is_strictly_blocked() -> void:
	# Arrange: Deck corrompido ou anômalo com 3 cartas
	_state.deck = ["c1", "c2", "c3"]
	_state.gold = 500
	var forge: ForgeScreen = autofree(ForgeScreen.new())
	forge.setup(_state, _manager, _rng)

	# Act
	var check: Dictionary = forge.can_purge_card()
	var result: bool = forge.purge_card("c1")

	# Assert
	assert_false(check["can"])
	assert_false(result)
	assert_eq(_state.deck.size(), 3)
	assert_eq(_state.gold, 500)

func test_purge_duplicate_cards_removes_single_instance_and_respects_limit() -> void:
	# Arrange: Deck de 6 cartas com cópias idênticas
	_state.deck = ["ataque", "ataque", "ataque", "defesa", "trabalho", "escavacao"]
	_state.gold = 300
	var forge: ForgeScreen = autofree(ForgeScreen.new())
	forge.setup(_state, _manager, _rng)

	# Act 1: Expurgar um "ataque"
	var p1: bool = forge.purge_card("ataque")

	# Assert 1
	assert_true(p1, "1º expurgo do 'ataque' deve ter sucesso")
	assert_eq(_state.deck.size(), 5, "Deck reduzido de 6 para 5")
	# Ainda deve haver exatamente 2 "ataque" no deck
	var count_ataque: int = 0
	for c in _state.deck:
		if c == "ataque":
			count_ataque += 1
	assert_eq(count_ataque, 2, "Apenas uma cópia foi removida")

	# Act 2: Tentar expurgar o segundo "ataque" em visita subsequente
	forge.purge_used_this_visit = false
	var p2: bool = forge.purge_card("ataque")

	# Assert 2: Bloqueado pelo limite de 5 cartas
	assert_false(p2, "2º expurgo bloqueado pois deck já atingiu o limite de 5 cartas")
	assert_eq(_state.deck.size(), 5, "Deck permanece em 5 cartas")

func test_purge_nonexistent_card_fails_without_spending_gold() -> void:
	# Arrange
	_state.gold = 200
	var initial_deck_size: int = _state.deck.size()
	var forge: ForgeScreen = autofree(ForgeScreen.new())
	forge.setup(_state, _manager, _rng)

	# Act
	var result: bool = forge.purge_card("carta_fantasma_inexistente")

	# Assert
	assert_false(result, "Expurgar carta inexistente deve falhar")
	assert_eq(_state.gold, 200, "Nenhum ouro debitado na falha")
	assert_eq(_state.deck.size(), initial_deck_size, "Tamanho do deck intacto")
	assert_eq(forge.purges_performed, 0, "Contador de expurgos não avançou")
	assert_false(forge.purge_used_this_visit, "Serviço da visita não foi queimado")

# ==============================================================================
# GRUPO C: Reentrância, Duplo Clique e Anti-Trapaça
# ==============================================================================

func test_reward_modal_rapid_double_claim_select_card() -> void:
	# Arrange
	var modal: RewardModal = autofree(RewardModal.new())
	var node: RunNode = RunNode.new(1, 1, 0, 0, RunNode.NodeType.COMBAT)
	modal.setup(_state, node, _rng)
	modal._ready()

	var card_a: String = modal.card_options[0].id
	var card_b: String = modal.card_options[1].id
	var initial_gold: int = _state.gold
	var initial_deck_size: int = _state.deck.size()

	# Act: Primeiro clique e segundo clique imediato (duplo clique)
	var first_click: bool = modal.select_card(card_a)
	var second_click: bool = modal.select_card(card_b)

	# Assert
	assert_true(first_click, "Primeiro claim deve ser aceito")
	assert_false(second_click, "Segundo claim rápido deve ser estritamente rejeitado")
	assert_eq(_state.gold, initial_gold + 15, "Ouro deve ser concedido apenas uma vez (+15)")
	assert_eq(_state.deck.size(), initial_deck_size + 1, "Apenas uma carta adicionada ao deck")
	assert_true(_state.deck.has(card_a), "Carta A adicionada")
	assert_false(_state.deck.has(card_b), "Carta B não adicionada")

func test_reward_modal_select_card_then_skip_card_rejected() -> void:
	# Arrange
	var modal: RewardModal = autofree(RewardModal.new())
	var node: RunNode = RunNode.new(1, 1, 0, 0, RunNode.NodeType.COMBAT)
	modal.setup(_state, node, _rng)
	modal._ready()

	var card_id: String = modal.card_options[0].id
	var initial_gold: int = _state.gold

	# Act
	assert_true(modal.select_card(card_id))
	var skip_after_select: bool = modal.skip_card()

	# Assert
	assert_false(skip_after_select, "skip_card após select_card deve ser rejeitado")
	assert_eq(_state.gold, initial_gold + 15, "Ouro não foi duplicado")

func test_reward_modal_skip_card_then_select_card_rejected() -> void:
	# Arrange
	var modal: RewardModal = autofree(RewardModal.new())
	var node: RunNode = RunNode.new(1, 1, 0, 0, RunNode.NodeType.COMBAT)
	modal.setup(_state, node, _rng)
	modal._ready()

	var card_id: String = modal.card_options[0].id
	var initial_deck_size: int = _state.deck.size()

	# Act
	assert_true(modal.skip_card())
	var select_after_skip: bool = modal.select_card(card_id)

	# Assert
	assert_false(select_after_skip, "select_card após skip_card deve ser rejeitado")
	assert_eq(_state.deck.size(), initial_deck_size, "Nenhuma carta adicionada")

func test_reward_modal_unoffered_card_injection_rejected() -> void:
	# Arrange
	var modal: RewardModal = autofree(RewardModal.new())
	var node: RunNode = RunNode.new(1, 1, 0, 0, RunNode.NodeType.COMBAT)
	modal.setup(_state, node, _rng)
	modal._ready()

	# Act: Injetar ID que não foi ofertado
	var injected: bool = modal.select_card("carta_super_cheat_999")

	# Assert
	assert_false(injected, "Carta não ofertada deve ser rejeitada")
	assert_false(modal.is_claimed, "Modal não deve ser considerado reivindicado")
	assert_false(_state.deck.has("carta_super_cheat_999"))

	# Reivindicação legítima subsequente deve continuar funcionando
	var legit_id: String = modal.card_options[0].id
	assert_true(modal.select_card(legit_id), "Seleção legítima subsequente funciona normalmente")

func test_forge_rapid_double_click_purchases() -> void:
	# Arrange
	_state.gold = 300
	var forge: ForgeScreen = autofree(ForgeScreen.new())
	forge.setup(_state, _manager, _rng)
	var card_cost: int = int(forge.card_inventory[0]["cost"])
	var initial_gold: int = _state.gold
	var initial_deck_size: int = _state.deck.size()

	# Act: Duplo clique no mesmo slot de carta
	var buy1: bool = forge.buy_card(0)
	var buy2: bool = forge.buy_card(0)

	# Assert
	assert_true(buy1)
	assert_false(buy2, "Segunda compra do mesmo slot é rejeitada")
	assert_eq(_state.gold, initial_gold - card_cost, "Ouro debitado apenas uma vez")
	assert_eq(_state.deck.size(), initial_deck_size + 1, "Carta adicionada apenas uma vez")

	# Duplo clique no mesmo slot de relíquia
	var relic_cost: int = int(forge.relic_inventory[0]["cost"])
	var rbuy1: bool = forge.buy_relic(0)
	var rbuy2: bool = forge.buy_relic(0)
	assert_true(rbuy1)
	assert_false(rbuy2, "Segunda compra da mesma relíquia é rejeitada")

# ==============================================================================
# GRUPO D: Exaustão de Pools e Resiliência
# ==============================================================================

func test_reward_modal_when_all_elite_relics_already_owned() -> void:
	# Arrange: Adicionar todas as relíquias de elite ao estado
	for r in RewardModal.ELITE_RELICS:
		_state.add_relic(r)

	var modal: RewardModal = autofree(RewardModal.new())
	var elite_node: RunNode = RunNode.new(5, 1, 3, 1, RunNode.NodeType.ELITE)

	# Act
	modal.setup(_state, elite_node, _rng)
	modal._ready()

	# Assert
	assert_eq(modal.offered_relic_id, "", "Pool de relíquias esgotado resulta em string vazia sem crash")
	assert_false(modal.lbl_relic_info.visible, "Label de relíquia fica oculta")

	# Finalizar modal não deve quebrar
	var completed: bool = modal.skip_card()
	assert_true(completed, "Conclusão de modal com pool vazio de relíquia conclui normalmente")

func test_reward_modal_forced_duplicate_relic_awards_compensatory_gold() -> void:
	# Arrange: Forçar via options uma relíquia que o jogador já possui
	_state.add_relic("reliquia_martelo_runico")
	var initial_gold: int = _state.gold

	var modal: RewardModal = autofree(RewardModal.new())
	var boss_node: RunNode = RunNode.new(11, 1, 5, 1, RunNode.NodeType.BOSS)

	# Act: Forçar "reliquia_martelo_runico"
	modal.setup(_state, boss_node, _rng, {"gold": 50, "relic_id": "reliquia_martelo_runico"})
	modal._ready()
	modal.skip_card()

	# Assert: Deve conceder 50 ouro do boss + 50 ouro de compensação pela duplicata = +100 ouro
	assert_eq(_state.gold, initial_gold + 50 + 50, "Relíquia duplicada deve compensar com +50 ouro")

func test_reward_modal_unknown_act_defaults_gracefully() -> void:
	# Arrange
	_state.act = 99 # Ato inexistente
	var modal: RewardModal = autofree(RewardModal.new())
	var node: RunNode = RunNode.new(1, 1, 0, 0, RunNode.NodeType.COMBAT)

	# Act
	modal.setup(_state, node, _rng)

	# Assert
	assert_eq(modal.card_options.size(), 3, "Ato anômalo deve cair no fallback e ofertar 3 cartas")
	for c in modal.card_options:
		assert_false(c.id.is_empty(), "Cartas do fallback possuem IDs válidos")

func test_forge_all_relics_already_owned_generates_empty_relic_inventory_safely() -> void:
	# Arrange: Adicionar todas as 10 relíquias canônicas ao estado
	for rid in ForgeScreen.CANONICAL_RELICS.keys():
		_state.add_relic(rid)

	var forge: ForgeScreen = autofree(ForgeScreen.new())

	# Act
	forge.setup(_state, _manager, _rng)
	forge._ready()
	forge.refresh_ui()

	# Assert
	assert_eq(forge.relic_inventory.size(), 0, "Inventário de relíquias vazio quando todas já são possuídas")
	assert_false(forge.buy_relic(0), "Tentativa de compra de relíquia em estoque vazio retorna falso sem crash")

func test_forge_out_of_bounds_slot_indices_safe() -> void:
	# Arrange
	var forge: ForgeScreen = autofree(ForgeScreen.new())
	forge.setup(_state, _manager, _rng)

	# Act & Assert
	assert_false(forge.buy_card(-1), "Slot negativo de carta retorna falso")
	assert_false(forge.buy_card(99), "Slot excessivo de carta retorna falso")
	assert_false(forge.buy_relic(-1), "Slot negativo de relíquia retorna falso")
	assert_false(forge.buy_relic(99), "Slot excessivo de relíquia retorna falso")

# ==============================================================================
# GRUPO E: Null Safety e Invariantes Multivisitas
# ==============================================================================

func test_reward_modal_null_dependencies_safe() -> void:
	# Arrange
	var modal: RewardModal = autofree(RewardModal.new())

	# Act: Setup com tudo nulo
	modal.setup(null, null, null)
	modal._ready()
	modal.refresh_display()

	# Assert
	assert_eq(modal.card_options.size(), 3, "3 cartas geradas mesmo sem estado")
	assert_false(modal.select_card(""), "Selecionar vazio falha com segurança")
	var success: bool = modal.select_card(modal.card_options[0].id)
	assert_true(success, "Selecionar carta válida sem estado conclui sem disparar null pointer")

func test_forge_screen_null_dependencies_safe() -> void:
	# Arrange
	var forge: ForgeScreen = autofree(ForgeScreen.new())

	# Act: Setup com tudo nulo
	forge.setup(null, null, null)
	forge._ready()
	forge.refresh_ui()

	# Assert
	assert_false(forge.buy_card(0), "Comprar carta sem estado retorna falso com segurança")
	assert_false(forge.buy_relic(0), "Comprar relíquia sem estado retorna falso com segurança")
	var pcheck: Dictionary = forge.can_purge_card()
	assert_false(pcheck["can"], "Expurgar sem estado retorna falso")
	assert_false(forge.purge_card("movimento"), "purge_card sem estado retorna falso")
	forge.close_forge()
	assert_true(true, "close_forge sem estado conclui sem null pointer")

func test_deck_minimum_holds_across_multiple_forge_visits() -> void:
	# Arrange: Deck inicial com 7 cartas
	_state.deck = ["c1", "c2", "c3", "c4", "c5", "c6", "c7"]
	_state.gold = 500

	# Visita 1 na Forja
	var forge1: ForgeScreen = autofree(ForgeScreen.new())
	forge1.setup(_state, _manager, _rng)
	assert_eq(forge1.get_current_purge_cost(), 50, "Custo inicial de expurgo deve ser 50g")
	assert_true(forge1.purge_card("c7"), "Expurgo 1 bem-sucedido")
	assert_eq(_state.deck.size(), 6)
	forge1.close_forge()

	# Visita 2 na Forja (novo nó)
	var forge2: ForgeScreen = autofree(ForgeScreen.new())
	forge2.setup(_state, _manager, _rng)
	assert_eq(forge2.get_current_purge_cost(), 75, "Custo escalonado para 75g na 2ª visita")
	assert_true(forge2.purge_card("c6"), "Expurgo 2 bem-sucedido")
	assert_eq(_state.deck.size(), 5, "Deck reduzido a exatamente 5 cartas")
	forge2.close_forge()

	# Visita 3 na Forja (novo nó)
	var forge3: ForgeScreen = autofree(ForgeScreen.new())
	forge3.setup(_state, _manager, _rng)
	assert_eq(forge3.get_current_purge_cost(), 100, "Custo escalonado para 100g na 3ª visita")
	var check3: Dictionary = forge3.can_purge_card()
	assert_false(check3["can"], "Expurgo 3 estritamente bloqueado (deck em 5)")
	assert_false(forge3.purge_card("c5"), "Tentativa de expurgo rejeitada")
	assert_eq(_state.deck.size(), 5, "Invariante de 5 cartas inviolável através de múltiplas forjas")


# res://test/unit/test_reward_modal.gd
extends GutTest

## Suíte de Testes Unitários para o Modal de Recompensas Pós-Combate (M3).
## Segue o padrão estrito Arrange-Act-Assert (AAA), segurança headless (zero crash),
## determinismo por injeção de RNG e prevenção contra vazamento de memória.

var _state: RunState
var _generator: RunMapGenerator
var _rng: RandomNumberGenerator

func before_each() -> void:
	_generator = RunMapGenerator.new(6, 3, 2)
	_rng = RandomNumberGenerator.new()
	_rng.seed = 1234
	_state = RunState.new(_generator, _rng)
	_state.start_run({"aquele": 30, "stark": 34, "elden": 26}, ["marcha", "trabalho"], 1234)

func after_each() -> void:
	RunSession.clear()
	_state = null
	_generator = null
	_rng = null

# ── 1. Inicialização Headless & Segurança ─────────────────────────────────────

func test_reward_modal_bare_node_headless_safety() -> void:
	# Arrange
	var modal: RewardModal = autofree(RewardModal.new())

	# Act
	modal._ready()
	modal.refresh_display()

	# Assert
	assert_not_null(modal, "Instanciação bare-node deve inicializar sem falhar")
	assert_not_null(modal.modal_panel, "Painel central criado programaticamente")
	assert_not_null(modal.btn_skip, "Botão de skip criado programaticamente")

# ── 2. Recompensas por Tipo de Nó ───────────────────────────────────────────

func test_setup_combat_node_generates_3_cards_and_standard_gold() -> void:
	# Arrange
	var modal: RewardModal = autofree(RewardModal.new())
	var combat_node: RunNode = RunNode.new(1, 1, 0, 0, RunNode.NodeType.COMBAT)

	# Act
	modal.setup(_state, combat_node, _rng)
	modal._ready()

	# Assert
	assert_eq(modal.offered_gold, 15, "Combate normal concede 15 de ouro")
	assert_eq(modal.offered_relic_id, "", "Combate normal não concede relíquia garantida")
	assert_eq(modal.card_options.size(), 3, "Exatamente 3 cartas devem ser ofertadas")
	for c in modal.card_options:
		assert_false(c.id.is_empty(), "Cada carta deve possuir ID válido")

func test_setup_elite_node_awards_relic_and_extra_gold() -> void:
	# Arrange
	var modal: RewardModal = autofree(RewardModal.new())
	var elite_node: RunNode = RunNode.new(5, 1, 3, 1, RunNode.NodeType.ELITE)

	# Act
	modal.setup(_state, elite_node, _rng)
	modal._ready()

	# Assert
	assert_eq(modal.offered_gold, 30, "Elite concede 30 de ouro")
	assert_false(modal.offered_relic_id.is_empty(), "Elite concede relíquia garantida")
	assert_true(RewardModal.ELITE_RELICS.has(modal.offered_relic_id), "Relíquia pertence ao pool de elite")
	assert_eq(modal.card_options.size(), 3, "Elite também oferta 3 cartas")

func test_setup_boss_node_awards_boss_relic_and_high_gold() -> void:
	# Arrange
	var modal: RewardModal = autofree(RewardModal.new())
	var boss_node: RunNode = RunNode.new(11, 1, 5, 1, RunNode.NodeType.BOSS)

	# Act
	modal.setup(_state, boss_node, _rng)
	modal._ready()

	# Assert
	assert_eq(modal.offered_gold, 50, "Chefe de Ato concede 50 de ouro")
	assert_false(modal.offered_relic_id.is_empty(), "Chefe concede relíquia de boss")
	assert_true(RewardModal.BOSS_RELICS.has(modal.offered_relic_id), "Relíquia pertence ao pool de chefes")

# ── 3. Seleção de Carta & Opção de Skip ──────────────────────────────────────

func test_card_selection_adds_card_to_run_state_deck() -> void:
	# Arrange
	var modal: RewardModal = autofree(RewardModal.new())
	var combat_node: RunNode = RunNode.new(1, 1, 0, 0, RunNode.NodeType.COMBAT)
	modal.setup(_state, combat_node, _rng)
	modal._ready()

	var target_card: CardData = modal.card_options[0]
	var initial_deck_size: int = _state.deck.size()
	var signal_received: Array = []
	modal.card_selected.connect(func(cid): signal_received.append(cid))

	# Act
	var success: bool = modal.select_card(target_card.id)

	# Assert
	assert_true(success, "select_card deve retornar true")
	assert_eq(_state.deck.size(), initial_deck_size + 1, "Deck da expedição aumentou em 1")
	assert_true(_state.deck.has(target_card.id), "Carta selecionada agora está no deck")
	assert_eq(signal_received, [target_card.id], "Sinal card_selected emitido com o ID correto")

func test_skip_card_leaves_deck_unchanged_and_emits_card_skipped() -> void:
	# Arrange
	var modal: RewardModal = autofree(RewardModal.new())
	var combat_node: RunNode = RunNode.new(1, 1, 0, 0, RunNode.NodeType.COMBAT)
	modal.setup(_state, combat_node, _rng)
	modal._ready()

	var initial_deck_size: int = _state.deck.size()
	var skip_emitted: Array = []
	var completed_summary: Array = []
	modal.card_skipped.connect(func(): skip_emitted.append(true))
	modal.reward_completed.connect(func(s): completed_summary.append(s))

	# Act
	var success: bool = modal.skip_card()

	# Assert
	assert_true(success, "skip_card deve retornar true")
	assert_eq(_state.deck.size(), initial_deck_size, "Deck permanece com o mesmo tamanho (enxuto)")
	assert_false(skip_emitted.is_empty(), "Sinal card_skipped emitido")
	assert_false(completed_summary.is_empty(), "Resumo emitido")
	assert_true(completed_summary[0].get("skipped", false), "Resumo indica que a carta foi pulada")

# ── 4. Coleta de Ouro e Relíquias ───────────────────────────────────────────

func test_gold_is_credited_to_run_state_on_completion() -> void:
	# Arrange
	var modal: RewardModal = autofree(RewardModal.new())
	var combat_node: RunNode = RunNode.new(1, 1, 0, 0, RunNode.NodeType.COMBAT)
	var initial_gold: int = _state.gold
	modal.setup(_state, combat_node, _rng)
	modal._ready()

	# Act: Pular carta ainda coleta o ouro ganho
	modal.skip_card()

	# Assert
	assert_eq(_state.gold, initial_gold + 15, "Ouro do combate creditado no RunState")

func test_relic_is_credited_to_run_state_on_elite_completion() -> void:
	# Arrange
	var modal: RewardModal = autofree(RewardModal.new())
	var elite_node: RunNode = RunNode.new(5, 1, 3, 1, RunNode.NodeType.ELITE)
	modal.setup(_state, elite_node, _rng)
	modal._ready()
	var granted_relic: String = modal.offered_relic_id

	# Act
	modal.skip_card()

	# Assert
	assert_true(_state.has_relic(granted_relic), "Relíquia do Elite adicionada ao RunState.relics")

func test_duplicate_relic_avoidance() -> void:
	# Arrange: Conceder todas as relíquias de elite menos uma
	for r in RewardModal.ELITE_RELICS.slice(1):
		_state.add_relic(r)

	var expected_relic: String = RewardModal.ELITE_RELICS[0]
	var modal: RewardModal = autofree(RewardModal.new())
	var elite_node: RunNode = RunNode.new(5, 1, 3, 1, RunNode.NodeType.ELITE)

	# Act
	modal.setup(_state, elite_node, _rng)

	# Assert
	assert_eq(modal.offered_relic_id, expected_relic, "Deve sortear apenas a relíquia restante não possuída")

# ── 5. Robustez, Determinismo e Edge Cases ──────────────────────────────────

func test_double_claim_prevention() -> void:
	# Arrange
	var modal: RewardModal = autofree(RewardModal.new())
	var combat_node: RunNode = RunNode.new(1, 1, 0, 0, RunNode.NodeType.COMBAT)
	modal.setup(_state, combat_node, _rng)
	modal._ready()

	var card_a: String = modal.card_options[0].id
	var card_b: String = modal.card_options[1].id
	var initial_gold: int = _state.gold

	# Act: Primeiro resgate
	assert_true(modal.select_card(card_a))
	# Tentativas subsequentes devem ser rejeitadas
	assert_false(modal.select_card(card_b), "Segundo resgate de carta rejeitado")
	assert_false(modal.skip_card(), "Pular após resgate rejeitado")

	# Assert
	assert_eq(_state.gold, initial_gold + 15, "Ouro não foi duplicado")
	assert_true(_state.deck.has(card_a))
	assert_false(_state.deck.has(card_b))

func test_deterministic_card_drafting_with_seeded_rng() -> void:
	# Arrange
	var rng1: RandomNumberGenerator = RandomNumberGenerator.new()
	var rng2: RandomNumberGenerator = RandomNumberGenerator.new()
	rng1.seed = 98765
	rng2.seed = 98765

	var modal1: RewardModal = autofree(RewardModal.new())
	var modal2: RewardModal = autofree(RewardModal.new())
	var node_ref: RunNode = RunNode.new(1, 1, 0, 0, RunNode.NodeType.COMBAT)

	# Act
	modal1.setup(_state, node_ref, rng1)
	modal2.setup(_state, node_ref, rng2)

	# Assert
	assert_eq(modal1.card_options.size(), 3)
	assert_eq(modal2.card_options.size(), 3)
	for i in range(3):
		assert_eq(modal1.card_options[i].id, modal2.card_options[i].id, "Mesma seed produz exatamente o mesmo draft")

func test_act_filtering_offers_act_appropriate_cards() -> void:
	# Arrange
	var modal_a1: RewardModal = autofree(RewardModal.new())
	var modal_a2: RewardModal = autofree(RewardModal.new())
	var modal_a3: RewardModal = autofree(RewardModal.new())

	var node_a1: RunNode = RunNode.new(1, 1, 0, 0, RunNode.NodeType.COMBAT)
	var node_a2: RunNode = RunNode.new(2, 2, 0, 0, RunNode.NodeType.COMBAT)
	var node_a3: RunNode = RunNode.new(3, 3, 0, 0, RunNode.NodeType.COMBAT)

	_state.act = 1
	modal_a1.setup(_state, node_a1, _rng)

	_state.act = 2
	modal_a2.setup(_state, node_a2, _rng)

	_state.act = 3
	modal_a3.setup(_state, node_a3, _rng)

	# Act & Assert
	var a1_ids: Array = RewardModal.CARD_POOLS[1].map(func(c): return c["id"])
	var a2_ids: Array = RewardModal.CARD_POOLS[2].map(func(c): return c["id"])
	var a3_ids: Array = RewardModal.CARD_POOLS[3].map(func(c): return c["id"])

	for c in modal_a1.card_options:
		assert_true(a1_ids.has(c.id) or ["marcha", "trabalho", "escavacao"].has(c.id))

	for c in modal_a2.card_options:
		assert_true(a2_ids.has(c.id) or ["marcha", "trabalho", "escavacao"].has(c.id))

	for c in modal_a3.card_options:
		assert_true(a3_ids.has(c.id) or ["marcha", "trabalho", "escavacao"].has(c.id))

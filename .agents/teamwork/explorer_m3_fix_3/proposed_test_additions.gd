# Proposed Test Additions for Milestone M3 Remediation

# ── 1. Addition for godot_project/test/unit/test_forge_system.gd ──────────────
# Append to test_forge_system.gd:

func test_purge_cost_persists_across_separate_forge_instances() -> void:
	# Arrange: 10 cartas e ouro suficiente
	assert_eq(_state.card_purges_count, 0)
	assert_eq(_forge.get_current_purge_cost(), 50)
	
	# Act 1: 1º expurgo na 1ª instância da Forja
	var p1: bool = _forge.purge_card("movimento")
	assert_true(p1, "1º expurgo deve ser bem-sucedido")
	assert_eq(_state.card_purges_count, 1, "RunState.card_purges_count deve ser incrementado para 1")
	_forge.close_forge()
	
	# Act 2: Instanciar uma 2ª Forja vinculada ao mesmo RunState
	var forge2: ForgeScreen = autofree(ForgeScreen.new())
	forge2.setup(_state, null, _rng)
	
	# Assert 2: Custo deve iniciar em 75g (50 + 1 * 25)
	assert_eq(forge2.purges_performed, 1, "2ª forja deve sincronizar 1 expurgo realizado")
	assert_eq(forge2.get_current_purge_cost(), 75, "2ª forja deve cobrar 75g devido ao expurgo prévio")
	
	# Act 3: 2º expurgo na 2ª forja
	var p2: bool = forge2.purge_card("trabalho")
	assert_true(p2, "2º expurgo deve ser bem-sucedido")
	assert_eq(_state.card_purges_count, 2, "RunState.card_purges_count deve ser incrementado para 2")
	forge2.close_forge()
	
	# Act 4: Instanciar uma 3ª Forja
	var forge3: ForgeScreen = autofree(ForgeScreen.new())
	forge3.setup(_state, null, _rng)
	assert_eq(forge3.purges_performed, 2)
	assert_eq(forge3.get_current_purge_cost(), 100, "3ª forja deve cobrar 100g (50 + 2 * 25)")

func test_card_purges_count_persists_through_run_state_save_roundtrip() -> void:
	# Arrange
	_state.card_purges_count = 2
	
	# Act
	var dict: Dictionary = _state.to_dict()
	var restored: RunState = RunState.new()
	var ok: bool = restored.from_dict(dict)
	
	# Assert
	assert_true(ok, "Restauração de RunState com card_purges_count deve suceder")
	assert_eq(restored.card_purges_count, 2, "card_purges_count deve ser 2 após restauração")
	
	var forge_restored: ForgeScreen = autofree(ForgeScreen.new())
	forge_restored.setup(restored, null, _rng)
	assert_eq(forge_restored.get_current_purge_cost(), 100, "Forja restaurada deve iniciar com custo de 100g")


# ── 2. Addition for godot_project/test/unit/test_adversarial_m3.gd ───────────
# Update test_deck_minimum_holds_across_multiple_forge_visits() around line 493:

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


# ── 3. Addition for godot_project/test/unit/test_run_map_and_state.gd ─────────
# In test_run_state_serialization_roundtrip() around line 345:
# Add:
# 	_state.card_purges_count = 3
# And assert:
# 	assert_eq(restored.card_purges_count, 3, "card_purges_count deve ser deserializado")

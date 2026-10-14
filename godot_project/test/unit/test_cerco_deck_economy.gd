# res://test/unit/test_cerco_deck_economy.gd
extends GutTest

## Comprehensive GUT Unit Test Suite for Milestone 4:
## Deckbuilder, Economia de Oficinas & Sincronia Co-op
##
## Tests CardData resource, WorkshopEconomy, CercoDeck, and CercoSyncRound.
## Adheres strictly to the Arrange-Act-Assert (AAA) pattern and zero ObjectDB leaks.

var _economy: WorkshopEconomy
var _deck: CercoDeck
var _board: FortressBoard
var _judge: CercoCombatJudge
var _sync_round: CercoSyncRound

func before_each() -> void:
	_economy = WorkshopEconomy.new()
	_deck = CercoDeck.new()
	_board = FortressBoard.new()
	_judge = CercoCombatJudge.new()
	_sync_round = CercoSyncRound.new()

func after_each() -> void:
	_deck.clear()
	_sync_round.clear_actions()
	_economy = null
	_deck = null
	_board = null
	_judge = null
	_sync_round = null

# ==============================================================================
# 1. CardData Unit Tests
# ==============================================================================

func test_card_data_default_properties() -> void:
	# Arrange & Act
	var card: CardData = CardData.new()

	# Assert
	assert_eq(card.id, "")
	assert_eq(card.card_name, "")
	assert_eq(card.card_type, CardData.TYPE_ACAO)
	assert_eq(card.badge, CardData.BADGE_MARCHA)
	assert_eq(card.cost_wood, 0)
	assert_eq(card.cost_leather, 0)
	assert_eq(card.cost_metal, 0)
	assert_eq(card.cost_crystal, 0)
	assert_eq(card.cost_ap, 0)
	assert_eq(card.effect_value, 0)

func test_card_data_custom_initialization_and_legacy_sync() -> void:
	# Arrange
	var card: CardData = CardData.new()

	# Act
	card.id = "upgrade_martelo"
	card.card_name = "Martelo Forjado"
	card.card_type = CardData.TYPE_UPGRADE
	card.badge = CardData.BADGE_TRABALHO
	card.cost_wood = 2
	card.cost_metal = 1
	card.cost_crystal = 1
	card.work = 5
	card.effect_value = 5

	# Assert
	assert_eq(card.id, "upgrade_martelo")
	assert_eq(card.card_name, "Martelo Forjado")
	assert_eq(card.name, "Martelo Forjado", "Legacy 'name' property is synced with card_name")
	assert_eq(card.cost_wood, 2)
	assert_eq(card.cost_metal, 1)
	assert_eq(card.cost_crystal, 1)
	assert_eq(card.trabalho, 5, "Legacy 'trabalho' property is synced with work")

func test_card_data_legacy_name_setter_syncs_card_name() -> void:
	# Arrange
	var card: CardData = CardData.new()

	# Act
	card.name = "Escavação Profunda"

	# Assert
	assert_eq(card.card_name, "Escavação Profunda")
	assert_eq(card.name, "Escavação Profunda")

func test_card_data_get_cost_dict() -> void:
	# Arrange
	var card: CardData = CardData.new()
	card.cost_wood = 3
	card.cost_metal = 2
	card.cost_crystal = 1

	# Act
	var costs: Dictionary = card.get_cost_dict()

	# Assert
	assert_eq(costs.size(), 3)
	assert_eq(costs.get("wood", 0), 3)
	assert_eq(costs.get("metal", 0), 2)
	assert_eq(costs.get("crystal", 0), 1)
	assert_eq(costs.get("leather", 0), 0)

func test_card_data_can_afford_validation() -> void:
	# Arrange
	var card: CardData = CardData.new()
	card.cost_wood = 2
	card.cost_metal = 1
	_economy.set_resources(2, 0, 1, 0, 0)

	# Act & Assert - Affordable
	assert_true(card.can_afford(_economy), "Economy with 2 wood and 1 metal can afford card")

	# Act & Assert - Unaffordable (spend 1 wood)
	_economy.spend_resource("wood", 1)
	assert_false(card.can_afford(_economy), "Economy with 1 wood cannot afford 2 wood cost")

	# Act & Assert - Null economy
	assert_false(card.can_afford(null), "Null economy returns false safely")

func test_card_data_clone_is_independent_deep_copy() -> void:
	# Arrange
	var original: CardData = CardData.new()
	original.id = "corrida_1"
	original.card_name = "Corrida Livre"
	original.card_type = CardData.TYPE_UPGRADE
	original.badge = CardData.BADGE_MARCHA
	original.cost_leather = 2
	original.movement = 30
	original.effect_value = 30
	original.cost["extra_ap"] = 1

	# Act
	var copy: CardData = original.clone()
	copy.card_name = "Corrida Modificada"
	copy.cost_leather = 5
	copy.cost["extra_ap"] = 99

	# Assert
	assert_eq(original.card_name, "Corrida Livre", "Original card_name remains untouched")
	assert_eq(original.cost_leather, 2, "Original cost_leather remains untouched")
	assert_eq(original.cost["extra_ap"], 1, "Original cost dict remains untouched")
	assert_eq(copy.card_name, "Corrida Modificada")
	assert_eq(copy.cost_leather, 5)
	assert_eq(copy.cost["extra_ap"], 99)

# ==============================================================================
# 2. WorkshopEconomy Unit Tests
# ==============================================================================

func test_workshop_economy_initial_and_set_resources() -> void:
	# Arrange & Act
	_economy.set_resources(10, 5, 8, 3, 4)

	# Assert
	assert_eq(_economy.wood, 10)
	assert_eq(_economy.leather, 5)
	assert_eq(_economy.metal, 8)
	assert_eq(_economy.crystal, 3)
	assert_eq(_economy.ap, 4)
	assert_eq(_economy.madeira, 10, "Portuguese property 'madeira' maps to wood")
	assert_eq(_economy.couro, 5, "Portuguese property 'couro' maps to leather")
	assert_eq(_economy.ferro, 8, "Portuguese property 'ferro' maps to metal")
	assert_eq(_economy.cristais, 3, "Portuguese property 'cristais' maps to crystal")

func test_workshop_economy_add_and_spend_resources() -> void:
	# Arrange
	watch_signals(_economy)

	# Act 1: Add resources
	var new_wood: int = _economy.add_resource("wood", 15)
	var new_crystal: int = _economy.add_resource("cristais", 5)

	# Assert 1
	assert_eq(new_wood, 15)
	assert_eq(new_crystal, 5)
	assert_signal_emitted(_economy, "resource_added")
	assert_signal_emitted(_economy, "resources_updated")

	# Act 2: Spend valid amount
	var spent: bool = _economy.spend_resource("wood", 10)

	# Assert 2
	assert_true(spent)
	assert_eq(_economy.wood, 5)
	assert_signal_emitted(_economy, "resource_spent")

	# Act 3: Spend excessive amount (must fail without deducting)
	var overspent: bool = _economy.spend_resource("wood", 20)

	# Assert 3
	assert_false(overspent)
	assert_eq(_economy.wood, 5, "Wood balance unchanged after failed spend")

func test_workshop_economy_can_afford_and_spend_costs_atomic() -> void:
	# Arrange
	_economy.set_resources(5, 5, 2, 0, 2)
	var cost_success: Dictionary = {"madeira": 3, "metal": 2}
	var cost_failure: Dictionary = {"madeira": 3, "cristal": 1}

	# Act & Assert: Can afford check
	assert_true(_economy.can_afford(cost_success), "Has 5 wood and 2 metal, can afford 3 wood and 2 metal")
	assert_false(_economy.can_afford(cost_failure), "Lacks crystal, cannot afford")

	# Act & Assert: Failed atomic spend does not deduct anything
	var spend_failed: bool = _economy.spend_costs(cost_failure)
	assert_false(spend_failed)
	assert_eq(_economy.wood, 5, "Wood unchanged after failed atomic transaction")
	assert_eq(_economy.metal, 2, "Metal unchanged after failed atomic transaction")

	# Act & Assert: Successful atomic spend deducts correctly
	var spend_ok: bool = _economy.spend_costs(cost_success)
	assert_true(spend_ok)
	assert_eq(_economy.wood, 2)
	assert_eq(_economy.metal, 0)

func test_workshop_economy_production_per_workshop() -> void:
	# Arrange
	watch_signals(_economy)

	# Act 1: Carpintaria (2 wood per worker)
	var prod_carp: Dictionary = _economy.produce_at_workshop("CARPINTARIA", 3)

	# Assert 1
	assert_eq(prod_carp.get("wood", 0), 6)
	assert_eq(_economy.wood, 6)

	# Act 2: Curtume (2 leather per worker)
	var prod_curt: Dictionary = _economy.produce_at_workshop("curtume", 2)

	# Assert 2
	assert_eq(prod_curt.get("leather", 0), 4)
	assert_eq(_economy.leather, 4)

	# Act 3: Fundição (1 metal and 1 crystal per worker)
	var prod_fund: Dictionary = _economy.produce_at_workshop("FUNDICAO", 4)

	# Assert 3
	assert_eq(prod_fund.get("metal", 0), 4)
	assert_eq(prod_fund.get("crystal", 0), 4)
	assert_eq(_economy.metal, 4)
	assert_eq(_economy.crystal, 4)
	assert_signal_emitted(_economy, "production_completed")

func test_workshop_economy_production_zero_workers_or_invalid_zone() -> void:
	# Arrange & Act
	var res_zero: Dictionary = _economy.produce_at_workshop("CARPINTARIA", 0)
	var res_invalid: Dictionary = _economy.produce_at_workshop("INVALID_ZONE", 5)

	# Assert
	assert_true(res_zero.is_empty(), "Zero workers yield empty dictionary")
	assert_true(res_invalid.is_empty(), "Invalid zone yields empty dictionary")
	assert_eq(_economy.wood, 0)

func test_workshop_economy_repair_wall_with_resources() -> void:
	# Arrange
	_board.damage_wall(FortressBoard.ZONE_MURALHA_NORTE, 50)
	var hp_before: int = _board.get_wall_hp(FortressBoard.ZONE_MURALHA_NORTE)
	assert_eq(hp_before, 50)

	_economy.set_resources(3, 0, 1, 0, 0) # 3 wood, 1 metal
	watch_signals(_economy)

	# Act: Repair with 2 wood (2*10 = 20 HP) and 1 metal (1*15 = 15 HP) = 35 HP repair
	var new_hp: int = _economy.repair_wall_with_resources(
		FortressBoard.ZONE_MURALHA_NORTE, _board, 2, 1
	)

	# Assert
	assert_eq(new_hp, 85, "Wall repaired by 35 HP (50 + 35 = 85)")
	assert_eq(_board.get_wall_hp(FortressBoard.ZONE_MURALHA_NORTE), 85)
	assert_eq(_economy.wood, 1, "Remaining wood is 1 (3 - 2)")
	assert_eq(_economy.metal, 0, "Remaining metal is 0 (1 - 1)")
	assert_signal_emitted(_economy, "wall_repaired_with_resources")

func test_workshop_economy_repair_wall_insufficient_resources_fails() -> void:
	# Arrange
	_board.damage_wall(FortressBoard.ZONE_MURALHA_SUL, 40)
	_economy.set_resources(1, 0, 0, 0, 0) # 1 wood, 0 metal

	# Act: Attempt to spend 2 wood and 1 metal
	var res: int = _economy.repair_wall_with_resources(
		FortressBoard.ZONE_MURALHA_SUL, _board, 2, 1
	)

	# Assert
	assert_eq(res, 0, "Returns 0 on failure due to lack of resources")
	assert_eq(_board.get_wall_hp(FortressBoard.ZONE_MURALHA_SUL), 60, "Wall HP remains at 60")
	assert_eq(_economy.wood, 1, "Wood balance remains at 1")

# ==============================================================================
# 3. CercoDeck Unit Tests
# ==============================================================================

func test_cerco_deck_build_starter_deck() -> void:
	# Arrange & Act
	var starter: Array[CardData] = _deck.build_starter_deck()

	# Assert
	assert_eq(starter.size(), 10, "Starter deck has exactly 10 cards")
	assert_eq(_deck.get_draw_pile_size(), 10)
	assert_eq(_deck.get_hand_size(), 0)
	assert_eq(_deck.get_discard_pile_size(), 0)

	var march_count: int = 0
	var work_count: int = 0
	var exc_count: int = 0
	var combat_count: int = 0
	for c in starter:
		match c.badge:
			CardData.BADGE_MARCHA: march_count += 1
			CardData.BADGE_TRABALHO: work_count += 1
			CardData.BADGE_ESCAVACAO: exc_count += 1
			CardData.BADGE_COMBATE: combat_count += 1

	assert_eq(march_count, 4, "Starter has 4 Marcha cards")
	assert_eq(work_count, 3, "Starter has 3 Trabalho cards")
	assert_eq(exc_count, 2, "Starter has 2 Escavação cards")
	assert_eq(combat_count, 1, "Starter has 1 Combate card")

func test_cerco_deck_draw_and_play_card() -> void:
	# Arrange
	_deck.build_starter_deck()
	watch_signals(_deck)

	# Act 1: Draw 4 cards
	var drawn: Array[CardData] = _deck.draw_cards(4)

	# Assert 1
	assert_eq(drawn.size(), 4)
	assert_eq(_deck.get_hand_size(), 4)
	assert_eq(_deck.get_draw_pile_size(), 6)
	assert_signal_emitted(_deck, "card_drawn")

	# Act 2: Play the first card from hand
	var card_to_play: CardData = drawn[0]
	var played: CardData = _deck.play_card(card_to_play.id)

	# Assert 2
	assert_not_null(played)
	assert_eq(played.id, card_to_play.id)
	assert_eq(_deck.get_hand_size(), 3)
	assert_eq(_deck.get_discard_pile_size(), 1)
	assert_signal_emitted(_deck, "card_played")

func test_cerco_deck_discard_card() -> void:
	# Arrange
	_deck.build_starter_deck()
	var drawn: Array[CardData] = _deck.draw_cards(2)
	var card_to_discard: CardData = drawn[1]
	watch_signals(_deck)

	# Act
	var ok: bool = _deck.discard_card(card_to_discard.id)

	# Assert
	assert_true(ok)
	assert_eq(_deck.get_hand_size(), 1)
	assert_eq(_deck.get_discard_pile_size(), 1)
	assert_signal_emitted(_deck, "card_discarded")

func test_cerco_deck_automatic_reshuffle_when_draw_pile_empty() -> void:
	# Arrange
	_deck.build_starter_deck() # 10 cards in draw pile
	# Draw all 10 cards
	_deck.draw_cards(10)
	assert_eq(_deck.get_draw_pile_size(), 0)
	assert_eq(_deck.get_hand_size(), 10)

	# Play 5 cards to populate discard pile
	for i in range(5):
		var card: CardData = _deck.hand[0]
		_deck.play_card(card.id)

	assert_eq(_deck.get_hand_size(), 5)
	assert_eq(_deck.get_discard_pile_size(), 5)
	assert_eq(_deck.get_draw_pile_size(), 0)

	watch_signals(_deck)

	# Act: Draw 3 more cards while draw pile is empty
	var drawn_after: Array[CardData] = _deck.draw_cards(3)

	# Assert
	assert_eq(drawn_after.size(), 3)
	assert_eq(_deck.get_hand_size(), 8)
	assert_eq(_deck.get_draw_pile_size(), 2, "5 reshuffled - 3 drawn = 2 in draw pile")
	assert_eq(_deck.get_discard_pile_size(), 0, "Discard pile emptied on reshuffle")
	assert_signal_emitted(_deck, "deck_reshuffled")

func test_cerco_deck_upgrade_market_buying() -> void:
	# Arrange
	_deck.populate_default_market()
	assert_gt(_deck.get_market_size(), 0)
	var market_card: CardData = _deck.market_cards[0]
	var card_id: String = market_card.id

	# Give economy enough resources
	_economy.set_resources(10, 10, 10, 10, 10)
	watch_signals(_deck)

	# Act: Buy card
	var bought: CardData = _deck.buy_card_from_market(card_id, _economy)

	# Assert
	assert_not_null(bought)
	assert_eq(bought.id, card_id)
	assert_eq(_deck.get_discard_pile_size(), 1, "Bought cards enter discard pile")
	assert_signal_emitted(_deck, "card_bought")

func test_cerco_deck_upgrade_market_buying_unaffordable_fails() -> void:
	# Arrange
	_deck.populate_default_market()
	var market_card: CardData = _deck.market_cards[0]
	_economy.set_resources(0, 0, 0, 0, 0) # Broke economy

	# Act
	var bought: CardData = _deck.buy_card_from_market(market_card.id, _economy)

	# Assert
	assert_null(bought)
	assert_eq(_deck.get_discard_pile_size(), 0)

# ==============================================================================
# 4. CercoSyncRound & Synergy System Unit Tests
# ==============================================================================

func test_sync_round_register_actions() -> void:
	# Arrange
	var card: CardData = CardData.new()
	card.id = "marcha_1"
	card.badge = CardData.BADGE_MARCHA
	watch_signals(_sync_round)

	# Act
	var ok: bool = _sync_round.register_player_action("player_1", card, {"target_cell": Vector2i(5, 5)})

	# Assert
	assert_true(ok)
	assert_eq(_sync_round.get_action_count(), 1)
	assert_signal_emitted(_sync_round, "action_registered")

func test_sync_round_register_action_rejects_invalid() -> void:
	# Arrange & Act
	var ok1: bool = _sync_round.register_player_action("", CardData.new())
	var ok2: bool = _sync_round.register_player_action("p1", null)

	# Assert
	assert_false(ok1, "Empty player_id rejected")
	assert_false(ok2, "Null card rejected")
	assert_eq(_sync_round.get_action_count(), 0)

func test_sync_round_synergy_detection_team_synergy() -> void:
	# Arrange: 3 players (2 choose TRABALHO, 1 chooses MARCHA)
	var c_trab1: CardData = CardData.new()
	c_trab1.id = "t1"
	c_trab1.badge = CardData.BADGE_TRABALHO

	var c_trab2: CardData = CardData.new()
	c_trab2.id = "t2"
	c_trab2.badge = CardData.BADGE_TRABALHO

	var c_mar: CardData = CardData.new()
	c_mar.id = "m1"
	c_mar.badge = CardData.BADGE_MARCHA

	_sync_round.register_player_action("p1", c_trab1)
	_sync_round.register_player_action("p2", c_trab2)
	_sync_round.register_player_action("p3", c_mar)

	# Act
	var syn: Dictionary = _sync_round.calculate_synergies()

	# Assert
	assert_eq(syn["total_players"], 3)
	assert_false(syn["supreme_synchrony"], "Not all players chose the same badge")
	assert_eq(syn["crystal_bonus"], 0)
	assert_true(syn["team_synergies"].has(CardData.BADGE_TRABALHO), "Team synergy detected for TRABALHO")
	assert_false(syn["team_synergies"].has(CardData.BADGE_MARCHA), "Only 1 player chose MARCHA -> no synergy")

func test_sync_round_supreme_synchrony_awards_two_crystals() -> void:
	# Arrange: 4 players, ALL choose MARCHA (Sincronia Suprema)
	for i in range(1, 5):
		var c: CardData = CardData.new()
		c.id = "mar_%d" % i
		c.badge = CardData.BADGE_MARCHA
		_sync_round.register_player_action("player_%d" % i, c)

	_economy.set_resources(0, 0, 0, 0, 0)
	watch_signals(_sync_round)

	# Act
	var syn: Dictionary = _sync_round.calculate_synergies()
	var round_summary: Dictionary = _sync_round.resolve_synchrony_round(1, _board, _judge, _economy)

	# Assert
	assert_true(syn["supreme_synchrony"], "Supreme synchrony triggered when all players match")
	assert_eq(syn["supreme_badge"], CardData.BADGE_MARCHA)
	assert_eq(syn["crystal_bonus"], 2, "Supreme synchrony awards +2 crystals")
	assert_eq(_economy.crystal, 2, "Fortress economy received exactly +2 crystals from Supreme Synchrony")
	assert_signal_emitted(_sync_round, "supreme_synchrony_triggered")
	assert_signal_emitted(_sync_round, "round_completed")

func test_sync_round_supreme_synchrony_with_escavacao_stacks_bonus() -> void:
	# Arrange: 4 players, ALL choose ESCAVACAO (Sincronia Suprema + Excavation layer)
	for i in range(1, 5):
		var c: CardData = CardData.new()
		c.id = "esc_%d" % i
		c.badge = CardData.BADGE_ESCAVACAO
		c.excavation = 3
		_sync_round.register_player_action("player_%d" % i, c)

	_economy.set_resources(0, 0, 0, 0, 0)

	# Act
	var round_summary: Dictionary = _sync_round.resolve_synchrony_round(1, _board, _judge, _economy)

	# Assert: 2 crystals from Supreme Synchrony + 4 players * (1 base + 1 synergy bonus) = 10 crystals
	assert_eq(_economy.crystal, 10, "2 crystals from Supreme Synchrony + 8 from 4x excavation with synergy")

func test_sync_round_4_layer_execution_order_and_details() -> void:
	# Arrange:
	# Player 1: MARCHA -> move unit on board
	# Player 2: TRABALHO -> workshop production
	# Player 3: ESCAVACAO -> resource extraction
	# Player 4: COMBATE -> melee attack
	_board.place_unit("hero_1", Vector2i(9, 9))

	var c_mar: CardData = CardData.new()
	c_mar.id = "c_mar"
	c_mar.badge = CardData.BADGE_MARCHA
	c_mar.movement = 15

	var c_tra: CardData = CardData.new()
	c_tra.id = "c_tra"
	c_tra.badge = CardData.BADGE_TRABALHO
	c_tra.work = 4

	var c_esc: CardData = CardData.new()
	c_esc.id = "c_esc"
	c_esc.badge = CardData.BADGE_ESCAVACAO
	c_esc.excavation = 6

	var c_com: CardData = CardData.new()
	c_com.id = "c_com"
	c_com.badge = CardData.BADGE_COMBATE

	_sync_round.register_player_action("p1", c_mar, {
		"unit_id": "hero_1",
		"to_pos": Vector2i(9, 10)
	})
	_sync_round.register_player_action("p2", c_tra, {
		"workshop_zone": "CARPINTARIA",
		"worker_count": 2
	})
	_sync_round.register_player_action("p3", c_esc, {
		"crystals": 2,
		"metal": 1
	})
	_sync_round.register_player_action("p4", c_com, {
		"attacker_id": "p4",
		"defender_id": "beetle_boss",
		"forced_rolls": [CercoCombatJudge.D6Face.IMPACTO, CercoCombatJudge.D6Face.IMPACTO]
	})

	_economy.set_resources(0, 0, 0, 0, 0)
	watch_signals(_sync_round)

	# Act
	var summary: Dictionary = _sync_round.resolve_synchrony_round(1, _board, _judge, _economy)

	# Assert
	assert_signal_emitted(_sync_round, "layer_started")
	assert_signal_emitted(_sync_round, "layer_resolved")
	assert_signal_emitted(_sync_round, "round_completed")

	# Check Layer 1 (Marcha)
	var l1: Dictionary = summary["layer_marcha"]
	assert_eq(l1["actions_executed"], 1)
	assert_eq(_board.get_unit_position("hero_1"), Vector2i(9, 10), "Unit moved on board in Layer 1")

	# Check Layer 2 (Trabalho)
	var l2: Dictionary = summary["layer_trabalho"]
	assert_eq(l2["actions_executed"], 1)
	assert_eq(_economy.wood, 4, "Carpintaria produced 4 wood (2*2) in Layer 2")

	# Check Layer 3 (Escavação)
	var l3: Dictionary = summary["layer_escavacao"]
	assert_eq(l3["actions_executed"], 1)
	assert_eq(_economy.crystal, 2, "Extracted 2 crystals in Layer 3")
	assert_eq(_economy.metal, 1, "Extracted 1 metal in Layer 3")

	# Check Layer 4 (Combat)
	var l4: Dictionary = summary["layer_combate"]
	assert_eq(l4["actions_executed"], 1)
	var combat_res: Dictionary = l4["details"][0]["result"]
	assert_eq(combat_res["final_damage"], 1, "Melee combat resolved via CercoCombatJudge in Layer 4 (2 impacts = 1 dmg)")

	# Check Actions reset
	assert_eq(_sync_round.get_action_count(), 0, "Registered actions cleared after round resolution")

# ==============================================================================
# 5. Edge Cases & Robustness Unit Tests
# ==============================================================================

func test_card_data_can_afford_individual_cost_shortages() -> void:
	# Arrange
	var c_leather: CardData = CardData.new()
	c_leather.cost_leather = 3
	var c_crystal: CardData = CardData.new()
	c_crystal.cost_crystal = 2
	var c_ap: CardData = CardData.new()
	c_ap.cost_ap = 4

	_economy.set_resources(10, 2, 10, 1, 3) # lacking 1 leather, 1 crystal, 1 ap

	# Act & Assert
	assert_false(c_leather.can_afford(_economy), "Cannot afford: 2 leather < 3 cost")
	assert_false(c_crystal.can_afford(_economy), "Cannot afford: 1 crystal < 2 cost")
	assert_false(c_ap.can_afford(_economy), "Cannot afford: 3 ap < 4 cost")

func test_workshop_economy_zero_and_negative_operations() -> void:
	# Arrange
	_economy.set_resources(5, 5, 5, 5, 5)

	# Act 1: Add non-positive amounts
	var res1: int = _economy.add_resource("wood", 0)
	var res2: int = _economy.add_resource("wood", -10)

	# Assert 1
	assert_eq(res1, 5)
	assert_eq(res2, 5)
	assert_eq(_economy.wood, 5)

	# Act 2: Spend non-positive amounts
	var ok1: bool = _economy.spend_resource("wood", 0)
	var ok2: bool = _economy.spend_resource("wood", -5)

	# Assert 2
	assert_true(ok1)
	assert_true(ok2)
	assert_eq(_economy.wood, 5)

func test_workshop_economy_patio_central_crystal_production() -> void:
	# Arrange & Act
	var prod: Dictionary = _economy.produce_at_workshop(FortressBoard.ZONE_PATIO_CENTRAL, 3)

	# Assert
	assert_eq(prod.get("crystal", 0), 3)
	assert_eq(_economy.crystal, 3)

func test_workshop_economy_repair_wall_zero_resources_returns_current_hp() -> void:
	# Arrange
	_board.damage_wall(FortressBoard.ZONE_MURALHA_OESTE, 30)
	var current_hp: int = _board.get_wall_hp(FortressBoard.ZONE_MURALHA_OESTE)

	# Act: 0 wood and 0 metal
	var res: int = _economy.repair_wall_with_resources(
		FortressBoard.ZONE_MURALHA_OESTE, _board, 0, 0
	)

	# Assert
	assert_eq(res, current_hp)
	assert_eq(_board.get_wall_hp(FortressBoard.ZONE_MURALHA_OESTE), current_hp)

func test_workshop_economy_repair_wall_null_board_or_negative_returns_zero() -> void:
	# Arrange & Act
	var res_null: int = _economy.repair_wall_with_resources("MURALHA_NORTE", null, 2, 2)
	var res_neg: int = _economy.repair_wall_with_resources("MURALHA_NORTE", _board, -1, 2)

	# Assert
	assert_eq(res_null, 0)
	assert_eq(res_neg, 0)

func test_workshop_economy_reset_clears_all_resources() -> void:
	# Arrange
	_economy.set_resources(10, 20, 30, 40, 50)
	watch_signals(_economy)

	# Act
	_economy.reset()

	# Assert
	assert_eq(_economy.wood, 0)
	assert_eq(_economy.leather, 0)
	assert_eq(_economy.metal, 0)
	assert_eq(_economy.crystal, 0)
	assert_eq(_economy.ap, 0)
	assert_signal_emitted(_economy, "resources_updated")

func test_cerco_deck_play_card_by_index_bounds() -> void:
	# Arrange
	_deck.build_starter_deck()
	_deck.draw_cards(3)

	# Act & Assert
	var invalid_neg: CardData = _deck.play_card_by_index(-1)
	var invalid_overflow: CardData = _deck.play_card_by_index(99)
	assert_null(invalid_neg)
	assert_null(invalid_overflow)
	assert_eq(_deck.get_hand_size(), 3)

	var valid: CardData = _deck.play_card_by_index(0)
	assert_not_null(valid)
	assert_eq(_deck.get_hand_size(), 2)
	assert_eq(_deck.get_discard_pile_size(), 1)

func test_cerco_deck_draw_when_empty_and_no_discard_is_safe() -> void:
	# Arrange
	# Empty deck and empty discard
	assert_eq(_deck.get_draw_pile_size(), 0)
	assert_eq(_deck.get_discard_pile_size(), 0)

	# Act
	var drawn: Array[CardData] = _deck.draw_cards(5)

	# Assert
	assert_true(drawn.is_empty())
	assert_eq(_deck.get_hand_size(), 0)

func test_cerco_deck_add_custom_card_to_market() -> void:
	# Arrange
	var custom_card: CardData = CardData.new()
	custom_card.id = "custom_relic"
	custom_card.card_name = "Relíquia Antiga"

	# Act
	_deck.add_card_to_market(custom_card)

	# Assert
	assert_eq(_deck.get_market_size(), 1)
	assert_eq(_deck.market_cards[0].id, "custom_relic")

func test_sync_round_empty_or_single_player_no_synergies() -> void:
	# Arrange 1: 0 players
	var syn_0: Dictionary = _sync_round.calculate_synergies()
	assert_eq(syn_0["total_players"], 0)
	assert_false(syn_0["supreme_synchrony"])
	assert_true(syn_0["team_synergies"].is_empty())

	# Arrange 2: 1 player
	var c: CardData = CardData.new()
	c.id = "solo_1"
	c.badge = CardData.BADGE_COMBATE
	_sync_round.register_player_action("p1", c)

	# Act 2
	var syn_1: Dictionary = _sync_round.calculate_synergies()

	# Assert 2
	assert_eq(syn_1["total_players"], 1)
	assert_false(syn_1["supreme_synchrony"])
	assert_true(syn_1["team_synergies"].is_empty())

func test_sync_round_player_re_registration_overwrites_action() -> void:
	# Arrange
	var c1: CardData = CardData.new()
	c1.id = "c1"
	c1.badge = CardData.BADGE_MARCHA

	var c2: CardData = CardData.new()
	c2.id = "c2"
	c2.badge = CardData.BADGE_TRABALHO

	# Act: Register p1 twice with different cards
	_sync_round.register_player_action("p1", c1)
	_sync_round.register_player_action("p1", c2)

	# Assert
	assert_eq(_sync_round.get_action_count(), 1, "Player registration is idempotent per player_id")
	var actions: Dictionary = _sync_round.get_registered_actions()
	assert_eq(actions["p1"]["badge"], CardData.BADGE_TRABALHO, "Latest registration overwrote previous")

func test_sync_round_team_synergy_trabalho_wall_repair_bonus() -> void:
	# Arrange: 2 players choose TRABALHO -> activates TRABALHO Team Synergy (+10 bonus repair)
	_board.damage_wall(FortressBoard.ZONE_MURALHA_NORTE, 50)
	var hp_before: int = _board.get_wall_hp(FortressBoard.ZONE_MURALHA_NORTE) # 50 HP

	var c1: CardData = CardData.new()
	c1.id = "t1"
	c1.badge = CardData.BADGE_TRABALHO

	var c2: CardData = CardData.new()
	c2.id = "t2"
	c2.badge = CardData.BADGE_TRABALHO

	_economy.set_resources(2, 0, 0, 0, 0) # 2 wood = 20 HP repair

	_sync_round.register_player_action("p1", c1, {
		"wall_id": FortressBoard.ZONE_MURALHA_NORTE,
		"wood_spent": 2,
		"metal_spent": 0
	})
	_sync_round.register_player_action("p2", c2) # generic work

	# Act
	var summary: Dictionary = _sync_round.resolve_synchrony_round(1, _board, _judge, _economy)

	# Assert: 50 base + 20 repair + 10 synergy bonus = 80 HP
	assert_eq(_board.get_wall_hp(FortressBoard.ZONE_MURALHA_NORTE), 80, "Wall received +10 bonus repair from Team Synergy")

func test_sync_round_team_synergy_combate_adds_bonus_die() -> void:
	# Arrange: 2 players choose COMBATE -> activates COMBATE Team Synergy (+1 combat die)
	var c1: CardData = CardData.new()
	c1.id = "cb1"
	c1.badge = CardData.BADGE_COMBATE

	var c2: CardData = CardData.new()
	c2.id = "cb2"
	c2.badge = CardData.BADGE_COMBATE

	# Normal 2 dice forced with 3 rolls (so 3rd die only consumed if synergy granted +1 die)
	_sync_round.register_player_action("p1", c1, {
		"attacker_id": "hero_guerreiro",
		"defender_id": "isectum_grunt",
		"num_dice": 2,
		"forced_rolls": [CercoCombatJudge.D6Face.IMPACTO, CercoCombatJudge.D6Face.IMPACTO, CercoCombatJudge.D6Face.IMPACTO]
	})
	_sync_round.register_player_action("p2", c2)

	# Act
	var summary: Dictionary = _sync_round.resolve_synchrony_round(1, _board, _judge, _economy)

	# Assert
	var l4: Dictionary = summary["layer_combate"]
	assert_true(l4["synergy_active"], "Combat team synergy was active")
	var res: Dictionary = l4["details"][0]["result"]
	assert_eq(res["rolls"].size(), 3, "Combat used 3 dice instead of 2 due to +1 combat die synergy bonus")

func test_sync_round_resolve_with_null_dependencies_safe() -> void:
	# Arrange
	var c: CardData = CardData.new()
	c.id = "c1"
	c.badge = CardData.BADGE_MARCHA
	_sync_round.register_player_action("p1", c)

	# Act: pass all nulls
	var summary: Dictionary = _sync_round.resolve_synchrony_round(1, null, null, null)

	# Assert
	assert_not_null(summary)
	assert_eq(summary["round_number"], 1)
	assert_eq(_sync_round.get_action_count(), 0)


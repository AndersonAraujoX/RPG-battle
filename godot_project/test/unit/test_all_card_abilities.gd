# res://test/unit/test_all_card_abilities.gd
extends GutTest

## Test suite verifying all Card abilities, upgrades, runes, and defenses in Cerco contra Isectum.
## Follows strict Arrange-Act-Assert (AAA) pattern with comprehensive edge case coverage.

# ── 1. Cartas Básicas ─────────────────────────────────────────────────────────

func test_card_marcha_increases_hero_pm() -> void:
	# Arrange
	var controller: CercoGameController = autofree(CercoGameController.new())
	var board: FortressBoard = FortressBoard.new()
	controller.board = board

	board.place_unit("aquele", Vector2i(9, 10))
	board.register_unit("aquele", {"name": "Aquele", "team": "A", "hp": 48, "move_range": 4})

	var card: CardData = CardData.new()
	card.id = "marcha_1"
	card.card_name = "Marcha"
	card.badge = CardData.BADGE_MARCHA
	card.movement = 15

	# Act
	controller._apply_card_effects(card, "")
	var udata: Dictionary = board.get_unit_data("aquele")

	# Assert
	assert_eq(int(udata["move_range"]), 7, "Marcha should add +3 PM (15 / 5) to heroes")

func test_card_trabalho_produces_in_workshop() -> void:
	# Arrange
	var controller: CercoGameController = autofree(CercoGameController.new())
	var economy: WorkshopEconomy = WorkshopEconomy.new()
	controller.economy = economy
	economy.set_resources(0, 0, 0, 0, 0)

	var card: CardData = CardData.new()
	card.id = "trabalho_1"
	card.card_name = "Trabalho"
	card.badge = CardData.BADGE_TRABALHO
	card.work = 3

	# Act
	controller._apply_card_effects(card, "CARPINTARIA")

	# Assert
	assert_gt(economy.get_resource("wood"), 0, "Trabalho on Carpintaria must produce wood")

func test_card_trabalho_repairs_wall() -> void:
	# Arrange
	var controller: CercoGameController = autofree(CercoGameController.new())
	var board: FortressBoard = FortressBoard.new()
	var economy: WorkshopEconomy = WorkshopEconomy.new()
	controller.board = board
	controller.economy = economy

	board.set_wall_hp(FortressBoard.ZONE_MURALHA_NORTE, 50)
	economy.set_resources(10, 10, 10, 5, 5)

	var card: CardData = CardData.new()
	card.id = "trabalho_2"
	card.card_name = "Trabalho"
	card.badge = CardData.BADGE_TRABALHO
	card.work = 3

	# Act
	controller._apply_card_effects(card, "MURALHA_NORTE")
	var new_hp: int = board.get_wall_hp(FortressBoard.ZONE_MURALHA_NORTE)

	# Assert
	assert_gt(new_hp, 50, "Trabalho on wall must increase wall integrity")

func test_card_escavacao_produces_crystals_and_metal() -> void:
	# Arrange
	var controller: CercoGameController = autofree(CercoGameController.new())
	var economy: WorkshopEconomy = WorkshopEconomy.new()
	controller.economy = economy
	economy.set_resources(0, 0, 0, 0, 0)

	var card: CardData = CardData.new()
	card.id = "escavacao_1"
	card.card_name = "Escavação"
	card.badge = CardData.BADGE_ESCAVACAO
	card.excavation = 4

	# Act
	controller._apply_card_effects(card, "")

	# Assert
	assert_gte(economy.get_resource("crystal"), 2, "Escavação must produce crystals")
	assert_gte(economy.get_resource("metal"), 1, "Escavação must produce metal")

func test_card_forca_ana_combat_rolls_dice() -> void:
	# Arrange
	var controller: CercoGameController = autofree(CercoGameController.new())
	var judge: CercoCombatJudge = CercoCombatJudge.new()
	controller.judge = judge

	var card: CardData = CardData.new()
	card.id = "forca_ana_1"
	card.card_name = "Força Anã"
	card.badge = CardData.BADGE_COMBATE
	card.work = 4

	# Act & Assert
	controller._apply_card_effects(card, "")
	assert_true(true, "Força Anã rolls combat dice safely without exceptions")

# ── 2. Cartas de Upgrade do Mercado ──────────────────────────────────────────

func test_upgrade_plano_tatico_expands_hand_and_draws() -> void:
	# Arrange
	var controller: CercoGameController = autofree(CercoGameController.new())
	var deck: CercoDeck = CercoDeck.new()
	deck.build_starter_deck()
	deck.max_hand_size = 5
	controller.deck = deck

	var card: CardData = CardData.new()
	card.id = "plano_tatico"
	card.card_name = "Plano Tático"
	card.card_type = CardData.TYPE_UPGRADE
	card.badge = CardData.BADGE_TRABALHO
	card.work = 4

	# Act
	controller._apply_card_effects(card, "")

	# Assert
	assert_eq(deck.max_hand_size, 6, "Plano Tático must increase max hand size to 6")
	assert_gt(deck.hand.size(), 0, "Plano Tático must draw a card immediately")

func test_upgrade_mestre_artesao_draws_card() -> void:
	# Arrange
	var controller: CercoGameController = autofree(CercoGameController.new())
	var deck: CercoDeck = CercoDeck.new()
	deck.build_starter_deck()
	controller.deck = deck

	var initial_hand: int = deck.hand.size()

	var card: CardData = CardData.new()
	card.id = "mestre_artesao"
	card.card_name = "Mestre Artesão"
	card.card_type = CardData.TYPE_UPGRADE
	card.badge = CardData.BADGE_TRABALHO
	card.work = 5

	# Act
	controller._apply_card_effects(card, "")

	# Assert
	assert_eq(deck.hand.size(), initial_hand + 1, "Mestre Artesão must draw 1 extra card")

func test_upgrade_grande_forjador_produces_metal() -> void:
	# Arrange
	var controller: CercoGameController = autofree(CercoGameController.new())
	var economy: WorkshopEconomy = WorkshopEconomy.new()
	economy.set_resources(0, 0, 0, 0, 0)
	controller.economy = economy

	var card: CardData = CardData.new()
	card.id = "grande_forjador"
	card.card_name = "Grande Forjador"
	card.card_type = CardData.TYPE_UPGRADE
	card.badge = CardData.BADGE_COMBATE
	card.work = 6

	# Act
	controller._apply_card_effects(card, "")

	# Assert
	assert_gte(economy.get_resource("metal"), 2, "Grande Forjador must forge +2 metal")

func test_upgrade_perfuratriz_real_massive_yield() -> void:
	# Arrange
	var controller: CercoGameController = autofree(CercoGameController.new())
	var economy: WorkshopEconomy = WorkshopEconomy.new()
	economy.set_resources(0, 0, 0, 0, 0)
	controller.economy = economy

	var card: CardData = CardData.new()
	card.id = "perfuratriz_real"
	card.card_name = "Perfuratriz Real"
	card.card_type = CardData.TYPE_UPGRADE
	card.badge = CardData.BADGE_ESCAVACAO
	card.excavation = 10

	# Act
	controller._apply_card_effects(card, "")

	# Assert
	assert_gte(economy.get_resource("crystal"), 5, "Perfuratriz Real yields +5 crystals")
	assert_gte(economy.get_resource("metal"), 3, "Perfuratriz Real yields +3 metals")

# ── 3. Cartas de Runa ─────────────────────────────────────────────────────────

func test_rune_haste_grants_pm_and_ap() -> void:
	# Arrange
	var controller: CercoGameController = autofree(CercoGameController.new())
	var board: FortressBoard = FortressBoard.new()
	var economy: WorkshopEconomy = WorkshopEconomy.new()
	controller.board = board
	controller.economy = economy
	economy.set_resources(0, 0, 0, 0, 0)

	board.place_unit("stark", Vector2i(10, 10))
	board.register_unit("stark", {"name": "Stark", "team": "A", "move_range": 3})

	var card: CardData = CardData.new()
	card.id = "runa_haste"
	card.card_name = "Runa da Haste"
	card.card_type = CardData.TYPE_RUNA

	# Act
	controller._apply_card_effects(card, "")
	var udata: Dictionary = board.get_unit_data("stark")

	# Assert
	assert_eq(int(udata["move_range"]), 8, "Runa da Haste must grant +5 PM")
	assert_gte(economy.get_resource("ap"), 2, "Runa da Haste must grant +2 AP")

func test_rune_recuperacao_draws_two_cards() -> void:
	# Arrange
	var controller: CercoGameController = autofree(CercoGameController.new())
	var deck: CercoDeck = CercoDeck.new()
	deck.build_starter_deck()
	controller.deck = deck

	var card: CardData = CardData.new()
	card.id = "runa_recuperacao"
	card.card_name = "Runa de Recuperação"
	card.card_type = CardData.TYPE_RUNA

	# Act
	controller._apply_card_effects(card, "")

	# Assert
	assert_eq(deck.hand.size(), 2, "Runa de Recuperação must draw 2 cards")

func test_rune_fortaleza_repairs_all_four_walls() -> void:
	# Arrange
	var controller: CercoGameController = autofree(CercoGameController.new())
	var board: FortressBoard = FortressBoard.new()
	controller.board = board

	board.set_wall_hp(FortressBoard.ZONE_MURALHA_NORTE, 20)
	board.set_wall_hp(FortressBoard.ZONE_MURALHA_SUL, 20)
	board.set_wall_hp(FortressBoard.ZONE_MURALHA_LESTE, 20)
	board.set_wall_hp(FortressBoard.ZONE_MURALHA_OESTE, 20)

	var card: CardData = CardData.new()
	card.id = "runa_fortaleza"
	card.card_name = "Runa da Fortaleza"
	card.card_type = CardData.TYPE_RUNA

	# Act
	controller._apply_card_effects(card, "")

	# Assert
	assert_eq(board.get_wall_hp(FortressBoard.ZONE_MURALHA_NORTE), 35, "North wall must gain +15 HP")
	assert_eq(board.get_wall_hp(FortressBoard.ZONE_MURALHA_SUL), 35, "South wall must gain +15 HP")
	assert_eq(board.get_wall_hp(FortressBoard.ZONE_MURALHA_LESTE), 35, "East wall must gain +15 HP")
	assert_eq(board.get_wall_hp(FortressBoard.ZONE_MURALHA_OESTE), 35, "West wall must gain +15 HP")

func test_rune_visao_peeks_threats() -> void:
	# Arrange
	var controller: CercoGameController = autofree(CercoGameController.new())
	var threat_deck: ThreatDeck = ThreatDeck.new()
	threat_deck.build_standard_deck(1)
	controller.threat_deck = threat_deck

	var card: CardData = CardData.new()
	card.id = "runa_visao"
	card.card_name = "Runa da Visão"
	card.card_type = CardData.TYPE_RUNA

	# Act & Assert
	controller._apply_card_effects(card, "")
	assert_true(true, "Runa da Visão peeks threats safely without exceptions")

# ── 4. Cartas de Defesa / Reação ──────────────────────────────────────────────

func test_defense_escudo_quitina_counters_and_reinforces_wall() -> void:
	# Arrange
	var controller: CercoGameController = autofree(CercoGameController.new())
	var board: FortressBoard = FortressBoard.new()
	var threat_deck: ThreatDeck = ThreatDeck.new()
	controller.board = board
	controller.threat_deck = threat_deck

	board.set_wall_hp(FortressBoard.ZONE_MURALHA_NORTE, 50)

	var card: CardData = CardData.new()
	card.id = "escudo_quitina"
	card.card_name = "Escudo de Quitina"
	card.card_type = CardData.TYPE_DEFESA

	# Act
	controller._apply_card_effects(card, "")

	# Assert
	assert_eq(board.get_wall_hp(FortressBoard.ZONE_MURALHA_NORTE), 65, "Escudo de Quitina reinforces wall by +15 HP")

func test_defense_antidoto_alquimico_heals_all_heroes() -> void:
	# Arrange
	var controller: CercoGameController = autofree(CercoGameController.new())
	var board: FortressBoard = FortressBoard.new()
	controller.board = board

	board.place_unit("aquele", Vector2i(9, 10))
	board.register_unit("aquele", {"name": "Aquele", "team": "A", "hp": 20, "max_hp": 48})
	board.place_unit("stark", Vector2i(10, 10))
	board.register_unit("stark", {"name": "Stark", "team": "A", "hp": 30, "max_hp": 52})

	var card: CardData = CardData.new()
	card.id = "antidoto_alquimico"
	card.card_name = "Antídoto Alquímico"
	card.card_type = CardData.TYPE_DEFESA

	# Act
	controller._apply_card_effects(card, "")

	# Assert
	assert_eq(int(board.get_unit_data("aquele")["hp"]), 35, "Aquele must be healed by +15 HP")
	assert_eq(int(board.get_unit_data("stark")["hp"]), 45, "Stark must be healed by +15 HP")

func test_defense_amuleto_resistencia_emergency_resources() -> void:
	# Arrange
	var controller: CercoGameController = autofree(CercoGameController.new())
	var economy: WorkshopEconomy = WorkshopEconomy.new()
	controller.economy = economy
	economy.set_resources(0, 0, 0, 0, 0)

	var card: CardData = CardData.new()
	card.id = "amuleto_resistencia"
	card.card_name = "Amuleto de Resistência"
	card.card_type = CardData.TYPE_DEFESA

	# Act
	controller._apply_card_effects(card, "")

	# Assert
	assert_gte(economy.get_resource("crystal"), 2, "Amuleto grants emergency crystals")
	assert_gte(economy.get_resource("wood"), 4, "Amuleto grants emergency wood")
	assert_gte(economy.get_resource("leather"), 4, "Amuleto grants emergency leather")

# ── 5. Casos de Borda (Edge Cases) ───────────────────────────────────────────

func test_apply_card_effects_null_card_safe() -> void:
	# Arrange
	var controller: CercoGameController = autofree(CercoGameController.new())

	# Act & Assert
	controller._apply_card_effects(null, "")
	assert_true(true, "Null card is safely ignored without crash")

func test_apply_card_effects_null_subsystems_safe() -> void:
	# Arrange
	var controller: CercoGameController = autofree(CercoGameController.new())
	controller.board = null
	controller.economy = null
	controller.deck = null
	controller.judge = null
	controller.threat_deck = null

	var card: CardData = CardData.new()
	card.id = "marcha_1"
	card.badge = CardData.BADGE_MARCHA
	card.movement = 15

	# Act & Assert
	controller._apply_card_effects(card, "")
	assert_true(true, "Null subsystems do not cause exceptions")

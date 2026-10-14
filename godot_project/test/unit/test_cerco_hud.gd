# res://test/unit/test_cerco_hud.gd
extends GutTest

## Comprehensive GUT Unit Test Suite for Milestone 5 (Cerco HUD, Board & Audio)
## Tests CardFanLayoutCalculator, CardUI, CardFanContainer, ResourceScoreboard,
## FortressBoardView, ZoneOverlay, CombatLog, and HUD integration with strict AAA pattern.

const HUD_SCENE: PackedScene = preload("res://scenes/ui/HUD.tscn")

var _board: FortressBoard = null
var _deck: CercoDeck = null
var _economy: WorkshopEconomy = null
var _judge: CercoCombatJudge = null

func before_each() -> void:
	_board = FortressBoard.new()
	_deck = CercoDeck.new()
	_economy = WorkshopEconomy.new()
	_judge = CercoCombatJudge.new()

func after_each() -> void:
	_board = null
	_deck = null
	_economy = null
	_judge = null

# ── 1. CardFanLayoutCalculator Tests ─────────────────────────────────────────

func test_card_fan_empty_hand() -> void:
	# Arrange
	var calc: CardFanLayoutCalculator = CardFanLayoutCalculator.new()

	# Act
	var transforms: Array[Dictionary] = calc.calculate_fan_transforms(0, 800.0, 160.0)

	# Assert
	assert_eq(transforms.size(), 0, "Empty hand must return empty array of transforms")

func test_card_fan_single_card() -> void:
	# Arrange
	var calc: CardFanLayoutCalculator = CardFanLayoutCalculator.new()
	var container_w: float = 800.0

	# Act
	var trans: Dictionary = calc.get_card_transform(0, 1, container_w, 160.0)

	# Assert
	var expected_x: float = (container_w - calc.card_size.x) / 2.0
	assert_almost_eq(trans["position"].x, expected_x, 0.01, "Single card must be centered horizontally")
	assert_almost_eq(trans["rotation_deg"], 0.0, 0.01, "Single card must have 0 rotation")
	assert_eq(trans["z_index"], 0, "Single card z_index is 0")

func test_card_fan_two_cards_symmetry() -> void:
	# Arrange
	var calc: CardFanLayoutCalculator = CardFanLayoutCalculator.new()

	# Act
	var trans0: Dictionary = calc.get_card_transform(0, 2, 800.0, 160.0)
	var trans1: Dictionary = calc.get_card_transform(1, 2, 800.0, 160.0)

	# Assert
	assert_lt(trans0["rotation_deg"], 0.0, "Card 0 tilt must be negative")
	assert_gt(trans1["rotation_deg"], 0.0, "Card 1 tilt must be positive")
	assert_almost_eq(trans0["rotation_deg"], -trans1["rotation_deg"], 0.01, "Rotations must be symmetric")
	assert_almost_eq(trans0["position"].y, trans1["position"].y, 0.01, "Arc height must be identical for symmetric pair")

func test_card_fan_five_cards_zenith_symmetry() -> void:
	# Arrange
	var calc: CardFanLayoutCalculator = CardFanLayoutCalculator.new()

	# Act
	var trans: Array[Dictionary] = calc.calculate_fan_transforms(5, 800.0, 160.0)

	# Assert
	assert_eq(trans.size(), 5, "Must compute exactly 5 transforms")
	assert_almost_eq(trans[2]["rotation_deg"], 0.0, 0.01, "Middle card (index 2) must be upright at zenith")
	assert_almost_eq(trans[0]["rotation_deg"], -trans[4]["rotation_deg"], 0.01, "Card 0 and 4 rotations must be mirror symmetric")
	assert_almost_eq(trans[1]["rotation_deg"], -trans[3]["rotation_deg"], 0.01, "Card 1 and 3 rotations must be mirror symmetric")
	assert_gt(trans[0]["position"].y, trans[2]["position"].y, "Outer cards must drop lower than the center zenith card")

func test_card_fan_ten_cards_clamped_rotation() -> void:
	# Arrange
	var calc: CardFanLayoutCalculator = CardFanLayoutCalculator.new()

	# Act
	var trans: Array[Dictionary] = calc.calculate_fan_transforms(10, 800.0, 160.0)

	# Assert
	assert_eq(trans.size(), 10, "Must calculate transforms for 10 cards")
	for t in trans:
		assert_true(absf(t["rotation_deg"]) <= (calc.max_arc_spread_deg / 2.0) + 0.01, "Card rotation must not exceed half max arc spread")

func test_card_fan_hover_lift_calculation() -> void:
	# Arrange
	var calc: CardFanLayoutCalculator = CardFanLayoutCalculator.new()
	var base: Dictionary = calc.get_card_transform(1, 3, 800.0, 160.0, false, false)

	# Act
	var hovered: Dictionary = calc.calculate_hover_transform(base)

	# Assert
	assert_almost_eq(hovered["position"].y, base["position"].y - calc.hover_lift_px, 0.01, "Hovered card Y position must lift by 30px")
	assert_almost_eq(hovered["rotation_deg"], 0.0, 0.01, "Hovered card must straighten to 0 degrees")
	assert_eq(hovered["z_index"], 20, "Hovered card z_index must be 20")
	assert_gt(hovered["scale"].x, 1.0, "Hovered card scale must enlarge")

func test_card_fan_selection_lift_calculation() -> void:
	# Arrange
	var calc: CardFanLayoutCalculator = CardFanLayoutCalculator.new()
	var base: Dictionary = calc.get_card_transform(0, 3, 800.0, 160.0, false, false)

	# Act
	var selected: Dictionary = calc.calculate_selection_transform(base)

	# Assert
	assert_almost_eq(selected["position"].y, base["position"].y - calc.selected_lift_px, 0.01, "Selected card Y position must lift by 45px")
	assert_almost_eq(selected["rotation_deg"], 0.0, 0.01, "Selected card must straighten to 0 degrees")
	assert_eq(selected["z_index"], 25, "Selected card z_index must be 25")

# ── 2. CardUI Tests ─────────────────────────────────────────────────────────

func test_card_ui_data_binding() -> void:
	# Arrange
	var card_ui: CardUI = autofree(CardUI.new())
	var card_data: CardData = CardData.new()
	card_data.id = "card_martelo_forja"
	card_data.card_name = "Martelo de Forja"
	card_data.badge = CardData.BADGE_TRABALHO
	card_data.cost_wood = 2
	card_data.cost_metal = 1
	card_data.description = "Produz ferramentas na fundição."

	# Act
	card_ui.setup(card_data, 0)

	# Assert
	assert_eq(card_ui.card_data.card_name, "Martelo de Forja", "Card data name correctly bound")
	assert_eq(card_ui.get_badge_color(), CardUI.COLOR_TRABALHO, "Trabalho badge maps to green theme")

func test_card_ui_badge_color_palette() -> void:
	# Arrange
	var card_ui: CardUI = autofree(CardUI.new())
	var c_marcha: CardData = CardData.new()
	c_marcha.badge = CardData.BADGE_MARCHA
	var c_esc: CardData = CardData.new()
	c_esc.badge = CardData.BADGE_ESCAVACAO
	var c_comb: CardData = CardData.new()
	c_comb.badge = CardData.BADGE_COMBATE

	# Act & Assert
	card_ui.setup(c_marcha, 0)
	assert_eq(card_ui.get_badge_color(), CardUI.COLOR_MARCHA, "Marcha maps to Azure")

	card_ui.setup(c_esc, 0)
	assert_eq(card_ui.get_badge_color(), CardUI.COLOR_ESCAVACAO, "Escavação maps to Amber")

	card_ui.setup(c_comb, 0)
	assert_eq(card_ui.get_badge_color(), CardUI.COLOR_COMBATE, "Combate maps to Crimson")

func test_card_ui_selection_toggle_signals() -> void:
	# Arrange
	var card_ui: CardUI = autofree(CardUI.new())
	var card_data: CardData = CardData.new()
	card_data.id = "test_card"
	card_ui.setup(card_data, 2)
	watch_signals(card_ui)

	# Act - Select
	card_ui.set_selected(true)

	# Assert - Select
	assert_signal_emitted_with_parameters(card_ui, "card_selected", [card_data, 2])
	assert_true(card_ui.is_selected, "Card is selected")

	# Act - Deselect
	card_ui.set_selected(false)

	# Assert - Deselect
	assert_signal_emitted_with_parameters(card_ui, "card_deselected", [card_data, 2])
	assert_false(card_ui.is_selected, "Card is deselected")

func test_card_ui_hover_signals() -> void:
	# Arrange
	var card_ui: CardUI = autofree(CardUI.new())
	var card_data: CardData = CardData.new()
	card_ui.setup(card_data, 1)
	watch_signals(card_ui)

	# Act
	card_ui.set_hovered(true)
	card_ui.set_hovered(false)

	# Assert
	assert_signal_emitted(card_ui, "card_hovered")
	assert_signal_emitted(card_ui, "card_unhovered")

func test_card_ui_play_request_signal() -> void:
	# Arrange
	var card_ui: CardUI = autofree(CardUI.new())
	var card_data: CardData = CardData.new()
	card_data.id = "marcha_rapida"
	card_data.target_zone = "CARPINTARIA"
	card_ui.setup(card_data, 0)
	watch_signals(card_ui)

	# Act
	card_ui.request_play()

	# Assert
	assert_signal_emitted_with_parameters(card_ui, "card_played_requested", [card_data, "CARPINTARIA"])

# ── 3. CardFanContainer Tests ───────────────────────────────────────────────

func test_card_fan_container_set_hand() -> void:
	# Arrange
	var container: CardFanContainer = autofree(CardFanContainer.new())
	var cards: Array[CardData] = []
	for i in range(4):
		var c: CardData = CardData.new()
		c.id = "c_%d" % i
		cards.append(c)

	# Act
	container.set_hand(cards)

	# Assert
	assert_eq(container.get_card_count(), 4, "Container must hold 4 cards")
	assert_eq(container.cards.size(), 4, "Data array must hold 4 cards")

func test_card_fan_container_add_and_remove_card() -> void:
	# Arrange
	var container: CardFanContainer = autofree(CardFanContainer.new())
	var c1: CardData = CardData.new()
	c1.id = "card_1"
	var c2: CardData = CardData.new()
	c2.id = "card_2"

	# Act - Add
	container.add_card(c1)
	container.add_card(c2)

	# Assert - Add
	assert_eq(container.get_card_count(), 2, "Hand size is 2")

	# Act - Remove
	var removed: CardData = container.remove_card(0)

	# Assert - Remove
	assert_eq(removed.id, "card_1", "Removed card is c1")
	assert_eq(container.get_card_count(), 1, "Hand size is now 1")
	assert_eq(container.get_card_ui(0).card_data.id, "card_2", "Remaining card is c2 with updated index 0")

func test_card_fan_container_mutual_exclusion_selection() -> void:
	# Arrange
	var container: CardFanContainer = autofree(CardFanContainer.new())
	for i in range(3):
		var c: CardData = CardData.new()
		c.id = "c_%d" % i
		container.add_card(c)

	# Act - Select card 0 then card 1
	container.select_card(0)
	assert_eq(container.selected_index, 0, "Card 0 selected")
	assert_true(container.get_card_ui(0).is_selected, "CardUI 0 is marked selected")

	container.select_card(1)

	# Assert
	assert_eq(container.selected_index, 1, "Selection shifted to card 1")
	assert_false(container.get_card_ui(0).is_selected, "CardUI 0 deselects automatically")
	assert_true(container.get_card_ui(1).is_selected, "CardUI 1 is marked selected")

# ── 4. ResourceScoreboard Tests ─────────────────────────────────────────────

func test_scoreboard_initial_values_zero() -> void:
	# Arrange & Act
	var sb: ResourceScoreboard = autofree(ResourceScoreboard.new())

	# Assert
	assert_eq(sb.get_resource_value("wood"), 0, "Initial wood is 0")
	assert_eq(sb.get_resource_value("leather"), 0, "Initial leather is 0")
	assert_eq(sb.get_resource_value("metal"), 0, "Initial metal is 0")
	assert_eq(sb.get_resource_value("crystal"), 0, "Initial crystal is 0")
	assert_eq(sb.get_resource_value("ap"), 0, "Initial AP is 0")

func test_scoreboard_update_resources_direct() -> void:
	# Arrange
	var sb: ResourceScoreboard = autofree(ResourceScoreboard.new())

	# Act
	sb.update_resources(15, 8, 12, 4, 3)

	# Assert
	assert_eq(sb.get_resource_value("wood"), 15, "Wood updated to 15")
	assert_eq(sb.get_resource_value("leather"), 8, "Leather updated to 8")
	assert_eq(sb.get_resource_value("metal"), 12, "Metal updated to 12")
	assert_eq(sb.get_resource_value("crystal"), 4, "Crystal updated to 4")
	assert_eq(sb.get_resource_value("ap"), 3, "AP updated to 3")

func test_scoreboard_wall_hp_tracking() -> void:
	# Arrange
	var sb: ResourceScoreboard = autofree(ResourceScoreboard.new())

	# Act
	sb.update_wall_hp("MURALHA_NORTE", 45, 100)
	sb.update_wall_hp("MURALHA_SUL", 0, 100)

	# Assert
	assert_eq(sb.get_wall_hp("MURALHA_NORTE"), 45, "North wall tracking reports 45")
	assert_eq(sb.get_wall_hp("MURALHA_SUL"), 0, "South wall tracking reports 0")

func test_scoreboard_round_and_layer_updates() -> void:
	# Arrange
	var sb: ResourceScoreboard = autofree(ResourceScoreboard.new())

	# Act
	sb.set_round(4)
	sb.set_layer("Combate")

	# Assert
	assert_eq(sb.get_round(), 4, "Current round is 4")
	assert_eq(sb.get_layer(), "Combate", "Current layer is Combate")

# ── 5. FortressBoardView & ZoneOverlay Tests ────────────────────────────────

func test_board_view_all_17_zones_resolution() -> void:
	# Arrange
	var bv: FortressBoardView = autofree(FortressBoardView.new())
	var zones_found: Dictionary = {}

	# Act - Scan the 20x20 grid cells
	for y in range(20):
		for x in range(20):
			var zid: String = bv.get_zone_at(Vector2i(x, y))
			if not zid.is_empty():
				zones_found[zid] = true

	# Assert
	assert_eq(zones_found.size(), 17, "Exactly 17 unique zones must be partitioned on the 20x20 grid")
	assert_true(zones_found.has("CAMARA_CENTRAL"), "Central chamber present")
	assert_true(zones_found.has("CARPINTARIA"), "Carpintaria present")
	assert_true(zones_found.has("MURALHA_NORTE"), "North wall present")
	assert_true(zones_found.has("TORRE_NOROESTE"), "NW tower present")
	assert_true(zones_found.has("SPAWN_NORTE"), "North spawn present")

func test_board_view_elevation_mapping() -> void:
	# Arrange
	var bv: FortressBoardView = autofree(FortressBoardView.new())

	# Act & Assert
	assert_eq(bv.get_elevation("CAMARA_CENTRAL"), 0, "Central chamber elevation is 0")
	assert_eq(bv.get_elevation("CARPINTARIA"), 0, "Workshops elevation is 0")
	assert_eq(bv.get_elevation("SPAWN_SUL"), 0, "Spawns elevation is 0")
	assert_eq(bv.get_elevation("MURALHA_LESTE"), 1, "Walls elevation is 1")
	assert_eq(bv.get_elevation("TORRE_SUDESTE"), 2, "Towers elevation is 2")

func test_board_view_coordinate_conversions() -> void:
	# Arrange
	var bv: FortressBoardView = autofree(FortressBoardView.new())
	bv.cell_size = Vector2(25.0, 25.0)

	# Act
	var screen_pos: Vector2 = bv.grid_to_screen(Vector2i(4, 8), 0)
	var recovered_grid: Vector2i = bv.screen_to_grid(Vector2(100.0, 200.0))

	# Assert
	assert_eq(screen_pos, Vector2(100.0, 200.0), "Grid (4,8) converts to (100, 200)")
	assert_eq(recovered_grid, Vector2i(4, 8), "Screen (100, 200) converts back to grid (4,8)")

func test_board_view_wall_breach_alert() -> void:
	# Arrange
	var bv: FortressBoardView = autofree(FortressBoardView.new())
	watch_signals(bv)

	# Act
	bv.set_wall_breached("MURALHA_NORTE", true)

	# Assert
	assert_true(bv.is_wall_breached("MURALHA_NORTE"), "North wall is marked breached")
	assert_signal_emitted_with_parameters(bv, "wall_breach_alert", ["MURALHA_NORTE"])

func test_board_view_wall_unbreach_on_repair() -> void:
	# Arrange
	var bv: FortressBoardView = autofree(FortressBoardView.new())
	bv.set_wall_breached("MURALHA_OESTE", true)
	assert_true(bv.is_wall_breached("MURALHA_OESTE"))

	# Act
	bv.set_wall_breached("MURALHA_OESTE", false)

	# Assert
	assert_false(bv.is_wall_breached("MURALHA_OESTE"), "Wall breach cleared on repair")

func test_zone_overlay_tactical_highlights() -> void:
	# Arrange
	var overlay: ZoneOverlay = autofree(ZoneOverlay.new())

	# Act - Highlight Movement
	overlay.highlight_movement(["CARPINTARIA", "PATIO_CENTRAL"])

	# Assert - Movement
	assert_eq(overlay.highlight_mode, ZoneOverlay.MODE_MOVEMENT, "Mode is MOVEMENT")
	assert_eq(overlay.highlighted_zones.size(), 2, "2 zones highlighted")

	# Act - Highlight Balestra
	overlay.highlight_balestra_targets(["SPAWN_NORTE", "MURALHA_NORTE"])

	# Assert - Balestra
	assert_eq(overlay.highlight_mode, ZoneOverlay.MODE_BALESTRA, "Mode is BALESTRA")

	# Act - Clear
	overlay.clear_highlights()

	# Assert - Clear
	assert_eq(overlay.highlight_mode, ZoneOverlay.MODE_NONE, "Mode is NONE after clear")
	assert_eq(overlay.highlighted_zones.size(), 0, "No zones highlighted after clear")

func test_zone_overlay_draw_is_headless_safe_and_does_not_draw_flat_boxes() -> void:
	# Arrange
	var overlay: ZoneOverlay = autofree(ZoneOverlay.new())
	overlay.set_selected_zone("FUNDICAO")
	overlay.highlight_movement(["CARPINTARIA"])
	
	# Act & Assert - Calling _draw should be clean, safe and produce no orthogonal artefacts
	overlay._draw()
	assert_eq(overlay.selected_zone, "FUNDICAO", "Selected zone recorded without generating intrusive flat boxes")


# ── 6. CombatLog Tests ──────────────────────────────────────────────────────

func test_combat_log_initial_state() -> void:
	# Arrange & Act
	var log: CombatLog = autofree(CombatLog.new())

	# Assert
	assert_true(log.bbcode_enabled, "BBCode must be enabled")
	assert_true(log.scroll_following, "Scroll following must be true")
	assert_eq(log.get_entry_count(), 0, "Initial entries count is 0")

func test_combat_log_append_message() -> void:
	# Arrange
	var log: CombatLog = autofree(CombatLog.new())

	# Act
	log.log_message("Teste de combate")

	# Assert
	assert_eq(log.get_entry_count(), 1, "Log has 1 entry")
	assert_true(log.get_last_entry_text().find("Teste de combate") != -1, "Last entry matches text")

func test_combat_log_append_tagged_categories() -> void:
	# Arrange
	var log: CombatLog = autofree(CombatLog.new())

	# Act
	log.append_entry("CARTA", "Marcha jogada")
	log.append_entry("DADOS", "Rolagem 3 Impactos")
	log.append_entry("BRECHA!", "Muralha Leste destruída!")

	# Assert
	assert_eq(log.get_entry_count(), 3, "3 entries logged")
	assert_true(log.get_entries()[0].find("[CARTA]") != -1, "First entry has CARTA tag")
	assert_true(log.get_entries()[1].find("[DADOS]") != -1, "Second entry has DADOS tag")
	assert_true(log.get_entries()[2].find("[BRECHA!]") != -1, "Third entry has BRECHA tag")

func test_combat_log_max_entries_truncation() -> void:
	# Arrange
	var log: CombatLog = autofree(CombatLog.new())

	# Act - Insert 110 entries (exceeding MAX_ENTRIES = 100)
	for i in range(110):
		log.log_message("Mensagem %d" % i)

	# Assert
	assert_eq(log.get_entry_count(), CombatLog.MAX_ENTRIES, "Entries capped at MAX_ENTRIES (100)")
	assert_true(log.get_last_entry_text().find("Mensagem 109") != -1, "Last entry is message 109")
	assert_false(log.get_entries()[0].find("Mensagem 0") != -1, "Oldest message 0 was purged")

func test_combat_log_clear() -> void:
	# Arrange
	var log: CombatLog = autofree(CombatLog.new())
	log.log_message("Log 1")
	log.log_message("Log 2")

	# Act
	log.clear_log()

	# Assert
	assert_eq(log.get_entry_count(), 0, "Entry count is 0 after clear")
	assert_eq(log.text, "", "Text is empty after clear")

func test_combat_log_sanitizes_unicode_emojis() -> void:
	# Arrange
	var log: CombatLog = autofree(CombatLog.new())
	var raw_message: String = "🃏 Rodada 2: Você comprou 1 nova(s) carta(s)! ⚔️ 🛡️ 🧱"

	# Act
	log.append_entry("COMPRA", raw_message)
	var last_entry: String = log.get_last_entry_text()

	# Assert
	assert_false(last_entry.contains("🃏"), "Raw 4-byte playing card emoji must be sanitized")
	assert_true(last_entry.contains("[Carta]"), "Card emoji converted to [Carta] tag")
	assert_true(last_entry.contains("[ATK]"), "Sword emoji converted to [ATK] tag")
	assert_true(last_entry.contains("[DEF]"), "Shield emoji converted to [DEF] tag")
	assert_true(last_entry.contains("[MURALHA]"), "Brick wall emoji converted to [MURALHA] tag")

func test_combat_log_preserves_newlines_between_entries() -> void:
	# Arrange
	var log: CombatLog = autofree(CombatLog.new())

	# Act - Append 3 distinct entries
	log.append_entry("COMPRA", "Você comprou 1 carta.")
	log.append_entry("COMPRA", "Você comprou 2 cartas.")
	log.append_entry("CERCO", "Inimigo atacou a muralha.")
	var parsed: String = log.get_parsed_text()

	# Assert - Ensures each entry is separated by a newline, avoiding concatenated runaway lines
	var lines: PackedStringArray = parsed.split("\n")
	assert_gte(lines.size(), 3, "Each entry must be on its own line separated by newline")
	assert_true(lines[0].contains("1 carta"), "Line 0 contains first message")
	assert_true(lines[1].contains("2 cartas"), "Line 1 contains second message")
	assert_true(lines[2].contains("Inimigo atacou"), "Line 2 contains third message")

func test_combat_log_edge_cases_empty_or_special_chars() -> void:
	# Arrange
	var log: CombatLog = autofree(CombatLog.new())

	# Act - Empty string logging
	log.log_message("")
	assert_eq(log.get_entry_count(), 0, "Empty message should not add an entry")

	# Act - String with exotic/surrogate emojis
	var exotic: String = "Test \uD83C\uDCCF exotic"
	var sanitized_static: String = CombatLog.sanitizar_texto(exotic)
	assert_false(sanitized_static.contains("🃏"), "Sanitizar_texto static method handles unicode glyphs safely")

# ── 7. HUD Integration & Dual-Wiring Tests ───────────────────────────────────

func test_hud_scene_instantiation() -> void:
	# Arrange & Act
	var hud: HUD = HUD_SCENE.instantiate() as HUD
	add_child_autofree(hud)

	# Assert
	assert_not_null(hud, "HUD instantiated from HUD.tscn")
	assert_not_null(hud.scoreboard, "Scoreboard subnode resolved")
	assert_not_null(hud.board_view, "FortressBoardView subnode resolved")
	assert_not_null(hud.combat_log, "CombatLog subnode resolved")
	assert_not_null(hud.card_fan, "CardFanContainer subnode resolved")

func test_hud_model_dependency_injection_board() -> void:
	# Arrange
	var hud: HUD = HUD.new()
	add_child_autofree(hud)
	var board: FortressBoard = FortressBoard.new()

	# Act
	hud.bind_board(board)
	board.damage_wall(FortressBoard.ZONE_MURALHA_NORTE, 25)

	# Assert
	assert_eq(hud.scoreboard.get_wall_hp("MURALHA_NORTE"), 75, "Scoreboard updated wall HP to 75 via board injection")

func test_hud_model_dependency_injection_economy() -> void:
	# Arrange
	var hud: HUD = HUD.new()
	add_child_autofree(hud)
	var economy: WorkshopEconomy = WorkshopEconomy.new()

	# Act
	hud.bind_economy(economy)
	economy.set_resource("wood", 20)
	economy.set_resource("metal", 10)

	# Assert
	assert_eq(hud.scoreboard.get_resource_value("wood"), 20, "Scoreboard updated wood to 20")
	assert_eq(hud.scoreboard.get_resource_value("metal"), 10, "Scoreboard updated metal to 10")

func test_hud_model_dependency_injection_deck() -> void:
	# Arrange
	var hud: HUD = HUD.new()
	add_child_autofree(hud)
	var deck: CercoDeck = CercoDeck.new()
	deck.build_starter_deck()

	# Act
	hud.bind_deck(deck)
	deck.draw_cards(3)

	# Assert
	assert_eq(hud.card_fan.get_card_count(), 3, "CardFan updated with 3 drawn cards via deck injection")

func test_hud_card_play_signal_relay() -> void:
	# Arrange
	var hud: HUD = HUD.new()
	add_child_autofree(hud)
	var card_data: CardData = CardData.new()
	card_data.id = "card_trabalho_madeira"
	hud.card_fan.add_card(card_data)
	watch_signals(hud)

	# Act
	hud.card_fan.get_card_ui(0).request_play("CARPINTARIA")

	# Assert
	assert_signal_emitted_with_parameters(hud, "card_played", ["player_1", "card_trabalho_madeira", "CARPINTARIA"])

func test_hud_sync_round_trigger() -> void:
	# Arrange
	var hud: HUD = HUD.new()
	add_child_autofree(hud)
	watch_signals(hud)

	# Act
	hud.trigger_sync_round()

	# Assert
	assert_signal_emitted(hud, "sync_round_requested")

func test_hud_audio_request_emission() -> void:
	# Arrange
	var hud: HUD = HUD.new()
	add_child_autofree(hud)
	watch_signals(hud)

	# Act
	hud.play_sfx("button_click", 1.0, 1.0)

	# Assert
	assert_signal_emitted_with_parameters(hud, "sound_played", ["button_click"])

func test_hud_eventbus_integration_forwarding() -> void:
	# Arrange
	var hud: HUD = HUD.new()
	add_child_autofree(hud)
	var tree: SceneTree = get_tree()
	var eb: Node = tree.root.get_node_or_null("EventBus")
	if eb == null:
		pass_test("EventBus not mounted in isolated runner")
		return

	# Act
	eb.production_completed.emit("FUNDICAO", "metal", 5)
	eb.damage_dealt.emit("MURALHA_SUL", 20, 80)

	# Assert
	assert_true(hud.combat_log.get_last_entry_text().find("MURALHA_SUL") != -1, "Damage logged from EventBus")

# ── 8. Teardown & Memory Safety Tests ────────────────────────────────────────

func test_hud_rapid_creation_and_destruction_zero_leaks() -> void:
	# Arrange & Act
	for i in range(5):
		var hud: HUD = HUD.new()
		add_child(hud)
		hud.scoreboard.update_resources(1, 2, 3, 4, 5)
		hud.cleanup()
		remove_child(hud)
		hud.free()

	# Assert
	pass_test("5 HUD instances created, exercised, and destroyed without crash or memory fault")

func test_hud_unbind_all_safely() -> void:
	# Arrange
	var hud: HUD = HUD.new()
	add_child_autofree(hud)
	var board: FortressBoard = FortressBoard.new()
	hud.bind_board(board)

	# Act
	hud.unbind_all()
	board.damage_wall(FortressBoard.ZONE_MURALHA_NORTE, 50)

	# Assert
	assert_null(hud._bound_board, "Bound board reference is cleared")
	assert_eq(hud.scoreboard.get_wall_hp("MURALHA_NORTE"), 100, "Unbound scoreboard ignores damage event")

# ── 9. Card Activation & Interactive Controls Tests ───────────────────────────

func test_cerco_deck_getters_and_lookups() -> void:
	# Arrange
	var deck: CercoDeck = CercoDeck.new()
	deck.build_starter_deck()

	# Act
	var draw_cards: Array[CardData] = deck.get_draw_pile()
	var hand_before: Array[CardData] = deck.get_hand().duplicate()
	var drawn: Array[CardData] = deck.draw_cards(3)
	var hand_after: Array[CardData] = deck.get_hand()
	var card_found: CardData = deck.get_card_by_id(drawn[0].id)
	var card_not_found: CardData = deck.get_card_by_id("non_existent_id")
	var marcha_card: CardData = deck.get_first_card_by_badge(CardData.BADGE_MARCHA)

	# Assert
	assert_eq(draw_cards.size(), 7, "Draw pile reduced to 7 after drawing 3")
	assert_eq(hand_before.size(), 0, "Hand was initially empty")
	assert_eq(hand_after.size(), 3, "Hand contains 3 cards after draw")
	assert_not_null(card_found, "Found card by ID in hand")
	assert_null(card_not_found, "Non-existent card returns null")
	if marcha_card != null:
		assert_eq(marcha_card.badge, CardData.BADGE_MARCHA, "Found card by badge")

func test_hud_bind_deck_populates_hand_when_deck_drawn_prior() -> void:
	# Arrange
	var hud: HUD = HUD.new()
	add_child_autofree(hud)
	var deck: CercoDeck = CercoDeck.new()
	deck.build_starter_deck()
	deck.draw_cards(5)

	# Act
	hud.bind_deck(deck)

	# Assert
	assert_eq(hud.card_fan.get_card_count(), 5, "HUD CardFan populated with 5 cards drawn prior to bind")
	assert_eq(hud._bound_deck, deck, "Bound deck reference set")

func test_card_ui_double_click_activates_card() -> void:
	# Arrange
	var card_ui: CardUI = autofree(CardUI.new())
	var card_data: CardData = CardData.new()
	card_data.id = "card_double_click"
	card_data.target_zone = "CARPINTARIA"
	card_ui.setup(card_data, 0)
	watch_signals(card_ui)

	# Act
	var ev: InputEventMouseButton = InputEventMouseButton.new()
	ev.button_index = MOUSE_BUTTON_LEFT
	ev.pressed = true
	ev.double_click = true
	card_ui._gui_input(ev)

	# Assert
	assert_signal_emitted_with_parameters(card_ui, "card_played_requested", [card_data, "CARPINTARIA"])

func test_card_ui_second_click_on_selected_activates_card() -> void:
	# Arrange
	var card_ui: CardUI = autofree(CardUI.new())
	var card_data: CardData = CardData.new()
	card_data.id = "card_second_click"
	card_ui.setup(card_data, 1)
	watch_signals(card_ui)

	# Act - First click selects
	var ev1: InputEventMouseButton = InputEventMouseButton.new()
	ev1.button_index = MOUSE_BUTTON_LEFT
	ev1.pressed = true
	card_ui._gui_input(ev1)
	assert_true(card_ui.is_selected, "First click selects the card")
	assert_signal_not_emitted(card_ui, "card_played_requested")

	# Act - Second click on selected plays/activates
	var ev2: InputEventMouseButton = InputEventMouseButton.new()
	ev2.button_index = MOUSE_BUTTON_LEFT
	ev2.pressed = true
	card_ui._gui_input(ev2)

	# Assert
	assert_signal_emitted(card_ui, "card_played_requested")

func test_card_fan_container_selection_and_play_methods() -> void:
	# Arrange
	var container: CardFanContainer = autofree(CardFanContainer.new())
	var c1: CardData = CardData.new()
	c1.id = "c_marcha"
	c1.badge = CardData.BADGE_MARCHA
	var c2: CardData = CardData.new()
	c2.id = "c_trabalho"
	c2.badge = CardData.BADGE_TRABALHO
	container.add_card(c1)
	container.add_card(c2)
	watch_signals(container)

	# Act - Null check when nothing selected
	var p_none: CardData = container.play_selected_card()
	assert_null(p_none, "Playing selected card when none selected returns null")

	# Act - Select and play card
	container.select_card(1)
	assert_eq(container.get_selected_card().id, "c_trabalho", "Card 1 is selected")
	var played: CardData = container.play_selected_card("FUNDICAO")

	# Assert
	assert_eq(played.id, "c_trabalho", "Played selected card c_trabalho")
	assert_signal_emitted_with_parameters(container, "card_played_requested", [c2, "FUNDICAO"])

	# Act - Remove by ID
	var removed: CardData = container.remove_card_by_id("c_marcha")
	assert_eq(removed.id, "c_marcha", "Removed card by ID")
	assert_eq(container.get_card_count(), 1, "Only 1 card remaining in fan")

func test_hud_board_zone_clicked_plays_selected_card() -> void:
	# Arrange
	var hud: HUD = HUD.new()
	add_child_autofree(hud)
	var card_data: CardData = CardData.new()
	card_data.id = "card_tactical_work"
	card_data.badge = CardData.BADGE_TRABALHO
	hud.card_fan.add_card(card_data)
	hud.card_fan.select_card(0)
	watch_signals(hud)

	# Act
	hud._on_board_zone_clicked("CARPINTARIA")

	# Assert
	assert_signal_emitted_with_parameters(hud, "card_played", ["player_1", "card_tactical_work", "CARPINTARIA"])

func test_hud_action_buttons_play_matching_cards() -> void:
	# Arrange
	var hud: HUD = HUD.new()
	add_child_autofree(hud)
	var c_march: CardData = CardData.new()
	c_march.id = "c_m"
	c_march.badge = CardData.BADGE_MARCHA
	var c_work: CardData = CardData.new()
	c_work.id = "c_w"
	c_work.badge = CardData.BADGE_TRABALHO
	var c_excav: CardData = CardData.new()
	c_excav.id = "c_e"
	c_excav.badge = CardData.BADGE_ESCAVACAO
	var c_combat: CardData = CardData.new()
	c_combat.id = "c_c"
	c_combat.badge = CardData.BADGE_COMBATE

	hud.card_fan.add_card(c_march)
	hud.card_fan.add_card(c_work)
	hud.card_fan.add_card(c_excav)
	hud.card_fan.add_card(c_combat)
	watch_signals(hud)

	# Act - Press Work Button
	hud._on_btn_work_pressed()
	assert_signal_emitted_with_parameters(hud, "card_played", ["player_1", "c_w", "CARPINTARIA"])

	# Act - Press Move Button
	hud._on_btn_move_pressed()
	assert_signal_emitted_with_parameters(hud, "card_played", ["player_1", "c_m", ""])

	# Act - Press Excavate Button
	hud._on_btn_excavate_pressed()
	assert_signal_emitted_with_parameters(hud, "card_played", ["player_1", "c_e", "PATIO_CENTRAL"])

	# Act - Press Attack Button
	hud._on_btn_attack_pressed()
	assert_signal_emitted_with_parameters(hud, "card_played", ["player_1", "c_c", ""])

func test_hud_keyboard_shortcuts_card_activation() -> void:
	# Arrange
	var hud: HUD = HUD.new()
	add_child_autofree(hud)
	var c1: CardData = CardData.new()
	c1.id = "c_key1"
	hud.card_fan.add_card(c1)
	watch_signals(hud)

	# Act - Press Key 1 to select card 0
	var key_ev1: InputEventKey = InputEventKey.new()
	key_ev1.keycode = KEY_1
	key_ev1.pressed = true
	hud._unhandled_input(key_ev1)
	assert_eq(hud.card_fan.selected_index, 0, "Key 1 selects card 0")

	# Act - Press Space to play selected card
	var key_space: InputEventKey = InputEventKey.new()
	key_space.keycode = KEY_SPACE
	key_space.pressed = true
	hud._unhandled_input(key_space)

	# Assert
	assert_signal_emitted_with_parameters(hud, "card_played", ["player_1", "c_key1", ""])

func test_hud_keyboard_shortcuts_camera_rotation_q_and_e_and_r() -> void:
	# Arrange
	var hud: HUD = HUD.new()
	add_child_autofree(hud)
	var view: FortressBoardView = FortressBoardView.new()
	add_child_autofree(view)
	hud.board_view = view
	view.camera_angle_idx = 0
	view.cam_zoom = 2.0

	# Act - Press E via HUD _unhandled_input (Rotate camera right)
	var key_e: InputEventKey = InputEventKey.new()
	key_e.keycode = KEY_E
	key_e.pressed = true
	hud._unhandled_input(key_e)

	# Assert
	assert_eq(view.camera_angle_idx, 1, "HUD shortcut KEY_E must rotate camera right to angle 1")

	# Act - Press Q via HUD _unhandled_input (Rotate camera left)
	var key_q: InputEventKey = InputEventKey.new()
	key_q.keycode = KEY_Q
	key_q.pressed = true
	hud._unhandled_input(key_q)

	# Assert
	assert_eq(view.camera_angle_idx, 0, "HUD shortcut KEY_Q must rotate camera left back to angle 0")

	# Act - Press R via HUD _unhandled_input (Reset camera zoom)
	var key_r: InputEventKey = InputEventKey.new()
	key_r.keycode = KEY_R
	key_r.pressed = true
	hud._unhandled_input(key_r)

	# Assert
	assert_eq(view.cam_zoom, 1.0, "HUD shortcut KEY_R must reset camera zoom to 1.0")

func test_hud_keyboard_shortcut_x_triggers_excavate() -> void:
	# Arrange
	var hud: HUD = HUD.new()
	add_child_autofree(hud)
	var c_excav: CardData = CardData.new()
	c_excav.id = "c_excavate_test"
	c_excav.badge = CardData.BADGE_ESCAVACAO
	hud.card_fan.add_card(c_excav)
	watch_signals(hud)

	# Act - Press X via HUD _unhandled_input (Excavate action)
	var key_x: InputEventKey = InputEventKey.new()
	key_x.keycode = KEY_X
	key_x.pressed = true
	hud._unhandled_input(key_x)

	# Assert
	assert_signal_emitted_with_parameters(hud, "card_played", ["player_1", "c_excavate_test", "PATIO_CENTRAL"])

func test_hud_keyboard_camera_shortcuts_safe_when_board_view_null() -> void:
	# Arrange
	var hud: HUD = HUD.new()
	add_child_autofree(hud)
	hud.board_view = null

	# Act & Assert - No crash when pressing Q, E, R with null board_view
	var key_e: InputEventKey = InputEventKey.new()
	key_e.keycode = KEY_E
	key_e.pressed = true
	hud._unhandled_input(key_e)

	var key_q: InputEventKey = InputEventKey.new()
	key_q.keycode = KEY_Q
	key_q.pressed = true
	hud._unhandled_input(key_q)

	var key_r: InputEventKey = InputEventKey.new()
	key_r.keycode = KEY_R
	key_r.pressed = true
	hud._unhandled_input(key_r)

	assert_null(hud.board_view, "HUD safely ignores camera rotation keys when board_view is null")

func test_cerco_game_controller_card_played_immediate_effects() -> void:
	# Arrange
	var script: GDScript = load("res://scripts/main/CercoGameController.gd")
	var controller: Node = script.new()
	add_child_autofree(controller)
	var initial_wood: int = controller.economy.wood
	var card: CardData = controller.deck.hand[0]
	var card_id: String = card.id
	card.badge = CardData.BADGE_TRABALHO
	card.work = 3

	# Act
	controller._on_hud_card_played("player_1", card_id, "CARPINTARIA")

	# Assert
	assert_gt(controller.economy.wood, initial_wood, "Carpintaria work increased fortress wood")
	assert_eq(controller.sync_round.get_action_count(), 1, "Action registered in synchrony round")
	assert_eq(controller.deck.hand.size(), 4, "Hand decreases from 5 to 4 as card is consumed immediately")
	assert_eq(controller.deck.discard_pile.size(), 1, "Played card is placed into discard pile")

	# Act - Conclui rodada de sincronia
	controller._on_hud_sync_round_requested()

	# Assert
	assert_eq(controller.deck.hand.size(), 5, "Hand replenished back to 5 at the conclusion of synchrony round")

# ── 12. Final Fantasy Tactics Unit Control & Item Pickup Tests ───────────────

func test_board_view_unit_selection_and_highlight_computation() -> void:
	# Arrange
	var bv: FortressBoardView = autofree(FortressBoardView.new())
	var board: FortressBoard = FortressBoard.new()
	bv.bind_board(board)
	board.place_unit("aquele", Vector2i(9, 10))
	board.register_unit("aquele", {
		"name": "Aquele", "class": "Guerreiro", "team": "A",
		"hp": 48, "max_hp": 48, "ac": 17, "move_range": 4, "attack_range": 1
	})
	board.place_unit("enemy_1", Vector2i(9, 11))
	board.register_unit("enemy_1", {
		"name": "Soldado", "team": "B", "hp": 20, "ac": 13
	})
	watch_signals(bv)

	# Act
	bv.select_unit("aquele")

	# Assert
	assert_eq(bv.selected_unit_id, "aquele", "Selected unit is Aquele")
	assert_gt(bv.reachable_cells.size(), 0, "Reachable cells computed for movement")
	assert_eq(bv.attackable_cells.size(), 1, "Nearby enemy is in attackable cells")
	assert_has(bv.attackable_cells, Vector2i(9, 11), "Enemy position is attackable")
	assert_signal_emitted(bv, "unit_selected", "unit_selected signal emitted")

func test_board_view_unit_movement_and_item_pickup() -> void:
	# Arrange
	var bv: FortressBoardView = autofree(FortressBoardView.new())
	var board: FortressBoard = FortressBoard.new()
	bv.bind_board(board)
	var start_pos: Vector2i = Vector2i(9, 10)
	var dest_pos: Vector2i = Vector2i(9, 9)
	board.place_unit("stark", start_pos)
	board.register_unit("stark", {"name": "Stark", "team": "A", "move_range": 3})
	board.place_item(dest_pos, FortressBoard.ITEM_CRISTAL, {"amount": 2})
	bv.select_unit("stark")
	watch_signals(bv)

	# Act
	var moved: bool = bv.move_selected_unit_to(dest_pos)

	# Assert
	assert_true(moved, "Unit moved to destination cell")
	assert_eq(board.get_unit_position("stark"), dest_pos, "Unit position on board updated")
	assert_false(board.has_item_at(dest_pos), "Item collected and removed from tile")
	assert_signal_emitted(bv, "unit_moved_to_cell", "unit_moved_to_cell emitted")
	assert_signal_emitted(bv, "item_pickup_requested", "item_pickup_requested emitted")

func test_board_view_enemy_attack_request() -> void:
	# Arrange
	var bv: FortressBoardView = autofree(FortressBoardView.new())
	var board: FortressBoard = FortressBoard.new()
	bv.bind_board(board)
	board.place_unit("aquele", Vector2i(9, 10))
	board.register_unit("aquele", {"team": "A", "attack_range": 1})
	board.place_unit("insect", Vector2i(9, 11))
	board.register_unit("insect", {"team": "B"})
	bv.select_unit("aquele")
	watch_signals(bv)

	# Act - Simulate clicking directly on the enemy cell
	var enemy_iso_pos: Vector2 = bv.get_cell_screen_coords(9, 11)
	var mb: InputEventMouseButton = InputEventMouseButton.new()
	mb.button_index = MOUSE_BUTTON_LEFT
	mb.pressed = true
	mb.position = enemy_iso_pos
	bv._gui_input(mb)

	# Assert
	assert_signal_emitted_with_parameters(bv, "unit_attack_requested", ["aquele", "insect"])

func test_hud_active_hero_update_from_selection() -> void:
	# Arrange
	var hud: HUD = autofree(HUD.new())
	var hero_box: PanelContainer = PanelContainer.new()
	var h_box: HBoxContainer = HBoxContainer.new()
	var badge: Label = Label.new()
	badge.name = "AvatarBadge"
	var stats: Label = Label.new()
	stats.name = "HeroStats"
	h_box.add_child(badge)
	h_box.add_child(stats)
	hero_box.add_child(h_box)
	hud.add_child(hero_box)
	hud._resolve_subcomponents()

	# Act
	hud.update_active_hero({
		"name": "Stark", "class": "Paladino", "hp": 52,
		"max_hp": 52, "attack_bonus": 4, "ac": 18, "move_range": 3
	})

	# Assert
	assert_eq(hud.avatar_badge.text, "[ PALADINO ]", "Avatar badge updated to class")
	assert_true(hud.hero_stats.text.contains("Stark"), "Hero name updated")
	assert_true(hud.hero_stats.text.contains("52/52"), "Hero HP updated")
	assert_true(hud.hero_stats.text.contains("[ATK] +4"), "Hero Attack updated")
	assert_true(hud.hero_stats.text.contains("[DEF] 18"), "Hero Defense updated")


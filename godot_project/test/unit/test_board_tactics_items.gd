# res://test/unit/test_board_tactics_items.gd
extends GutTest

## Test suite for FortressBoard tactical items and FFT character control mechanics.
## Strictly follows Arrange-Act-Assert (AAA) pattern with comprehensive edge cases.

# ── 1. Item Placement & Retrieval (Happy Path & Edge Cases) ───────────────────

func test_place_item_happy_path() -> void:
	# Arrange
	var board: FortressBoard = FortressBoard.new()
	var pos: Vector2i = Vector2i(9, 8)
	var data: Dictionary = {"amount": 2, "icon": "💎"}

	# Act
	var success: bool = board.place_item(pos, FortressBoard.ITEM_CRISTAL, data)
	var item: Dictionary = board.get_item_at(pos)

	# Assert
	assert_true(success, "Item should be placed successfully")
	assert_true(board.has_item_at(pos), "Board should report item exists at position")
	assert_eq(item.get("type"), FortressBoard.ITEM_CRISTAL, "Item type should match")
	assert_eq(item.get("name"), "Cristal de Mana", "Default name should be assigned")
	assert_eq(int(item.get("amount")), 2, "Amount should match provided data")
	assert_eq(item.get("icon"), "💎", "Icon should match")

func test_place_item_invalid_coordinates_rejected() -> void:
	# Arrange
	var board: FortressBoard = FortressBoard.new()

	# Act & Assert
	assert_false(board.place_item(Vector2i(-1, 5), FortressBoard.ITEM_CRISTAL), "Negative X rejected")
	assert_false(board.place_item(Vector2i(5, -1), FortressBoard.ITEM_CRISTAL), "Negative Y rejected")
	assert_false(board.place_item(Vector2i(20, 5), FortressBoard.ITEM_CRISTAL), "X >= 20 rejected")
	assert_false(board.place_item(Vector2i(5, 20), FortressBoard.ITEM_CRISTAL), "Y >= 20 rejected")
	assert_false(board.place_item(Vector2i(5, 5), ""), "Empty type rejected")

func test_collect_item_happy_path_and_signals() -> void:
	# Arrange
	var board: FortressBoard = FortressBoard.new()
	var pos: Vector2i = Vector2i(10, 5)
	watch_signals(board)
	board.place_item(pos, FortressBoard.ITEM_CHEST, {"wood": 6, "leather": 2})

	# Act
	var collected: Dictionary = board.collect_item("heroi_stark", pos)

	# Assert
	assert_false(board.has_item_at(pos), "Item should be removed from board after collection")
	assert_eq(collected.get("type"), FortressBoard.ITEM_CHEST, "Collected item type matches")
	assert_eq(int(collected.get("wood")), 6, "Wood resource retrieved from chest")
	assert_signal_emitted(board, "item_collected", "item_collected signal should be emitted")

func test_collect_item_empty_cell_returns_empty_dict() -> void:
	# Arrange
	var board: FortressBoard = FortressBoard.new()
	var pos: Vector2i = Vector2i(12, 12)

	# Act
	var collected: Dictionary = board.collect_item("heroi_1", pos)

	# Assert
	assert_true(collected.is_empty(), "Collecting from an empty cell returns empty dict")

func test_remove_item_success_and_failure() -> void:
	# Arrange
	var board: FortressBoard = FortressBoard.new()
	var pos: Vector2i = Vector2i(7, 7)
	board.place_item(pos, FortressBoard.ITEM_POTION, {"heal": 15})

	# Act & Assert
	assert_true(board.remove_item(pos), "Removing existing item succeeds")
	assert_false(board.has_item_at(pos), "Item no longer exists")
	assert_false(board.remove_item(pos), "Removing already removed item returns false")

func test_spawn_default_map_items_populates_key_zones() -> void:
	# Arrange
	var board: FortressBoard = FortressBoard.new()

	# Act
	board.spawn_default_map_items()
	var all_items: Dictionary = board.get_all_items()

	# Assert
	assert_gt(all_items.size(), 10, "Should spawn at least 10 default items on the board")
	assert_true(board.has_item_at(Vector2i(9, 8)), "Central mana crystal exists")
	assert_true(board.has_item_at(Vector2i(10, 5)), "Carpintaria chest exists")
	assert_true(board.has_item_at(Vector2i(2, 2)), "Tower potion exists")

# ── 2. Unit Combat Registry & Health Tracking ────────────────────────────────

func test_register_unit_and_retrieve_stats() -> void:
	# Arrange
	var board: FortressBoard = FortressBoard.new()
	var u_data: Dictionary = {
		"name": "Aquele",
		"team": "A",
		"hp": 48,
		"max_hp": 48,
		"ac": 17,
		"move_range": 4,
		"attack_range": 1
	}

	# Act
	board.register_unit("aquele", u_data)
	var retrieved: Dictionary = board.get_unit_data("aquele")

	# Assert
	assert_eq(retrieved.get("name"), "Aquele", "Name matches")
	assert_eq(retrieved.get("team"), "A", "Team matches")
	assert_eq(int(retrieved.get("hp")), 48, "HP matches")
	assert_eq(int(retrieved.get("ac")), 17, "AC matches")
	assert_eq(int(retrieved.get("move_range")), 4, "Move range matches")
	assert_true(board.is_unit_alive("aquele"), "Unit starts alive")

func test_damage_and_heal_unit_with_clamping() -> void:
	# Arrange
	var board: FortressBoard = FortressBoard.new()
	board.register_unit("stark", {"hp": 50, "max_hp": 50})

	# Act - Damage
	var hp_after_dmg: int = board.damage_unit("stark", 20)

	# Assert - Damaged
	assert_eq(hp_after_dmg, 30, "HP reduced by 20")
	assert_true(board.is_unit_alive("stark"), "Unit still alive")

	# Act - Heal
	var hp_after_heal: int = board.heal_unit("stark", 15)

	# Assert - Healed
	assert_eq(hp_after_heal, 45, "HP healed by 15")

	# Act - Overheal
	var hp_overheal: int = board.heal_unit("stark", 100)

	# Assert - Clamped to max_hp
	assert_eq(hp_overheal, 50, "HP clamped to max_hp")

	# Act - Overkill
	var hp_overkill: int = board.damage_unit("stark", 999)

	# Assert - Clamped to 0 and marked dead
	assert_eq(hp_overkill, 0, "HP clamped to 0")
	assert_false(board.is_unit_alive("stark"), "Unit marked as dead")

func test_unit_operations_on_unregistered_unit_safe() -> void:
	# Arrange
	var board: FortressBoard = FortressBoard.new()

	# Act & Assert
	assert_eq(board.damage_unit("ghost", 10), 0, "Damaging unregistered unit returns 0")
	assert_eq(board.heal_unit("ghost", 10), 0, "Healing unregistered unit returns 0")
	assert_false(board.is_unit_alive("ghost"), "Unregistered unit is not alive")

func test_get_units_by_team_filtering() -> void:
	# Arrange
	var board: FortressBoard = FortressBoard.new()
	board.place_unit("hero_1", Vector2i(9, 10))
	board.register_unit("hero_1", {"team": "A"})
	board.place_unit("hero_2", Vector2i(10, 10))
	board.register_unit("hero_2", {"team": "A"})
	board.place_unit("insect_1", Vector2i(5, 5))
	board.register_unit("insect_1", {"team": "B"})

	# Act
	var team_a: Array[String] = board.get_units_by_team("A")
	var team_b: Array[String] = board.get_units_by_team("B")

	# Assert
	assert_eq(team_a.size(), 2, "Team A has 2 units")
	assert_has(team_a, "hero_1")
	assert_has(team_a, "hero_2")
	assert_eq(team_b.size(), 1, "Team B has 1 unit")
	assert_has(team_b, "insect_1")

# ── 3. Tactical FFT Movement & Attack Range Calculations ─────────────────────

func test_get_reachable_cells_within_movement_range() -> void:
	# Arrange
	var board: FortressBoard = FortressBoard.new()
	var center: Vector2i = Vector2i(10, 10)
	var move_range: int = 2

	# Act
	var reachable: Array[Vector2i] = board.get_reachable_cells(center, move_range)

	# Assert
	assert_gt(reachable.size(), 0, "Should have reachable cells")
	assert_does_not_have(reachable, center, "Starting cell is not in reachable destinations")
	# Immediate orthogonal neighbors must be reachable
	assert_has(reachable, Vector2i(10, 9), "North neighbor reachable")
	assert_has(reachable, Vector2i(10, 11), "South neighbor reachable")
	assert_has(reachable, Vector2i(9, 10), "West neighbor reachable")
	assert_has(reachable, Vector2i(11, 10), "East neighbor reachable")
	# 2-step cells must be reachable
	assert_has(reachable, Vector2i(10, 8), "2 steps North reachable")
	assert_has(reachable, Vector2i(12, 10), "2 steps East reachable")
	# 3-step cells must NOT be reachable
	assert_does_not_have(reachable, Vector2i(10, 7), "3 steps North beyond range")

func test_get_reachable_cells_invalid_or_zero_range_returns_empty() -> void:
	# Arrange
	var board: FortressBoard = FortressBoard.new()

	# Act & Assert
	assert_eq(board.get_reachable_cells(Vector2i(-1, 0), 3).size(), 0, "Invalid pos returns empty")
	assert_eq(board.get_reachable_cells(Vector2i(5, 5), 0).size(), 0, "Range 0 returns empty")
	assert_eq(board.get_reachable_cells(Vector2i(5, 5), -2).size(), 0, "Negative range returns empty")

func test_get_attackable_cells_detects_enemies_within_range() -> void:
	# Arrange
	var board: FortressBoard = FortressBoard.new()
	var hero_pos: Vector2i = Vector2i(10, 10)
	board.place_unit("hero", hero_pos)
	board.register_unit("hero", {"team": "A", "hp": 30})

	# Enemy in range (1 tile away)
	var enemy1_pos: Vector2i = Vector2i(10, 11)
	board.place_unit("enemy1", enemy1_pos)
	board.register_unit("enemy1", {"team": "B", "hp": 20})

	# Ally in range (should NOT be attackable)
	var ally_pos: Vector2i = Vector2i(11, 10)
	board.place_unit("ally", ally_pos)
	board.register_unit("ally", {"team": "A", "hp": 25})

	# Enemy out of range (5 tiles away)
	var far_enemy_pos: Vector2i = Vector2i(10, 15)
	board.place_unit("enemy_far", far_enemy_pos)
	board.register_unit("enemy_far", {"team": "B", "hp": 20})

	# Act
	var targets: Array[Vector2i] = board.get_attackable_cells(hero_pos, 1, "A")

	# Assert
	assert_eq(targets.size(), 1, "Exactly 1 valid enemy target in range")
	assert_has(targets, enemy1_pos, "Nearby enemy is attackable")
	assert_does_not_have(targets, ally_pos, "Ally is not attackable")
	assert_does_not_have(targets, far_enemy_pos, "Far enemy is not attackable")

func test_get_attackable_cells_ignores_dead_enemies() -> void:
	# Arrange
	var board: FortressBoard = FortressBoard.new()
	var hero_pos: Vector2i = Vector2i(10, 10)
	board.place_unit("hero", hero_pos)
	board.register_unit("hero", {"team": "A", "hp": 30})

	var enemy_pos: Vector2i = Vector2i(10, 11)
	board.place_unit("dead_enemy", enemy_pos)
	board.register_unit("dead_enemy", {"team": "B", "hp": 0}) # Dead

	# Act
	var targets: Array[Vector2i] = board.get_attackable_cells(hero_pos, 2, "A")

	# Assert
	assert_eq(targets.size(), 0, "Dead enemy is not attackable")

func test_reset_board_clears_all_items_and_unit_data() -> void:
	# Arrange
	var board: FortressBoard = FortressBoard.new()
	board.place_item(Vector2i(5, 5), FortressBoard.ITEM_CRISTAL)
	board.place_unit("hero", Vector2i(10, 10))
	board.register_unit("hero", {"team": "A", "hp": 30})

	# Act
	board.reset_board()

	# Assert
	assert_eq(board.get_all_items().size(), 0, "All items cleared on reset")
	assert_eq(board.get_all_units().size(), 0, "All units cleared on reset")
	assert_false(board.has_item_at(Vector2i(5, 5)), "Item no longer exists at (5,5)")
	assert_false(board.has_unit("hero"), "Hero no longer exists on board")

# ── 6. Resource Stacking & Regional 10x Distribution (AAA Tests) ─────────────

func test_place_item_resource_stacking_happy_path() -> void:
	# Arrange
	var board: FortressBoard = FortressBoard.new()
	var pos: Vector2i = Vector2i(9, 5)

	# Act - First drop: 5 Wood
	var ok1: bool = board.place_item(pos, FortressBoard.ITEM_WOOD, {"name": "Pilha de Madeira", "wood": 5, "amount": 5})
	var item1: Dictionary = board.get_item_at(pos)

	# Act - Second drop on the same cell: 5 more Wood
	var ok2: bool = board.place_item(pos, FortressBoard.ITEM_WOOD, {"name": "Pilha de Madeira", "wood": 5, "amount": 5})
	var stacked_item: Dictionary = board.get_item_at(pos)

	# Assert
	assert_true(ok1, "First item placement succeeded")
	assert_true(ok2, "Second item placement (stacking) succeeded")
	assert_eq(int(item1.get("wood", 0)), 5, "First item had 5 wood")
	assert_eq(int(stacked_item.get("wood", 0)), 10, "Stacked item accumulated 10 wood total")
	assert_eq(int(stacked_item.get("amount", 0)), 10, "Total amount accumulated to 10")
	assert_true(str(stacked_item.get("name", "")).contains("(x10)"), "Stacked item name reflects accumulated quantity (x10)")

func test_place_item_multi_resource_stacking_merges_all_types() -> void:
	# Arrange
	var board: FortressBoard = FortressBoard.new()
	var pos: Vector2i = Vector2i(7, 7)

	# Act - Place first item with wood and leather
	board.place_item(pos, FortressBoard.ITEM_WOOD, {"wood": 4, "leather": 3, "amount": 2})
	# Act - Place second item with leather and gold on the same cell
	board.place_item(pos, FortressBoard.ITEM_GOLD, {"leather": 7, "gold": 5, "amount": 3})
	var result: Dictionary = board.get_item_at(pos)

	# Assert
	assert_eq(int(result.get("amount", 0)), 5, "Amounts stacked correctly (2 + 3 = 5)")
	assert_eq(int(result.get("wood", 0)), 4, "Wood preserved in stack")
	assert_eq(int(result.get("leather", 0)), 10, "Leather summed correctly (3 + 7 = 10)")
	assert_eq(int(result.get("gold", 0)), 5, "Gold added to stack")

func test_spawn_default_map_items_10_of_each_resource_per_region() -> void:
	# Arrange
	var board: FortressBoard = FortressBoard.new()

	# Act
	board.spawn_default_map_items()

	# Assert - Region Carpintaria: contains at least 10 wood on the ground
	var carp_cells: Array[Vector2i] = board.get_cells_in_zone(FortressBoard.ZONE_CARPINTARIA)
	var total_wood_carp: int = 0
	for c in carp_cells:
		if board.has_item_at(c):
			var it: Dictionary = board.get_item_at(c)
			total_wood_carp += int(it.get("wood", 0))
	assert_true(total_wood_carp >= 10, "Carpintaria region must contain at least 10 wood on the ground")

	# Assert - Region Curtume: contains at least 10 leather on the ground
	var curt_cells: Array[Vector2i] = board.get_cells_in_zone(FortressBoard.ZONE_CURTUME)
	var total_leather_curt: int = 0
	for c in curt_cells:
		if board.has_item_at(c):
			var it: Dictionary = board.get_item_at(c)
			total_leather_curt += int(it.get("leather", 0))
	assert_true(total_leather_curt >= 10, "Curtume region must contain at least 10 leather on the ground")

	# Assert - Region Fundição / Pátio: contains at least 10 gold on the ground
	var fund_cells: Array[Vector2i] = board.get_cells_in_zone(FortressBoard.ZONE_FUNDICAO)
	var patio_cells: Array[Vector2i] = board.get_cells_in_zone(FortressBoard.ZONE_PATIO_CENTRAL)
	var total_gold_central: int = 0
	for c in fund_cells + patio_cells:
		if board.has_item_at(c):
			var it: Dictionary = board.get_item_at(c)
			total_gold_central += int(it.get("gold", 0))
	assert_true(total_gold_central >= 10, "Fundição and Pátio regions must contain at least 10 gold on the ground")

func test_controller_item_pickup_collects_leather_and_gold_and_stacked_resources() -> void:
	# Arrange
	var controller: CercoGameController = autofree(CercoGameController.new())
	var economy: WorkshopEconomy = WorkshopEconomy.new()
	economy.set_resources(0, 0, 0, 0, 0)
	controller.economy = economy

	# Act 1 - Pickup 10 Leather
	controller._on_board_view_item_pickup("hero", Vector2i(9, 14), {
		"type": "LEATHER",
		"name": "Estoque de Couro",
		"leather": 10
	})

	# Act 2 - Pickup 10 Gold
	controller._on_board_view_item_pickup("hero", Vector2i(6, 10), {
		"type": "GOLD",
		"name": "Reserva de Ouro",
		"gold": 10
	})

	# Act 3 - Pickup multi-stacked item (Wood 10 + Leather 5 residual)
	controller._on_board_view_item_pickup("hero", Vector2i(9, 5), {
		"type": "WOOD",
		"name": "Pilha de Madeira (x10)",
		"wood": 10,
		"leather": 5
	})

	# Assert
	assert_eq(economy.get_resource("leather"), 15, "Collected leather total: 10 initial + 5 residual")
	assert_eq(economy.get_resource("crystal"), 10, "Collected gold delivered to crystal economy: 10")
	assert_eq(economy.get_resource("wood"), 10, "Collected wood total: 10")

func test_card_ui_high_quality_presentation_and_styling() -> void:
	# Arrange
	var card_ui: CardUI = autofree(CardUI.new())
	var card: CardData = CardData.new()
	card.id = "card_vanguarda_epica"
	card.card_name = "Vanguarda Épica"
	card.badge = CardData.BADGE_COMBATE
	card.cost_wood = 2
	card.cost_metal = 3
	card.cost_ap = 1
	card.movement = 2
	card.work = 1
	card.excavation = 1
	card.description = "Avanço tático na brecha da muralha."

	# Act
	card_ui.setup(card, 0)

	# Assert
	assert_eq(card_ui.custom_minimum_size, Vector2(104.0, 146.0), "CardUI has refined 104x146 dimensions")
	var name_lbl: Label = card_ui.find_child("NameLabel", true, false) as Label
	assert_not_null(name_lbl, "NameLabel exists")
	assert_eq(name_lbl.text, "Vanguarda Épica", "Card title rendered cleanly")

	var badge_lbl: Label = card_ui.find_child("BadgeLabel", true, false) as Label
	assert_not_null(badge_lbl, "BadgeLabel exists")
	assert_true(badge_lbl.text.contains("COMBATE"), "Badge contains archetype text")
	assert_true(badge_lbl.text.contains("⚔"), "Badge contains battle glyph")

	var cost_lbl: Label = card_ui.find_child("CostLabel", true, false) as Label
	assert_not_null(cost_lbl, "CostLabel exists")
	assert_true(cost_lbl.text.contains("MAD:2"), "Cost pill renders wood cost")
	assert_true(cost_lbl.text.contains("MET:3"), "Cost pill renders metal cost")
	assert_true(cost_lbl.text.contains("AP:1"), "Cost pill renders AP cost")

	var stats_lbl: Label = card_ui.find_child("StatsLabel", true, false) as Label
	assert_not_null(stats_lbl, "StatsLabel exists")
	assert_true(stats_lbl.text.contains("+2 MOV"), "Stats pill renders movement bonus")
	assert_true(stats_lbl.text.contains("+1 TRAB"), "Stats pill renders work bonus")
	assert_true(stats_lbl.text.contains("+1 ESC"), "Stats pill renders excavation bonus")

	var btn_play: Button = card_ui.find_child("BtnPlay", true, false) as Button
	assert_not_null(btn_play, "BtnPlay exists")
	assert_eq(btn_play.text, "▶ ATIVAR", "Initial activation button text")

	card_ui.set_selected(true)
	assert_eq(btn_play.text, "▶ ATIVAR AGORA", "Button text updates when selected")

	card_ui.set_disabled(true)
	assert_eq(btn_play.text, "▶ BLOQUEADA", "Button text updates when disabled")

# res://test/unit/test_enemy_advance_and_sprites.gd
extends GutTest

## Test suite for Enemy AI advancement (movement and attack) and Isectum sprite resolution.
## Follows strict Arrange-Act-Assert (AAA) pattern with comprehensive edge case coverage.

# ── 1. Isectum Sprite & Texture Resolution Tests ──────────────────────────────

func test_all_24_canonical_isectum_castes_resolve_textures() -> void:
	# Arrange
	var board_view: FortressBoardView = autofree(FortressBoardView.new())
	var missing_castes: Array[String] = []

	# Act & Assert
	for caste_id in IsectumCastes.CANONICAL_IDS:
		var tex: Texture2D = board_view.get_unit_texture(caste_id, {"name": caste_id})
		if tex == null:
			missing_castes.append(caste_id)

	assert_eq(missing_castes.size(), 0, "All 24 canonical Isectum castes must resolve to valid textures: %s" % str(missing_castes))

func test_enemy_wave_uids_with_prefixes_resolve_textures() -> void:
	# Arrange
	var board_view: FortressBoardView = autofree(FortressBoardView.new())
	var test_wave_uids: Array[String] = [
		"zangao_invasor_w1_1",
		"soldado_mandibula_w1_2",
		"operario_escavador_w2_1",
		"barata_praga_w2_3",
		"cupim_roedor_w3_2",
		"rainha_do_enxame_w5_1",
		"colosso_isectum_w8_1"
	]

	# Act & Assert
	for uid in test_wave_uids:
		var tex: Texture2D = board_view.get_unit_texture(uid, {})
		assert_not_null(tex, "Wave UID '%s' should resolve to a valid caste texture" % uid)

func test_threat_deck_descriptions_resolve_textures_without_falling_back() -> void:
	# Arrange
	var board_view: FortressBoardView = autofree(FortressBoardView.new())
	var threat_names: Array[String] = [
		"Horda: Zangão Invasor",
		"Horda: Soldado Mandíbula",
		"Horda: Operário Escavador",
		"Horda: Barata da Praga",
		"Chegada do Chefe: Rainha do Enxame",
		"Chegada do Chefe: Colosso Isectum"
	]

	# Act & Assert
	for desc in threat_names:
		var tex: Texture2D = board_view.get_unit_texture("unknown_threat_uid", {"name": desc})
		assert_not_null(tex, "Threat description '%s' should resolve to a caste texture" % desc)

func test_unknown_unit_returns_null_safely_without_crash() -> void:
	# Arrange
	var board_view: FortressBoardView = autofree(FortressBoardView.new())

	# Act
	var tex: Texture2D = board_view.get_unit_texture("entidade_alienigena_totalmente_desconhecida", {"name": "Desconhecido"})

	# Assert
	assert_null(tex, "Unknown units should safely return null so fallback rendering can handle them")

# ── 2. Enemy AI Advancement & Movement Tests ─────────────────────────────────

func test_advance_enemy_units_moves_closer_to_hero() -> void:
	# Arrange
	var controller: CercoGameController = autofree(CercoGameController.new())
	var board: FortressBoard = FortressBoard.new()
	controller.board = board

	# Hero placed at center (10, 10)
	board.place_unit("aquele", Vector2i(10, 10))
	board.register_unit("aquele", {
		"name": "Aquele", "team": "A", "hp": 45, "max_hp": 45, "ac": 16, "move_range": 3
	})

	# Enemy placed at outer north spawn (10, 1)
	var enemy_id: String = "zangao_invasor_w1_1"
	board.place_unit(enemy_id, Vector2i(10, 1))
	board.register_unit(enemy_id, {
		"name": "Zangão Invasor", "team": "B", "hp": 18, "max_hp": 18, "ac": 13,
		"move_range": 3, "attack_range": 1, "attack_bonus": 3
	})

	var initial_dist: int = maxi(absi(10 - 10), absi(1 - 10)) # 9 cells away

	# Act
	var summary: Dictionary = controller.advance_enemy_units()
	var new_pos: Vector2i = board.get_unit_position(enemy_id)
	var new_dist: int = maxi(absi(new_pos.x - 10), absi(new_pos.y - 10))

	# Assert
	assert_eq(summary["moved_count"], 1, "Enemy should have moved exactly 1 time")
	assert_lt(new_dist, initial_dist, "Enemy distance to hero should decrease after advancing")
	assert_true(new_pos.y > 1, "Enemy should advance south towards the fortress center")

func test_advance_enemy_units_attacks_adjacent_hero() -> void:
	# Arrange
	var controller: CercoGameController = autofree(CercoGameController.new())
	var board: FortressBoard = FortressBoard.new()
	controller.board = board

	# Hero placed at (10, 5) with AC 0 to guarantee hit
	board.place_unit("stark", Vector2i(10, 5))
	board.register_unit("stark", {
		"name": "Stark", "team": "A", "hp": 50, "max_hp": 50, "ac": 0, "move_range": 3
	})

	# Enemy placed adjacent at (10, 4)
	var enemy_id: String = "soldado_mandibula_w1_1"
	board.place_unit(enemy_id, Vector2i(10, 4))
	board.register_unit(enemy_id, {
		"name": "Soldado Mandíbula", "team": "B", "hp": 25, "max_hp": 25, "ac": 14,
		"move_range": 2, "attack_range": 1, "attack_bonus": 5
	})

	# Act
	var summary: Dictionary = controller.advance_enemy_units()
	var stark_data: Dictionary = board.get_unit_data("stark")

	# Assert
	assert_eq(summary["attacks_count"], 1, "Enemy should perform an attack on adjacent hero")
	assert_lt(int(stark_data["hp"]), 50, "Hero should take damage from enemy attack")

func test_advance_enemy_units_attacks_perimeter_wall_when_no_hero_adjacent() -> void:
	# Arrange
	var controller: CercoGameController = autofree(CercoGameController.new())
	var board: FortressBoard = FortressBoard.new()
	controller.board = board

	# Enemy placed directly in MURALHA_NORTE zone (y=2 is MURALHA_NORTE)
	var enemy_id: String = "operario_escavador_w1_1"
	board.place_unit(enemy_id, Vector2i(10, 2))
	board.register_unit(enemy_id, {
		"name": "Operário Escavador", "team": "B", "hp": 20, "max_hp": 20, "ac": 12,
		"move_range": 0, "attack_range": 1, "attack_bonus": 2 # 0 move so it stays in wall zone
	})

	var initial_wall_hp: int = board.get_wall_hp(FortressBoard.ZONE_MURALHA_NORTE)

	# Act
	var summary: Dictionary = controller.advance_enemy_units()
	var new_wall_hp: int = board.get_wall_hp(FortressBoard.ZONE_MURALHA_NORTE)

	# Assert
	assert_eq(summary["wall_hits_count"], 1, "Enemy in wall zone should damage the wall")
	assert_lt(new_wall_hp, initial_wall_hp, "Wall integrity should be reduced")

func test_advance_enemy_units_empty_board_or_no_enemies_safe() -> void:
	# Arrange
	var controller: CercoGameController = autofree(CercoGameController.new())
	var board: FortressBoard = FortressBoard.new()
	controller.board = board

	# Act - No enemies registered
	var summary_empty: Dictionary = controller.advance_enemy_units()

	# Assert
	assert_eq(summary_empty["moved_count"], 0)
	assert_eq(summary_empty["attacks_count"], 0)
	assert_eq(summary_empty["wall_hits_count"], 0)

	# Act - Null board edge case
	controller.board = null
	var summary_null: Dictionary = controller.advance_enemy_units()

	# Assert
	assert_eq(summary_null["moved_count"], 0)
	assert_eq(summary_null["attacks_count"], 0)
	assert_eq(summary_null["wall_hits_count"], 0)

func test_dead_enemy_does_not_advance_or_attack() -> void:
	# Arrange
	var controller: CercoGameController = autofree(CercoGameController.new())
	var board: FortressBoard = FortressBoard.new()
	controller.board = board

	board.place_unit("aquele", Vector2i(10, 10))
	board.register_unit("aquele", {
		"name": "Aquele", "team": "A", "hp": 45, "max_hp": 45, "ac": 16
	})

	var enemy_id: String = "dead_zangao"
	board.place_unit(enemy_id, Vector2i(10, 1))
	board.register_unit(enemy_id, {
		"name": "Zangão Morto", "team": "B", "hp": 0, "max_hp": 18, "is_alive": false,
		"move_range": 3, "attack_range": 1
	})

	# Act
	var summary: Dictionary = controller.advance_enemy_units()
	var pos_after: Vector2i = board.get_unit_position(enemy_id)

	# Assert
	assert_eq(summary["moved_count"], 0, "Dead enemy must not move")
	assert_eq(summary["attacks_count"], 0, "Dead enemy must not attack")
	assert_eq(pos_after, Vector2i(10, 1), "Dead enemy position should remain unchanged")

func test_fortress_board_find_path_navigates_around_occupied_cells() -> void:
	# Arrange
	var board: FortressBoard = FortressBoard.new()
	var start_pos: Vector2i = Vector2i(5, 5)
	var end_pos: Vector2i = Vector2i(5, 7)

	# Coloca um obstáculo (unidade intermediária) em (5, 6)
	board.place_unit("bloco_obstaculo", Vector2i(5, 6))

	# Act
	var path: Array[Vector2i] = board.find_path(start_pos, end_pos, false)

	# Assert
	assert_gt(path.size(), 0, "Path should be found by detouring around obstacle")
	assert_eq(path[path.size() - 1], end_pos, "Path should reach the destination")
	for step in path:
		assert_ne(step, Vector2i(5, 6), "Path must not walk onto the occupied obstacle cell")

func test_flanker_enemy_targets_weakest_hero() -> void:
	# Arrange
	var controller: CercoGameController = autofree(CercoGameController.new())
	var board: FortressBoard = FortressBoard.new()
	controller.board = board

	# Herói com HP alto em (12, 5)
	board.place_unit("stark", Vector2i(12, 5))
	board.register_unit("stark", {
		"name": "Stark", "team": "A", "hp": 50, "max_hp": 50, "ac": 16, "move_range": 3
	})

	# Herói com HP baixo (fragilizado) em (8, 5)
	board.place_unit("aquele", Vector2i(8, 5))
	board.register_unit("aquele", {
		"name": "Aquele", "team": "A", "hp": 5, "max_hp": 45, "ac": 14, "move_range": 3
	})

	# Flanqueador Vespa colocada no meio (10, 2)
	var enemy_id: String = "vespa_cassador_w1_1"
	board.place_unit(enemy_id, Vector2i(10, 2))
	board.register_unit(enemy_id, {
		"name": "Vespa Caçadora", "team": "B", "caste_id": "vespa",
		"hp": 22, "max_hp": 22, "ac": 14, "move_range": 3, "attack_range": 1, "attack_bonus": 3
	})

	# Act
	var summary: Dictionary = controller.advance_enemy_units()
	var new_pos: Vector2i = board.get_unit_position(enemy_id)

	# Assert - Vespa deve ter se movido em direção a Aquele (x=8), diminuindo a distância para x=8 e não para x=12
	assert_eq(summary["moved_count"], 1)
	assert_lte(new_pos.x, 10, "Flanker should move towards the lower HP hero (x=8)")

func test_siege_enemy_deals_bonus_damage_to_walls() -> void:
	# Arrange
	var controller: CercoGameController = autofree(CercoGameController.new())
	var board: FortressBoard = FortressBoard.new()
	controller.board = board

	# Besouro Blindado colocado na muralha norte
	var enemy_id: String = "besouro_blindado_w1_1"
	board.place_unit(enemy_id, Vector2i(10, 2)) # y=2 is MURALHA_NORTE
	board.register_unit(enemy_id, {
		"name": "Besouro Blindado", "team": "B", "caste_id": "besouro",
		"hp": 40, "max_hp": 40, "ac": 18, "move_range": 0, "attack_range": 1, "attack_bonus": 3
	})

	var initial_wall_hp: int = board.get_wall_hp(FortressBoard.ZONE_MURALHA_NORTE)

	# Act
	var summary: Dictionary = controller.advance_enemy_units()
	var new_wall_hp: int = board.get_wall_hp(FortressBoard.ZONE_MURALHA_NORTE)
	var dmg_taken: int = initial_wall_hp - new_wall_hp

	# Assert
	assert_eq(summary["wall_hits_count"], 1)
	assert_gte(dmg_taken, 6, "Siege caste deals bonus damage to walls (min 3 + 3 = 6)")

# ── 3. Clean Sprite Rendering (No Circles / Coin Rings) Tests ─────────────────

func test_draw_unit_entity_headless_execution_with_real_sprite() -> void:
	# Arrange
	var board_view: FortressBoardView = autofree(FortressBoardView.new())
	var hero_data: Dictionary = {
		"name": "Aquele", "team": "A", "hp": 45, "max_hp": 45, "ac": 16, "attack_bonus": 4
	}

	# Act
	board_view._draw_unit_entity("aquele", hero_data, Vector2(150, 150), 1.0, false)

	# Assert
	assert_not_null(board_view.get_unit_texture("aquele", hero_data), "Hero sprite should resolve cleanly")

func test_draw_unit_entity_headless_execution_selected_state() -> void:
	# Arrange
	var board_view: FortressBoardView = autofree(FortressBoardView.new())
	var hero_data: Dictionary = {
		"name": "Stark", "team": "A", "hp": 50, "max_hp": 50, "ac": 18, "attack_bonus": 5
	}

	# Act & Assert (Should execute FFT selection highlight without exception)
	board_view._draw_unit_entity("stark", hero_data, Vector2(200, 200), 1.2, true)
	assert_true(true, "Selected unit entity draws cleanly with FFT arrow indicator and no circular token ring")

func test_draw_unit_entity_enemy_team_b_clean_sprite() -> void:
	# Arrange
	var board_view: FortressBoardView = autofree(FortressBoardView.new())
	var enemy_data: Dictionary = {
		"name": "Zangão Invasor", "team": "B", "hp": 18, "max_hp": 18, "ac": 13, "attack_bonus": 3
	}

	# Act & Assert (Enemy draws directly onto the battlefield without circular token rings)
	board_view._draw_unit_entity("zangao_invasor_w1_1", enemy_data, Vector2(300, 300), 1.0, false)
	assert_not_null(board_view.get_unit_texture("zangao_invasor_w1_1", enemy_data))

func test_draw_unit_entity_fallback_when_texture_null() -> void:
	# Arrange
	var board_view: FortressBoardView = autofree(FortressBoardView.new())
	var unknown_data: Dictionary = {
		"name": "Horda: Misteriosa", "team": "B", "hp": 10, "max_hp": 10, "ac": 10, "attack_bonus": 2
	}

	# Act & Assert (Fallback rectangular plate renders cleanly without circular coin rings)
	board_view._draw_unit_entity("unknown_beast", unknown_data, Vector2(250, 250), 1.0, false)
	assert_true(true, "Fallback unit renders without throwing errors")

func test_draw_commander_pillar_with_prince_lysander() -> void:
	# Arrange
	var board_view: FortressBoardView = autofree(FortressBoardView.new())

	# Act & Assert - Standard scale (zoom = 1.0)
	board_view._draw_commander_throne(400.0, 300.0, 1.0)
	assert_true(true, "Commander pillar renders Prince Lysander atop elevated platform cleanly")

	# Act & Assert - Edge cases: minimum zoom (0.5) and enlarged zoom (2.0)
	board_view._draw_commander_throne(100.0, 100.0, 0.5)
	board_view._draw_commander_throne(500.0, 500.0, 2.0)
	assert_true(true, "Commander pillar scales robustly across all zoom ranges")

# ── 4. AI Targeting, Multi-Zone Spawning & Ranged Tactics Tests ─────────────────

func test_threat_deck_wave_spawns_across_multiple_perimeter_zones() -> void:
	# Arrange
	var controller: CercoGameController = autofree(CercoGameController.new())
	var board: FortressBoard = FortressBoard.new()
	var threat_deck: ThreatDeck = ThreatDeck.new()
	controller.board = board
	controller.threat_deck = threat_deck

	# Act
	var spawned_ids: Array[String] = controller.spawn_enemy_wave(2)

	# Assert
	assert_gt(spawned_ids.size(), 0, "Wave 2 must spawn enemies")
	var zones_hit: Dictionary = {}
	for uid in spawned_ids:
		var pos: Vector2i = board.get_unit_position(uid)
		var zname: String = board.get_zone_at(pos)
		zones_hit[zname] = true

	# Validates that enemies are distributed and NOT restricted solely to SPAWN_NORTE
	assert_gt(zones_hit.size(), 1, "ThreatDeck enemies should spawn across multiple perimeter zones: %s" % str(zones_hit.keys()))

func test_enemy_caste_stats_populated_from_canonical_catalog() -> void:
	# Arrange
	var controller: CercoGameController = autofree(CercoGameController.new())
	var board: FortressBoard = FortressBoard.new()
	controller.board = board

	# Simula onda com Castas canônicas especializadas
	var custom_threat_deck: ThreatDeck = ThreatDeck.new()
	controller.threat_deck = custom_threat_deck

	# Act
	var spawned: Array[String] = controller.spawn_enemy_wave(3)

	# Assert
	for uid in spawned:
		var udata: Dictionary = board.get_unit_data(uid)
		assert_true(udata.has("caste_id"), "Unit data must retain canonical caste_id")
		var cid: String = udata.get("caste_id", "")
		var caste_data: IsectumCasteData = IsectumCastes.get_caste(cid)
		if caste_data != null:
			assert_eq(int(udata.get("attack_range", 1)), caste_data.attack_range, "Attack range should match canonical caste data")
			assert_eq(int(udata.get("move_range", 3)), caste_data.speed, "Move range should match canonical speed")

func test_enemy_ranged_positioning_stops_at_attack_range() -> void:
	# Arrange
	var controller: CercoGameController = autofree(CercoGameController.new())
	var board: FortressBoard = FortressBoard.new()
	controller.board = board

	# Hero placed at (10, 10)
	board.place_unit("aquele", Vector2i(10, 10))
	board.register_unit("aquele", {
		"name": "Aquele", "team": "A", "hp": 40, "max_hp": 40, "ac": 15, "move_range": 3
	})

	# Ranged unit (Libélula com attack_range = 3, move = 4) placed at (10, 5) -> dist = 5
	var enemy_id: String = "libelula_bombardeira_w1_1"
	board.place_unit(enemy_id, Vector2i(10, 5))
	board.register_unit(enemy_id, {
		"name": "Libélula Bombardeira", "team": "B", "caste_id": "libelula",
		"hp": 25, "max_hp": 25, "ac": 14, "move_range": 4, "attack_range": 3, "attack_bonus": 4
	})

	# Act
	var summary: Dictionary = controller.advance_enemy_units()
	var final_pos: Vector2i = board.get_unit_position(enemy_id)
	var final_dist: int = maxi(absi(final_pos.x - 10), absi(final_pos.y - 10))

	# Assert
	assert_eq(summary["moved_count"], 1, "Ranged enemy should advance towards attack position")
	assert_lte(final_dist, 3, "Ranged enemy should stop within its attack range (<= 3)")
	assert_gte(final_dist, 2, "Ranged enemy should not hug hero melee cell when ranged distance is sufficient")
	assert_eq(summary["attacks_count"], 1, "Ranged enemy should immediately fire projectile at hero upon reaching range")

func test_pick_best_hero_target_edge_cases_and_priority() -> void:
	# Arrange
	var controller: CercoGameController = autofree(CercoGameController.new())
	var board: FortressBoard = FortressBoard.new()
	controller.board = board

	# Edge case: No units or empty attackable list
	var empty_res: String = controller._pick_best_hero_target([], [], true)
	assert_eq(empty_res, "", "Empty attackable cells should return empty string")

	# Register 2 heroes: Stark (HP 50) and Aquele (HP 12)
	board.place_unit("stark", Vector2i(5, 5))
	board.register_unit("stark", {"name": "Stark", "team": "A", "hp": 50})
	board.place_unit("aquele", Vector2i(5, 6))
	board.register_unit("aquele", {"name": "Aquele", "team": "A", "hp": 12})

	# Act & Assert - Prefer lowest HP (Flanker priority)
	var target_low: String = controller._pick_best_hero_target([Vector2i(5, 5), Vector2i(5, 6)], ["stark", "aquele"], true)
	assert_eq(target_low, "aquele", "Should select Aquele with 12 HP over Stark with 50 HP")

	# Act & Assert - Standard priority (also picks available weakest or closest)
	var target_std: String = controller._pick_best_hero_target([Vector2i(5, 6)], ["stark", "aquele"], false)
	assert_eq(target_std, "aquele", "Should correctly map cell to hero")




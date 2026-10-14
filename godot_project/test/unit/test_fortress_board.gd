# res://test/unit/test_fortress_board.gd
extends GutTest

## Test suite for FortressBoard
## Validates 20x20 grid geometry, 400-cell 17-zone coverage, elevation levels,
## bidirectional adjacency graph, invasion pathways, wall integrity, and unit tracking.

# ── 1. Grid Dimensions & Cell Validation ──────────────────────────────────────

func test_board_grid_dimensions_is_20x20() -> void:
	# Arrange
	var board: FortressBoard = FortressBoard.new()

	# Act
	var width: int = FortressBoard.GRID_WIDTH
	var height: int = FortressBoard.GRID_HEIGHT
	var total: int = FortressBoard.TOTAL_CELLS

	# Assert
	assert_eq(width, 20, "Board width must be 20")
	assert_eq(height, 20, "Board height must be 20")
	assert_eq(total, 400, "Board total cell count must be 400")

func test_is_valid_cell_boundary_checks() -> void:
	# Arrange
	var board: FortressBoard = FortressBoard.new()

	# Act & Assert - Valid corners and center
	assert_true(board.is_valid_cell(Vector2i(0, 0)), "Corner (0,0) is valid")
	assert_true(board.is_valid_cell(Vector2i(19, 0)), "Corner (19,0) is valid")
	assert_true(board.is_valid_cell(Vector2i(0, 19)), "Corner (0,19) is valid")
	assert_true(board.is_valid_cell(Vector2i(19, 19)), "Corner (19,19) is valid")
	assert_true(board.is_valid_cell(Vector2i(10, 10)), "Center (10,10) is valid")

	# Act & Assert - Out of bounds
	assert_false(board.is_valid_cell(Vector2i(-1, 0)), "Negative X is invalid")
	assert_false(board.is_valid_cell(Vector2i(0, -1)), "Negative Y is invalid")
	assert_false(board.is_valid_cell(Vector2i(20, 10)), "X >= 20 is invalid")
	assert_false(board.is_valid_cell(Vector2i(10, 20)), "Y >= 20 is invalid")
	assert_false(board.is_valid_cell(Vector2i(-5, -5)), "Negative both is invalid")
	assert_false(board.is_valid_cell(Vector2i(100, 100)), "Extreme out of bounds is invalid")

# ── 2. Complete 400-Cell Coverage & 17 Canonical Zones ────────────────────────

func test_all_17_zones_exist_and_match_canonical_names() -> void:
	# Arrange & Act
	var zones: Array[String] = FortressBoard.ALL_ZONES

	# Assert
	assert_eq(zones.size(), 17, "Exactly 17 logical fortress zones must exist")
	assert_has(zones, FortressBoard.ZONE_CAMARA_CENTRAL, "Câmara Central present")
	assert_has(zones, FortressBoard.ZONE_CARPINTARIA, "Carpintaria present")
	assert_has(zones, FortressBoard.ZONE_CURTUME, "Curtume present")
	assert_has(zones, FortressBoard.ZONE_FUNDICAO, "Fundição present")
	assert_has(zones, FortressBoard.ZONE_PATIO_CENTRAL, "Pátio Central present")
	assert_has(zones, FortressBoard.ZONE_MURALHA_NORTE, "Muralha Norte present")
	assert_has(zones, FortressBoard.ZONE_MURALHA_SUL, "Muralha Sul present")
	assert_has(zones, FortressBoard.ZONE_MURALHA_LESTE, "Muralha Leste present")
	assert_has(zones, FortressBoard.ZONE_MURALHA_OESTE, "Muralha Oeste present")
	assert_has(zones, FortressBoard.ZONE_TORRE_NOROESTE, "Torre Noroeste present")
	assert_has(zones, FortressBoard.ZONE_TORRE_NORDESTE, "Torre Nordeste present")
	assert_has(zones, FortressBoard.ZONE_TORRE_SUDOESTE, "Torre Sudoeste present")
	assert_has(zones, FortressBoard.ZONE_TORRE_SUDESTE, "Torre Sudeste present")
	assert_has(zones, FortressBoard.ZONE_SPAWN_NORTE, "Spawn Norte present")
	assert_has(zones, FortressBoard.ZONE_SPAWN_SUL, "Spawn Sul present")
	assert_has(zones, FortressBoard.ZONE_SPAWN_LESTE, "Spawn Leste present")
	assert_has(zones, FortressBoard.ZONE_SPAWN_OESTE, "Spawn Oeste present")

func test_full_400_cell_mapping_no_duplicates_no_missing() -> void:
	# Arrange
	var board: FortressBoard = FortressBoard.new()
	var visited_cells: Dictionary = {}
	var zone_counts: Dictionary = {}

	# Act
	for y in range(FortressBoard.GRID_HEIGHT):
		for x in range(FortressBoard.GRID_WIDTH):
			var cell: Vector2i = Vector2i(x, y)
			var zone_id: String = board.get_zone_at(cell)

			# Validate every cell has a non-empty valid zone
			assert_true(not zone_id.is_empty(), "Cell (%d, %d) must map to a zone" % [x, y])
			assert_has(FortressBoard.ALL_ZONES, zone_id, "Zone '%s' at (%d, %d) is valid" % [zone_id, x, y])

			visited_cells[cell] = zone_id
			zone_counts[zone_id] = zone_counts.get(zone_id, 0) + 1

	# Assert
	assert_eq(visited_cells.size(), 400, "Exactly 400 distinct cells visited")
	assert_eq(zone_counts.size(), 17, "All 17 zones received at least 1 cell")

	var total_sum: int = 0
	for count_val in zone_counts.values():
		total_sum += int(count_val)
	assert_eq(total_sum, 400, "Sum of cell counts across all zones must equal 400")

func test_zone_cell_distribution_exact_counts() -> void:
	# Arrange
	var board: FortressBoard = FortressBoard.new()

	# Act & Assert - Central core: 4x4 = 16 cells
	assert_eq(board.get_zone_cell_count(FortressBoard.ZONE_CAMARA_CENTRAL), 16, "Câmara Central has 16 cells")

	# Act & Assert - 4 Corner Towers: 4x4 = 16 cells each
	assert_eq(board.get_zone_cell_count(FortressBoard.ZONE_TORRE_NOROESTE), 16, "Torre NO has 16 cells")
	assert_eq(board.get_zone_cell_count(FortressBoard.ZONE_TORRE_NORDESTE), 16, "Torre NE has 16 cells")
	assert_eq(board.get_zone_cell_count(FortressBoard.ZONE_TORRE_SUDOESTE), 16, "Torre SO has 16 cells")
	assert_eq(board.get_zone_cell_count(FortressBoard.ZONE_TORRE_SUDESTE), 16, "Torre SE has 16 cells")

	# Act & Assert - 4 Perimeter Walls: 12x2 = 24 cells each
	assert_eq(board.get_zone_cell_count(FortressBoard.ZONE_MURALHA_NORTE), 24, "Muralha Norte has 24 cells")
	assert_eq(board.get_zone_cell_count(FortressBoard.ZONE_MURALHA_SUL), 24, "Muralha Sul has 24 cells")
	assert_eq(board.get_zone_cell_count(FortressBoard.ZONE_MURALHA_LESTE), 24, "Muralha Leste has 24 cells")
	assert_eq(board.get_zone_cell_count(FortressBoard.ZONE_MURALHA_OESTE), 24, "Muralha Oeste has 24 cells")

	# Act & Assert - 4 Outer Spawns: 12x2 = 24 cells each
	assert_eq(board.get_zone_cell_count(FortressBoard.ZONE_SPAWN_NORTE), 24, "Spawn Norte has 24 cells")
	assert_eq(board.get_zone_cell_count(FortressBoard.ZONE_SPAWN_SUL), 24, "Spawn Sul has 24 cells")
	assert_eq(board.get_zone_cell_count(FortressBoard.ZONE_SPAWN_LESTE), 24, "Spawn Leste has 24 cells")
	assert_eq(board.get_zone_cell_count(FortressBoard.ZONE_SPAWN_OESTE), 24, "Spawn Oeste has 24 cells")

	# Act & Assert - 3 Workshops + Courtyard: 32 cells each
	assert_eq(board.get_zone_cell_count(FortressBoard.ZONE_CARPINTARIA), 32, "Carpintaria has 32 cells")
	assert_eq(board.get_zone_cell_count(FortressBoard.ZONE_CURTUME), 32, "Curtume has 32 cells")
	assert_eq(board.get_zone_cell_count(FortressBoard.ZONE_FUNDICAO), 32, "Fundição has 32 cells")
	assert_eq(board.get_zone_cell_count(FortressBoard.ZONE_PATIO_CENTRAL), 32, "Pátio Central has 32 cells")

func test_get_cells_in_zone_returns_matching_cells() -> void:
	# Arrange
	var board: FortressBoard = FortressBoard.new()

	# Act
	var camara_cells: Array[Vector2i] = board.get_cells_in_zone(FortressBoard.ZONE_CAMARA_CENTRAL)

	# Assert
	assert_eq(camara_cells.size(), 16, "Câmara Central returns 16 cells")
	for cell in camara_cells:
		assert_eq(board.get_zone_at(cell), FortressBoard.ZONE_CAMARA_CENTRAL, "Cell (%d,%d) maps to Câmara" % [cell.x, cell.y])

# ── 3. Elevation Levels ───────────────────────────────────────────────────────

func test_elevation_levels_by_zone_type() -> void:
	# Arrange
	var board: FortressBoard = FortressBoard.new()

	# Act & Assert - Towers: Elevation 2
	for tower_id in FortressBoard.ALL_TOWERS:
		assert_eq(board.get_elevation(tower_id), 2, "Tower %s has elevation 2" % tower_id)

	# Act & Assert - Walls: Elevation 1
	for wall_id in FortressBoard.ALL_WALLS:
		assert_eq(board.get_elevation(wall_id), 1, "Wall %s has elevation 1" % wall_id)

	# Act & Assert - Ground level (Spawns, Workshops, Patio, Camara): Elevation 0
	for spawn_id in FortressBoard.ALL_SPAWNS:
		assert_eq(board.get_elevation(spawn_id), 0, "Spawn %s has elevation 0" % spawn_id)
	assert_eq(board.get_elevation(FortressBoard.ZONE_CAMARA_CENTRAL), 0, "Câmara has elevation 0")
	assert_eq(board.get_elevation(FortressBoard.ZONE_CARPINTARIA), 0, "Carpintaria has elevation 0")
	assert_eq(board.get_elevation(FortressBoard.ZONE_CURTUME), 0, "Curtume has elevation 0")
	assert_eq(board.get_elevation(FortressBoard.ZONE_FUNDICAO), 0, "Fundição has elevation 0")
	assert_eq(board.get_elevation(FortressBoard.ZONE_PATIO_CENTRAL), 0, "Pátio Central has elevation 0")

func test_elevation_at_coordinates() -> void:
	# Arrange
	var board: FortressBoard = FortressBoard.new()

	# Act & Assert
	assert_eq(board.get_elevation_at(Vector2i(0, 0)), 2, "Tower corner (0,0) elevation 2")
	assert_eq(board.get_elevation_at(Vector2i(5, 2)), 1, "Muralha Norte (5,2) elevation 1")
	assert_eq(board.get_elevation_at(Vector2i(10, 10)), 0, "Câmara Central (10,10) elevation 0")
	assert_eq(board.get_elevation_at(Vector2i(5, 0)), 0, "Spawn Norte (5,0) elevation 0")
	assert_eq(board.get_elevation_at(Vector2i(-1, -1)), 0, "Out of bounds elevation 0")

# ── 4. Adjacency Graph ────────────────────────────────────────────────────────

func test_adjacency_graph_symmetry() -> void:
	# Arrange
	var board: FortressBoard = FortressBoard.new()

	# Act & Assert - Every adjacency relation must be bidirectional
	for zone_id in FortressBoard.ALL_ZONES:
		var neighbors: Array[String] = board.get_adjacent_zones(zone_id)
		assert_gt(neighbors.size(), 0, "Zone '%s' must have at least one neighbor" % zone_id)
		for neighbor in neighbors:
			var reciprocal: Array[String] = board.get_adjacent_zones(neighbor)
			assert_has(reciprocal, zone_id, "Reciprocal adjacency: %s must contain %s" % [neighbor, zone_id])

func test_tower_adjacencies_connect_to_neighboring_walls_and_spawns() -> void:
	# Arrange
	var board: FortressBoard = FortressBoard.new()

	# Act
	var nw_adj: Array[String] = board.get_adjacent_zones(FortressBoard.ZONE_TORRE_NOROESTE)
	var ne_adj: Array[String] = board.get_adjacent_zones(FortressBoard.ZONE_TORRE_NORDESTE)
	var sw_adj: Array[String] = board.get_adjacent_zones(FortressBoard.ZONE_TORRE_SUDOESTE)
	var se_adj: Array[String] = board.get_adjacent_zones(FortressBoard.ZONE_TORRE_SUDESTE)

	# Assert - Northwest Tower connects to North/West Walls and Spawns
	assert_has(nw_adj, FortressBoard.ZONE_MURALHA_NORTE)
	assert_has(nw_adj, FortressBoard.ZONE_MURALHA_OESTE)
	assert_has(nw_adj, FortressBoard.ZONE_SPAWN_NORTE)
	assert_has(nw_adj, FortressBoard.ZONE_SPAWN_OESTE)

	# Assert - Northeast Tower connects to North/East Walls and Spawns
	assert_has(ne_adj, FortressBoard.ZONE_MURALHA_NORTE)
	assert_has(ne_adj, FortressBoard.ZONE_MURALHA_LESTE)
	assert_has(ne_adj, FortressBoard.ZONE_SPAWN_NORTE)
	assert_has(ne_adj, FortressBoard.ZONE_SPAWN_LESTE)

	# Assert - Southwest Tower connects to South/West Walls and Spawns
	assert_has(sw_adj, FortressBoard.ZONE_MURALHA_SUL)
	assert_has(sw_adj, FortressBoard.ZONE_MURALHA_OESTE)
	assert_has(sw_adj, FortressBoard.ZONE_SPAWN_SUL)
	assert_has(sw_adj, FortressBoard.ZONE_SPAWN_OESTE)

	# Assert - Southeast Tower connects to South/East Walls and Spawns
	assert_has(se_adj, FortressBoard.ZONE_MURALHA_SUL)
	assert_has(se_adj, FortressBoard.ZONE_MURALHA_LESTE)
	assert_has(se_adj, FortressBoard.ZONE_SPAWN_SUL)
	assert_has(se_adj, FortressBoard.ZONE_SPAWN_LESTE)

# ── 5. Invasion Pathway Graph ─────────────────────────────────────────────────

func test_invasion_pathway_from_all_spawns_to_camara_central() -> void:
	# Arrange
	var board: FortressBoard = FortressBoard.new()

	# Act & Assert - North Invasion Chain
	var n1: Array[String] = board.get_next_invasion_zones(FortressBoard.ZONE_SPAWN_NORTE)
	assert_eq(n1, [FortressBoard.ZONE_MURALHA_NORTE], "Spawn Norte -> Muralha Norte")
	var n2: Array[String] = board.get_next_invasion_zones(FortressBoard.ZONE_MURALHA_NORTE)
	assert_eq(n2, [FortressBoard.ZONE_CARPINTARIA], "Muralha Norte -> Carpintaria")
	var n3: Array[String] = board.get_next_invasion_zones(FortressBoard.ZONE_CARPINTARIA)
	assert_eq(n3, [FortressBoard.ZONE_CAMARA_CENTRAL], "Carpintaria -> Câmara Central")

	# Act & Assert - South Invasion Chain
	var s1: Array[String] = board.get_next_invasion_zones(FortressBoard.ZONE_SPAWN_SUL)
	assert_eq(s1, [FortressBoard.ZONE_MURALHA_SUL], "Spawn Sul -> Muralha Sul")
	var s2: Array[String] = board.get_next_invasion_zones(FortressBoard.ZONE_MURALHA_SUL)
	assert_eq(s2, [FortressBoard.ZONE_CURTUME], "Muralha Sul -> Curtume")
	var s3: Array[String] = board.get_next_invasion_zones(FortressBoard.ZONE_CURTUME)
	assert_eq(s3, [FortressBoard.ZONE_CAMARA_CENTRAL], "Curtume -> Câmara Central")

	# Act & Assert - West Invasion Chain
	var w1: Array[String] = board.get_next_invasion_zones(FortressBoard.ZONE_SPAWN_OESTE)
	assert_eq(w1, [FortressBoard.ZONE_MURALHA_OESTE], "Spawn Oeste -> Muralha Oeste")
	var w2: Array[String] = board.get_next_invasion_zones(FortressBoard.ZONE_MURALHA_OESTE)
	assert_eq(w2, [FortressBoard.ZONE_FUNDICAO], "Muralha Oeste -> Fundição")
	var w3: Array[String] = board.get_next_invasion_zones(FortressBoard.ZONE_FUNDICAO)
	assert_eq(w3, [FortressBoard.ZONE_CAMARA_CENTRAL], "Fundição -> Câmara Central")

	# Act & Assert - East Invasion Chain
	var e1: Array[String] = board.get_next_invasion_zones(FortressBoard.ZONE_SPAWN_LESTE)
	assert_eq(e1, [FortressBoard.ZONE_MURALHA_LESTE], "Spawn Leste -> Muralha Leste")
	var e2: Array[String] = board.get_next_invasion_zones(FortressBoard.ZONE_MURALHA_LESTE)
	assert_eq(e2, [FortressBoard.ZONE_PATIO_CENTRAL], "Muralha Leste -> Pátio Central")
	var e3: Array[String] = board.get_next_invasion_zones(FortressBoard.ZONE_PATIO_CENTRAL)
	assert_eq(e3, [FortressBoard.ZONE_CAMARA_CENTRAL], "Pátio Central -> Câmara Central")

	# Act & Assert - Câmara Central terminal: No next invasion zones
	var c_end: Array[String] = board.get_next_invasion_zones(FortressBoard.ZONE_CAMARA_CENTRAL)
	assert_eq(c_end.size(), 0, "Câmara Central is final objective; invasion complete")

# ── 6. Wall Integrity, Damage & Repair ────────────────────────────────────────

func test_wall_initial_hp_and_max_hp() -> void:
	# Arrange
	var board: FortressBoard = FortressBoard.new()

	# Act & Assert
	for wall_id in FortressBoard.ALL_WALLS:
		assert_eq(board.get_wall_hp(wall_id), 100, "Initial wall HP is 100")
		assert_eq(board.get_wall_max_hp(wall_id), 100, "Max wall HP is 100")
		assert_false(board.is_wall_breached(wall_id), "Initial wall is not breached")

func test_wall_damage_and_breach_detection() -> void:
	# Arrange
	var board: FortressBoard = FortressBoard.new()
	var wall: String = FortressBoard.ZONE_MURALHA_NORTE

	# Act 1: Partial damage
	var rem1: int = board.damage_wall(wall, 40)

	# Assert 1
	assert_eq(rem1, 60, "Remaining HP after 40 damage is 60")
	assert_eq(board.get_wall_hp(wall), 60, "Wall HP updated to 60")
	assert_false(board.is_wall_breached(wall), "Wall with 60 HP is not breached")

	# Act 2: Fatal damage causing breach
	var rem2: int = board.damage_wall(wall, 60)

	# Assert 2
	assert_eq(rem2, 0, "Remaining HP is 0")
	assert_true(board.is_wall_breached(wall), "Wall with 0 HP is breached")

	# Act 3: Overkill damage clamped at 0
	var rem3: int = board.damage_wall(wall, 50)
	assert_eq(rem3, 0, "Overkill damage clamped at 0")

func test_wall_repair_restores_hp_and_clears_breach() -> void:
	# Arrange
	var board: FortressBoard = FortressBoard.new()
	var wall: String = FortressBoard.ZONE_MURALHA_SUL
	board.damage_wall(wall, 100) # Breached
	assert_true(board.is_wall_breached(wall))

	# Act 1: Partial repair
	var rep1: int = board.repair_wall(wall, 35)

	# Assert 1
	assert_eq(rep1, 35, "Repaired to 35 HP")
	assert_eq(board.get_wall_hp(wall), 35)
	assert_false(board.is_wall_breached(wall), "Wall is no longer breached")

	# Act 2: Over-repair clamped at max HP (100)
	var rep2: int = board.repair_wall(wall, 200)
	assert_eq(rep2, 100, "HP clamped at max 100")
	assert_eq(board.get_wall_hp(wall), 100)

func test_wall_signals_fired_on_damage_repair_and_breach() -> void:
	# Arrange
	var board: FortressBoard = FortressBoard.new()
	var wall: String = FortressBoard.ZONE_MURALHA_OESTE
	watch_signals(board)

	# Act 1: Damage wall
	board.damage_wall(wall, 30)

	# Assert 1
	assert_signal_emitted_with_parameters(board, "wall_damaged", [wall, 30, 70])
	assert_signal_not_emitted(board, "wall_breached")

	# Act 2: Breach wall
	board.damage_wall(wall, 70)

	# Assert 2
	assert_signal_emitted(board, "wall_breached")

	# Act 3: Repair wall
	board.repair_wall(wall, 25)
	assert_signal_emitted_with_parameters(board, "wall_repaired", [wall, 25, 25])

# ── 7. Unit Tracking & Movement ───────────────────────────────────────────────

func test_place_unit_tracks_position_and_zone() -> void:
	# Arrange
	var board: FortressBoard = FortressBoard.new()
	var pos: Vector2i = Vector2i(10, 10) # Câmara Central

	# Act
	var ok: bool = board.place_unit("heroi_1", pos)

	# Assert
	assert_true(ok, "Unit successfully placed")
	assert_eq(board.get_unit_position("heroi_1"), pos, "Unit position matches")
	assert_eq(board.get_unit_zone("heroi_1"), FortressBoard.ZONE_CAMARA_CENTRAL, "Unit zone matches")
	assert_has(board.get_units_in_zone(FortressBoard.ZONE_CAMARA_CENTRAL), "heroi_1", "Zone unit list contains unit")
	assert_has(board.get_units_at_cell(pos), "heroi_1", "Cell unit list contains unit")

func test_move_unit_updates_position_and_zone_membership() -> void:
	# Arrange
	var board: FortressBoard = FortressBoard.new()
	var pos_start: Vector2i = Vector2i(10, 10) # Câmara Central
	var pos_dest: Vector2i = Vector2i(5, 2)   # Muralha Norte
	board.place_unit("heroi_1", pos_start)

	# Act
	var ok: bool = board.move_unit("heroi_1", pos_dest)

	# Assert
	assert_true(ok, "Unit successfully moved")
	assert_eq(board.get_unit_position("heroi_1"), pos_dest, "Unit at destination")
	assert_eq(board.get_unit_zone("heroi_1"), FortressBoard.ZONE_MURALHA_NORTE, "Unit in destination zone")
	assert_does_not_have(board.get_units_in_zone(FortressBoard.ZONE_CAMARA_CENTRAL), "heroi_1", "Unit left old zone")
	assert_has(board.get_units_in_zone(FortressBoard.ZONE_MURALHA_NORTE), "heroi_1", "Unit entered new zone")
	assert_does_not_have(board.get_units_at_cell(pos_start), "heroi_1", "Unit left old cell")
	assert_has(board.get_units_at_cell(pos_dest), "heroi_1", "Unit entered new cell")

func test_remove_unit_cleans_up_all_tracking() -> void:
	# Arrange
	var board: FortressBoard = FortressBoard.new()
	var pos: Vector2i = Vector2i(2, 2) # Torre Noroeste
	board.place_unit("sentinela", pos)
	assert_true(board.has_unit("sentinela"))

	# Act
	var ok: bool = board.remove_unit("sentinela")

	# Assert
	assert_true(ok, "Unit removed successfully")
	assert_false(board.has_unit("sentinela"), "Board no longer has unit")
	assert_eq(board.get_unit_position("sentinela"), Vector2i(-1, -1), "Position reset to (-1,-1)")
	assert_eq(board.get_unit_zone("sentinela"), "", "Zone reset to empty")
	assert_does_not_have(board.get_units_in_zone(FortressBoard.ZONE_TORRE_NOROESTE), "sentinela")

func test_invalid_unit_operations_fail_gracefully() -> void:
	# Arrange
	var board: FortressBoard = FortressBoard.new()

	# Act & Assert
	assert_false(board.place_unit("", Vector2i(5, 5)), "Empty unit id rejected")
	assert_false(board.place_unit("ghost", Vector2i(-1, 5)), "Negative coord rejected")
	assert_false(board.place_unit("ghost", Vector2i(25, 5)), "Out of bounds coord rejected")
	assert_false(board.move_unit("nonexistent_unit", Vector2i(5, 5)), "Moving unplaced unit returns false")
	assert_false(board.remove_unit("nonexistent_unit"), "Removing unplaced unit returns false")

func test_board_reset_restores_clean_state() -> void:
	# Arrange
	var board: FortressBoard = FortressBoard.new()
	board.place_unit("u1", Vector2i(5, 5))
	board.place_unit("u2", Vector2i(10, 10))
	board.damage_wall(FortressBoard.ZONE_MURALHA_NORTE, 80)

	# Act
	board.reset_board()

	# Assert
	assert_eq(board.get_all_units().size(), 0, "All units cleared")
	assert_eq(board.get_wall_hp(FortressBoard.ZONE_MURALHA_NORTE), 100, "Wall HP restored to 100")
	assert_false(board.is_wall_breached(FortressBoard.ZONE_MURALHA_NORTE), "Wall no longer breached")



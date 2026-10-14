# res://test/unit/test_tactical_grid.gd
extends GutTest

func before_each() -> void:
	pass

func after_each() -> void:
	pass

# ── 1. Grid Dimensions & Bounds ──────────────────────────────────────────────

func test_grid_dimensions_default_20x20() -> void:
	# Arrange
	var grid: TacticalGrid = TacticalGrid.new()
	
	# Act
	var w: int = grid.width
	var h: int = grid.height
	var cell_0_0: String = grid.get_cell_type(Vector2i(0, 0))
	var cell_19_19: String = grid.get_cell_type(Vector2i(19, 19))
	
	# Assert
	assert_eq(w, 20, "Default grid width must be 20")
	assert_eq(h, 20, "Default grid height must be 20")
	assert_eq(cell_0_0, TacticalGrid.TERRENO_NORMAL, "Initial cell (0,0) must be NORMAL")
	assert_eq(cell_19_19, TacticalGrid.TERRENO_NORMAL, "Initial cell (19,19) must be NORMAL")

func test_is_valid_cell_boundaries() -> void:
	# Arrange
	var grid: TacticalGrid = TacticalGrid.new()
	
	# Act & Assert
	assert_true(grid.is_valid_cell(Vector2i(0, 0)), "(0, 0) should be valid")
	assert_true(grid.is_valid_cell(Vector2i(19, 19)), "(19, 19) should be valid")
	assert_true(grid.is_valid_cell(Vector2i(10, 10)), "(10, 10) should be valid")
	assert_false(grid.is_valid_cell(Vector2i(-1, 0)), "(-1, 0) should be invalid")
	assert_false(grid.is_valid_cell(Vector2i(0, -1)), "(0, -1) should be invalid")
	assert_false(grid.is_valid_cell(Vector2i(20, 10)), "(20, 10) should be invalid")
	assert_false(grid.is_valid_cell(Vector2i(10, 20)), "(10, 20) should be invalid")
	assert_false(grid.is_valid_cell(Vector2i(99, 99)), "(99, 99) should be invalid")

func test_point_to_id_and_reverse_mapping() -> void:
	# Arrange
	var grid: TacticalGrid = TacticalGrid.new()
	var test_points: Array[Vector2i] = [Vector2i(0, 0), Vector2i(19, 19), Vector2i(5, 7), Vector2i(13, 11)]
	
	# Act & Assert
	assert_eq(grid.point_to_id(Vector2i(0, 0)), 0, "ID of (0,0) must be 0")
	assert_eq(grid.point_to_id(Vector2i(19, 19)), 399, "ID of (19,19) must be 399")
	for pt in test_points:
		var id: int = grid.point_to_id(pt)
		var reconstructed: Vector2i = grid.id_to_point(id)
		assert_eq(reconstructed, pt, "Bijective conversion must restore original point")

# ── 2. Border Walls & Limiters ───────────────────────────────────────────────

func test_add_border_walls_applies_perimeter_walls() -> void:
	# Arrange
	var grid: TacticalGrid = TacticalGrid.new()
	
	# Act
	grid.add_border_walls()
	
	# Assert
	assert_eq(grid.get_cell_type(Vector2i(0, 5)), TacticalGrid.TERRENO_PAREDE, "Left edge should be PAREDE")
	assert_eq(grid.get_cell_type(Vector2i(19, 5)), TacticalGrid.TERRENO_PAREDE, "Right edge should be PAREDE")
	assert_eq(grid.get_cell_type(Vector2i(5, 0)), TacticalGrid.TERRENO_PAREDE, "Top edge should be PAREDE")
	assert_eq(grid.get_cell_type(Vector2i(5, 19)), TacticalGrid.TERRENO_PAREDE, "Bottom edge should be PAREDE")
	assert_eq(grid.get_cell_type(Vector2i(10, 10)), TacticalGrid.TERRENO_NORMAL, "Center tile should remain NORMAL")

func test_border_walls_clear_occupants() -> void:
	# Arrange
	var grid: TacticalGrid = TacticalGrid.new()
	var unit: Dictionary = {"id": "guard_1"}
	grid.place_unit(unit, Vector2i(0, 5))
	assert_true(grid.is_cell_occupied(Vector2i(0, 5)), "Unit placed on edge before walls")
	
	# Act
	grid.add_border_walls()
	
	# Assert
	assert_false(grid.is_cell_occupied(Vector2i(0, 5)), "Unit should be cleared by border walls")
	assert_null(grid.get_unit_at(Vector2i(0, 5)), "Cell should have null unit")

# ── 3. Walkability & Movement Costs ──────────────────────────────────────────

func test_terrain_walkability_flags() -> void:
	# Arrange
	var grid: TacticalGrid = TacticalGrid.new()
	
	# Act
	grid.set_cell_type(Vector2i(1, 1), TacticalGrid.TERRENO_NORMAL)
	grid.set_cell_type(Vector2i(1, 2), TacticalGrid.TERRENO_DIFICIL)
	grid.set_cell_type(Vector2i(1, 3), TacticalGrid.TERRENO_FLORESTA)
	grid.set_cell_type(Vector2i(1, 4), TacticalGrid.TERRENO_GELO)
	grid.set_cell_type(Vector2i(1, 5), TacticalGrid.TERRENO_AGUA)
	grid.set_cell_type(Vector2i(1, 6), TacticalGrid.TERRENO_PAREDE)
	grid.set_cell_type(Vector2i(1, 7), TacticalGrid.TERRENO_ROCHA)
	grid.set_cell_type(Vector2i(1, 8), TacticalGrid.TERRENO_BARRIL)
	
	# Assert
	assert_true(grid.is_cell_walkable(Vector2i(1, 1)), "NORMAL must be walkable")
	assert_true(grid.is_cell_walkable(Vector2i(1, 2)), "DIFICIL must be walkable")
	assert_true(grid.is_cell_walkable(Vector2i(1, 3)), "FLORESTA must be walkable")
	assert_true(grid.is_cell_walkable(Vector2i(1, 4)), "GELO must be walkable")
	assert_true(grid.is_cell_walkable(Vector2i(1, 5)), "AGUA must be walkable")
	assert_false(grid.is_cell_walkable(Vector2i(1, 6)), "PAREDE must be impassable")
	assert_false(grid.is_cell_walkable(Vector2i(1, 7)), "ROCHA must be impassable")
	assert_false(grid.is_cell_walkable(Vector2i(1, 8)), "BARRIL must be impassable")
	assert_false(grid.is_cell_walkable(Vector2i(-5, -5)), "Out of bounds must be not walkable")

func test_terrain_cost_values() -> void:
	# Arrange
	var grid: TacticalGrid = TacticalGrid.new()
	grid.set_cell_type(Vector2i(2, 2), TacticalGrid.TERRENO_NORMAL)
	grid.set_cell_type(Vector2i(2, 3), TacticalGrid.TERRENO_DIFICIL)
	grid.set_cell_type(Vector2i(2, 4), TacticalGrid.TERRENO_PAREDE)
	
	# Act & Assert
	assert_eq(grid.get_terrain_cost(Vector2i(2, 2)), 1.0, "NORMAL cost should be 1.0")
	assert_eq(grid.get_terrain_cost(Vector2i(2, 3)), 2.0, "DIFICIL cost should be 2.0")
	assert_gt(grid.get_terrain_cost(Vector2i(2, 4)), 9000.0, "PAREDE cost should be impassable")
	assert_gt(grid.get_terrain_cost(Vector2i(-1, -1)), 9000.0, "Out of bounds cost should be impassable")

# ── 4. Destructible Structures ───────────────────────────────────────────────

func test_structure_hp_initialized_to_20() -> void:
	# Arrange
	var grid: TacticalGrid = TacticalGrid.new()
	
	# Act
	grid.set_cell_type(Vector2i(3, 3), TacticalGrid.TERRENO_FLORESTA)
	grid.set_cell_type(Vector2i(3, 4), TacticalGrid.TERRENO_ROCHA)
	grid.set_cell_type(Vector2i(3, 5), TacticalGrid.TERRENO_BARRIL)
	grid.set_cell_type(Vector2i(3, 6), TacticalGrid.TERRENO_NORMAL)
	
	# Assert
	assert_eq(grid.get_structure_hp(Vector2i(3, 3)), 20, "FLORESTA HP must be 20")
	assert_eq(grid.get_structure_hp(Vector2i(3, 4)), 20, "ROCHA HP must be 20")
	assert_eq(grid.get_structure_hp(Vector2i(3, 5)), 20, "BARRIL HP must be 20")
	assert_eq(grid.get_structure_hp(Vector2i(3, 6)), 0, "NORMAL HP must be 0")

func test_apply_structure_damage_partial() -> void:
	# Arrange
	var grid: TacticalGrid = TacticalGrid.new()
	grid.set_cell_type(Vector2i(4, 4), TacticalGrid.TERRENO_ROCHA)
	
	# Act
	var destroyed: bool = grid.apply_structure_damage(Vector2i(4, 4), 10)
	
	# Assert
	assert_false(destroyed, "Structure should survive 10 damage")
	assert_eq(grid.get_structure_hp(Vector2i(4, 4)), 10, "Structure HP should be 10")
	assert_eq(grid.get_cell_type(Vector2i(4, 4)), TacticalGrid.TERRENO_ROCHA, "Terrain should still be ROCHA")

func test_apply_structure_damage_destruction_transforms_to_dificil() -> void:
	# Arrange
	var grid: TacticalGrid = TacticalGrid.new()
	grid.set_cell_type(Vector2i(4, 4), TacticalGrid.TERRENO_ROCHA)
	
	# Act
	var destroyed: bool = grid.apply_structure_damage(Vector2i(4, 4), 25)
	
	# Assert
	assert_true(destroyed, "Structure should be destroyed by 25 damage")
	assert_eq(grid.get_structure_hp(Vector2i(4, 4)), 0, "Structure HP should be 0")
	assert_eq(grid.get_cell_type(Vector2i(4, 4)), TacticalGrid.TERRENO_DIFICIL, "Destroyed rock becomes DIFICIL")
	assert_true(grid.is_cell_walkable(Vector2i(4, 4)), "Cell should now be walkable")
	assert_eq(grid.get_terrain_cost(Vector2i(4, 4)), 2.0, "Cost should now be difficult terrain 2.0")

func test_structure_damage_signals_emitted() -> void:
	# Arrange
	var grid: TacticalGrid = TacticalGrid.new()
	grid.set_cell_type(Vector2i(5, 5), TacticalGrid.TERRENO_BARRIL)
	watch_signals(grid)
	
	# Act
	grid.apply_structure_damage(Vector2i(5, 5), 10)
	grid.apply_structure_damage(Vector2i(5, 5), 15)
	
	# Assert
	assert_signal_emitted(grid, "structure_damaged", "structure_damaged should be emitted")
	assert_signal_emitted(grid, "structure_destroyed", "structure_destroyed should be emitted")

# ── 5. Elemental Terrain Interactions & Hazards ──────────────────────────────

func test_elemental_fire_ignites_forest_to_fire() -> void:
	# Arrange
	var grid: TacticalGrid = TacticalGrid.new()
	grid.set_cell_type(Vector2i(6, 6), TacticalGrid.TERRENO_FLORESTA)
	
	# Act
	grid.apply_terrain_damage(Vector2i(6, 6), "fogo")
	
	# Assert
	assert_eq(grid.get_cell_type(Vector2i(6, 6)), TacticalGrid.TERRENO_FOGO, "Forest should ignite to FOGO")

func test_elemental_ice_freezes_water_to_ice() -> void:
	# Arrange
	var grid: TacticalGrid = TacticalGrid.new()
	grid.set_cell_type(Vector2i(6, 6), TacticalGrid.TERRENO_AGUA)
	
	# Act
	grid.apply_terrain_damage(Vector2i(6, 6), "gelo")
	
	# Assert
	assert_eq(grid.get_cell_type(Vector2i(6, 6)), TacticalGrid.TERRENO_GELO, "Water should freeze to GELO")

func test_elemental_fire_melts_ice_to_water() -> void:
	# Arrange
	var grid: TacticalGrid = TacticalGrid.new()
	grid.set_cell_type(Vector2i(6, 6), TacticalGrid.TERRENO_GELO)
	
	# Act
	grid.apply_terrain_damage(Vector2i(6, 6), "fire")
	
	# Assert
	assert_eq(grid.get_cell_type(Vector2i(6, 6)), TacticalGrid.TERRENO_AGUA, "Ice should melt to AGUA")

func test_elemental_ice_extinguishes_fire_to_normal() -> void:
	# Arrange
	var grid: TacticalGrid = TacticalGrid.new()
	grid.set_cell_type(Vector2i(6, 6), TacticalGrid.TERRENO_FOGO)
	
	# Act
	grid.apply_terrain_damage(Vector2i(6, 6), "ice")
	
	# Assert
	assert_eq(grid.get_cell_type(Vector2i(6, 6)), TacticalGrid.TERRENO_NORMAL, "Fire should be extinguished to NORMAL")

func test_hazard_triggers() -> void:
	# Arrange
	var grid: TacticalGrid = TacticalGrid.new()
	grid.set_cell_type(Vector2i(7, 7), TacticalGrid.TERRENO_GELO)
	grid.set_cell_type(Vector2i(7, 8), TacticalGrid.TERRENO_FOGO)
	grid.set_cell_type(Vector2i(7, 9), TacticalGrid.TERRENO_VENENO)
	var dummy_unit: Dictionary = {"id": "player"}
	watch_signals(grid)
	
	# Act
	var h_ice: Dictionary = grid.check_hazard(Vector2i(7, 7), dummy_unit)
	var h_fire: Dictionary = grid.check_hazard(Vector2i(7, 8), dummy_unit)
	var h_poison: Dictionary = grid.check_hazard(Vector2i(7, 9), dummy_unit)
	var h_none: Dictionary = grid.check_hazard(Vector2i(0, 0), dummy_unit)
	
	# Assert
	assert_eq(h_ice["type"], "slip", "Ice hazard triggers slip")
	assert_eq(h_fire["type"], "fire", "Fire hazard triggers fire")
	assert_eq(h_poison["type"], "poison", "Poison hazard triggers poison")
	assert_eq(h_none["type"], "none", "Normal terrain has no hazard")
	assert_signal_emitted(grid, "hazard_triggered", "hazard_triggered emitted")

# ── 6. Unit Occupancy ────────────────────────────────────────────────────────

func test_unit_occupancy_lifecycle() -> void:
	# Arrange
	var grid: TacticalGrid = TacticalGrid.new()
	var unit_a: Dictionary = {"id": "hero_a"}
	var unit_b: Dictionary = {"id": "hero_b"}
	grid.set_cell_type(Vector2i(2, 2), TacticalGrid.TERRENO_NORMAL)
	grid.set_cell_type(Vector2i(2, 3), TacticalGrid.TERRENO_PAREDE)
	
	# Act & Assert
	# Place on walkable
	assert_true(grid.place_unit(unit_a, Vector2i(2, 2)), "Placing unit on free walkable cell succeeds")
	assert_true(grid.is_cell_occupied(Vector2i(2, 2)), "Cell (2, 2) is occupied")
	assert_eq(grid.get_unit_at(Vector2i(2, 2))["id"], "hero_a", "Unit at (2,2) matches")
	
	# Place on wall fails
	assert_false(grid.place_unit(unit_b, Vector2i(2, 3)), "Placing unit on wall fails")
	
	# Place on occupied fails
	assert_false(grid.place_unit(unit_b, Vector2i(2, 2)), "Placing unit on occupied cell fails")
	
	# Move unit
	assert_true(grid.move_unit(Vector2i(2, 2), Vector2i(3, 2)), "Moving unit to empty cell succeeds")
	assert_false(grid.is_cell_occupied(Vector2i(2, 2)), "Old cell is now free")
	assert_true(grid.is_cell_occupied(Vector2i(3, 2)), "New cell is now occupied")
	
	# Remove unit
	var removed: Variant = grid.remove_unit(Vector2i(3, 2))
	assert_eq(removed["id"], "hero_a", "Removed unit matches hero_a")
	assert_false(grid.is_cell_occupied(Vector2i(3, 2)), "Cell is empty after removal")

# ── 7. Pathfinding ───────────────────────────────────────────────────────────

func test_find_path_straight_line() -> void:
	# Arrange
	var grid: TacticalGrid = TacticalGrid.new()
	
	# Act
	var path: Array[Vector2i] = grid.find_path(Vector2i(2, 2), Vector2i(2, 5))
	
	# Assert
	assert_eq(path.size(), 3, "Straight path 3 steps long")
	assert_eq(path[0], Vector2i(2, 3), "First step (2, 3)")
	assert_eq(path[1], Vector2i(2, 4), "Second step (2, 4)")
	assert_eq(path[2], Vector2i(2, 5), "Destination reached (2, 5)")

func test_find_path_diagonal_8_way() -> void:
	# Arrange
	var grid: TacticalGrid = TacticalGrid.new()
	
	# Act
	var path: Array[Vector2i] = grid.find_path(Vector2i(2, 2), Vector2i(4, 4))
	
	# Assert
	assert_eq(path.size(), 2, "Diagonal 8-way path takes 2 steps")
	assert_eq(path[0], Vector2i(3, 3), "Diagonal step (3, 3)")
	assert_eq(path[1], Vector2i(4, 4), "Destination (4, 4)")

func test_find_path_obstacle_detour() -> void:
	# Arrange
	var grid: TacticalGrid = TacticalGrid.new()
	grid.set_cell_type(Vector2i(2, 3), TacticalGrid.TERRENO_PAREDE)
	
	# Act
	var path: Array[Vector2i] = grid.find_path(Vector2i(2, 2), Vector2i(2, 4))
	
	# Assert
	assert_gt(path.size(), 0, "Path exists around wall")
	assert_does_not_have(path, Vector2i(2, 3), "Path avoids the wall tile (2, 3)")
	assert_eq(path[-1], Vector2i(2, 4), "Destination reached")

func test_find_path_unit_detour_when_not_ignored() -> void:
	# Arrange
	var grid: TacticalGrid = TacticalGrid.new()
	grid.place_unit({"id": "blocker"}, Vector2i(2, 3))
	
	# Act
	var path_avoiding: Array[Vector2i] = grid.find_path(Vector2i(2, 2), Vector2i(2, 4), false)
	var path_ignoring: Array[Vector2i] = grid.find_path(Vector2i(2, 2), Vector2i(2, 4), true)
	
	# Assert
	assert_does_not_have(path_avoiding, Vector2i(2, 3), "When ignore_units is false, path avoids blocker")
	assert_has(path_ignoring, Vector2i(2, 3), "When ignore_units is true, path can cross blocker")

func test_find_path_unreachable_returns_empty() -> void:
	# Arrange
	var grid: TacticalGrid = TacticalGrid.new()
	# Box in target with walls
	var target: Vector2i = Vector2i(5, 5)
	for dx in [-1, 0, 1]:
		for dy in [-1, 0, 1]:
			if dx != 0 or dy != 0:
				grid.set_cell_type(target + Vector2i(dx, dy), TacticalGrid.TERRENO_PAREDE)
	
	# Act
	var path: Array[Vector2i] = grid.find_path(Vector2i(0, 0), target)
	
	# Assert
	assert_eq(path.size(), 0, "Completely boxed in target returns empty path")

func test_find_path_max_movement_truncation() -> void:
	# Arrange
	var grid: TacticalGrid = TacticalGrid.new()
	for x in range(grid.width):
		if x != 1:
			grid.set_cell_type(Vector2i(x, 2), TacticalGrid.TERRENO_PAREDE)
			grid.set_cell_type(Vector2i(x, 3), TacticalGrid.TERRENO_PAREDE)
	grid.set_cell_type(Vector2i(1, 2), TacticalGrid.TERRENO_DIFICIL) # cost 2.0
	grid.set_cell_type(Vector2i(1, 3), TacticalGrid.TERRENO_DIFICIL) # cost 2.0
	grid.rebuild_astar()
	
	# Act
	# Movement limit 3.0: 1st step (2.0) fits, 2nd step (2.0+2.0=4.0) exceeds
	var path: Array[Vector2i] = grid.find_path(Vector2i(1, 1), Vector2i(1, 5), false, 3.0)


	
	# Assert
	assert_eq(path.size(), 1, "Only 1 difficult terrain step fits in 3.0 movement")
	assert_eq(path[0], Vector2i(1, 2), "First step completed")

func test_diagonal_corner_cutting_prevention() -> void:
	# Arrange
	var grid: TacticalGrid = TacticalGrid.new()
	# Walls at (1, 2) and (2, 1) create an impassable corner between (1, 1) and (2, 2)
	grid.set_cell_type(Vector2i(1, 2), TacticalGrid.TERRENO_PAREDE)
	grid.set_cell_type(Vector2i(2, 1), TacticalGrid.TERRENO_PAREDE)
	grid.allow_corner_cutting = false
	grid.rebuild_astar()
	
	# Act
	var path: Array[Vector2i] = grid.find_path(Vector2i(1, 1), Vector2i(2, 2))
	
	# Assert
	if path.size() > 0:
		assert_ne(path[0], Vector2i(2, 2), "Cannot cut corner directly from (1, 1) to (2, 2)")

# ── 8. Line of Sight (LoS) ───────────────────────────────────────────────────

func test_bresenham_line_generation() -> void:
	# Arrange
	var grid: TacticalGrid = TacticalGrid.new()
	
	# Act
	var line: Array[Vector2i] = grid.get_bresenham_line(Vector2i(1, 1), Vector2i(1, 4))
	
	# Assert
	assert_eq(line.size(), 3, "Line contains 3 intermediate/target points")
	assert_eq(line[0], Vector2i(1, 2), "Step 1")
	assert_eq(line[1], Vector2i(1, 3), "Step 2")
	assert_eq(line[2], Vector2i(1, 4), "Target point")

func test_line_of_sight_clear() -> void:
	# Arrange
	var grid: TacticalGrid = TacticalGrid.new()
	
	# Act & Assert
	assert_true(grid.has_line_of_sight(Vector2i(2, 2), Vector2i(2, 6)), "Orthogonal LoS is clear")
	assert_true(grid.has_line_of_sight(Vector2i(2, 2), Vector2i(6, 6)), "Diagonal LoS is clear")
	assert_true(grid.has_line_of_sight(Vector2i(2, 2), Vector2i(2, 2)), "Same cell LoS is true")

func test_line_of_sight_blocked_by_wall() -> void:
	# Arrange
	var grid: TacticalGrid = TacticalGrid.new()
	grid.set_cell_type(Vector2i(2, 4), TacticalGrid.TERRENO_PAREDE)
	
	# Act
	var los: bool = grid.has_line_of_sight(Vector2i(2, 2), Vector2i(2, 6))
	
	# Assert
	assert_false(los, "Wall at (2, 4) blocks LoS")

func test_line_of_sight_blocked_by_rock() -> void:
	# Arrange
	var grid: TacticalGrid = TacticalGrid.new()
	grid.set_cell_type(Vector2i(2, 4), TacticalGrid.TERRENO_ROCHA)
	
	# Act
	var los: bool = grid.has_line_of_sight(Vector2i(2, 2), Vector2i(2, 6))
	
	# Assert
	assert_false(los, "Rock obstacle at (2, 4) blocks LoS")

func test_line_of_sight_blocked_by_unit_when_not_ignored() -> void:
	# Arrange
	var grid: TacticalGrid = TacticalGrid.new()
	grid.place_unit({"id": "creature"}, Vector2i(2, 4))
	
	# Act
	var los_blocked: bool = grid.has_line_of_sight(Vector2i(2, 2), Vector2i(2, 6), false)
	var los_ignored: bool = grid.has_line_of_sight(Vector2i(2, 2), Vector2i(2, 6), true)
	
	# Assert
	assert_false(los_blocked, "Unit in LoS blocks vision when not ignored")
	assert_true(los_ignored, "Unit in LoS does not block vision when ignored")

# ── 9. Cover Calculations ────────────────────────────────────────────────────

func test_cover_adjacent_forest_grants_3_ac() -> void:
	# Arrange
	var grid: TacticalGrid = TacticalGrid.new()
	grid.set_cell_type(Vector2i(3, 2), TacticalGrid.TERRENO_FLORESTA)
	
	# Act
	var cover: int = grid.get_adjacent_cover_bonus(Vector2i(2, 2))
	
	# Assert
	assert_eq(cover, 3, "Adjacent forest grants +3 AC")

func test_cover_adjacent_rock_grants_5_ac() -> void:
	# Arrange
	var grid: TacticalGrid = TacticalGrid.new()
	grid.set_cell_type(Vector2i(3, 2), TacticalGrid.TERRENO_ROCHA)
	
	# Act
	var cover: int = grid.get_adjacent_cover_bonus(Vector2i(2, 2))
	
	# Assert
	assert_eq(cover, 5, "Adjacent rock grants +5 AC")

func test_cover_open_field_is_zero() -> void:
	# Arrange
	var grid: TacticalGrid = TacticalGrid.new()
	
	# Act
	var cover: int = grid.get_adjacent_cover_bonus(Vector2i(10, 10))
	
	# Assert
	assert_eq(cover, 0, "Open field provides 0 AC cover")

func test_cover_raycast_creature_soft_cover_2_ac() -> void:
	# Arrange
	var grid: TacticalGrid = TacticalGrid.new()
	grid.place_unit({"id": "human_shield"}, Vector2i(2, 4))
	
	# Act
	var cover: int = grid.get_raycast_cover(Vector2i(2, 2), Vector2i(2, 6))
	
	# Assert
	assert_eq(cover, 2, "Creature between attacker and target provides +2 soft cover")

func test_cover_raycast_wall_total_cover_1000() -> void:
	# Arrange
	var grid: TacticalGrid = TacticalGrid.new()
	grid.set_cell_type(Vector2i(2, 4), TacticalGrid.TERRENO_PAREDE)
	
	# Act
	var cover: int = grid.get_raycast_cover(Vector2i(2, 2), Vector2i(2, 6))
	
	# Assert
	assert_eq(cover, 1000, "Wall on LoS ray provides 1000 Total Cover")

func test_total_cover_bonus_calculation() -> void:
	# Arrange
	var grid: TacticalGrid = TacticalGrid.new()
	# Soft cover unit at (2, 4) (+2) and adjacent forest at (2, 7) for target at (2, 6) (+3)
	grid.place_unit({"id": "shield"}, Vector2i(2, 4))
	grid.set_cell_type(Vector2i(2, 7), TacticalGrid.TERRENO_FLORESTA)
	
	# Act
	var total: int = grid.get_total_cover_bonus(Vector2i(2, 2), Vector2i(2, 6))
	
	# Assert
	assert_eq(total, 3, "Total cover should take maximum of soft cover (2) and adjacent (3)")

# ── 10. Distance Metrics ─────────────────────────────────────────────────────

func test_distance_metrics() -> void:
	# Arrange
	var grid: TacticalGrid = TacticalGrid.new()
	var p1: Vector2i = Vector2i(1, 1)
	var p2: Vector2i = Vector2i(4, 5) # dx = 3, dy = 4
	
	# Act & Assert
	assert_eq(grid.calculate_chebyshev_distance(p1, p2), 4, "Chebyshev distance max(3, 4) = 4")
	assert_eq(grid.calculate_manhattan_distance(p1, p2), 7, "Manhattan distance 3 + 4 = 7")
	assert_almost_eq(grid.calculate_euclidean_distance(p1, p2), 5.0, 0.001, "Euclidean 3-4-5 triangle = 5.0")

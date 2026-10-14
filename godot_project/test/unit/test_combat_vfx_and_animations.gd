# res://test/unit/test_combat_vfx_and_animations.gd
extends GutTest

## Test suite for Combat VFX, Unit Animations, and Floating Combat Text in FortressBoardView.
## Strictly follows Senior Software Engineer AAA pattern, covering happy paths, edge cases, and errors.

func test_animate_unit_move_registers_position_and_returns_tween() -> void:
	# Arrange
	var board_view: FortressBoardView = autofree(FortressBoardView.new())
	var from_cell: Vector2i = Vector2i(5, 5)
	var to_cell: Vector2i = Vector2i(6, 5)
	var unit_id: String = "arqueiro_teste"

	# Act
	var tween: Tween = board_view.animate_unit_move(unit_id, from_cell, to_cell, 0.25)

	# Assert
	assert_true(board_view._unit_visual_positions.has(unit_id), "Visual positions queue must track unit being animated")
	var expected_start: Vector2 = board_view.get_cell_screen_coords(from_cell.x, from_cell.y)
	assert_eq(board_view._unit_visual_positions[unit_id], expected_start, "Start position should match from_cell coordinates")

func test_animate_melee_attack_sets_initial_zero_offset() -> void:
	# Arrange
	var board_view: FortressBoardView = autofree(FortressBoardView.new())
	var attacker_id: String = "guerreiro_teste"
	var target_cell: Vector2i = Vector2i(9, 10)

	# Act
	var tween: Tween = board_view.animate_melee_attack(attacker_id, target_cell, 0.28)

	# Assert
	assert_true(board_view._unit_anim_offsets.has(attacker_id), "Unit anim offsets queue must register attacking unit")
	assert_eq(board_view._unit_anim_offsets[attacker_id], Vector2.ZERO, "Offset must start at Vector2.ZERO before lunge step")

func test_launch_projectile_happy_path_and_parabolic_arc() -> void:
	# Arrange
	var board_view: FortressBoardView = autofree(FortressBoardView.new())
	var from_cell: Vector2i = Vector2i(2, 2)
	var to_cell: Vector2i = Vector2i(8, 8)
	var proj_type: String = "arrow"
	var color: Color = Color(1.0, 0.8, 0.1)

	# Act
	board_view.launch_projectile(from_cell, to_cell, proj_type, color, 0.35)

	# Assert
	assert_eq(board_view._active_projectiles.size(), 1, "One active projectile should be queued")
	var p: Dictionary = board_view._active_projectiles[0]
	assert_eq(p["type"], "arrow")
	assert_eq(p["progress"], 0.0)
	assert_eq(p["duration"], 0.35)
	assert_gt(p["arc_height"], 0.0, "Ballistic projectile must have non-zero arc height")
	assert_eq(p["start_pos"], board_view.get_cell_screen_coords(from_cell.x, from_cell.y))
	assert_eq(p["end_pos"], board_view.get_cell_screen_coords(to_cell.x, to_cell.y))

func test_launch_projectile_beam_zero_arc_height() -> void:
	# Arrange
	var board_view: FortressBoardView = autofree(FortressBoardView.new())
	var from_cell: Vector2i = Vector2i(4, 4)
	var to_cell: Vector2i = Vector2i(5, 5)

	# Act
	board_view.launch_projectile(from_cell, to_cell, "beam", Color.GREEN, 0.20)

	# Assert
	assert_eq(board_view._active_projectiles.size(), 1)
	var p: Dictionary = board_view._active_projectiles[0]
	assert_eq(p["type"], "beam")
	assert_eq(p["arc_height"], 0.0, "Energy or acid beam must have linear (0.0) arc height")

func test_trigger_unit_damage_flash_lifecycle_and_timer_progress() -> void:
	# Arrange
	var board_view: FortressBoardView = autofree(FortressBoardView.new())
	var unit_id: String = "inimigo_boss"
	var flash_col: Color = Color(1.0, 0.1, 0.1, 0.9)

	# Act
	board_view.trigger_unit_damage_flash(unit_id, flash_col, 0.22)

	# Assert
	assert_true(board_view._unit_anim_flashes.has(unit_id), "Flash queue must track unit")
	var f_data: Dictionary = board_view._unit_anim_flashes[unit_id]
	assert_almost_eq(float(f_data["timer"]), 0.22, 0.001)
	assert_eq(f_data["color"], flash_col)

	# Act - Simula avanço de tempo no _process
	board_view._process(0.10)
	assert_true(board_view._unit_anim_flashes.has(unit_id), "Flash still active at 0.10s elapsed")
	assert_almost_eq(float(board_view._unit_anim_flashes[unit_id]["timer"]), 0.12, 0.001)

	# Act - Simula expiração do timer
	board_view._process(0.15)

	# Assert
	assert_false(board_view._unit_anim_flashes.has(unit_id), "Flash must be cleaned up after duration expires")

func test_spawn_floating_combat_text_lifecycle_and_fade() -> void:
	# Arrange
	var board_view: FortressBoardView = autofree(FortressBoardView.new())
	var text: String = "-18 💥"
	var cell: Vector2i = Vector2i(9, 9)
	var color: Color = Color(1.0, 0.85, 0.2)

	# Act
	board_view.spawn_floating_combat_text(text, cell, color, true)

	# Assert
	assert_eq(board_view._floating_combat_texts.size(), 1, "Floating text should be queued")
	var ft: Dictionary = board_view._floating_combat_texts[0]
	assert_eq(ft["text"], text)
	assert_eq(ft["is_crit"], true)
	assert_eq(ft["color"], color)
	assert_lt(ft["velocity"].y, 0.0, "Velocity should ascend upwards (negative y)")

	# Act - Processa movimento para cima
	var initial_y: float = ft["pos"].y
	board_view._process(0.20)
	assert_lt(board_view._floating_combat_texts[0]["pos"].y, initial_y, "Combat text must float upwards")

	# Act - Simula expiração completa (1.0s)
	board_view._process(1.0)

	# Assert
	assert_eq(board_view._floating_combat_texts.size(), 0, "Floating text must be erased when expired")

func test_active_projectiles_progress_and_completion_in_process() -> void:
	# Arrange
	var board_view: FortressBoardView = autofree(FortressBoardView.new())
	board_view.launch_projectile(Vector2i(0, 0), Vector2i(3, 3), "arrow", Color.YELLOW, 0.20)

	# Act - Avança 50% da duração (0.10s de 0.20s)
	board_view._process(0.10)

	# Assert
	assert_eq(board_view._active_projectiles.size(), 1)
	assert_almost_eq(float(board_view._active_projectiles[0]["progress"]), 0.50, 0.02)

	# Act - Conclui o percurso (avança mais 0.15s)
	board_view._process(0.15)

	# Assert
	assert_eq(board_view._active_projectiles.size(), 0, "Finished projectiles must be removed from queue")

func test_vfx_edge_cases_empty_and_zero_duration() -> void:
	# Arrange
	var board_view: FortressBoardView = autofree(FortressBoardView.new())

	# Act & Assert - Processamento com filas vazias não quebra nem gera exceções
	board_view._process(0.016)
	assert_eq(board_view._active_projectiles.size(), 0)
	assert_eq(board_view._floating_combat_texts.size(), 0)
	assert_eq(board_view._unit_anim_flashes.size(), 0)

	# Act & Assert - Duração quase nula é segura contra divisão por zero
	board_view.launch_projectile(Vector2i(1, 1), Vector2i(2, 2), "arrow", Color.WHITE, 0.0)
	assert_gt(board_view._active_projectiles[0]["duration"], 0.0, "Duration must be clamped to safe minimum")
	board_view._process(0.1)
	assert_eq(board_view._active_projectiles.size(), 0)

# res://test/unit/test_board_textures_and_camera.gd
extends GutTest

## Test suite for FortressBoardView procedural & pixel art texture rendering and camera controls.
## Follows strict Arrange-Act-Assert (AAA) pattern per project guidelines.

# ── 1. Texture Loading & Zone Mapping Tests ────────────────────────────────────

func test_pine_tree_texture_asset_exists_and_loads() -> void:
	# Arrange
	var tree_path: String = "res://assets/images/environment/arvore_pinheiro.png"

	# Act
	var exists: bool = ResourceLoader.exists(tree_path) or FileAccess.file_exists(tree_path)
	var tex: Texture2D = load(tree_path) as Texture2D if exists else null

	# Assert
	assert_true(exists, "arvore_pinheiro.png must exist in assets/images/environment/")
	assert_not_null(tex, "arvore_pinheiro.png must load as valid Texture2D")
	if tex != null:
		assert_gt(tex.get_width(), 32, "Tree texture width must be > 32px")
		assert_gt(tex.get_height(), 32, "Tree texture height must be > 32px")

func test_all_canonical_zone_textures_load_properly() -> void:
	# Arrange
	var view: FortressBoardView = add_child_autofree(FortressBoardView.new())
	var zones_to_test: Array[String] = [
		"MURALHA_NORTE",
		"TORRE_NOROESTE",
		"CARPINTARIA",
		"CURTUME",
		"FUNDICAO",
		"CAMARA_CENTRAL",
		"PATIO_CENTRAL",
		"_campo",
		"SPAWN_NORTE"
	]

	# Act & Assert
	for zid in zones_to_test:
		var tex: Texture2D = view.get_zone_texture(zid)
		assert_not_null(tex, "Zone %s must resolve to a valid Texture2D" % zid)
		assert_gt(tex.get_width(), 0, "Texture for %s must have non-zero width" % zid)
		assert_gt(tex.get_height(), 0, "Texture for %s must have non-zero height" % zid)

func test_zone_texture_edge_cases_empty_and_unknown() -> void:
	# Arrange
	var view: FortressBoardView = add_child_autofree(FortressBoardView.new())

	# Act
	var empty_tex: Texture2D = view.get_zone_texture("")
	var unknown_tex: Texture2D = view.get_zone_texture("NON_EXISTENT_ZONE_XYZ_999")

	# Assert
	assert_null(empty_tex, "Empty zone string should return null safely without errors")
	assert_null(unknown_tex, "Unknown zone string should return null safely without errors")

func test_clear_terrain_textures_cleans_cache() -> void:
	# Arrange
	var view: FortressBoardView = add_child_autofree(FortressBoardView.new())
	var tex1: Texture2D = view.get_zone_texture("MURALHA_NORTE")
	assert_not_null(tex1, "Texture must be loaded into cache")

	# Act
	view.clear_terrain_textures()

	# Assert
	assert_eq(view._terrain_textures.size(), 0, "clear_terrain_textures() must empty the internal cache")
	var tex2: Texture2D = view.get_zone_texture("MURALHA_NORTE")
	assert_not_null(tex2, "Texture must be reloadable after clearing cache")

# ── 2. Camera Pan & Zoom Tests ────────────────────────────────────────────────

func test_camera_zoom_in_and_out_limits() -> void:
	# Arrange
	var view: FortressBoardView = add_child_autofree(FortressBoardView.new())
	view.size = Vector2(600, 600)

	# Act - Zoom In beyond max
	for _i in range(30):
		view._apply_zoom(view.cam_zoom + FortressBoardView.CAM_ZOOM_STEP, Vector2(300, 300))
	var max_zoom_reached: float = view.cam_zoom

	# Act - Zoom Out beyond min
	for _i in range(40):
		view._apply_zoom(view.cam_zoom - FortressBoardView.CAM_ZOOM_STEP, Vector2(300, 300))
	var min_zoom_reached: float = view.cam_zoom

	# Assert
	assert_almost_eq(max_zoom_reached, FortressBoardView.CAM_ZOOM_MAX, 0.001, "Zoom cannot exceed CAM_ZOOM_MAX")
	assert_almost_eq(min_zoom_reached, FortressBoardView.CAM_ZOOM_MIN, 0.001, "Zoom cannot go below CAM_ZOOM_MIN")

func test_camera_pan_to_unit_centers_view() -> void:
	# Arrange
	var view: FortressBoardView = add_child_autofree(FortressBoardView.new())
	view.size = Vector2(800, 600)
	var board: FortressBoard = FortressBoard.new()
	view.bind_board(board)
	board.place_unit("hero_1", Vector2i(10, 10))

	# Act
	view.pan_to_unit("hero_1")

	# Assert - camera pan was updated from Vector2.ZERO to frame the unit
	assert_ne(view.cam_pan, Vector2.ZERO, "pan_to_unit must adjust cam_pan to frame the unit")

func test_camera_reset_restores_clean_pan_and_zoom() -> void:
	# Arrange
	var view: FortressBoardView = add_child_autofree(FortressBoardView.new())
	view.cam_pan = Vector2(-120.0, 75.0)
	view.cam_zoom = 2.4

	# Act
	view.reset_camera()

	# Assert
	assert_eq(view.cam_pan, Vector2.ZERO, "reset_camera must reset pan to ZERO")
	assert_eq(view.cam_zoom, 1.0, "reset_camera must reset zoom to 1.0")

func test_screen_to_world_round_trip() -> void:
	# Arrange
	var view: FortressBoardView = add_child_autofree(FortressBoardView.new())
	view.cam_pan = Vector2(100.0, -50.0)
	view.cam_zoom = 1.5
	var original_world: Vector2 = Vector2(250.0, 180.0)

	# Act
	# screen = world * zoom + pan
	var screen: Vector2 = original_world * view.cam_zoom + view.cam_pan
	var recovered_world: Vector2 = view._screen_to_world(screen)

	# Assert
	assert_almost_eq(recovered_world.x, original_world.x, 0.01, "X coordinate must round-trip accurately")
	assert_almost_eq(recovered_world.y, original_world.y, 0.01, "Y coordinate must round-trip accurately")

# ── 3. Loot & Item Texture Tests ──────────────────────────────────────────────

func test_chest_and_gold_textures_exist_and_load() -> void:
	# Arrange
	var chest_path: String = "res://assets/images/material/bau_ouro.png"
	var gold_path: String = "res://assets/images/material/moedas_ouro.png"

	# Act
	var chest_exists: bool = ResourceLoader.exists(chest_path) or FileAccess.file_exists(chest_path)
	var gold_exists: bool = ResourceLoader.exists(gold_path) or FileAccess.file_exists(gold_path)
	var chest_tex: Texture2D = load(chest_path) as Texture2D if chest_exists else null
	var gold_tex: Texture2D = load(gold_path) as Texture2D if gold_exists else null

	# Assert
	assert_true(chest_exists, "bau_ouro.png must exist in assets/images/material/")
	assert_true(gold_exists, "moedas_ouro.png must exist in assets/images/material/")
	assert_not_null(chest_tex, "bau_ouro.png must load as valid Texture2D")
	assert_not_null(gold_tex, "moedas_ouro.png must load as valid Texture2D")

func test_draw_board_item_chest_and_gold_handles_safely() -> void:
	# Arrange
	var view: FortressBoardView = add_child_autofree(FortressBoardView.new())
	view.size = Vector2(800, 600)
	var board: FortressBoard = FortressBoard.new()
	view.bind_board(board)
	board.place_item(Vector2i(5, 5), FortressBoard.ITEM_CHEST, {"name": "Baú da Carpintaria"})
	board.place_item(Vector2i(6, 6), "OURO", {"name": "Pilha de Ouro", "amount": 100})

	# Act
	view.queue_redraw()

	# Assert
	assert_true(board.has_item_at(Vector2i(5, 5)), "Chest placed on board")
	assert_true(board.has_item_at(Vector2i(6, 6)), "Gold placed on board")

# ── 4. Final Fantasy Tactics 4-Way Camera & Occlusion Tests ───────────────────

func test_fft_camera_rotation_cycle_and_wrap_around() -> void:
	# Arrange
	var view: FortressBoardView = add_child_autofree(FortressBoardView.new())
	assert_eq(view.camera_angle_idx, 0, "Initial camera angle is 0 (0° NW)")

	# Act - Rotate Right: 0 -> 1 (90°) -> 2 (180°) -> 3 (270°) -> 0 (360° wrap)
	view.rotate_camera_right()
	assert_eq(view.camera_angle_idx, 1, "After 1st right rotation: angle 1")

	view.rotate_camera_right()
	assert_eq(view.camera_angle_idx, 2, "After 2nd right rotation: angle 2")

	view.rotate_camera_right()
	assert_eq(view.camera_angle_idx, 3, "After 3rd right rotation: angle 3")

	view.rotate_camera_right()
	assert_eq(view.camera_angle_idx, 0, "After 4th right rotation: wrap to 0")

	# Act - Rotate Left: 0 -> 3 (270°) -> 2 (180°) -> 1 (90°) -> 0
	view.rotate_camera_left()
	assert_eq(view.camera_angle_idx, 3, "After left rotation from 0: wrap to 3")

	view.rotate_camera_left()
	assert_eq(view.camera_angle_idx, 2, "After 2nd left rotation: angle 2")

func test_fft_rotated_coordinates_mapping() -> void:
	# Arrange
	var view: FortressBoardView = add_child_autofree(FortressBoardView.new())
	var test_d: Vector2 = Vector2(5.0, 3.0)

	# Act & Assert - 0°
	view.camera_angle_idx = 0
	assert_eq(view.get_rotated_dx_dy(test_d.x, test_d.y), Vector2(5.0, 3.0), "0° preserves (dx, dy)")

	# Act & Assert - 90°
	view.camera_angle_idx = 1
	assert_eq(view.get_rotated_dx_dy(test_d.x, test_d.y), Vector2(3.0, -5.0), "90° rotates to (dy, -dx)")

	# Act & Assert - 180°
	view.camera_angle_idx = 2
	assert_eq(view.get_rotated_dx_dy(test_d.x, test_d.y), Vector2(-5.0, -3.0), "180° rotates to (-dx, -dy)")

	# Act & Assert - 270°
	view.camera_angle_idx = 3
	assert_eq(view.get_rotated_dx_dy(test_d.x, test_d.y), Vector2(-3.0, 5.0), "270° rotates to (-dy, dx)")

func test_fft_camera_keyboard_q_and_e_input_triggers_rotation() -> void:
	# Arrange
	var view: FortressBoardView = add_child_autofree(FortressBoardView.new())
	view.camera_angle_idx = 0

	# Act - Press E (rotate right via gui_input)
	var ev_e: InputEventKey = InputEventKey.new()
	ev_e.pressed = true
	ev_e.keycode = KEY_E
	view._gui_input(ev_e)

	# Assert
	assert_eq(view.camera_angle_idx, 1, "KEY_E rotates camera right to angle 1")

	# Act - Press Q (rotate left via gui_input)
	var ev_q: InputEventKey = InputEventKey.new()
	ev_q.pressed = true
	ev_q.keycode = KEY_Q
	view._gui_input(ev_q)

	# Assert
	assert_eq(view.camera_angle_idx, 0, "KEY_Q rotates camera left back to angle 0")

func test_fft_camera_unhandled_input_q_e_and_r_triggers_rotation() -> void:
	# Arrange
	var view: FortressBoardView = add_child_autofree(FortressBoardView.new())
	view.camera_angle_idx = 0
	view.cam_zoom = 2.0

	# Act - Send KEY_E via _unhandled_input (rotate right: 0 -> 1)
	var ev_e: InputEventKey = InputEventKey.new()
	ev_e.pressed = true
	ev_e.keycode = KEY_E
	view._unhandled_input(ev_e)

	# Assert
	assert_eq(view.camera_angle_idx, 1, "_unhandled_input KEY_E must rotate camera right to angle 1")

	# Act - Send KEY_Q via _unhandled_input (rotate left: 1 -> 0)
	var ev_q: InputEventKey = InputEventKey.new()
	ev_q.pressed = true
	ev_q.keycode = KEY_Q
	view._unhandled_input(ev_q)

	# Assert
	assert_eq(view.camera_angle_idx, 0, "_unhandled_input KEY_Q must rotate camera left back to angle 0")

	# Act - Send KEY_R via _unhandled_input (reset zoom and pan)
	var ev_r: InputEventKey = InputEventKey.new()
	ev_r.pressed = true
	ev_r.keycode = KEY_R
	view._unhandled_input(ev_r)

	# Assert
	assert_eq(view.cam_zoom, 1.0, "_unhandled_input KEY_R must reset zoom to 1.0")

func test_fft_camera_unhandled_input_edge_cases_echo_and_released_events() -> void:
	# Arrange
	var view: FortressBoardView = add_child_autofree(FortressBoardView.new())
	view.camera_angle_idx = 0

	# Act - Echo event should be ignored
	var ev_echo: InputEventKey = InputEventKey.new()
	ev_echo.pressed = true
	ev_echo.echo = true
	ev_echo.keycode = KEY_E
	view._unhandled_input(ev_echo)

	# Assert
	assert_eq(view.camera_angle_idx, 0, "Echo key event must NOT change camera angle")

	# Act - Released event should be ignored
	var ev_released: InputEventKey = InputEventKey.new()
	ev_released.pressed = false
	ev_released.keycode = KEY_E
	view._unhandled_input(ev_released)

	# Assert
	assert_eq(view.camera_angle_idx, 0, "Key release event must NOT change camera angle")

func test_fft_camera_hud_touch_buttons_trigger_rotation() -> void:
	# Arrange
	var view: FortressBoardView = add_child_autofree(FortressBoardView.new())
	view.size = Vector2(800, 600)
	view.camera_angle_idx = 0

	# Act - Click on E ↻ button (top right: x = 800 - 40, y = 20)
	var click_e: InputEventMouseButton = InputEventMouseButton.new()
	click_e.button_index = MOUSE_BUTTON_LEFT
	click_e.pressed = true
	click_e.position = Vector2(760.0, 20.0)
	view._gui_input(click_e)

	# Assert
	assert_eq(view.camera_angle_idx, 1, "Clicking E button rotates camera right")

	# Act - Click on Q ↺ button (top right: x = 800 - 100, y = 20)
	var click_q: InputEventMouseButton = InputEventMouseButton.new()
	click_q.button_index = MOUSE_BUTTON_LEFT
	click_q.pressed = true
	click_q.position = Vector2(700.0, 20.0)
	view._gui_input(click_q)

	# Assert
	assert_eq(view.camera_angle_idx, 0, "Clicking Q button rotates camera left")

func test_intact_walls_block_movement_path_until_breached() -> void:
	# Arrange
	var board: FortressBoard = FortressBoard.new()
	var wall_pos: Vector2i = Vector2i(5, 2) # In ZONE_MURALHA_NORTE
	var is_walkable_init: bool = board.is_cell_walkable(wall_pos)

	# Assert initial wall blocks movement
	assert_false(is_walkable_init, "Intact wall at (5,2) must NOT be walkable")

	# Act - Damage wall to 0 (Breached)
	board.damage_wall(FortressBoard.ZONE_MURALHA_NORTE, 100)
	var is_walkable_after_breach: bool = board.is_cell_walkable(wall_pos)

	# Assert breached wall can now be crossed
	assert_true(board.is_wall_breached(FortressBoard.ZONE_MURALHA_NORTE), "Wall should be breached")
	assert_true(is_walkable_after_breach, "Breached wall must become walkable")




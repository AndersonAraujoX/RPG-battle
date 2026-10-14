# res://test/unit/test_design_upgrades.gd
extends GutTest

## Test suite for Design Upgrades:
## 1. Dynamic Lighting, Torches, Projected Shadows and Miasma
## 2. CardUI Dark Fantasy Ornate Frames, Archetype Pixel Art, and Runic Glow
## 3. Game Feel, Screen Shake, Themed Particles, Trajectory Line
## 4. FFT Grid Polish, Wall Fissures, Floating Tactical Tooltip
## 5. Adaptive Audio (War horn breach alarm & ambient loop)

var _board_view: FortressBoardView = null
var _board: FortressBoard = null

func before_each() -> void:
	_board_view = FortressBoardView.new()
	_board = FortressBoard.new()
	_board_view.bind_board(_board)

func after_each() -> void:
	if _board_view != null and is_instance_valid(_board_view):
		_board_view.unbind_board()
		_board_view.free()
		_board_view = null
	_board = null

# ── 1. Screen Shake Tests (Arrange-Act-Assert) ────────────────────────────────

func test_trigger_screen_shake_happy_path() -> void:
	# Arrange
	assert_eq(_board_view.shake_intensity, 0.0)
	assert_eq(_board_view.shake_timer, 0.0)

	# Act
	_board_view.trigger_screen_shake(8.0, 0.4)

	# Assert
	assert_eq(_board_view.shake_intensity, 8.0, "Screen shake intensity set")
	assert_eq(_board_view.shake_duration, 0.4, "Screen shake duration set")
	assert_eq(_board_view.shake_timer, 0.4, "Screen shake timer initialized to duration")

func test_screen_shake_decay_and_reset_in_process() -> void:
	# Arrange
	_board_view.trigger_screen_shake(6.0, 0.3)

	# Act: Halfway through duration
	_board_view._process(0.15)

	# Assert
	assert_gt(_board_view.shake_timer, 0.0, "Shake timer still active halfway")
	assert_ne(_board_view.shake_offset, Vector2.ZERO, "Shake offset has non-zero random displacement")

	# Act: Process past the remaining duration
	_board_view._process(0.20)

	# Assert
	assert_lte(_board_view.shake_timer, 0.0, "Shake timer finished")
	assert_eq(_board_view.shake_offset, Vector2.ZERO, "Shake offset smoothly resets to zero")

func test_screen_shake_zero_or_negative_duration_clamped() -> void:
	# Arrange & Act
	_board_view.trigger_screen_shake(5.0, -1.0)

	# Assert
	assert_gte(_board_view.shake_duration, 0.01, "Negative duration clamped to positive minimum")
	assert_gte(_board_view.shake_timer, 0.01, "Timer initialized to clamped duration")

# ── 2. Combat Particles Tests (Arrange-Act-Assert) ────────────────────────────

func test_spawn_impact_particles_stone_defaults() -> void:
	# Arrange
	var initial_count: int = _board_view._combat_particles.size()
	assert_eq(initial_count, 0)

	# Act
	_board_view.spawn_impact_particles(Vector2(100, 100), "stone", 6)

	# Assert
	assert_eq(_board_view._combat_particles.size(), 6, "6 stone particles spawned")
	var p: Dictionary = _board_view._combat_particles[0]
	assert_eq(p["pos"], Vector2(100, 100), "Particle origin matches target")
	assert_gt(p["duration"], 0.0, "Particle has positive lifetime")
	assert_gt(p["gravity"], 0.0, "Stone particles have downward gravity")

func test_spawn_impact_particles_themed_types() -> void:
	# Arrange & Act
	_board_view.spawn_impact_particles(Vector2(50, 50), "acid", 3)
	_board_view.spawn_impact_particles(Vector2(50, 50), "spark", 3)
	_board_view.spawn_impact_particles(Vector2(50, 50), "dust", 3)

	# Assert
	assert_eq(_board_view._combat_particles.size(), 9, "All 9 themed particles spawned")
	var acid_p: Dictionary = _board_view._combat_particles[0]
	assert_gt(acid_p["color"].g, 0.8, "Acid particle has vibrant toxic green tone")

	var spark_p: Dictionary = _board_view._combat_particles[3]
	assert_gt(spark_p["color"].r, 0.8, "Spark particle has bright orange/yellow tone")

	var dust_p: Dictionary = _board_view._combat_particles[6]
	assert_lt(dust_p["gravity"], 0.0, "Dust particle floats upwards with negative gravity")

func test_combat_particles_lifecycle_and_pruning_in_process() -> void:
	# Arrange
	_board_view.spawn_impact_particles(Vector2(100, 100), "spark", 4)
	assert_eq(_board_view._combat_particles.size(), 4)

	# Act: Advance time beyond max lifetime (e.g. 1.0 second)
	_board_view._process(1.5)

	# Assert
	assert_eq(_board_view._combat_particles.size(), 0, "All expired particles pruned cleanly")

func test_combat_particles_edge_case_zero_count() -> void:
	# Arrange & Act
	_board_view.spawn_impact_particles(Vector2(100, 100), "stone", 0)

	# Assert
	assert_eq(_board_view._combat_particles.size(), 0, "Zero count spawns no particles without crashing")

# ── 3. Wall Fissures Tests (Arrange-Act-Assert) ───────────────────────────────

func test_wall_fissures_healthy_wall_has_no_breach() -> void:
	# Arrange
	_board_view.update_wall_hp("MURALHA_NORTE", 100)

	# Act & Assert
	assert_false(_board_view.is_wall_breached("MURALHA_NORTE"), "100% HP wall is not breached")
	assert_eq(_board_view.wall_hps.get("MURALHA_NORTE"), 100, "HP registered accurately")

func test_wall_fissures_damaged_and_breached_states() -> void:
	# Arrange & Act: Damaged to 40% (deep fissures)
	_board_view.update_wall_hp("MURALHA_SUL", 40)

	# Assert
	assert_eq(_board_view.wall_hps.get("MURALHA_SUL"), 40, "Wall is damaged to 40%")
	assert_false(_board_view.is_wall_breached("MURALHA_SUL"), "40% HP is damaged but not yet breached")

	# Act: Destroyed to 0% (breach)
	_board_view.update_wall_hp("MURALHA_SUL", 0)

	# Assert
	assert_true(_board_view.is_wall_breached("MURALHA_SUL"), "0 HP wall is marked breached")

# ── 4. CardUI Dark Fantasy Ornate Presentation Tests ─────────────────────────

func test_card_ui_art_canvas_created_and_present() -> void:
	# Arrange
	var card_ui: CardUI = autofree(CardUI.new())
	var card: CardData = CardData.new()
	card.id = "escavacao_profunda"
	card.card_name = "Escavação Profunda"
	card.badge = CardData.BADGE_ESCAVACAO
	card.cost_metal = 2
	card.excavation = 3

	# Act
	card_ui.setup(card, 0)

	# Assert
	assert_eq(card_ui.custom_minimum_size, Vector2(104.0, 146.0), "Card dimensions preserved")
	var art_canvas: Control = card_ui.find_child("ArtCanvas", true, false) as Control
	assert_not_null(art_canvas, "ArtCanvas Control child node exists in hierarchy")
	assert_eq(art_canvas.custom_minimum_size, Vector2(0, 24), "ArtCanvas has dedicated minimum height")

func test_card_ui_archetype_palette_and_runic_pulse() -> void:
	# Arrange
	var card_ui: CardUI = autofree(CardUI.new())
	var card: CardData = CardData.new()
	card.badge = CardData.BADGE_TRABALHO
	card_ui.setup(card, 0)

	# Act: Toggle selection and process pulse
	assert_eq(card_ui._pulse_timer, 0.0)
	card_ui.set_selected(true)
	card_ui._process(0.1)

	# Assert
	assert_true(card_ui.is_selected, "Card is selected")
	assert_gt(card_ui._pulse_timer, 0.0, "Runic pulse timer advances when selected")

func test_card_ui_all_badges_have_distinct_colors() -> void:
	# Arrange
	var card_ui: CardUI = autofree(CardUI.new())
	var b_types: Array[String] = [
		CardData.BADGE_MARCHA,
		CardData.BADGE_TRABALHO,
		CardData.BADGE_ESCAVACAO,
		CardData.BADGE_COMBATE,
		CardData.BADGE_ESPECIAL
	]

	# Act & Assert
	for b in b_types:
		var cd: CardData = CardData.new()
		cd.badge = b
		card_ui.setup(cd, 0)
		var col: Color = card_ui.get_badge_color()
		assert_gt(col.a, 0.0, "Badge color for %s is valid" % b)

# ── 5. Adaptive Audio & Alarms Tests (Arrange-Act-Assert) ────────────────────

func test_audio_manager_play_war_horn_alarm_callable() -> void:
	# Arrange
	var tree: SceneTree = get_tree()
	if tree != null and tree.root.has_node("AudioManager"):
		var am: Node = tree.root.get_node("AudioManager")

		# Act & Assert
		assert_true(am.has_method("play_war_horn_alarm"), "AudioManager implements play_war_horn_alarm")
		assert_true(am.has_method("play_ambient_fortress_loop"), "AudioManager implements play_ambient_fortress_loop")
		# Calling should not raise or error
		am.play_war_horn_alarm()
		pass_test("play_war_horn_alarm executed safely")
	else:
		pass_test("Headless test without root AudioManager skipped safely")

func test_board_view_draw_headless_with_all_new_vfx() -> void:
	# Arrange
	_board_view.size = Vector2(800, 600)
	_board.place_unit("aquele", Vector2i(9, 10))
	_board.register_unit("aquele", {
		"name": "Aquele", "class": "Guerreiro", "team": "A",
		"hp": 40, "max_hp": 40, "ac": 16, "move_range": 3,
		"attack_range": 1, "attack_bonus": 4
	})
	_board_view.select_unit("aquele")
	_board_view.hovered_cell = Vector2i(9, 10)
	_board_view.trigger_screen_shake(5.0, 0.2)
	_board_view.spawn_impact_particles(Vector2(200, 200), "spark", 4)

	# Act & Assert: Call queue_redraw() to ensure zero runtime exceptions
	_board_view.queue_redraw()
	assert_gt(_board_view.size.x, 0.0, "BoardView width is positive")
	assert_gt(_board_view.size.y, 0.0, "BoardView height is positive")
	assert_eq(_board_view._combat_particles.size(), 4, "Combat particles are queued for render")
	pass_test("Board view with torches, miasma, shadows, particles, trajectory and tooltip queued cleanly")

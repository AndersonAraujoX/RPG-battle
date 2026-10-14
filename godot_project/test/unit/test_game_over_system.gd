# res://test/unit/test_game_over_system.gd
extends GutTest

## Test suite for GameOverModal, GameOverScene, and CercoGameController victory/defeat conditions.
## Follows strict Arrange-Act-Assert (AAA) pattern per project guidelines.

const GameOverModalScript = preload("res://scripts/ui/GameOverModal.gd")
const GameOverModalScene = preload("res://scenes/ui/GameOverModal.tscn")

# ── 1. GameOverModal Tests ───────────────────────────────────────────────────

func test_game_over_modal_setup_defeat_visuals_and_text() -> void:
	# Arrange
	var modal: Control = add_child_autofree(GameOverModalScene.instantiate())
	var test_stats: Dictionary = {
		"rounds_survived": 4,
		"enemies_defeated": 7,
		"cards_played": 12,
		"wood": 20,
		"leather": 15,
		"metal": 10,
		"crystals": 6
	}

	# Act
	modal.setup(false, "Todos os defensores tombaram em batalha!", test_stats)

	# Assert
	assert_false(modal.is_victory, "is_victory must be false for defeat")
	assert_eq(modal.victory_reason, "Todos os defensores tombaram em batalha!")
	assert_eq(modal.lbl_header.text, "💀 A FORTALEZA CAIU", "Defeat header must display skull title")
	assert_almost_eq(modal.lbl_header.modulate.r, 1.0, 0.05, "Defeat header must have red tint")

func test_game_over_modal_setup_victory_visuals_and_text() -> void:
	# Arrange
	var modal: Control = add_child_autofree(GameOverModalScene.instantiate())
	var test_stats: Dictionary = {
		"rounds_survived": 10,
		"enemies_defeated": 25,
		"cards_played": 30,
		"wood": 50,
		"leather": 40,
		"metal": 30,
		"crystals": 15
	}

	# Act
	modal.setup(true, "A Fortaleza resistiu a todas as ondas do cerco!", test_stats)

	# Assert
	assert_true(modal.is_victory, "is_victory must be true for victory")
	assert_eq(modal.lbl_header.text, "🏆 VITÓRIA TÁTICA!", "Victory header must display trophy title")
	assert_almost_eq(modal.lbl_header.modulate.g, 0.85, 0.05, "Victory header must have gold tint")

func test_game_over_modal_signals_restart_and_menu() -> void:
	# Arrange
	var modal: Control = add_child_autofree(GameOverModalScene.instantiate())
	watch_signals(modal)

	# Act - Press Restart
	modal._on_btn_restart_pressed()

	# Assert
	assert_signal_emitted(modal, "restart_requested", "restart_requested must emit on restart button press")

	# Act - Press Menu
	modal._on_btn_menu_pressed()

	# Assert
	assert_signal_emitted(modal, "menu_requested", "menu_requested must emit on menu button press")

func test_game_over_modal_unhandled_input_keyboard_shortcuts() -> void:
	# Arrange
	var modal: Control = add_child_autofree(GameOverModalScene.instantiate())
	watch_signals(modal)

	# Act - Press Space / Enter
	var ev_enter: InputEventKey = InputEventKey.new()
	ev_enter.pressed = true
	ev_enter.keycode = KEY_ENTER
	modal._unhandled_input(ev_enter)

	# Assert
	assert_signal_emitted(modal, "restart_requested", "Enter key must trigger restart_requested")

	# Act - Press ESC
	var ev_esc: InputEventKey = InputEventKey.new()
	ev_esc.pressed = true
	ev_esc.keycode = KEY_ESCAPE
	modal._unhandled_input(ev_esc)

	# Assert
	assert_signal_emitted(modal, "menu_requested", "Escape key must trigger menu_requested")

func test_game_over_modal_edge_cases_empty_strings_and_null_stats() -> void:
	# Arrange
	var modal: Control = add_child_autofree(GameOverModalScene.instantiate())

	# Act - Call setup with empty parameters
	modal.setup(false, "", {})

	# Assert - Default fallback subtitle applied safely
	assert_false(modal.lbl_subtitle.text.is_empty(), "Empty reason string should fall back to default message")
	assert_true(modal.lbl_stats.text.contains("Rodadas Resistidas"), "Stats label must render without crashing on empty dict")

# ── 2. CercoGameController Victory/Defeat Conditions Tests ────────────────────

func test_check_game_over_conditions_ongoing_game_returns_false() -> void:
	# Arrange
	var controller: CercoGameController = add_child_autofree(CercoGameController.new())

	# Act
	var result: Dictionary = controller.check_game_over_conditions()

	# Assert
	assert_false(bool(result.get("game_over", false)), "Active game with healthy heroes must NOT be game over")

func test_check_game_over_conditions_defeat_when_all_heroes_dead() -> void:
	# Arrange
	var controller: CercoGameController = add_child_autofree(CercoGameController.new())

	# Act - Kill all heroes
	for hid in controller.board.get_units_by_team("A"):
		controller.board.damage_unit(hid, 9999)

	var result: Dictionary = controller.check_game_over_conditions()

	# Assert
	assert_true(bool(result.get("game_over", false)), "Game must trigger game over when all heroes die")
	assert_false(bool(result.get("victory", true)), "Result must be defeat (victory = false)")
	assert_true(str(result.get("reason", "")).contains("heróis"), "Defeat reason must state heroes fell")

func test_check_game_over_conditions_defeat_when_central_chamber_invaded() -> void:
	# Arrange
	var controller: CercoGameController = add_child_autofree(CercoGameController.new())

	# Act - Place 3 live insect enemies in CAMARA_CENTRAL (center around (9, 9), (10, 9), (9, 10))
	var camara_cells: Array[Vector2i] = [Vector2i(9, 8), Vector2i(10, 8), Vector2i(8, 9)]
	for i in range(3):
		var bug_id: String = "test_invader_%d" % i
		controller.board.place_unit(bug_id, camara_cells[i])
		controller.board.register_unit(bug_id, {
			"name": "Invasor %d" % i, "team": "B", "hp": 20, "is_alive": true
		})

	var result: Dictionary = controller.check_game_over_conditions()

	# Assert
	assert_true(bool(result.get("game_over", false)), "Game must trigger defeat when 3+ insects reach CAMARA_CENTRAL")
	assert_false(bool(result.get("victory", true)), "Result must be defeat")
	assert_true(str(result.get("reason", "")).contains("Câmara Central"), "Reason must mention central chamber invasion")

func test_check_game_over_conditions_victory_when_survived_max_rounds() -> void:
	# Arrange
	var controller: CercoGameController = add_child_autofree(CercoGameController.new())
	controller.max_rounds = 5
	controller.current_round = 6

	# Remove any active enemy units to simulate cleared board
	for eid in controller.board.get_units_by_team("B"):
		controller.board.remove_unit(eid)

	# Act
	var result: Dictionary = controller.check_game_over_conditions()

	# Assert
	assert_true(bool(result.get("game_over", false)), "Exceeding max_rounds with no enemies triggers game over")
	assert_true(bool(result.get("victory", false)), "Result must be victory")
	assert_true(str(result.get("reason", "")).contains("resistiu"), "Reason must state fortress resisted")

func test_trigger_game_over_idempotent_and_instantiates_modal() -> void:
	# Arrange
	var controller: CercoGameController = add_child_autofree(CercoGameController.new())
	assert_false(controller.is_game_over, "Initial state is not game over")

	# Act - Trigger Game Over
	controller.trigger_game_over(false, "Derrota de teste")

	# Assert
	assert_true(controller.is_game_over, "is_game_over must be set to true")
	assert_not_null(controller.game_over_modal_instance, "GameOverModal must be instantiated")
	assert_true(controller.game_over_modal_instance.is_visible_in_tree() or controller.game_over_modal_instance.visible, "Modal must be shown")

	# Act - Second call should be a no-op (idempotent)
	var first_modal = controller.game_over_modal_instance
	controller.trigger_game_over(true, "Segunda chamada ignorada")
	assert_eq(controller.game_over_modal_instance, first_modal, "Repeated trigger_game_over calls must be idempotent")

func test_game_over_blocks_further_actions() -> void:
	# Arrange
	var controller: CercoGameController = add_child_autofree(CercoGameController.new())
	controller.trigger_game_over(false, "Bloqueio de ações")
	var initial_round: int = controller.current_round

	# Act - Attempt sync round requested
	controller._on_hud_sync_round_requested()

	# Assert
	assert_eq(controller.current_round, initial_round, "current_round must not change after game over")

# ── 3. GameOverScene Standalone Integration Tests ────────────────────────────

func test_game_over_standalone_scene_instantiates_cleanly() -> void:
	# Arrange
	var scene_res: PackedScene = load("res://scenes/main/GameOver.tscn")
	assert_not_null(scene_res, "GameOver.tscn must exist and load successfully")

	# Act
	var instance: Node = add_child_autofree(scene_res.instantiate())

	# Assert
	assert_not_null(instance, "GameOver scene must instantiate")
	var modal: Node = instance.get_node_or_null("GameOverModal")
	assert_not_null(modal, "GameOver scene must contain a GameOverModal child")

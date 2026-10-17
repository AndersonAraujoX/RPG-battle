# res://test/unit/test_pm_movement_and_audio_rules.gd
extends GutTest

## Test Suite for Movement Points (PM) Consumption, Infinite Move Prevention,
## and Audio Narrator Removal Verification.

var _timer: SceneTreeTimer = null

func before_all() -> void:
	# Watchdog timer to prevent infinite execution / hangs (RULE[prevencao_execucao_infinita])
	_timer = get_tree().create_timer(10.0)

func test_hero_registration_initializes_remaining_pm_equal_to_move_range() -> void:
	# Arrange
	var board: FortressBoard = FortressBoard.new()
	var unit_id: String = "guerreiro_teste"
	var hero_data: Dictionary = {
		"name": "Herói Teste",
		"team": "A",
		"hp": 30,
		"max_hp": 30,
		"ac": 15,
		"move_range": 4
	}

	# Act
	board.register_unit(unit_id, hero_data)
	var registered: Dictionary = board.get_unit_data(unit_id)
	var pm: int = board.get_unit_remaining_pm(unit_id)

	# Assert
	assert_eq(int(registered.get("remaining_pm", 0)), 4, "Remaining PM must be initialized to 4")
	assert_eq(pm, 4, "get_unit_remaining_pm must return 4")

func test_moving_hero_consumes_pm_and_prevents_infinite_movement() -> void:
	# Arrange
	var board: FortressBoard = FortressBoard.new()
	var board_view: FortressBoardView = autofree(FortressBoardView.new())
	board_view.bind_board(board)

	var hero_id: String = "heroi_caminhante"
	board.place_unit(hero_id, Vector2i(10, 10))
	board.register_unit(hero_id, {
		"name": "Caminhante",
		"team": "A",
		"hp": 20,
		"move_range": 3,
		"remaining_pm": 3
	})
	board_view.select_unit(hero_id)

	var initial_reachable: Array[Vector2i] = board_view.get_reachable_cells()
	assert_gt(initial_reachable.size(), 0, "Hero with 3 PM must have reachable cells")

	# Act 1 - Move 2 steps diagonally/adjacent to (10, 8)
	var dest: Vector2i = Vector2i(10, 8)
	var move_ok: bool = board_view.move_selected_unit_to(dest)

	# Assert 1
	assert_true(move_ok, "Move to valid reachable cell must succeed")
	assert_eq(board.get_unit_position(hero_id), dest, "Unit must have moved to dest")
	var rem_pm_1: int = board.get_unit_remaining_pm(hero_id)
	assert_eq(rem_pm_1, 1, "Remaining PM must be reduced from 3 to 1 (distance was 2)")

	# Act 2 - Move 1 step to (10, 7)
	var dest2: Vector2i = Vector2i(10, 7)
	var move_ok_2: bool = board_view.move_selected_unit_to(dest2)

	# Assert 2
	assert_true(move_ok_2, "Move using last PM must succeed")
	var rem_pm_2: int = board.get_unit_remaining_pm(hero_id)
	assert_eq(rem_pm_2, 0, "Remaining PM must now be 0")
	assert_eq(board_view.get_reachable_cells().size(), 0, "Reachable cells must be empty when PM is 0")

	# Act 3 - Attempt to move again with 0 PM (Infinite Move Prevention)
	var dest3: Vector2i = Vector2i(10, 6)
	var move_ok_3: bool = board_view.move_selected_unit_to(dest3)

	# Assert 3
	assert_false(move_ok_3, "Moving with 0 PM must be strictly rejected")
	assert_eq(board.get_unit_position(hero_id), dest2, "Unit must remain at dest2")

func test_moving_more_steps_than_remaining_pm_is_rejected() -> void:
	# Arrange
	var board: FortressBoard = FortressBoard.new()
	var board_view: FortressBoardView = autofree(FortressBoardView.new())
	board_view.bind_board(board)

	var hero_id: String = "heroi_passolongo"
	board.place_unit(hero_id, Vector2i(10, 10))
	board.register_unit(hero_id, {
		"name": "PassoLongo",
		"team": "A",
		"hp": 20,
		"move_range": 3,
		"remaining_pm": 1 # Apenas 1 PM restante
	})
	board_view.select_unit(hero_id)

	# Act - Tenta andar 3 células de distância tendo apenas 1 PM
	var far_dest: Vector2i = Vector2i(10, 7)
	var result: bool = board_view.move_selected_unit_to(far_dest)

	# Assert
	assert_false(result, "Moving beyond remaining PM must return false")
	assert_eq(board.get_unit_position(hero_id), Vector2i(10, 10), "Unit position must not change")
	assert_eq(board.get_unit_remaining_pm(hero_id), 1, "PM must remain untouched on rejected move")

func test_sync_round_restores_pm_for_all_living_allies() -> void:
	# Arrange
	var main_scene: PackedScene = load("res://scenes/main/Main.tscn")
	var controller: Node = autofree(main_scene.instantiate())
	var board: FortressBoard = controller.board

	# Gastar todos os PMs do paladino Stark
	var udata: Dictionary = board.get_unit_data("stark")
	udata["remaining_pm"] = 0
	board.set_unit_data("stark", udata)
	assert_eq(board.get_unit_remaining_pm("stark"), 0, "Stark must have 0 PM before sync round")

	# Act - Dispara a virada de rodada sincronizada
	controller._on_hud_sync_round_requested()

	# Assert
	var udata_restored: Dictionary = board.get_unit_data("stark")
	var restored_pm: int = int(udata_restored.get("remaining_pm", 0))
	var max_pm: int = int(udata_restored.get("move_range", 3))
	assert_eq(restored_pm, max_pm, "Sync round must restore remaining_pm to max move_range (%d)" % max_pm)

func test_marcha_card_increases_both_move_range_and_remaining_pm() -> void:
	# Arrange
	var main_scene: PackedScene = load("res://scenes/main/Main.tscn")
	var controller: Node = autofree(main_scene.instantiate())
	var board: FortressBoard = controller.board

	# Deixar herói com 1 PM restante
	var udata: Dictionary = board.get_unit_data("stark")
	udata["remaining_pm"] = 1
	board.set_unit_data("stark", udata)

	var marcha_card: CardData = CardData.new()
	marcha_card.id = "marcha_bonus_teste"
	marcha_card.badge = CardData.BADGE_MARCHA
	marcha_card.movement = 10 # +2 PM

	# Act
	controller._apply_card_effects(marcha_card, "")

	# Assert
	var udata_after: Dictionary = board.get_unit_data("stark")
	assert_eq(int(udata_after.get("remaining_pm", 0)), 3, "Marcha card (+2 PM) must increase remaining_pm from 1 to 3")
	assert_gte(int(udata_after.get("move_range", 0)), 5, "move_range must also increase")

func test_audio_manager_does_not_play_narrator_on_map_and_results() -> void:
	# Arrange
	var am: Node = autofree(load("res://scripts/autoload/AudioManager.gd").new())

	# Act & Assert 1 - Checar mapeamento de BGM
	assert_false(am.narrator_voice_enabled, "Narrator voice must be disabled by default")
	assert_eq(am.BGM_PATHS.get("mapa"), "res://assets/sounds/menu.ogg", "Map BGM must be menu.ogg, not intro.ogg")
	assert_eq(am.BGM_PATHS.get("campanha"), "res://assets/sounds/menu.ogg", "Campanha BGM must be menu.ogg")
	assert_eq(am.BGM_PATHS.get("vitoria"), "res://assets/sounds/menu.ogg", "Vitoria BGM must be menu.ogg")
	assert_eq(am.BGM_PATHS.get("derrota"), "res://assets/sounds/menu.ogg", "Derrota BGM must be menu.ogg")

	# Act & Assert 2 - Chamar play_bgm com "intro" toca o tema instrumental (menu.ogg) sem voz de narrador
	assert_eq(am.BGM_PATHS.get("intro"), "res://assets/sounds/menu.ogg", "Intro BGM path must point to menu.ogg (narrator removed)")
	am.play_bgm("intro", 0.0)
	assert_eq(am.get_current_bgm(), "intro", "Playing 'intro' tracks as 'intro' but plays instrumental audio")
	assert_true(am.is_bgm_playing(), "BGM should be active")

func test_dev_key_k_does_not_grant_infinite_movement() -> void:
	# Arrange
	var board: FortressBoard = FortressBoard.new()
	var board_view: FortressBoardView = autofree(FortressBoardView.new())
	board_view.bind_board(board)

	board.place_unit("heroi_k", Vector2i(5, 5))
	board.register_unit("heroi_k", {
		"name": "Heroi K",
		"team": "A",
		"hp": 20,
		"move_range": 3,
		"remaining_pm": 0 # PMs zerados
	})
	board_view.select_unit("heroi_k")
	assert_eq(board.get_unit_remaining_pm("heroi_k"), 0, "PM starts at 0")

	# Act - Pressiona a tecla 'k'
	var key_ev: InputEventKey = InputEventKey.new()
	key_ev.keycode = KEY_K
	key_ev.pressed = true
	board_view._unhandled_input(key_ev)
	board_view._gui_input(key_ev)

	# Assert - Garante que PM continua 0 e não houve trapaça de dev
	var current_pm: int = board.get_unit_remaining_pm("heroi_k")
	assert_eq(current_pm, 0, "Pressing KEY_K must NOT grant free PM or infinite movement")
	assert_eq(board_view.get_reachable_cells().size(), 0, "Reachable cells must remain empty")

func test_board_consume_and_restore_pm_edge_cases() -> void:
	# Arrange
	var board: FortressBoard = FortressBoard.new()

	# Act & Assert 1 - Unidade inexistente
	assert_eq(board.get_unit_remaining_pm("nao_existe"), 0, "Nonexistent unit has 0 PM")
	assert_eq(board.consume_unit_pm("nao_existe", 5), 0, "Consuming PM on nonexistent unit returns 0")

	# Act & Assert 2 - Unidade morta não deve receber restauração
	board.place_unit("defunto", Vector2i(1, 1))
	board.register_unit("defunto", {
		"name": "Defunto", "team": "A", "hp": 0, "move_range": 3, "remaining_pm": 0
	})
	board.restore_units_pm("A")
	assert_eq(board.get_unit_remaining_pm("defunto"), 0, "Dead unit must not have PM restored")

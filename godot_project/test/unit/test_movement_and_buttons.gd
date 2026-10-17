# res://test/unit/test_movement_and_buttons.gd
extends GutTest

## Suíte de testes unitários para resolução dos bugs de botões e seleção de movimento do personagem
## Segue estritamente o padrão Arrange-Act-Assert (AAA), SOLID e segurança de execução hermética.

const HUD_SCENE: PackedScene = preload("res://scenes/ui/HUD.tscn")
const MAP_SCENE: PackedScene = preload("res://scenes/run/RunMapScreen.tscn")

var _hud: HUD
var _map_screen: RunMapScreen
var _run_state: RunState
var _rng: RandomNumberGenerator

func before_each() -> void:
	RunSession.clear()
	RunCombatBridge.clear()
	_rng = RandomNumberGenerator.new()
	_rng.seed = 42

func after_each() -> void:
	if _hud != null:
		_hud.queue_free()
		_hud = null
	if _map_screen != null:
		_map_screen.queue_free()
		_map_screen = null
	if _run_state != null:
		_run_state = null
	RunSession.clear()
	RunCombatBridge.clear()

# ── 1. HUD & Action Buttons Dynamic State Tests ──────────────────────────────

func test_hud_update_active_hero_tracks_remaining_pm_dynamically() -> void:
	# Arrange
	_hud = autofree(HUD_SCENE.instantiate()) as HUD
	var hero_data: Dictionary = {
		"name": "Stark",
		"hp": 45,
		"max_hp": 52,
		"attack_bonus": 4,
		"ac": 18,
		"move_range": 3,
		"remaining_pm": 2
	}

	# Act
	_hud.update_active_hero(hero_data)

	# Assert
	assert_true(_hud.hero_stats.text.contains("[PM] 2"), "hero_stats deve refletir remaining_pm (2) e não o move_range base")
	assert_true(_hud.btn_move.text.contains("Mover [2 PM]"), "Botão Mover deve exibir [2 PM]")

func test_hud_action_buttons_state_when_zero_pm() -> void:
	# Arrange
	_hud = autofree(HUD_SCENE.instantiate()) as HUD
	var hero_data: Dictionary = {
		"name": "Elden",
		"hp": 26,
		"max_hp": 26,
		"attack_bonus": 5,
		"ac": 12,
		"move_range": 3,
		"remaining_pm": 0
	}

	# Act
	_hud.update_active_hero(hero_data)

	# Assert
	assert_true(_hud.hero_stats.text.contains("[PM] 0"), "hero_stats deve exibir [PM] 0")
	assert_true(_hud.btn_move.text.contains("Mover [0 PM]"), "Botão Mover deve exibir [0 PM]")

func test_hud_btn_move_pressed_activates_movement_on_board_view() -> void:
	# Arrange
	_hud = autofree(HUD_SCENE.instantiate()) as HUD
	var board: FortressBoard = FortressBoard.new()
	board.place_unit("Stark", Vector2i(9, 9))
	board.set_unit_data("Stark", {
		"name": "Stark",
		"team": "A",
		"hp": 50,
		"max_hp": 50,
		"move_range": 3,
		"remaining_pm": 3
	})
	_hud.bind_board(board)
	_hud.board_view.select_unit("Stark")

	# Act
	_hud._on_btn_move_pressed()

	# Assert
	assert_eq(_hud.board_view.selected_unit_id, "Stark")
	assert_false(_hud.board_view.reachable_cells.is_empty(), "Células azuis de movimento devem ser populadas")

func test_hud_btn_attack_pressed_identifies_attackable_cells() -> void:
	# Arrange
	_hud = autofree(HUD_SCENE.instantiate()) as HUD
	var board: FortressBoard = FortressBoard.new()
	board.place_unit("Stark", Vector2i(9, 9))
	board.set_unit_data("Stark", {
		"name": "Stark",
		"team": "A",
		"hp": 50,
		"max_hp": 50,
		"attack_range": 1,
		"remaining_pm": 3
	})
	board.place_unit("Invasor", Vector2i(9, 10))
	board.set_unit_data("Invasor", {
		"name": "Invasor",
		"team": "B",
		"hp": 20,
		"max_hp": 20
	})
	_hud.bind_board(board)
	_hud.board_view.select_unit("Stark")

	# Act
	_hud._on_btn_attack_pressed()

	# Assert
	assert_true(_hud.board_view.attackable_cells.has(Vector2i(9, 10)), "Inimigo adjacente deve estar em attackable_cells")

# ── 2. Roguelike Map Screen Node Selection Tests ──────────────────────────────

func test_map_screen_scroll_preserved_on_subsequent_node_selection() -> void:
	# Arrange
	_map_screen = autofree(MAP_SCENE.instantiate()) as RunMapScreen
	var gen: RunMapGenerator = RunMapGenerator.new(7, 3, 3)
	_run_state = RunState.new(gen, _rng)
	_run_state.start_run({"aquele": 30, "stark": 34, "elden": 26}, ["ataque"], 123)
	
	# Simula que o jogador já avançou além do início
	_run_state.current_node_id = 1
	_map_screen.setup(_run_state, RunNodeResolver.new(), _rng)
	_map_screen._ready()

	var scroll: ScrollContainer = _map_screen.get_node_or_null("Scroll") as ScrollContainer
	if scroll != null:
		scroll.scroll_vertical = 250

	# Act
	_map_screen._rebuild_map_nodes()

	# Assert
	if scroll != null:
		assert_ne(scroll.scroll_vertical, int(540.0), "Scroll não deve ser resetado para a base quando a run já começou")

func test_board_view_misclick_retains_selected_unit() -> void:
	# Arrange
	var board_view: FortressBoardView = autofree(FortressBoardView.new())
	var board: FortressBoard = FortressBoard.new()
	board.place_unit("Guerreiro", Vector2i(5, 5))
	board.set_unit_data("Guerreiro", {
		"team": "A",
		"hp": 30,
		"remaining_pm": 2,
		"move_range": 2
	})
	board_view.bind_board(board)
	board_view.select_unit("Guerreiro")

	# Simula clique esquerdo fora do alcance
	var event: InputEventMouseButton = InputEventMouseButton.new()
	event.button_index = MOUSE_BUTTON_LEFT
	event.pressed = true
	event.position = Vector2(10, 10) # Coordenada distante / fora de alcance

	# Act
	board_view._gui_input(event)

	# Assert
	assert_eq(board_view.selected_unit_id, "Guerreiro", "Herói deve permanecer selecionado mesmo após clique fora de alcance")

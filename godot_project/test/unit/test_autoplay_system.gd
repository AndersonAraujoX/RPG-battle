# res://test/unit/test_autoplay_system.gd
extends GutTest

## Suíte de testes unitários do Sistema de Auto-Play (HUD, Combate Tático e Mapa Roguelike)
## Segue estritamente o padrão Arrange-Act-Assert (AAA), SOLID e segurança de execução.

const HUD_SCENE: PackedScene = preload("res://scenes/ui/HUD.tscn")
const MAP_SCENE: PackedScene = preload("res://scenes/run/RunMapScreen.tscn")

var _controller: CercoGameController
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
	if _controller != null:
		_controller.queue_free()
		_controller = null
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

# ── 1. HUD AutoPlay Button & Signal Tests ────────────────────────────────────

func test_hud_autoplay_button_and_signal_toggle() -> void:
	# Arrange
	_hud = autofree(HUD_SCENE.instantiate()) as HUD
	assert_not_null(_hud.btn_autoplay, "Botão BtnAutoPlay deve existir no HUD")
	watch_signals(_hud)

	# Act 1: Primeiro clique ativa o AutoPlay
	_hud._on_btn_autoplay_pressed()

	# Assert 1
	assert_signal_emitted_with_parameters(_hud, "autoplay_toggled", [true])
	assert_true(_hud.autoplay_active, "autoplay_active deve ser true")
	assert_true(_hud.btn_autoplay.text.contains("AUTO [ON]"), "Texto do botão deve refletir estado ativo")

	# Act 2: Segundo clique desativa o AutoPlay
	_hud._on_btn_autoplay_pressed()

	# Assert 2
	assert_signal_emitted_with_parameters(_hud, "autoplay_toggled", [false])
	assert_false(_hud.autoplay_active, "autoplay_active deve ser false")
	assert_true(_hud.btn_autoplay.text.contains("AutoPlay [F5]"), "Texto do botão deve reverter para padrão")

func test_hud_set_autoplay_active_idempotency_and_null_safety() -> void:
	# Arrange
	_hud = autofree(HUD_SCENE.instantiate()) as HUD

	# Act & Assert
	_hud.set_autoplay_active(true)
	assert_true(_hud.autoplay_active)
	_hud.set_autoplay_active(false)
	assert_false(_hud.autoplay_active)

	# Teste de segurança com botão nulo
	var bare_hud: HUD = autofree(HUD.new())
	bare_hud.set_autoplay_active(true)
	assert_true(bare_hud.autoplay_active, "Deve executar com segurança mesmo sem nós da cena instanciados")

# ── 2. CercoGameController Combat Auto-Play Tests ────────────────────────────

func test_controller_autoplay_toggle() -> void:
	# Arrange
	_controller = autofree(CercoGameController.new())
	_controller._ready()

	# Act 1: Ativa autoplay
	var state1: bool = _controller.toggle_autoplay()

	# Assert 1
	assert_true(state1, "toggle_autoplay deve retornar true")
	assert_true(_controller.autoplay_enabled, "autoplay_enabled deve ser true")

	# Act 2: Desativa autoplay
	var state2: bool = _controller.toggle_autoplay()

	# Assert 2
	assert_false(state2, "toggle_autoplay deve retornar false")
	assert_false(_controller.autoplay_enabled, "autoplay_enabled deve ser false")

func test_controller_autoplay_synchronous_turn_attacks_adjacent_enemy() -> void:
	# Arrange: Configura herói e inimigo adjacente
	_controller = autofree(CercoGameController.new())
	_controller._ready()
	_controller.board.clear_all()
	_controller.board.place_unit("Guerreiro", Vector2i(9, 9))
	_controller.board.set_unit_data("Guerreiro", {
		"team": "A", "hp": 30, "max_hp": 30, "attack_range": 1, "remaining_pm": 3, "move_range": 3, "attack_bonus": 5
	})
	_controller.board.place_unit("Invasor", Vector2i(9, 10))
	_controller.board.set_unit_data("Invasor", {
		"team": "B", "hp": 20, "max_hp": 20, "ac": 10
	})

	# Act: Executa rodada de autoplay de forma síncrona
	var summary: Dictionary = _controller.execute_autoplay_turn_synchronous()

	# Assert: O herói atacou o inimigo adjacente e a rodada avançou
	assert_gt(summary.get("attacks_made", 0), 0, "Herói deve ter atacado o inimigo no alcance")
	assert_true(summary.get("round_advanced", false), "A rodada deve ter sido avançada")

func test_controller_autoplay_synchronous_moves_towards_distant_enemy() -> void:
	# Arrange: Herói distante do inimigo
	_controller = autofree(CercoGameController.new())
	_controller._ready()
	_controller.board.clear_all()
	var start_pos: Vector2i = Vector2i(4, 4)
	var enemy_pos: Vector2i = Vector2i(14, 14)
	_controller.board.place_unit("Guerreiro", start_pos)
	_controller.board.set_unit_data("Guerreiro", {
		"team": "A", "hp": 30, "max_hp": 30, "attack_range": 1, "remaining_pm": 3, "move_range": 3, "attack_bonus": 5
	})
	_controller.board.place_unit("Invasor", enemy_pos)
	_controller.board.set_unit_data("Invasor", {
		"team": "B", "hp": 20, "max_hp": 20, "ac": 12
	})

	# Act
	var summary: Dictionary = _controller.execute_autoplay_turn_synchronous()

	# Assert: O herói deve ter se movimentado em direção ao inimigo
	assert_gt(summary.get("units_moved", 0), 0, "Herói deve ter se movido em direção ao inimigo")
	var new_pos: Vector2i = _controller.board.get_unit_position("Guerreiro")
	var initial_dist: int = maxi(absi(start_pos.x - enemy_pos.x), absi(start_pos.y - enemy_pos.y))
	var new_dist: int = maxi(absi(new_pos.x - enemy_pos.x), absi(new_pos.y - enemy_pos.y))
	assert_lt(new_dist, initial_dist, "Nova distância (%d) deve ser menor que inicial (%d)" % [new_dist, initial_dist])

func test_controller_autoplay_synchronous_plays_viable_cards() -> void:
	# Arrange: Configura recursos e carta na mão
	_controller = autofree(CercoGameController.new())
	_controller._ready()
	_controller.economy.set_resource("wood", 10)
	_controller.economy.set_resource("metal", 10)
	_controller.economy.set_resource("crystal", 10)

	var test_card: CardData = CardData.new()
	test_card.id = "card_teste_auto"
	test_card.card_name = "Ataque Rápido"
	test_card.card_type = CardData.TYPE_ACAO
	test_card.cost_wood = 1
	_controller.deck.hand.clear()
	_controller.deck.hand.append(test_card)

	# Act
	var summary: Dictionary = _controller.execute_autoplay_turn_synchronous()

	# Assert
	assert_gt(summary.get("cards_played", 0), 0, "Deve jogar cartas viáveis da mão automaticamente")

func test_controller_autoplay_respects_game_over() -> void:
	# Arrange
	_controller = autofree(CercoGameController.new())
	_controller._ready()
	_controller.is_game_over = true

	# Act
	var summary: Dictionary = _controller.execute_autoplay_turn_synchronous()

	# Assert
	assert_eq(summary.get("attacks_made", 0), 0)
	assert_eq(summary.get("units_moved", 0), 0)
	assert_false(summary.get("round_advanced", false), "Não deve avançar turno se jogo acabou")

# ── 3. RunMapScreen Roguelike Map Auto-Play Tests ─────────────────────────────

func test_map_screen_autoplay_button_and_toggle() -> void:
	# Arrange
	_map_screen = autofree(MAP_SCENE.instantiate()) as RunMapScreen
	assert_not_null(_map_screen.btn_autoplay, "Botão BtnAutoPlay deve existir em RunMapScreen.tscn")

	var gen: RunMapGenerator = RunMapGenerator.new(7, 3, 3)
	_run_state = RunState.new(gen, _rng)
	_run_state.start_run({"aquele": 30, "stark": 34, "elden": 26}, ["ataque"], 123)
	_map_screen.setup(_run_state, RunNodeResolver.new(), _rng)
	_map_screen._ready()

	# Act 1: Ativa
	var active1: bool = _map_screen.toggle_autoplay()

	# Assert 1
	assert_true(active1)
	assert_true(_map_screen.autoplay_active)
	assert_true(_map_screen.btn_autoplay.text.contains("AUTO [ON]"))

	# Act 2: Desativa
	var active2: bool = _map_screen.toggle_autoplay()

	# Assert 2
	assert_false(active2)
	assert_false(_map_screen.autoplay_active)
	assert_true(_map_screen.btn_autoplay.text.contains("AUTO [F5]"))

func test_map_screen_pick_best_autoplay_node_priority_healing() -> void:
	# Arrange: Grupo com herói ferido
	_map_screen = autofree(MAP_SCENE.instantiate()) as RunMapScreen
	var gen: RunMapGenerator = RunMapGenerator.new(7, 3, 3)
	_run_state = RunState.new(gen, _rng)
	_run_state.start_run({"aquele": 30, "stark": 34, "elden": 26}, ["ataque"], 123)
	_run_state.hero_hp["aquele"] = 5 # < 50% HP (gravemente ferido)
	_map_screen.setup(_run_state, RunNodeResolver.new(), _rng)

	var node_combat: RunNode = RunNode.new(1, 1, 1, 0, RunNode.NodeType.COMBAT)
	var node_campfire: RunNode = RunNode.new(2, 1, 1, 1, RunNode.NodeType.CAMPFIRE)
	var available: Array[RunNode] = [node_combat, node_campfire]

	# Act
	var chosen: RunNode = _map_screen.pick_best_autoplay_node(available)

	# Assert: Prioriza Fogueira para salvar o herói ferido
	assert_not_null(chosen)
	assert_eq(chosen.type, RunNode.NodeType.CAMPFIRE, "Deve priorizar fogueira quando herói estiver com PV baixo")

func test_map_screen_pick_best_autoplay_node_edge_cases() -> void:
	# Arrange
	_map_screen = autofree(MAP_SCENE.instantiate()) as RunMapScreen

	# Act & Assert: Lista vazia
	var empty_res: RunNode = _map_screen.pick_best_autoplay_node([])
	assert_null(empty_res, "Lista vazia de nós deve retornar null de forma segura")

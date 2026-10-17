# res://test/unit/test_run_map_screen.gd
extends GutTest

## Testes unitários para a cena e controlador do mapa da run (RunMapScreen)
## Segue o padrão AAA, isolamento por injeção e segurança de memória.

var _screen: RunMapScreen
var _state: RunState
var _generator: RunMapGenerator
var _rng: RandomNumberGenerator

func before_each() -> void:
	_generator = RunMapGenerator.new(6, 3, 2)
	_rng = RandomNumberGenerator.new()
	_rng.seed = 42
	_state = RunState.new(_generator, _rng)
	_state.start_run({"aquele": 30, "stark": 34, "elden": 26}, ["ataque", "defesa"], 42)

	var scene_res: PackedScene = load("res://scenes/run/RunMapScreen.tscn")
	_screen = autofree(scene_res.instantiate()) as RunMapScreen

func after_each() -> void:
	RunSession.clear()
	_screen = null
	_state = null
	_generator = null
	_rng = null

func test_screen_bare_node_headless_safety() -> void:
	# Arrange
	var bare: RunMapScreen = autofree(RunMapScreen.new())

	# Act & Assert (não deve quebrar sem scene tree)
	bare._ready()
	bare.refresh_ui()
	assert_not_null(bare, "Bare node deve inicializar com segurança mesmo sem .tscn")

func test_screen_setup_and_header_labels() -> void:
	# Arrange
	var mock_resolver: RunNodeResolver = RunNodeResolver.new()

	# Act
	_screen.setup(_state, mock_resolver, _rng)
	_screen._ready()

	# Assert
	assert_eq(_screen.state, _state)
	assert_not_null(_screen.lbl_act, "Label do Ato deve existir")
	assert_true(_screen.lbl_act.text.contains("ATO I"), "Cabeçalho deve indicar Ato I")
	assert_true(_screen.lbl_boss.text.contains("Viúva Canibal"), "Cabeçalho deve indicar o Chefe Viúva Canibal")
	assert_true(_screen.lbl_gold.text.contains("50"), "Ouro inicial exibido")

func test_screen_node_buttons_generation_and_enabled_states() -> void:
	# Arrange & Act
	_screen.setup(_state, RunNodeResolver.new(), _rng)
	_screen._ready()

	# Assert
	assert_gt(_screen.node_buttons.size(), 0, "Botões de nós devem ser gerados")
	var start_nodes: Array[RunNode] = _state.get_available_nodes()
	for sn in start_nodes:
		assert_true(_screen.node_buttons.has(sn.id), "Botão do nó inicial deve existir")
		var btn: Button = _screen.node_buttons[sn.id]
		assert_false(btn.disabled, "Nós iniciais devem estar habilitados para clique")

	# Nós de andares superiores devem estar desabilitados inicialmente
	var boss: RunNode = _state.map.get_boss_node()
	assert_true(_screen.node_buttons.has(boss.id), "Botão do chefe deve existir")
	assert_true(_screen.node_buttons[boss.id].disabled, "Nó do chefe deve estar desabilitado no início")

func test_screen_node_selection_resolves_and_advances_turn() -> void:
	# Arrange
	_screen.setup(_state, RunNodeResolver.new(), _rng)
	_screen._ready()
	var start_id: int = _state.get_available_nodes()[0].id
	var signal_emitted: Array = []
	_screen.node_selected.connect(func(n): signal_emitted.append(n.id))

	# Act: Simular clique no nó inicial
	_screen._on_node_pressed(start_id)

	# Assert
	assert_eq(signal_emitted, [start_id], "Sinal node_selected emitido")
	assert_true(_state.map.get_node_by_id(start_id).visited, "Nó inicial visitado e concluído")
	assert_true(_screen.log_label.text.length() > 0, "Feedback exibido no painel de log")
	assert_gt(_state.get_available_nodes().size(), 0, "Próximos nós agora disponíveis")

func test_screen_hero_damage_and_fallen_indicator() -> void:
	# Arrange
	_screen.setup(_state, RunNodeResolver.new(), _rng)
	_screen._ready()

	# Act: Danificar e matar um herói
	_state.damage_hero("aquele", 30) # Letal
	_screen.refresh_ui()

	# Assert
	var children = _screen.hero_container.get_children()
	assert_eq(children.size(), 3, "3 cartões de heróis renderizados")
	var card_aquele = children[0]
	var vbox = card_aquele.get_child(0)
	var lbl_name: Label = vbox.get_child(0) as Label
	assert_true(lbl_name.text.contains("💀"), "Herói caído deve exibir indicador de morte")

func test_screen_apply_background_texture_lifecycle_and_idempotency() -> void:
	# Arrange
	_screen.setup(_state, RunNodeResolver.new(), _rng)
	_screen._ready()
	var bg: Node = _screen.get_node_or_null("Background")
	assert_not_null(bg, "Nó Background deve existir na cena")

	# Act
	_screen._apply_background_texture()
	_screen._apply_background_texture() # Idempotência

	# Assert
	var textures_count: int = 0
	for child in bg.get_children():
		if child.name == "MapTexture":
			textures_count += 1
	assert_lte(textures_count, 1, "Não deve duplicar instâncias de MapTexture na chamada repetida")

func test_screen_apply_background_texture_bare_node_without_background_safe() -> void:
	# Arrange
	var bare: RunMapScreen = autofree(RunMapScreen.new())

	# Act & Assert (não deve lançar exceção ou falhar quando Background for nulo)
	bare._apply_background_texture()
	assert_null(bare.get_node_or_null("Background"), "Bare node não tem nó Background mas executa com segurança")

func test_screen_spacing_and_medallion_sizing() -> void:
	# Arrange
	_screen.setup(_state, RunNodeResolver.new(), _rng)
	_screen._ready()

	# Act & Assert - Tamanho dos botões
	var boss_node: RunNode = _state.map.get_boss_node()
	assert_not_null(boss_node)
	var boss_btn: Button = _screen.node_buttons[boss_node.id]
	assert_eq(boss_btn.custom_minimum_size, Vector2(58, 58), "Botão do chefe deve ter tamanho de destaque (58x58)")

	for node in _state.map.nodes:
		if not node.is_boss():
			var btn: Button = _screen.node_buttons[node.id]
			assert_eq(btn.custom_minimum_size, Vector2(42, 42), "Botões regulares devem ter tamanho compacto despoluído (42x42)")

	# Assert - Ausência de sobreposição vertical entre andares consecutivos
	for floor_idx in range(_state.map.floor_count - 1):
		var nodes_current = _state.map.get_nodes_on_floor(floor_idx)
		var nodes_next = _state.map.get_nodes_on_floor(floor_idx + 1)
		for nc in nodes_current:
			var btn_c: Button = _screen.node_buttons[nc.id]
			for nn in nodes_next:
				# Apenas checa se estiverem na mesma coluna ou conectados
				if nc.next_ids.has(nn.id) or nc.column == nn.column:
					var btn_n: Button = _screen.node_buttons[nn.id]
					var vertical_dist: float = absf(btn_c.position.y - btn_n.position.y)
					assert_gte(vertical_dist, 42.0, "Distância vertical entre andares (%f) deve ser >= ao tamanho do botão (42.0)" % vertical_dist)

func test_screen_dynamic_canvas_height_scaling() -> void:
	# Arrange: Gerar mapa com 12 andares (modo estendido)
	var extended_gen: RunMapGenerator = RunMapGenerator.new(12, 4, 3)
	var extended_state: RunState = RunState.new(extended_gen, _rng)
	extended_state.start_run({"aquele": 30, "stark": 34, "elden": 26}, ["ataque"], 42)

	# Act
	_screen.setup(extended_state, RunNodeResolver.new(), _rng)
	_screen.refresh_ui()

	# Assert: Canvas deve expandir para manter respiro vertical
	assert_gt(_screen.map_canvas.custom_minimum_size.y, 540.0, "Mapa com 12 andares deve expandir a altura do canvas dinamicamente")
	assert_gte(_screen.map_canvas.custom_minimum_size.y, 12 * 75.0, "Canvas deve garantir pelo menos 75px por andar")

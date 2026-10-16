# res://test/unit/test_run_map_and_state.gd
extends GutTest

## Testes Unitários para a Estrutura da Run Roguelike (M1 & M2)
## Cobre RunNode, RunMap, RunMapGenerator, RunState, RunNodeResolver e RunSession
## Padrão estrito Arrange-Act-Assert (AAA), isolamento por injeção e zero leaks.

var _generator: RunMapGenerator
var _rng: RandomNumberGenerator
var _state: RunState
var _resolver: RunNodeResolver

func before_each() -> void:
	_generator = RunMapGenerator.new(8, 3, 2)
	_rng = RandomNumberGenerator.new()
	_rng.seed = 12345
	_state = RunState.new(_generator, _rng)
	_resolver = RunNodeResolver.new()

func after_each() -> void:
	RunSession.clear()
	_generator = null
	_rng = null
	_state = null
	_resolver = null

# ==============================================================================
# 1. RunNode Tests
# ==============================================================================

func test_run_node_initialization_and_helpers() -> void:
	# Arrange & Act
	var node: RunNode = RunNode.new(5, 1, 2, 1, RunNode.NodeType.ELITE)

	# Assert
	assert_eq(node.id, 5, "ID deve ser 5")
	assert_eq(node.act, 1, "Ato deve ser 1")
	assert_eq(node.floor_index, 2, "Andar deve ser 2")
	assert_eq(node.column, 1, "Coluna deve ser 1")
	assert_eq(node.type, RunNode.NodeType.ELITE, "Tipo deve ser ELITE")
	assert_true(node.is_combat_type(), "Elite deve ser combate")
	assert_false(node.is_boss(), "Elite não é Boss")
	assert_eq(node.get_type_name(), "Elite", "Nome do tipo")
	assert_eq(node.get_short_label(), "E", "Label curto")

func test_run_node_connections_and_edge_cases() -> void:
	# Arrange
	var node: RunNode = RunNode.new(1, 1, 0, 0, RunNode.NodeType.COMBAT)

	# Act
	var ok1: bool = node.connect_to(2)
	var ok_dup: bool = node.connect_to(2)
	var ok_self: bool = node.connect_to(1)
	var ok_neg: bool = node.connect_to(-1)

	# Assert
	assert_true(ok1, "Conexão válida com nó 2")
	assert_false(ok_dup, "Conexão duplicada deve ser rejeitada")
	assert_false(ok_self, "Auto-conexão deve ser rejeitada")
	assert_false(ok_neg, "Conexão negativa deve ser rejeitada")
	assert_eq(node.next_ids.size(), 1, "Apenas uma conexão aceita")

func test_run_node_serialization_roundtrip() -> void:
	# Arrange
	var original: RunNode = RunNode.new(10, 2, 4, 3, RunNode.NodeType.CAMPFIRE)
	original.connect_to(11)
	original.connect_to(12)
	original.visited = true

	# Act
	var dict: Dictionary = original.to_dict()
	var restored: RunNode = RunNode.from_dict(dict)

	# Assert
	assert_not_null(restored, "Dicionário válido restaura RunNode")
	assert_eq(restored.id, 10)
	assert_eq(restored.act, 2)
	assert_eq(restored.floor_index, 4)
	assert_eq(restored.column, 3)
	assert_eq(restored.type, RunNode.NodeType.CAMPFIRE)
	assert_eq(restored.next_ids, [11, 12])
	assert_true(restored.visited)

	# Edge Case: Dicionário malformado
	assert_null(RunNode.from_dict({}), "Dicionário vazio retorna null")
	assert_null(RunNode.from_dict({"id": 1}), "Faltando campos obrigatórios retorna null")

# ==============================================================================
# 2. RunMap Tests
# ==============================================================================

func test_run_map_structure_and_reachability() -> void:
	# Arrange
	var map: RunMap = RunMap.new(1, 3)
	var n0: RunNode = RunNode.new(0, 1, 0, 0, RunNode.NodeType.COMBAT)
	var n1: RunNode = RunNode.new(1, 1, 1, 0, RunNode.NodeType.CAMPFIRE)
	var boss: RunNode = RunNode.new(2, 1, 2, 1, RunNode.NodeType.BOSS)
	n0.connect_to(n1.id)
	n1.connect_to(boss.id)

	# Act
	assert_true(map.add_node(n0))
	assert_true(map.add_node(n1))
	assert_true(map.add_node(boss))
	assert_false(map.add_node(n0), "Não deve adicionar nó com id duplicado")
	assert_false(map.add_node(null), "Não deve adicionar nó nulo")

	# Assert
	assert_eq(map.size(), 3)
	assert_eq(map.get_start_nodes().size(), 1)
	assert_eq(map.get_start_nodes()[0].id, 0)
	assert_not_null(map.get_boss_node())
	assert_eq(map.get_boss_node().id, 2)
	assert_true(map.has_edge(0, 1))
	assert_false(map.has_edge(0, 2))
	assert_true(map.can_reach_boss(0), "Nó 0 alcança o boss via BFS")
	assert_true(map.can_reach_boss(1), "Nó 1 alcança o boss via BFS")
	assert_true(map.can_reach_boss(2), "Boss alcança a si mesmo")

func test_run_map_serialization_roundtrip() -> void:
	# Arrange
	var map: RunMap = RunMap.new(1, 2)
	var n0: RunNode = RunNode.new(0, 1, 0, 0, RunNode.NodeType.COMBAT)
	var b: RunNode = RunNode.new(1, 1, 1, 0, RunNode.NodeType.BOSS)
	n0.connect_to(b.id)
	map.add_node(n0)
	map.add_node(b)

	# Act
	var dict: Dictionary = map.to_dict()
	var restored: RunMap = RunMap.from_dict(dict)

	# Assert
	assert_not_null(restored, "Mapa restaurado com sucesso")
	assert_eq(restored.size(), 2)
	assert_eq(restored.act, 1)
	assert_true(restored.has_edge(0, 1))

	# Edge cases de deserialização
	assert_null(RunMap.from_dict({}), "Dicionário vazio retorna null")
	assert_null(RunMap.from_dict({"nodes": ["invalido"]}), "Lista de nós inválida retorna null")

# ==============================================================================
# 3. RunMapGenerator Tests
# ==============================================================================

func test_map_generator_determinism_and_rules() -> void:
	# Arrange
	var gen: RunMapGenerator = RunMapGenerator.new(10, 4, 3)
	var rng1: RandomNumberGenerator = RandomNumberGenerator.new()
	var rng2: RandomNumberGenerator = RandomNumberGenerator.new()
	rng1.seed = 9999
	rng2.seed = 9999

	# Act
	var map1: RunMap = gen.generate(1, rng1)
	var map2: RunMap = gen.generate(1, rng2)

	# Assert - Determinismo
	assert_not_null(map1)
	assert_not_null(map2)
	assert_eq(map1.size(), map2.size(), "Mesma seed gera mesmo número de nós")
	
	# Assert - Regras de Andar
	var start_nodes: Array[RunNode] = map1.get_start_nodes()
	assert_gt(start_nodes.size(), 0, "Deve haver nós iniciais no andar 0")
	for sn in start_nodes:
		assert_eq(sn.type, RunNode.NodeType.COMBAT, "Andar 0 deve ser sempre Combate")
		assert_true(map1.can_reach_boss(sn.id), "Todo nó inicial deve alcançar o boss!")

	var campfire_floor: Array[RunNode] = map1.get_nodes_on_floor(8)
	assert_gt(campfire_floor.size(), 0, "Deve haver nós no penúltimo andar")
	for cn in campfire_floor:
		assert_eq(cn.type, RunNode.NodeType.CAMPFIRE, "Penúltimo andar deve ser Fogueira")

	var boss_node: RunNode = map1.get_boss_node()
	assert_not_null(boss_node, "Deve existir nó de Chefe")
	assert_eq(boss_node.floor_index, 9, "Chefe deve estar no último andar")

func test_map_generator_error_handling_and_clamping() -> void:
	# Arrange
	var gen_small: RunMapGenerator = RunMapGenerator.new(1, 1, 1) # floor < 3
	var rng: RandomNumberGenerator = RandomNumberGenerator.new()
	rng.seed = 42

	# Act & Assert
	assert_gte(gen_small.floor_count, 3, "Andares mínimos devem ser clampados para 3")
	var null_map: RunMap = gen_small.generate(1, null)
	assert_null(null_map, "RNG nulo deve retornar null de forma segura")

	var invalid_act_map: RunMap = gen_small.generate(0, rng)
	assert_null(invalid_act_map, "Ato < 1 deve retornar null")

# ==============================================================================
# 4. RunState Tests (Lifecycle, Heroes & Permadeath)
# ==============================================================================

func test_run_state_start_run_happy_path() -> void:
	# Arrange
	var party: Dictionary = {"aquele": 30, "stark": 34, "elden": 26}
	var starter_deck: Array[String] = ["movimento", "ataque", "escavacao"]

	# Act
	var ok: bool = _state.start_run(party, starter_deck, 777)

	# Assert
	assert_true(ok, "start_run deve retornar true")
	assert_true(_state.is_active(), "Estado deve estar ativo")
	assert_eq(_state.act, 1, "Ato inicial é 1")
	assert_eq(_state.gold, RunState.STARTING_GOLD, "Ouro inicial é 50")
	assert_eq(_state.get_living_heroes().size(), 3, "3 heróis vivos")
	assert_eq(_state.deck.size(), 3, "3 cartas no deck")
	assert_eq(_state.get_current_boss_id(), "viuva_canibal", "Boss do Ato 1 é Viúva Canibal")
	assert_gt(_state.get_available_nodes().size(), 0, "Nós iniciais disponíveis")

func test_run_state_start_run_validation_edge_cases() -> void:
	# Arrange
	var empty_party: Dictionary = {}
	var oversized_party: Dictionary = {"a": 10, "b": 10, "c": 10, "d": 10}
	var invalid_hp_party: Dictionary = {"aquele": 0}

	# Act & Assert
	assert_false(_state.start_run(empty_party, [], 1), "Grupo vazio rejeitado")
	assert_false(_state.start_run(oversized_party, [], 1), "Grupo > 3 rejeitado")
	assert_false(_state.start_run(invalid_hp_party, [], 1), "Herói com 0 HP rejeitado")
	assert_false(_state.is_active(), "Estado permanece inativo")

func test_run_state_hero_damage_death_and_permadeath() -> void:
	# Arrange
	_state.start_run({"aquele": 30, "stark": 30}, ["ataque"], 10)
	var died_signals: Array = []
	_state.hero_died.connect(func(h): died_signals.append(h))

	# Act 1: Dano parcial
	var hp1: int = _state.damage_hero("aquele", 10)
	assert_eq(hp1, 20, "HP restante é 20")

	# Act 2: Dano letal
	var hp2: int = _state.damage_hero("aquele", 25)
	assert_eq(hp2, 0, "HP cai para 0")
	assert_false(_state.is_hero_alive("aquele"), "Aquele está morto")
	assert_eq(died_signals, ["aquele"], "Sinal hero_died disparado")

	# Act 3: Tentativa de cura em herói morto (Permadeath)
	var hp_heal_dead: int = _state.heal_hero("aquele", 15)
	assert_eq(hp_heal_dead, 0, "Herói morto não pode ser curado!")

	# Act 4: Dano letal no último herói -> Derrota da Run
	var run_ended_signals: Array = []
	_state.run_ended.connect(func(victory): run_ended_signals.append(victory))
	_state.damage_hero("stark", 30)

	assert_eq(_state.status, RunState.Status.DEFEAT, "Status muda para DEFEAT")
	assert_false(_state.is_active(), "Run não está mais ativa")
	assert_eq(run_ended_signals, [false], "Sinal run_ended emitido com false")

func test_run_state_navigation_and_node_completion() -> void:
	# Arrange
	_state.start_run({"aquele": 30}, ["ataque"], 123)
	var start_nodes: Array[RunNode] = _state.get_available_nodes()
	var target_node: RunNode = start_nodes[0]

	# Act 1: Mover para o primeiro nó
	var moved: bool = _state.move_to(target_node.id)
	assert_true(moved, "Mover para nó inicial permitido")
	assert_eq(_state.current_node_id, target_node.id)
	assert_false(target_node.visited, "Nó não é visitado até ser completado")

	# Act 2: Tentar mover sem completar
	assert_eq(_state.get_available_nodes().size(), 0, "Nenhum nó disponível enquanto o atual estiver pendente")

	# Act 3: Completar nó
	var completed: bool = _state.complete_current_node()
	assert_true(completed, "Nó completado")
	assert_true(target_node.visited, "Nó marcado como visitado")
	assert_eq(_state.floors_cleared, 1, "1 andar limpo")
	assert_gt(_state.get_available_nodes().size(), 0, "Próximos nós agora disponíveis")

func test_run_state_act_transition_and_final_victory() -> void:
	# Arrange
	_state.start_run({"aquele": 30}, ["ataque"], 456)
	var act_signals: Array = []
	var victory_signals: Array = []
	_state.act_advanced.connect(func(a): act_signals.append(a))
	_state.run_ended.connect(func(v): victory_signals.append(v))

	# Danificar o herói para testar a cura da transição de Ato
	_state.damage_hero("aquele", 10) # 20 / 30 HP

	# Act 1: Forçar conclusão do boss do Ato 1
	var boss_a1: RunNode = _state.map.get_boss_node()
	_state.current_node_id = boss_a1.id
	_state.complete_current_node()

	# Assert 1: Avanço para o Ato 2
	assert_eq(_state.act, 2, "Avançou para o Ato 2")
	assert_eq(act_signals, [2], "Sinal act_advanced disparado")
	assert_gt(_state.hero_hp["aquele"], 20, "Herói recebeu cura na transição de Ato")
	assert_eq(_state.get_current_boss_id(), "rainha_do_enxame", "Boss do Ato 2 é Rainha do Enxame")

	# Act 2: Concluir boss do Ato 2
	var boss_a2: RunNode = _state.map.get_boss_node()
	_state.current_node_id = boss_a2.id
	_state.complete_current_node()
	assert_eq(_state.act, 3, "Avançou para o Ato 3")
	assert_eq(_state.get_current_boss_id(), "rei_isectum", "Boss do Ato 3 é o Rei Isectum")

	# Act 3: Derrotar o Rei Isectum (Chefe Final)
	var boss_a3: RunNode = _state.map.get_boss_node()
	_state.current_node_id = boss_a3.id
	_state.complete_current_node()

	# Assert 3: Vitória da Run e Cálculo de Âmbar
	assert_eq(_state.status, RunState.Status.VICTORY, "Status é VICTORY")
	assert_eq(victory_signals, [true], "Sinal run_ended disparado com vitória")
	var amber: int = _state.calculate_amber()
	# 3 bosses (30) + 3 floors (3) + vitória (25) = 58
	assert_gte(amber, 55, "Âmbar Real calculado corretamente com bônus de vitória")

func test_run_state_gold_cards_and_relics() -> void:
	# Arrange
	_state.start_run({"aquele": 30}, ["ataque"], 1)

	# Act & Assert - Ouro
	assert_true(_state.add_gold(25))
	assert_eq(_state.gold, 75)
	assert_false(_state.add_gold(-5), "Ouro negativo rejeitado")
	assert_true(_state.spend_gold(50))
	assert_eq(_state.gold, 25)
	assert_false(_state.spend_gold(100), "Não pode gastar mais do que tem")

	# Act & Assert - Cartas
	assert_true(_state.add_card("defesa_runica"))
	assert_true(_state.deck.has("defesa_runica"))
	assert_true(_state.remove_card("defesa_runica"))
	assert_false(_state.deck.has("defesa_runica"))
	assert_false(_state.remove_card("carta_inexistente"))

	# Act & Assert - Relíquias
	assert_true(_state.add_relic("dente_da_viuva"))
	assert_true(_state.has_relic("dente_da_viuva"))
	assert_false(_state.add_relic("dente_da_viuva"), "Relíquia duplicada rejeitada")
	assert_false(_state.add_relic(""), "Relíquia vazia rejeitada")

func test_run_state_serialization_roundtrip() -> void:
	# Arrange
	_state.start_run({"aquele": 30, "stark": 34}, ["ataque", "movimento"], 888)
	_state.damage_hero("aquele", 5)
	_state.add_gold(40)
	_state.add_relic("amuleto_ferro")
	var start_id: int = _state.get_available_nodes()[0].id
	_state.move_to(start_id)

	# Act
	var dict: Dictionary = _state.to_dict()
	var restored: RunState = RunState.new()
	var success: bool = restored.from_dict(dict)

	# Assert
	assert_true(success, "from_dict deve restaurar com sucesso")
	assert_eq(restored.status, RunState.Status.ACTIVE)
	assert_eq(restored.act, 1)
	assert_eq(restored.gold, 90)
	assert_eq(restored.hero_hp["aquele"], 25)
	assert_true(restored.has_relic("amuleto_ferro"))
	assert_eq(restored.current_node_id, start_id)
	assert_not_null(restored.map)

	# Edge Case: Dicionário vazio
	assert_false(restored.from_dict({}), "Dicionário vazio retorna false")

# ==============================================================================
# 5. RunNodeResolver Tests
# ==============================================================================

func test_run_node_resolver_campfire_heals_party() -> void:
	# Arrange
	_state.start_run({"aquele": 30}, ["ataque"], 1)
	_state.damage_hero("aquele", 15) # 15 / 30
	var campfire_node: RunNode = RunNode.new(99, 1, 1, 0, RunNode.NodeType.CAMPFIRE)
	_state.map.add_node(campfire_node)
	_state.current_node_id = 99

	# Act
	var res: Dictionary = _resolver.resolve(_state, _rng)

	# Assert
	assert_true(res["ok"], "Resolução bem-sucedida")
	assert_gt(_state.hero_hp["aquele"], 15, "Fogueira curou o herói")
	assert_true(campfire_node.visited, "Nó de fogueira concluído")

func test_run_node_resolver_combat_deals_damage_and_awards_gold() -> void:
	# Arrange
	_state.start_run({"aquele": 30}, ["ataque"], 1)
	var combat_node: RunNode = RunNode.new(100, 1, 0, 0, RunNode.NodeType.COMBAT)
	_state.map.add_node(combat_node)
	_state.current_node_id = 100

	# Act
	var res: Dictionary = _resolver.resolve(_state, _rng)

	# Assert
	assert_true(res["ok"])
	assert_lt(_state.hero_hp["aquele"], 30, "Herói sofreu dano de combate")
	assert_gt(_state.gold, RunState.STARTING_GOLD, "Vitória concedeu ouro")
	assert_gt(_state.enemies_killed, 0, "Inimigos abatidos foram contabilizados")
	assert_true(combat_node.visited)

# ==============================================================================
# 6. RunSession Tests
# ==============================================================================

func test_run_session_singleton_lifecycle() -> void:
	# Arrange & Act
	assert_false(RunSession.has_active_run(), "Inicialmente sem run ativa")
	var state: RunState = RunSession.start_new(1234)

	# Assert
	assert_not_null(state)
	assert_true(RunSession.has_active_run())
	assert_eq(RunSession.current, state)

	# Cleanup
	RunSession.clear()
	assert_false(RunSession.has_active_run())
	assert_null(RunSession.current)

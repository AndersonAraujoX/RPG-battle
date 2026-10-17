# res://test/unit/test_run_hearts_and_end.gd
extends GutTest

## Testes Unitários: Mecânica dos 3 Corações da Colmeia e Bônus de Vitória no RunState
## Valida a destruição dos nós de Elite Especial no Ato 3, persistência e bônus supremo de Âmbar Real.

var _state: RunState
var _rng: RandomNumberGenerator

func before_each() -> void:
	_rng = RandomNumberGenerator.new()
	_rng.seed = 9999
	_state = RunState.new(null, _rng)
	var party: Dictionary = {"aquele": 45, "stark": 50, "elden": 40}
	var deck: Array[String] = ["card_1", "card_2", "card_3", "card_4", "card_5"]
	_state.start_run(party, deck, 9999)

func after_each() -> void:
	if _state != null:
		_state = null

func test_destroy_heart_happy_path() -> void:
	# Arrange
	watch_signals(_state)

	# Act
	var ok: bool = _state.destroy_heart("coracao_da_mente")

	# Assert
	assert_true(ok)
	assert_true(_state.has_destroyed_heart("coracao_da_mente"))
	assert_eq(_state.get_destroyed_hearts().size(), 1)
	assert_signal_emitted_with_parameters(_state, "heart_destroyed", ["coracao_da_mente"])

func test_destroy_heart_edge_cases_duplicates_and_empty() -> void:
	# Arrange
	_state.destroy_heart("coracao_da_carapaca")

	# Act & Assert
	assert_false(_state.destroy_heart(""), "ID vazio deve ser rejeitado")
	assert_false(_state.destroy_heart("coracao_da_carapaca"), "Coração já destruído deve ser rejeitado")
	assert_eq(_state.get_destroyed_hearts().size(), 1)

func test_complete_current_node_in_act_3_elite_destroys_next_heart() -> void:
	# Arrange: Coloca o state no Ato 3
	_state.act = 3
	_state.map = RunMapGenerator.new().generate(3, _rng)
	var elite_node: RunNode = null
	for n in _state.map.get_nodes_on_floor(4):
		if n.type == RunNode.NodeType.ELITE:
			elite_node = n
			break
	if elite_node == null:
		# Cria nó de elite sintético para o teste
		elite_node = RunNode.new(99, 3, 4, 0, RunNode.NodeType.ELITE)
		_state.map.add_node(elite_node)

	_state.current_node_id = elite_node.id
	assert_eq(_state.get_destroyed_hearts().size(), 0)

	# Act
	var completed: bool = _state.complete_current_node()

	# Assert
	assert_true(completed)
	assert_eq(_state.get_destroyed_hearts().size(), 1)
	assert_true(_state.has_destroyed_heart("coracao_da_mente"))

func test_calculate_amber_doubles_on_victory_with_zero_hearts_destroyed() -> void:
	# Arrange: Run vitoriosa sem destruir corações (bônus supremo)
	_state.floors_cleared = 12
	_state.bosses_defeated = 3
	_state.status = RunState.Status.VICTORY
	assert_true(_state.destroyed_hearts.is_empty())

	# Act
	# Base: 12 * 1 + 3 * 10 + 25 = 67 -> Dobrado = 134
	var amber: int = _state.calculate_amber()

	# Assert
	assert_eq(amber, 134, "Vitória com todos os corações poupados dobra o Âmbar Real")

func test_calculate_amber_normal_when_hearts_destroyed() -> void:
	# Arrange: Run vitoriosa com corações destruídos
	_state.floors_cleared = 12
	_state.bosses_defeated = 3
	_state.status = RunState.Status.VICTORY
	_state.destroy_heart("coracao_da_mente")

	# Act
	# Base: 12 * 1 + 3 * 10 + 25 = 67 (sem dobrar)
	var amber: int = _state.calculate_amber()

	# Assert
	assert_eq(amber, 67, "Vitória com corações destruídos recebe pontuação padrão")

func test_serialization_roundtrip_preserves_destroyed_hearts() -> void:
	# Arrange
	_state.destroy_heart("coracao_da_mente")
	_state.destroy_heart("coracao_da_carapaca")

	# Act
	var dict: Dictionary = _state.to_dict()
	var restored: RunState = RunState.new()
	var ok: bool = restored.from_dict(dict)

	# Assert
	assert_true(ok)
	assert_true(restored.has_destroyed_heart("coracao_da_mente"))
	assert_true(restored.has_destroyed_heart("coracao_da_carapaca"))
	assert_false(restored.has_destroyed_heart("coracao_da_ninhada"))
	assert_eq(restored.get_destroyed_hearts().size(), 2)

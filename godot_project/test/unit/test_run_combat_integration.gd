# res://test/unit/test_run_combat_integration.gd
extends GutTest

## Suíte de Testes Unitários de Integração: Combate Tático ↔ Run Roguelike (Marco M4)
## Valida persistência bidirecional de PV, permadeath, roteamento de vitória/derrota,
## ingestão do estado da run pelo CercoGameController e compatibilidade standalone.

var _generator: RunMapGenerator
var _rng: RandomNumberGenerator
var _state: RunState

func before_each() -> void:
	_generator = RunMapGenerator.new(8, 3, 2)
	_rng = RandomNumberGenerator.new()
	_rng.seed = 4242
	_state = RunState.new(_generator, _rng)
	var party: Dictionary = {"aquele": 30, "stark": 34, "elden": 26}
	var starter_deck: Array[String] = ["movimento", "trabalho", "escavacao", "ataque", "defesa"]
	_state.start_run(party, starter_deck, 4242)

func after_each() -> void:
	RunSession.clear()
	_state = null
	_generator = null
	_rng = null

# ── 1. Setup & Headless Safety ───────────────────────────────────────────────

func test_bridge_setup_combat_without_run_safe_fallback() -> void:
	# Arrange
	RunSession.clear()

	# Act
	var payload: Dictionary = RunCombatBridge.setup_combat(null, null)

	# Assert
	assert_false(payload.get("ok", true), "Setup sem run deve retornar ok: false")
	assert_eq(payload.get("living_heroes", []).size(), 0, "Sem heróis vivos")

func test_bridge_setup_combat_populates_living_heroes_and_deck() -> void:
	# Arrange
	var start_nodes: Array[RunNode] = _state.get_available_nodes()
	var node: RunNode = start_nodes[0]
	_state.move_to(node.id)

	# Act
	var payload: Dictionary = RunCombatBridge.setup_combat(_state, node, _rng)

	# Assert
	assert_true(payload.get("ok", false), "Payload deve indicar sucesso")
	assert_eq(payload.get("act", 0), 1, "Ato correto")
	assert_eq(payload.get("node_id", -1), node.id, "ID do nó correto")
	assert_eq(payload.get("living_heroes", []).size(), 3, "3 heróis vivos")
	assert_eq(payload.get("hero_hp", {})["aquele"], 30, "PV de Aquele correto")
	assert_eq(payload.get("deck", []).size(), 5, "Deck com 5 cartas")
	assert_gte(payload.get("party", []).size(), 3, "Party gerada com 3 registros")

func test_bridge_setup_combat_filters_out_fallen_heroes() -> void:
	# Arrange
	_state.damage_hero("aquele", 30) # Aquele morre
	var node: RunNode = _state.get_available_nodes()[0]

	# Act
	var payload: Dictionary = RunCombatBridge.setup_combat(_state, node, _rng)

	# Assert
	var living: Array = payload.get("living_heroes", [])
	assert_false(living.has("aquele"), "Herói caído não pode estar no grupo de combate")
	assert_true(living.has("stark"), "Stark deve estar vivo")
	assert_true(living.has("elden"), "Elden deve estar vivo")
	assert_eq(living.size(), 2, "Apenas 2 heróis vivos")

	var party: Array = payload.get("party", [])
	assert_eq(party.size(), 2, "Lista de party do tabuleiro deve conter apenas 2 heróis")

# ── 2. Persistência de PV ───────────────────────────────────────────────────

func test_sync_combat_result_updates_partial_hp() -> void:
	# Arrange
	var node: RunNode = _state.get_available_nodes()[0]
	_state.move_to(node.id)
	var combat_res: Dictionary = {
		"victory": true,
		"surviving_heroes_hp": {"aquele": 18, "stark": 22, "elden": 26},
		"enemies_killed": 3
	}

	# Act
	var summary: Dictionary = RunCombatBridge.sync_combat_result(_state, combat_res)

	# Assert
	assert_true(summary.get("victory", false))
	assert_eq(_state.hero_hp["aquele"], 18, "PV de Aquele sincronizado para 18")
	assert_eq(_state.hero_hp["stark"], 22, "PV de Stark sincronizado para 22")
	assert_eq(_state.hero_hp["elden"], 26, "PV de Elden sincronizado para 26")
	assert_true(_state.is_hero_alive("aquele"))

func test_sync_combat_result_clamps_overheal_to_max_hp() -> void:
	# Arrange
	var node: RunNode = _state.get_available_nodes()[0]
	_state.move_to(node.id)
	var combat_res: Dictionary = {
		"victory": true,
		"surviving_heroes_hp": {"aquele": 999}, # Excesso de cura
		"enemies_killed": 2
	}

	# Act
	RunCombatBridge.sync_combat_result(_state, combat_res)

	# Assert
	assert_eq(_state.hero_hp["aquele"], 30, "PV deve ser clampeado no max_hp (30)")

func test_sync_combat_result_clamps_negative_hp_to_zero() -> void:
	# Arrange
	var node: RunNode = _state.get_available_nodes()[0]
	_state.move_to(node.id)
	var combat_res: Dictionary = {
		"victory": true,
		"surviving_heroes_hp": {"aquele": -15, "stark": 20, "elden": 20},
		"enemies_killed": 2
	}

	# Act
	RunCombatBridge.sync_combat_result(_state, combat_res)

	# Assert
	assert_eq(_state.hero_hp["aquele"], 0)
	assert_true(_state.fallen_heroes.has("aquele"), "Herói com PV <= 0 marcado como caído")

# ── 3. Permadeath ───────────────────────────────────────────────────────────

func test_sync_combat_result_single_hero_death_marks_fallen() -> void:
	# Arrange
	var node: RunNode = _state.get_available_nodes()[0]
	_state.move_to(node.id)
	var combat_res: Dictionary = {
		"victory": true,
		"surviving_heroes_hp": {"stark": 20, "elden": 25},
		"fallen_heroes": ["aquele"],
		"enemies_killed": 4
	}

	# Act
	var summary: Dictionary = RunCombatBridge.sync_combat_result(_state, combat_res)

	# Assert
	assert_true(summary["victory"])
	assert_false(_state.is_hero_alive("aquele"), "Aquele não deve mais estar vivo")
	assert_true(_state.fallen_heroes.has("aquele"), "Aquele está em fallen_heroes")
	assert_eq(_state.get_living_heroes().size(), 2)

func test_permadeath_hero_cannot_be_healed_subsequently() -> void:
	# Arrange
	_state.damage_hero("aquele", 30) # Tombou
	_state.damage_hero("stark", 20)  # 14 / 34 PV

	# Act 1: Fogueira (30% heal)
	_state.heal_party_percent(0.30)

	# Assert 1
	assert_eq(_state.hero_hp["aquele"], 0, "Herói morto não é curado por fogueira")
	assert_gt(_state.hero_hp["stark"], 14, "Herói vivo recebe cura")

	# Act 2: Cura direta
	var res_heal: int = _state.heal_hero("aquele", 50)
	assert_eq(res_heal, 0, "heal_hero direto recusa curar morto")

# ── 4. Roteamento de Derrota & Vitória ───────────────────────────────────────

func test_sync_combat_result_party_wipe_triggers_defeat() -> void:
	# Arrange
	var node: RunNode = _state.get_available_nodes()[0]
	_state.move_to(node.id)
	var combat_res: Dictionary = {
		"victory": false,
		"surviving_heroes_hp": {},
		"fallen_heroes": ["aquele", "stark", "elden"],
		"enemies_killed": 1
	}

	# Act
	var summary: Dictionary = RunCombatBridge.sync_combat_result(_state, combat_res)

	# Assert
	assert_false(summary["victory"])
	assert_true(summary["game_over"])
	assert_true(summary["party_wipe"])
	assert_eq(_state.status, RunState.Status.DEFEAT)
	assert_false(_state.is_active())

func test_sync_combat_result_defeat_calculates_amber_without_bonus() -> void:
	# Arrange
	_state.floors_cleared = 4
	_state.bosses_defeated = 1
	var combat_res: Dictionary = {
		"victory": false,
		"surviving_heroes_hp": {},
		"fallen_heroes": ["aquele", "stark", "elden"],
		"enemies_killed": 0
	}

	# Act
	var summary: Dictionary = RunCombatBridge.sync_combat_result(_state, combat_res)

	# Assert
	# 4 andares * 1 + 1 boss * 10 = 14 âmbar (sem bônus de 25 de vitória)
	assert_eq(summary["amber_earned"], 14)

func test_sync_combat_result_victory_completes_current_node() -> void:
	# Arrange
	var node: RunNode = _state.get_available_nodes()[0]
	_state.move_to(node.id)
	var combat_res: Dictionary = {
		"victory": true,
		"surviving_heroes_hp": {"aquele": 25, "stark": 25, "elden": 25},
		"enemies_killed": 3,
		"gold_earned": 10
	}

	# Act
	var summary: Dictionary = RunCombatBridge.sync_combat_result(_state, combat_res)

	# Assert
	assert_true(summary["victory"])
	assert_true(node.visited)
	assert_eq(_state.floors_cleared, 1)
	assert_eq(_state.gold, RunState.STARTING_GOLD + 10)
	assert_eq(_state.enemies_killed, 3)

func test_victory_boss_act1_advances_act_and_heals_survivors() -> void:
	# Arrange
	var boss: RunNode = _state.map.get_boss_node()
	_state.current_node_id = boss.id
	_state.damage_hero("aquele", 15) # 15 / 30 PV
	var combat_res: Dictionary = {
		"victory": true,
		"surviving_heroes_hp": {"aquele": 15, "stark": 34, "elden": 26},
		"enemies_killed": 5
	}

	# Act
	var summary: Dictionary = RunCombatBridge.sync_combat_result(_state, combat_res)

	# Assert
	assert_true(summary["victory"])
	assert_eq(_state.act, 2, "Avançou para o Ato 2")
	assert_eq(_state.bosses_defeated, 1)
	assert_gt(_state.hero_hp["aquele"], 15, "Sobrevivente recebeu cura de transição de Ato (+25%)")

func test_can_deploy_hero_validation() -> void:
	# Arrange
	_state.damage_hero("aquele", 30)

	# Act & Assert
	assert_false(RunCombatBridge.can_deploy_hero(_state, "aquele"))
	assert_true(RunCombatBridge.can_deploy_hero(_state, "stark"))
	assert_false(RunCombatBridge.can_deploy_hero(_state, "inexistente"))
	assert_false(RunCombatBridge.can_deploy_hero(null, "stark"))

# ── 5. Ingestão no CercoGameController & Isolamento Standalone ───────────────

func test_cerco_game_controller_standalone_when_no_run() -> void:
	# Arrange
	RunSession.clear()

	# Act
	var controller: CercoGameController = autofree(CercoGameController.new())
	controller._initialize_models()

	# Assert
	assert_false(controller.board.has_unit("aquele"), "Aquele é personagem secreto e não deve estar no standalone")
	assert_true(controller.board.has_unit("stark"), "Stark presente no standalone")
	assert_true(controller.board.has_unit("elden"), "Elden presente no standalone")
	assert_true(controller.board.has_unit("lysander"), "Lysander presente no standalone")

func test_cerco_game_controller_ingests_run_session_with_living_heroes_only() -> void:
	# Arrange
	RunSession.start_new(999, {"aquele": 22, "stark": 20, "elden": 18}, ["movimento", "trabalho", "escavacao"])
	var run: RunState = RunSession.current
	# Mata stark antes do combate
	run.damage_hero("stark", 9999)
	assert_false(run.is_hero_alive("stark"), "Stark está tombado")

	var node: RunNode = run.get_available_nodes()[0]
	run.move_to(node.id)

	# Act
	var controller: CercoGameController = autofree(CercoGameController.new())
	controller._initialize_models()

	# Assert
	assert_true(controller.is_run_mode, "Controller deve reconhecer sessão ativa da run")
	assert_true(controller.board.has_unit("aquele"), "Aquele (vivo) deve estar no tabuleiro")
	assert_true(controller.board.has_unit("elden"), "Elden (vivo) deve estar no tabuleiro")
	assert_false(controller.board.has_unit("stark"), "Stark (caído/permadeath) NÃO pode ser colocado no tabuleiro")
	assert_false(controller.board.has_unit("lysander"), "Lysander (não faz parte do grupo da run) não deve estar no tabuleiro")

	var aquele_data: Dictionary = controller.board.get_unit_data("aquele")
	assert_eq(int(aquele_data.get("hp", 0)), 22, "PV inicial no tabuleiro deve coincidir exatamente com o PV persistido (22)")
	assert_true(controller.has_spawned_encounter, "Esquadrão do combate tático foi spawnado no tabuleiro")
	assert_not_null(controller.relic_manager, "RelicManager deve ser instanciado em modo run")
	assert_not_null(controller.relic_manager.event_bus, "EventBus deve ser conectado ao RelicManager no controller")

func test_sync_combat_result_populates_newly_fallen_heroes() -> void:
	# Arrange
	var party: Dictionary = {"aquele": 30, "stark": 20, "lysander": 20}
	var state: RunState = RunState.new()
	state.start_run(party, ["movimento", "trabalho"], 101)
	var node: RunNode = state.get_available_nodes()[0]
	state.move_to(node.id)

	var combat_res: Dictionary = {
		"victory": true,
		"surviving_heroes_hp": {
			"aquele": 25,
			"stark": 0
		},
		"fallen_heroes": ["lysander"],
		"enemies_killed": 3
	}

	# Act
	var summary: Dictionary = RunCombatBridge.sync_combat_result(state, combat_res)

	# Assert
	assert_true(summary["newly_fallen"].has("stark"), "Stark deve estar em newly_fallen após dano fatal via final_hps")
	assert_true(summary["newly_fallen"].has("lysander"), "Lysander deve estar em newly_fallen via reported_fallen")
	assert_false(summary["newly_fallen"].has("aquele"), "Aquele sobreviveu e não deve estar em newly_fallen")
	assert_eq(summary["newly_fallen"].size(), 2, "Exatamente 2 heróis devem ter tombado neste combate")


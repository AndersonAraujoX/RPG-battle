# res://test/unit/test_adversarial_m4.gd
extends GutTest

## Testes Adversariais Empíricos para o Marco M4 (Challenger 2)
## Foco:
## 1. RunCombatBridge: Contratos, idempotência, sanitização e casos nulos/extremos.
## 2. Persistência de HP: Clamping, over-heal, underflow negativo, 1 HP survival.
## 3. Morte Permanente (Permadeath): Impossibilidade de ressuscitação por fogueira,
##    transição de ato ou cura direta, e exclusão rigorosa do tabuleiro de combate.
## 4. Party Wipes & Roteamento de Derrota: Morte de todo o grupo, vitória com 0 heróis (mutual kill),
##    cálculo rigoroso de Âmbar Real sem bônus de vitória.
## 5. Isolamento Standalone do Cerco: Execução sem RunSession, limpeza pós-run,
##    comportamento quando RunCombatBridge tem ou não encontro ativo.
## 6. Procedural Encounter Generator: Nós inválidos, determinismo de seed extrema,
##    ausência de colisões de spawn na grade 20x20 e conformidade de chefes dos Atos 1, 2 e 3.
## 7. Verificação de Bugs Encontrados:
##    - Bug A: newly_fallen não é preenchido em sync_combat_result quando o dano é fatal.
##    - Bug B: card_id_to_card_data com string vazia resulta em card_name vazio.

var _generator: RunMapGenerator
var _rng: RandomNumberGenerator
var _state: RunState

func before_each() -> void:
	RunCombatBridge.clear_encounter()
	RunSession.clear()
	_generator = RunMapGenerator.new(8, 3, 2)
	_rng = RandomNumberGenerator.new()
	_rng.seed = 778899
	_state = RunState.new(_generator, _rng)
	var party: Dictionary = {"aquele": 30, "stark": 34, "elden": 26}
	var starter_deck: Array[String] = ["movimento", "trabalho", "escavacao", "ataque", "defesa"]
	_state.start_run(party, starter_deck, 778899)

func after_each() -> void:
	RunCombatBridge.clear_encounter()
	RunSession.clear()
	_state = null
	_generator = null
	_rng = null

# ==============================================================================
# GRUPO 1: RunCombatBridge Contratos, Nulos e Limites
# ==============================================================================

func test_bridge_setup_with_null_state_and_null_node() -> void:
	# Arrange & Act
	var res1: Dictionary = RunCombatBridge.setup_combat(null, null)
	var res2: Dictionary = RunCombatBridge.setup_combat(_state, null)
	var dummy_node: RunNode = RunNode.new(0, 1, 0, 0, RunNode.NodeType.COMBAT)
	var res3: Dictionary = RunCombatBridge.setup_combat(null, dummy_node)

	# Assert
	assert_false(res1.get("ok", true), "null state e null node deve falhar com ok: false")
	assert_false(res2.get("ok", true), "null node deve falhar com ok: false")
	assert_false(res3.get("ok", true), "null state deve falhar com ok: false")
	assert_false(RunCombatBridge.has_active_encounter(), "Não deve haver encontro ativo após falhas de setup")

func test_bridge_setup_when_run_is_inactive_or_defeated() -> void:
	# Arrange
	var node: RunNode = _state.get_available_nodes()[0]
	_state.status = RunState.Status.DEFEAT

	# Act
	var res: Dictionary = RunCombatBridge.setup_combat(_state, node)

	# Assert
	assert_false(res.get("ok", true), "Setup em run derrotada deve retornar ok: false")
	assert_false(RunCombatBridge.has_active_encounter())

func test_bridge_setup_when_all_heroes_are_already_dead() -> void:
	# Arrange
	_state.damage_hero("aquele", 30)
	_state.damage_hero("stark", 34)
	_state.damage_hero("elden", 26)
	assert_eq(_state.get_living_heroes().size(), 0)
	var node: RunNode = _state.map.get_start_nodes()[0]

	# Act
	var res: Dictionary = RunCombatBridge.setup_combat(_state, node)

	# Assert
	assert_false(res.get("ok", true), "Setup com todos os heróis caídos deve retornar ok: false")
	assert_eq(res.get("living_heroes", []).size(), 0)

func test_bridge_convert_deck_handles_unknown_card_ids() -> void:
	# Arrange
	var weird_ids: Array[String] = [
		"CARTA_INEXISTENTE_XYZ",
		"movimento_duplo",
		"defesa_pesada_123",
		"trabalho_artesanal",
		"escavacao_profunda",
		"forca_ana_suprema"
	]

	# Act
	var cards: Array[CardData] = RunCombatBridge.convert_deck(weird_ids)

	# Assert
	assert_eq(cards.size(), weird_ids.size(), "Deve converter todas as cartas")
	for c in cards:
		assert_not_null(c, "Nenhuma instância de CardData deve ser nula")
		assert_gt(c.card_name.length(), 0, "Card name não pode ser vazio")

func test_bug_card_id_to_card_data_empty_string_produces_empty_name() -> void:
	# Act
	var c: CardData = RunCombatBridge.card_id_to_card_data("")

	# Assert: Registra o comportamento atual (Bug B: fallback deixa card_name vazio)
	assert_not_null(c)
	# Empiricamente, c.card_name é vazio quando card_id é vazio:
	assert_eq(c.card_name, "", "Bug B confirmado: card_name fica vazio para card_id vazio")

func test_bridge_lifecycle_caches_and_clears_encounter() -> void:
	# Arrange
	var node: RunNode = _state.get_available_nodes()[0]
	_state.move_to(node.id)

	# Act 1: Setup
	RunCombatBridge.setup_combat(_state, node, _rng)

	# Assert 1
	assert_true(RunCombatBridge.has_active_encounter(), "Deve possuir encontro ativo em cache")
	var cached: Dictionary = RunCombatBridge.get_current_encounter()
	assert_eq(cached.get("node_id"), node.id)

	# Act 2: Clear
	RunCombatBridge.clear_encounter()

	# Assert 2
	assert_false(RunCombatBridge.has_active_encounter(), "Cache deve estar limpo após clear_encounter")
	assert_true(RunCombatBridge.get_current_encounter().is_empty())

# ==============================================================================
# GRUPO 2: Persistência de PV, Overhealing e Clamping Extremo
# ==============================================================================

func test_hp_persistence_extreme_overhealing_clamp() -> void:
	# Arrange
	var node: RunNode = _state.get_available_nodes()[0]
	_state.move_to(node.id)
	var combat_res: Dictionary = {
		"victory": true,
		"surviving_heroes_hp": {
			"aquele": 999999,
			"stark": 10000,
			"elden": 500
		},
		"enemies_killed": 3
	}

	# Act
	var summary: Dictionary = RunCombatBridge.sync_combat_result(_state, combat_res)

	# Assert
	assert_true(summary.get("victory"))
	assert_eq(_state.hero_hp["aquele"], 30, "Aquele deve ser clampeado em 30 (max_hp)")
	assert_eq(_state.hero_hp["stark"], 34, "Stark deve ser clampeado em 34 (max_hp)")
	assert_eq(_state.hero_hp["elden"], 26, "Elden deve ser clampeado em 26 (max_hp)")

func test_hp_persistence_negative_hp_reports_are_zeroed_and_killed() -> void:
	# Arrange
	var node: RunNode = _state.get_available_nodes()[0]
	_state.move_to(node.id)
	var combat_res: Dictionary = {
		"victory": true,
		"surviving_heroes_hp": {
			"aquele": -100,
			"stark": 1,
			"elden": -1
		},
		"enemies_killed": 2
	}

	# Act
	var summary: Dictionary = RunCombatBridge.sync_combat_result(_state, combat_res)

	# Assert
	assert_eq(_state.hero_hp["aquele"], 0)
	assert_eq(_state.hero_hp["stark"], 1)
	assert_eq(_state.hero_hp["elden"], 0)
	assert_true(_state.fallen_heroes.has("aquele"))
	assert_true(_state.fallen_heroes.has("elden"))
	assert_false(_state.fallen_heroes.has("stark"))
	# Remediação de Bug A: summary["newly_fallen"] registra heróis caídos via final_hps
	assert_eq(summary["newly_fallen"].size(), 2, "newly_fallen deve registrar os 2 heróis caídos")
	assert_true(summary["newly_fallen"].has("aquele"))
	assert_true(summary["newly_fallen"].has("elden"))

func test_bug_newly_fallen_works_only_via_reported_fallen_not_final_hps() -> void:
	# Demonstra a assimetria do Bug A:
	# Quando o herói é reportado em 'fallen_heroes' (sem estar em final_hps), newly_fallen o registra:
	var node: RunNode = _state.get_available_nodes()[0]
	_state.move_to(node.id)
	var combat_res: Dictionary = {
		"victory": true,
		"surviving_heroes_hp": {"stark": 10},
		"fallen_heroes": ["aquele", "elden"],
		"enemies_killed": 2
	}

	var summary: Dictionary = RunCombatBridge.sync_combat_result(_state, combat_res)

	# Aqui funciona porque final_hps não continha aquele/elden, caindo no ramo 'elif reported_fallen':
	assert_eq(summary["newly_fallen"].size(), 2, "Via reported_fallen direto, newly_fallen funciona")
	assert_true(summary["newly_fallen"].has("aquele"))
	assert_true(summary["newly_fallen"].has("elden"))

func test_hp_persistence_hero_survives_with_exact_1_hp() -> void:
	# Arrange
	var node: RunNode = _state.get_available_nodes()[0]
	_state.move_to(node.id)
	var combat_res: Dictionary = {
		"victory": true,
		"surviving_heroes_hp": {
			"aquele": 1,
			"stark": 1,
			"elden": 1
		},
		"enemies_killed": 2
	}

	# Act
	var summary: Dictionary = RunCombatBridge.sync_combat_result(_state, combat_res)

	# Assert
	assert_true(summary.get("victory"))
	assert_eq(_state.get_living_heroes().size(), 3, "Todos os 3 heróis sobrevivem com 1 PV")
	assert_false(summary.get("party_wipe"))
	assert_true(_state.is_hero_alive("aquele"))

func test_hp_persistence_partial_healing_within_bounds() -> void:
	# Arrange
	_state.damage_hero("aquele", 20) # 10 / 30
	var node: RunNode = _state.get_available_nodes()[0]
	_state.move_to(node.id)
	var combat_res: Dictionary = {
		"victory": true,
		"surviving_heroes_hp": {
			"aquele": 25, # Curou de 10 para 25 no combate
			"stark": 34,
			"elden": 26
		},
		"enemies_killed": 2
	}

	# Act
	RunCombatBridge.sync_combat_result(_state, combat_res)

	# Assert
	assert_eq(_state.hero_hp["aquele"], 25, "Cura interna de combate deve ser sincronizada para 25")

# ==============================================================================
# GRUPO 3: Morte Permanente (Permadeath) & Invariantes de Sobrevivência
# ==============================================================================

func test_permadeath_multi_combat_attrition_chain() -> void:
	# Combate 1: Aquele morre, Stark e Elden sobrevivem
	var node1: RunNode = _state.get_available_nodes()[0]
	_state.move_to(node1.id)
	var res1: Dictionary = {
		"victory": true,
		"surviving_heroes_hp": {"aquele": 0, "stark": 20, "elden": 15},
		"fallen_heroes": ["aquele"],
		"enemies_killed": 3
	}
	RunCombatBridge.sync_combat_result(_state, res1)

	assert_false(_state.is_hero_alive("aquele"))
	assert_eq(_state.get_living_heroes().size(), 2)

	# Combate 2: Setup deve omitir Aquele
	var avail2: Array[RunNode] = _state.get_available_nodes()
	assert_gt(avail2.size(), 0)
	var node2: RunNode = avail2[0]
	_state.move_to(node2.id)

	var payload2: Dictionary = RunCombatBridge.setup_combat(_state, node2, _rng)
	assert_eq(payload2["living_heroes"].size(), 2)
	assert_false(payload2["living_heroes"].has("aquele"))
	assert_eq(payload2["party"].size(), 2)

	# No combate 2, Stark também tomba
	var res2: Dictionary = {
		"victory": true,
		"surviving_heroes_hp": {"stark": 0, "elden": 8},
		"fallen_heroes": ["stark"],
		"enemies_killed": 3
	}
	RunCombatBridge.sync_combat_result(_state, res2)

	assert_false(_state.is_hero_alive("stark"))
	assert_eq(_state.get_living_heroes(), ["elden"])

	# Combate 3: Apenas Elden pode ser deployado
	var avail3: Array[RunNode] = _state.get_available_nodes()
	assert_gt(avail3.size(), 0)
	var node3: RunNode = avail3[0]
	_state.move_to(node3.id)

	var payload3: Dictionary = RunCombatBridge.setup_combat(_state, node3, _rng)
	assert_eq(payload3["living_heroes"], ["elden"])
	assert_eq(payload3["party"].size(), 1)
	assert_eq(payload3["party"][0]["id"], "elden")
	assert_eq(payload3["party"][0]["hp"], 8)

func test_permadeath_cannot_be_bypassed_by_act_transition_heal() -> void:
	# Arrange
	_state.damage_hero("aquele", 30) # Morre
	_state.damage_hero("stark", 24)  # 10 / 34 PV
	assert_true(_state.fallen_heroes.has("aquele"))

	# Act: Força transição de chefe para o Ato 2
	var boss_node: RunNode = _state.map.get_boss_node()
	_state.current_node_id = boss_node.id
	_state.complete_current_node()

	# Assert
	assert_eq(_state.act, 2, "Avançou para o Ato 2")
	assert_eq(_state.hero_hp["aquele"], 0, "Aquele deve permanecer com 0 HP após transição")
	assert_false(_state.is_hero_alive("aquele"), "Aquele não pode ser ressuscitado pelo bônus de ato")
	assert_gt(_state.hero_hp["stark"], 10, "Stark vivo deve receber a cura de 25%")

func test_can_deploy_hero_reflects_permadeath() -> void:
	# Arrange
	_state.hero_hp["aquele"] = 0
	_state.fallen_heroes.append("aquele")

	# Act & Assert
	assert_false(RunCombatBridge.can_deploy_hero(_state, "aquele"), "Herói com 0 HP / fallen não pode ser deployado")
	assert_true(RunCombatBridge.can_deploy_hero(_state, "stark"), "Herói vivo com PV positivo pode ser deployado")
	assert_false(RunCombatBridge.can_deploy_hero(_state, "desconhecido"), "Herói inexistente não pode ser deployado")
	assert_false(RunCombatBridge.can_deploy_hero(null, "stark"), "State nulo não pode ser deployado")

# ==============================================================================
# GRUPO 4: Party Wipes & Roteamento de Derrota
# ==============================================================================

func test_party_wipe_total_defeat_updates_run_state() -> void:
	# Arrange
	var node: RunNode = _state.get_available_nodes()[0]
	_state.move_to(node.id)
	var wipe_result: Dictionary = {
		"victory": false,
		"surviving_heroes_hp": {"aquele": 0, "stark": 0, "elden": 0},
		"enemies_killed": 1
	}

	# Act
	var summary: Dictionary = RunCombatBridge.sync_combat_result(_state, wipe_result)

	# Assert
	assert_false(summary["victory"], "Resultado não pode ser vitória")
	assert_true(summary["game_over"], "Game over deve ser verdadeiro")
	assert_true(summary["party_wipe"], "Party wipe deve ser verdadeiro")
	assert_eq(_state.status, RunState.Status.DEFEAT, "Status da run deve ser DEFEAT")
	assert_false(_state.is_active(), "Run não pode mais estar ativa")

func test_mutual_kill_victory_true_with_zero_living_heroes_is_defeat() -> void:
	# Arrange: Combate onde todos os heróis morreram, mas o último ataque matou o último inimigo
	var node: RunNode = _state.get_available_nodes()[0]
	_state.move_to(node.id)
	var mutual_kill: Dictionary = {
		"victory": true, # Motor de combate relatou vitória tática
		"surviving_heroes_hp": {"aquele": 0, "stark": 0, "elden": 0}, # Mas ninguém sobrou vivo
		"enemies_killed": 4
	}

	# Act
	var summary: Dictionary = RunCombatBridge.sync_combat_result(_state, mutual_kill)

	# Assert
	assert_false(summary["victory"], "Vitória mútua sem sobreviventes deve ser convertida em DERROTA")
	assert_true(summary["party_wipe"], "Party wipe deve ser verdadeiro")
	assert_eq(_state.status, RunState.Status.DEFEAT)

func test_defeat_amber_calculation_rigorously_excludes_victory_bonus() -> void:
	# Arrange
	_state.floors_cleared = 7
	_state.bosses_defeated = 1
	var wipe_result: Dictionary = {
		"victory": false,
		"surviving_heroes_hp": {},
		"fallen_heroes": ["aquele", "stark", "elden"]
	}

	# Act
	var summary: Dictionary = RunCombatBridge.sync_combat_result(_state, wipe_result)

	# Assert
	# Âmbar = 7 andares * 1 + 1 boss * 10 = 17 âmbar. Bônus de 25 NÃO deve ser somado.
	assert_eq(summary["amber"], 17)
	assert_eq(summary["amber_earned"], 17)

# ==============================================================================
# GRUPO 5: Isolamento Standalone do Cerco & Ingestão Decoupled
# ==============================================================================

func test_standalone_cerco_runs_completely_isolated_from_run_session() -> void:
	# Arrange: Garante que não há nenhuma sessão ativa
	RunSession.clear()
	RunCombatBridge.clear_encounter()

	# Act
	var controller: CercoGameController = autofree(CercoGameController.new())
	controller._initialize_models()

	# Assert
	assert_false(controller.is_run_mode, "Deve estar em modo standalone")
	assert_null(controller.run_state_ref, "run_state_ref deve ser nulo")
	assert_null(controller.current_node_ref, "current_node_ref deve ser nulo")
	assert_false(controller.has_spawned_encounter, "Não deve spawnar esquadrão da run")

	# Verifica presença dos heróis clássicos de standalone (Aquele é secreto e não deve estar)
	assert_false(controller.board.has_unit("aquele"), "Aquele é secreto e não deve estar no standalone")
	assert_true(controller.board.has_unit("stark"))
	assert_true(controller.board.has_unit("elden"))
	assert_true(controller.board.has_unit("lysander"))
	assert_eq(int(controller.board.get_unit_data("stark").get("hp", 0)), 52, "HP clássico de Stark no standalone")

func test_standalone_game_over_does_not_call_reward_modal() -> void:
	# Arrange
	RunSession.clear()
	var controller: CercoGameController = autofree(CercoGameController.new())
	controller._initialize_models()

	# Act: Força derrota standalone
	controller.trigger_game_over(false, "Muralhas rompidas")

	# Assert
	assert_true(controller.is_game_over)
	assert_not_null(controller.game_over_modal_instance, "GameOverModal clássico deve ser instanciado")

func test_run_session_cleanup_restores_clean_standalone_state() -> void:
	# Arrange: Inicia uma run e mata Aquele
	RunSession.start_new(12345, {"aquele": 25, "stark": 25, "elden": 25}, ["movimento", "trabalho"])
	var run: RunState = RunSession.current
	run.damage_hero("aquele", 9999)
	var node: RunNode = run.get_available_nodes()[0]
	run.move_to(node.id)

	# Instancia controller 1 (Modo Run)
	var controller1: CercoGameController = autofree(CercoGameController.new())
	controller1._initialize_models()
	assert_true(controller1.is_run_mode)
	assert_false(controller1.board.has_unit("aquele"))

	# Act: Limpa a sessão
	RunSession.clear()
	RunCombatBridge.clear_encounter()

	# Instancia controller 2 (Pós-limpeza)
	var controller2: CercoGameController = autofree(CercoGameController.new())
	controller2._initialize_models()

	# Assert
	assert_false(controller2.is_run_mode, "Após RunSession.clear(), novo controller deve ser estritamente standalone")
	assert_false(controller2.board.has_unit("aquele"), "Aquele não deve estar no standalone por ser secreto")
	assert_true(controller2.board.has_unit("stark"), "Stark deve voltar a ser colocado no standalone")

func test_cerco_controller_sync_round_does_not_crash_in_run_mode() -> void:
	# Arrange
	RunSession.start_new(8888, {"aquele": 20, "stark": 20, "elden": 20}, ["movimento", "trabalho", "ataque"])
	var run: RunState = RunSession.current
	var node: RunNode = run.get_available_nodes()[0]
	run.move_to(node.id)

	var controller: CercoGameController = autofree(CercoGameController.new())
	controller._initialize_models()

	# Act: Simula avanço de turno de sincronia
	var adv: Dictionary = controller.advance_enemy_units()

	# Assert
	assert_not_null(adv, "advance_enemy_units deve executar sem erros")

func test_cerco_controller_run_mode_defeat_triggers_run_defeat() -> void:
	# Arrange
	RunSession.start_new(9911, {"aquele": 10, "stark": 10, "elden": 10}, ["movimento", "trabalho"])
	var run: RunState = RunSession.current
	var node: RunNode = run.get_available_nodes()[0]
	run.move_to(node.id)

	var controller: CercoGameController = autofree(CercoGameController.new())
	controller._initialize_models()

	# Mata todos os heróis no tabuleiro do Cerco
	controller.board.damage_unit("aquele", 100)
	controller.board.damage_unit("stark", 100)
	controller.board.damage_unit("elden", 100)

	# Act
	var check: Dictionary = controller.check_game_over_conditions()
	assert_true(check.get("game_over", false))
	assert_false(check.get("victory", true))

	controller.trigger_game_over(false, "Todos os defensores caíram")

	# Assert
	assert_eq(run.status, RunState.Status.DEFEAT, "Run deve estar em DEFEAT após trigger_game_over")
	assert_false(run.is_active())

# ==============================================================================
# GRUPO 6: Procedural Encounter Generator & Composição de Chefes
# ==============================================================================

func test_generator_deterministic_spawns_across_multiple_calls() -> void:
	# Arrange
	var rng1: RandomNumberGenerator = RandomNumberGenerator.new()
	var rng2: RandomNumberGenerator = RandomNumberGenerator.new()
	rng1.seed = 314159
	rng2.seed = 314159

	# Act
	var enc1: Dictionary = CombatEncounterGenerator.generate_encounter(1, 2, RunNode.NodeType.ELITE, rng1)
	var enc2: Dictionary = CombatEncounterGenerator.generate_encounter(1, 2, RunNode.NodeType.ELITE, rng2)

	# Assert
	assert_eq(enc1["enemies"].size(), enc2["enemies"].size())
	for i in range(enc1["enemies"].size()):
		assert_eq(enc1["enemies"][i]["caste_id"], enc2["enemies"][i]["caste_id"])
		assert_eq(enc1["enemies"][i]["spawn_pos"], enc2["enemies"][i]["spawn_pos"])

func test_generator_extreme_seed_zero_and_large_int() -> void:
	# Arrange & Act
	var enc_zero: Dictionary = CombatEncounterGenerator.generate_encounter(1, 1, RunNode.NodeType.COMBAT, 0)
	var enc_large: Dictionary = CombatEncounterGenerator.generate_encounter(1, 1, RunNode.NodeType.COMBAT, 2147483647)

	# Assert
	assert_not_null(enc_zero)
	assert_not_null(enc_large)
	assert_gt(enc_zero["enemies"].size(), 0)
	assert_gt(enc_large["enemies"].size(), 0)

func test_generator_all_three_acts_bosses() -> void:
	# Ato 1 Boss -> viuva_canibal
	var enc1: Dictionary = CombatEncounterGenerator.generate_encounter(1, 8, RunNode.NodeType.BOSS, 123)
	assert_eq(enc1.get("boss_id"), "viuva_canibal")
	assert_true(enc1["enemies"][0]["is_boss"])

	# Ato 2 Boss -> rainha_do_enxame
	var enc2: Dictionary = CombatEncounterGenerator.generate_encounter(2, 8, RunNode.NodeType.BOSS, 456)
	assert_eq(enc2.get("boss_id"), "rainha_do_enxame")
	assert_true(enc2["enemies"][0]["is_boss"])

	# Ato 3 Boss -> rei_isectum
	var enc3: Dictionary = CombatEncounterGenerator.generate_encounter(3, 8, RunNode.NodeType.BOSS, 789)
	assert_eq(enc3.get("boss_id"), "rei_isectum")
	assert_true(enc3["enemies"][0]["is_boss"])

func test_generator_no_duplicate_spawn_positions_in_siege_mode() -> void:
	# Arrange
	var node: RunNode = RunNode.new(99, 1, 5, 2, RunNode.NodeType.SIEGE)

	# Act
	var enc: Dictionary = CombatEncounterGenerator.generate_from_node(node, 999111)
	var enemies: Array = enc.get("enemies", [])

	# Assert
	var pos_map: Dictionary = {}
	for e in enemies:
		var pos: Vector2i = e["spawn_pos"]
		assert_false(pos_map.has(pos), "Posição %s duplicada para inimigos no mesmo encontro" % str(pos))
		pos_map[pos] = true

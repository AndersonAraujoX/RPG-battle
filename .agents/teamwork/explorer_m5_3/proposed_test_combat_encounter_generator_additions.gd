# res://test/unit/proposed_test_combat_encounter_generator_additions.gd
## Adições de testes para test_combat_encounter_generator.gd (Marco M5 - Ato II)

func test_combat_node_act2_squad_and_cocoons() -> void:
	# Arrange
	var node: RunNode = RunNode.new(10, 2, 2, 0, RunNode.NodeType.COMBAT)

	# Act
	var enc: Dictionary = CombatEncounterGenerator.generate_from_node(node, 2024)
	var enemies: Array = enc.get("enemies", [])
	var cocoons: Array = enc.get("cocoons", [])

	# Assert
	assert_gte(enemies.size(), 3, "Combate Ato 2 possui pelo menos 3 inimigos")
	assert_gt(cocoons.size(), 0, "Combate Ato 2 deve gerar casulos de quitina (ChitinCocoon)")

	var has_tier2: bool = false
	for e in enemies:
		var cid: String = str(e["caste_id"])
		if cid in [
			IsectumCastes.ID_VESPA_FURTIVA,
			IsectumCastes.ID_LOUVA_DEUS_CEIFADOR,
			IsectumCastes.ID_CENTOPEIA_VENENOSA,
			IsectumCastes.ID_LIBELULA_BOMBARDEIRA,
			IsectumCastes.ID_VAGALUME_CEGO,
			IsectumCastes.ID_ARANHA_SALTADORA
		]:
			has_tier2 = true
			break
	assert_true(has_tier2, "Ato 2 introduz castas Tier 2")

	for c in cocoons:
		assert_eq(c["type"], "COCOON", "Tipo de estrutura deve ser COCOON")
		assert_eq(c["hp"], 15, "Casulo possui 15 PV")
		assert_eq(c["turns_remaining"], 3, "Casulo possui 3 turnos para eclosão")

func test_siege_node_act2_squad_and_cocoons() -> void:
	# Arrange
	var node: RunNode = RunNode.new(11, 2, 4, 1, RunNode.NodeType.SIEGE)

	# Act
	var enc: Dictionary = CombatEncounterGenerator.generate_from_node(node, 3030)
	var enemies: Array = enc.get("enemies", [])
	var cocoons: Array = enc.get("cocoons", [])

	# Assert
	assert_gte(enemies.size(), 4, "Cerco Ato 2 tem pelo menos 4 invasores")
	assert_true(enc["rules"]["is_siege_mode"], "is_siege_mode deve ser verdadeiro")
	assert_gt(cocoons.size(), 0, "Cerco Ato 2 deve conter casulos")

func test_elite_node_act2_generates_cigarra_ressonante() -> void:
	# Arrange
	var node: RunNode = RunNode.new(12, 2, 6, 2, RunNode.NodeType.ELITE)

	# Act
	var enc: Dictionary = CombatEncounterGenerator.generate_from_node(node, 7777)
	var enemies: Array = enc.get("enemies", [])
	var cocoons: Array = enc.get("cocoons", [])

	# Assert
	assert_gt(enemies.size(), 0)
	var leader: Dictionary = enemies[0]
	assert_true(leader["is_elite"], "Primeira unidade deve ser líder de elite")
	assert_eq(leader["caste_id"], IsectumCastes.ID_GRILO_ATORDOANTE, "Líder de elite do Ato 2 é Cigarra Ressonante")
	assert_eq(leader["trait_id"], "pulso_sonico", "Habilidade do líder de elite é pulso_sonico")
	assert_gte(int(leader["hp"]), 80, "Cigarra Ressonante possui PV de mini-boss (>= 80)")
	assert_eq(leader["symbol"], "🦗", "Símbolo da Cigarra é 🦗")
	assert_true(enc["rewards"]["guaranteed_relic"], "Nó de Elite garante relíquia")
	assert_gt(cocoons.size(), 0, "Elite do Ato 2 possui casulos")

func test_boss_node_act2_generates_rainha_do_enxame_with_royal_guards() -> void:
	# Arrange
	var node: RunNode = RunNode.new(13, 2, 11, 0, RunNode.NodeType.BOSS)

	# Act
	var enc: Dictionary = CombatEncounterGenerator.generate_from_node(node, 8888)
	var enemies: Array = enc.get("enemies", [])
	var cocoons: Array = enc.get("cocoons", [])

	# Assert
	assert_eq(enc.get("boss_id", ""), "rainha_do_enxame", "Chefe do Ato 2 é Rainha do Enxame")
	assert_true(enc["rules"]["has_royal_guards"], "Encontro possui guardas reais")
	assert_not_empty(enc["rules"]["transition_hook"], "Possui gancho narrativo de transição")

	var boss: Dictionary = enemies[0]
	assert_true(boss["is_boss"], "Primeira unidade é chefe")
	assert_eq(boss["caste_id"], IsectumCastes.ID_RAINHA_DO_ENXAME)
	assert_gte(int(boss["hp"]), 180, "Rainha possui PV elevado de boss de Ato (>= 180)")
	assert_eq(boss["trait_id"], "chamado_da_rainha", "Trait da Rainha é chamado_da_rainha")

	# Verifica presença das Guardas Reais na escolta
	var guard_count: int = 0
	for e in enemies:
		if bool(e.get("is_royal_guard", false)):
			guard_count += 1
	assert_gte(guard_count, 2, "Rainha do Enxame deve ter pelo menos 2 Guardas Reais de escolta inicial")
	assert_gt(cocoons.size(), 0, "Câmara da Rainha possui casulos iniciais")

func test_act2_spatial_anti_collision_between_units_and_cocoons() -> void:
	# Arrange
	var node: RunNode = RunNode.new(14, 2, 7, 1, RunNode.NodeType.COMBAT)

	# Act
	var enc: Dictionary = CombatEncounterGenerator.generate_from_node(node, 9999)
	var enemies: Array = enc.get("enemies", [])
	var cocoons: Array = enc.get("cocoons", [])

	# Assert
	var occupied_positions: Dictionary = {}
	for u in enemies:
		var p: Vector2i = u["spawn_pos"]
		assert_false(occupied_positions.has(p), "Nenhuma unidade pode colidir na mesma célula: %s" % str(p))
		occupied_positions[p] = "unit"

	for c in cocoons:
		var p: Vector2i = c["pos"]
		assert_false(occupied_positions.has(p), "Casulo não pode sobrepor unidade ou outro casulo: %s" % str(p))
		occupied_positions[p] = "cocoon"

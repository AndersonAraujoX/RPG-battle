# res://test/unit/test_combat_encounter_generator.gd
extends GutTest

## Suíte de Testes Unitários: Gerador de Encontros de Combate (CombatEncounterGenerator)
## Marco M4: Valida determinismo por seed, composição por nós/Atos, chefes e perigos.
## Segue o padrão estrito Arrange-Act-Assert (AAA) e prevenção de memory leaks.

var _gen: CombatEncounterGenerator
var _rng: RandomNumberGenerator

func before_each() -> void:
	_gen = CombatEncounterGenerator.new()
	_rng = RandomNumberGenerator.new()
	_rng.seed = 98765

func after_each() -> void:
	_gen = null
	_rng = null

# ── 1. Inicialização & Segurança Headless ─────────────────────────────────────

func test_generator_initialization() -> void:
	# Arrange & Act & Assert
	assert_not_null(_gen, "Gerador deve instanciar com sucesso")

func test_generator_safe_fallback_on_invalid_inputs() -> void:
	# Arrange & Act
	var enc: Dictionary = _gen.generate_encounter(-1, -1, -1, null)

	# Assert
	assert_not_null(enc, "Encontro gerado não deve ser nulo")
	assert_true(enc.has("enemies"), "Deve conter chave 'enemies'")
	assert_true(enc.has("squad"), "Deve conter chave 'squad'")
	assert_gt(enc["enemies"].size(), 0, "Deve gerar fallback com pelo menos 1 inimigo básico")

# ── 2. Determinismo via Seed ──────────────────────────────────────────────────

func test_generator_determinism_with_same_seed() -> void:
	# Arrange
	var rng1: RandomNumberGenerator = RandomNumberGenerator.new()
	var rng2: RandomNumberGenerator = RandomNumberGenerator.new()
	rng1.seed = 5555
	rng2.seed = 5555

	# Act
	var enc1: Dictionary = _gen.generate_encounter(1, 3, RunNode.NodeType.COMBAT, rng1)
	var enc2: Dictionary = _gen.generate_encounter(1, 3, RunNode.NodeType.COMBAT, rng2)

	# Assert
	assert_eq(enc1["enemies"].size(), enc2["enemies"].size(), "Tamanho do esquadrão idêntico")
	for i in range(enc1["enemies"].size()):
		assert_eq(enc1["enemies"][i]["caste_id"], enc2["enemies"][i]["caste_id"], "Casta idêntica na posição %d" % i)
		assert_eq(enc1["enemies"][i]["spawn_pos"], enc2["enemies"][i]["spawn_pos"], "Posição idêntica na posição %d" % i)
		assert_eq(enc1["enemies"][i]["target_zone"], enc2["enemies"][i]["target_zone"], "Zona alvo idêntica na posição %d" % i)

# ── 3. Composição de Esquadrão no Ato 1 ──────────────────────────────────────

func test_combat_node_act1_squad_size_and_basic_castes() -> void:
	# Arrange
	var node: RunNode = RunNode.new(1, 1, 0, 0, RunNode.NodeType.COMBAT)

	# Act
	var enc: Dictionary = CombatEncounterGenerator.generate_from_node(node, 1234)
	var enemies: Array = enc.get("enemies", [])

	# Assert
	assert_gte(enemies.size(), 3, "COMBAT regular tem pelo menos 3 inimigos")
	assert_lte(enemies.size(), 4, "COMBAT regular tem no máximo 4 inimigos")
	assert_false(enc["rules"]["is_siege_mode"], "COMBAT comum não é modo cerco")
	assert_false(enc["rewards"]["guaranteed_relic"], "COMBAT comum não garante relíquia")

	for e in enemies:
		var cid: String = str(e["caste_id"])
		assert_true(
			cid in [
				"zangao_invasor", "soldado_mandibula", "operario_escavador",
				"formiga_acida", "barata_praga", "larva_necrotica", "cupim_roedor"
			],
			"Casta %s deve ser do pool Tier 1" % cid
		)

func test_siege_node_act1_has_siege_castes_and_larger_squad() -> void:
	# Arrange
	var node: RunNode = RunNode.new(2, 1, 3, 1, RunNode.NodeType.SIEGE)

	# Act
	var enc: Dictionary = CombatEncounterGenerator.generate_from_node(node, 5678)
	var enemies: Array = enc.get("enemies", [])

	# Assert
	assert_gte(enemies.size(), 4, "SIEGE tem pelo menos 4 inimigos")
	assert_lte(enemies.size(), 6, "SIEGE tem no máximo 6 inimigos")
	assert_true(enc["rules"]["is_siege_mode"], "is_siege_mode deve ser verdadeiro")

	var has_siege_unit: bool = false
	for e in enemies:
		var cid: String = str(e["caste_id"])
		if bool(e.get("is_siege", false)) or cid in [
			IsectumCastes.ID_OPERARIO_ESCAVADOR,
			IsectumCastes.ID_BESOURO_RINOCERONTE,
			IsectumCastes.ID_ESCARAVELHO_COURACADO,
			IsectumCastes.ID_CUPIM_ROEDOR
		]:
			has_siege_unit = true
			break
	assert_true(has_siege_unit, "SIEGE deve conter pelo menos uma casta especializada em cerco")

func test_elite_node_act1_contains_heavy_leader_and_guarantees_relic() -> void:
	# Arrange
	var node: RunNode = RunNode.new(3, 1, 5, 2, RunNode.NodeType.ELITE)

	# Act
	var enc: Dictionary = CombatEncounterGenerator.generate_from_node(node, 9999)
	var enemies: Array = enc.get("enemies", [])

	# Assert
	assert_gte(enemies.size(), 3, "ELITE deve ter líder e escolta (>= 3)")
	assert_true(enc["rewards"]["guaranteed_relic"], "Nó Elite deve garantir relíquia")

	var leader: Dictionary = enemies[0]
	assert_true(leader["is_elite"], "Primeira unidade deve ser líder de elite")
	assert_gte(int(leader["hp"]), 18, "Líder de elite possui PV elevado (>= 18)")
	assert_true(
		leader["caste_id"] in [IsectumCastes.ID_ESCARAVELHO_COURACADO, IsectumCastes.ID_COLOSSO_ISECTUM],
		"Líder deve ser couraçado ou colosso"
	)

func test_boss_node_act1_generates_viuva_canibal() -> void:
	# Arrange
	var node: RunNode = RunNode.new(4, 1, 11, 0, RunNode.NodeType.BOSS)

	# Act
	var enc: Dictionary = CombatEncounterGenerator.generate_from_node(node, 4321)

	# Assert
	assert_eq(enc.get("boss_id", ""), "viuva_canibal", "Chefe do Ato 1 é Viúva Canibal")
	var enemies: Array = enc.get("enemies", [])
	assert_gt(enemies.size(), 0)

	var boss: Dictionary = enemies[0]
	assert_true(boss["is_boss"], "Primeira unidade é chefe")
	assert_eq(boss["caste_id"], IsectumCastes.ID_TECE_TEIA)
	assert_gte(int(boss["hp"]), 60, "Viúva Canibal possui PV elevado de chefe (>= 60)")

	var hazards: Array = enc.get("hazards", [])
	assert_gt(hazards.size(), 0, "Encontro com Viúva Canibal deve gerar perigos de teia")
	for h in hazards:
		assert_eq(h["type"], "WEB", "Tipo de perigo deve ser WEB")
		assert_true(h.has("pos"), "Perigo deve conter coordenada de grade")

# ── 4. Escalonamento por Ato ────────────────────────────────────────────────

func test_combat_node_act2_includes_tier2_castes() -> void:
	# Arrange & Act
	var enc: Dictionary = _gen.generate_encounter(2, 2, RunNode.NodeType.COMBAT, _rng)
	var enemies: Array = enc.get("enemies", [])

	# Assert
	assert_gt(enemies.size(), 0)
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
	assert_true(has_tier2, "Ato 2 deve introduzir castas Tier 2")

func test_boss_node_act2_generates_rainha_do_enxame() -> void:
	# Arrange & Act
	var enc: Dictionary = _gen.generate_encounter(2, 11, RunNode.NodeType.BOSS, _rng)

	# Assert
	assert_eq(enc.get("boss_id", ""), "rainha_do_enxame", "Chefe do Ato 2 é Rainha do Enxame")
	var boss: Dictionary = enc["enemies"][0]
	assert_true(boss["is_boss"])
	assert_eq(boss["caste_id"], IsectumCastes.ID_RAINHA_DO_ENXAME)
	assert_gte(int(boss["hp"]), 80)

func test_boss_node_act3_generates_rei_isectum() -> void:
	# Arrange & Act
	var enc: Dictionary = _gen.generate_encounter(3, 11, RunNode.NodeType.BOSS, _rng)

	# Assert
	assert_eq(enc.get("boss_id", ""), "rei_isectum", "Chefe do Ato 3 é Rei Isectum")
	var boss: Dictionary = enc["enemies"][0]
	assert_true(boss["is_boss"])
	assert_eq(boss["caste_id"], IsectumCastes.ID_COLOSSO_ISECTUM)
	assert_gte(int(boss["hp"]), 100)

# ── 5. Integridade do Catálogo & Anticolisão ──────────────────────────────────

func test_generated_enemies_have_valid_caste_data() -> void:
	# Arrange & Act
	var enc: Dictionary = _gen.generate_encounter(1, 1, RunNode.NodeType.COMBAT, _rng)

	# Assert
	for e in enc["enemies"]:
		var cid: String = str(e["caste_id"])
		var caste: IsectumCasteData = IsectumCastes.get_caste(cid)
		assert_not_null(caste, "Casta %s deve existir no catálogo IsectumCastes" % cid)
		assert_gt(int(e["hp"]), 0, "HP deve ser positivo")
		assert_gt(int(e["ac"]), 0, "CA deve ser positiva")
		assert_gt(int(e["move_range"]), 0, "Deslocamento deve ser positivo")

func test_spawn_zones_are_valid_perimeter_zones() -> void:
	# Arrange & Act
	var enc: Dictionary = _gen.generate_encounter(1, 1, RunNode.NodeType.COMBAT, _rng)
	var valid_zones: Array[String] = [
		FortressBoard.ZONE_SPAWN_NORTE,
		FortressBoard.ZONE_SPAWN_SUL,
		FortressBoard.ZONE_SPAWN_LESTE,
		FortressBoard.ZONE_SPAWN_OESTE
	]

	# Assert
	for e in enc["enemies"]:
		var z: String = str(e.get("target_zone", ""))
		assert_true(z in valid_zones, "Zona de spawn %s deve ser um dos 4 perímetros externos" % z)

func test_spatial_anti_collision_guarantee() -> void:
	# Arrange
	var node: RunNode = RunNode.new(8, 1, 4, 1, RunNode.NodeType.SIEGE)

	# Act
	var enc: Dictionary = CombatEncounterGenerator.generate_from_node(node, 10101)

	# Assert
	var positions_seen: Dictionary = {}
	var squad: Array = enc.get("enemies", [])
	for u in squad:
		var p: Vector2i = u["spawn_pos"]
		assert_false(positions_seen.has(p), "Nenhum par de inimigos pode colidir na mesma célula: %s" % str(p))
		assert_true(p.x >= 0 and p.x < 20 and p.y >= 0 and p.y < 20, "Posição deve estar contida na grade 20x20")
		positions_seen[p] = true

# ── 6. Encontros do Ato 2 (Túneis Vivos) & Anticolisão de Casulos ─────────────

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
	assert_ne(String(enc["rules"]["transition_hook"]), "", "Possui gancho narrativo de transição")

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


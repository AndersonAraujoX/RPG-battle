# res://scripts/run/combat/CombatEncounterGenerator.gd
class_name CombatEncounterGenerator
extends RefCounted

## CombatEncounterGenerator: Gerador procedural de encontros de combate tático
## para a Campanha Roguelike (Marcos M4 & M5). Deterministicamente cria esquadrões
## inimigos, chefes de Ato (Viúva Canibal, Rainha do Enxame, Rei Isectum),
## perigos ambientais de teia, casulos de quitina e regras de recompensa com base no Ato, andar e tipo de nó.

# ── Apelidos Canônicos de Castas ─────────────────────────────────────────────
const CASTE_ALIASES: Dictionary = {
	"larva_carniceira": IsectumCastes.ID_LARVA_NECROTICA,
	"besouro_gorgulho": IsectumCastes.ID_CUPIM_ROEDOR,
	"gafanhoto_praga": IsectumCastes.ID_BARATA_PRAGA,
	"viuva_canibal": IsectumCastes.ID_TECE_TEIA,
	"tarantula_golias": IsectumCastes.ID_COLOSSO_ISECTUM,
	"formiga_correicao": IsectumCastes.ID_FORMIGA_ACIDA,
	"escaravelho_necrofago": IsectumCastes.ID_ESCARAVELHO_COURACADO,
	"cigarra_ressonante": IsectumCastes.ID_GRILO_ATORDOANTE,
	"batedor": IsectumCastes.ID_ZANGAO_INVASOR,
	"soldado": IsectumCastes.ID_SOLDADO_MANDIBULA,
	"operario": IsectumCastes.ID_OPERARIO_ESCAVADOR,
	"besouro": IsectumCastes.ID_BESOURO_RINOCERONTE,
	"rei_isectum": IsectumCastes.ID_COLOSSO_ISECTUM,
	"louva_deus_ceifador": IsectumCastes.ID_LOUVA_DEUS_CEIFADOR,
	"vespa_cacadora": IsectumCastes.ID_VESPA_FURTIVA,
	"aranha_clepto": IsectumCastes.ID_ARANHA_SALTADORA,
	"libelula_blindada": IsectumCastes.ID_LIBELULA_BOMBARDEIRA,
	"infiltrador": IsectumCastes.ID_BICHO_PAU_EMBOSCADOR,
	"vagalume_sombras": IsectumCastes.ID_VAGALUME_CEGO,
	"rainha_do_enxame": IsectumCastes.ID_RAINHA_DO_ENXAME,
	"guarda_real": IsectumCastes.ID_ESCARAVELHO_COURACADO,
}

# ── Pools de Castas por Ato ───────────────────────────────────────────────────
const ACT_1_COMBAT_POOL: Array[String] = [
	"larva_carniceira",
	"formiga_acida",
	"besouro_gorgulho",
	"gafanhoto_praga",
	IsectumCastes.ID_ZANGAO_INVASOR,
	IsectumCastes.ID_SOLDADO_MANDIBULA,
	IsectumCastes.ID_OPERARIO_ESCAVADOR,
]

const ACT_1_SIEGE_POOL: Array[String] = [
	"besouro_gorgulho",
	IsectumCastes.ID_OPERARIO_ESCAVADOR,
	IsectumCastes.ID_BESOURO_RINOCERONTE,
	IsectumCastes.ID_ESCARAVELHO_COURACADO,
	"formiga_acida",
	IsectumCastes.ID_SOLDADO_MANDIBULA,
]

const ACT_1_ELITE_LEADERS: Array[String] = [
	IsectumCastes.ID_ESCARAVELHO_COURACADO,
	"tarantula_golias",
]

const ACT_2_COMBAT_POOL: Array[String] = [
	IsectumCastes.ID_VESPA_FURTIVA,
	IsectumCastes.ID_LOUVA_DEUS_CEIFADOR,
	IsectumCastes.ID_CENTOPEIA_VENENOSA,
	IsectumCastes.ID_LIBELULA_BOMBARDEIRA,
	IsectumCastes.ID_VAGALUME_CEGO,
	IsectumCastes.ID_ARANHA_SALTADORA,
]

const ACT_2_SIEGE_POOL: Array[String] = [
	IsectumCastes.ID_LIBELULA_BOMBARDEIRA,
	IsectumCastes.ID_OPERARIO_ESCAVADOR,
	IsectumCastes.ID_BESOURO_RINOCERONTE,
	IsectumCastes.ID_LOUVA_DEUS_CEIFADOR,
	IsectumCastes.ID_VESPA_FURTIVA,
	IsectumCastes.ID_ESCARAVELHO_COURACADO,
]

const ACT_2_ELITE_LEADERS: Array[String] = [
	"cigarra_ressonante",
]

const ACT_3_COMBAT_POOL: Array[String] = [
	IsectumCastes.ID_ESCARAVELHO_COURACADO,
	IsectumCastes.ID_COLOSSO_ISECTUM,
	IsectumCastes.ID_CENTOPEIA_VENENOSA,
	IsectumCastes.ID_LOUVA_DEUS_CEIFADOR,
]

# ── API Pública do Gerador ───────────────────────────────────────────────────

## Gera o dicionário de encontro completo a partir de um RunNode.
static func generate_from_node(node: RunNode, seed_or_rng: Variant = null) -> Dictionary:
	if node == null:
		push_error("[CombatEncounterGenerator] Nó nulo recebido")
		return generate_encounter(1, 0, RunNode.NodeType.COMBAT, -1, seed_or_rng)
	return generate_encounter(node.act, node.floor_index, node.type, node.id, seed_or_rng)

## Gera o dicionário de encontro suportando múltiplas assinaturas polimórficas:
## 1) (node: RunNode, seed_or_rng: Variant = null)
## 2) (node: RunNode, floor_index: int, custom_rng: RandomNumberGenerator)
## 3) (act: int, floor_index: int, node_type: int, rng: RandomNumberGenerator)
## 4) (act: int, floor_index: int, node_type: int, node_id: int, seed_or_rng: Variant)
static func generate_encounter(
	act_or_node: Variant,
	floor_index: Variant = null,
	node_type: int = 0,
	p4: Variant = null,
	p5: Variant = null
) -> Dictionary:
	var act: int = 1
	var floor_idx: int = 0
	var ntype: int = RunNode.NodeType.COMBAT
	var node_id: int = -1
	var seed_or_rng: Variant = null

	if act_or_node is RunNode:
		var n: RunNode = act_or_node as RunNode
		act = n.act
		floor_idx = n.floor_index
		ntype = n.type
		node_id = n.id
		if p4 != null:
			if floor_index != null and (floor_index is int or floor_index is float):
				floor_idx = int(floor_index)
			seed_or_rng = p4
		else:
			seed_or_rng = floor_index
	else:
		act = int(act_or_node) if act_or_node != null else 1
		floor_idx = int(floor_index) if floor_index != null else 0
		ntype = node_type
		if p5 != null:
			node_id = int(p4)
			seed_or_rng = p5
		elif p4 is RandomNumberGenerator or (p4 != null and not (p4 is int)):
			node_id = -1
			seed_or_rng = p4
		elif p4 is int:
			node_id = int(p4)
			seed_or_rng = int(p4)
		else:
			node_id = -1
			seed_or_rng = null

	# Validação defensiva com safe fallbacks
	var safe_act: int = clampi(act, 1, 3) if act > 0 else 1
	var safe_floor: int = maxi(0, floor_idx)
	var safe_type: int = ntype if ntype in [
		RunNode.NodeType.COMBAT,
		RunNode.NodeType.SIEGE,
		RunNode.NodeType.ELITE,
		RunNode.NodeType.BOSS
	] else RunNode.NodeType.COMBAT

	var rng: RandomNumberGenerator = _resolve_rng(seed_or_rng, safe_act, safe_floor, node_id)

	var squad: Array[Dictionary] = []
	var hazards: Array[Dictionary] = []
	var cocoons: Array[Dictionary] = []
	var forced_waves: Array[Dictionary] = []
	var occupied_cells: Dictionary = {}
	var encounter_name: String = ""
	var rules: Dictionary = {
		"max_rounds": 10,
		"objective": "defeat_all",
		"is_siege_mode": false,
		"boss_id": "",
		"can_flee": false,
		"has_royal_guards": false,
		"transition_hook": ""
	}
	var rewards: Dictionary = {
		"base_gold": 15,
		"gold_min": 12,
		"gold_max": 18,
		"card_draft_count": 3,
		"guaranteed_relic": false,
		"relic_pool": "standard",
		"amber_reward": 0
	}

	match safe_type:
		RunNode.NodeType.COMBAT:
			encounter_name = "Combate Tático: Enxame Isectum (Ato %d)" % safe_act
			squad = _generate_combat_squad(safe_act, safe_floor, rng, occupied_cells)
			rewards["base_gold"] = 15 + safe_floor
			rewards["gold_min"] = maxi(10, rewards["base_gold"] - 3)
			rewards["gold_max"] = rewards["base_gold"] + 4

		RunNode.NodeType.SIEGE:
			encounter_name = "Cerco ao Posto Avançado (Ato %d)" % safe_act
			squad = _generate_siege_squad(safe_act, safe_floor, rng, occupied_cells)
			rules["is_siege_mode"] = true
			rules["objective"] = "survive_siege"
			rewards["base_gold"] = 22 + safe_floor * 2
			rewards["gold_min"] = rewards["base_gold"] - 4
			rewards["gold_max"] = rewards["base_gold"] + 5

		RunNode.NodeType.ELITE:
			encounter_name = "Inimigo de Elite Isectum (Ato %d)" % safe_act
			squad = _generate_elite_squad(safe_act, safe_floor, rng, occupied_cells)
			rules["objective"] = "defeat_elite"
			rewards["base_gold"] = 35 + safe_floor * 2
			rewards["gold_min"] = rewards["base_gold"] - 5
			rewards["gold_max"] = rewards["base_gold"] + 8
			rewards["guaranteed_relic"] = true
			rewards["relic_pool"] = "elite"

		RunNode.NodeType.BOSS:
			squad = _generate_boss_squad(safe_act, safe_floor, rng, rules, occupied_cells)
			if safe_act == 1:
				encounter_name = "Covil da Viúva Canibal (Chefe do Ato I)"
				hazards = _generate_boss_web_hazards(rng)
			elif safe_act == 2:
				encounter_name = "Câmara da Rainha do Enxame (Chefe do Ato II)"
			else:
				encounter_name = "Trono de Âmbar do Rei Isectum (Chefe Final)"

			rules["objective"] = "kill_boss"
			rules["max_rounds"] = 15
			rewards["base_gold"] = 50
			rewards["gold_min"] = 45
			rewards["gold_max"] = 60
			rewards["guaranteed_relic"] = true
			rewards["relic_pool"] = "boss"
			rewards["amber_reward"] = 10

	# Ato II: Integração de Casulos de Quitina (ChitinCocoon)
	if safe_act == 2:
		cocoons = _generate_act2_cocoons(safe_type, rng, occupied_cells)
		# Anexa casulos como perigos interativos para compatibilidade com sistemas legados
		for c in cocoons:
			hazards.append(c)

	# Constrói ondas forçadas correspondentes para o ThreatDeck
	forced_waves = _build_forced_waves_from_squad(squad, safe_type)

	var enc_id: String = "encounter_a%d_f%d_n%d" % [safe_act, safe_floor, node_id]
	return {
		"encounter_id": enc_id,
		"encounter_name": encounter_name,
		"act": safe_act,
		"floor": safe_floor,
		"node_id": node_id,
		"node_type": safe_type,
		"squad": squad,
		"enemies": squad, # Aliás canônico para conveniência e testes GUT
		"hazards": hazards,
		"cocoons": cocoons,
		"rules": rules,
		"boss_id": rules.get("boss_id", ""),
		"rewards": rewards,
		"forced_waves": forced_waves
	}

# ── Geração de Esquadrões ───────────────────────────────────────────────────

static func _generate_combat_squad(act: int, floor_index: int, rng: RandomNumberGenerator, occupied: Dictionary = {}) -> Array[Dictionary]:
	var squad: Array[Dictionary] = []
	var count: int = 3
	if floor_index >= 3:
		count = rng.randi_range(3, 4)

	var unit_index: int = 1

	if act == 1:
		# Garante pelo menos 1 corpo-a-corpo e 1 à distância/flanqueador
		var melee_castes: Array[String] = ["larva_carniceira", IsectumCastes.ID_SOLDADO_MANDIBULA, "besouro_gorgulho"]
		var ranged_castes: Array[String] = ["formiga_acida", "gafanhoto_praga", IsectumCastes.ID_ZANGAO_INVASOR]

		var selected: Array[String] = []
		selected.append(melee_castes[rng.randi() % melee_castes.size()])
		selected.append(ranged_castes[rng.randi() % ranged_castes.size()])

		while selected.size() < count:
			selected.append(ACT_1_COMBAT_POOL[rng.randi() % ACT_1_COMBAT_POOL.size()])

		for raw_id in selected:
			var pos: Vector2i = _pick_spawn_cell(rng, occupied)
			var u: Dictionary = _create_unit_dict(raw_id, "combat_%d" % unit_index, pos, act, floor_index, false, false)
			squad.append(u)
			unit_index += 1
	elif act == 2:
		var selected: Array[String] = []
		# Garante pelo menos uma casta Tier 2
		selected.append(ACT_2_COMBAT_POOL[rng.randi() % ACT_2_COMBAT_POOL.size()])
		while selected.size() < count:
			selected.append(ACT_2_COMBAT_POOL[rng.randi() % ACT_2_COMBAT_POOL.size()])

		for raw_id in selected:
			var pos: Vector2i = _pick_spawn_cell(rng, occupied)
			var u: Dictionary = _create_unit_dict(raw_id, "combat_a2_%d" % unit_index, pos, act, floor_index, false, false)
			squad.append(u)
			unit_index += 1
	else:
		for i in range(count):
			var raw_id: String = ACT_3_COMBAT_POOL[rng.randi() % ACT_3_COMBAT_POOL.size()]
			var pos: Vector2i = _pick_spawn_cell(rng, occupied)
			var u: Dictionary = _create_unit_dict(raw_id, "combat_a3_%d" % unit_index, pos, act, floor_index, false, false)
			squad.append(u)
			unit_index += 1

	return squad

static func _generate_siege_squad(act: int, floor_index: int, rng: RandomNumberGenerator, occupied: Dictionary = {}) -> Array[Dictionary]:
	var squad: Array[Dictionary] = []
	var count: int = rng.randi_range(4, 5) if floor_index < 5 else rng.randi_range(5, 6)
	var unit_index: int = 1

	var sapper_castes: Array[String] = [IsectumCastes.ID_OPERARIO_ESCAVADOR, "besouro_gorgulho"]
	var heavy_castes: Array[String] = [IsectumCastes.ID_ESCARAVELHO_COURACADO, IsectumCastes.ID_BESOURO_RINOCERONTE]

	var selected: Array[String] = []
	selected.append(sapper_castes[rng.randi() % sapper_castes.size()])
	selected.append(sapper_castes[rng.randi() % sapper_castes.size()])
	selected.append(heavy_castes[rng.randi() % heavy_castes.size()])

	var pool: Array[String] = ACT_1_SIEGE_POOL if act == 1 else ACT_2_SIEGE_POOL
	while selected.size() < count:
		selected.append(pool[rng.randi() % pool.size()])

	for raw_id in selected:
		var pos: Vector2i = _pick_spawn_cell(rng, occupied)
		var is_siege_unit: bool = (raw_id in sapper_castes or raw_id in heavy_castes or raw_id == IsectumCastes.ID_LIBELULA_BOMBARDEIRA)
		var u: Dictionary = _create_unit_dict(raw_id, "siege_%d" % unit_index, pos, act, floor_index, false, is_siege_unit)
		squad.append(u)
		unit_index += 1

	return squad

static func _generate_elite_squad(act: int, floor_index: int, rng: RandomNumberGenerator, occupied: Dictionary = {}) -> Array[Dictionary]:
	var squad: Array[Dictionary] = []

	if act == 1:
		# Líder Pesado de Elite do Ato 1
		var leader_raw: String = ACT_1_ELITE_LEADERS[rng.randi() % ACT_1_ELITE_LEADERS.size()]
		var leader_pos: Vector2i = _pick_spawn_cell(rng, occupied, FortressBoard.ZONE_SPAWN_NORTE)
		var leader: Dictionary = _create_unit_dict(leader_raw, "elite_leader_1", leader_pos, act, floor_index, true, false)

		leader["is_elite"] = true
		var is_beetle: bool = (leader["caste_id"] == IsectumCastes.ID_ESCARAVELHO_COURACADO)
		leader["name"] = "Escaravelho Couraçado Alfa" if is_beetle else "Tarântula Golias Titânica"
		leader["max_hp"] = 20 + floor_index
		leader["hp"] = leader["max_hp"]
		leader["ac"] = maxi(15, leader["ac"] + 2)
		leader["attack_bonus"] = leader["attack_bonus"] + 1
		leader["attack_dice"] = leader["attack_dice"] + 1
		squad.append(leader)

		# Lacaios de Escolta (2 a 3 unidades)
		var minion_count: int = rng.randi_range(2, 3)
		var minion_pool: Array[String] = ["gafanhoto_praga", "formiga_acida", IsectumCastes.ID_SOLDADO_MANDIBULA]
		for i in range(minion_count):
			var raw_caste: String = minion_pool[rng.randi() % minion_pool.size()]
			var m_pos: Vector2i = _pick_spawn_cell(rng, occupied)
			var minion: Dictionary = _create_unit_dict(raw_caste, "elite_escort_%d" % (i + 1), m_pos, act, floor_index, false, false)
			squad.append(minion)

	elif act == 2:
		# Líder de Elite do Ato 2: Mini-chefe Cigarra Ressonante
		var leader_pos: Vector2i = _pick_spawn_cell(rng, occupied, FortressBoard.ZONE_SPAWN_NORTE)
		var leader: Dictionary = _create_unit_dict("cigarra_ressonante", "elite_leader_cigarra", leader_pos, act, floor_index, true, false)

		leader["is_elite"] = true
		leader["name"] = "Cigarra Ressonante, Emissária do Trono"
		leader["max_hp"] = 80 + floor_index * 2
		leader["hp"] = leader["max_hp"]
		leader["ac"] = 15
		leader["move_range"] = 4
		leader["attack_range"] = 3
		leader["attack_bonus"] = 4
		leader["attack_dice"] = 3
		leader["trait_id"] = "pulso_sonico"
		leader["symbol"] = "🦗"
		squad.append(leader)

		# Lacaios de escolta do Ato 2 (2 a 3 unidades Tier 2)
		var minion_count: int = rng.randi_range(2, 3)
		for i in range(minion_count):
			var raw_caste: String = ACT_2_COMBAT_POOL[rng.randi() % ACT_2_COMBAT_POOL.size()]
			var m_pos: Vector2i = _pick_spawn_cell(rng, occupied)
			var minion: Dictionary = _create_unit_dict(raw_caste, "elite_escort_a2_%d" % (i + 1), m_pos, act, floor_index, false, false)
			squad.append(minion)

	else:
		# Líder de Elite do Ato 3
		var leader_pos: Vector2i = _pick_spawn_cell(rng, occupied, FortressBoard.ZONE_SPAWN_NORTE)
		var leader: Dictionary = _create_unit_dict(IsectumCastes.ID_COLOSSO_ISECTUM, "elite_leader_a3", leader_pos, act, floor_index, true, false)
		leader["is_elite"] = true
		leader["name"] = "Colosso Isectum Ancião"
		leader["max_hp"] = 45 + floor_index * 2
		leader["hp"] = leader["max_hp"]
		leader["ac"] = 16
		squad.append(leader)

		var minion_count: int = rng.randi_range(2, 3)
		for i in range(minion_count):
			var raw_caste: String = ACT_3_COMBAT_POOL[rng.randi() % ACT_3_COMBAT_POOL.size()]
			var m_pos: Vector2i = _pick_spawn_cell(rng, occupied)
			var minion: Dictionary = _create_unit_dict(raw_caste, "elite_escort_a3_%d" % (i + 1), m_pos, act, floor_index, false, false)
			squad.append(minion)

	return squad

static func _generate_boss_squad(act: int, floor_index: int, rng: RandomNumberGenerator, rules: Dictionary, occupied: Dictionary = {}) -> Array[Dictionary]:
	var squad: Array[Dictionary] = []

	if act == 1:
		rules["boss_id"] = "viuva_canibal"
		var boss_pos: Vector2i = Vector2i(9, 3)
		occupied[boss_pos] = true

		var boss: Dictionary = {
			"id": "viuva_canibal_boss",
			"caste_id": IsectumCastes.ID_TECE_TEIA,
			"name": "Viúva Canibal, Tecelã das Sombras",
			"team": "B",
			"hp": 70,
			"max_hp": 70,
			"ac": 15,
			"move_range": 3,
			"attack_range": 3,
			"attack_bonus": 4,
			"attack_dice": 4,
			"threat_cost": 10,
			"trait_id": "teia_imobilizante",
			"symbol": "🕷️",
			"spawn_pos": boss_pos,
			"target_zone": FortressBoard.ZONE_SPAWN_NORTE,
			"is_boss": true,
			"is_elite": false,
			"is_siege": false
		}
		squad.append(boss)

		# 3 larvas de escolta para mecânica de canibalismo/cura
		var larvae_positions: Array[Vector2i] = [Vector2i(7, 3), Vector2i(11, 3), Vector2i(9, 5)]
		for i in range(3):
			var l_pos: Vector2i = larvae_positions[i]
			occupied[l_pos] = true
			var larva: Dictionary = _create_unit_dict("larva_carniceira", "boss_larva_%d" % (i + 1), l_pos, act, floor_index, false, false)
			larva["name"] = "Larva de Alimento"
			larva["target_zone"] = FortressBoard.ZONE_SPAWN_NORTE
			squad.append(larva)

	elif act == 2:
		rules["boss_id"] = "rainha_do_enxame"
		rules["has_royal_guards"] = true
		rules["transition_hook"] = "Vocês matam a carne, mas a Mente é eterna! Enquanto os Três Corações baterem, o Rei jamais cairá!"

		var boss_pos: Vector2i = Vector2i(10, 2)
		occupied[boss_pos] = true

		var boss: Dictionary = {
			"id": "rainha_enxame_boss",
			"caste_id": IsectumCastes.ID_RAINHA_DO_ENXAME,
			"name": "Rainha do Enxame",
			"team": "B",
			"hp": 200,
			"max_hp": 200,
			"ac": 16,
			"move_range": 3,
			"attack_range": 2,
			"attack_bonus": 5,
			"attack_dice": 5,
			"threat_cost": 12,
			"trait_id": "chamado_da_rainha",
			"symbol": "👑",
			"spawn_pos": boss_pos,
			"target_zone": FortressBoard.ZONE_SPAWN_NORTE,
			"is_boss": true,
			"is_elite": false,
			"is_siege": false,
			"damage_reduction": 0.5
		}
		squad.append(boss)

		# 2 Guardas Reais couraçados com redução de dano compartilhada
		var guards_pos: Array[Vector2i] = [Vector2i(8, 2), Vector2i(12, 2)]
		for i in range(2):
			var p: Vector2i = guards_pos[i]
			occupied[p] = true
			var guard: Dictionary = _create_unit_dict("guarda_real", "boss_guard_%d" % (i + 1), p, act, floor_index, false, false)
			guard["name"] = "Guarda Real da Colmeia"
			guard["hp"] = 25
			guard["max_hp"] = 25
			guard["ac"] = 16
			guard["is_royal_guard"] = true
			guard["target_zone"] = FortressBoard.ZONE_SPAWN_NORTE
			squad.append(guard)

		# 1 Lacaio alado da ninhada inicial
		var brood_pos: Vector2i = Vector2i(10, 4)
		occupied[brood_pos] = true
		var brood: Dictionary = _create_unit_dict("vespa_cacadora", "boss_brood_1", brood_pos, act, floor_index, false, false)
		brood["target_zone"] = FortressBoard.ZONE_SPAWN_NORTE
		squad.append(brood)

	else:
		rules["boss_id"] = "rei_isectum"
		var boss_pos: Vector2i = Vector2i(10, 2)
		occupied[boss_pos] = true

		var boss: Dictionary = {
			"id": "rei_isectum_boss",
			"caste_id": IsectumCastes.ID_COLOSSO_ISECTUM,
			"name": "Rei Isectum (Trono de Âmbar)",
			"team": "B",
			"hp": 120,
			"max_hp": 120,
			"ac": 17,
			"move_range": 2,
			"attack_range": 2,
			"attack_bonus": 6,
			"attack_dice": 6,
			"threat_cost": 15,
			"trait_id": "mente_colmeia",
			"symbol": "👑",
			"spawn_pos": boss_pos,
			"target_zone": FortressBoard.ZONE_SPAWN_NORTE,
			"is_boss": true,
			"is_elite": false,
			"is_siege": false
		}
		squad.append(boss)

		# Guardas reais couraçados do Rei
		var guards_pos: Array[Vector2i] = [Vector2i(8, 2), Vector2i(12, 2)]
		for i in range(2):
			var p: Vector2i = guards_pos[i]
			occupied[p] = true
			var guard: Dictionary = _create_unit_dict(IsectumCastes.ID_ESCARAVELHO_COURACADO, "boss_guard_%d" % (i + 1), p, act, floor_index, false, false)
			guard["target_zone"] = FortressBoard.ZONE_SPAWN_NORTE
			squad.append(guard)

	return squad

# ── Perigos Ambientais & Casulos ─────────────────────────────────────────────

static func _generate_boss_web_hazards(rng: RandomNumberGenerator) -> Array[Dictionary]:
	var hazards: Array[Dictionary] = []
	var candidates: Array[Vector2i] = [
		Vector2i(8, 6), Vector2i(11, 6),
		Vector2i(6, 8), Vector2i(13, 8),
		Vector2i(8, 12), Vector2i(11, 12),
		Vector2i(9, 7), Vector2i(10, 7)
	]
	var count: int = rng.randi_range(5, 7)
	for i in range(candidates.size() - 1, 0, -1):
		var j: int = rng.randi_range(0, i)
		var tmp: Vector2i = candidates[i]
		candidates[i] = candidates[j]
		candidates[j] = tmp

	for i in range(mini(count, candidates.size())):
		hazards.append({
			"pos": candidates[i],
			"type": "WEB",
			"name": "Teia Viscosa",
			"icon": "🕸️",
			"effect": "slow",
			"move_penalty": 99,
			"duration": -1
		})

	return hazards

static func _generate_act2_cocoons(node_type: int, rng: RandomNumberGenerator, occupied: Dictionary) -> Array[Dictionary]:
	var cocoons: Array[Dictionary] = []
	var count: int = 1

	match node_type:
		RunNode.NodeType.COMBAT:
			count = rng.randi_range(1, 2)
		RunNode.NodeType.SIEGE:
			count = rng.randi_range(1, 3)
		RunNode.NodeType.ELITE:
			count = 2
		RunNode.NodeType.BOSS:
			count = rng.randi_range(2, 3)

	var candidates: Array[Vector2i] = [
		Vector2i(6, 6), Vector2i(13, 6),
		Vector2i(6, 13), Vector2i(13, 13),
		Vector2i(7, 9), Vector2i(12, 9),
		Vector2i(9, 6), Vector2i(10, 13),
		Vector2i(8, 7), Vector2i(11, 7),
		Vector2i(6, 4), Vector2i(14, 4),
		Vector2i(9, 12), Vector2i(10, 12)
	]

	for i in range(candidates.size() - 1, 0, -1):
		var j: int = rng.randi_range(0, i)
		var tmp: Vector2i = candidates[i]
		candidates[i] = candidates[j]
		candidates[j] = tmp

	var placed: int = 0
	for pos in candidates:
		if placed >= count:
			break
		if occupied.has(pos):
			continue
		occupied[pos] = true
		var spawn_caste: String = ACT_2_COMBAT_POOL[rng.randi() % ACT_2_COMBAT_POOL.size()]
		var cocoon: Dictionary = {
			"id": "cocoon_a2_%d" % (placed + 1),
			"pos": pos,
			"type": "COCOON",
			"name": "Casulo de Quitina",
			"icon": "🥚",
			"hp": 15,
			"max_hp": 15,
			"ac": 10,
			"turns_remaining": 3,
			"spawn_caste": spawn_caste,
			"acid_damage": 5,
			"effect": "hatch_threat"
		}
		cocoons.append(cocoon)
		placed += 1

	return cocoons

# ── Utilitários & Posicionamento Espacial ─────────────────────────────────────

static func resolve_caste_id(raw_id: String) -> String:
	var lower: String = raw_id.to_lower().strip_edges()
	if CASTE_ALIASES.has(lower):
		return CASTE_ALIASES[lower]
	return lower

static func _create_unit_dict(
	raw_id: String,
	unit_uid: String,
	spawn_pos: Vector2i,
	act: int,
	floor_index: int,
	is_elite: bool,
	is_siege: bool
) -> Dictionary:
	var cid: String = resolve_caste_id(raw_id)
	var caste: IsectumCasteData = IsectumCastes.get_caste(cid)

	var base_hp: int = caste.hp if caste != null else 4
	var base_ac: int = caste.ac if caste != null else 12
	var base_speed: int = caste.speed if caste != null else 3
	var base_atk_dice: int = caste.attack_dice if caste != null else 2
	var base_range: int = caste.attack_range if caste != null else 1
	var trait_name: String = caste.trait_id if caste != null else ""
	var sym: String = caste.symbol if caste != null else "🦗"
	var disp_name: String = caste.caste_name if caste != null else raw_id.capitalize()

	# Escalonamento sutil por andar
	if floor_index >= 7:
		base_hp += 1

	var target_zone: String = _determine_zone_for_pos(spawn_pos)

	return {
		"id": unit_uid,
		"caste_id": cid,
		"name": disp_name,
		"team": "B",
		"hp": base_hp,
		"max_hp": base_hp,
		"ac": base_ac,
		"move_range": base_speed,
		"attack_range": base_range,
		"attack_bonus": base_atk_dice,
		"attack_dice": base_atk_dice,
		"threat_cost": caste.threat_cost if caste != null else 1,
		"trait_id": trait_name,
		"symbol": sym,
		"spawn_pos": spawn_pos,
		"target_zone": target_zone,
		"is_boss": false,
		"is_elite": is_elite,
		"is_siege": is_siege
	}

static func _determine_zone_for_pos(pos: Vector2i) -> String:
	if pos.y <= 3:
		return FortressBoard.ZONE_SPAWN_NORTE
	elif pos.y >= 16:
		return FortressBoard.ZONE_SPAWN_SUL
	elif pos.x <= 3:
		return FortressBoard.ZONE_SPAWN_OESTE
	elif pos.x >= 16:
		return FortressBoard.ZONE_SPAWN_LESTE
	return FortressBoard.ZONE_SPAWN_NORTE

static func _pick_spawn_cell(
	rng: RandomNumberGenerator,
	occupied: Dictionary,
	zone_pref: String = ""
) -> Vector2i:
	var candidates: Array[Vector2i] = []
	if zone_pref == FortressBoard.ZONE_SPAWN_NORTE or (zone_pref.is_empty() and rng.randi() % 2 == 0):
		for x in range(4, 16):
			for y in range(0, 3):
				var p: Vector2i = Vector2i(x, y)
				if not occupied.has(p):
					candidates.append(p)
	else:
		var side: int = rng.randi() % 3
		match side:
			0: # Sul
				for x in range(4, 16):
					for y in range(17, 20):
						var p: Vector2i = Vector2i(x, y)
						if not occupied.has(p):
							candidates.append(p)
			1: # Oeste
				for x in range(0, 3):
					for y in range(4, 16):
						var p: Vector2i = Vector2i(x, y)
						if not occupied.has(p):
							candidates.append(p)
			2: # Leste
				for x in range(17, 20):
					for y in range(4, 16):
						var p: Vector2i = Vector2i(x, y)
						if not occupied.has(p):
							candidates.append(p)

	if candidates.is_empty():
		for x in range(20):
			for y in range(20):
				var p: Vector2i = Vector2i(x, y)
				if not occupied.has(p):
					occupied[p] = true
					return p
		return Vector2i(0, 0)

	var chosen: Vector2i = candidates[rng.randi() % candidates.size()]
	occupied[chosen] = true
	return chosen

static func _resolve_rng(seed_or_rng: Variant, act: int, floor_index: int, node_id: int) -> RandomNumberGenerator:
	if seed_or_rng is RandomNumberGenerator:
		return seed_or_rng
	var r: RandomNumberGenerator = RandomNumberGenerator.new()
	var base_s: int = int(seed_or_rng) if seed_or_rng != null else 0
	r.seed = compute_encounter_seed(base_s, act, floor_index, node_id)
	return r

static func compute_encounter_seed(base_seed: int, act: int, floor_index: int, node_id: int) -> int:
	var p1: int = 73856093
	var p2: int = 19349663
	var p3: int = 83492791
	return (base_seed + (act * p1) + (floor_index * p2) + (node_id * p3)) & 0x7FFFFFFF

static func _build_forced_waves_from_squad(squad: Array[Dictionary], ntype: int) -> Array[Dictionary]:
	var waves: Array[Dictionary] = []
	var card_type: String = ThreatDeck.TYPE_BOSS_ASSAULT if (ntype == RunNode.NodeType.BOSS or ntype == RunNode.NodeType.ELITE) else ThreatDeck.TYPE_SPAWN_WAVE

	var idx: int = 1
	for u in squad:
		var z: String = str(u.get("target_zone", FortressBoard.ZONE_SPAWN_NORTE))
		var w_id: String = "wave_%d" % idx
		var threat: Dictionary = {
			"id": w_id,
			"card_type": card_type,
			"title": str(u.get("name", "Invasores Isectum")),
			"caste_id": str(u.get("caste_id", IsectumCastes.ID_ZANGAO_INVASOR)),
			"count": 1,
			"target_zone": z,
			"round": mini(idx, 3),
			"threat_cost": int(u.get("threat_cost", 2)),
			"status": ThreatDeck.STATUS_ACTIVE,
			"hp": int(u.get("hp", 4)),
			"ac": int(u.get("ac", 12)),
			"move": int(u.get("move_range", 3)),
			"atk": int(u.get("attack_bonus", 2)),
			"description": "%s atacando %s." % [str(u.get("name")), z]
		}
		waves.append(threat)
		idx += 1

	return waves

# res://scripts/run/combat/RunCombatBridge.gd
class_name RunCombatBridge
extends RefCounted

## RunCombatBridge: Mediador desacoplado entre RunSession / RunState e CercoGameController.
## Orquestra o setup de encontros táticos, filtragem de heróis sobreviventes (Permadeath),
## conversão de cartas de deck em CardData e sincronização bidirecional de resultados (PV, baixas, ouro).

const DEFAULT_HERO_POSITIONS: Array[Vector2i] = [
	Vector2i(9, 10),  # Pátio Oeste
	Vector2i(10, 9),  # Pátio Norte
	Vector2i(10, 11), # Pátio Sul
	Vector2i(9, 11),  # Pátio Centro-Oeste
]

static var _current_encounter: Dictionary = {}
static var _last_result: Dictionary = {}

static func has_active_encounter() -> bool:
	return not _current_encounter.is_empty()

static func get_current_encounter() -> Dictionary:
	return _current_encounter.duplicate(true)

static func clear_encounter() -> void:
	_current_encounter.clear()

static func clear() -> void:
	_current_encounter.clear()
	_last_result.clear()

static func get_last_result() -> Dictionary:
	return _last_result.duplicate(true)

## 1. Configura os parâmetros do combate tático a partir de RunState e RunNode
static func setup_combat(run_state: RunState, node: RunNode, rng: RandomNumberGenerator = null) -> Dictionary:
	if run_state == null or node == null or not run_state.is_active():
		return {
			"ok": false,
			"living_heroes": [],
			"hero_hp": {},
			"hero_max_hp": {},
			"deck": [],
			"relics": [],
			"encounter": {}
		}

	var living: Array[String] = run_state.get_living_heroes()
	if living.is_empty():
		return {
			"ok": false,
			"living_heroes": [],
			"hero_hp": {},
			"hero_max_hp": {},
			"deck": [],
			"relics": [],
			"encounter": {}
		}

	var h_hp: Dictionary = {}
	var h_max: Dictionary = {}
	var party_data: Array[Dictionary] = []

	for i in range(living.size()):
		var hid: String = living[i]
		var cur_hp: int = int(run_state.hero_hp.get(hid, 1))
		var max_hp: int = int(run_state.hero_max_hp.get(hid, cur_hp))
		h_hp[hid] = cur_hp
		h_max[hid] = max_hp

		var pos: Vector2i = DEFAULT_HERO_POSITIONS[i] if i < DEFAULT_HERO_POSITIONS.size() else Vector2i(9 + i, 10)
		var h_info: Dictionary = get_hero_battle_stats(hid, cur_hp, max_hp)
		h_info["spawn_pos"] = pos
		party_data.append(h_info)

	var gen_enc: Dictionary = CombatEncounterGenerator.generate_from_node(node, rng)

	var max_rounds: int = 3
	match node.type:
		RunNode.NodeType.COMBAT: max_rounds = 3
		RunNode.NodeType.ELITE: max_rounds = 4
		RunNode.NodeType.SIEGE: max_rounds = 5
		RunNode.NodeType.BOSS: max_rounds = 5

	var encounter_payload: Dictionary = {
		"ok": true,
		"is_run_combat": true,
		"act": run_state.act,
		"floor": node.floor_index,
		"node_id": node.id,
		"node_type": node.type,
		"is_boss": node.is_boss(),
		"boss_id": run_state.get_current_boss_id() if node.is_boss() else "",
		"living_heroes": living,
		"fallen_heroes": run_state.fallen_heroes.duplicate(),
		"hero_hp": h_hp,
		"hero_max_hp": h_max,
		"party": party_data,
		"deck": run_state.deck.duplicate(),
		"deck_ids": run_state.deck.duplicate(),
		"relics": run_state.relics.duplicate(),
		"max_rounds": max_rounds,
		"encounter": gen_enc,
		"squad": gen_enc.get("squad", []),
		"enemies": gen_enc.get("enemies", []),
		"hazards": gen_enc.get("hazards", []),
		"forced_waves": gen_enc.get("forced_waves", []),
		"gold_reward": RewardModal.NODE_GOLD_TABLE.get(node.type, 15),
		"destroyed_hearts": run_state.get_destroyed_hearts() if run_state.has_method("get_destroyed_hearts") else []
	}

	_current_encounter = encounter_payload.duplicate(true)
	return _current_encounter

## 2. Sincroniza os resultados do combate no RunState (PV, Permadeath, Abates, Ouro)
static func sync_combat_result(run_state: RunState, result: Dictionary) -> Dictionary:
	var summary: Dictionary = {
		"victory": false,
		"game_over": false,
		"party_wipe": false,
		"status": RunState.Status.NOT_STARTED,
		"living_heroes_count": 0,
		"living_heroes": [],
		"fallen_heroes": [],
		"hero_hp": {},
		"gold": 0,
		"amber": 0,
		"amber_earned": 0,
		"act": 1,
		"newly_fallen": []
	}

	if run_state == null or not run_state.is_active() or result.is_empty():
		return summary

	var victory: bool = bool(result.get("victory", false))
	# Suporta tanto 'surviving_heroes_hp' quanto 'hero_hp' para interoperabilidade
	var final_hps: Dictionary = result.get("surviving_heroes_hp", result.get("hero_hp", {}))
	var reported_fallen: Array = result.get("fallen_heroes", [])
	var kills: int = int(result.get("enemies_killed", 0))
	var gold_loot: int = int(result.get("gold_collected", result.get("gold_earned", 0)))

	# 1. Sincroniza PV e detecta heróis caídos (Permadeath)
	for hid in run_state.heroes:
		if run_state.fallen_heroes.has(hid):
			run_state.hero_hp[hid] = 0
			continue

		var was_alive: bool = run_state.is_hero_alive(hid)

		if final_hps.has(hid):
			var max_h: int = int(run_state.hero_max_hp.get(hid, 1))
			var target_hp: int = clampi(int(final_hps[hid]), 0, max_h)
			var prev_hp: int = int(run_state.hero_hp.get(hid, 0))

			if target_hp < prev_hp:
				run_state.damage_hero(hid, prev_hp - target_hp)
			elif target_hp > prev_hp:
				run_state.heal_hero(hid, target_hp - prev_hp)

			if target_hp <= 0:
				if was_alive and not summary["newly_fallen"].has(hid):
					summary["newly_fallen"].append(hid)
				run_state.hero_hp[hid] = 0
		elif reported_fallen.has(hid):
			if was_alive:
				run_state.damage_hero(hid, 9999)
				if not summary["newly_fallen"].has(hid):
					summary["newly_fallen"].append(hid)
			run_state.hero_hp[hid] = 0

	# 2. Registrar abates e ouro adquirido no mapa/baús
	if kills > 0:
		run_state.register_kills(kills)
	if gold_loot > 0:
		run_state.add_gold(gold_loot)

	# 3. Avaliar vitória ou derrota
	var living: Array[String] = run_state.get_living_heroes()
	var living_count: int = living.size()
	summary["living_heroes_count"] = living_count

	if living_count == 0 or not victory:
		if run_state.is_active():
			run_state.status = RunState.Status.DEFEAT
			run_state.run_ended.emit(false)
		summary["victory"] = false
		summary["game_over"] = true
		summary["party_wipe"] = (living_count == 0)
	else:
		run_state.complete_current_node()
		summary["victory"] = true
		summary["game_over"] = (run_state.status == RunState.Status.VICTORY)

	var amber: int = run_state.calculate_amber()
	summary["status"] = run_state.status
	summary["living_heroes"] = run_state.get_living_heroes()
	summary["fallen_heroes"] = run_state.fallen_heroes.duplicate()
	summary["hero_hp"] = run_state.hero_hp.duplicate()
	summary["gold"] = run_state.gold
	summary["amber"] = amber
	summary["amber_earned"] = amber
	summary["act"] = run_state.act

	_last_result = summary.duplicate(true)
	clear_encounter()
	return summary

## 3. Valida se o herói está apto a entrar em combate
static func can_deploy_hero(run_state: RunState, hero_id: String) -> bool:
	if run_state == null:
		return false
	return run_state.is_hero_alive(hero_id) and int(run_state.hero_hp.get(hero_id, 0)) > 0

## 4. Converte strings de IDs do deck para recursos tipados CardData
static func convert_deck(card_ids: Array[String]) -> Array[CardData]:
	var cards: Array[CardData] = []
	for cid in card_ids:
		cards.append(card_id_to_card_data(cid))
	return cards

static func card_id_to_card_data(card_id: String) -> CardData:
	var c: CardData = CardData.new()
	c.id = card_id
	var clean: String = card_id.to_lower().strip_edges()

	if clean.begins_with("movimento") or clean.begins_with("marcha"):
		c.card_name = "Marcha"
		c.card_type = CardData.TYPE_ACAO
		c.badge = CardData.BADGE_MARCHA
		c.movement = 15
		c.effect_value = 15
		c.description = "+15 Movimento"
		return c

	if clean.begins_with("trabalho"):
		c.card_name = "Trabalho"
		c.card_type = CardData.TYPE_ACAO
		c.badge = CardData.BADGE_TRABALHO
		c.work = 3
		c.effect_value = 3
		c.description = "+3 Trabalho"
		return c

	if clean.begins_with("escavacao"):
		c.card_name = "Escavação"
		c.card_type = CardData.TYPE_ACAO
		c.badge = CardData.BADGE_ESCAVACAO
		c.excavation = 4
		c.effect_value = 4
		c.description = "+4 Escavação"
		return c

	if clean.begins_with("ataque") or clean == "golpe":
		c.card_name = "Ataque Tático"
		c.card_type = CardData.TYPE_ACAO
		c.badge = CardData.BADGE_COMBATE
		c.effect_value = 10
		c.description = "⚔️ Causa 8-12 de dano físico a um inimigo"
		return c

	if clean.begins_with("forca_ana") or clean.begins_with("combate"):
		c.card_name = "Força Anã"
		c.card_type = CardData.TYPE_ACAO
		c.badge = CardData.BADGE_COMBATE
		c.work = 4
		c.movement = 15
		c.effect_value = 10
		c.description = "⚔️ Causa 8-12 de dano (+4 Trab / +15 Mov)"
		return c

	if clean.begins_with("defesa") or clean.begins_with("bloqueio"):
		c.card_name = "Bloqueio"
		c.card_type = CardData.TYPE_DEFESA
		c.badge = CardData.BADGE_COMBATE
		c.effect_value = 5
		c.description = "+5 Defesa / Armadura"
		return c

	# Consulta catálogo de preços da Forja se disponível
	if ForgeScreen.CARD_PRICES.has(clean):
		var info: Dictionary = ForgeScreen.CARD_PRICES[clean]
		c.card_name = str(info.get("name", clean.capitalize()))
		c.card_type = CardData.TYPE_ACAO
		c.badge = str(info.get("badge", CardData.BADGE_COMBATE))
		c.description = str(info.get("desc", ""))
		c.cost_wood = int(info.get("cost", 50))
		match clean:
			"golpe_pesado": c.effect_value = 16
			"tiro_balista": c.effect_value = 15
			"lamina_ignea": c.effect_value = 16
			"martelo_do_trovao": c.effect_value = 12
			"furor_ancestral": c.effect_value = 24
			"fogo_alquimico": c.effect_value = 30
			"colapso_estrutural": c.effect_value = 20
			_: c.effect_value = int(info.get("effect_value", 10))
		return c

	# Fallback genérico de ação
	c.card_name = clean.capitalize()
	c.card_type = CardData.TYPE_ACAO
	c.badge = CardData.BADGE_COMBATE
	c.effect_value = 8
	c.description = "⚔️ Ação tática de combate (Causa dano direto)"
	return c

## 5. Mapeia dados e atributos de combate dos heróis
static func get_hero_battle_stats(hero_id: String, cur_hp: int, max_hp: int) -> Dictionary:
	var clean: String = hero_id.to_lower().strip_edges()
	var base_data: Dictionary = {
		"id": clean,
		"name": clean.capitalize(),
		"team": "A",
		"hp": cur_hp,
		"max_hp": max_hp,
		"ac": 15,
		"move_range": 3,
		"attack_range": 1,
		"attack_bonus": 3,
		"is_alive": cur_hp > 0
	}

	match clean:
		"stark":
			base_data["name"] = "Stark"
			base_data["class"] = "Paladino"
			base_data["ac"] = 18
			base_data["move_range"] = 3
			base_data["attack_bonus"] = 3
		"elden":
			base_data["name"] = "Elden"
			base_data["class"] = "Clérigo"
			base_data["ac"] = 16
			base_data["move_range"] = 3
			base_data["attack_range"] = 2
			base_data["attack_bonus"] = 4
		"doom":
			base_data["name"] = "Doom"
			base_data["class"] = "Ladino"
			base_data["ac"] = 15
			base_data["move_range"] = 4
			base_data["attack_bonus"] = 4
		"gruu":
			base_data["name"] = "Gruu"
			base_data["class"] = "Bárbaro"
			base_data["ac"] = 14
			base_data["move_range"] = 4
			base_data["attack_bonus"] = 5
		"novak":
			base_data["name"] = "Novak"
			base_data["class"] = "Guerreiro"
			base_data["ac"] = 19
			base_data["move_range"] = 4
			base_data["attack_bonus"] = 4
		"lysander":
			base_data["name"] = "Pr. Lysander"
			base_data["class"] = "Comandante"
			base_data["ac"] = 14
			base_data["move_range"] = 3
			base_data["attack_range"] = 2
			base_data["attack_bonus"] = 5
		"aquele":
			base_data["name"] = "Aquele"
			base_data["class"] = "Guerreiro (Secreto)"
			base_data["ac"] = 17
			base_data["move_range"] = 4
			base_data["attack_bonus"] = 4

	return base_data

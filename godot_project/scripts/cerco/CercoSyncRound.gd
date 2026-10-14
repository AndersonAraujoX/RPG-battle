# res://scripts/cerco/CercoSyncRound.gd
class_name CercoSyncRound
extends RefCounted

## CercoSyncRound: Co-op Synchrony Turn Resolution for Cerco da Fortaleza contra Isectum.
## Resolves all player actions simultaneously across 4 distinct sequential layers:
## 1. March / Movement layer (Defenders maneuver, Isectum advance)
## 2. Work / Production layer (Workshops produce resources, Wall repairs)
## 3. Excavation layer (Resource extraction from rubble / zones)
## 4. Combat layer (Tower balestras fire, Melee combat resolved via CercoCombatJudge)
##
## Implements the Synergy Combo System:
## - Team Synergy: >= 2 players choose the same badge -> +1 bonus (production, speed, armor/die).
## - Supreme Synchrony (Sincronia Suprema): ALL players choose the exact same badge -> +2 Cristais bonus!

# ── Signals ──────────────────────────────────────────────────────────────────
signal action_registered(player_id: String, badge: String, card: CardData)
signal layer_started(layer_name: String)
signal layer_resolved(layer_name: String, layer_result: Dictionary)
signal synergy_detected(synergy_type: String, badge: String, bonus: Dictionary)
signal supreme_synchrony_triggered(badge: String, crystal_bonus: int)
signal round_completed(round_number: int, summary: Dictionary)

# ── Layer Constants ──────────────────────────────────────────────────────────
const LAYER_MARCHA: String = "MARCHA"
const LAYER_TRABALHO: String = "TRABALHO"
const LAYER_ESCAVACAO: String = "ESCAVACAO"
const LAYER_COMBATE: String = "COMBATE"

const ALL_LAYERS: Array[String] = [
	LAYER_MARCHA,
	LAYER_TRABALHO,
	LAYER_ESCAVACAO,
	LAYER_COMBATE
]

const SUPREME_SYNCHRONY_CRYSTAL_BONUS: int = 2

# ── Registered Actions ───────────────────────────────────────────────────────
# player_id -> { "player_id": String, "card": CardData, "badge": String, "target_params": Dictionary }
var _registered_actions: Dictionary = {}

# ── Registration API ─────────────────────────────────────────────────────────

## Registers a player's chosen card and target parameters for the simultaneous round.
func register_player_action(
	player_id: String,
	card: CardData,
	target_params: Dictionary = {}
) -> bool:
	if player_id.strip_edges().is_empty() or card == null:
		return false

	var badge_norm: String = card.badge.strip_edges().to_upper()
	if badge_norm.is_empty():
		badge_norm = CardData.BADGE_MARCHA

	_registered_actions[player_id] = {
		"player_id": player_id,
		"card": card,
		"badge": badge_norm,
		"target_params": target_params.duplicate(true)
	}

	action_registered.emit(player_id, badge_norm, card)

	# Global EventBus notification
	var eb: Node = _get_event_bus()
	if eb != null and eb.has_signal("card_selected"):
		eb.card_selected.emit(player_id, card.id)

	return true

func get_registered_actions() -> Dictionary:
	return _registered_actions.duplicate(true)

func get_action_count() -> int:
	return _registered_actions.size()

func clear_actions() -> void:
	_registered_actions.clear()

# ── Synergy Calculation ──────────────────────────────────────────────────────

## Analyzes all registered actions and calculates Team Synergies and Supreme Synchrony.
func calculate_synergies() -> Dictionary:
	var total_players: int = _registered_actions.size()
	var badge_counts: Dictionary = {}

	for pid in _registered_actions:
		var act: Dictionary = _registered_actions[pid]
		var b: String = act["badge"]
		badge_counts[b] = badge_counts.get(b, 0) + 1

	var supreme_synchrony: bool = false
	var supreme_badge: String = ""
	var team_synergies: Array[String] = []

	if total_players >= 2:
		for b in badge_counts:
			var count: int = badge_counts[b]
			if count == total_players:
				supreme_synchrony = true
				supreme_badge = b

			if count >= 2:
				team_synergies.append(b)

	var bonuses: Dictionary = {}
	for s in team_synergies:
		match s:
			CardData.BADGE_MARCHA:
				bonuses[s] = {"type": "movement_speed", "value": 1, "description": "+1 Velocidade de Marcha"}
			CardData.BADGE_TRABALHO:
				bonuses[s] = {"type": "production_boost", "value": 1, "description": "+1 Produção / +10 Reparo"}
			CardData.BADGE_ESCAVACAO:
				bonuses[s] = {"type": "excavation_yield", "value": 1, "description": "+1 Recurso Escavado"}
			CardData.BADGE_COMBATE:
				bonuses[s] = {"type": "combat_die", "value": 1, "description": "+1 Dado de Combate"}
			CardData.BADGE_ESPECIAL:
				bonuses[s] = {"type": "action_points", "value": 1, "description": "+1 Ponto de Ação (AP)"}

	return {
		"total_players": total_players,
		"badge_counts": badge_counts,
		"team_synergies": team_synergies,
		"supreme_synchrony": supreme_synchrony,
		"supreme_badge": supreme_badge,
		"crystal_bonus": SUPREME_SYNCHRONY_CRYSTAL_BONUS if supreme_synchrony else 0,
		"bonuses": bonuses
	}

# ── 4-Layer Synchronous Turn Resolution ──────────────────────────────────────

## Resolves the simultaneous co-op round through the 4 distinct layers:
## 1. March / Movement
## 2. Work / Production & Wall Repairs
## 3. Excavation
## 4. Combat
## Alias for resolve_synchrony_round to support alternate caller conventions.
func resolve_round(
	arg1: Variant = 1,
	arg2: Variant = null,
	arg3: Variant = null,
	arg4: Variant = null
) -> Dictionary:
	if arg1 is int:
		var r_num: int = arg1
		var b: FortressBoard = arg2 as FortressBoard
		var j: CercoCombatJudge = arg3 as CercoCombatJudge
		var e: WorkshopEconomy = arg4 as WorkshopEconomy
		return resolve_synchrony_round(r_num, b, j, e)
	else:
		var b: FortressBoard = arg1 as FortressBoard
		var e: WorkshopEconomy = arg2 as WorkshopEconomy
		var j: CercoCombatJudge = arg3 as CercoCombatJudge
		return resolve_synchrony_round(1, b, j, e)

func resolve_synchrony_round(
	round_number: int,
	board: FortressBoard = null,
	judge: CercoCombatJudge = null,
	economy: WorkshopEconomy = null
) -> Dictionary:
	# Step 0: Synergy Evaluation & Supreme Synchrony Award
	var syn_info: Dictionary = calculate_synergies()

	if syn_info["supreme_synchrony"]:
		if economy != null:
			economy.add_resource("crystal", SUPREME_SYNCHRONY_CRYSTAL_BONUS)
		supreme_synchrony_triggered.emit(syn_info["supreme_badge"], SUPREME_SYNCHRONY_CRYSTAL_BONUS)

		var eb_sup: Node = _get_event_bus()
		if eb_sup != null and eb_sup.has_signal("synergy_triggered"):
			eb_sup.synergy_triggered.emit("SUPREME", "Sincronia Suprema! +2 Cristais para a fortaleza!")

	for syn_badge in syn_info["team_synergies"]:
		var bonus_data: Dictionary = syn_info["bonuses"].get(syn_badge, {})
		synergy_detected.emit("TEAM", syn_badge, bonus_data)
		var eb_team: Node = _get_event_bus()
		if eb_team != null and eb_team.has_signal("synergy_triggered"):
			eb_team.synergy_triggered.emit("TEAM", "Sinergia de Equipe: %s" % syn_badge)

	# ── LAYER 1: Movement / March ─────────────────────────────────────────────
	layer_started.emit(LAYER_MARCHA)
	var layer1_results: Array[Dictionary] = []
	var has_march_synergy: bool = syn_info["team_synergies"].has(CardData.BADGE_MARCHA)

	for pid in _registered_actions:
		var act: Dictionary = _registered_actions[pid]
		if act["badge"] == CardData.BADGE_MARCHA:
			var card: CardData = act["card"]
			var params: Dictionary = act["target_params"]
			var move_info: Dictionary = {
				"player_id": pid,
				"card_id": card.id,
				"speed": card.movement + (1 if has_march_synergy else 0),
				"synergy_applied": has_march_synergy,
				"success": true
			}

			# Execute physical unit move if specified
			if board != null and params.has("unit_id") and (params.has("to_pos") or params.has("target_cell")):
				var unit_id: String = params["unit_id"]
				var to_pos: Vector2i = params.get("to_pos", params.get("target_cell", Vector2i.ZERO))
				var moved: bool = board.move_unit(unit_id, to_pos)
				move_info["unit_id"] = unit_id
				move_info["to_pos"] = to_pos
				move_info["moved_on_board"] = moved
			layer1_results.append(move_info)

	var layer1_summary: Dictionary = {
		"actions_executed": layer1_results.size(),
		"synergy_active": has_march_synergy,
		"details": layer1_results
	}
	layer_resolved.emit(LAYER_MARCHA, layer1_summary)

	# ── LAYER 2: Work / Production & Wall Repairs ─────────────────────────────
	layer_started.emit(LAYER_TRABALHO)
	var layer2_results: Array[Dictionary] = []
	var has_work_synergy: bool = syn_info["team_synergies"].has(CardData.BADGE_TRABALHO)

	for pid in _registered_actions:
		var act: Dictionary = _registered_actions[pid]
		if act["badge"] == CardData.BADGE_TRABALHO:
			var card: CardData = act["card"]
			var params: Dictionary = act["target_params"]
			var work_info: Dictionary = {
				"player_id": pid,
				"card_id": card.id,
				"synergy_applied": has_work_synergy
			}

			# 2a. Wall Repair
			if params.has("wall_id"):
				var wall_id: String = params["wall_id"]
				var wood_spent: int = params.get("wood_spent", 0)
				var metal_spent: int = params.get("metal_spent", 0)

				var new_hp: int = 0
				if economy != null and board != null:
					new_hp = economy.repair_wall_with_resources(wall_id, board, wood_spent, metal_spent)
					if has_work_synergy:
						new_hp = board.repair_wall(wall_id, 10) # Team synergy bonus +10 repair

				work_info["action"] = "wall_repair"
				work_info["wall_id"] = wall_id
				work_info["wood_spent"] = wood_spent
				work_info["metal_spent"] = metal_spent
				work_info["new_hp"] = new_hp
				work_info["bonus_repair"] = 10 if has_work_synergy else 0

			# 2b. Workshop Production
			elif params.has("workshop_zone"):
				var zone: String = params["workshop_zone"]
				var workers: int = params.get("worker_count", 1)
				var produced: Dictionary = {}
				if economy != null:
					produced = economy.produce_at_workshop(zone, workers)
					if has_work_synergy:
						# Bonus +1 to main produced resource
						var norm_zone: String = zone.to_upper()
						if norm_zone == "CARPINTARIA":
							economy.add_resource("wood", 1)
							produced["wood"] = produced.get("wood", 0) + 1
						elif norm_zone == "CURTUME":
							economy.add_resource("leather", 1)
							produced["leather"] = produced.get("leather", 0) + 1
						elif norm_zone == "FUNDICAO":
							economy.add_resource("metal", 1)
							produced["metal"] = produced.get("metal", 0) + 1

				work_info["action"] = "workshop_production"
				work_info["workshop_zone"] = zone
				work_info["produced"] = produced
				work_info["bonus_produced"] = 1 if has_work_synergy else 0
			else:
				# Generic work
				work_info["action"] = "generic_work"
				work_info["work_points"] = card.work + (1 if has_work_synergy else 0)

			layer2_results.append(work_info)

	var layer2_summary: Dictionary = {
		"actions_executed": layer2_results.size(),
		"synergy_active": has_work_synergy,
		"details": layer2_results
	}
	layer_resolved.emit(LAYER_TRABALHO, layer2_summary)

	# ── LAYER 3: Excavation ───────────────────────────────────────────────────
	layer_started.emit(LAYER_ESCAVACAO)
	var layer3_results: Array[Dictionary] = []
	var has_excavation_synergy: bool = syn_info["team_synergies"].has(CardData.BADGE_ESCAVACAO)

	for pid in _registered_actions:
		var act: Dictionary = _registered_actions[pid]
		if act["badge"] == CardData.BADGE_ESCAVACAO:
			var card: CardData = act["card"]
			var params: Dictionary = act["target_params"]

			var base_yield: int = maxi(1, floori(float(card.excavation) / 3.0)) if card.excavation > 0 else 1
			var bonus_yield: int = 1 if has_excavation_synergy else 0
			var total_crystals: int = params.get("crystals", base_yield) + bonus_yield
			var total_metal: int = params.get("metal", 1) + bonus_yield

			if economy != null:
				economy.add_resource("crystal", total_crystals)
				economy.add_resource("metal", total_metal)

			var exc_info: Dictionary = {
				"player_id": pid,
				"card_id": card.id,
				"crystals_extracted": total_crystals,
				"metal_extracted": total_metal,
				"synergy_applied": has_excavation_synergy
			}
			layer3_results.append(exc_info)

	var layer3_summary: Dictionary = {
		"actions_executed": layer3_results.size(),
		"synergy_active": has_excavation_synergy,
		"details": layer3_results
	}
	layer_resolved.emit(LAYER_ESCAVACAO, layer3_summary)

	# ── LAYER 4: Combat ───────────────────────────────────────────────────────
	layer_started.emit(LAYER_COMBATE)
	var layer4_results: Array[Dictionary] = []
	var has_combat_synergy: bool = syn_info["team_synergies"].has(CardData.BADGE_COMBATE)

	for pid in _registered_actions:
		var act: Dictionary = _registered_actions[pid]
		if act["badge"] == CardData.BADGE_COMBATE:
			var card: CardData = act["card"]
			var params: Dictionary = act["target_params"]
			var combat_info: Dictionary = {
				"player_id": pid,
				"card_id": card.id,
				"synergy_applied": has_combat_synergy
			}

			if judge != null:
				# 4a. Tower Balestra Attack
				if params.get("attack_type", "") == "tower" or params.has("attacker_zone"):
					var att_zone: String = params.get("attacker_zone", FortressBoard.ZONE_TORRE_NOROESTE)
					var tgt_zone: String = params.get("target_zone", FortressBoard.ZONE_MURALHA_NORTE)
					var num_dice: int = params.get("num_dice", 2)
					if has_combat_synergy:
						num_dice += 1
					var forced_rolls: Array = params.get("forced_rolls", [])
					var tgt_armor: int = params.get("target_armor", 0)

					var ranged_res: Dictionary = judge.resolve_tower_ranged_attack(
						att_zone, tgt_zone, num_dice, forced_rolls, board, tgt_armor
					)
					combat_info["attack_type"] = "tower_balestra"
					combat_info["result"] = ranged_res

				# 4b. Melee Attack
				else:
					var att_id: String = params.get("attacker_id", pid)
					var def_id: String = params.get("defender_id", "isectum_swarm")
					var num_dice: int = params.get("num_dice", 2)
					if has_combat_synergy:
						num_dice += 1
					var forced_rolls: Array = params.get("forced_rolls", [])
					var def_armor: int = params.get("defender_armor", 0)
					var allies: int = params.get("num_allies_in_zone", 1)

					var melee_res: Dictionary = judge.resolve_melee_attack(
						att_id, def_id, num_dice, forced_rolls, def_armor, allies
					)
					combat_info["attack_type"] = "melee"
					combat_info["result"] = melee_res
			else:
				combat_info["attack_type"] = "unresolved_no_judge"

			layer4_results.append(combat_info)

	var layer4_summary: Dictionary = {
		"actions_executed": layer4_results.size(),
		"synergy_active": has_combat_synergy,
		"details": layer4_results
	}
	layer_resolved.emit(LAYER_COMBATE, layer4_summary)

	# ── Round Summary Compilation ─────────────────────────────────────────────
	var summary: Dictionary = {
		"round_number": round_number,
		"total_actions": _registered_actions.size(),
		"synergies": syn_info,
		"layer_marcha": layer1_summary,
		"layer_trabalho": layer2_summary,
		"layer_escavacao": layer3_summary,
		"layer_combate": layer4_summary,
		"economy_state": economy.to_dict() if economy != null else {}
	}

	round_completed.emit(round_number, summary)

	var eb_round: Node = _get_event_bus()
	if eb_round != null and eb_round.has_signal("round_resolved"):
		eb_round.round_resolved.emit(round_number, summary)

	clear_actions()
	return summary

func _get_event_bus() -> Node:
	var loop = Engine.get_main_loop()
	if loop is SceneTree and loop.root != null:
		return loop.root.get_node_or_null("EventBus")
	return null

# res://scripts/run/relics/RelicData.gd
class_name RelicData
extends RefCounted

## RelicData: Base polymorphic class for all passive artifacts and relics in the roguelike run.
## Extends RefCounted to ensure memory leak safety in headless test environments.
## Provides virtual hooks for combat events, campfire resting, economy, and exploration.

# ── Rarity Constants ─────────────────────────────────────────────────────────
const RARITY_COMUM: String = "COMUM"
const RARITY_INCOMUM: String = "INCOMUM"
const RARITY_RARO: String = "RARO"
const RARITY_LENDARIO: String = "LENDARIO"
const RARITY_BOSS: String = "BOSS"

# ── Canonical Properties ─────────────────────────────────────────────────────
var id: String = ""
var relic_name: String = ""
var description: String = ""
var rarity: String = RARITY_COMUM
var cost_gold: int = 50
var icon_path: String = ""

## Transient per-combat / per-run counters
var counter: int = 0
var counter_max: int = 0
var is_active: bool = true

func _init(p_id: String = "", p_name: String = "", p_desc: String = "", p_rarity: String = RARITY_COMUM, p_cost: int = 50) -> void:
	id = p_id
	relic_name = p_name
	description = p_desc
	rarity = p_rarity
	cost_gold = p_cost

# ── Virtual Lifecycle Hooks ──────────────────────────────────────────────────

## Called when the relic is added to RelicManager / expedition.
func on_registered(_run_state: RunState) -> void:
	pass

## Called when the relic is removed from RelicManager / expedition.
## Guarantees relic deactivation and ephemeral counter reset.
func on_unregistered(_run_state: RunState) -> void:
	is_active = false
	counter = 0

## Called when the party moves into a new map node.
func on_node_entered(_node: RunNode, _run_state: RunState) -> void:
	pass

## Called at the beginning of a tactical battle.
func on_combat_started(_node_type: int, _run_state: RunState) -> void:
	reset_combat_state()

## Called when a new turn begins.
func on_turn_started(_turn_number: int, _active_unit_id: String, _run_state: RunState) -> void:
	pass

# ── Virtual Combat Hooks ─────────────────────────────────────────────────────

## Modifies an attack dealt.
## Returns Dictionary with possible keys:
## { "bonus_damage": int, "bonus_type": String, "heal_attacker": int, "override_crit": bool }
func on_attack_dealt(
	_attacker_id: String,
	_target_id: String,
	_is_hero: bool,
	_damage: int,
	_damage_type: String,
	_is_crit: bool,
	_run_state: RunState
) -> Dictionary:
	return {}

## Modifies damage received by a unit.
## Returns Dictionary with possible keys:
## { "damage_reduction": int, "cancel_damage": bool, "riposte_damage": int }
func on_damage_received(
	_target_id: String,
	_is_hero: bool,
	_incoming_damage: int,
	_current_hp: int,
	_max_hp: int,
	_run_state: RunState
) -> Dictionary:
	return {}

## Called when a unit is killed.
## Returns Dictionary with possible keys: { "bonus_gold": int, "heal_killer": int }
func on_unit_killed(_victim_id: String, _is_enemy: bool, _killer_id: String, _run_state: RunState) -> Dictionary:
	return {}

## Called when a condition/status effect is applied.
## Returns Dictionary with possible keys: { "cancel_status": bool }
func on_status_applied(_unit_id: String, _status_id: String, _duration: int, _run_state: RunState) -> Dictionary:
	return {}

## Called when an unconscious hero rolls a death saving throw.
## Returns Dictionary with possible keys: { "force_advantage": bool, "mitigate_crit_fail": bool }
func on_death_save_rolled(
	_unit_id: String,
	_roll: int,
	_successes: int,
	_failures: int,
	_status: String,
	_run_state: RunState
) -> Dictionary:
	return {}

## Called when a card is played in tactical grid / cerco.
func on_card_played(_player_id: String, _card_id: String, _target_zone: String, _run_state: RunState) -> Dictionary:
	return {}

# ── Virtual Economy & Campfire Hooks ─────────────────────────────────────────

## Modifies campfire resting recovery percent (e.g. 0.30 -> 0.45).
func on_campfire_rest(base_heal_pct: float, _run_state: RunState) -> float:
	return base_heal_pct

## Modifies post-combat victory rewards (e.g. rewards["gold"] += 10).
func on_combat_victory(rewards: Dictionary, _run_state: RunState) -> Dictionary:
	return rewards

## Modifies purchase price of items in the Forge (e.g. discount).
func on_forge_discount(_item_type: String, base_cost: int, _run_state: RunState) -> int:
	return base_cost

# ── State Reset & Serialization ──────────────────────────────────────────────

## Resets ephemeral combat state (charges, per-fight flags).
func reset_combat_state() -> void:
	counter = 0

func to_dict() -> Dictionary:
	return {
		"id": id,
		"relic_name": relic_name,
		"description": description,
		"rarity": rarity,
		"cost_gold": cost_gold,
		"counter": counter,
		"counter_max": counter_max,
		"is_active": is_active,
	}

func from_dict(data: Dictionary) -> void:
	id = str(data.get("id", id))
	relic_name = str(data.get("relic_name", relic_name))
	description = str(data.get("description", description))
	rarity = str(data.get("rarity", rarity))
	cost_gold = int(data.get("cost_gold", cost_gold))
	counter = int(data.get("counter", 0))
	counter_max = int(data.get("counter_max", 0))
	is_active = bool(data.get("is_active", true))

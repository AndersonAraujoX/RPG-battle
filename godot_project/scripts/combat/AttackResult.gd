# res://scripts/combat/AttackResult.gd
class_name AttackResult
extends RefCounted

var hit: bool = false
var is_critical: bool = false
var is_critical_miss: bool = false
var d20_roll: int = 0
var dice_rolled: Array[int] = []
var attack_modifier: int = 0
var total_attack: int = 0
var target_ac: int = 10
var cover_ac_bonus: int = 0
var had_advantage: bool = false
var had_disadvantage: bool = false
var modifiers_log: Array[String] = []
var damage_result: Variant = null # DamageResult

func to_dict() -> Dictionary:
	return {
		"hit": hit,
		"is_critical": is_critical,
		"is_critical_miss": is_critical_miss,
		"d20_roll": d20_roll,
		"dice_rolled": dice_rolled.duplicate(),
		"attack_modifier": attack_modifier,
		"total_attack": total_attack,
		"target_ac": target_ac,
		"cover_ac_bonus": cover_ac_bonus,
		"had_advantage": had_advantage,
		"had_disadvantage": had_disadvantage,
		"modifiers_log": modifiers_log.duplicate(),
		"damage_result": damage_result.to_dict() if damage_result != null and damage_result.has_method("to_dict") else null
	}

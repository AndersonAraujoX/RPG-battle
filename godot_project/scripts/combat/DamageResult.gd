# res://scripts/combat/DamageResult.gd
class_name DamageResult
extends RefCounted

var raw_damage: int = 0
var final_damage: int = 0
var damage_type: String = "cortante"
var is_critical: bool = false
var is_immune: bool = false
var is_resistant: bool = false
var is_vulnerable: bool = false
var dice_rolls: Array[int] = []
var dice_sum: int = 0
var modifier_applied: int = 0
var target_hp_before: int = 0
var target_hp_after: int = 0
var caused_unconscious: bool = false
var caused_death: bool = false

func to_dict() -> Dictionary:
	return {
		"raw_damage": raw_damage,
		"final_damage": final_damage,
		"damage_type": damage_type,
		"is_critical": is_critical,
		"is_immune": is_immune,
		"is_resistant": is_resistant,
		"is_vulnerable": is_vulnerable,
		"dice_rolls": dice_rolls.duplicate(),
		"dice_sum": dice_sum,
		"modifier_applied": modifier_applied,
		"target_hp_before": target_hp_before,
		"target_hp_after": target_hp_after,
		"caused_unconscious": caused_unconscious,
		"caused_death": caused_death
	}

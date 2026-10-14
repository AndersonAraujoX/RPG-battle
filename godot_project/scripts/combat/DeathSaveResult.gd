# res://scripts/combat/DeathSaveResult.gd
class_name DeathSaveResult
extends RefCounted

var roll: int = 0
var is_critical_success: bool = false
var is_critical_failure: bool = false
var is_success: bool = false
var successes: int = 0
var failures: int = 0
var previous_state: String = "INCONSCIENTE"
var new_state: String = "INCONSCIENTE"
var hp_recovered: int = 0

func to_dict() -> Dictionary:
	return {
		"roll": roll,
		"is_critical_success": is_critical_success,
		"is_critical_failure": is_critical_failure,
		"is_success": is_success,
		"successes": successes,
		"failures": failures,
		"previous_state": previous_state,
		"new_state": new_state,
		"hp_recovered": hp_recovered
	}

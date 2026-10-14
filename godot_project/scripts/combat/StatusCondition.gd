# res://scripts/combat/StatusCondition.gd
class_name StatusCondition
extends Resource

enum Category {
	CANONICAL_5E,
	ELEMENTAL,
	TACTICAL_BUFF,
	TACTICAL_DEBUFF
}

@export var id: String = ""
@export var display_name: String = ""
@export var category: Category = Category.CANONICAL_5E
@export var duration_turns: int = 1
@export var extra_data: Dictionary = {}

# Mechanics Flags
@export var blocks_action: bool = false
@export var blocks_movement: bool = false
@export var speed_multiplier: float = 1.0
@export var speed_bonus: int = 0

# Attack & Combat Modifiers
@export var grants_attacker_advantage: bool = false
@export var grants_attacker_disadvantage: bool = false
@export var inflicts_disadvantage_on_attack: bool = false
@export var inflicts_advantage_on_attack: bool = false
@export var auto_crit_range: float = 0.0

# Stat Offsets
@export var bonus_ac: int = 0
@export var bonus_attack_roll: int = 0
@export var bonus_damage: int = 0
@export var damage_resistance_modifier: float = 0.0

# Saving Throw Modifiers
@export var auto_fail_str_dex_saves: bool = false
@export var save_disadvantage_dex: bool = false
@export var save_advantage_dex: bool = false

# Damage Over Time (DoT)
@export var dot_fixed_damage: int = 0
@export var dot_percent_hp_max: float = 0.0
@export var dot_dice_count: int = 0
@export var dot_dice_faces: int = 0
@export var dot_damage_type: String = "fisico"

func duplicate_condition() -> StatusCondition:
	var copy: StatusCondition = StatusCondition.new()
	copy.id = id
	copy.display_name = display_name
	copy.category = category
	copy.duration_turns = duration_turns
	copy.extra_data = extra_data.duplicate(true)
	copy.blocks_action = blocks_action
	copy.blocks_movement = blocks_movement
	copy.speed_multiplier = speed_multiplier
	copy.speed_bonus = speed_bonus
	copy.grants_attacker_advantage = grants_attacker_advantage
	copy.grants_attacker_disadvantage = grants_attacker_disadvantage
	copy.inflicts_disadvantage_on_attack = inflicts_disadvantage_on_attack
	copy.inflicts_advantage_on_attack = inflicts_advantage_on_attack
	copy.auto_crit_range = auto_crit_range
	copy.bonus_ac = bonus_ac
	copy.bonus_attack_roll = bonus_attack_roll
	copy.bonus_damage = bonus_damage
	copy.damage_resistance_modifier = damage_resistance_modifier
	copy.auto_fail_str_dex_saves = auto_fail_str_dex_saves
	copy.save_disadvantage_dex = save_disadvantage_dex
	copy.save_advantage_dex = save_advantage_dex
	copy.dot_fixed_damage = dot_fixed_damage
	copy.dot_percent_hp_max = dot_percent_hp_max
	copy.dot_dice_count = dot_dice_count
	copy.dot_dice_faces = dot_dice_faces
	copy.dot_damage_type = dot_damage_type
	return copy

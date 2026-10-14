# res://scripts/resources/IsectumCasteData.gd
class_name IsectumCasteData
extends Resource

## IsectumCasteData: Custom Resource representing an Isectum caste unit profile.
## Encapsulates Cerco-specific stats, archetype flags (Brutamontes, Infiltrator,
## Catapult, Flyer), D6 attack dice, range, speed, and unique caste traits.

# ── Primary Milestone 3 Typed Fields ─────────────────────────────────────────
@export var id: String = ""
@export var caste_name: String = "":
	set(value):
		caste_name = value
		if name.is_empty():
			name = value

@export var hp: int = 4:
	set(value):
		hp = maxi(0, value)

@export var max_hp: int = 4:
	set(value):
		max_hp = maxi(1, value)

@export var is_brutamontes: bool = false
@export var is_infiltrator: bool = false
@export var is_catapult: bool = false
@export var is_flyer: bool = false

@export var speed: int = 3
@export var attack_dice: int = 2
@export var attack_range: int = 1
@export var trait_id: String = ""
@export var threat_cost: int = 1

# ── Compatibility & Presentation Fields ──────────────────────────────────────
@export var name: String = "":
	set(value):
		name = value
		if caste_name.is_empty():
			caste_name = value

@export var symbol: String = "🦗"
@export var description: String = ""
@export var ac: int = 12
@export var damage: int = 2
@export var threat_type: String = "tradicional"
@export var effect_id: String = ""
@export var is_boss: bool = false
@export var inverted_boss_effect: String = ""
@export var sprite_path: String = ""

# ── Lifecycle & State Methods ────────────────────────────────────────────────
func take_damage(amount: int) -> int:
	var effective_damage: int = maxi(0, amount)
	var prev_hp: int = hp
	hp = maxi(0, hp - effective_damage)
	return prev_hp - hp

func heal(amount: int) -> int:
	var effective_heal: int = maxi(0, amount)
	var prev_hp: int = hp
	hp = mini(max_hp, hp + effective_heal)
	return hp - prev_hp

func is_alive() -> bool:
	return hp > 0

func clone() -> IsectumCasteData:
	var copy_caste: IsectumCasteData = IsectumCasteData.new()
	copy_caste.id = id
	copy_caste.caste_name = caste_name
	copy_caste.name = name
	copy_caste.hp = hp
	copy_caste.max_hp = max_hp
	copy_caste.is_brutamontes = is_brutamontes
	copy_caste.is_infiltrator = is_infiltrator
	copy_caste.is_catapult = is_catapult
	copy_caste.is_flyer = is_flyer
	copy_caste.speed = speed
	copy_caste.attack_dice = attack_dice
	copy_caste.attack_range = attack_range
	copy_caste.trait_id = trait_id
	copy_caste.threat_cost = threat_cost
	copy_caste.symbol = symbol
	copy_caste.description = description
	copy_caste.ac = ac
	copy_caste.damage = damage
	copy_caste.threat_type = threat_type
	copy_caste.effect_id = effect_id
	copy_caste.is_boss = is_boss
	copy_caste.inverted_boss_effect = inverted_boss_effect
	copy_caste.sprite_path = sprite_path
	return copy_caste

func to_dict() -> Dictionary:
	return {
		"id": id,
		"caste_name": caste_name,
		"name": name,
		"hp": hp,
		"max_hp": max_hp,
		"is_brutamontes": is_brutamontes,
		"is_infiltrator": is_infiltrator,
		"is_catapult": is_catapult,
		"is_flyer": is_flyer,
		"speed": speed,
		"attack_dice": attack_dice,
		"attack_range": attack_range,
		"trait_id": trait_id,
		"threat_cost": threat_cost,
		"symbol": symbol,
		"description": description,
		"is_boss": is_boss
	}

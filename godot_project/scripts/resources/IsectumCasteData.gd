# res://scripts/resources/IsectumCasteData.gd
class_name IsectumCasteData
extends Resource

@export var id: String = ""
@export var name: String = ""
@export var symbol: String = "🦗"
@export var description: String = ""
@export var hp: int = 4
@export var ac: int = 12
@export var damage: int = 2
@export var speed: int = 3
@export var threat_type: String = "tradicional" # "tradicional" or "sobrenatural"
@export var effect_id: String = ""
@export var is_boss: bool = false
@export var inverted_boss_effect: String = ""
@export var sprite_path: String = ""

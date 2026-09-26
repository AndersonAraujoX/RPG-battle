# res://scripts/resources/CardData.gd
class_name CardData
extends Resource

@export var id: String = ""
@export var name: String = ""
@export var symbol: String = "⚔"
@export var card_type: String = "basica" # "basica", "defesa", "runa", "upgrade"
@export var subtype: String = "acao"     # "reacao", "continua", "passiva", "acao_extra"
@export var cost: Dictionary = {}        # {"madeira": 1, "metal": 2, "cristal": 0}
@export var description: String = ""
@export var movement: int = 0
@export var work: int = 0
@export var excavation: int = 0
@export var effect: String = ""

# Alias for Portuguese nomenclature used in Cerco mode
var escavacao: int:
	get:
		return excavation
	set(value):
		excavation = value

var movimento: int:
	get:
		return movement
	set(value):
		movement = value

var trabalho: int:
	get:
		return work
	set(value):
		work = value

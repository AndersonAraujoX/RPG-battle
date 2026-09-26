# res://scripts/resources/CharacterData.gd
class_name CharacterData
extends Resource

@export var id: String = ""
@export var name: String = ""
@export var team: String = "A" # "A" = Heroes, "B" = Enemies

# D&D 5e Ability Scores
@export var forca: int = 10
@export var destreza: int = 10
@export var constituicao: int = 10
@export var inteligencia: int = 10
@export var sabedoria: int = 10
@export var carisma: int = 10

# Stats dictionary for backward/forward compatibility with tests and Python models
@export var stats: Dictionary = {
	"forca": 10,
	"destreza": 10,
	"constituicao": 10,
	"inteligencia": 10,
	"sabedoria": 10,
	"carisma": 10
}

# Combat Vitals & Metrics
@export var hp: int = 10
@export var max_hp: int = 10
@export var ac: int = 10
@export var velocidade: int = 3
@export var alcance: int = 1
@export var tipo_dano: String = "Cortante"

# Dice Formulas [count, faces] e.g. [1, 10]
@export var dado_vida: Array = [1, 8]
@export var dado_dano: Array = [1, 6]

# Resistances & Vulnerabilities
@export var resistencias: Dictionary = {}   # e.g. {"Necrotico": 0.5}
@export var vulnerabilidades: Dictionary = {} # e.g. {"Esmagamento": 2.0}
@export var imunidades: Array = []

# Perks & Level
@export var nivel: int = 1
@export var perks: Array = []

func get_modifier(stat_value: int) -> int:
	return int(floor((float(stat_value) - 10.0) / 2.0))

func get_proficiency_bonus() -> int:
	return 1 + int(ceil(float(nivel) / 4.0))

func sync_stats_dict() -> void:
	stats["forca"] = forca
	stats["destreza"] = destreza
	stats["constituicao"] = constituicao
	stats["inteligencia"] = inteligencia
	stats["sabedoria"] = sabedoria
	stats["carisma"] = carisma

func duplicate_data() -> CharacterData:
	var copy: CharacterData = CharacterData.new()
	copy.id = id
	copy.name = name
	copy.team = team
	copy.forca = forca
	copy.destreza = destreza
	copy.constituicao = constituicao
	copy.inteligencia = inteligencia
	copy.sabedoria = sabedoria
	copy.carisma = carisma
	copy.stats = stats.duplicate(true)
	copy.hp = hp
	copy.max_hp = max_hp
	copy.ac = ac
	copy.velocidade = velocidade
	copy.alcance = alcance
	copy.tipo_dano = tipo_dano
	copy.dado_vida = dado_vida.duplicate()
	copy.dado_dano = dado_dano.duplicate()
	copy.resistencias = resistencias.duplicate(true)
	copy.vulnerabilidades = vulnerabilidades.duplicate(true)
	copy.imunidades = imunidades.duplicate()
	copy.nivel = nivel
	copy.perks = perks.duplicate()
	return copy

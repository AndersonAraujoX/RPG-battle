# res://scripts/autoload/DataManager.gd
extends Node

## Centralized Data Manager Singleton (DataManager.gd)
## Parses, validates, caches, and serves structured game resources.

const CANONICAL_HERO_IDS: Array[String] = [
	"Aquele", "Stark", "Elden", "Doom", "Gruu",
	"Kuro", "Darwin", "Novak", "Rilem", "Yukito", "Koema"
]

const CANONICAL_CLASS_IDS: Array[String] = [
	"Guerreiro", "Mago", "Ladino", "Arqueiro", "Barbaro",
	"Clerigo", "Paladino", "Druida", "Bruxo"
]

const DEFAULT_PERSONAGENS_PATH: String = "res://dados/personagens.json"

var _characters_cache: Dictionary = {} # Dictionary[String, CharacterData]
var _castes_cache: Dictionary = {}      # Dictionary[String, IsectumCasteData]
var _cards_cache: Dictionary = {}       # Dictionary[String, CardData]
var _is_loaded: bool = false

func _init() -> void:
	name = "DataManager"

func _ready() -> void:
	load_all_data()

func is_data_loaded() -> bool:
	return _is_loaded

func clear_cache() -> void:
	_characters_cache.clear()
	_castes_cache.clear()
	_cards_cache.clear()
	_is_loaded = false

## Loads all structured game data from default or custom JSON paths
func load_all_data(path: String = DEFAULT_PERSONAGENS_PATH) -> bool:
	clear_cache()
	var success = load_from_file(path)
	_load_fallback_castes()
	_load_fallback_cards()
	_is_loaded = success
	return success

## Ingests JSON data directly from a file
func load_from_file(file_path: String) -> bool:
	if not FileAccess.file_exists(file_path):
		push_warning("[DataManager] File '%s' not found." % file_path)
		return false

	var file: FileAccess = FileAccess.open(file_path, FileAccess.READ)
	if file == null:
		var err: Error = FileAccess.get_open_error()
		push_error("[DataManager] Could not open '%s'. Error code: %d" % [file_path, err])
		return false

	var json_text: String = file.get_as_text()
	file.close()

	return parse_raw_json(json_text)

## Parses raw JSON text into structured character models
func parse_raw_json(json_string: String) -> bool:
	var json: JSON = JSON.new()
	var error: Error = json.parse(json_string)
	if error != OK:
		push_error("[DataManager] JSON Parse Error on line %d: %s" % [json.get_error_line(), json.get_error_message()])
		return false

	if not (json.data is Dictionary):
		push_error("[DataManager] Root JSON data is not a Dictionary.")
		return false

	var raw_dict: Dictionary = json.data
	for key in raw_dict.keys():
		var entry = raw_dict[key]
		if entry is Dictionary:
			var char_data: CharacterData = _parse_single_character(key, entry)
			_characters_cache[key] = char_data

	_is_loaded = true
	return true

## Method wrapper for Error enum return
func parse_characters_from_string(json_string: String) -> Error:
	var ok = parse_raw_json(json_string)
	return OK if ok else ERR_PARSE_ERROR

func _parse_single_character(char_id: String, d: Dictionary) -> CharacterData:
	var c: CharacterData = CharacterData.new()
	c.id = char_id
	c.name = d.get("nome", char_id)
	c.team = d.get("time", "A" if (CANONICAL_HERO_IDS.has(char_id) or CANONICAL_CLASS_IDS.has(char_id)) else "B")

	var stats: Dictionary = d.get("stats", {})
	c.forca = int(stats.get("forca", 10))
	c.destreza = int(stats.get("destreza", 10))
	c.constituicao = int(stats.get("constituicao", 10))
	c.inteligencia = int(stats.get("inteligencia", 10))
	c.sabedoria = int(stats.get("sabedoria", 10))
	c.carisma = int(stats.get("carisma", 10))
	c.sync_stats_dict()

	c.ac = int(d.get("ac", 10))
	c.velocidade = int(d.get("velocidade", 3))
	c.alcance = int(d.get("alcance", 1))
	c.tipo_dano = str(d.get("tipo_dano", "Cortante"))

	if d.has("hp"):
		c.max_hp = int(d["hp"])
		c.hp = c.max_hp
	else:
		var con_mod: int = c.get_modifier(c.constituicao)
		var dice: Array = d.get("dado_vida", [1, 8])
		c.max_hp = max(1, int(dice[1]) + con_mod)
		c.hp = c.max_hp

	if d.has("dado_vida") and d["dado_vida"] is Array and d["dado_vida"].size() >= 2:
		c.dado_vida = [int(d["dado_vida"][0]), int(d["dado_vida"][1])]
	if d.has("dado_dano") and d["dado_dano"] is Array and d["dado_dano"].size() >= 2:
		c.dado_dano = [int(d["dado_dano"][0]), int(d["dado_dano"][1])]

	c.resistencias = d.get("resistencias", {})
	c.vulnerabilidades = d.get("vulnerabilidades", {})
	c.imunidades = d.get("imunidades", [])

	return c

# ── Character & Hero Accessors ──────────────────────────────────────────────

func get_hero_data(hero_id: String) -> CharacterData:
	if hero_id.is_empty():
		return null
	if not _characters_cache.has(hero_id):
		return null
	return _characters_cache[hero_id]

func get_character_data(char_id: String) -> CharacterData:
	return get_hero_data(char_id)

func get_hero_duplicate(hero_id: String) -> CharacterData:
	var h = get_hero_data(hero_id)
	return h.duplicate_data() if h != null else null

func get_all_heroes() -> Array[CharacterData]:
	var result: Array[CharacterData] = []
	for c in _characters_cache.values():
		result.append(c)
	return result

func has_character(char_id: String) -> bool:
	return _characters_cache.has(char_id)

# ── Isectum Caste Accessors ─────────────────────────────────────────────────

func get_isectum_caste(caste_id: String) -> IsectumCasteData:
	if caste_id.is_empty():
		return null
	return _castes_cache.get(caste_id, null)

func get_all_isectum_castes() -> Array[IsectumCasteData]:
	var result: Array[IsectumCasteData] = []
	for caste in _castes_cache.values():
		result.append(caste)
	return result

func has_caste(caste_id: String) -> bool:
	return _castes_cache.has(caste_id)

# ── Card Accessors ──────────────────────────────────────────────────────────

func get_card_data(card_id: String) -> CardData:
	if card_id.is_empty():
		return null
	return _cards_cache.get(card_id, null)

func get_all_cards() -> Array[CardData]:
	var result: Array[CardData] = []
	for card in _cards_cache.values():
		result.append(card)
	return result

func has_card(card_id: String) -> bool:
	return _cards_cache.has(card_id)

# ── Fallback Setup ──────────────────────────────────────────────────────────

func _load_fallback_castes() -> void:
	var default_castes: Array[String] = [
		"vespa_cacadora", "louva_deus", "viuva_canibal", "escaravelho_necrofago",
		"besouro_unicornio", "gafanhoto_praga", "carrapato_vampiro", "libelula_blindada",
		"besouro_gorgulho", "cigarra_ressonante", "enxame_rainha", "vagalume_sombras",
		"larva_carniceira", "tarantula_golias", "formiga_correicao", "aranha_clepto",
		"centopeia_olhos", "abelha_tecela", "mariposa_esfinge", "efemera_mimetica",
		"vespa_joia", "viuva_negra", "besouro_rinoceronte", "mosca_tse_tse"
	]
	for caste_id in default_castes:
		var c: IsectumCasteData = IsectumCasteData.new()
		c.id = caste_id
		c.name = caste_id.capitalize()
		c.hp = 5
		c.ac = 12
		c.damage = 2
		c.speed = 3
		c.threat_type = "tradicional"
		c.effect_id = caste_id
		_castes_cache[caste_id] = c

func _load_fallback_cards() -> void:
	var default_cards: Array[Dictionary] = [
		{"id": "trabalho_1", "nome": "Trabalho", "tipo": "basica", "trabalho": 3},
		{"id": "movimento_1", "nome": "Movimento", "tipo": "basica", "movimento": 3},
		{"id": "escavacao_1", "nome": "Escavação", "tipo": "basica", "escavacao": 3},
		{"id": "escudo_quitina", "nome": "Escudo de Quitina", "tipo": "defesa", "subtipo": "reacao"},
		{"id": "runa_haste", "nome": "Runa da Haste", "tipo": "runa", "subtipo": "acao_extra"}
	]
	for c_dict in default_cards:
		var c: CardData = CardData.new()
		c.id = c_dict["id"]
		c.name = c_dict["nome"]
		c.card_type = c_dict["tipo"]
		c.subtype = c_dict.get("subtipo", "acao")
		c.work = c_dict.get("trabalho", 0)
		c.movement = c_dict.get("movimento", 0)
		c.excavation = c_dict.get("escavacao", 0)
		_cards_cache[c.id] = c

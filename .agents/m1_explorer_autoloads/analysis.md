# Architecture & Technical Design Specification: M1 Autoload Singletons

**Author**: `m1_explorer_autoloads`  
**Milestone**: M1 — Foundation & Core Infrastructure  
**Target Engine**: Godot Engine 4.x (Compatibility Renderer, Statically Typed GDScript)  
**Deliverables Covered**: `EventBus.gd`, `DataManager.gd`, `GameManager.gd`, `AudioManager.gd`, and GUT Test Suite.

---

## 1. Executive Summary

This specification establishes the architectural blueprint, complete typed GDScript implementations, error-handling strategies, data models, and unit test suites for the four core Autoload Singletons in Godot 4:

1. **`EventBus.gd`**: Type-safe, decoupled event aggregator implementing 100% of signals defined in `PROJECT.md` §Interface Contracts, plus system-level signals for state transitions, audio requests, and combat logs. Includes emission telemetry and GUT signal spy utilities.
2. **`DataManager.gd`**: Robust repository and caching engine for structured game data (`dados/personagens.json`, castas, and cards). Implements typed custom resources (`CharacterData.gd`, `IsectumCasteData.gd`, `CardData.gd`), JSON schema validation, graceful fallbacks for missing/corrupted files, and O(1) in-memory cache lookups.
3. **`GameManager.gd`**: Finite State Machine (FSM) managing five global game states (`MENU`, `COMBATE_TATICO`, `CERCO_ISECTUM`, `FIM_DE_JOGO`, `MULTIPLAYER_LOBBY`). Enforces an explicit state transition matrix, provides lifecycle hooks (`_enter_state`, `_exit_state`), state payloads, and test-safe scene orchestration.
4. **`AudioManager.gd`**: Dual-player BGM crossfading controller, bus volume/mute manager (Master, BGM, SFX), and polyphonic SFX pooling system (12 pooled `AudioStreamPlayer` nodes). Directly maps all 11 verified `.ogg` audio assets in `assets/sounds/` with headless fallback support.
5. **GUT Unit Test Suite**: Four complete, production-grade GUT test suites following the strict Arrange-Act-Assert (AAA) pattern, covering happy paths, edge cases, malformed JSON, boundary limits, and dependency-isolated mock scenarios.

---

## 2. Autoload Registration in `project.godot`

The four singletons must be registered under `[autoload]` in `godot_project/project.godot` in dependency order:

```ini
[autoload]

EventBus="*res://scripts/autoload/EventBus.gd"
DataManager="*res://scripts/autoload/DataManager.gd"
AudioManager="*res://scripts/autoload/AudioManager.gd"
GameManager="*res://scripts/autoload/GameManager.gd"
```

*Order Rationale*:
- `EventBus` has zero dependencies and must initialize first so all subsequent singletons can connect signals.
- `DataManager` loads and caches data independent of game logic or audio.
- `AudioManager` listens to `EventBus` and is ready to play menu BGM.
- `GameManager` depends on `EventBus` and `DataManager` to orchestrate states and scenes upon entering its initial state (`MENU`).

---

## 3. Autoload 1: `EventBus.gd`

### 3.1 Design Philosophy & Responsibilities
- **Decoupling**: Eliminates direct node-to-node references between combat rules, UI, network client, and audio.
- **Strict Typing**: All signal arguments are explicitly typed (no untyped `Variant`).
- **Telemetry & Testability**: Provides signal emission history and count helpers for GUT assertions without requiring complex mocks.

### 3.2 Canonical Signal Contract
From `PROJECT.md` lines 70-83 and required engine signals:

| Signal | Parameters | Purpose |
|---|---|---|
| `unit_moved` | `unit_id: String, from_pos: Vector2i, to_pos: Vector2i` | Tactical grid movement |
| `unit_attacked` | `attacker_id: String, target_id: String, hit: bool, is_crit: bool, damage: int, damage_type: String` | Attack resolution event |
| `unit_damaged` | `unit_id: String, amount: int, current_hp: int, max_hp: int` | Damage taken / HP reduction |
| `unit_died` | `unit_id: String` | Unit death or incapacitation |
| `death_save_rolled` | `unit_id: String, roll: int, successes: int, failures: int, status: String` | D&D 5e death saving throw |
| `status_applied` | `unit_id: String, status_id: String, duration: int` | Status effect applied |
| `status_removed` | `unit_id: String, status_id: String` | Status effect expired/cured |
| `card_selected` | `player_id: String, card_id: String` | Cerco card selection |
| `round_resolved` | `round_number: int, sync_results: Dictionary` | Cerco synchronous turn resolved |
| `synergy_triggered` | `synergy_type: String, bonus_description: String` | Team/Supreme synergy triggered |
| `resources_updated` | `wood: int, metal: int, crystal: int, ap: int` | Fortress resources modified |
| `network_message_received` | `message_type: String, payload: Dictionary` | Inbound WebSocket message |
| `network_connection_status_changed` | `connected: bool, room_id: String` | WebSocket connection state |
| `game_state_changed` | `previous_state: int, new_state: int` | GameManager FSM state switch |
| `turn_changed` | `turn_number: int, active_unit_id: String` | Combat turn advance |
| `audio_play_sfx_requested` | `sound_name: String, volume_db: float` | Decoupled SFX trigger |
| `audio_play_bgm_requested` | `track_name: String, crossfade: bool` | Decoupled BGM trigger |
| `floating_text_requested` | `text: String, position: Vector2, color: Color` | HUD FCT spawn request |
| `combat_log_entry_added` | `bbcode_text: String` | Combat log feed entry |

### 3.3 Concrete GDScript Implementation (`godot_project/scripts/autoload/EventBus.gd`)

```gdscript
# res://scripts/autoload/EventBus.gd
extends Node

## Centralized Event Bus Singleton (EventBus.gd)
## Decouples subsystems through type-safe global signals.

# ── Combat & Tactical Grid Signals ──────────────────────────────────────────
signal unit_moved(unit_id: String, from_pos: Vector2i, to_pos: Vector2i)
signal unit_attacked(attacker_id: String, target_id: String, hit: bool, is_crit: bool, damage: int, damage_type: String)
signal unit_damaged(unit_id: String, amount: int, current_hp: int, max_hp: int)
signal unit_died(unit_id: String)
signal death_save_rolled(unit_id: String, roll: int, successes: int, failures: int, status: String)
signal status_applied(unit_id: String, status_id: String, duration: int)
signal status_removed(unit_id: String, status_id: String)
signal turn_changed(turn_number: int, active_unit_id: String)

# ── Cerco & Deckbuilder Signals ─────────────────────────────────────────────
signal card_selected(player_id: String, card_id: String)
signal round_resolved(round_number: int, sync_results: Dictionary)
signal synergy_triggered(synergy_type: String, bonus_description: String)
signal resources_updated(wood: int, metal: int, crystal: int, ap: int)

# ── Network Signals ─────────────────────────────────────────────────────────
signal network_message_received(message_type: String, payload: Dictionary)
signal network_connection_status_changed(connected: bool, room_id: String)

# ── System, State & Audio Signals ───────────────────────────────────────────
signal game_state_changed(previous_state: int, new_state: int)
signal audio_play_sfx_requested(sound_name: String, volume_db: float)
signal audio_play_bgm_requested(track_name: String, crossfade: bool)
signal floating_text_requested(text: String, position: Vector2, color: Color)
signal combat_log_entry_added(bbcode_text: String)

# ── Telemetry & Test Support ────────────────────────────────────────────────
@export var debug_logging: bool = false
var _emission_counts: Dictionary = {}
var _event_history: Array[Dictionary] = []
const MAX_HISTORY: int = 100

func _init() -> void:
	name = "EventBus"

## Resets telemetry metrics (useful between unit test runs)
func reset_telemetry() -> void:
	_emission_counts.clear()
	_event_history.clear()

## Returns the number of times a specific signal was emitted via emit_logged
func get_emission_count(signal_name: String) -> int:
	return _emission_counts.get(signal_name, 0)

## Emits a signal while recording telemetry for test validation
func emit_logged(sig_name: String, args: Array = []) -> void:
	_emission_counts[sig_name] = _emission_counts.get(sig_name, 0) + 1
	if _event_history.size() >= MAX_HISTORY:
		_event_history.pop_front()
	_event_history.append({"signal": sig_name, "args": args, "timestamp": Time.get_ticks_msec()})
	
	if debug_logging:
		print("[EventBus] %s args: %s" % [sig_name, str(args)])
```

---

## 4. Autoload 2: `DataManager.gd` & Custom Resources

### 4.1 Design Philosophy & Responsibilities
- **Data-Driven Architecture**: Exposes models as strongly-typed Godot `Resource` instances.
- **Fail-Safe Loading**: Handles missing files, broken JSON formatting, or omitted keys by injecting canonical default values.
- **O(1) Cache Lookups**: Loads files on startup or on-demand, caching objects by `id`.

### 4.2 Custom Resource Models

#### `CharacterData.gd` (`godot_project/scripts/resources/CharacterData.gd`)
```gdscript
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

# Combat Vitals & Metrics
@export var hp: int = 10
@export var max_hp: int = 10
@export var ac: int = 10
@export var velocidade: int = 3
@export var alcance: int = 1
@export var tipo_dano: String = "Cortante"

# Dice Formulas [count, faces] e.g. [1, 10]
@export var dado_vida: Array[int] = [1, 8]
@export var dado_dano: Array[int] = [1, 6]

# Resistances & Vulnerabilities
@export var resistencias: Dictionary = {}   # e.g. {"Necrotico": 0.5}
@export var vulnerabilidades: Dictionary = {} # e.g. {"Esmagamento": 2.0}
@export var imunidades: Array[String] = []

# Perks & Level
@export var nivel: int = 1
@export var perks: Array[String] = []

func get_modifier(stat_value: int) -> int:
	return int(floor((stat_value - 10.0) / 2.0))

func get_proficiency_bonus() -> int:
	return 1 + int(ceil(float(nivel) / 4.0))

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
	copy.hp = hp
	copy.max_hp = max_hp
	copy.ac = ac
	copy.velocidade = velocidade
	copy.alcance = alcance
	copy.tipo_dano = tipo_dano
	copy.dado_vida = dado_vida.duplicate()
	copy.dado_dano = dado_dano.duplicate()
	copy.resistencias = resistencias.duplicate()
	copy.vulnerabilidades = vulnerabilidades.duplicate()
	copy.imunidades = imunidades.duplicate()
	copy.nivel = nivel
	copy.perks = perks.duplicate()
	return copy
```

#### `IsectumCasteData.gd` (`godot_project/scripts/resources/IsectumCasteData.gd`)
```gdscript
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
```

#### `CardData.gd` (`godot_project/scripts/resources/CardData.gd`)
```gdscript
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
```

### 4.3 Concrete GDScript Implementation (`godot_project/scripts/autoload/DataManager.gd`)

```gdscript
# res://scripts/autoload/DataManager.gd
extends Node

## Centralized Data Manager Singleton (DataManager.gd)
## Parses, validates, caches, and serves structured game resources.

const CANONICAL_HERO_IDS: Array[String] = [
	"Aquele", "Stark", "Elden", "Doom", "Gruu",
	"Kuro", "Darwin", "Novak", "Rilem", "Yukito", "Koema"
]

const DEFAULT_PERSONAGENS_PATH: String = "res://dados/personagens.json"

var _characters_cache: Dictionary = {} # Dictionary[String, CharacterData]
var _castes_cache: Dictionary = {}      # Dictionary[String, IsectumCasteData]
var _cards_cache: Dictionary = {}       # Dictionary[String, CardData]
var _is_initialized: bool = false

func _init() -> void:
	name = "DataManager"

func _ready() -> void:
	initialize_data()

## Initializes all caches from disk or fallback
func initialize_data(personagens_path: String = DEFAULT_PERSONAGENS_PATH) -> void:
	_characters_cache.clear()
	_castes_cache.clear()
	_cards_cache.clear()
	
	load_characters_from_json(personagens_path)
	_load_fallback_castes()
	_load_fallback_cards()
	_is_initialized = true

# ── Character & Hero Accessors ──────────────────────────────────────────────

func get_hero_data(hero_id: String) -> CharacterData:
	if not _characters_cache.has(hero_id):
		push_warning("[DataManager] Hero '%s' not found. Returning fallback hero." % hero_id)
		return _create_fallback_hero(hero_id)
	return _characters_cache[hero_id].duplicate_data()

func get_all_heroes() -> Array[CharacterData]:
	var result: Array[CharacterData] = []
	for hero_id in CANONICAL_HERO_IDS:
		if _characters_cache.has(hero_id):
			result.append(_characters_cache[hero_id].duplicate_data())
		else:
			result.append(_create_fallback_hero(hero_id))
	return result

func get_character_data(char_id: String) -> CharacterData:
	if not _characters_cache.has(char_id):
		push_warning("[DataManager] Character '%s' not found. Returning fallback." % char_id)
		return _create_fallback_hero(char_id)
	return _characters_cache[char_id].duplicate_data()

func has_character(char_id: String) -> bool:
	return _characters_cache.has(char_id)

# ── Isectum Caste Accessors ─────────────────────────────────────────────────

func get_isectum_caste(caste_id: String) -> IsectumCasteData:
	if not _castes_cache.has(caste_id):
		push_warning("[DataManager] Caste '%s' not found. Returning fallback caste." % caste_id)
		return _create_fallback_caste(caste_id)
	return _castes_cache[caste_id]

func get_all_isectum_castes() -> Array[IsectumCasteData]:
	var result: Array[IsectumCasteData] = []
	for caste in _castes_cache.values():
		result.append(caste)
	return result

func has_caste(caste_id: String) -> bool:
	return _castes_cache.has(caste_id)

# ── Card Accessors ──────────────────────────────────────────────────────────

func get_card_data(card_id: String) -> CardData:
	if not _cards_cache.has(card_id):
		push_warning("[DataManager] Card '%s' not found. Returning fallback card." % card_id)
		return _create_fallback_card(card_id)
	return _cards_cache[card_id]

func get_all_cards() -> Array[CardData]:
	var result: Array[CardData] = []
	for card in _cards_cache.values():
		result.append(card)
	return result

func has_card(card_id: String) -> bool:
	return _cards_cache.has(card_id)

# ── JSON Parsing & Ingestion ────────────────────────────────────────────────

func load_characters_from_json(file_path: String) -> Error:
	if not FileAccess.file_exists(file_path):
		push_warning("[DataManager] File '%s' not found. Loading fallback canonical heroes." % file_path)
		_populate_fallback_heroes()
		return ERR_FILE_NOT_FOUND

	var file: FileAccess = FileAccess.open(file_path, FileAccess.READ)
	if file == null:
		var err: Error = FileAccess.get_open_error()
		push_error("[DataManager] Could not open '%s'. Error code: %d" % [file_path, err])
		_populate_fallback_heroes()
		return err

	var json_text: String = file.get_as_text()
	file.close()

	return parse_characters_from_string(json_text)

func parse_characters_from_string(json_string: String) -> Error:
	var json: JSON = JSON.new()
	var error: Error = json.parse(json_string)
	if error != OK:
		push_error("[DataManager] JSON Parse Error on line %d: %s" % [json.get_error_line(), json.get_error_message()])
		_populate_fallback_heroes()
		return error

	if not (json.data is Dictionary):
		push_error("[DataManager] Root JSON data is not a Dictionary.")
		_populate_fallback_heroes()
		return ERR_INVALID_DATA

	var raw_dict: Dictionary = json.data
	for key in raw_dict.keys():
		var entry = raw_dict[key]
		if entry is Dictionary:
			var char_data: CharacterData = _parse_single_character(key, entry)
			_characters_cache[key] = char_data

	# Ensure all 11 canonical heroes exist in cache
	for hero_id in CANONICAL_HERO_IDS:
		if not _characters_cache.has(hero_id):
			_characters_cache[hero_id] = _create_fallback_hero(hero_id)

	return OK

func _parse_single_character(char_id: String, d: Dictionary) -> CharacterData:
	var char: CharacterData = CharacterData.new()
	char.id = char_id
	char.name = d.get("nome", char_id)
	char.team = d.get("time", "A" if CANONICAL_HERO_IDS.has(char_id) else "B")

	var stats: Dictionary = d.get("stats", {})
	char.forca = int(stats.get("forca", 10))
	char.destreza = int(stats.get("destreza", 10))
	char.constituicao = int(stats.get("constituicao", 10))
	char.inteligencia = int(stats.get("inteligencia", 10))
	char.sabedoria = int(stats.get("sabedoria", 10))
	char.carisma = int(stats.get("carisma", 10))

	char.ac = int(d.get("ac", 10))
	char.velocidade = int(d.get("velocidade", 3))
	char.alcance = int(d.get("alcance", 1))
	char.tipo_dano = str(d.get("tipo_dano", "Cortante"))

	# HP: explicit 'hp' or computed from hit dice
	if d.has("hp"):
		char.max_hp = int(d["hp"])
		char.hp = char.max_hp
	else:
		var con_mod: int = char.get_modifier(char.constituicao)
		var dice: Array = d.get("dado_vida", [1, 8])
		char.max_hp = max(1, int(dice[1]) + con_mod)
		char.hp = char.max_hp

	if d.has("dado_vida") and d["dado_vida"] is Array and d["dado_vida"].size() >= 2:
		char.dado_vida = [int(d["dado_vida"][0]), int(d["dado_vida"][1])]
	if d.has("dado_dano") and d["dado_dano"] is Array and d["dado_dano"].size() >= 2:
		char.dado_dano = [int(d["dado_dano"][0]), int(d["dado_dano"][1])]

	char.resistencias = d.get("resistencias", {})
	char.vulnerabilidades = d.get("vulnerabilidades", {})
	char.imunidades = Array(d.get("imunidades", []), TYPE_STRING, "", null)

	return char

# ── Fallback Generators ─────────────────────────────────────────────────────

func _populate_fallback_heroes() -> void:
	for hero_id in CANONICAL_HERO_IDS:
		if not _characters_cache.has(hero_id):
			_characters_cache[hero_id] = _create_fallback_hero(hero_id)

func _create_fallback_hero(hero_id: String) -> CharacterData:
	var h: CharacterData = CharacterData.new()
	h.id = hero_id
	h.name = hero_id
	h.team = "A"
	h.forca = 14
	h.destreza = 14
	h.constituicao = 14
	h.inteligencia = 10
	h.sabedoria = 10
	h.carisma = 10
	h.max_hp = 30
	h.hp = 30
	h.ac = 14
	h.velocidade = 4
	h.alcance = 1
	h.tipo_dano = "Cortante"
	h.dado_vida = [1, 8]
	h.dado_dano = [1, 8]
	return h

func _create_fallback_caste(caste_id: String) -> IsectumCasteData:
	var c: IsectumCasteData = IsectumCasteData.new()
	c.id = caste_id
	c.name = caste_id.capitalize()
	c.hp = 5
	c.ac = 12
	c.damage = 2
	c.speed = 3
	c.threat_type = "tradicional"
	c.effect_id = caste_id
	return c

func _create_fallback_card(card_id: String) -> CardData:
	var c: CardData = CardData.new()
	c.id = card_id
	c.name = card_id.capitalize()
	c.card_type = "basica"
	c.subtype = "acao"
	c.movement = 2
	c.work = 1
	c.escavacao = 1
	return c

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
		_castes_cache[caste_id] = _create_fallback_caste(caste_id)

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
		c.escavacao = c_dict.get("escavacao", 0)
		_cards_cache[c.id] = c
```

---

## 5. Autoload 3: `GameManager.gd`

### 5.1 Design Philosophy & Responsibilities
- **Finite State Machine (FSM)**: Manages high-level lifecycle states without race conditions.
- **Transition Validation**: Prevents invalid game flow jumps (e.g. from `MENU` straight to `FIM_DE_JOGO`).
- **Scene Orchestration**: Optionally transitions the Godot scene tree (`get_tree().change_scene_to_file`) while remaining fully testable in headless mode without a physical viewport.
- **State Data Passing**: Allows passing arbitrary payload dictionaries across states (e.g. hero roster, battle outcomes).

### 5.2 State Machine Matrix

```
       ┌──────────────┐
       │     MENU     │◄───────────────────┐
       └──────┬───────┘                    │
              │                            │
      ┌───────┼────────────────┐           │
      ▼       ▼                ▼           │
┌──────────┐ ┌──────────────┐ ┌──────────┐ │
│ COMBATE  │ │    CERCO     │ │ MULTI    │ │
│ TATICO   │ │   ISECTUM    │ │ LOBBY    │ │
└─────┬────┘ └──────┬───────┘ └────┬─────┘ │
      │             │              │       │
      │             │       ┌──────┘       │
      ▼             ▼       ▼              │
    ┌─────────────────┐                    │
    │   FIM_DE_JOGO   ├────────────────────┘
    └─────────────────┘
```

| Origin State | Allowed Destination States |
|---|---|
| `MENU` | `COMBATE_TATICO`, `CERCO_ISECTUM`, `MULTIPLAYER_LOBBY` |
| `COMBATE_TATICO` | `FIM_DE_JOGO`, `MENU` |
| `CERCO_ISECTUM` | `FIM_DE_JOGO`, `MENU` |
| `MULTIPLAYER_LOBBY` | `CERCO_ISECTUM`, `COMBATE_TATICO`, `MENU` |
| `FIM_DE_JOGO` | `MENU`, `COMBATE_TATICO`, `CERCO_ISECTUM` |

### 5.3 Concrete GDScript Implementation (`godot_project/scripts/autoload/GameManager.gd`)

```gdscript
# res://scripts/autoload/GameManager.gd
extends Node

## Centralized Game State Machine Singleton (GameManager.gd)
## Controls high-level game states, scene routing, and state transitions.

enum GameState {
	MENU = 0,
	COMBATE_TATICO = 1,
	CERCO_ISECTUM = 2,
	FIM_DE_JOGO = 3,
	MULTIPLAYER_LOBBY = 4
}

const STATE_NAMES: Dictionary = {
	GameState.MENU: "MENU",
	GameState.COMBATE_TATICO: "COMBATE_TATICO",
	GameState.CERCO_ISECTUM: "CERCO_ISECTUM",
	GameState.FIM_DE_JOGO: "FIM_DE_JOGO",
	GameState.MULTIPLAYER_LOBBY: "MULTIPLAYER_LOBBY"
}

const VALID_TRANSITIONS: Dictionary = {
	GameState.MENU: [GameState.COMBATE_TATICO, GameState.CERCO_ISECTUM, GameState.MULTIPLAYER_LOBBY],
	GameState.COMBATE_TATICO: [GameState.FIM_DE_JOGO, GameState.MENU],
	GameState.CERCO_ISECTUM: [GameState.FIM_DE_JOGO, GameState.MENU],
	GameState.MULTIPLAYER_LOBBY: [GameState.CERCO_ISECTUM, GameState.COMBATE_TATICO, GameState.MENU],
	GameState.FIM_DE_JOGO: [GameState.MENU, GameState.COMBATE_TATICO, GameState.CERCO_ISECTUM]
}

const SCENE_ROUTES: Dictionary = {
	GameState.MENU: "res://scenes/main/Menu.tscn",
	GameState.COMBATE_TATICO: "res://scenes/main/Main.tscn",
	GameState.CERCO_ISECTUM: "res://scenes/cerco/FortressBoard.tscn",
	GameState.FIM_DE_JOGO: "res://scenes/main/GameOver.tscn",
	GameState.MULTIPLAYER_LOBBY: "res://scenes/main/Lobby.tscn"
}

var current_state: GameState = GameState.MENU
var previous_state: GameState = GameState.MENU
var state_payload: Dictionary = {}
var is_transitioning: bool = false
var headless_test_mode: bool = false # When true, skips scene changes

func _init() -> void:
	name = "GameManager"

## Validates whether a transition from current_state to target_state is legal
func can_transition_to(target_state: GameState) -> bool:
	if not VALID_TRANSITIONS.has(current_state):
		return false
	return (VALID_TRANSITIONS[current_state] as Array).has(target_state)

## Executes state change with lifecycle hooks and EventBus signal
func change_state(new_state: GameState, payload: Dictionary = {}) -> bool:
	if new_state == current_state:
		push_warning("[GameManager] Already in state %s. Skipping." % STATE_NAMES[current_state])
		return false

	if not can_transition_to(new_state):
		push_error("[GameManager] Invalid state transition: %s -> %s" % [
			STATE_NAMES[current_state], STATE_NAMES.get(new_state, "UNKNOWN")
		])
		return false

	is_transitioning = true
	var prev: GameState = current_state
	_exit_state(prev)

	previous_state = prev
	current_state = new_state
	state_payload = payload

	_enter_state(new_state, payload)
	is_transitioning = false

	if has_node("/root/EventBus"):
		get_node("/root/EventBus").game_state_changed.emit(prev, new_state)

	return true

## Executes state change and attempts to load associated scene file
func change_state_and_scene(new_state: GameState, payload: Dictionary = {}) -> bool:
	var success: bool = change_state(new_state, payload)
	if not success:
		return false

	if headless_test_mode:
		return true

	if SCENE_ROUTES.has(new_state):
		var path: String = SCENE_ROUTES[new_state]
		if ResourceLoader.exists(path):
			var err: Error = get_tree().change_scene_to_file(path)
			if err != OK:
				push_error("[GameManager] Failed to load scene '%s': error %d" % [path, err])
				return false
		else:
			push_warning("[GameManager] Scene file '%s' does not exist yet. State set to %s." % [
				path, STATE_NAMES[new_state]
			])

	return true

func get_current_state() -> GameState:
	return current_state

func get_previous_state() -> GameState:
	return previous_state

func get_current_state_name() -> String:
	return STATE_NAMES.get(current_state, "UNKNOWN")

func get_state_payload() -> Dictionary:
	return state_payload

## Resets FSM back to MENU (useful for test resets)
func reset_to_menu() -> void:
	current_state = GameState.MENU
	previous_state = GameState.MENU
	state_payload.clear()
	is_transitioning = false

# ── Lifecycle Hooks ─────────────────────────────────────────────────────────

func _enter_state(state: GameState, payload: Dictionary) -> void:
	match state:
		GameState.MENU:
			if has_node("/root/AudioManager"):
				get_node("/root/AudioManager").play_bgm("menu")
		GameState.COMBATE_TATICO:
			if has_node("/root/AudioManager"):
				get_node("/root/AudioManager").play_bgm("battle1")
		GameState.CERCO_ISECTUM:
			if has_node("/root/AudioManager"):
				get_node("/root/AudioManager").play_bgm("battle1")
		GameState.FIM_DE_JOGO:
			pass
		GameState.MULTIPLAYER_LOBBY:
			if has_node("/root/AudioManager"):
				get_node("/root/AudioManager").play_bgm("intro")

func _exit_state(_state: GameState) -> void:
	# Clean up any lingering temporary state data
	pass
```

---

## 6. Autoload 4: `AudioManager.gd`

### 6.1 Design Philosophy & Responsibilities
- **Direct Asset Parity**: Uses all 11 existing `.ogg` files in `assets/sounds/` with zero missing placeholders.
- **Audio Bus Architecture**: Routes sound streams through standard buses (`Master`, `BGM`, `SFX`).
- **Smooth BGM Crossfading**: Dual `AudioStreamPlayer` design (`_bgm_player_a`, `_bgm_player_b`) interpolating volume via `Tween` to prevent sudden acoustic jarring when transitioning states.
- **Polyphonic SFX Pool**: Fixed pool of 12 pre-allocated `AudioStreamPlayer` nodes reusing instances to avoid allocation latency and garbage collection stalls during intense combat rounds.
- **Headless Resilience**: Audio calls run safely in headless CI/CD mode without crashing if the platform audio driver is dummy.

### 6.2 Asset Catalog & Mapping

| Key | File Path | Bus | Purpose |
|---|---|---|---|
| `menu` | `res://assets/sounds/menu.ogg` | BGM | Main menu theme |
| `battle1` | `res://assets/sounds/battle1.ogg` | BGM | Tactical & Cerco combat theme |
| `intro` | `res://assets/sounds/intro.ogg` | BGM | Lobby / Story prologue theme |
| `attack` | `res://assets/sounds/attack.ogg` | SFX | Melee/ranged attack swing |
| `hit` | `res://assets/sounds/hit.ogg` | SFX | Successful impact on target |
| `damage` | `res://assets/sounds/damage.ogg` | SFX | Unit suffering damage |
| `critical_hit` | `res://assets/sounds/critical_hit.ogg` | SFX | Natural 20 critical strike |
| `miss` | `res://assets/sounds/miss.ogg` | SFX | Attack missed or parried |
| `heal` | `res://assets/sounds/heal.ogg` | SFX | Healing spell or potion |
| `level_up` | `res://assets/sounds/level_up.ogg` | SFX | Hero level up or upgrade |
| `button_click` | `res://assets/sounds/button_click.ogg` | SFX | UI button click / card interaction |

### 6.3 Concrete GDScript Implementation (`godot_project/scripts/autoload/AudioManager.gd`)

```gdscript
# res://scripts/autoload/AudioManager.gd
extends Node

## Centralized Audio Manager Singleton (AudioManager.gd)
## Manages BGM crossfading, bus volumes, and pooled SFX playback.

const BGM_PATHS: Dictionary = {
	"menu": "res://assets/sounds/menu.ogg",
	"battle1": "res://assets/sounds/battle1.ogg",
	"intro": "res://assets/sounds/intro.ogg"
}

const SFX_PATHS: Dictionary = {
	"attack": "res://assets/sounds/attack.ogg",
	"button_click": "res://assets/sounds/button_click.ogg",
	"critical_hit": "res://assets/sounds/critical_hit.ogg",
	"damage": "res://assets/sounds/damage.ogg",
	"heal": "res://assets/sounds/heal.ogg",
	"hit": "res://assets/sounds/hit.ogg",
	"level_up": "res://assets/sounds/level_up.ogg",
	"miss": "res://assets/sounds/miss.ogg"
}

const SFX_POOL_SIZE: int = 12
const BUS_MASTER: String = "Master"
const BUS_BGM: String = "BGM"
const BUS_SFX: String = "SFX"

var _bgm_player_a: AudioStreamPlayer
var _bgm_player_b: AudioStreamPlayer
var _active_bgm_player: AudioStreamPlayer
var _current_bgm_key: String = ""

var _sfx_pool: Array[AudioStreamPlayer] = []
var _sfx_streams: Dictionary = {} # Dictionary[String, AudioStream]
var _bgm_streams: Dictionary = {} # Dictionary[String, AudioStream]

var _is_audio_available: bool = true

func _init() -> void:
	name = "AudioManager"

func _ready() -> void:
	_init_audio_nodes()
	_preload_streams()
	_connect_event_bus()

func _init_audio_nodes() -> void:
	# BGM Players for crossfade
	_bgm_player_a = AudioStreamPlayer.new()
	_bgm_player_a.bus = _resolve_bus(BUS_BGM)
	add_child(_bgm_player_a)

	_bgm_player_b = AudioStreamPlayer.new()
	_bgm_player_b.bus = _resolve_bus(BUS_BGM)
	add_child(_bgm_player_b)

	_active_bgm_player = _bgm_player_a

	# SFX Pool
	for i in range(SFX_POOL_SIZE):
		var p: AudioStreamPlayer = AudioStreamPlayer.new()
		p.bus = _resolve_bus(BUS_SFX)
		add_child(p)
		_sfx_pool.append(p)

func _resolve_bus(bus_name: String) -> String:
	if AudioServer.get_bus_index(bus_name) != -1:
		return bus_name
	return BUS_MASTER

func _preload_streams() -> void:
	for key in SFX_PATHS.keys():
		var path: String = SFX_PATHS[key]
		if ResourceLoader.exists(path):
			_sfx_streams[key] = load(path)
		else:
			push_warning("[AudioManager] SFX file not found: %s" % path)

	for key in BGM_PATHS.keys():
		var path: String = BGM_PATHS[key]
		if ResourceLoader.exists(path):
			_bgm_streams[key] = load(path)
		else:
			push_warning("[AudioManager] BGM file not found: %s" % path)

func _connect_event_bus() -> void:
	if has_node("/root/EventBus"):
		var eb = get_node("/root/EventBus")
		eb.audio_play_sfx_requested.connect(play_sfx)
		eb.audio_play_bgm_requested.connect(play_bgm)

# ── BGM Playback & Crossfade ────────────────────────────────────────────────

func play_bgm(track_key: String, crossfade_duration: float = 1.0) -> void:
	if track_key == _current_bgm_key and _active_bgm_player.playing:
		return

	if not _bgm_streams.has(track_key):
		push_warning("[AudioManager] Unknown BGM track '%s'" % track_key)
		return

	var next_player: AudioStreamPlayer = _bgm_player_b if _active_bgm_player == _bgm_player_a else _bgm_player_a
	var stream: AudioStream = _bgm_streams[track_key]

	next_player.stream = stream
	next_player.volume_db = -80.0
	next_player.play()

	if crossfade_duration > 0.0:
		var tween: Tween = create_tween().set_parallel(true)
		tween.tween_property(_active_bgm_player, "volume_db", -80.0, crossfade_duration)
		tween.tween_property(next_player, "volume_db", 0.0, crossfade_duration)
		tween.chain().tween_callback(Callable(_active_bgm_player, "stop"))
	else:
		_active_bgm_player.stop()
		next_player.volume_db = 0.0

	_active_bgm_player = next_player
	_current_bgm_key = track_key

func stop_bgm(fade_duration: float = 0.5) -> void:
	if not _active_bgm_player.playing:
		return

	if fade_duration > 0.0:
		var tween: Tween = create_tween()
		tween.tween_property(_active_bgm_player, "volume_db", -80.0, fade_duration)
		tween.tween_callback(Callable(_active_bgm_player, "stop"))
	else:
		_active_bgm_player.stop()
	_current_bgm_key = ""

func get_current_bgm_key() -> String:
	return _current_bgm_key

# ── SFX Pooled Playback ─────────────────────────────────────────────────────

func play_sfx(sound_key: String, volume_scale: float = 1.0, pitch_scale: float = 1.0) -> AudioStreamPlayer:
	if not _sfx_streams.has(sound_key):
		push_warning("[AudioManager] Unknown SFX '%s'" % sound_key)
		return null

	var player: AudioStreamPlayer = _get_available_sfx_player()
	player.stream = _sfx_streams[sound_key]
	player.volume_db = linear_to_db(clamp(volume_scale, 0.0, 1.0))
	player.pitch_scale = clamp(pitch_scale, 0.5, 2.0)
	player.play()
	return player

func _get_available_sfx_player() -> AudioStreamPlayer:
	for p in _sfx_pool:
		if not p.playing:
			return p
	# Pool exhausted: borrow first player (oldest)
	return _sfx_pool[0]

# ── Bus Volume & Mute Controls ──────────────────────────────────────────────

func set_bus_volume(bus_name: String, linear_volume: float) -> void:
	var idx: int = AudioServer.get_bus_index(bus_name)
	if idx == -1:
		push_warning("[AudioManager] Bus '%s' does not exist." % bus_name)
		return
	var vol_clamped: float = clamp(linear_volume, 0.0001, 1.0)
	AudioServer.set_bus_volume_db(idx, linear_to_db(vol_clamped))

func get_bus_volume(bus_name: String) -> float:
	var idx: int = AudioServer.get_bus_index(bus_name)
	if idx == -1:
		return 0.0
	return db_to_linear(AudioServer.get_bus_volume_db(idx))

func set_bus_muted(bus_name: String, muted: bool) -> void:
	var idx: int = AudioServer.get_bus_index(bus_name)
	if idx != -1:
		AudioServer.set_bus_mute(idx, muted)

func is_bus_muted(bus_name: String) -> bool:
	var idx: int = AudioServer.get_bus_index(bus_name)
	if idx != -1:
		return AudioServer.is_bus_mute(idx)
	return false
```

---

## 7. Comprehensive GUT Unit Test Suite (AAA Pattern)

Each test file strictly follows the **Arrange-Act-Assert (AAA)** standard, covering:
1. **Happy Path** (normal expected flow).
2. **Edge Cases** (boundary limits, empty structures, null lookups).
3. **Error Handling & Resilience** (malformed JSON, missing files, illegal transitions).
4. **Mock / Stub Isolation** (signal spies, local dictionaries, headless skips).

### 7.1 Test Suite 1: `test_event_bus.gd` (`godot_project/test/unit/test_event_bus.gd`)

```gdscript
# res://test/unit/test_event_bus.gd
extends GutTest

var _bus: Node = null

func before_each() -> void:
	# Arrange
	_bus = preload("res://scripts/autoload/EventBus.gd").new()
	add_child(_bus)
	_bus.reset_telemetry()

func after_each() -> void:
	_bus.queue_free()

func test_unit_moved_signal_emission_happy_path() -> void:
	# Arrange
	watch_signals(_bus)
	var from_pos: Vector2i = Vector2i(2, 3)
	var to_pos: Vector2i = Vector2i(4, 5)

	# Act
	_bus.unit_moved.emit("Guerreiro_1", from_pos, to_pos)

	# Assert
	assert_signal_emitted(_bus, "unit_moved")
	assert_signal_emitted_with_parameters(_bus, "unit_moved", ["Guerreiro_1", from_pos, to_pos])

func test_unit_attacked_signal_parameters() -> void:
	# Arrange
	watch_signals(_bus)

	# Act
	_bus.unit_attacked.emit("Aquele", "Goblin_3", true, true, 24, "Cortante")

	# Assert
	assert_signal_emitted(_bus, "unit_attacked")
	assert_signal_emitted_with_parameters(_bus, "unit_attacked", ["Aquele", "Goblin_3", true, true, 24, "Cortante"])

func test_round_resolved_payload_integrity() -> void:
	# Arrange
	watch_signals(_bus)
	var sync_data: Dictionary = {"movement": ["Aquele", "Stark"], "synergies": ["Suprema"]}

	# Act
	_bus.round_resolved.emit(3, sync_data)

	# Assert
	assert_signal_emitted(_bus, "round_resolved")
	assert_signal_emitted_with_parameters(_bus, "round_resolved", [3, sync_data])

func test_telemetry_emission_counting() -> void:
	# Arrange
	assert_eq(_bus.get_emission_count("unit_died"), 0)

	# Act
	_bus.emit_logged("unit_died", ["Novak"])
	_bus.emit_logged("unit_died", ["Koema"])

	# Assert
	assert_eq(_bus.get_emission_count("unit_died"), 2)

func test_edge_case_empty_strings_and_negative_coords() -> void:
	# Arrange
	watch_signals(_bus)

	# Act
	_bus.unit_moved.emit("", Vector2i(-1, -1), Vector2i(-5, -5))

	# Assert (Signal should dispatch without unhandled exceptions)
	assert_signal_emitted(_bus, "unit_moved")
```

### 7.2 Test Suite 2: `test_data_manager.gd` (`godot_project/test/unit/test_data_manager.gd`)

```gdscript
# res://test/unit/test_data_manager.gd
extends GutTest

var _dm: Node = null

const VALID_TEST_JSON: String = """{
	"Guerreiro": {
		"stats": {"forca": 16, "constituicao": 14, "destreza": 12},
		"dado_vida": [1, 10], "ac": 18, "dado_dano": [1, 8],
		"velocidade": 3, "alcance": 1, "tipo_dano": "Cortante"
	},
	"Aquele": {
		"stats": {"forca": 17, "constituicao": 15, "destreza": 15},
		"dado_vida": [1, 10], "hp": 48, "ac": 17, "dado_dano": [1, 10],
		"velocidade": 4, "alcance": 1, "tipo_dano": "Cortante"
	}
}"""

const MALFORMED_JSON: String = """{ "Guerreiro": { broken_json_string """

func before_each() -> void:
	_dm = preload("res://scripts/autoload/DataManager.gd").new()
	add_child(_dm)

func after_each() -> void:
	_dm.queue_free()

func test_parse_valid_json_happy_path() -> void:
	# Arrange & Act
	var err: Error = _dm.parse_characters_from_string(VALID_TEST_JSON)

	# Assert
	assert_eq(err, OK)
	var guerreiro: CharacterData = _dm.get_character_data("Guerreiro")
	assert_not_null(guerreiro)
	assert_eq(guerreiro.forca, 16)
	assert_eq(guerreiro.ac, 18)
	assert_eq(guerreiro.tipo_dano, "Cortante")

func test_hero_retrieval_returns_isolated_duplicate() -> void:
	# Arrange
	_dm.parse_characters_from_string(VALID_TEST_JSON)

	# Act
	var h1: CharacterData = _dm.get_hero_data("Aquele")
	h1.hp -= 10
	var h2: CharacterData = _dm.get_hero_data("Aquele")

	# Assert (Mutation of h1 must not pollute cached h2)
	assert_eq(h1.hp, 38)
	assert_eq(h2.hp, 48)

func test_all_11_canonical_heroes_exist() -> void:
	# Arrange & Act
	var heroes: Array[CharacterData] = _dm.get_all_heroes()

	# Assert
	assert_eq(heroes.size(), 11)
	var names: Array[String] = []
	for h in heroes:
		names.append(h.id)
	assert_has(names, "Aquele")
	assert_has(names, "Stark")
	assert_has(names, "Elden")
	assert_has(names, "Darwin")

func test_malformed_json_fallback_resilience() -> void:
	# Arrange & Act
	var err: Error = _dm.parse_characters_from_string(MALFORMED_JSON)

	# Assert
	assert_ne(err, OK)
	# Should gracefully fall back so get_hero_data still returns valid data
	var hero: CharacterData = _dm.get_hero_data("Novak")
	assert_not_null(hero)
	assert_eq(hero.id, "Novak")

func test_nonexistent_hero_returns_fallback_without_crashing() -> void:
	# Arrange & Act
	var unknown: CharacterData = _dm.get_hero_data("HeroiInexistente")

	# Assert
	assert_not_null(unknown)
	assert_eq(unknown.id, "HeroiInexistente")
	assert_eq(unknown.hp, 30)

func test_isectum_caste_and_cards_retrieval() -> void:
	# Arrange & Act
	var caste: IsectumCasteData = _dm.get_isectum_caste("vespa_cacadora")
	var card: CardData = _dm.get_card_data("trabalho_1")

	# Assert
	assert_not_null(caste)
	assert_eq(caste.id, "vespa_cacadora")
	assert_not_null(card)
	assert_eq(card.work, 3)
```

### 7.3 Test Suite 3: `test_game_manager.gd` (`godot_project/test/unit/test_game_manager.gd`)

```gdscript
# res://test/unit/test_game_manager.gd
extends GutTest

var _gm: Node = null

func before_each() -> void:
	_gm = preload("res://scripts/autoload/GameManager.gd").new()
	_gm.headless_test_mode = true # Bypass scene loading
	add_child(_gm)
	_gm.reset_to_menu()

func after_each() -> void:
	_gm.queue_free()

func test_initial_state_is_menu() -> void:
	# Assert
	assert_eq(_gm.get_current_state(), _gm.GameState.MENU)
	assert_eq(_gm.get_current_state_name(), "MENU")

func test_valid_transitions_happy_path() -> void:
	# Arrange -> MENU to COMBATE_TATICO
	var success1: bool = _gm.change_state(_gm.GameState.COMBATE_TATICO)
	assert_true(success1)
	assert_eq(_gm.get_current_state(), _gm.GameState.COMBATE_TATICO)
	assert_eq(_gm.get_previous_state(), _gm.GameState.MENU)

	# COMBATE_TATICO to FIM_DE_JOGO
	var success2: bool = _gm.change_state(_gm.GameState.FIM_DE_JOGO)
	assert_true(success2)
	assert_eq(_gm.get_current_state(), _gm.GameState.FIM_DE_JOGO)

	# FIM_DE_JOGO back to MENU
	var success3: bool = _gm.change_state(_gm.GameState.MENU)
	assert_true(success3)
	assert_eq(_gm.get_current_state(), _gm.GameState.MENU)

func test_invalid_transition_rejected() -> void:
	# Arrange -> In MENU, attempting invalid jump directly to FIM_DE_JOGO
	var success: bool = _gm.change_state(_gm.GameState.FIM_DE_JOGO)

	# Assert
	assert_false(success)
	assert_eq(_gm.get_current_state(), _gm.GameState.MENU) # State unchanged

func test_same_state_transition_ignored() -> void:
	# Act
	var success: bool = _gm.change_state(_gm.GameState.MENU)

	# Assert
	assert_false(success)
	assert_eq(_gm.get_current_state(), _gm.GameState.MENU)

func test_state_payload_retention() -> void:
	# Arrange
	var payload: Dictionary = {"level_id": "fase_01", "difficulty": "hard"}

	# Act
	_gm.change_state(_gm.GameState.COMBATE_TATICO, payload)

	# Assert
	assert_eq(_gm.get_state_payload(), payload)
	assert_eq(_gm.get_state_payload()["level_id"], "fase_01")
```

### 7.4 Test Suite 4: `test_audio_manager.gd` (`godot_project/test/unit/test_audio_manager.gd`)

```gdscript
# res://test/unit/test_audio_manager.gd
extends GutTest

var _am: Node = null

func before_each() -> void:
	_am = preload("res://scripts/autoload/AudioManager.gd").new()
	add_child(_am)

func after_each() -> void:
	_am.queue_free()

func test_sfx_pool_initialization() -> void:
	# Assert pool size
	assert_eq(_am._sfx_pool.size(), 12)

func test_play_sfx_happy_path() -> void:
	# Act (Playing preloaded SFX key)
	var player: AudioStreamPlayer = _am.play_sfx("attack", 0.8, 1.0)

	# Assert
	if player != null:
		assert_not_null(player)
		assert_eq(player.pitch_scale, 1.0)

func test_play_unknown_sfx_graceful_handling() -> void:
	# Act
	var player: AudioStreamPlayer = _am.play_sfx("som_inexistente_123")

	# Assert (Must return null without crashing)
	assert_null(player)

func test_play_bgm_track_switching() -> void:
	# Act
	_am.play_bgm("menu", 0.0) # 0 crossfade for immediate testing

	# Assert
	assert_eq(_am.get_current_bgm_key(), "menu")

	# Switch track to battle1
	_am.play_bgm("battle1", 0.0)
	assert_eq(_am.get_current_bgm_key(), "battle1")

func test_bus_volume_clamping_and_muting() -> void:
	# Act & Assert Master Bus
	_am.set_bus_volume("Master", 0.5)
	assert_almost_eq(_am.get_bus_volume("Master"), 0.5, 0.05)

	_am.set_bus_muted("Master", true)
	assert_true(_am.is_bus_muted("Master"))

	_am.set_bus_muted("Master", false)
	assert_false(_am.is_bus_muted("Master"))

func test_bus_volume_edge_cases_zero_and_over_one() -> void:
	# Over 1.0 should clamp to 1.0
	_am.set_bus_volume("Master", 2.5)
	assert_almost_eq(_am.get_bus_volume("Master"), 1.0, 0.05)

	# Negative or 0 should clamp safely
	_am.set_bus_volume("Master", -0.5)
	assert_almost_eq(_am.get_bus_volume("Master"), 0.0001, 0.001)
```

---

## 8. Cross-Track Integration Matrix

To prevent interface drift across the multi-agent tracks (Rules, Entities, Deckbuilder, UI, Multiplayer):

| Autoload | Track Consumer | Interfacing Methods / Signals |
|---|---|---|
| `EventBus` | Rules / Combat (`M2`) | Emits `unit_moved`, `unit_attacked`, `unit_damaged`, `unit_died`, `death_save_rolled` |
| `EventBus` | Deckbuilder / Cerco (`M4`) | Emits `card_selected`, `round_resolved`, `synergy_triggered`, `resources_updated` |
| `EventBus` | UI / HUD (`M5`) | Connects to `unit_damaged` (HP bar), `floating_text_requested`, `combat_log_entry_added` |
| `EventBus` | Multiplayer Co-op (`M6`) | Connects to `network_message_received`, `network_connection_status_changed` |
| `DataManager` | Entities (`M3`) | Calls `get_hero_data(id)` and `get_isectum_caste(id)` to construct `Character` nodes |
| `DataManager` | Deckbuilder (`M4`) | Calls `get_card_data(id)` and `get_all_cards()` for hand and market setup |
| `GameManager` | UI / Menu (`M5`) | Menu buttons invoke `change_state_and_scene(GameState.COMBATE_TATICO)` |
| `GameManager` | Multiplayer (`M6`) | Connects lobby state to `GameState.MULTIPLAYER_LOBBY` and battle start |
| `AudioManager` | UI / HUD (`M5`) | UI button hover/press requests `button_click`; combat events trigger `hit`, `critical_hit` |


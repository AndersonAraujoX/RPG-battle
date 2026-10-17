# res://scripts/run/meta/MetaProgression.gd
class_name MetaProgression
extends RefCounted

## MetaProgression: Gerenciador permanente de progresso entre expedições (Marcos M7 & M8).
## Responsável por:
## 1. Salvar e carregar Âmbar Real em disco ("user://meta_save.json").
## 2. Quartel de Heróis: Desbloqueio dos 11 heróis via Âmbar Real.
## 3. Códice & Bestiário Isectum (registro de castas encontradas).
## 4. Sistema de Ascensão (Níveis 1 a 10 após a primeira vitória).
## 5. Estatísticas agregadas da conta do jogador.

signal amber_changed(new_balance: int, delta: int)
signal hero_unlocked(hero_id: String)
signal ascension_changed(new_level: int)
signal caste_recorded(caste_id: String)
signal saved()
signal loaded()

const DEFAULT_SAVE_PATH: String = "user://meta_save.json"
const MAX_ASCENSION: int = 10

const DEFAULT_UNLOCKED_HEROES: Array[String] = [
	"stark",
	"elden",
	"novak",
]

const SECRET_HEROES: Array[String] = [
	"aquele",
]

const HERO_UNLOCK_COSTS: Dictionary = {
	"stark": 0,
	"elden": 0,
	"novak": 0,
	"doom": 30,
	"gruu": 40,
	"kuro": 50,
	"darwin": 60,
	"rilem": 90,
	"yukito": 110,
	"koema": 150,
}

func is_hero_secret(hero_id: String) -> bool:
	return SECRET_HEROES.has(hero_id.to_lower().strip_edges())

func unlock_secret_hero(hero_id: String) -> bool:
	var hid: String = hero_id.to_lower().strip_edges()
	if not is_hero_secret(hid):
		return false
	if is_hero_unlocked(hid):
		return false
	unlocked_heroes.append(hid)
	hero_unlocked.emit(hid)
	save_to_disk()
	return true

# ── Propriedades Persistentes ──────────────────────────────────────────────────
var save_path: String = DEFAULT_SAVE_PATH
var amber_balance: int = 0
var lifetime_amber: int = 0
var unlocked_heroes: Array[String] = []
var codex_castes: Array[String] = []
var defeated_bosses: Array[String] = []
var current_ascension: int = 0
var max_unlocked_ascension: int = 0

# Estatísticas gerais
var total_runs: int = 0
var total_victories: int = 0
var total_defeats: int = 0
var total_floors_cleared: int = 0
var total_enemies_killed: int = 0

# Singleton estático opcional para acesso facilitado
static var _instance: MetaProgression = null

static func get_instance() -> MetaProgression:
	if _instance == null:
		_instance = MetaProgression.new()
		_instance.load_from_disk()
	return _instance

static func reset_instance() -> void:
	_instance = null

func _init(custom_path: String = "") -> void:
	if not custom_path.is_empty():
		save_path = custom_path
	reset_to_defaults()

func reset_to_defaults() -> void:
	amber_balance = 0
	lifetime_amber = 0
	unlocked_heroes = DEFAULT_UNLOCKED_HEROES.duplicate()
	codex_castes.clear()
	defeated_bosses.clear()
	current_ascension = 0
	max_unlocked_ascension = 0
	total_runs = 0
	total_victories = 0
	total_defeats = 0
	total_floors_cleared = 0
	total_enemies_killed = 0

# ── Economia de Âmbar Real ────────────────────────────────────────────────────

func deposit_amber(amount: int) -> bool:
	if amount <= 0:
		return false
	amber_balance += amount
	lifetime_amber += amount
	amber_changed.emit(amber_balance, amount)
	return true

func spend_amber(amount: int) -> bool:
	if amount <= 0 or amount > amber_balance:
		return false
	amber_balance -= amount
	amber_changed.emit(amber_balance, -amount)
	return true

# ── Quartel dos Heróis ────────────────────────────────────────────────────────

func is_hero_unlocked(hero_id: String) -> bool:
	return unlocked_heroes.has(hero_id.to_lower().strip_edges())

func get_hero_cost(hero_id: String) -> int:
	var hid: String = hero_id.to_lower().strip_edges()
	return int(HERO_UNLOCK_COSTS.get(hid, -1))

func can_unlock_hero(hero_id: String) -> bool:
	var hid: String = hero_id.to_lower().strip_edges()
	if not HERO_UNLOCK_COSTS.has(hid):
		return false
	if is_hero_unlocked(hid):
		return false
	var cost: int = HERO_UNLOCK_COSTS[hid]
	return amber_balance >= cost

func unlock_hero(hero_id: String) -> bool:
	var hid: String = hero_id.to_lower().strip_edges()
	if not can_unlock_hero(hid):
		return false
	var cost: int = HERO_UNLOCK_COSTS[hid]
	if spend_amber(cost):
		unlocked_heroes.append(hid)
		hero_unlocked.emit(hid)
		save_to_disk()
		return true
	return false

# ── Códice & Bestiário Isectum ─────────────────────────────────────────────────

func record_caste_encounter(caste_id: String) -> bool:
	var cid: String = caste_id.to_lower().strip_edges()
	if cid.is_empty() or codex_castes.has(cid):
		return false
	codex_castes.append(cid)
	caste_recorded.emit(cid)
	return true

func is_caste_in_codex(caste_id: String) -> bool:
	return codex_castes.has(caste_id.to_lower().strip_edges())

# ── Sistema de Ascensão (1 a 10) ──────────────────────────────────────────────

func is_ascension_unlocked() -> bool:
	return total_victories > 0 or max_unlocked_ascension > 0

func set_ascension_level(level: int) -> bool:
	if level < 0 or level > MAX_ASCENSION:
		return false
	if level > 0 and not is_ascension_unlocked():
		return false
	if level > max_unlocked_ascension:
		return false
	current_ascension = level
	ascension_changed.emit(current_ascension)
	return true

func get_ascension_modifiers(level: int = -1) -> Dictionary:
	var lvl: int = current_ascension if level < 0 else clampi(level, 0, MAX_ASCENSION)
	return {
		"level": lvl,
		"enemy_hp_multiplier": 1.0 + (0.10 if lvl >= 1 else 0.0),
		"elite_bonus_damage": 2 if lvl >= 2 else 0,
		"campfire_heal_pct": 0.20 if lvl >= 3 else 0.30,
		"forge_cost_multiplier": 1.20 if lvl >= 4 else 1.0,
		"starting_gold": 25 if lvl >= 5 else 50,
		"enemy_ac_bonus": 1 if lvl >= 6 else 0,
		"hazard_damage_multiplier": 2.0 if lvl >= 7 else 1.0,
		"campfire_count_penalty": 1 if lvl >= 8 else 0,
		"boss_hp_multiplier": 1.20 if lvl >= 9 else 1.0,
		"rei_frenzy_threshold": 200 if lvl >= 10 else 150,
	}

# ── Registro de Encerramento de Run ───────────────────────────────────────────

func record_run_finished(run_state: RunState, victory: bool) -> Dictionary:
	total_runs += 1
	var amber_earned: int = 0

	if run_state != null:
		amber_earned = run_state.calculate_amber()
		total_floors_cleared += run_state.floors_cleared
		total_enemies_killed += run_state.enemies_killed

		# Registra castas e chefes
		if run_state.map != null:
			for nid in run_state.map.nodes:
				var node: RunNode = run_state.map.nodes[nid]
				if node.visited and node.is_boss():
					var b_id: String = run_state.get_current_boss_id()
					if not b_id.is_empty() and not defeated_bosses.has(b_id):
						defeated_bosses.append(b_id)

	if victory:
		total_victories += 1
		# Se venceu no nível máximo de ascensão atual, desbloqueia o próximo
		if current_ascension == max_unlocked_ascension and max_unlocked_ascension < MAX_ASCENSION:
			max_unlocked_ascension += 1
		elif max_unlocked_ascension == 0:
			max_unlocked_ascension = 1
	else:
		total_defeats += 1

	if amber_earned > 0:
		deposit_amber(amber_earned)

	save_to_disk()

	return {
		"victory": victory,
		"amber_earned": amber_earned,
		"total_amber": amber_balance,
		"ascension": current_ascension,
		"max_ascension": max_unlocked_ascension,
	}

# ── Serialização & Persistência em Disco ───────────────────────────────────────

func to_dict() -> Dictionary:
	return {
		"version": 1,
		"amber_balance": amber_balance,
		"lifetime_amber": lifetime_amber,
		"unlocked_heroes": unlocked_heroes.duplicate(),
		"codex_castes": codex_castes.duplicate(),
		"defeated_bosses": defeated_bosses.duplicate(),
		"current_ascension": current_ascension,
		"max_unlocked_ascension": max_unlocked_ascension,
		"total_runs": total_runs,
		"total_victories": total_victories,
		"total_defeats": total_defeats,
		"total_floors_cleared": total_floors_cleared,
		"total_enemies_killed": total_enemies_killed,
	}

func from_dict(data: Dictionary) -> bool:
	if data.is_empty():
		return false

	amber_balance = maxi(int(data.get("amber_balance", 0)), 0)
	lifetime_amber = maxi(int(data.get("lifetime_amber", amber_balance)), amber_balance)

	unlocked_heroes.clear()
	for h in data.get("unlocked_heroes", DEFAULT_UNLOCKED_HEROES):
		var norm: String = String(h).to_lower().strip_edges()
		if not unlocked_heroes.has(norm):
			unlocked_heroes.append(norm)

	for base_h in DEFAULT_UNLOCKED_HEROES:
		if not unlocked_heroes.has(base_h):
			unlocked_heroes.append(base_h)

	codex_castes.clear()
	for c in data.get("codex_castes", []):
		var c_norm: String = String(c).to_lower().strip_edges()
		if not codex_castes.has(c_norm):
			codex_castes.append(c_norm)

	defeated_bosses.clear()
	for b in data.get("defeated_bosses", []):
		var b_norm: String = String(b).to_lower().strip_edges()
		if not defeated_bosses.has(b_norm):
			defeated_bosses.append(b_norm)

	current_ascension = clampi(int(data.get("current_ascension", 0)), 0, MAX_ASCENSION)
	max_unlocked_ascension = clampi(int(data.get("max_unlocked_ascension", 0)), 0, MAX_ASCENSION)
	total_runs = maxi(int(data.get("total_runs", 0)), 0)
	total_victories = maxi(int(data.get("total_victories", 0)), 0)
	total_defeats = maxi(int(data.get("total_defeats", 0)), 0)
	total_floors_cleared = maxi(int(data.get("total_floors_cleared", 0)), 0)
	total_enemies_killed = maxi(int(data.get("total_enemies_killed", 0)), 0)
	return true

func save_to_disk() -> bool:
	var file: FileAccess = FileAccess.open(save_path, FileAccess.WRITE)
	if file == null:
		push_error("[MetaProgression] Falha ao abrir arquivo para escrita: %s (Erro %d)" % [save_path, FileAccess.get_open_error()])
		return false

	var json_str: String = JSON.stringify(to_dict(), "\t")
	file.store_string(json_str)
	file.close()
	saved.emit()
	return true

func load_from_disk() -> bool:
	if not FileAccess.file_exists(save_path):
		return false

	var file: FileAccess = FileAccess.open(save_path, FileAccess.READ)
	if file == null:
		push_error("[MetaProgression] Falha ao abrir arquivo para leitura: %s" % save_path)
		return false

	var content: String = file.get_as_text()
	file.close()

	if content.strip_edges().is_empty():
		return false

	var parsed: Variant = JSON.parse_string(content)
	if not (parsed is Dictionary):
		push_warning("[MetaProgression] Conteúdo JSON corrompido em: %s" % save_path)
		return false

	var ok: bool = from_dict(parsed as Dictionary)
	if ok:
		loaded.emit()
	return ok

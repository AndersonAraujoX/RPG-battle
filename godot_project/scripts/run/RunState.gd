# res://scripts/run/RunState.gd
class_name RunState
extends RefCounted

## Estado completo de uma run roguelike: grupo, HP persistente, deck, relíquias,
## ouro, posição no mapa e progresso pelos 3 Atos até o Rei Isectum.
## Dependências (gerador de mapa e RNG) são injetadas para testes determinísticos.

signal node_entered(node: RunNode)
signal hero_died(hero_id: String)
signal act_advanced(new_act: int)
signal run_ended(victory: bool)
signal heart_destroyed(heart_id: String)

enum Status { NOT_STARTED, ACTIVE, VICTORY, DEFEAT }

const FINAL_ACT: int = 3
const MAX_PARTY_SIZE: int = 3
const STARTING_GOLD: int = 50
const ACT_TRANSITION_HEAL_PCT: float = 0.25
const AMBER_PER_FLOOR: int = 1
const AMBER_PER_BOSS: int = 10
const AMBER_VICTORY_BONUS: int = 25

const CANONICAL_HEART_IDS: Array[String] = [
	"coracao_da_mente",
	"coracao_da_carapaca",
	"coracao_da_ninhada",
]

const ACT_BOSSES: Dictionary = {
	1: "viuva_canibal",
	2: "rainha_do_enxame",
	3: "rei_isectum",
}

var status: int = Status.NOT_STARTED
var seed_value: int = 0
var act: int = 1
var heroes: Array[String] = []
var hero_hp: Dictionary = {}
var hero_max_hp: Dictionary = {}
var fallen_heroes: Array[String] = []
var deck: Array[String] = []
var relics: Array[String] = []
var gold: int = 0
var current_node_id: int = -1
var map: RunMap = null
var floors_cleared: int = 0
var bosses_defeated: int = 0
var enemies_killed: int = 0
var card_purges_count: int = 0
var destroyed_hearts: Array[String] = []

var _generator: RunMapGenerator
var _rng: RandomNumberGenerator

func _init(generator: RunMapGenerator = null, rng: RandomNumberGenerator = null) -> void:
	_generator = generator if generator != null else RunMapGenerator.new()
	_rng = rng if rng != null else RandomNumberGenerator.new()

# ── Ciclo de vida ───────────────────────────────────────────────────────────

## party: { hero_id: max_hp }. Retorna false para grupo vazio, grande demais ou HP inválido.
func start_run(party: Dictionary, starting_deck: Array[String], p_seed: int) -> bool:
	if party.is_empty() or party.size() > MAX_PARTY_SIZE:
		push_warning("[RunState] Tamanho de grupo inválido: %d" % party.size())
		return false
	for hid in party.keys():
		if String(hid).is_empty() or int(party[hid]) <= 0:
			push_warning("[RunState] Herói inválido: %s" % str(hid))
			return false

	_reset()
	seed_value = p_seed
	_rng.seed = p_seed
	for hid in party.keys():
		var h: String = String(hid)
		heroes.append(h)
		hero_max_hp[h] = int(party[hid])
		hero_hp[h] = int(party[hid])
	deck = starting_deck.duplicate()
	gold = STARTING_GOLD
	map = _generator.generate(act, _rng)
	if map == null:
		return false
	status = Status.ACTIVE
	return true

func is_active() -> bool:
	return status == Status.ACTIVE

func get_current_boss_id() -> String:
	return ACT_BOSSES.get(act, "")

# ── Navegação no mapa ──────────────────────────────────────────────────────

func get_current_node() -> RunNode:
	return map.get_node_by_id(current_node_id) if map != null else null

func get_available_nodes() -> Array[RunNode]:
	var empty: Array[RunNode] = []
	if not is_active() or map == null:
		return empty
	if current_node_id < 0:
		return map.get_start_nodes()
	var cur: RunNode = get_current_node()
	if cur == null or not cur.visited:
		return empty
	return map.get_next_nodes(current_node_id)

func can_move_to(node_id: int) -> bool:
	for n in get_available_nodes():
		if n.id == node_id:
			return true
	return false

## Entra no nó. O nó só conta como "concluído" após complete_current_node().
func move_to(node_id: int) -> bool:
	if not can_move_to(node_id):
		return false
	current_node_id = node_id
	var node: RunNode = get_current_node()
	node_entered.emit(node)
	return true

## Marca o nó atual como vencido; se for o chefe, avança Ato ou encerra a run.
func complete_current_node() -> bool:
	if not is_active():
		return false
	var node: RunNode = get_current_node()
	if node == null or node.visited:
		return false
	node.visited = true
	floors_cleared += 1
	if act == 3 and node.type == RunNode.NodeType.ELITE:
		for hid in CANONICAL_HEART_IDS:
			if not destroyed_hearts.has(hid):
				destroy_heart(hid)
				break
	if node.is_boss():
		_on_boss_defeated()
	return true

## Destrói permanentemente um dos Corações da Colmeia (Ato 3).
func destroy_heart(heart_id: String) -> bool:
	if heart_id.is_empty() or destroyed_hearts.has(heart_id):
		return false
	destroyed_hearts.append(heart_id)
	heart_destroyed.emit(heart_id)
	return true

func has_destroyed_heart(heart_id: String) -> bool:
	return destroyed_hearts.has(heart_id)

func get_destroyed_hearts() -> Array[String]:
	return destroyed_hearts.duplicate()

func _on_boss_defeated() -> void:
	bosses_defeated += 1
	if act >= FINAL_ACT:
		status = Status.VICTORY
		run_ended.emit(true)
		return
	act += 1
	heal_party_percent(ACT_TRANSITION_HEAL_PCT)
	map = _generator.generate(act, _rng)
	current_node_id = -1
	act_advanced.emit(act)

# ── Heróis ──────────────────────────────────────────────────────────────────

func get_living_heroes() -> Array[String]:
	var alive: Array[String] = []
	for h in heroes:
		if not fallen_heroes.has(h):
			alive.append(h)
	return alive

func is_hero_alive(hero_id: String) -> bool:
	return heroes.has(hero_id) and not fallen_heroes.has(hero_id)

## Retorna o HP restante, ou -1 se o herói não existir.
func damage_hero(hero_id: String, amount: int) -> int:
	if not heroes.has(hero_id):
		return -1
	if amount < 0:
		push_warning("[RunState] Dano negativo ignorado")
		return int(hero_hp[hero_id])
	if not is_hero_alive(hero_id):
		return 0
	hero_hp[hero_id] = maxi(int(hero_hp[hero_id]) - amount, 0)
	if hero_hp[hero_id] == 0:
		fallen_heroes.append(hero_id)
		hero_died.emit(hero_id)
		if get_living_heroes().is_empty() and is_active():
			status = Status.DEFEAT
			run_ended.emit(false)
	return int(hero_hp[hero_id])

## Heróis caídos não podem ser curados (morte permanente na run).
func heal_hero(hero_id: String, amount: int) -> int:
	if not heroes.has(hero_id):
		return -1
	if amount < 0 or not is_hero_alive(hero_id):
		return int(hero_hp[hero_id])
	hero_hp[hero_id] = mini(int(hero_hp[hero_id]) + amount, int(hero_max_hp[hero_id]))
	return int(hero_hp[hero_id])

func heal_party_percent(pct: float) -> void:
	var p: float = clampf(pct, 0.0, 1.0)
	for h in get_living_heroes():
		heal_hero(h, int(ceil(float(hero_max_hp[h]) * p)))

# ── Economia, deck e relíquias ──────────────────────────────────────────────

func add_gold(amount: int) -> bool:
	if amount < 0:
		return false
	gold += amount
	return true

func spend_gold(amount: int) -> bool:
	if amount < 0 or amount > gold:
		return false
	gold -= amount
	return true

func add_card(card_id: String) -> bool:
	if card_id.is_empty():
		return false
	deck.append(card_id)
	return true

func remove_card(card_id: String) -> bool:
	var idx: int = deck.find(card_id)
	if idx < 0:
		return false
	deck.remove_at(idx)
	return true

func add_relic(relic_id: String) -> bool:
	if relic_id.is_empty() or has_relic(relic_id):
		return false
	var norm: String = RelicManager.normalize_id(relic_id)
	relics.append(norm)
	return true

func has_relic(relic_id: String) -> bool:
	if relics.has(relic_id):
		return true
	var norm: String = RelicManager.normalize_id(relic_id)
	for r in relics:
		if RelicManager.normalize_id(r) == norm:
			return true
	return false

func remove_relic(relic_id: String) -> bool:
	var idx: int = relics.find(relic_id)
	if idx >= 0:
		relics.remove_at(idx)
		return true
	var norm: String = RelicManager.normalize_id(relic_id)
	for i in range(relics.size()):
		if RelicManager.normalize_id(relics[i]) == norm:
			relics.remove_at(i)
			return true
	return false

func register_kills(count: int) -> void:
	enemies_killed += maxi(count, 0)

## Moeda de meta-progressão ganha ao fim da run.
func calculate_amber() -> int:
	var amber: int = floors_cleared * AMBER_PER_FLOOR + bosses_defeated * AMBER_PER_BOSS
	if status == Status.VICTORY:
		amber += AMBER_VICTORY_BONUS
		# Bônus supremo: enfrentar o Rei com força total poupando todos os 3 Corações dobra o Âmbar Real!
		if destroyed_hearts.is_empty():
			amber *= 2
	return amber

# ── Persistência ────────────────────────────────────────────────────────────

func to_dict() -> Dictionary:
	return {
		"status": status,
		"seed": seed_value,
		"act": act,
		"heroes": heroes.duplicate(),
		"hero_hp": hero_hp.duplicate(),
		"hero_max_hp": hero_max_hp.duplicate(),
		"fallen": fallen_heroes.duplicate(),
		"deck": deck.duplicate(),
		"relics": relics.duplicate(),
		"gold": gold,
		"current_node_id": current_node_id,
		"map": map.to_dict() if map != null else {},
		"floors_cleared": floors_cleared,
		"bosses_defeated": bosses_defeated,
		"enemies_killed": enemies_killed,
		"card_purges_count": card_purges_count,
		"destroyed_hearts": destroyed_hearts.duplicate(),
	}

## Restaura de um dicionário; retorna false (sem alterar o estado) se os dados forem inválidos.
func from_dict(data: Dictionary) -> bool:
	for key in ["status", "act", "heroes", "hero_hp", "hero_max_hp", "map"]:
		if not data.has(key):
			return false
	var restored_map: RunMap = RunMap.from_dict(data["map"]) if data["map"] is Dictionary else null
	if restored_map == null:
		return false
	_reset()
	status = int(data["status"])
	seed_value = int(data.get("seed", 0))
	act = int(data["act"])
	for h in data["heroes"]:
		heroes.append(String(h))
	for h in data.get("fallen", []):
		fallen_heroes.append(String(h))
	for c in data.get("deck", []):
		deck.append(String(c))
	for r in data.get("relics", []):
		relics.append(String(r))
	for h in data.get("destroyed_hearts", []):
		destroyed_hearts.append(String(h))
	hero_hp = (data["hero_hp"] as Dictionary).duplicate()
	hero_max_hp = (data["hero_max_hp"] as Dictionary).duplicate()
	gold = int(data.get("gold", 0))
	current_node_id = int(data.get("current_node_id", -1))
	floors_cleared = int(data.get("floors_cleared", 0))
	bosses_defeated = int(data.get("bosses_defeated", 0))
	enemies_killed = int(data.get("enemies_killed", 0))
	card_purges_count = int(data.get("card_purges_count", 0))
	map = restored_map
	return true

func _reset() -> void:
	status = Status.NOT_STARTED
	act = 1
	heroes.clear()
	hero_hp.clear()
	hero_max_hp.clear()
	fallen_heroes.clear()
	deck.clear()
	relics.clear()
	destroyed_hearts.clear()
	gold = 0
	current_node_id = -1
	map = null
	floors_cleared = 0
	bosses_defeated = 0
	enemies_killed = 0
	card_purges_count = 0

# res://scripts/run/relics/RelicManager.gd
class_name RelicManager
extends RefCounted

## RelicManager: Central controller connecting RunState.relics to EventBus signals.
## Manages relic registration, lifecycle hooks, and modifier pipelines.
## Ensures zero memory leaks by cleanly disconnecting signals and clearing references.

var run_state: RunState = null
var event_bus: Node = null

## Active instantiated relics: { relic_id: RelicData }
var _active_relics: Dictionary = {}

## Catalog factory registry: { relic_id: Callable -> RelicData }
var _catalog: Dictionary = {}

var _connected: bool = false

func _init(p_run_state: RunState = null, p_event_bus: Node = null) -> void:
	_register_canonical_catalog()
	if p_run_state != null:
		setup(p_run_state, p_event_bus)

## Initializes with dependencies and synchronizes existing RunState.relics
func setup(p_run_state: RunState, p_event_bus: Node = null) -> void:
	run_state = p_run_state
	event_bus = p_event_bus
	if event_bus == null and Engine.has_singleton("EventBus"):
		event_bus = Engine.get_singleton("EventBus")
	
	connect_event_bus()
	sync_from_run_state()

# ── Signal Connection & Lifecycle ───────────────────────────────────────────

func connect_event_bus() -> void:
	if _connected or event_bus == null:
		return
	
	if event_bus.has_signal("unit_attacked") and not event_bus.unit_attacked.is_connected(_on_unit_attacked):
		event_bus.unit_attacked.connect(_on_unit_attacked)
	if event_bus.has_signal("unit_damaged") and not event_bus.unit_damaged.is_connected(_on_unit_damaged):
		event_bus.unit_damaged.connect(_on_unit_damaged)
	if event_bus.has_signal("unit_died") and not event_bus.unit_died.is_connected(_on_unit_died):
		event_bus.unit_died.connect(_on_unit_died)
	if event_bus.has_signal("turn_changed") and not event_bus.turn_changed.is_connected(_on_turn_changed):
		event_bus.turn_changed.connect(_on_turn_changed)
	if event_bus.has_signal("card_played") and not event_bus.card_played.is_connected(_on_card_played):
		event_bus.card_played.connect(_on_card_played)
	if event_bus.has_signal("status_applied") and not event_bus.status_applied.is_connected(_on_status_applied):
		event_bus.status_applied.connect(_on_status_applied)
	if event_bus.has_signal("death_save_rolled") and not event_bus.death_save_rolled.is_connected(_on_death_save_rolled):
		event_bus.death_save_rolled.connect(_on_death_save_rolled)
	
	if run_state != null and run_state.has_signal("node_entered"):
		if not run_state.node_entered.is_connected(_on_node_entered):
			run_state.node_entered.connect(_on_node_entered)
	
	_connected = true

func disconnect_event_bus() -> void:
	if not _connected or event_bus == null:
		return
	
	if event_bus.has_signal("unit_attacked") and event_bus.unit_attacked.is_connected(_on_unit_attacked):
		event_bus.unit_attacked.disconnect(_on_unit_attacked)
	if event_bus.has_signal("unit_damaged") and event_bus.unit_damaged.is_connected(_on_unit_damaged):
		event_bus.unit_damaged.disconnect(_on_unit_damaged)
	if event_bus.has_signal("unit_died") and event_bus.unit_died.is_connected(_on_unit_died):
		event_bus.unit_died.disconnect(_on_unit_died)
	if event_bus.has_signal("turn_changed") and event_bus.turn_changed.is_connected(_on_turn_changed):
		event_bus.turn_changed.disconnect(_on_turn_changed)
	if event_bus.has_signal("card_played") and event_bus.card_played.is_connected(_on_card_played):
		event_bus.card_played.disconnect(_on_card_played)
	if event_bus.has_signal("status_applied") and event_bus.status_applied.is_connected(_on_status_applied):
		event_bus.status_applied.disconnect(_on_status_applied)
	if event_bus.has_signal("death_save_rolled") and event_bus.death_save_rolled.is_connected(_on_death_save_rolled):
		event_bus.death_save_rolled.disconnect(_on_death_save_rolled)
	
	if run_state != null and run_state.has_signal("node_entered"):
		if run_state.node_entered.is_connected(_on_node_entered):
			run_state.node_entered.disconnect(_on_node_entered)
	
	_connected = false

# ── Relic Management ────────────────────────────────────────────────────────

## Synchronizes active relics with IDs present in RunState.relics
func sync_from_run_state() -> void:
	if run_state == null:
		return
	for r_id in run_state.relics:
		if not _active_relics.has(r_id):
			var relic: RelicData = create_relic(r_id)
			if relic != null:
				_active_relics[r_id] = relic
				relic.on_registered(run_state)

## Registers a new relic by ID. Adds to RunState if not present.
func register_relic(relic_id: String) -> bool:
	if relic_id.is_empty() or _active_relics.has(relic_id):
		return false
	
	var relic: RelicData = create_relic(relic_id)
	if relic == null:
		push_warning("[RelicManager] Relíquia desconhecida: '%s'" % relic_id)
		return false
	
	_active_relics[relic_id] = relic
	if run_state != null:
		if not run_state.has_relic(relic_id):
			run_state.add_relic(relic_id)
		relic.on_registered(run_state)
	
	return true

## Unregisters and removes a relic
func unregister_relic(relic_id: String) -> bool:
	if not _active_relics.has(relic_id):
		return false
	var relic: RelicData = _active_relics[relic_id]
	if run_state != null:
		relic.on_unregistered(run_state)
		var idx: int = run_state.relics.find(relic_id)
		if idx >= 0:
			run_state.relics.remove_at(idx)
	_active_relics.erase(relic_id)
	return true

## Cleans up all relics and disconnects signals (prevents memory leaks)
func unregister_all() -> void:
	for r_id in _active_relics.keys():
		var relic: RelicData = _active_relics[r_id]
		if run_state != null:
			relic.on_unregistered(run_state)
	_active_relics.clear()
	disconnect_event_bus()

func get_relic(relic_id: String) -> RelicData:
	return _active_relics.get(relic_id, null)

func has_relic(relic_id: String) -> bool:
	return _active_relics.has(relic_id)

func get_all_relics() -> Array[RelicData]:
	var list: Array[RelicData] = []
	for r in _active_relics.values():
		list.append(r)
	return list

func get_relic_count() -> int:
	return _active_relics.size()

# ── Modifier Pipelines (Queried by Combat & Systems) ─────────────────────────

## Calculates cumulative attack modifiers across all active relics.
func modify_attack_damage(
	attacker_id: String,
	target_id: String,
	is_hero: bool,
	damage: int,
	damage_type: String,
	is_crit: bool
) -> Dictionary:
	var result: Dictionary = {
		"bonus_damage": 0,
		"bonus_type": "",
		"heal_attacker": 0,
		"override_crit": false,
		"final_damage": damage
	}
	for relic in _active_relics.values():
		if not relic.is_active:
			continue
		var mod: Dictionary = relic.on_attack_dealt(
			attacker_id, target_id, is_hero, result["final_damage"], damage_type, is_crit, run_state
		)
		if mod.has("bonus_damage"):
			result["bonus_damage"] += int(mod["bonus_damage"])
			result["final_damage"] += int(mod["bonus_damage"])
		if mod.has("bonus_type") and not String(mod["bonus_type"]).is_empty():
			result["bonus_type"] = String(mod["bonus_type"])
		if mod.has("heal_attacker"):
			result["heal_attacker"] += int(mod["heal_attacker"])
		if mod.get("override_crit", false):
			result["override_crit"] = true
	return result

## Calculates cumulative damage received modifiers across all active relics.
func modify_incoming_damage(
	target_id: String,
	is_hero: bool,
	incoming_damage: int,
	current_hp: int,
	max_hp: int
) -> Dictionary:
	var result: Dictionary = {
		"damage_reduction": 0,
		"cancel_damage": false,
		"riposte_damage": 0,
		"final_damage": incoming_damage
	}
	for relic in _active_relics.values():
		if not relic.is_active:
			continue
		var mod: Dictionary = relic.on_damage_received(
			target_id, is_hero, result["final_damage"], current_hp, max_hp, run_state
		)
		if mod.get("cancel_damage", false):
			result["cancel_damage"] = true
			result["final_damage"] = 0
			break
		if mod.has("damage_reduction"):
			var red: int = int(mod["damage_reduction"])
			result["damage_reduction"] += red
			result["final_damage"] = maxi(1, result["final_damage"] - red)
		if mod.has("riposte_damage"):
			result["riposte_damage"] += int(mod["riposte_damage"])
	return result

## Calculates campfire heal rate (e.g. 0.30 -> 0.45)
func modify_campfire_heal(base_heal_pct: float) -> float:
	var current_pct: float = base_heal_pct
	for relic in _active_relics.values():
		if relic.is_active:
			current_pct = relic.on_campfire_rest(current_pct, run_state)
	return current_pct

## Calculates post-combat victory rewards with relic bonuses
func modify_combat_victory_rewards(rewards: Dictionary) -> Dictionary:
	var mod_rewards: Dictionary = rewards.duplicate(true)
	for relic in _active_relics.values():
		if relic.is_active:
			mod_rewards = relic.on_combat_victory(mod_rewards, run_state)
	return mod_rewards

## Calculates Forge shop discounts
func modify_forge_cost(item_type: String, base_cost: int) -> int:
	var final_cost: int = base_cost
	for relic in _active_relics.values():
		if relic.is_active:
			final_cost = relic.on_forge_discount(item_type, final_cost, run_state)
	return maxi(0, final_cost)

## Resets combat state across all active relics at the start/end of battle
func reset_all_combat_states() -> void:
	for relic in _active_relics.values():
		relic.reset_combat_state()

# ── EventBus Listeners ───────────────────────────────────────────────────────

func _on_unit_attacked(attacker_id: String, target_id: String, hit: bool, is_crit: bool, damage: int, damage_type: String) -> void:
	if not hit:
		return
	var is_hero: bool = run_state != null and run_state.heroes.has(attacker_id)
	for relic in _active_relics.values():
		if relic.is_active:
			relic.on_attack_dealt(attacker_id, target_id, is_hero, damage, damage_type, is_crit, run_state)

func _on_unit_damaged(unit_id: String, amount: int, current_hp: int, max_hp: int) -> void:
	var is_hero: bool = run_state != null and run_state.heroes.has(unit_id)
	for relic in _active_relics.values():
		if relic.is_active:
			relic.on_damage_received(unit_id, is_hero, amount, current_hp, max_hp, run_state)

func _on_unit_died(unit_id: String) -> void:
	var is_enemy: bool = run_state != null and not run_state.heroes.has(unit_id)
	for relic in _active_relics.values():
		if relic.is_active:
			relic.on_unit_killed(unit_id, is_enemy, "", run_state)

func _on_turn_changed(turn_number: int, active_unit_id: String) -> void:
	for relic in _active_relics.values():
		if relic.is_active:
			relic.on_turn_started(turn_number, active_unit_id, run_state)

func _on_card_played(player_id: String, card_id: String, target_zone: String) -> void:
	for relic in _active_relics.values():
		if relic.is_active:
			relic.on_card_played(player_id, card_id, target_zone, run_state)

func _on_status_applied(unit_id: String, status_id: String, duration: int) -> void:
	for relic in _active_relics.values():
		if relic.is_active:
			relic.on_status_applied(unit_id, status_id, duration, run_state)

func _on_death_save_rolled(unit_id: String, roll: int, successes: int, failures: int, status: String) -> void:
	for relic in _active_relics.values():
		if relic.is_active:
			relic.on_death_save_rolled(unit_id, roll, successes, failures, status, run_state)

func _on_node_entered(node: RunNode) -> void:
	if node != null and node.is_combat_type():
		reset_all_combat_states()
	for relic in _active_relics.values():
		if relic.is_active:
			relic.on_node_entered(node, run_state)

# ── Catalog Factory ──────────────────────────────────────────────────────────

func register_catalog_entry(relic_id: String, factory_callable: Callable) -> void:
	_catalog[relic_id] = factory_callable

func create_relic(relic_id: String) -> RelicData:
	if _catalog.has(relic_id):
		return _catalog[relic_id].call()
	var stripped: String = relic_id.replace("reliquia_", "")
	if _catalog.has(stripped):
		return _catalog[stripped].call()
	return null

func get_catalog_ids() -> Array[String]:
	var keys: Array[String] = []
	for k in _catalog.keys():
		keys.append(String(k))
	return keys

func _register_canonical_catalog() -> void:
	register_catalog_entry("martelo_runico", func(): return RelicMarteloRunico.new())
	register_catalog_entry("escudo_ancestral", func(): return RelicEscudoAncestral.new())
	register_catalog_entry("bolsa_do_mercador", func(): return RelicBolsaDoMercador.new())
	register_catalog_entry("amuleto_ambar", func(): return RelicAmuletoAmbar.new())
	register_catalog_entry("dente_da_viuva", func(): return RelicDenteDaViuva.new())
	register_catalog_entry("tocha_eterna", func(): return RelicTochaEterna.new())
	register_catalog_entry("oleo_alquimico", func(): return RelicOleoAlquimico.new())
	register_catalog_entry("frasco_feromonio", func(): return RelicFrascoFeromonio.new())
	register_catalog_entry("coroa_quitina", func(): return RelicCoroaQuitina.new())
	register_catalog_entry("relogio_da_forja", func(): return RelicRelogioDaForja.new())

# ── Canonical 10 Relic Concrete Implementations ──────────────────────────────

class RelicMarteloRunico extends RelicData:
	func _init() -> void:
		super("martelo_runico", "Martelo Rúnico de Karak-Dur", "O primeiro ataque Melee dos heróis em cada combate causa +3 de dano contundente.", RARITY_COMUM, 50)
		counter_max = 1

	func on_attack_dealt(_attacker_id: String, _target_id: String, is_hero: bool, _damage: int, damage_type: String, _is_crit: bool, _run_state: RunState) -> Dictionary:
		if is_hero and counter == 0:
			if damage_type in ["cortante", "contundente", "perfurante", "fisico"]:
				counter = 1
				return {"bonus_damage": 3, "bonus_type": "contundente"}
		return {}

class RelicEscudoAncestral extends RelicData:
	func _init() -> void:
		super("escudo_ancestral", "Broquel dos Reis Anões", "Reduz todo o dano recebido pelos heróis em 1 ponto (mínimo de 1 de dano).", RARITY_INCOMUM, 70)

	func on_damage_received(_target_id: String, is_hero: bool, incoming_damage: int, _current_hp: int, _max_hp: int, _run_state: RunState) -> Dictionary:
		if is_hero and incoming_damage > 1:
			return {"damage_reduction": 1}
		return {}

class RelicBolsaDoMercador extends RelicData:
	func _init() -> void:
		super("bolsa_do_mercador", "Bolsa de Moedas da Guilda", "Vitórias em combate concedem +10 de ouro adicional.", RARITY_COMUM, 45)

	func on_combat_victory(rewards: Dictionary, p_run_state: RunState) -> Dictionary:
		rewards["gold"] = int(rewards.get("gold", 0)) + 10
		if p_run_state != null:
			p_run_state.add_gold(10)
		return rewards

class RelicAmuletoAmbar extends RelicData:
	func _init() -> void:
		super("amuleto_ambar", "Amuleto de Âmbar Resinoso", "Na Fogueira, o grupo recupera 45% do HP máximo em vez de 30%.", RARITY_INCOMUM, 65)

	func on_campfire_rest(base_heal_pct: float, _run_state: RunState) -> float:
		return base_heal_pct * 1.5

class RelicDenteDaViuva extends RelicData:
	func _init() -> void:
		super("dente_da_viuva", "Dente da Viúva Canibal", "Acertos críticos causam +4 de dano de veneno e curam o herói em 2 PV.", RARITY_RARO, 90)

	func on_attack_dealt(attacker_id: String, _target_id: String, is_hero: bool, _damage: int, _damage_type: String, is_crit: bool, p_run_state: RunState) -> Dictionary:
		if is_hero and is_crit:
			if p_run_state != null and p_run_state.is_hero_alive(attacker_id):
				p_run_state.heal_hero(attacker_id, 2)
			return {"bonus_damage": 4, "bonus_type": "veneno", "heal_attacker": 2}
		return {}

class RelicTochaEterna extends RelicData:
	func _init() -> void:
		super("tocha_eterna", "Tocha Eterna de Sulfeto", "Ataques contra alvos em chamas ou vulneráveis a fogo sofrem +2 de dano de fogo.", RARITY_RARO, 85)

	func on_attack_dealt(_attacker_id: String, _target_id: String, is_hero: bool, _damage: int, damage_type: String, _is_crit: bool, _run_state: RunState) -> Dictionary:
		if is_hero and (damage_type == "fogo" or damage_type == "burning"):
			return {"bonus_damage": 2, "bonus_type": "fogo"}
		return {}

class RelicOleoAlquimico extends RelicData:
	func _init() -> void:
		super("oleo_alquimico", "Frasco de Óleo de Incineração", "Golpes dos heróis causam +1 de dano de fogo, ativando fraquezas elementais.", RARITY_COMUM, 55)

	func on_attack_dealt(_attacker_id: String, _target_id: String, is_hero: bool, _damage: int, _damage_type: String, _is_crit: bool, _run_state: RunState) -> Dictionary:
		if is_hero:
			return {"bonus_damage": 1, "bonus_type": "fogo"}
		return {}

class RelicFrascoFeromonio extends RelicData:
	func _init() -> void:
		super("frasco_feromonio", "Frasco de Feromônio Neutralizador", "Anula a primeira condição negativa recebida pelos heróis em cada combate.", RARITY_RARO, 80)
		counter_max = 1

	func on_status_applied(_unit_id: String, status_id: String, _duration: int, _run_state: RunState) -> Dictionary:
		if counter == 0 and status_id in ["poisoned", "stunned", "frightened", "burning", "restrained"]:
			counter = 1
			return {"cancel_status": true}
		return {}

class RelicCoroaQuitina extends RelicData:
	func _init() -> void:
		super("coroa_quitina", "Carapaça de Quitina Cristalizada", "Concede Vantagem no primeiro Death Save por combate e mitiga falha crítica.", RARITY_LENDARIO, 120)
		counter_max = 1

	func on_death_save_rolled(_unit_id: String, roll: int, _successes: int, _failures: int, _status: String, _run_state: RunState) -> Dictionary:
		var result: Dictionary = {}
		if counter == 0:
			counter = 1
			result["force_advantage"] = true
		if roll == 1:
			result["mitigate_crit_fail"] = true
		return result

class RelicRelogioDaForja extends RelicData:
	func _init() -> void:
		super("relogio_da_forja", "Engrenagem Mestra da Forja", "Concede 20% de desconto na Forja Anã e +5 de ouro ao entrar na Forja.", RARITY_RARO, 95)

	func on_forge_discount(_item_type: String, base_cost: int, _run_state: RunState) -> int:
		return int(round(float(base_cost) * 0.80))

	func on_node_entered(node: RunNode, p_run_state: RunState) -> void:
		if node != null and node.type == RunNode.NodeType.FORGE:
			if p_run_state != null:
				p_run_state.add_gold(5)

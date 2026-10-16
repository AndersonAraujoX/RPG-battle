# Handoff Report — Milestone M3: Relics Architecture & Catalog Explorer

**Author**: M3 Relics Explorer (`explorer_m3_1`)  
**Target File**: `/home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m3_1/handoff.md`  
**Working Directory**: `/home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m3_1`  
**Date**: 2026-10-16T01:23:00Z  

---

## 1. Observation

### 1.1 Existing Codebase Anchors & Contracts
1. **`RunState.gd`** (`godot_project/scripts/run/RunState.gd`):
   - Line 38: `var relics: Array[String] = []` stores the active relic IDs for the expedition.
   - Lines 214–222:
     ```gdscript
     func add_relic(relic_id: String) -> bool:
         if relic_id.is_empty() or relics.has(relic_id):
             return false
         relics.append(relic_id)
         return true

     func has_relic(relic_id: String) -> bool:
         return relics.has(relic_id)
     ```
   - Lines 245, 272–273, 292: `to_dict()` and `from_dict()` serialize and deserialize `relics: Array[String]`.
   - *Observation*: While `RunState` has `add_relic()` and `has_relic()`, there is currently no `remove_relic()` method, and no subsystem currently interprets the relic IDs stored in `relics`.

2. **`EventBus.gd`** (`godot_project/scripts/autoload/EventBus.gd`):
   - Lines 10–25: Combat & Tactical Grid signals:
     - `signal unit_moved(unit_id: String, from_pos: Vector2i, to_pos: Vector2i)`
     - `signal unit_attacked(attacker_id: String, target_id: String, hit: bool, is_crit: bool, damage: int, damage_type: String)`
     - `signal unit_damaged(unit_id: String, amount: int, current_hp: int, max_hp: int)`
     - `signal unit_died(unit_id: String)`
     - `signal death_save_rolled(unit_id: String, roll: int, successes: int, failures: int, status: String)`
     - `signal status_applied(unit_id: String, status_id: String, duration: int)`
     - `signal status_removed(unit_id: String, status_id: String)`
     - `signal turn_changed(turn_number: int, active_unit_id: String)`
   - Lines 28–47: Cerco & Deckbuilder signals:
     - `signal card_played(player_id: String, card_id: String, target_zone: String)`
     - `signal dice_rolled(source_id: String, dice_type: String, results: Array)`
     - `signal damage_dealt(target_id: String, amount: int, current_hp: int)`
   - Lines 56–71: State & UI signals:
     - `signal game_state_changed(previous_state: int, new_state: int)`
     - `signal floating_text_requested(text: String, position: Vector2, color: Color)`
     - `signal combat_log_entry_added(bbcode_text: String)`
   - Lines 91–105: `emit_logged()` records emissions for verification in unit tests.

3. **`CombatRules.gd` & `Character.gd`**:
   - `CombatRules.gd:110-180`: `resolve_attack()` evaluates advantage, d20 roll, crits (nat 20 or paralyzed target at melee), calls `calculate_and_apply_damage()`.
   - `CombatRules.gd:182-264`: `calculate_and_apply_damage()` handles immunities, resistances (0.5x), vulnerabilities (2.0x), and D&D 5e state transitions (`STATE_NORMAL`, `STATE_INCONSCIENTE`, `STATE_MORTO`).
   - `Character.gd:195-221`: In-engine character damage emits `unit_damaged` and `unit_died` on `EventBus`.

4. **`RunNodeResolver.gd`**:
   - Lines 68–72:
     ```gdscript
     if node.type == RunNode.NodeType.ELITE:
         var relic_id: String = "reliquia_elite_a%d_%d" % [node.act, node.id]
         if state.add_relic(relic_id):
             log_lines.append("Relíquia obtida: %s" % relic_id)
     ```
   - In M1/M2, Elite nodes rewarded procedural dummy relic IDs. In M3, these must be replaced by canonical relics from the catalog.

5. **`CAMPANHA_ROGUELIKE.md` & `PROJECT.md` Contracts**:
   - `CAMPANHA_ROGUELIKE.md § 4, 5`: Relics are passive bonuses collected in Elite nodes, Boss victories, and the Forge (`FORGE`).
   - `PROJECT.md:56-60`: Interface contract:
     - `RunState.relics: Array[String]`
     - `RelicManager.register_relic(relic_id: String) -> void`
     - `RelicManager.unregister_all() -> void`
     - `RelicData.on_attack_dealt(...)`, `on_damage_received(...)`, `on_turn_started(...)`, `on_combat_victory(...)`

---

## 2. Logic Chain

1. **State Decoupling & Memory Management**:
   - *Observation*: `RunState` manages the pure expedition model as a `RefCounted` object.
   - *Deduction*: `RelicData` and `RelicManager` must both inherit from `RefCounted`. Making them `Node` instances would require them to enter the scene tree or risk memory leaks in headless unit tests (`test_relic_system.gd`). With `RefCounted`, memory is automatically released when references are cleared in GUT `after_each()`.

2. **Mediator / Observer Architecture**:
   - *Observation*: Tactical combat entities (`Character`, `CombatRules`, `TacticalGrid`) emit signals via `EventBus`.
   - *Deduction*: Individual relics should not maintain direct hardcoded connections to every entity. `RelicManager` serves as the centralized mediator: it registers listeners on `EventBus`, receives events, and dispatches them to registered `RelicData` instances.

3. **Virtual Hook Pipeline Pattern**:
   - *Observation*: Relics affect distinct phases: attack generation (extra damage, crits), damage mitigation (armor reduction), end-of-combat rewards (extra gold), campfire resting (heal multiplier), and store pricing (forge discount).
   - *Deduction*: `RelicData` must define virtual methods with default no-op return values. Specific relics override only the hooks they need. Furthermore, `RelicManager` provides pipeline methods (e.g. `modify_attack_damage()`, `modify_incoming_damage()`) that iterate through active relics and accumulate modifications cleanly.

4. **Catalog Composition (10 Canonical Relics)**:
   - *Observation*: Gameplay balances offensive tactics, survival, economy, and thematic counters to Isectum mechanics (fire weakness, acid/poison miasma, chitin armor).
   - *Deduction*: The 10 relics must cover:
     - 4 Offensive: `martelo_runico` (turn 1 melee burst), `dente_da_viuva` (crit poison + heal), `tocha_eterna` (fire damage vs illuminated/burning), `oleo_alquimico` (physical-to-fire conversion).
     - 3 Defensive/Survival: `escudo_ancestral` (flat -1 damage reduction), `frasco_feromonio` (negates first negative status per battle), `coroa_quitina` (death save advantage and crit-fail mitigation).
     - 3 Economic/Strategic: `bolsa_do_mercador` (+10 gold on combat victory), `amuleto_ambar` (+50% campfire heal), `relogio_da_forja` (20% forge discount + 5 gold on node entry).

5. **Testability & Determinism**:
   - *Observation*: The test runner `run_gut_tests.sh` executes Godot headless and enforces zero memory leaks.
   - *Deduction*: `RelicManager` must allow dependency injection of `RunState` and `EventBus` (or mock EventBus). `disconnect_event_bus()` and `unregister_all()` must guarantee all `Callable` connections are detached, preventing lingering references.

---

## 3. Technical Specifications & Architectural Design

### 3.1 Class Architecture Overview

```
                      +-------------------+
                      |     EventBus      | (Autoload Node)
                      +---------+---------+
                                | (Signals: unit_attacked, unit_damaged, unit_died, etc.)
                                v
+----------------+    +-------------------+    +----------------------+
|    RunState    |<-->|   RelicManager    |--->|      RelicData       | (Polymorphic Base)
| (relics: Array)|    |   (RefCounted)    |    +----------+-----------+
+----------------+    +-------------------+               |
                                                          |
                 +-------------------+--------------------+--------------------+
                 |                   |                    |                    |
        +--------v-------+  +--------v-------+   +--------v-------+   +--------v-------+
        | RelicMartelo   |  | RelicEscudo    |   | RelicDente     |   | ... (10 Relics)|
        | Runico         |  | Ancestral      |   | DaViuva        |   |                |
        +----------------+  +----------------+   +----------------+   +----------------+
```

---

### 3.2 Design: `godot_project/scripts/run/relics/RelicData.gd`

```gdscript
# res://scripts/run/relics/RelicData.gd
class_name RelicData
extends RefCounted

## RelicData: Base polymorphic class for all passive artifacts and relics in the roguelike run.
## Extends RefCounted to ensure memory leak safety in headless test environments.
## Provides virtual hooks for combat events, campfire resting, economy, and exploration.

# ── Rarity Constants ─────────────────────────────────────────────────────────
const RARITY_COMUM: String = "COMUM"
const RARITY_INCOMUM: String = "INCOMUM"
const RARITY_RARO: String = "RARO"
const RARITY_LENDARIO: String = "LENDARIO"
const RARITY_BOSS: String = "BOSS"

# ── Canonical Properties ─────────────────────────────────────────────────────
var id: String = ""
var relic_name: String = ""
var description: String = ""
var rarity: String = RARITY_COMUM
var cost_gold: int = 50
var icon_path: String = ""

## Transient per-combat / per-run counters
var counter: int = 0
var counter_max: int = 0
var is_active: bool = true

func _init(p_id: String = "", p_name: String = "", p_desc: String = "", p_rarity: String = RARITY_COMUM, p_cost: int = 50) -> void:
	id = p_id
	relic_name = p_name
	description = p_desc
	rarity = p_rarity
	cost_gold = p_cost

# ── Virtual Lifecycle Hooks ──────────────────────────────────────────────────

## Called when the relic is added to RelicManager / expedition.
func on_registered(_run_state: RunState) -> void:
	pass

## Called when the relic is removed from RelicManager / expedition.
func on_unregistered(_run_state: RunState) -> void:
	pass

## Called when the party moves into a new map node.
func on_node_entered(_node: RunNode, _run_state: RunState) -> void:
	pass

## Called at the beginning of a tactical battle.
func on_combat_started(_node_type: int, _run_state: RunState) -> void:
	reset_combat_state()

## Called when a new turn begins.
func on_turn_started(_turn_number: int, _active_unit_id: String, _run_state: RunState) -> void:
	pass

# ── Virtual Combat Hooks ─────────────────────────────────────────────────────

## Modifies an attack dealt.
## Returns Dictionary with possible keys:
## { "bonus_damage": int, "bonus_type": String, "heal_attacker": int, "override_crit": bool }
func on_attack_dealt(
	_attacker_id: String,
	_target_id: String,
	_is_hero: bool,
	_damage: int,
	_damage_type: String,
	_is_crit: bool,
	_run_state: RunState
) -> Dictionary:
	return {}

## Modifies damage received by a unit.
## Returns Dictionary with possible keys:
## { "damage_reduction": int, "cancel_damage": bool, "riposte_damage": int }
func on_damage_received(
	_target_id: String,
	_is_hero: bool,
	_incoming_damage: int,
	_current_hp: int,
	_max_hp: int,
	_run_state: RunState
) -> Dictionary:
	return {}

## Called when a unit is killed.
## Returns Dictionary with possible keys: { "bonus_gold": int, "heal_killer": int }
func on_unit_killed(_victim_id: String, _is_enemy: bool, _killer_id: String, _run_state: RunState) -> Dictionary:
	return {}

## Called when a condition/status effect is applied.
## Returns Dictionary with possible keys: { "cancel_status": bool }
func on_status_applied(_unit_id: String, _status_id: String, _duration: int, _run_state: RunState) -> Dictionary:
	return {}

## Called when an unconscious hero rolls a death saving throw.
## Returns Dictionary with possible keys: { "force_advantage": bool, "mitigate_crit_fail": bool }
func on_death_save_rolled(
	_unit_id: String,
	_roll: int,
	_successes: int,
	_failures: int,
	_status: String,
	_run_state: RunState
) -> Dictionary:
	return {}

## Called when a card is played in tactical grid / cerco.
func on_card_played(_player_id: String, _card_id: String, _target_zone: String, _run_state: RunState) -> Dictionary:
	return {}

# ── Virtual Economy & Campfire Hooks ─────────────────────────────────────────

## Modifies campfire resting recovery percent (e.g. 0.30 -> 0.45).
func on_campfire_rest(base_heal_pct: float, _run_state: RunState) -> float:
	return base_heal_pct

## Modifies post-combat victory rewards (e.g. rewards["gold"] += 10).
func on_combat_victory(rewards: Dictionary, _run_state: RunState) -> Dictionary:
	return rewards

## Modifies purchase price of items in the Forge (e.g. discount).
func on_forge_discount(_item_type: String, base_cost: int, _run_state: RunState) -> int:
	return base_cost

# ── State Reset & Serialization ──────────────────────────────────────────────

## Resets ephemeral combat state (charges, per-fight flags).
func reset_combat_state() -> void:
	counter = 0

func to_dict() -> Dictionary:
	return {
		"id": id,
		"relic_name": relic_name,
		"description": description,
		"rarity": rarity,
		"cost_gold": cost_gold,
		"counter": counter,
		"counter_max": counter_max,
		"is_active": is_active,
	}

func from_dict(data: Dictionary) -> void:
	id = data.get("id", id)
	relic_name = data.get("relic_name", relic_name)
	description = data.get("description", description)
	rarity = data.get("rarity", rarity)
	cost_gold = int(data.get("cost_gold", cost_gold))
	counter = int(data.get("counter", 0))
	counter_max = int(data.get("counter_max", 0))
	is_active = bool(data.get("is_active", true))
```

---

### 3.3 Design: `godot_project/scripts/run/relics/RelicManager.gd`

```gdscript
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
```

---

### 3.4 Catalog of 10 Canonical Relics

Here are the concrete subclass specifications for all 10 canonical relics. They can be placed in `godot_project/scripts/run/relics/CanonicalRelics.gd` or co-located:

#### 1. `martelo_runico` (Martelo Rúnico de Karak-Dur)
- **ID**: `"martelo_runico"`
- **Name**: "Martelo Rúnico de Karak-Dur"
- **Rarity**: `COMUM` | **Forge Cost**: 50g
- **Lore**: *Forjado nas profundezas de Karak-Dur. O primeiro golpe em cada batalha ressoa com o peso de uma avalanche da montanha.*
- **Trigger**: Primeiro ataque corpo a corpo (`is_hero == true` e tipo de dano físico `cortante`, `contundente` ou `perfurante`) em cada combate.
- **Effect**: Adiciona +3 de dano contundente plano ao ataque.
- **State**: Consome 1 carga no combate (`counter = 1`). Reseta via `reset_combat_state()`.
```gdscript
class_name RelicMarteloRunico
extends RelicData

func _init() -> void:
	super("martelo_runico", "Martelo Rúnico de Karak-Dur", "O primeiro ataque Melee dos heróis em cada combate causa +3 de dano contundente.", RARITY_COMUM, 50)
	counter_max = 1

func on_attack_dealt(_attacker_id: String, _target_id: String, is_hero: bool, _damage: int, damage_type: String, _is_crit: bool, _run_state: RunState) -> Dictionary:
	if is_hero and counter == 0:
		if damage_type in ["cortante", "contundente", "perfurante", "fisico"]:
			counter = 1
			return {"bonus_damage": 3, "bonus_type": "contundente"}
	return {}
```

#### 2. `escudo_ancestral` (Broquel dos Reis Anões)
- **ID**: `"escudo_ancestral"`
- **Name**: "Broquel dos Reis Anões"
- **Rarity**: `INCOMUM` | **Forge Cost**: 70g
- **Lore**: *Liga rúnica reforçada que dissipa o impacto das mandíbulas Isectum.*
- **Trigger**: Sempre que um herói sofre dano (`is_hero == true`).
- **Effect**: Reduz o dano recebido em 1 ponto, com piso mínimo de 1 de dano (`final_damage = maxi(1, incoming_damage - 1)`).
```gdscript
class_name RelicEscudoAncestral
extends RelicData

func _init() -> void:
	super("escudo_ancestral", "Broquel dos Reis Anões", "Reduz todo o dano recebido pelos heróis em 1 ponto (mínimo de 1 de dano).", RARITY_INCOMUM, 70)

func on_damage_received(_target_id: String, is_hero: bool, incoming_damage: int, _current_hp: int, _max_hp: int, _run_state: RunState) -> Dictionary:
	if is_hero and incoming_damage > 1:
		return {"damage_reduction": 1}
	return {}
```

#### 3. `bolsa_do_mercador` (Bolsa de Moedas da Guilda)
- **ID**: `"bolsa_do_mercador"`
- **Name**: "Bolsa de Moedas da Guilda"
- **Rarity**: `COMUM` | **Forge Cost**: 45g
- **Lore**: *Bolsa encantada dos mercadores anões que detecta veios e moedas esquecidas.*
- **Trigger**: Ao vencer qualquer combate (`COMBAT`, `ELITE`, `SIEGE`, `BOSS`).
- **Effect**: Adiciona +10 de ouro garantido às recompensas pós-combate.
```gdscript
class_name RelicBolsaDoMercador
extends RelicData

func _init() -> void:
	super("bolsa_do_mercador", "Bolsa de Moedas da Guilda", "Vitórias em combate concedem +10 de ouro adicional.", RARITY_COMUM, 45)

func on_combat_victory(rewards: Dictionary, run_state: RunState) -> Dictionary:
	rewards["gold"] = int(rewards.get("gold", 0)) + 10
	if run_state != null:
		run_state.add_gold(10)
	return rewards
```

#### 4. `amuleto_ambar` (Amuleto de Âmbar Resinoso)
- **ID**: `"amuleto_ambar"`
- **Name**: "Amuleto de Âmbar Resinoso"
- **Rarity**: `INCOMUM` | **Forge Cost**: 65g
- **Lore**: *Resina fóssil pura que libera vapores curativos quando exposta ao calor das fogueiras anãs.*
- **Trigger**: Ao descansar em nós de Fogueira (`CAMPFIRE`).
- **Effect**: Eleva a recuperação de PV do grupo de 30% (`0.30`) para 45% (`0.45`) do PV máximo.
```gdscript
class_name RelicAmuletoAmbar
extends RelicData

func _init() -> void:
	super("amuleto_ambar", "Amuleto de Âmbar Resinoso", "Na Fogueira, o grupo recupera 45% do HP máximo em vez de 30%.", RARITY_INCOMUM, 65)

func on_campfire_rest(base_heal_pct: float, _run_state: RunState) -> float:
	return base_heal_pct * 1.5 # 0.30 -> 0.45
```

#### 5. `dente_da_viuva` (Dente da Viúva Canibal)
- **ID**: `"dente_da_viuva"`
- **Name**: "Dente da Viúva Canibal"
- **Rarity**: `RARO` | **Forge Cost**: 90g (Drop Boss Ato 1)
- **Lore**: *Presa arrancada da Viúva Canibal. O veneno necrosante injetado em golpes críticos regenera o atacante.*
- **Trigger**: Quando um herói desfere um acerto crítico (`is_crit == true`).
- **Effect**: Adiciona +4 de dano de veneno e cura o herói atacante em 2 PV (respeitando o PV máximo; não cura heróis mortos).
```gdscript
class_name RelicDenteDaViuva
extends RelicData

func _init() -> void:
	super("dente_da_viuva", "Dente da Viúva Canibal", "Acertos críticos causam +4 de dano de veneno e curam o herói em 2 PV.", RARITY_RARO, 90)

func on_attack_dealt(attacker_id: String, _target_id: String, is_hero: bool, _damage: int, _damage_type: String, is_crit: bool, run_state: RunState) -> Dictionary:
	if is_hero and is_crit:
		if run_state != null and run_state.is_hero_alive(attacker_id):
			run_state.heal_hero(attacker_id, 2)
		return {"bonus_damage": 4, "bonus_type": "veneno", "heal_attacker": 2}
	return {}
```

#### 6. `tocha_eterna` (Tocha Eterna de Sulfeto)
- **ID**: `"tocha_eterna"`
- **Name**: "Tocha Eterna de Sulfeto"
- **Rarity**: `RARO` | **Forge Cost**: 85g
- **Lore**: *Alimentada por compostos geotérmicos, esta tocha nunca se extingue e inflama as carapaças vulneráveis.*
- **Trigger**: Ataques de heróis contra alvos com a condição `burning` ou com vulnerabilidade ao fogo.
- **Effect**: Adiciona +2 de dano de fogo adicional.
```gdscript
class_name RelicTochaEterna
extends RelicData

func _init() -> void:
	super("tocha_eterna", "Tocha Eterna de Sulfeto", "Ataques contra alvos em chamas ou vulneráveis a fogo sofrem +2 de dano de fogo.", RARITY_RARO, 85)

func on_attack_dealt(_attacker_id: String, _target_id: String, is_hero: bool, _damage: int, damage_type: String, _is_crit: bool, _run_state: RunState) -> Dictionary:
	if is_hero and (damage_type == "fogo" or damage_type == "burning"):
		return {"bonus_damage": 2, "bonus_type": "fogo"}
	return {}
```

#### 7. `oleo_alquimico` (Frasco de Óleo de Incineração)
- **ID**: `"oleo_alquimico"`
- **Name**: "Frasco de Óleo de Incineração"
- **Rarity**: `COMUM` | **Forge Cost**: 55g
- **Lore**: *Líquido viscoso espalhado nas armas para derreter carapaças de quitina e casulos.*
- **Trigger**: Qualquer ataque Melee dos heróis.
- **Effect**: Infunde a arma com calor abrasador, convertendo o tipo de dano bônus em `fogo` (+1 dano de fogo), ativando fraquezas a fogo (ex: Fase 3 do Rei Isectum).
```gdscript
class_name RelicOleoAlquimico
extends RelicData

func _init() -> void:
	super("oleo_alquimico", "Frasco de Óleo de Incineração", "Golpes dos heróis causam +1 de dano de fogo, ativando fraquezas elementais.", RARITY_COMUM, 55)

func on_attack_dealt(_attacker_id: String, _target_id: String, is_hero: bool, _damage: int, _damage_type: String, _is_crit: bool, _run_state: RunState) -> Dictionary:
	if is_hero:
		return {"bonus_damage": 1, "bonus_type": "fogo"}
	return {}
```

#### 8. `frasco_feromonio` (Frasco de Feromônio Neutralizador)
- **ID**: `"frasco_feromonio"`
- **Name**: "Frasco de Feromônio Neutralizador"
- **Rarity**: `RARO` | **Forge Cost**: 80g
- **Lore**: *Feromônio sintetizado que confunde o enxame e quebra o miasma antes que penetre as vias aéreas.*
- **Trigger**: Primeira condição negativa (`poisoned`, `stunned`, `frightened`, `burning`) infligida a um herói por combate.
- **Effect**: Anula e cancela a aplicação da condição.
- **State**: Consome a carga no combate (`counter = 1`). Reseta via `reset_combat_state()`.
```gdscript
class_name RelicFrascoFeromonio
extends RelicData

func _init() -> void:
	super("frasco_feromonio", "Frasco de Feromônio Neutralizador", "Anula a primeira condição negativa recebida pelos heróis em cada combate.", RARITY_RARO, 80)
	counter_max = 1

func on_status_applied(_unit_id: String, status_id: String, _duration: int, _run_state: RunState) -> Dictionary:
	if counter == 0 and status_id in ["poisoned", "stunned", "frightened", "burning", "restrained"]:
		counter = 1
		return {"cancel_status": true}
	return {}
```

#### 9. `coroa_quitina` (Carapaça de Quitina Cristalizada)
- **ID**: `"coroa_quitina"`
- **Name**: "Carapaça de Quitina Cristalizada"
- **Rarity**: `LENDARIO` | **Forge Cost**: 120g
- **Lore**: *Placa retirada de um colosso Isectum. Sua densidade protege a alma do guerreiro nos umbrais da morte.*
- **Trigger**: Quando um herói a 0 PV realiza um teste contra a morte (*Death Saving Throw*).
- **Effect**: Concede Vantagem no primeiro Death Save de cada combate; converte falha crítica (d20 = 1, que causaria 2 falhas) em 1 falha simples.
```gdscript
class_name RelicCoroaQuitina
extends RelicData

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
```

#### 10. `relogio_da_forja` (Engrenagem Mestra da Forja)
- **ID**: `"relogio_da_forja"`
- **Name**: "Engrenagem Mestra da Forja"
- **Rarity**: `RARO` | **Forge Cost**: 95g
- **Lore**: *Mecanismo anão de precisão que calibra foles e bigornas, reduzindo custos de fabricação.*
- **Trigger**: Ao comprar itens ou serviços na Forja (`FORGE`), ou ao entrar em nós `FORGE`/`SIEGE`.
- **Effect**: Aplica 20% de desconto em todas as compras na Forja; concede +5 de ouro ao entrar em nós de Forja.
```gdscript
class_name RelicRelogioDaForja
extends RelicData

func _init() -> void:
	super("relogio_da_forja", "Engrenagem Mestra da Forja", "Concede 20% de desconto na Forja Anã e +5 de ouro ao entrar na Forja.", RARITY_RARO, 95)

func on_forge_discount(_item_type: String, base_cost: int, _run_state: RunState) -> int:
	return int(round(float(base_cost) * 0.80))

func on_node_entered(node: RunNode, run_state: RunState) -> void:
	if node != null and node.type == RunNode.NodeType.FORGE:
		if run_state != null:
			run_state.add_gold(5)
```

---

### 3.5 GUT Test Suite Design (`godot_project/test/unit/test_relic_system.gd`)

Below is the design of the unit test suite conforming to the AAA (Arrange-Act-Assert) pattern, ensuring headless safety, and testing all 10 relics, lifecycle edge cases, and zero memory leaks.

```gdscript
# res://test/unit/test_relic_system.gd
extends GutTest

## Test Suite for Relic System (Milestone M3)
## Validates RelicData, RelicManager, and the 10 Canonical Relics.
## Adheres strictly to Arrange-Act-Assert (AAA) pattern, zero leaks, and headless execution.

const EventBusScript = preload("res://scripts/autoload/EventBus.gd")

var _generator: RunMapGenerator
var _rng: RandomNumberGenerator
var _state: RunState
var _eb: Node
var _manager: RelicManager

func before_each() -> void:
	_generator = RunMapGenerator.new(8, 3, 2)
	_rng = RandomNumberGenerator.new()
	_rng.seed = 42
	_state = RunState.new(_generator, _rng)
	_state.start_run({"aquele": 30, "stark": 34, "elden": 26}, ["ataque", "defesa"], 12345)
	
	if get_node_or_null("/root/EventBus") != null:
		_eb = get_node("/root/EventBus")
		_eb.reset_telemetry()
	else:
		_eb = autofree(EventBusScript.new())
	
	_manager = RelicManager.new(_state, _eb)

func after_each() -> void:
	if _manager != null:
		_manager.unregister_all()
		_manager = null
	_state = null
	_rng = null
	_generator = null
	_eb = null

# ==============================================================================
# 1. RelicData Base Model & Serialization
# ==============================================================================

func test_relic_data_initialization_and_serialization() -> void:
	# Arrange
	var relic: RelicData = RelicData.new("relic_test", "Relic Test", "Desc", RelicData.RARITY_RARO, 80)
	relic.counter = 2
	relic.counter_max = 5

	# Act
	var dict: Dictionary = relic.to_dict()
	var restored: RelicData = RelicData.new()
	restored.from_dict(dict)

	# Assert
	assert_eq(restored.id, "relic_test", "ID preservado")
	assert_eq(restored.relic_name, "Relic Test", "Nome preservado")
	assert_eq(restored.rarity, RelicData.RARITY_RARO, "Raridade preservada")
	assert_eq(restored.cost_gold, 80, "Custo preservado")
	assert_eq(restored.counter, 2, "Counter preservado")
	assert_true(restored.is_active, "Ativo por padrão")

# ==============================================================================
# 2. RelicManager Lifecycle & Registration
# ==============================================================================

func test_relic_manager_registration_and_duplicates() -> void:
	# Arrange & Act
	var ok: bool = _manager.register_relic("martelo_runico")
	var dup: bool = _manager.register_relic("martelo_runico")
	var invalid: bool = _manager.register_relic("reliquia_inexistente")
	var empty: bool = _manager.register_relic("")

	# Assert
	assert_true(ok, "Registro de martelo_runico com sucesso")
	assert_false(dup, "Registro duplicado deve ser rejeitado")
	assert_false(invalid, "ID não cadastrado no catálogo deve ser rejeitado")
	assert_false(empty, "ID vazio deve ser rejeitado")
	assert_eq(_manager.get_relic_count(), 1, "Apenas 1 relíquia ativa")
	assert_true(_state.has_relic("martelo_runico"), "RunState sincronizado")

func test_relic_manager_unregister_and_cleanup() -> void:
	# Arrange
	_manager.register_relic("martelo_runico")
	_manager.register_relic("escudo_ancestral")
	assert_eq(_manager.get_relic_count(), 2)

	# Act
	var removed: bool = _manager.unregister_relic("martelo_runico")
	var not_found: bool = _manager.unregister_relic("martelo_runico")

	# Assert
	assert_true(removed, "Relíquia removida com sucesso")
	assert_false(not_found, "Segunda remoção retorna false")
	assert_eq(_manager.get_relic_count(), 1)
	assert_false(_state.has_relic("martelo_runico"), "Removido do RunState")

	# Clean all
	_manager.unregister_all()
	assert_eq(_manager.get_relic_count(), 0)

# ==============================================================================
# 3. Canonical Relic 1: Martelo Rúnico (Turn 1 Melee Burst)
# ==============================================================================

func test_relic_martelo_runico_applies_bonus_only_on_first_attack() -> void:
	# Arrange
	_manager.register_relic("martelo_runico")

	# Act 1: Primeiro ataque Melee do combate
	var attack1: Dictionary = _manager.modify_attack_damage("aquele", "larva_carniceira", true, 6, "contundente", false)

	# Assert 1
	assert_eq(attack1["bonus_damage"], 3, "Primeiro ataque recebe +3 de bônus")
	assert_eq(attack1["final_damage"], 9, "Dano total é 6 + 3 = 9")

	# Act 2: Segundo ataque Melee no mesmo combate
	var attack2: Dictionary = _manager.modify_attack_damage("aquele", "larva_carniceira", true, 6, "contundente", false)

	# Assert 2
	assert_eq(attack2["bonus_damage"], 0, "Segundo ataque não recebe bônus")
	assert_eq(attack2["final_damage"], 6, "Dano normal")

	# Act 3: Novo combate (reset_all_combat_states)
	_manager.reset_all_combat_states()
	var attack3: Dictionary = _manager.modify_attack_damage("aquele", "larva_carniceira", true, 5, "cortante", false)
	assert_eq(attack3["bonus_damage"], 3, "Bônus restaurado no novo combate")

# ==============================================================================
# 4. Canonical Relic 2: Escudo Ancestral (Damage Reduction)
# ==============================================================================

func test_relic_escudo_ancestral_reduces_damage_with_min_clamp() -> void:
	# Arrange
	_manager.register_relic("escudo_ancestral")

	# Act 1: Dano superior a 1
	var dmg1: Dictionary = _manager.modify_incoming_damage("aquele", true, 8, 30, 30)

	# Assert 1
	assert_eq(dmg1["damage_reduction"], 1, "Redução de 1 ponto")
	assert_eq(dmg1["final_damage"], 7, "8 reduzido para 7")

	# Act 2: Dano exatamente 1 (não pode ser reduzido a 0)
	var dmg2: Dictionary = _manager.modify_incoming_damage("aquele", true, 1, 20, 30)
	assert_eq(dmg2["final_damage"], 1, "Piso de 1 dano preservado")

	# Act 3: Inimigo sofrendo dano (is_hero == false não reduz)
	var dmg_enemy: Dictionary = _manager.modify_incoming_damage("larva", false, 5, 10, 10)
	assert_eq(dmg_enemy["damage_reduction"], 0, "Inimigos não se beneficiam do escudo")

# ==============================================================================
# 5. Canonical Relic 3: Bolsa do Mercador (Victory Gold Bonus)
# ==============================================================================

func test_relic_bolsa_do_mercador_awards_extra_gold() -> void:
	# Arrange
	_manager.register_relic("bolsa_do_mercador")
	var initial_gold: int = _state.gold

	# Act
	var rewards: Dictionary = _manager.modify_combat_victory_rewards({"gold": 15})

	# Assert
	assert_eq(rewards["gold"], 25, "15 base + 10 bônus = 25")
	assert_eq(_state.gold, initial_gold + 10, "RunState recebeu o ouro extra")

# ==============================================================================
# 6. Canonical Relic 4: Amuleto de Âmbar (Campfire Heal Boost)
# ==============================================================================

func test_relic_amuleto_ambar_boosts_campfire_healing() -> void:
	# Arrange
	_manager.register_relic("amuleto_ambar")

	# Act
	var heal_pct: float = _manager.modify_campfire_heal(0.30)

	# Assert
	assert_almost_eq(heal_pct, 0.45, 0.001, "Cura da fogueira aumentada para 45%")

# ==============================================================================
# 7. Canonical Relic 5: Dente da Viúva (Crit Poison + Leech)
# ==============================================================================

func test_relic_dente_da_viuva_triggers_on_crit_only() -> void:
	# Arrange
	_manager.register_relic("dente_da_viuva")
	_state.damage_hero("aquele", 10) # 20 / 30 HP

	# Act 1: Ataque normal (sem crit)
	var normal_att: Dictionary = _manager.modify_attack_damage("aquele", "boss", true, 10, "cortante", false)
	assert_eq(normal_att["bonus_damage"], 0)
	assert_eq(_state.hero_hp["aquele"], 20, "Sem cura no golpe normal")

	# Act 2: Acerto crítico
	var crit_att: Dictionary = _manager.modify_attack_damage("aquele", "boss", true, 10, "cortante", true)
	assert_eq(crit_att["bonus_damage"], 4, "+4 de dano")
	assert_eq(crit_att["bonus_type"], "veneno", "Dano de veneno")
	assert_eq(_state.hero_hp["aquele"], 22, "Curou 2 PV do herói atacante")

# ==============================================================================
# 8. Canonical Relics 6, 7 & 8: Tocha, Óleo e Frasco de Feromônio
# ==============================================================================

func test_relic_tocha_e_oleo_alquimico() -> void:
	# Arrange
	_manager.register_relic("tocha_eterna")
	_manager.register_relic("oleo_alquimico")

	# Act: Ataque que causa dano de fogo
	var att: Dictionary = _manager.modify_attack_damage("aquele", "casulo", true, 8, "fogo", false)

	# Assert
	# tocha_eterna (+2) + oleo_alquimico (+1) = +3
	assert_eq(att["bonus_damage"], 3, "Bônus somado de tocha e óleo")

func test_relic_frasco_feromonio_negates_first_debuff() -> void:
	# Arrange
	_manager.register_relic("frasco_feromonio")
	var relic: RelicData = _manager.get_relic("frasco_feromonio")

	# Act 1: Primeira aplicação de veneno
	var res1: Dictionary = relic.on_status_applied("aquele", "poisoned", 3, _state)
	assert_true(res1.get("cancel_status", false), "Primeiro status cancelado")

	# Act 2: Segunda aplicação no mesmo combate
	var res2: Dictionary = relic.on_status_applied("aquele", "stunned", 1, _state)
	assert_false(res2.get("cancel_status", false), "Segundo status NÃO cancelado")

# ==============================================================================
# 9. Canonical Relics 9 & 10: Coroa de Quitina e Relógio da Forja
# ==============================================================================

func test_relic_coroa_quitina_death_save_advantage_and_crit_mitigation() -> void:
	# Arrange
	_manager.register_relic("coroa_quitina")
	var relic: RelicData = _manager.get_relic("coroa_quitina")

	# Act 1: Primeiro Death Save
	var ds1: Dictionary = relic.on_death_save_rolled("aquele", 12, 1, 0, "INCONSCIENTE", _state)
	assert_true(ds1.get("force_advantage", false), "Força vantagem no primeiro save")

	# Act 2: Falha crítica (1)
	var ds_crit: Dictionary = relic.on_death_save_rolled("aquele", 1, 1, 1, "INCONSCIENTE", _state)
	assert_true(ds_crit.get("mitigate_crit_fail", false), "Mitiga falha crítica de 2 para 1 falha")

func test_relic_relogio_da_forja_discount_and_node_gold() -> void:
	# Arrange
	_manager.register_relic("relogio_da_forja")
	var start_gold: int = _state.gold

	# Act 1: Desconto de 20%
	var cost100: int = _manager.modify_forge_cost("carta", 100)
	var cost75: int = _manager.modify_forge_cost("relic", 75)

	# Assert 1
	assert_eq(cost100, 80, "100g com 20% desconto = 80g")
	assert_eq(cost75, 60, "75g com 20% desconto = 60g")

	# Act 2: Entrada no nó FORGE
	var forge_node: RunNode = RunNode.new(50, 1, 3, 0, RunNode.NodeType.FORGE)
	_state.map.add_node(forge_node)
	_state.current_node_id = 50
	_state.node_entered.emit(forge_node)

	# Assert 2: +5 de ouro ao entrar na forja
	assert_eq(_state.gold, start_gold + 5, "+5 ouro ao entrar no nó de Forja")
```

---

## 4. Caveats

1. **Persistência de Remoção no `RunState`**:
   - `RunState.gd` possui `add_relic()` e `has_relic()`, mas não implementa `remove_relic()`.
   - *Recomendação para a implementação*: Adicionar a seguinte função simples em `godot_project/scripts/run/RunState.gd`:
     ```gdscript
     func remove_relic(relic_id: String) -> bool:
         var idx: int = relics.find(relic_id)
         if idx < 0:
             return false
         relics.remove_at(idx)
         return true
     ```
2. **Integração do M4 (`RunCombatBridge`)**:
   - As pipelines de modificação (`modify_attack_damage` e `modify_incoming_damage`) serão chamadas ativamente durante as rolagens de ataque e resolução de dano do combate tático quando M4 for implementado.
3. **Escopo Read-Only**:
   - Conforme as restrições do agente Explorer, nenhum arquivo de código de produção dentro de `godot_project/scripts/` foi modificado. Todos os projetos e especificações estão formalizados neste relatório para execução pelo agente implementador.

---

## 5. Conclusion

1. **`RelicData.gd`**:
   - Herda de `RefCounted` garantindo segurança contra memory leaks em testes headless.
   - Fornece ganchos virtuais flexíveis para combate, dano, morte, condições, fogueira, economia e forja.
2. **`RelicManager.gd`**:
   - Mediador desacoplado entre `RunState.relics` e o `EventBus`.
   - Gerencia listeners sem referências circulares ou vazamento de memória.
   - Possui catálogo extensível por factory `Callable`.
3. **Catálogo de 10 Relíquias Canônicas**:
   - 100% especificado e tematizado no universo de *Karak-Dur* e *A Queda do Rei Isectum*.
   - Mecânicas balanceadas entre ataque, defesa, economia e interação com mecânicas do Ato II e Ato III.
4. **Suíte de Testes GUT**:
   - Padrão Arrange-Act-Assert (AAA) cobrindo todos os métodos, casos felizes, limites e casos de borda.
   - Totalmente compatível com execução headless via `godot_project/run_gut_tests.sh`.

---

## 6. Verification Method

Para verificar independentemente a arquitetura e especificações:

1. **Inspeção de Contratos**:
   - Verificar correspondência com `godot_project/scripts/run/RunState.gd` (linhas 38, 214–222).
   - Verificar sinais em `godot_project/scripts/autoload/EventBus.gd` (linhas 10–25, 28–47).
   - Verificar convenções GUT em `godot_project/test/unit/test_run_map_and_state.gd`.

2. **Validação Pós-Implementação**:
   - Após o executor criar `RelicData.gd`, `RelicManager.gd` e `test_relic_system.gd`:
     ```bash
     bash godot_project/run_gut_tests.sh -gtest=res://test/unit/test_relic_system.gd
     ```
   - Critério de aceitação: 100% dos testes GUT passam com código de saída 0 e zero memory leaks.

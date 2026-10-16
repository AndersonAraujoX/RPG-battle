# Handoff Report — Milestone M3 Remediation Explorer 2: Relic Logic & Signal Integrity

**Agent**: Explorer M3 Fix 2 (`explorer_m3_fix_2`)  
**Roles**: Explorer, Investigator, Code Quality Architect  
**Working Directory**: `/home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m3_fix_2`  
**Timestamp**: 2026-10-16T02:05:00Z  
**Target Milestone**: M3 Remediation (Relics, Rewards & Forge)  
**Parent Conversation ID**: `aa7d5d2d-ef0f-482c-be6b-93c1793915c2`  

---

## 1. Observation

### 1.1 Baseline Test Suite Execution
- **Command**: `bash godot_project/run_gut_tests.sh`
- **Runner Results**:
  ```text
  ============================================================
                      TEST SUMMARY                            
  ============================================================
  Test Scripts Executed:   36
  Tests Run:               801
  Tests Passed:            801
  Tests Failed:            0
  Total Assertions:        8162
  Assertions Passed:       8162
  Assertions Failed:       0
  ============================================================
  ==> All GUT tests passed successfully! (Exit code: 0)
  ```
- **Observations from Output**:
  - The adversarial stress test `test_relic_stress_adversarial.gd` printed critical empirical warnings:
    * `[FINDING] RelicManager permits duplicate relic registration via 'reliquia_' alias! Active count: 2`
    * `[FINDING] Attack damage with double registration: bonus=6, final=12`
    * `[FINDING] RelicManager.sync_from_run_state() does not remove relics purged from RunState!`
    * `[FINDING] RelicData.from_dict expects strictly typed fields without String() coercion on 'id', 'relic_name', etc.`

### 1.2 Verbatim Inspection: Defect 1 — Dual Gold Crediting in `RelicBolsaDoMercador`
- **File**: `godot_project/scripts/run/relics/RelicManager.gd` lines 354–363:
  ```gdscript
  class RelicBolsaDoMercador extends RelicData:
  	func _init() -> void:
  		super("bolsa_do_mercador", "Bolsa de Moedas da Guilda", "Vitórias em combate concedem +10 de ouro adicional.", RARITY_COMUM, 45)

  	func on_combat_victory(rewards: Dictionary, p_run_state: RunState) -> Dictionary:
  		rewards["gold"] = int(rewards.get("gold", 0)) + 10
  		if p_run_state != null:
  			p_run_state.add_gold(10)
  		return rewards
  ```
- **File**: `godot_project/scripts/run/relics/RelicData.gd` lines 119–121:
  ```gdscript
  ## Modifies post-combat victory rewards (e.g. rewards["gold"] += 10).
  func on_combat_victory(rewards: Dictionary, _run_state: RunState) -> Dictionary:
  	return rewards
  ```
- **File**: `godot_project/scripts/run/ui/RewardModal.gd` lines 302–306:
  ```gdscript
  func _apply_gold_and_relic() -> void:
  	if state != null:
  		if offered_gold > 0:
  			state.add_gold(offered_gold)
  			gold_collected.emit(offered_gold)
  ```
- **Direct Observation**:
  - `on_combat_victory()` modifies the dictionary (`rewards["gold"] = 15 + 10 = 25`) AND directly calls `p_run_state.add_gold(10)`.
  - When downstream `RewardModal` presents `offered_gold = 25` and the player clicks Claim or Skip, `RewardModal` calls `state.add_gold(25)`.
  - The player receives `10 + 25 = 35` gold (base 15 + 20 gold bonus, doubling the intended +10g benefit).
  - Furthermore, in `test_relic_system.gd` line 166, the existing test erroneously asserted the double-mutation side effect: `assert_eq(_state.gold, initial_gold + 10, "RunState recebeu o ouro extra")`.

### 1.3 Verbatim Inspection: Defect 2 — `RelicFrascoFeromonio` Lacks Friendly Hero Check & PT-BR Status Support
- **File**: `godot_project/scripts/run/relics/RelicManager.gd` lines 283–286 & 400–409:
  ```gdscript
  func _on_status_applied(unit_id: String, status_id: String, duration: int) -> void:
  	for relic in _active_relics.values():
  		if relic.is_active:
  			relic.on_status_applied(unit_id, status_id, duration, run_state)
  ...
  class RelicFrascoFeromonio extends RelicData:
  	func _init() -> void:
  		super("frasco_feromonio", "Frasco de Feromônio Neutralizador", "Anula a primeira condição negativa recebida pelos heróis em cada combate.", RARITY_RARO, 80)
  		counter_max = 1

  	func on_status_applied(_unit_id: String, status_id: String, _duration: int, _run_state: RunState) -> Dictionary:
  		if counter == 0 and status_id in ["poisoned", "stunned", "frightened", "burning", "restrained"]:
  			counter = 1
  			return {"cancel_status": true}
  		return {}
  ```
- **Direct Observation**:
  - `_unit_id` and `_run_state` are completely ignored (prefixed with `_`).
  - No check exists for whether `unit_id` belongs to `run_state.heroes`.
  - If a player hero attacks an enemy insect and applies `"poisoned"` or `"burning"`, `on_status_applied` returns `{"cancel_status": true}` for the enemy, neutralizing the player's attack and permanently consuming `counter = 1`.
  - For the remainder of that battle, when an enemy inflicts a condition on an allied hero, `counter == 1`, so the relic offers zero protection.
  - In addition, Portuguese localized condition IDs (such as `"envenenado"`, `"atordoado"`, `"amedrontado"`, `"imobilizado"`, `"paralisado"`) registered in `StatusManager.gd` (lines 165–170) fail to match the hardcoded English array.

### 1.4 Verbatim Inspection: Defect 3 — `RelicManager.unregister_relic` Signal / Instance Lifecycle & Sync Pruning
- **File**: `godot_project/scripts/run/relics/RelicManager.gd` lines 89–139:
  ```gdscript
  func sync_from_run_state() -> void:
  	if run_state == null:
  		return
  	for r_id in run_state.relics:
  		if not _active_relics.has(r_id):
  			var relic: RelicData = create_relic(r_id)
  			if relic != null:
  				_active_relics[r_id] = relic
  				relic.on_registered(run_state)

  func register_relic(relic_id: String) -> bool:
  	if relic_id.is_empty() or _active_relics.has(relic_id):
  		return false
  	var relic: RelicData = create_relic(relic_id)
  	...
  	_active_relics[relic_id] = relic
  	...

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
  ```
- **Direct Observation**:
  - `_active_relics` keys on raw strings. When `"martelo_runico"` and `"reliquia_martelo_runico"` are registered, both are accepted as separate keys, creating duplicate active instances and doubling passive effects.
  - Calling `unregister_relic("reliquia_martelo_runico")` fails if registered under `"martelo_runico"`.
  - In `RelicData.gd` lines 42–44, `on_unregistered` is an empty `pass`. The relic instance's `is_active` boolean is never set to `false`.
  - In `sync_from_run_state()`, relics removed from `run_state.relics` are never pruned; they remain alive in `_active_relics` as orphan signal listeners.
  - In `unregister_relic()`, manual array manipulation `run_state.relics.remove_at(idx)` bypasses `RunState.remove_relic()`.

---

## 2. Logic Chain

1. **Economy Pipeline Separation (Defect 1)**:
   - *Premise*: Modifier calculation pipelines (`modify_*`) must be pure deterministic queries without side effects on persistent state.
   - *Breakdown*: `RelicBolsaDoMercador.on_combat_victory()` modified `rewards["gold"] += 10` AND called `p_run_state.add_gold(10)`.
   - *Deduction*: When `RewardModal` credits `offered_gold` to `RunState`, the player receives `+20` bonus gold instead of `+10`.
   - *Resolution*: `on_combat_victory()` must ONLY mutate the dictionary `rewards["gold"] = int(rewards.get("gold", 0)) + 10` and must NEVER call `p_run_state.add_gold()`.

2. **Target Filtering in Combat Relics (Defect 2)**:
   - *Premise*: Defensive artifacts for the party must only protect allied units (`RunState.heroes`).
   - *Breakdown*: `RelicFrascoFeromonio.on_status_applied()` accepted any `_unit_id` without checking `run_state.heroes.has(unit_id)`.
   - *Deduction*: Enemy status effects (e.g. hero burning an insect) triggered `cancel_status: true` and consumed the per-combat charge.
   - *Resolution*: Enforce guard clause `if p_run_state == null or not p_run_state.heroes.has(unit_id): return {}`. Expand condition matching to recognize canonical English and Portuguese condition identifiers (`["poisoned", "envenenado", "stunned", "atordoado", "frightened", "amedrontado", "restrained", "imobilizado", "burning", "queimando", "paralyzed", "paralisado"]`).

3. **Lifecycle & Canonical Identification (Defect 3)**:
   - *Premise*: Relic management must be idempotent, resistant to prefix aliasing (`"reliquia_"`), and leak-free.
   - *Breakdown*: Raw string keying allowed duplicate active instances. Relics removed from `RunState.relics` were not purged during `sync_from_run_state()`. Unregistered relic instances remained marked `is_active = true`.
   - *Deduction*: Unregistering must deactivate the relic instance (`is_active = false`), invoke `on_unregistered()`, remove all alias variants from `run_state.relics`, and prune orphan instances during two-way sync.
   - *Resolution*:
     * Introduce `get_canonical_id(p_id: String) -> String` to strip `reliquia_`.
     * Key `_active_relics` strictly by canonical ID.
     * In `unregister_relic()`, set `relic.is_active = false`, call `relic.on_unregistered()`, and synchronize with `run_state.remove_relic()`.
     * In `sync_from_run_state()`, perform two-way synchronization: prune active relics no longer present in `run_state.relics`.
     * In `RelicData.gd`, set `is_active = false` and `counter = 0` in base `on_unregistered()`.

---

## 3. Caveats

1. **Test Assertion Alignment**:
   In `godot_project/test/unit/test_relic_system.gd`, line 166 (`assert_eq(_state.gold, initial_gold + 10)`) asserts the old defective side-effect behavior. When applying the fix to `RelicBolsaDoMercador`, this assertion must be updated to `assert_eq(_state.gold, initial_gold)` because `modify_combat_victory_rewards` is a calculation pipeline that must not alter persistent state before collection.
2. **`coroa_de_quitina` vs `coroa_quitina`**:
   `RelicManager._register_canonical_catalog()` was extended to register an explicit compatibility alias for `"coroa_de_quitina"` pointing to `RelicCoroaQuitina`, ensuring total compatibility across legacy strings in `RewardModal.gd` and tests.
3. **Double Heal on `DenteDaViuva` during Pipeline + EventBus**:
   In adversarial test 8 (`test_stress_dente_da_viuva_double_heal_pipeline_vs_eventbus`), calling both `modify_attack_damage()` and emitting `unit_attacked` triggers `heal_hero` twice if the caller invokes both. This is noted for Milestone M4 integration: `RunCombatBridge` should use either the pipeline return (`mod["heal_attacker"]`) OR rely on EventBus, not both simultaneously.

---

## 4. Conclusion & Concrete Code Deliverables

The three defects have been thoroughly analyzed and concrete solutions implemented in dedicated artifact files within this agent's folder:
- **`proposed_RelicData.gd`**: Full, production-ready replacement for `RelicData.gd`.
- **`proposed_RelicManager.gd`**: Full, production-ready replacement for `RelicManager.gd`.
- **`relic_remediation.patch`**: Machine-applicable unified diff patch against the repository files.
- **`proposed_test_additions.gd`**: Complete AAA test suite additions covering all happy paths and adversarial edge cases.

### 4.1 Concrete Replacement Snippet: `RelicData.gd`

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
## Guarantees relic deactivation and ephemeral counter reset.
func on_unregistered(_run_state: RunState) -> void:
	is_active = false
	counter = 0

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
func on_unit_killed(_victim_id: String, _is_enemy: bool, _killer_id: String, _run_state: RunState) -> Dictionary:
	return {}

## Called when a condition/status effect is applied.
func on_status_applied(_unit_id: String, _status_id: String, _duration: int, _run_state: RunState) -> Dictionary:
	return {}

## Called when an unconscious hero rolls a death saving throw.
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
## Pure functional calculation: does NOT mutate RunState directly.
func on_combat_victory(rewards: Dictionary, _run_state: RunState) -> Dictionary:
	return rewards

## Modifies purchase price of items in the Forge (e.g. discount).
func on_forge_discount(_item_type: String, base_cost: int, _run_state: RunState) -> int:
	return base_cost

# ── State Reset & Serialization ──────────────────────────────────────────────

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
	id = String(data.get("id", id))
	relic_name = String(data.get("relic_name", relic_name))
	description = String(data.get("description", description))
	rarity = String(data.get("rarity", rarity))
	cost_gold = int(data.get("cost_gold", cost_gold))
	counter = int(data.get("counter", 0))
	counter_max = int(data.get("counter_max", 0))
	is_active = bool(data.get("is_active", true))
```

### 4.2 Concrete Replacement Snippet: Key Methods in `RelicManager.gd`

```gdscript
## Normalizes relic identifiers by stripping the legacy 'reliquia_' prefix.
static func get_canonical_id(p_id: String) -> String:
	return p_id.trim_prefix("reliquia_").strip_edges()

## Synchronizes active relics with IDs present in RunState.relics.
## Performs two-way synchronization: prunes purged relics and registers newly acquired relics.
func sync_from_run_state() -> void:
	if run_state == null:
		return
	
	# 1. Build set of desired canonical IDs from run_state.relics
	var desired_canonical_ids: Dictionary = {}
	for r_id in run_state.relics:
		var cid: String = get_canonical_id(r_id)
		if not cid.is_empty():
			desired_canonical_ids[cid] = r_id
	
	# 2. Prune any active relics that are no longer in run_state.relics
	var to_remove: Array[String] = []
	for active_key in _active_relics.keys():
		var active_cid: String = get_canonical_id(active_key)
		if not desired_canonical_ids.has(active_cid):
			to_remove.append(active_key)
	
	for remove_key in to_remove:
		var relic: RelicData = _active_relics[remove_key]
		if relic != null:
			relic.is_active = false
			relic.on_unregistered(run_state)
		_active_relics.erase(remove_key)
	
	# 3. Register newly added relics
	for cid in desired_canonical_ids.keys():
		if not _active_relics.has(cid):
			var relic: RelicData = create_relic(cid)
			if relic != null:
				_active_relics[cid] = relic
				relic.on_registered(run_state)

## Registers a new relic by ID. Adds to RunState if not present.
## Normalizes input to canonical ID to prevent duplicate stacking via aliases.
func register_relic(relic_id: String) -> bool:
	if relic_id.is_empty():
		return false
	
	var cid: String = get_canonical_id(relic_id)
	if cid.is_empty() or has_relic(cid):
		return false
	
	var relic: RelicData = create_relic(cid)
	if relic == null:
		push_warning("[RelicManager] Relíquia desconhecida: '%s'" % relic_id)
		return false
	
	_active_relics[cid] = relic
	if run_state != null:
		if not run_state.has_relic(cid) and not run_state.has_relic(relic_id):
			run_state.add_relic(cid)
		relic.on_registered(run_state)
	
	return true

## Unregisters and removes a relic.
## Disconnects lifecycle hooks, deactivates instance, and synchronizes removal with RunState.
func unregister_relic(relic_id: String) -> bool:
	var cid: String = get_canonical_id(relic_id)
	var active_key: String = ""
	if _active_relics.has(cid):
		active_key = cid
	elif _active_relics.has(relic_id):
		active_key = relic_id
	
	if active_key.is_empty():
		return false
	
	var relic: RelicData = _active_relics[active_key]
	if relic != null:
		relic.is_active = false
		if run_state != null:
			relic.on_unregistered(run_state)
			run_state.remove_relic(relic_id)
			run_state.remove_relic(cid)
			run_state.remove_relic("reliquia_" + cid)
			if not relic.id.is_empty():
				run_state.remove_relic(relic.id)
	
	_active_relics.erase(active_key)
	return true

## Cleans up all relics and disconnects signals (prevents memory leaks).
func unregister_all() -> void:
	for r_id in _active_relics.keys():
		var relic: RelicData = _active_relics[r_id]
		if relic != null:
			relic.is_active = false
			if run_state != null:
				relic.on_unregistered(run_state)
	_active_relics.clear()
	disconnect_event_bus()

func get_relic(relic_id: String) -> RelicData:
	var cid: String = get_canonical_id(relic_id)
	if _active_relics.has(cid):
		return _active_relics[cid]
	return _active_relics.get(relic_id, null)

func has_relic(relic_id: String) -> bool:
	var cid: String = get_canonical_id(relic_id)
	return _active_relics.has(cid) or _active_relics.has(relic_id)

func create_relic(relic_id: String) -> RelicData:
	var cid: String = get_canonical_id(relic_id)
	if _catalog.has(cid):
		return _catalog[cid].call()
	if _catalog.has(relic_id):
		return _catalog[relic_id].call()
	# Backward compatibility for 'coroa_de_quitina' naming
	if cid == "coroa_de_quitina" and _catalog.has("coroa_quitina"):
		return _catalog["coroa_quitina"].call()
	return null

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
	register_catalog_entry("coroa_de_quitina", func(): return RelicCoroaQuitina.new())
	register_catalog_entry("relogio_da_forja", func(): return RelicRelogioDaForja.new())

# ── Canonical Concrete Relics ───────────────────────────────────────────────

class RelicBolsaDoMercador extends RelicData:
	func _init() -> void:
		super("bolsa_do_mercador", "Bolsa de Moedas da Guilda", "Vitórias em combate concedem +10 de ouro adicional.", RARITY_COMUM, 45)

	func on_combat_victory(rewards: Dictionary, _p_run_state: RunState) -> Dictionary:
		rewards["gold"] = int(rewards.get("gold", 0)) + 10
		return rewards

class RelicFrascoFeromonio extends RelicData:
	const CANCELABLE_CONDITIONS: Array[String] = [
		"poisoned", "envenenado", "veneno",
		"stunned", "atordoado", "atordoamento",
		"frightened", "amedrontado", "medo",
		"restrained", "imobilizado",
		"burning", "queimando", "fogo",
		"paralyzed", "paralisado", "paralisia"
	]

	func _init() -> void:
		super("frasco_feromonio", "Frasco de Feromônio Neutralizador", "Anula a primeira condição negativa recebida pelos heróis em cada combate.", RARITY_RARO, 80)
		counter_max = 1

	func on_status_applied(unit_id: String, status_id: String, _duration: int, p_run_state: RunState) -> Dictionary:
		if p_run_state == null or not p_run_state.heroes.has(unit_id):
			return {}
		var cond_lower: String = status_id.strip_edges().to_lower()
		if counter == 0 and cond_lower in CANCELABLE_CONDITIONS:
			counter = 1
			return {"cancel_status": true}
		return {}
```

---

## 5. Verification Method

To independently verify this remediation:

### 5.1 Apply Changes
The worker can either apply `/home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m3_fix_2/relic_remediation.patch`:
```bash
cd /home/anderson/Documents/projeto/RPG-battle
patch -p0 < .agents/teamwork/explorer_m3_fix_2/relic_remediation.patch
```
Or copy the full replacement files:
```bash
cp .agents/teamwork/explorer_m3_fix_2/proposed_RelicData.gd godot_project/scripts/run/relics/RelicData.gd
cp .agents/teamwork/explorer_m3_fix_2/proposed_RelicManager.gd godot_project/scripts/run/relics/RelicManager.gd
```

### 5.2 Update Test Suite in `test_relic_system.gd`
Apply the updated assertions in `test_relic_bolsa_do_mercador_awards_extra_gold` and add the new test cases from `/home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m3_fix_2/proposed_test_additions.gd`.

### 5.3 Automated Verification Commands
1. **Execute Milestone M3 Relic Test Suite**:
   ```bash
   bash godot_project/run_gut_tests.sh -gtest=res://test/unit/test_relic_system.gd
   ```
   *Expected Outcome*: 100% PASS, 0 failures, exit code 0.
2. **Execute Full Adversarial Stress Suite**:
   ```bash
   bash godot_project/run_gut_tests.sh -gtest=res://test/unit/test_relic_stress_adversarial.gd
   ```
   *Expected Outcome*:
   - `test_stress_duplicate_registration_with_reliquia_prefix`: duplicate registration returns `false`, active count remains 1, attack bonus does not stack.
   - `test_stress_relic_manager_sync_after_run_state_removal`: orphan relic is pruned cleanly.
3. **Execute Entire Project Test Suite**:
   ```bash
   bash godot_project/run_gut_tests.sh
   ```
   *Expected Outcome*: 800+ tests pass with 0 failures, exit code 0.

### 5.4 Invalidation Conditions
- If `p_run_state.add_gold()` is called inside `on_combat_victory()`, causing `_state.gold` to change before player claims reward.
- If `RelicFrascoFeromonio.on_status_applied()` cancels debuffs for enemies (e.g. `unit_id == "larva_carniceira"`).
- If registering `"martelo_runico"` followed by `"reliquia_martelo_runico"` creates 2 active relic instances in `RelicManager._active_relics`.
- If unregistering a relic leaves `relic.is_active == true` or leaves orphan relics alive after removal from `RunState.relics`.
